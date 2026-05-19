#!/usr/bin/env bash
set -euo pipefail

SOURCE="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Obsidian/MyObsidian/English-Word"
DEST="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for path in Roots Themes scripts index.md AGENTS.md RTK.md; do
  if [ -e "$SOURCE/$path" ]; then
    rsync -a --delete "$SOURCE/$path" "$DEST/"
  fi
done

echo "Synced Obsidian notes from iCloud vault to $DEST"
