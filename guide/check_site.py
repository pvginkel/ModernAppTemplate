"""The guide's own checks, beyond the strict build and DevGuides' check_guide.py, over its source.

Run from this directory: `uv run --locked python check_site.py`. check_guide.py runs it after the
build; the guide contract it checks (nav and llms coverage, links) is not repeated here.

- Every rule is a level-3 heading of one form, `### API-1 — Title { #api-1 }`: the id, an em dash,
  the title, and the id in lower case as the anchor. Links and the guide's skill address a rule by
  that anchor, and a heading that misses it gets one Zensical derives from the title, which the
  next reword breaks.
- No two rules share an id, across pages. An id is never reused, so a duplicate is always wrong.
- Every rule has its reason: a `**Why.**` paragraph before the next heading.

The pages are every *.md under pages/, mkdocs.yml's docs_dir, which excludes none.
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGES = HERE / "pages"
# A level-3 heading that opens with something shaped like a rule id is meant to be a rule.
RULE_LIKE = re.compile(r"^### +[A-Z]+-[0-9]")
RULE = re.compile(r"^### (?P<id>[A-Z]+-[1-9][0-9]*) — \S.*\S \{ #(?P<anchor>[a-z]+-[0-9]+) \}$")
HEADING = re.compile(r"^#{1,6} ")
FENCE = re.compile(r"^\s*(```|~~~)")


def _lines(path: Path) -> list[tuple[int, str]]:
    """The page's lines outside fenced code blocks, numbered from 1."""
    lines, fenced = [], False
    for number, line in enumerate(path.read_text(encoding="utf8").splitlines(), start=1):
        if FENCE.match(line):
            fenced = not fenced
        elif not fenced:
            lines.append((number, line))
    return lines


def main() -> int:
    errors: list[str] = []
    seen: dict[str, str] = {}
    for path in sorted(PAGES.rglob("*.md")):
        page = path.relative_to(HERE).as_posix()
        open_rule: tuple[str, str] | None = None

        def close(rule: tuple[str, str] | None) -> None:
            if rule is not None:
                errors.append(f"{rule[1]}: {rule[0]} has no **Why.** paragraph")

        for number, line in _lines(path):
            where = f"{page}:{number}"
            if HEADING.match(line):
                close(open_rule)
                open_rule = None
            if RULE_LIKE.match(line):
                match = RULE.fullmatch(line)
                if match is None:
                    errors.append(f"{where}: a rule heading is `### ID-n — Title {{ #id-n }}`")
                    continue
                rule_id = match["id"]
                if match["anchor"] != rule_id.lower():
                    errors.append(f"{where}: {rule_id}'s anchor is #{rule_id.lower()}")
                if rule_id in seen:
                    errors.append(f"{where}: {rule_id} is already {seen[rule_id]}")
                seen[rule_id] = where
                open_rule = (rule_id, where)
            elif open_rule is not None and line.startswith("**Why.**"):
                open_rule = None
        close(open_rule)

    for error in errors:
        print(error, file=sys.stderr)
    if not seen:
        print("no rule found under pages/", file=sys.stderr)
        return 1
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
