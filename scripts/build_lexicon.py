#!/usr/bin/env python3
"""Build a compact word-to-root index for Roots/*.md."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROOTS_DIR = ROOT / "Roots"
LEXICON_PATH = ROOTS_DIR / "_Lexicon.json"


HEADING_RE = re.compile(r"^(#{2,3})\s+(.+?)\s*$")
CODE_RE = re.compile(r"`([^`]+)`")
EXCLUDED_ENTRY_SECTIONS = {"비교 단어"}


def normalize(value: str) -> str:
    return value.casefold().strip()


def clean_heading(value: str) -> str:
    value = re.sub(r"\s+#.*$", "", value)
    return value.strip()


def heading_terms(heading: str) -> list[str]:
    """Return searchable terms from a word-entry heading."""

    cleaned = clean_heading(heading)
    terms = {cleaned}

    for code_term in CODE_RE.findall(cleaned):
        terms.add(code_term.strip())

    # Split only on obvious listing punctuation, not on spaces. Phrases such as
    # "fiscal policy" should remain searchable as phrases.
    for part in re.split(r"[,;/]", cleaned):
        part = part.strip()
        if part:
            terms.add(part)

    return sorted({term for term in terms if term})


def read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return path.read_text().splitlines()


def add_hit(
    terms: dict[str, list[dict[str, Any]]],
    term: str,
    *,
    path: Path,
    line_no: int,
    heading: str,
    section: str | None,
) -> None:
    normalized = normalize(term)
    if not normalized:
        return

    rel = path.relative_to(ROOT).as_posix()
    hit = {
        "term": term,
        "root": path.stem,
        "doc": rel,
        "line": line_no,
        "heading": heading,
        "section": section,
    }
    terms.setdefault(normalized, []).append(hit)


def parse_doc(path: Path) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    lines = read_lines(path)
    section: str | None = None
    heading_count = 0
    local_terms: dict[str, list[dict[str, Any]]] = {}

    for line_no, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if not match:
            continue

        marker, title = match.groups()
        title = clean_heading(title)

        if marker == "##":
            section = title
            continue

        if section in EXCLUDED_ENTRY_SECTIONS:
            continue

        heading_count += 1
        for term in heading_terms(title):
            add_hit(
                local_terms,
                term,
                path=path,
                line_no=line_no,
                heading=title,
                section=section,
            )

    stat = path.stat()
    doc_info = {
        "root": path.stem,
        "doc": path.relative_to(ROOT).as_posix(),
        "heading_count": heading_count,
        "mtime": stat.st_mtime,
    }
    return doc_info, local_terms


def build_lexicon() -> dict[str, Any]:
    docs: dict[str, dict[str, Any]] = {}
    terms: dict[str, list[dict[str, Any]]] = {}

    for path in sorted(ROOTS_DIR.glob("*.md")):
        if path.name.startswith("_"):
            continue
        doc_info, local_terms = parse_doc(path)
        docs[doc_info["doc"]] = doc_info
        for term, hits in local_terms.items():
            terms.setdefault(term, []).extend(hits)

    for hits in terms.values():
        hits.sort(key=lambda hit: (hit["doc"], hit["line"]))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schema": 1,
        "root": ROOT.as_posix(),
        "documents": docs,
        "terms": dict(sorted(terms.items())),
    }


def write_lexicon(path: Path = LEXICON_PATH) -> dict[str, Any]:
    lexicon = build_lexicon()
    path.write_text(
        json.dumps(lexicon, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return lexicon


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build Roots/_Lexicon.json for fast word lookup."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=LEXICON_PATH,
        help="lexicon JSON path",
    )
    args = parser.parse_args()

    lexicon = write_lexicon(args.output)
    print(
        f"indexed {len(lexicon['terms'])} terms from "
        f"{len(lexicon['documents'])} docs -> {args.output.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
