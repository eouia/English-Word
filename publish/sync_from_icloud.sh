#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$ROOT/publish/local.env"
RUN_GUARD=1

usage() {
  cat <<'EOF'
Usage: publish/sync_from_icloud.sh [--no-guard]

Sync Obsidian vault content from iCloud into the Workspace repo.

Options:
  --no-guard  Skip the Workspace-vs-vault dirty-file guard. Use only from
              publish/publish_notes.sh after its initial guard has passed.
  -h, --help  Show this help.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --no-guard)
      RUN_GUARD=0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [ -f "$CONFIG" ]; then
  # shellcheck disable=SC1090
  source "$CONFIG"
fi

SOURCE="${OBSIDIAN_VAULT_PATH:-$HOME/Library/Mobile Documents/com~apple~CloudDocs/Obsidian/MyObsidian/English-Word}"
DEST="$ROOT"
VAULT_SYNC_PATHS=(Roots Themes index.md AGENTS.md RTK.md)

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

if [ "$RUN_GUARD" -eq 1 ]; then
  guard_workspace_note_changes
fi

for path in "${VAULT_SYNC_PATHS[@]}"; do
  if [ -e "$SOURCE/$path" ]; then
    rsync -a --delete "$SOURCE/$path" "$DEST/"
  fi
done

echo "Synced Obsidian notes from iCloud vault to $DEST"
