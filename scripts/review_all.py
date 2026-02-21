#!/usr/bin/env python3
"""Show all pending changes (unpushed commits + uncommitted work) across repos."""

import io
import os
import subprocess
import sys

from workspace import get_repos


def run(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def run_color(args, cwd):
    return subprocess.run([*args, "--color=always"], cwd=cwd, capture_output=True, text=True)


def review_repo(name, path):
    sections = []

    # Unpushed commits (commits ahead of upstream)
    log = run(
        ["git", "log", "--oneline", "@{upstream}..HEAD"],
        cwd=path,
    )
    if log.returncode == 0 and log.stdout.strip():
        commits = log.stdout.strip()
        diff = run_color(
            ["git", "diff", "@{upstream}..HEAD"],
            cwd=path,
        )
        sections.append(("Unpushed commits", commits, diff.stdout))

    # Staged changes
    staged = run_color(["git", "diff", "--cached"], cwd=path)
    if staged.stdout.strip():
        sections.append(("Staged changes", None, staged.stdout))

    # Unstaged changes
    unstaged = run_color(["git", "diff"], cwd=path)
    if unstaged.stdout.strip():
        sections.append(("Unstaged changes", None, unstaged.stdout))

    # Untracked files
    untracked = run(["git", "ls-files", "--others", "--exclude-standard"], cwd=path)
    if untracked.stdout.strip():
        sections.append(("Untracked files", untracked.stdout.strip(), None))

    return sections


def main():
    found_any = False

    for name, path in get_repos():
        sections = review_repo(name, path)
        if not sections:
            continue

        found_any = True
        print(f"\n{'=' * 76}")
        print(f"  {name}  ({path})")
        print(f"{'=' * 76}")

        for title, summary, diff in sections:
            print(f"\n--- {title} ---")
            if summary:
                print(summary)
            if diff:
                print(diff)

    if not found_any:
        print("No pending changes in any repo.")

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
