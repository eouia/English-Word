#!/usr/bin/env python3
"""Insert IPA pronunciation lines for indexed vocabulary entries.

The script only touches headings already present in Roots/_Lexicon.json and
Themes/_Lexicon.json. Multiword headings are skipped unless the heading also
has single-token indexed terms, such as "ideal / ideals".
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRONUNCIATION_PATH = ROOT / "scripts" / "pronunciations.json"
LEXICON_PATHS = (ROOT / "Roots" / "_Lexicon.json", ROOT / "Themes" / "_Lexicon.json")

ELIGIBLE_TERM_RE = re.compile(r"^[A-Za-z][A-Za-z'-]*$")
PRONUNCIATION_LINE_RE = re.compile(r"^-\s+발음:")


@dataclass(frozen=True)
class HeadingTarget:
    doc: Path
    line: int
    heading: str
    terms: tuple[str, ...]


def is_eligible_term(term: str) -> bool:
    return bool(ELIGIBLE_TERM_RE.match(term)) and " " not in term


def load_pronunciations(path: Path) -> dict[str, list[dict[str, str]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["entries"]


def iter_lexicon_hits(paths: tuple[Path, ...]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for path in paths:
        lexicon = json.loads(path.read_text(encoding="utf-8"))
        for term, entries in lexicon["terms"].items():
            if not is_eligible_term(term):
                continue
            for entry in entries:
                hits.append({**entry, "term": term})
    return hits


def collect_targets(hits: list[dict[str, Any]]) -> list[HeadingTarget]:
    grouped: dict[tuple[str, int, str], set[str]] = {}
    for hit in hits:
        key = (hit["doc"], int(hit["line"]), hit["heading"])
        grouped.setdefault(key, set()).add(hit["term"])

    targets: list[HeadingTarget] = []
    for (doc, line, heading), terms in grouped.items():
        targets.append(
            HeadingTarget(
                doc=ROOT / doc,
                line=line,
                heading=heading,
                terms=tuple(sorted(terms, key=str.casefold)),
            )
        )
    return sorted(targets, key=lambda item: (item.doc.as_posix(), item.line))


def format_entry(term: str, entries: list[dict[str, str]]) -> str:
    parts = []
    for entry in entries:
        label = entry.get("label")
        ipa = entry["ipa"]
        parts.append(f"{label} {ipa}" if label else ipa)
    return ", ".join(parts)


def format_line(terms: tuple[str, ...], pronunciations: dict[str, list[dict[str, str]]]) -> str:
    if len(terms) == 1:
        term = terms[0].casefold()
        return f"- 발음: {format_entry(term, pronunciations[term])}"

    parts = []
    for term in terms:
        key = term.casefold()
        parts.append(f"`{term}` {format_entry(key, pronunciations[key])}")
    return "- 발음: " + "; ".join(parts)


def insert_for_doc(
    path: Path,
    targets: list[HeadingTarget],
    pronunciations: dict[str, list[dict[str, str]]],
    *,
    write: bool,
    refresh: bool,
) -> tuple[int, int, list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    changed = 0
    skipped_existing = 0
    missing: list[str] = []

    for target in sorted(targets, key=lambda item: item.line, reverse=True):
        missing_terms = [term for term in target.terms if term.casefold() not in pronunciations]
        if missing_terms:
            missing.append(f"{path.relative_to(ROOT)}:{target.line} {', '.join(missing_terms)}")
            continue

        idx = target.line - 1
        if idx < 0 or idx >= len(lines) or not lines[idx].lstrip().startswith("### "):
            missing.append(f"{path.relative_to(ROOT)}:{target.line} heading line changed")
            continue

        insert_at = idx + 1
        if insert_at < len(lines) and lines[insert_at].strip() == "":
            insert_at += 1

        line = format_line(target.terms, pronunciations)
        if insert_at < len(lines) and PRONUNCIATION_LINE_RE.match(lines[insert_at]):
            if refresh and lines[insert_at] != line:
                lines[insert_at] = line
                changed += 1
            else:
                skipped_existing += 1
            continue

        lines.insert(insert_at, line)
        changed += 1

    if write and changed:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return changed, skipped_existing, missing


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add '- 발음:' IPA lines to indexed Roots and Themes entries."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="modify markdown files; without this flag, only print a dry-run summary",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=PRONUNCIATION_PATH,
        help="pronunciation JSON path",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="replace existing pronunciation lines when data has changed",
    )
    args = parser.parse_args()

    pronunciations = load_pronunciations(args.data)
    targets = collect_targets(iter_lexicon_hits(LEXICON_PATHS))

    by_doc: dict[Path, list[HeadingTarget]] = {}
    for target in targets:
        by_doc.setdefault(target.doc, []).append(target)

    total_inserted = 0
    total_existing = 0
    all_missing: list[str] = []
    touched_docs = 0

    for path, doc_targets in sorted(by_doc.items()):
        changed, existing, missing = insert_for_doc(
            path, doc_targets, pronunciations, write=args.write, refresh=args.refresh
        )
        total_inserted += changed
        total_existing += existing
        all_missing.extend(missing)
        if changed:
            touched_docs += 1

    mode = "updated" if args.write else "would update"
    print(
        f"{mode} {touched_docs} docs; changed {total_inserted} pronunciation lines; "
        f"skipped {total_existing} existing lines; missing {len(all_missing)} headings"
    )
    if all_missing:
        print("missing examples:")
        for item in all_missing[:40]:
            print(f"- {item}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
