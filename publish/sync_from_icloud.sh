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
VAULT_SYNC_PATHS=(Roots Themes scripts index.md AGENTS.md RTK.md)

guard_workspace_note_changes() {
  local dirty unsafe line path
  dirty="$(git -C "$ROOT" status --porcelain -- "${VAULT_SYNC_PATHS[@]}")"
  if [ -z "$dirty" ]; then
    return
  fi

  unsafe=""
  while IFS= read -r line; do
    path="${line:3}"
    if [ -e "$ROOT/$path" ] && [ -e "$SOURCE/$path" ] && cmp -s "$ROOT/$path" "$SOURCE/$path"; then
      continue
    fi
    if [ ! -e "$ROOT/$path" ] && [ ! -e "$SOURCE/$path" ]; then
      continue
    fi
    unsafe+="$line"$'\n'
  done <<< "$dirty"

  if [ -n "$unsafe" ]; then
    cat >&2 <<EOF
Workspace has uncommitted changes that differ from the iCloud Vault source:
$unsafe

Sync is Vault -> Workspace only. Move those edits to the iCloud Obsidian Vault first,
or commit/stash/remove them before running this sync.
EOF
    exit 1
  fi
}

if [ ! -d "$SOURCE" ]; then
  cat >&2 <<EOF
Obsidian vault path not found:
  $SOURCE

Create publish/local.env from publish/local.env.example and set:
  OBSIDIAN_VAULT_PATH="/absolute/path/to/English-Word"
EOF
  exit 1
fi

guard_workspace_note_changes

for path in Roots Themes scripts index.md AGENTS.md RTK.md; do
  if [ -e "$SOURCE/$path" ]; then
    rsync -a --delete "$SOURCE/$path" "$DEST/"
  fi
done

echo "Synced Obsidian notes from iCloud vault to $DEST"
