#!/usr/bin/env bash
# Usage:
#   ./git-auto-commit.sh                    # prompts for a commit message
#   ./git-auto-commit.sh "Fast commit msg"  # message provided via argument
#
# Stages all tracked changes, commits them, and pushes to origin/main.

set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "✗ Not inside a Git repository"
  exit 1
}

cd "$repo_root"

echo "Current changes:"
git status --short

if [ -n "${1:-}" ]; then
  commit_msg="$1"
else
  read -rp "Commit message: " commit_msg
fi

git add -A
git commit -m "$commit_msg"
git push origin main
