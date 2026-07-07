#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MESSAGE="${1:-Update notes}"
CONFIG="$ROOT/publish/local.env"

if [ -f "$CONFIG" ]; then
  # shellcheck disable=SC1090
  source "$CONFIG"
fi

SOURCE="${OBSIDIAN_VAULT_PATH:-$HOME/Library/Mobile Documents/com~apple~CloudDocs/Obsidian/MyObsidian/English-Word}"
VAULT_SYNC_PATHS=(Roots Themes index.md AGENTS.md RTK.md)

guard_workspace_note_changes() {
  local dirty unsafe line path
  dirty="$(git status --porcelain -- "${VAULT_SYNC_PATHS[@]}")"
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

Edit the iCloud Obsidian Vault first, or copy these exact changes there, then rerun this script.
This guard prevents Workspace edits from being overwritten by Vault -> Workspace sync.
EOF
    exit 1
  fi
}

prepare_vault() {
  if [ ! -d "$SOURCE" ]; then
    cat >&2 <<EOF
Obsidian vault path not found:
  $SOURCE

Create publish/local.env from publish/local.env.example and set:
  OBSIDIAN_VAULT_PATH="/absolute/path/to/English-Word"
EOF
    exit 1
  fi

  ENGLISH_WORD_ROOT="$SOURCE" python3 "$ROOT/scripts/build_lexicon.py"
  ENGLISH_WORD_ROOT="$SOURCE" python3 "$ROOT/scripts/link_theme_roots.py" --write --list-ambiguous
  ENGLISH_WORD_ROOT="$SOURCE" python3 "$ROOT/scripts/build_theme_lexicon.py"
}

build_site() {
  cd "$ROOT/site"
  export npm_config_cache="${NPM_CONFIG_CACHE:-$ROOT/.npm-cache}"
  export npm_config_update_notifier=false

  if [ ! -d node_modules ]; then
    npm ci
  fi

  npm run quartz -- build -d ..
}

push_changes() {
  local branch origin_url repo_path ssh_url

  branch="$(git branch --show-current)"
  if git push; then
    return
  fi

  origin_url="$(git remote get-url origin || true)"
  if [[ "$origin_url" =~ ^https://github.com/(.+)\.git$ ]]; then
    repo_path="${BASH_REMATCH[1]}"
    ssh_url="git@github.com:${repo_path}.git"
    echo "git push via origin failed; retrying via SSH: $ssh_url"
    git push "$ssh_url" "$branch"
    git fetch origin "$branch"
    return
  fi

  return 1
}

cd "$ROOT"
guard_workspace_note_changes
git pull --ff-only
prepare_vault
publish/sync_from_icloud.sh --no-guard
build_site

cd "$ROOT"
if git diff --quiet --exit-code && [ -z "$(git status --short)" ]; then
  echo "No changes to publish."
  exit 0
fi

git add .
git commit -m "$MESSAGE"
push_changes

echo "Published notes. GitHub Pages will deploy from the pushed commit."
