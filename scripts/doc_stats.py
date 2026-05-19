#!/usr/bin/env python3
"""Show compact size stats for root documents."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROOTS_DIR = ROOT / "Roots"
LEXICON_PATH = ROOTS_DIR / "_Lexicon.json"


def count_headings(path: Path) -> int:
    return sum(
        1
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("### ")
    )


def load_fresh_lexicon() -> dict[str, Any] | None:
    if not LEXICON_PATH.exists():
        return None
    try:
        lexicon = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None

    docs = lexicon.get("documents")
    if not isinstance(docs, dict):
        return None

    current_docs = {
        path.relative_to(ROOT).as_posix(): path
        for path in ROOTS_DIR.glob("*.md")
        if not path.name.startswith("_")
    }
    if set(current_docs) != set(docs):
        return None

    for rel, path in current_docs.items():
        recorded = docs.get(rel, {}).get("mtime")
        if recorded is None or path.stat().st_mtime > float(recorded) + 0.001:
            return None
    return lexicon


def stats_from_lexicon(lexicon: dict[str, Any]) -> list[tuple[int, Path]]:
    rows: list[tuple[int, Path]] = []
    for doc, info in lexicon["documents"].items():
        rows.append((int(info["heading_count"]), ROOT / doc))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List root docs with many word/comparison headings."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="number of files to show",
    )
    parser.add_argument(
        "--warn",
        type=int,
        default=20,
        help="mark files at or above this heading count",
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="ignore Roots/_Lexicon.json and scan markdown files",
    )
    args = parser.parse_args()

    lexicon = None if args.scan else load_fresh_lexicon()
    if lexicon is not None:
        rows = stats_from_lexicon(lexicon)
    else:
        rows = []
        for path in sorted(ROOTS_DIR.glob("*.md")):
            if path.name.startswith("_"):
                continue
            rows.append((count_headings(path), path))

    for count, path in sorted(rows, key=lambda item: (-item[0], str(item[1])))[: args.limit]:
        marker = " !" if count >= args.warn else ""
        print(f"{count:2d}{marker} {path.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
