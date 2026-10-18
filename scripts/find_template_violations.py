#!/usr/bin/env python3
"""Find drift between one component of a downstream app and its template.

Renders the template twice with the app's own answers (its
`.copier-answers.yml`): at the app's `_commit`, the old render, which is what
the app's last `copier update` produced; and at the release a `copier update`
takes, the new render (the template's latest release tag, or `--new-ref`).
Copier renders from a clone of the template at the ref, so only files the
template tracks count: a gitignored stray in the checkout
(`scripts/__pycache__/*.pyc`) never shows.

1. Template-owned files: every file of the old render, the Jinja-rendered ones
   included, is compared with the app's copy. A difference is an edit to a
   template-owned file, or a conflict resolution the last update left. Files
   the render has and the app lacks are listed as missing.
2. App-owned files (`_skip_if_exists`, the new release's list, which is the
   one `copier update` reads): the update leaves them alone, so a template
   change to one reaches the app only by hand, through the changelog's step for
   it. Each is sorted by its old render, its new render and the app's copy into
   what the sync has to do.

Run it with the pinned copier (the backend template's uv project), from the
parent repo, once per component of a monorepo app:

    cexec modern-app uv run --project backend --locked python scripts/find_template_violations.py /work/<App> --template-repo .
    cexec modern-app uv run --project backend --locked python scripts/find_template_violations.py /work/<App>/backend --template-repo backend
    cexec modern-app uv run --project backend --locked python scripts/find_template_violations.py /work/<App>/frontend --template-repo frontend

Exits 1 when a template-owned file differs from the render or is missing.
"""

from __future__ import annotations

import argparse
import difflib
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ANSWERS_FILE = ".copier-answers.yml"


# ── Copier and git ───────────────────────────────────────────────────


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    )
    return result.stdout


def latest_release_tag(template_repo: Path) -> str:
    """The tag `copier update` takes by default: the highest PEP 440 release."""
    from packaging.version import InvalidVersion, Version

    best: tuple[Version, str] | None = None
    for tag in _git(template_repo, "tag", "--list").split():
        try:
            version = Version(tag)
        except InvalidVersion:
            continue
        if version.is_prerelease:
            continue
        if best is None or version > best[0]:
            best = (version, tag)
    if best is None:
        sys.exit(f"Error: {template_repo} has no release tag; pass --new-ref")
    return best[1]


def skip_if_exists_matcher(template_repo: Path, ref: str, data: dict):
    """Match paths against the ref's `_skip_if_exists`, as copier does."""
    import jinja2
    from packaging.version import Version
    from pathspec import PathSpec
    from pathspec import __version__ as pathspec_version

    config = yaml.safe_load(_git(template_repo, "show", f"{ref}:copier.yml"))
    env = jinja2.Environment()
    patterns = [
        env.from_string(p).render(**data) for p in config.get("_skip_if_exists", [])
    ]
    style = (
        "gitignore" if Version(pathspec_version) >= Version("1.0.0") else "gitwildmatch"
    )
    spec = PathSpec.from_lines(style, patterns)
    return spec.match_file


def render(template_repo: Path, ref: str, data: dict, dst: Path) -> None:
    try:
        from copier import run_copy
    except ImportError:
        sys.exit(
            "Error: copier is not importable. Run this script with the pinned copier:\n"
            "  cexec modern-app uv run --project backend --locked python "
            "scripts/find_template_violations.py ..."
        )
    run_copy(
        str(template_repo),
        dst,
        data=data,
        vcs_ref=ref,
        defaults=True,
        overwrite=True,
        unsafe=True,
        skip_tasks=True,
        quiet=True,
    )


def rendered_files(root: Path) -> set[str]:
    files = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in filenames:
            rel = os.path.relpath(os.path.join(dirpath, name), root)
            if rel != ANSWERS_FILE:
                files.add(rel)
    return files


def find_copier_commit(app_dir: Path) -> str | None:
    """The most recent commit that changed .copier-answers.yml."""
    out = _git(app_dir, "log", "--format=%H", "-1", "--", ANSWERS_FILE).strip()
    return out or None


def changed_since(app_dir: Path, commit: str, rel: str) -> bool:
    return bool(_git(app_dir, "diff", "--name-only", commit, "--", rel).strip())


def commits_since(app_dir: Path, commit: str, rel: str) -> list[str]:
    out = _git(app_dir, "log", "--oneline", f"{commit}..HEAD", "--", rel)
    return [line for line in out.splitlines() if line]


# ── Comparison ───────────────────────────────────────────────────────


def read(path: Path) -> bytes | None:
    if path.is_symlink():
        return b"symlink -> " + os.readlink(path).encode()
    if not path.is_file():
        return None
    return path.read_bytes()


def unified(a: bytes | None, b: bytes | None, a_name: str, b_name: str) -> str:
    try:
        a_lines = (a or b"").decode().splitlines(keepends=True)
        b_lines = (b or b"").decode().splitlines(keepends=True)
    except UnicodeDecodeError:
        return f"Binary files {a_name} and {b_name} differ\n"
    return "".join(difflib.unified_diff(a_lines, b_lines, a_name, b_name))


def count_diff_lines(diff_text: str) -> tuple[int, int]:
    added = removed = 0
    for line in diff_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    return added, removed


@dataclass
class Report:
    # Template-owned files that differ: (file, diff from the render to the app)
    differs: list[tuple[str, str]] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    template_equal: int = 0
    # App-owned buckets: file → diff to show (old→new template change, or "")
    buckets: dict[str, list[tuple[str, str]]] = field(default_factory=dict)


# Bucket order and their explanations. O = old render, N = new render, A = app.
BUCKETS = [
    (
        "take",
        "TAKE BY HAND",
        "The template changed it, and the app still has the old render: copier "
        "update keeps the old text. Take the template's change by hand (the "
        "changelog's step, or the new render).",
    ),
    (
        "merge",
        "MERGE BY HAND",
        "The template changed it, and the app has its own edits: copier update "
        "keeps the app's. Merge the template's change by hand (the changelog's step).",
    ),
    (
        "current",
        "ALREADY CURRENT",
        "The template changed it, and the app's copy already equals the new render.",
    ),
    (
        "new-absent",
        "NEW, APP HAS NONE",
        "The new release adds it: copier update creates it.",
    ),
    (
        "new-present",
        "NEW, APP HAS ITS OWN",
        "The new release adds it, and the app already has the file: copier "
        "update keeps the app's. Compare the two by hand.",
    ),
    (
        "dropped",
        "DROPPED BY THE TEMPLATE",
        "The new release no longer renders it: the app keeps its copy. Delete it "
        "by hand if the changelog says so.",
    ),
    (
        "deleted",
        "DELETED BY THE APP",
        "The render has it and the app doesn't: copier update re-creates it.",
    ),
    (
        "own",
        "THE APP'S OWN",
        "The template didn't change it; the app's copy differs from the render.",
    ),
    (
        "pristine",
        "EQUAL TO THE RENDER",
        "The template didn't change it; the app's copy equals the render.",
    ),
]
QUIET_BUCKETS = {"own", "pristine"}


def classify_app_owned(rel: str, old: Path, new: Path, app: Path) -> tuple[str, str]:
    o, n, a = read(old / rel), read(new / rel), read(app / rel)
    if o is None and n is None:
        return "", ""
    if o is None:
        if a is None:
            return "new-absent", ""
        return ("current" if a == n else "new-present"), ""
    if n is None:
        return "dropped", ""
    if a is None:
        return "deleted", ""
    if o == n:
        return ("pristine" if a == n else "own"), ""
    change = unified(o, n, f"old/{rel}", f"new/{rel}")
    if a == n:
        return "current", change
    if a == o:
        return "take", change
    return "merge", change


def build_report(
    app_dir: Path, current: Path, old: Path, new: Path, is_app_owned
) -> Report:
    """Template-owned files against the current render (the app's _commit);
    app-owned ones sorted by the old render, the new render and the app."""
    report = Report(buckets={key: [] for key, _, _ in BUCKETS})
    for rel in sorted(rendered_files(old) | rendered_files(new)):
        if is_app_owned(rel):
            bucket, change = classify_app_owned(rel, old, new, app_dir)
            if bucket:
                report.buckets[bucket].append((rel, change))
    for rel in sorted(rendered_files(current)):
        if is_app_owned(rel):
            continue
        expected, actual = read(current / rel), read(app_dir / rel)
        if actual is None:
            report.missing.append(rel)
        elif actual != expected:
            report.differs.append(
                (rel, unified(expected, actual, f"render/{rel}", rel))
            )
        else:
            report.template_equal += 1
    return report


# ── Output ───────────────────────────────────────────────────────────


class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def c(color: str, text: str) -> str:
    if sys.stdout.isatty():
        return f"{color}{text}{Colors.RESET}"
    return text


def print_diff(diff_text: str) -> None:
    for line in diff_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            print(f"    {c(Colors.GREEN, line)}")
        elif line.startswith("-") and not line.startswith("---"):
            print(f"    {c(Colors.RED, line)}")
        elif line.startswith("@@"):
            print(f"    {c(Colors.CYAN, line)}")
        else:
            print(f"    {line}")
    print()


def heading(color: str, text: str, note: str | None = None) -> None:
    print(c(Colors.BOLD + color, text))
    if note:
        print(c(Colors.DIM, f"({note})"))
    print(c(Colors.DIM, "-" * 60))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find drift between a downstream app component and its template.",
    )
    parser.add_argument(
        "app_dir", type=Path, help="The app component (holds .copier-answers.yml)"
    )
    parser.add_argument(
        "--template-repo",
        type=Path,
        default=None,
        help="The template repo (default: the answers' _src_path, from the app directory)",
    )
    parser.add_argument(
        "--old-ref",
        default=None,
        help="Template ref the app-owned files are sorted from (default: the "
        "app's _commit; after an update, the release the app came from)",
    )
    parser.add_argument(
        "--new-ref",
        default=None,
        help="Template ref the app-owned files are sorted to (default: the latest "
        "release tag, which copier update takes; HEAD for an unreleased change)",
    )
    parser.add_argument("--diff", action="store_true", help="Show the diffs")
    parser.add_argument(
        "--commits",
        action="store_true",
        help="Show the commits since the last copier update that touched each differing file",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Also list the app-owned files the template didn't change",
    )
    args = parser.parse_args()

    app_dir: Path = args.app_dir.resolve()
    if not (app_dir / ANSWERS_FILE).exists():
        sys.exit(f"Error: {app_dir} does not contain {ANSWERS_FILE}")
    answers = yaml.safe_load((app_dir / ANSWERS_FILE).read_text())
    data = {k: v for k, v in answers.items() if not k.startswith("_")}

    if args.template_repo:
        template_repo = args.template_repo.resolve()
    elif answers.get("_src_path"):
        template_repo = (app_dir / answers["_src_path"]).resolve()
    else:
        sys.exit("Error: cannot determine the template repo. Use --template-repo.")
    if not (template_repo / "copier.yml").exists():
        sys.exit(f"Error: {template_repo} does not contain copier.yml")

    current_ref = answers.get("_commit")
    if not current_ref:
        sys.exit(f"Error: {ANSWERS_FILE} has no _commit")
    old_ref = args.old_ref or current_ref
    new_ref = args.new_ref or latest_release_tag(template_repo)

    def commit_of(ref: str) -> str:
        return _git(template_repo, "rev-parse", f"{ref}^{{commit}}").strip()

    same_ref = commit_of(old_ref) == commit_of(new_ref)

    with tempfile.TemporaryDirectory(prefix="template-render.") as tmp:
        renders: dict[str, Path] = {}

        def rendered(ref: str) -> Path:
            commit = commit_of(ref)
            if commit not in renders:
                renders[commit] = Path(tmp, str(len(renders)))
                render(template_repo, ref, data, renders[commit])
            return renders[commit]

        current, old, new = rendered(current_ref), rendered(old_ref), rendered(new_ref)
        is_app_owned = skip_if_exists_matcher(template_repo, new_ref, data)
        report = build_report(app_dir, current, old, new, is_app_owned)

    baseline = find_copier_commit(app_dir)

    # ── Header ────────────────────────────────────────────────────
    print()
    print(c(Colors.BOLD, f"Template drift report: {app_dir}"))
    print(c(Colors.DIM, "=" * 60))
    print(f"Template:   {template_repo}")
    print(f"Render:     {current_ref} (the app's _commit)")
    new_note = (
        "the latest release, which copier update takes"
        if not args.new_ref
        else "--new-ref"
    )
    print(f"Update to:  {new_ref} ({new_note})")
    flags = {
        k: v for k, v in data.items() if k.startswith("use_") and isinstance(v, bool)
    }
    if flags:
        print("Flags:      " + ", ".join(f"{k}={v}" for k, v in sorted(flags.items())))
    if baseline:
        desc = _git(app_dir, "log", "--format=%h %s", "-1", baseline).strip()
        print(f"Last copier update: {desc}")
    print()

    # ── Template-owned ────────────────────────────────────────────
    if report.differs:
        heading(
            Colors.RED,
            f"TEMPLATE-OWNED FILES THAT DIFFER FROM THE RENDER: {len(report.differs)}",
            f"against the {current_ref} render, so edits to template-owned files; "
            "* = changed since the last copier update",
        )
        for rel, diff in report.differs:
            added, removed = count_diff_lines(diff)
            mark = " *" if baseline and changed_since(app_dir, baseline, rel) else ""
            print(
                f"  {c(Colors.YELLOW, rel)}  {c(Colors.DIM, f'+{added}/-{removed}')}{mark}"
            )
            if args.commits and baseline:
                for line in commits_since(app_dir, baseline, rel):
                    print(f"    {c(Colors.CYAN, line)}")
            if args.diff:
                print_diff(diff)
        print()
    else:
        print(c(Colors.GREEN, "Every template-owned file equals the render."))
        print()

    if report.missing:
        heading(
            Colors.YELLOW,
            f"MISSING: {len(report.missing)} template-owned files the render has and the app lacks",
            "the app deleted them, or never took them",
        )
        for rel in report.missing:
            print(f"  {rel}")
        print()

    # ── App-owned ─────────────────────────────────────────────────
    span = old_ref if same_ref else f"{old_ref} -> {new_ref}"
    print(c(Colors.BOLD, f"APP-OWNED FILES (_skip_if_exists), {span}"))
    print(
        c(
            Colors.DIM,
            "(copier update leaves these alone; a template change reaches the app by hand)",
        )
    )
    print(c(Colors.DIM, "=" * 60))
    shown = [
        (key, title, note)
        for key, title, note in BUCKETS
        if report.buckets[key] and (key not in QUIET_BUCKETS or args.all)
    ]
    if not shown:
        print(c(Colors.GREEN, "Nothing to take by hand."))
        print()
    for key, title, note in shown:
        entries = report.buckets[key]
        heading(Colors.BLUE, f"{title}: {len(entries)}", note)
        for rel, change in entries:
            print(f"  {rel}")
            if args.diff and change:
                print_diff(change)
        print()

    # ── Summary ───────────────────────────────────────────────────
    print(c(Colors.BOLD, "Summary:"))
    print(
        f"  {c(Colors.GREEN, str(report.template_equal))} template-owned files equal the render"
    )
    if report.differs:
        print(
            f"  {c(Colors.RED, str(len(report.differs)))} template-owned files differ from it"
        )
    if report.missing:
        print(
            f"  {c(Colors.YELLOW, str(len(report.missing)))} template-owned files missing"
        )
    counts = ", ".join(
        f"{len(report.buckets[key])} {title.lower()}"
        for key, title, _ in BUCKETS
        if report.buckets[key]
    )
    print(f"  app-owned: {counts or 'none'}")
    if not args.all and any(report.buckets[k] for k in QUIET_BUCKETS):
        print(
            c(
                Colors.DIM,
                "  (--all lists the app-owned files the template didn't change)",
            )
        )
    print()

    if report.differs or report.missing:
        sys.exit(1)


if __name__ == "__main__":
    main()
