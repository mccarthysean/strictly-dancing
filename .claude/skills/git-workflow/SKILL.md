---
name: Git Workflow
description: Manage Git workflows with branch creation, commits, and pull requests. Create feature branches, write commit messages, generate PRs, and follow git best practices. Use when creating branches, committing changes, making PRs, or handling version control.
allowed-tools: [Bash, Read]
---

# Git Workflow Skill

## Purpose
Manage Git workflows including feature branches, commits, and pull requests for the Strictly Dancing project.

## When to Use This Skill
- Creating feature branches
- Committing code changes
- Creating pull requests
- Branch management
- Git workflow management

## Feature Branch Workflow

### Create New Feature Branch
```bash
# Get GitHub username
GITHUB_USER=$(gh api user --jq '.login' 2>/dev/null || git config user.name | tr '[:upper:]' '[:lower:]' | cut -d' ' -f1)
TIMESTAMP=$(date +"%Y-%m-%d-%H%M")
BRANCH_NAME="${GITHUB_USER}/${TIMESTAMP}"

# Create and push branch
git stash push -m "Auto-stash before branch switch"
git checkout main && git pull origin main
git checkout -b "$BRANCH_NAME"
git push -u origin "$BRANCH_NAME"
git stash pop 2>/dev/null || true
```

### Branch Naming Convention
```
feature/<description>    # New features
bugfix/<description>     # Bug fixes
hotfix/<description>     # Urgent production fixes
```

## Commit Workflow

### Standard Commit Process
```bash
# 1. Check status
git status

# 2. Review changes
git diff

# 3. Stage files
git add <files>

# 4. Commit with descriptive message
git commit -m "feat: Add host profile search

Implements search with location and dance style filters.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Commit Message Format
```
<type>: <subject>

<body>

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `docs`: Documentation
- `test`: Tests
- `chore`: Maintenance
- `perf`: Performance improvements

### Using Heredoc for Commits
```bash
git commit -m "$(cat <<'EOF'
feat: Add host profile search

Implements search with location and dance style filters.

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Pre-Commit Checklist

### Code Quality
```bash
# Python linting
cd /home/sean/git_wsl/strictly-dancing/backend
uv run ruff check --fix .
uv run ruff format .

# TypeScript checks
cd /home/sean/git_wsl/strictly-dancing/frontend
bun run build
bun run lint
```

### Type Generation
```bash
# If FastAPI changes were made
cd /home/sean/git_wsl/strictly-dancing/frontend
bun run generate-types
```

## Pull Request Creation

### Using GitHub CLI
```bash
gh pr create --draft --title "Add host profile search" --body "$(cat <<'EOF'
## Summary
- Implement host search with location filter
- Add dance style filtering
- Connect to FastAPI endpoint

## Test Plan
- [ ] Verify search loads results
- [ ] Test location radius filter
- [ ] Test dance style filter

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Common Git Operations

### Update from Main
```bash
git checkout main
git pull origin main
git checkout feature/my-feature
git merge main
```

### Stash Changes
```bash
git stash save "WIP: description"
git stash list
git stash pop
```

### View History
```bash
git log --oneline -10
git log --graph --oneline --all
```

## Best Practices

1. **Commit often**: Small, focused commits
2. **Write clear messages**: Describe why, not what
3. **Test before commit**: Run linters and tests
4. **Review changes**: Use `git diff` before committing
5. **Pull before push**: Keep branch updated
6. **Use feature branches**: Never commit directly to main
7. **Delete merged branches**: Clean up after PR merge

## Integration
This skill automatically activates when:
- Creating feature branches
- Committing code changes
- Creating pull requests
- Managing git workflows
