Push my recent commits to origin and create a draft pull request.

## Pre-PR Validation

Before creating the PR, run the full lint and build workflow:

### Step 1: Python Linting

```bash
cd /home/sean/git_wsl/strictly-dancing/backend
uv run ruff check --fix .
uv run ruff format .
```

### Step 2: TypeScript Build

```bash
cd /home/sean/git_wsl/strictly-dancing/frontend
bun run build
```

### Step 3: ESLint

```bash
cd /home/sean/git_wsl/strictly-dancing/frontend
bun run lint
```

### Step 4: Commit & Push Fixes

If any fixes were made during linting:

```bash
git add -A
git commit -m "chore: Fix lint and format issues"
git push
```

### Step 5: Create PR

```bash
gh pr create --draft --base main
```

Return the PR URL when done.
