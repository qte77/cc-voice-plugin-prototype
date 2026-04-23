#!/bin/bash
# Create a PR for a version bump.
# Usage: create_pr.sh <base> <head> <title_suffix> <old_version> <new_version>
set -euo pipefail

if [[ $# -lt 5 ]]; then
  echo "Usage: $0 <base> <head> <title_suffix> <old_version> <new_version>" >&2
  exit 1
fi

base="$1"
head="$2"
title_suffix="$3"
old_version="$4"
new_version="$5"

pr_title="chore: bump version $old_version → $new_version $title_suffix"
pr_body="PR automatically created to bump from \`$old_version\` to \`$new_version\` on \`$head\`. Tag \`v$new_version\` will be created and must be deleted manually if PR is closed without merge."

if [[ "${DRY_RUN:-}" == "1" ]]; then
  echo "gh pr create --base $base --head $head --title \"$pr_title\" --body \"$pr_body\""
  exit 0
fi

gh pr create \
  --base "$base" \
  --head "$head" \
  --title "$pr_title" \
  --body "$pr_body"
