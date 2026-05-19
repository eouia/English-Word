#!/usr/bin/env python3
"""Find vocabulary entries in Roots/*.md without dumping every document."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROOTS_DIR = ROOT / "Roots"
LEXICON_PATH = ROOTS_DIR / "_Lexicon.json"


def normalize(value: str) -> str:
    return value.casefold().strip()


def load_lexicon() -> dict[str, Any] | None:
    if not LEXICON_PATH.exists():
        return None
    try:
        return json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def lexicon_is_fresh(lexicon: dict[str, Any]) -> bool:
    docs = lexicon.get("documents", {})
    if not isinstance(docs, dict):
        return False

    current_docs = {
        path.relative_to(ROOT).as_posix(): path
        for path in ROOTS_DIR.glob("*.md")
        if not path.name.startswith("_")
    }
    if set(current_docs) != set(docs):
        return False

    for rel, path in current_docs.items():
        recorded = docs.get(rel, {}).get("mtime")
        if recorded is None:
            return False
        if path.stat().st_mtime > float(recorded) + 0.001:
            return False
    return True


def find_term_in_lexicon(
    term: str, lexicon: dict[str, Any], include_index: bool
) -> list[tuple[int, Path, int, str]]:
    terms = lexicon.get("terms", {})
    if not isinstance(terms, dict):
        return []

    normalized = normalize(term)
    rows = terms.get(normalized, [])
    hits: list[tuple[int, Path, int, str]] = []
    for row in rows:
        doc = row.get("doc")
        if not isinstance(doc, str):
            continue
        path = ROOT / doc
        if not include_index and path.name.startswith("_"):
            continue
        line_no = int(row.get("line", 0))
        heading = str(row.get("heading", term))
        section = row.get("section")
        context = f"### {heading}"
        if section:
            context = f"{context} ({section})"
        hits.append((10, path, line_no, context))
    return hits


def score_line(term: str, line: str) -> int:
    lowered = normalize(line)
    exact_code = re.search(rf"`{re.escape(term)}`", lowered)
    word_boundary = re.search(rf"\b{re.escape(term)}\b", lowered)

    score = 0
    if exact_code:
        score += 5
    if word_boundary:
        score += 2
    if line.lstrip().startswith(("#", "-", "|")) and word_boundary:
        score += 1
    return score


def find_term(term: str, include_index: bool) -> list[tuple[int, Path, int, str]]:
    normalized = normalize(term)
    hits: list[tuple[int, Path, int, str]] = []

    for path in sorted(ROOTS_DIR.glob("*.md")):
        if not include_index and path.name.startswith("_"):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            lines = path.read_text().splitlines()

        for line_no, line in enumerate(lines, start=1):
            score = score_line(normalized, line)
            if score:
                snippet = line.strip()
                hits.append((score, path, line_no, snippet))

    return sorted(hits, key=lambda item: (-item[0], str(item[1]), item[2]))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Locate words already mentioned in Obsidian root docs."
    )
    parser.add_argument("terms", nargs="+", help="word or words to find")
    parser.add_argument(
        "--include-index",
        action="store_true",
        help="also search management docs such as Roots/_Index.md",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=8,
        help="maximum hits shown per term",
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="ignore Roots/_Lexicon.json and scan markdown files",
    )
    args = parser.parse_args()

    lexicon = None if args.scan else load_lexicon()
    use_lexicon = bool(lexicon and lexicon_is_fresh(lexicon))

    for term in args.terms:
        if use_lexicon and lexicon is not None:
            hits = find_term_in_lexicon(term, lexicon, args.include_index)
        else:
            hits = find_term(term, args.include_index)
        print(f"## {term}")
        if not hits:
            print("no hits")
            continue

        for score, path, line_no, snippet in hits[: args.limit]:
            rel = path.relative_to(ROOT)
            print(f"{rel}:{line_no}: score={score}: {snippet}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
