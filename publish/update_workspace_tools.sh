#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_BUILD=0

usage() {
  cat <<'EOF'
Usage: publish/update_workspace_tools.sh [--build]

Update only the Workspace repository tools and settings.

This script does not sync from the iCloud Obsidian vault and does not write to
the vault. Use it at the start of a new work session when another Mac may have
updated scripts, publish tooling, README, AGENTS.md, Quartz config, or GitHub
Actions.

Options:
  --build    Also run a Quartz build check after updating.
  -h, --help Show this help.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --build)
      RUN_BUILD=1
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

cd "$ROOT"

if [ ! -d .git ]; then
  echo "Not a git repository: $ROOT" >&2
  exit 1
fi

if [ -n "$(git status --short)" ]; then
  cat >&2 <<EOF
Workspace has local changes. Commit, stash, or inspect them before updating:

$(git status --short)
EOF
  exit 1
fi

git pull --ff-only

if compgen -G "scripts/*.py" > /dev/null; then
  python3 -m py_compile scripts/*.py
fi

if compgen -G "publish/*.sh" > /dev/null; then
  bash -n publish/*.sh
fi

if [ "$RUN_BUILD" -eq 1 ]; then
  cd "$ROOT/site"
  if [ ! -d node_modules ]; then
    npm ci
  fi
  npx quartz build -d ..
fi

cd "$ROOT"
echo "Workspace tools are up to date at $(git rev-parse --short HEAD)."
