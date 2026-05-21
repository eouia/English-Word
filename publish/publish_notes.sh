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

  (
    cd "$SOURCE"
    python3 scripts/build_lexicon.py
    python3 scripts/link_theme_roots.py --write --list-ambiguous
    python3 scripts/build_theme_lexicon.py
  )
}

cd "$ROOT"
git pull --ff-only
prepare_vault
publish/sync_from_icloud.sh
python3 scripts/build_lexicon.py
python3 scripts/link_theme_roots.py --write --list-ambiguous
python3 scripts/build_theme_lexicon.py

cd "$ROOT/site"
if [ ! -d node_modules ]; then
  npm ci
fi
npx quartz build -d ..

cd "$ROOT"
if git diff --quiet --exit-code && [ -z "$(git status --short)" ]; then
  echo "No changes to publish."
  exit 0
fi

git add .
git commit -m "$MESSAGE"
git push

echo "Published notes. GitHub Pages will deploy from the pushed commit."
