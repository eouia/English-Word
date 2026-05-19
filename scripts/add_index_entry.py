#!/usr/bin/env python3
"""Add or replace a root entry in Roots/_Index.md.

Usage:
  python3 scripts/add_index_entry.py simil '같음, 비슷함 계열 (`similar`, `assemble`)'
  python3 scripts/add_index_entry.py simil '같음, 비슷함 계열'
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "Roots" / "_Index.md"
ENTRY_RE = re.compile(r"^- \[\[([^\]]+)\]\] - (.*)$")
TABLE_ROW_RE = re.compile(r"^\|\s*\[\[([^\]]+)\]\]\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$")
TABLE_HEADER_RE = re.compile(r"^\|\s*어근\s*\|\s*핵심 의미\s*\|\s*대표 단어\s*\|$")
WORD_HEADING_RE = re.compile(r"^###\s+(.+?)\s*$")


def split_description(description: str) -> tuple[str, str]:
    match = re.match(r"^(.*?)\s+\((`.*`)\)$", description)
    if match:
        return match.group(1), match.group(2)
    return description, ""


def clean_heading(value: str) -> str:
    value = re.sub(r"\s+#.*$", "", value)
    return value.strip().strip("`")


def extract_examples(root: str, max_examples: int) -> str:
    path = ROOT / "Roots" / f"{root}.md"
    if not path.exists():
        return ""

    examples: list[str] = []
    in_words_section = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_words_section = line.strip() == "## 단어들"
            continue
        if not in_words_section:
            continue

        match = WORD_HEADING_RE.match(line)
        if not match:
            continue

        heading = clean_heading(match.group(1))
        if heading and heading not in examples:
            examples.append(heading)
        if len(examples) >= max_examples:
            break

    return ", ".join(f"`{example}`" for example in examples)


def entry_line(
    root: str,
    description: str,
    table: bool = False,
    *,
    auto_examples: bool = True,
    max_examples: int = 10,
) -> str:
    if table:
        meaning, examples = split_description(description)
        if not examples and auto_examples:
            examples = extract_examples(root, max_examples)
        return f"| [[{root}]] | {meaning} | {examples} |"
    return f"- [[{root}]] - {description}"


def entry_key(line: str) -> str | None:
    match = ENTRY_RE.match(line)
    if match:
        return match.group(1).casefold()
    match = TABLE_ROW_RE.match(line)
    if match:
        return match.group(1).casefold()
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Add or update an entry in Roots/_Index.md.")
    parser.add_argument("root", help="Root document name without .md")
    parser.add_argument(
        "description",
        help="core meaning; examples may be appended as '(`word`, `word`)'",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=10,
        help="maximum examples to auto-read from Roots/root.md when omitted",
    )
    parser.add_argument(
        "--no-auto-examples",
        action="store_true",
        help="do not auto-read representative words from Roots/root.md",
    )
    args = parser.parse_args()

    root = args.root.strip()
    description = args.description.strip()
    if not root or not description:
        raise SystemExit("root and description are required")

    lines = INDEX_PATH.read_text(encoding="utf-8").splitlines()
    root_key = root.casefold()

    existing_idx = None
    root_start = None
    root_end = None

    for idx, line in enumerate(lines):
        if line == "## Roots":
            root_start = idx + 1
            continue
        if root_start is not None and idx > root_start and line.startswith("## "):
            root_end = idx
            break
        key = entry_key(line)
        if key == root_key:
            existing_idx = idx

    if root_start is None:
        raise SystemExit("Could not find '## Roots' section")
    if root_end is None:
        root_end = len(lines)

    has_table = any(TABLE_HEADER_RE.match(line) for line in lines[root_start:root_end])
    new_line = entry_line(
        root,
        description,
        table=has_table,
        auto_examples=not args.no_auto_examples,
        max_examples=args.max_examples,
    )

    if existing_idx is not None:
        lines[existing_idx] = new_line
    else:
        insert_at = root_end
        for idx in range(root_start, root_end):
            key = entry_key(lines[idx])
            if key and key > root_key:
                insert_at = idx
                break
        lines.insert(insert_at, new_line)

    INDEX_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(new_line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
