#!/usr/bin/env python3
"""Push all repos and their tags, after verifying none have uncommitted changes."""

import subprocess
import sys

from workspace import get_repos


def run(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def main():
    repos = get_repos()

    # Pre-flight: check all repos are clean
    dirty = []
    for name, path in repos:
        status = run(["git", "status", "--porcelain"], cwd=path)
        if status.stdout.strip():
            dirty.append((name, path, status.stdout.strip()))

    if dirty:
        print("\033[1;31mAborting: the following repos have uncommitted changes:\033[0m\n")
        for name, path, changes in dirty:
            print(f"  {name}  ({path})")
            for line in changes.splitlines():
                print(f"    {line}")
            print()
        sys.exit(1)

    # Push all repos
    for name, path in repos:
        print(f"\n{'=' * 76}")
        print(f"  {name}  ({path})")
        print(f"{'=' * 76}")

        # Push commits
        push = run(["git", "push"], cwd=path)
        print(push.stderr.strip() or push.stdout.strip())

        # Push tags
        tags = run(["git", "push", "--tags"], cwd=path)
        tag_output = tags.stderr.strip() or tags.stdout.strip()
        if tag_output and tag_output != "Everything up-to-date":
            print(tag_output)

    print()


if __name__ == "__main__":
    main()
