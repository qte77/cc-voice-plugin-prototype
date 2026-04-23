#!/bin/bash
# Cleanup on bump failure: delete tag, close PR, delete branch.
# Usage: delete_branch_pr_tag.sh <repo> <branch> <version>
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <repo> <branch> <version>" >&2
  exit 1
fi

repo="$1"
branch="$2"
tag_to_delete="v$3"
branch_del_api="repos/$repo/git/refs/heads/$branch"
close_msg="Closing PR '$branch' to rollback after failure"

if [[ "${DRY_RUN:-}" == "1" ]]; then
  echo "git tag -d $tag_to_delete"
  echo "gh pr close $branch --comment \"$close_msg\""
  echo "gh api $branch_del_api -X DELETE"
  echo "Cleanup: tag=$tag_to_delete branch=$branch"
  exit 0
fi

echo "Deleting tag $tag_to_delete"
git tag -d "$tag_to_delete" 2>/dev/null || true

echo "Closing PR for $branch"
gh pr close "$branch" --comment "$close_msg" 2>/dev/null || true

echo "Deleting branch $branch"
gh api "$branch_del_api" -X DELETE 2>/dev/null && \
  echo "Branch deleted." || echo "Branch deletion failed (may not exist)."
