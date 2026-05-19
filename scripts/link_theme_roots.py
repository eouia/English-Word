#!/usr/bin/env python3
"""Link theme entry headings to matching root documents.

Default mode is a dry run. Use --write to update Theme markdown files.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
THEMES_DIR = ROOT / "Themes"
LEXICON_PATH = ROOT / "Roots" / "_Lexicon.json"

ENTRY_HEADING_RE = re.compile(r"^(###)\s+(.+?)\s*$")
WIKI_LINK_RE = re.compile(r"\[\[.+?\]\]")


def normalize(value: str) -> str:
    return value.casefold().strip()


def display_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def clean_heading(value: str) -> str:
    value = re.sub(r"\s+#.*$", "", value)
    return value.strip()


def load_lexicon() -> dict[str, list[dict[str, Any]]]:
    data = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
    terms = data.get("terms", {})
    if not isinstance(terms, dict):
        raise SystemExit(f"Invalid lexicon: {LEXICON_PATH}")
    return terms


def choose_hit(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Pick a single target if the lexicon points to one root document."""

    docs = {row.get("doc") for row in rows if isinstance(row.get("doc"), str)}
    if len(docs) != 1:
        return None
    return rows[0]


def iter_theme_paths(args: argparse.Namespace) -> list[Path]:
    if args.files:
        paths = []
        for value in args.files:
            path = Path(value)
            if not path.is_absolute():
                path = ROOT / path
            paths.append(path)
        return paths

    return sorted(
        path
        for path in THEMES_DIR.glob("*.md")
        if not path.name.startswith("_")
    )


def link_heading(title: str, hit: dict[str, Any]) -> str:
    root = str(hit["root"])
    return f"[[{root}|{title}]]"


def process_file(
    path: Path,
    terms: dict[str, list[dict[str, Any]]],
    *,
    write: bool,
) -> tuple[int, int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    changed = 0
    skipped_ambiguous = 0
    output: list[str] = []

    for line_no, line in enumerate(lines, start=1):
        match = ENTRY_HEADING_RE.match(line)
        if not match:
            output.append(line)
            continue

        marker, title = match.groups()
        title = clean_heading(title)
        if WIKI_LINK_RE.search(title):
            output.append(line)
            continue

        rows = terms.get(normalize(title), [])
        if not rows:
            output.append(line)
            continue

        hit = choose_hit(rows)
        if hit is None:
            skipped_ambiguous += 1
            roots = sorted(
                {
                    str(row.get("root"))
                    for row in rows
                    if isinstance(row.get("root"), str)
                }
            )
            print(
                f"ambiguous: {display_path(path)}:{line_no}: {title} -> "
                + ", ".join(roots)
            )
            output.append(line)
            continue

        new_line = f"{marker} {link_heading(title, hit)}"
        if new_line != line:
            changed += 1
            print(
                f"link: {display_path(path)}:{line_no}: "
                f"{title} -> [[{hit['root']}|{title}]]"
            )
            output.append(new_line)
        else:
            output.append(line)

    if write and changed:
        path.write_text("\n".join(output) + "\n", encoding="utf-8")

    return changed, skipped_ambiguous


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Link ### word headings in Themes/*.md to matching root documents "
            "using Roots/_Lexicon.json."
        )
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="optional theme files to process, relative to repository root",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="modify files in place; default is dry-run only",
    )
    args = parser.parse_args()

    terms = load_lexicon()
    total_changed = 0
    total_ambiguous = 0
    for path in iter_theme_paths(args):
        changed, ambiguous = process_file(path, terms, write=args.write)
        total_changed += changed
        total_ambiguous += ambiguous

    mode = "updated" if args.write else "would update"
    print(f"{mode} {total_changed} headings; skipped {total_ambiguous} ambiguous headings")
    if not args.write and total_changed:
        print("Run again with --write to apply these links.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
