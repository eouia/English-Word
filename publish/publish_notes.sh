#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MESSAGE="${1:-Update notes}"

cd "$ROOT"
git pull --ff-only
publish/sync_from_icloud.sh

cd "$ROOT/site"
if [ ! -d node_modules ]; then
  npm ci
fi
npx quartz build

cd "$ROOT"
if git diff --quiet --exit-code && [ -z "$(git status --short)" ]; then
  echo "No changes to publish."
  exit 0
fi

git add .
git commit -m "$MESSAGE"
git push

echo "Published notes. GitHub Pages will deploy from the pushed commit."
