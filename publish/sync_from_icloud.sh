#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$ROOT/publish/local.env"

if [ -f "$CONFIG" ]; then
  # shellcheck disable=SC1090
  source "$CONFIG"
fi

SOURCE="${OBSIDIAN_VAULT_PATH:-$HOME/Library/Mobile Documents/com~apple~CloudDocs/Obsidian/MyObsidian/English-Word}"
DEST="$ROOT"

if [ ! -d "$SOURCE" ]; then
  cat >&2 <<EOF
Obsidian vault path not found:
  $SOURCE

Create publish/local.env from publish/local.env.example and set:
  OBSIDIAN_VAULT_PATH="/absolute/path/to/English-Word"
EOF
  exit 1
fi

for path in Roots Themes scripts index.md AGENTS.md RTK.md; do
  if [ -e "$SOURCE/$path" ]; then
    rsync -a --delete "$SOURCE/$path" "$DEST/"
  fi
done

echo "Synced Obsidian notes from iCloud vault to $DEST"
