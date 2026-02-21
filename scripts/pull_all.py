#!/usr/bin/env python3
"""Read the workspace file, git pull each path, and report repo status."""

import subprocess

from workspace import get_repos


def main():
    for name, path in get_repos():
        print(f"\n{'=' * 76}")
        print(f"  {name}  ({path})")
        print(f"{'=' * 76}")

        # git pull
        pull = subprocess.run(
            ["git", "pull"],
            cwd=path,
            capture_output=True,
            text=True,
        )
        print(pull.stdout.strip())
        if pull.stderr.strip():
            print(pull.stderr.strip())

        # check clean/dirty
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path,
            capture_output=True,
            text=True,
        )
        if status.stdout.strip():
            print(f"Status: \033[1;31mDIRTY\033[0m")
            for line in status.stdout.strip().splitlines():
                print(f"  {line}")
        else:
            print(f"Status: \033[32mclean\033[0m")

    print()


if __name__ == "__main__":
    main()
