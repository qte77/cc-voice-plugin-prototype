#!/usr/bin/env bats
# Tests for .github/scripts/create_pr.sh and delete_branch_pr_tag.sh

SCRIPT_DIR=".github/scripts"

# --- File existence and permissions ---

@test "create_pr.sh exists" {
  [[ -f "$SCRIPT_DIR/create_pr.sh" ]]
}

@test "delete_branch_pr_tag.sh exists" {
  [[ -f "$SCRIPT_DIR/delete_branch_pr_tag.sh" ]]
}

@test "create_pr.sh is executable" {
  [[ -x "$SCRIPT_DIR/create_pr.sh" ]]
}

@test "delete_branch_pr_tag.sh is executable" {
  [[ -x "$SCRIPT_DIR/delete_branch_pr_tag.sh" ]]
}

# --- create_pr.sh argument validation ---

@test "create_pr.sh fails with no args" {
  run bash "$SCRIPT_DIR/create_pr.sh"
  [[ "$status" -ne 0 ]]
}

@test "create_pr.sh fails with 1 arg" {
  run bash "$SCRIPT_DIR/create_pr.sh" main
  [[ "$status" -ne 0 ]]
}

@test "create_pr.sh fails with 4 args (needs 5)" {
  run bash "$SCRIPT_DIR/create_pr.sh" main bump-1 suffix 0.5.0
  [[ "$status" -ne 0 ]]
}

# --- create_pr.sh dry-run ---

@test "create_pr.sh dry-run shows gh pr create" {
  run env DRY_RUN=1 bash "$SCRIPT_DIR/create_pr.sh" main bump-42-main "[skip ci]" 0.5.0 0.6.0
  [[ "$status" -eq 0 ]]
  [[ "$output" == *"gh pr create"* ]]
}

@test "create_pr.sh dry-run uses correct base branch" {
  run env DRY_RUN=1 bash "$SCRIPT_DIR/create_pr.sh" main bump-42-main "[skip ci]" 0.5.0 0.6.0
  [[ "$output" == *"--base main"* ]]
}

@test "create_pr.sh dry-run uses correct head branch" {
  run env DRY_RUN=1 bash "$SCRIPT_DIR/create_pr.sh" main bump-42-main "[skip ci]" 0.5.0 0.6.0
  [[ "$output" == *"--head bump-42-main"* ]]
}

@test "create_pr.sh dry-run body contains version transition" {
  run env DRY_RUN=1 bash "$SCRIPT_DIR/create_pr.sh" main bump-42-main "[skip ci]" 0.5.0 0.6.0
  [[ "$output" == *"0.5.0"* ]]
  [[ "$output" == *"0.6.0"* ]]
}

# --- delete_branch_pr_tag.sh argument validation ---

@test "delete_branch_pr_tag.sh fails with no args" {
  run bash "$SCRIPT_DIR/delete_branch_pr_tag.sh"
  [[ "$status" -ne 0 ]]
}

@test "delete_branch_pr_tag.sh fails with 2 args (needs 3)" {
  run bash "$SCRIPT_DIR/delete_branch_pr_tag.sh" owner/repo bump-42
  [[ "$status" -ne 0 ]]
}

# --- delete_branch_pr_tag.sh dry-run ---

@test "delete_branch_pr_tag.sh dry-run references correct tag" {
  run env DRY_RUN=1 bash "$SCRIPT_DIR/delete_branch_pr_tag.sh" owner/repo bump-42-main 0.6.0
  [[ "$status" -eq 0 ]]
  [[ "$output" == *"v0.6.0"* ]]
}

@test "delete_branch_pr_tag.sh dry-run references correct branch" {
  run env DRY_RUN=1 bash "$SCRIPT_DIR/delete_branch_pr_tag.sh" owner/repo bump-42-main 0.6.0
  [[ "$output" == *"bump-42-main"* ]]
}

@test "delete_branch_pr_tag.sh dry-run includes git tag delete" {
  run env DRY_RUN=1 bash "$SCRIPT_DIR/delete_branch_pr_tag.sh" owner/repo bump-42-main 0.6.0
  [[ "$output" == *"git tag -d"* ]]
}

@test "delete_branch_pr_tag.sh dry-run includes pr close" {
  run env DRY_RUN=1 bash "$SCRIPT_DIR/delete_branch_pr_tag.sh" owner/repo bump-42-main 0.6.0
  [[ "$output" == *"gh pr close"* ]]
}

@test "delete_branch_pr_tag.sh dry-run includes branch API delete" {
  run env DRY_RUN=1 bash "$SCRIPT_DIR/delete_branch_pr_tag.sh" owner/repo bump-42-main 0.6.0
  [[ "$output" == *"gh api"* ]]
}

# --- Workflow YAML structure ---

@test "workflow has workflow_dispatch trigger" {
  grep -q "workflow_dispatch" .github/workflows/bump-my-version.yaml
}

@test "workflow has pull-requests write permission" {
  grep -q "pull-requests: write" .github/workflows/bump-my-version.yaml
}

@test "workflow references create_pr.sh" {
  grep -q "create_pr.sh" .github/workflows/bump-my-version.yaml
}

@test "workflow references delete_branch_pr_tag.sh" {
  grep -q "delete_branch_pr_tag.sh" .github/workflows/bump-my-version.yaml
}

@test "workflow creates ephemeral bump branch" {
  grep -q 'BRANCH_NEW.*bump-' .github/workflows/bump-my-version.yaml
}

@test "workflow does NOT push directly to main" {
  ! grep -q "git push --follow-tags" .github/workflows/bump-my-version.yaml
}
