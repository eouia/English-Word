#!/usr/bin/env python3
"""Open a vault file in Obsidian from this project.

Usage:
  python3 scripts/open_in_obsidian.py Roots/dia.md
  python3 scripts/open_in_obsidian.py Roots/dia.md --same-tab
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def find_vault_root(start: Path) -> Path:
    for path in (start, *start.parents):
        if (path / ".obsidian").is_dir():
            return path
    raise SystemExit("Could not find an Obsidian vault root containing .obsidian")


def main() -> int:
    parser = argparse.ArgumentParser(description="Open a file in the current Obsidian vault.")
    parser.add_argument("path", help="File path, relative to this project or to the vault root.")
    parser.add_argument("--same-tab", action="store_true", help="Reuse the current tab instead of opening a new tab.")
    args = parser.parse_args()

    cwd = Path.cwd().resolve()
    project_root = Path(__file__).resolve().parents[1]
    vault_root = find_vault_root(project_root)

    raw = Path(args.path).expanduser()
    candidates = []
    if raw.is_absolute():
        candidates.append(raw)
    else:
        candidates.append((cwd / raw).resolve())
        candidates.append((project_root / raw).resolve())
        candidates.append((vault_root / raw).resolve())

    target = next((path for path in candidates if path.exists()), None)
    if target is None:
        checked = "\n".join(f"- {path}" for path in candidates)
        raise SystemExit(f"File not found. Checked:\n{checked}")

    try:
        vault_path = target.relative_to(vault_root).as_posix()
    except ValueError as exc:
        raise SystemExit(f"Target is outside the Obsidian vault: {target}") from exc

    cmd = ["obsidian", f"vault={vault_root.name}", "open", f"path={vault_path}"]
    if not args.same_tab:
        cmd.append("newtab")

    return subprocess.run(cmd, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
