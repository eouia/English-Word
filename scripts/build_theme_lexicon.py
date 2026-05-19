#!/usr/bin/env python3
"""Build a compact word-to-theme index for Themes/*.md."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
THEMES_DIR = ROOT / "Themes"
LEXICON_PATH = THEMES_DIR / "_Lexicon.json"


ENTRY_HEADING_RE = re.compile(r"^(###)\s+(.+?)\s*$")
SECTION_HEADING_RE = re.compile(r"^(##)\s+(.+?)\s*$")
CODE_RE = re.compile(r"`([^`]+)`")
WIKI_LINK_FULL_RE = re.compile(r"^\[\[(?P<target>[^|\]]+)(?:\|(?P<alias>[^\]]+))?\]\]$")
ROOT_LINK_SUFFIX_RE = re.compile(
    r"\s+\((?:\[\[[^\]]+\]\](?:,\s*)?)+\)\s*$"
)


def normalize(value: str) -> str:
    return value.casefold().strip()


def clean_heading(value: str) -> str:
    value = re.sub(r"\s+#.*$", "", value)
    return value.strip()


def strip_root_link_suffix(value: str) -> str:
    """Remove trailing root-choice links from a theme heading."""

    return ROOT_LINK_SUFFIX_RE.sub("", value).strip()


def display_title(value: str) -> str:
    """Return the visible title from a plain or wiki-linked heading."""

    cleaned = strip_root_link_suffix(clean_heading(value))
    match = WIKI_LINK_FULL_RE.match(cleaned)
    if not match:
        return cleaned

    alias = match.group("alias")
    if alias:
        return alias.strip()

    target = match.group("target")
    return target.split("#", 1)[0].split("/", 1)[-1].strip()


def heading_terms(heading: str) -> list[str]:
    """Return searchable terms from a theme word-entry heading."""

    title = display_title(heading)
    terms = {title}

    for code_term in CODE_RE.findall(title):
        terms.add(code_term.strip())

    for part in re.split(r"[,;/]", title):
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
        "theme": path.stem,
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
        section_match = SECTION_HEADING_RE.match(line)
        if section_match:
            section = clean_heading(section_match.group(2))
            continue

        entry_match = ENTRY_HEADING_RE.match(line)
        if not entry_match:
            continue

        title = display_title(entry_match.group(2))
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
        "theme": path.stem,
        "doc": path.relative_to(ROOT).as_posix(),
        "heading_count": heading_count,
        "mtime": stat.st_mtime,
    }
    return doc_info, local_terms


def build_lexicon() -> dict[str, Any]:
    docs: dict[str, dict[str, Any]] = {}
    terms: dict[str, list[dict[str, Any]]] = {}

    for path in sorted(THEMES_DIR.glob("*.md")):
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
        description="Build Themes/_Lexicon.json for fast theme word lookup."
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
