# Create New Feature Branch

Create a new feature branch following the naming convention: `<github-username>/YYYY-MM-DD-HHMM`

## Steps

1. Stash any uncommitted changes
2. Switch to main and pull latest
3. Create new branch with timestamp
4. Push to origin
5. Restore stashed changes

## Command

```bash
# Get GitHub username
GITHUB_USER=$(gh api user --jq '.login' 2>/dev/null || git config user.name | tr '[:upper:]' '[:lower:]' | cut -d' ' -f1)

# Create timestamp
TIMESTAMP=$(date +"%Y-%m-%d-%H%M")

# Branch name
BRANCH_NAME="${GITHUB_USER}/${TIMESTAMP}"

# Stash changes
git stash push -m "Auto-stash before branch switch"

# Switch to main and update
git checkout main
git pull origin main

# Create and push new branch
git checkout -b "$BRANCH_NAME"
git push -u origin "$BRANCH_NAME"

# Restore stashed changes
git stash pop 2>/dev/null || true

echo "Created branch: $BRANCH_NAME"
```

## Example

If your GitHub username is `mccarthysean` and you run this on January 28, 2026 at 10:30 AM:
- Branch name: `mccarthysean/2026-01-28-1030`
