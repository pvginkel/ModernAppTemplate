#!/usr/bin/env python3
"""Show app-specific changes in each downstream repo since its last copier sync."""

import io
import os
import subprocess
import sys
from pathlib import Path

from workspace import get_repos

ANSWERS_FILE = ".copier-answers.yml"


def run(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def run_color(args, cwd):
    return subprocess.run([*args, "--color=always"], cwd=cwd, capture_output=True, text=True)


def get_sync_commit(path):
    """Return the SHA of the last commit that touched .copier-answers.yml, or None."""
    result = run(
        ["git", "log", "-1", "--format=%H %ai", "--", ANSWERS_FILE],
        cwd=path,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None, None
    parts = result.stdout.strip().split(" ", 1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def get_template_version(path):
    """Extract _commit value from .copier-answers.yml (the template tag/ref)."""
    answers = Path(path) / ANSWERS_FILE
    for line in answers.read_text().splitlines():
        if line.startswith("_commit:"):
            return line.split(":", 1)[1].strip()
    return "unknown"


def review_repo(name, path):
    answers_path = Path(path) / ANSWERS_FILE
    if not answers_path.exists():
        return None  # Not a copier-managed repo

    sync_sha, sync_date = get_sync_commit(path)
    if not sync_sha:
        return {"name": name, "path": path, "error": f"No git history for {ANSWERS_FILE}"}

    version = get_template_version(path)

    # Commits since the sync commit (excluding the sync commit itself)
    log = run(
        ["git", "log", "--oneline", f"{sync_sha}..HEAD", "--", ".", ":(exclude)docs/"],
        cwd=path,
    )
    commits = log.stdout.strip() if log.returncode == 0 else ""

    # Full diff since the sync commit (--color=always must come before -- to be recognized)
    diff = run(
        ["git", "diff", "--color=always", f"{sync_sha}..HEAD", "--", ".", ":(exclude)docs/"],
        cwd=path,
    )
    diff_output = diff.stdout if diff.returncode == 0 else ""

    return {
        "name": name,
        "path": path,
        "version": version,
        "sync_sha": sync_sha[:12],
        "sync_date": sync_date.split(" ")[0],  # date only
        "commits": commits,
        "diff": diff_output,
    }


def print_repo(info):
    if "error" in info:
        print(f"\n{'=' * 76}")
        print(f"  {info['name']}  ({info['path']})")
        print(f"{'=' * 76}")
        print(f"  ERROR: {info['error']}")
        return

    commit_count = len(info["commits"].splitlines()) if info["commits"] else 0
    noun = "commit" if commit_count == 1 else "commits"

    print(f"\n{'=' * 76}")
    print(f"  {info['name']}  (template {info['version']})")
    print(f"  {info['path']}")
    print(f"{'=' * 76}")
    print(
        f"\n  Last sync: {info['sync_sha']}  {info['sync_date']}"
        f"  —  {commit_count} app {noun} since then"
    )

    if info["commits"]:
        print(f"\n--- Commits since last sync ---")
        print(info["commits"])

    if info["diff"]:
        print(f"\n--- Diff since last sync ---")
        print(info["diff"])

    if not info["commits"] and not info["diff"]:
        print("\n  (no app changes since last sync)")


def main():
    found_any = False

    for name, path in get_repos():
        info = review_repo(name, path)
        if info is None:
            continue  # Skip repos without .copier-answers.yml (templates, parent)

        found_any = True
        print_repo(info)

    if not found_any:
        print("No copier-managed repos found.")

    print()


if __name__ == "__main__":
    if sys.stdout.isatty():
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        main()
        sys.stdout = old_stdout
        output = buf.getvalue()
        if output:
            pager = subprocess.Popen(
                ["less", "-R"],
                stdin=subprocess.PIPE,
                env={**os.environ, "LESSCHARSET": "utf-8"},
            )
            try:
                pager.communicate(input=output.encode())
            except KeyboardInterrupt:
                pager.kill()
    else:
        main()
