# Ralph Wiggum Reference

Quick reference for PRD structure and naming conventions.

## PRD Schema

```json
{
  "id": "{YYYY-MM-DD}-{type}-{slug}",
  "metadata": {
    "title": "...",
    "type": "feature|bugfix|refactor|epic|spike",
    "github_issue": "https://github.com/.../issues/N",
    "github_issue_number": N
  },
  "completion": {
    "promise": "PLAN_COMPLETE",
    "criteria": [
      {"id": "CC01", "description": "...", "passes": false}
    ]
  },
  "tasks": [
    {
      "id": "T001",
      "title": "...",
      "passes": false,
      "phase": "discovery|design|implementation|testing|validation",
      "dependencies": [],
      "acceptance_criteria": [
        {"id": "AC01", "criterion": "...", "met": false}
      ]
    }
  ],
  "worktree": {
    "enabled": true,
    "name": "worktree1",
    "path": "/project/worktrees/worktree1",
    "branch": "ralph/worktree1-{YYYYMMDD}-{slug}",
    "ports": {"fastapi": N, "vite": N, "flask": N}
  }
}
```

## Naming Convention

| Type | Example |
|------|---------|
| feature | `2026-01-09-feature-user-dashboard` |
| bugfix | `2026-01-09-bugfix-auth-timeout` |
| refactor | `2026-01-09-refactor-api-format` |
| epic | `2026-01-09-epic-auth-overhaul` |
| spike | `2026-01-09-spike-graphql` |

## ID Formats

- **Tasks**: T001, T002, T003...
- **Acceptance Criteria**: AC01, AC02...
- **Completion Criteria**: CC01, CC02...

## Templates

- `/project/ralph/_templates/feature-prd.template.json`
- `/project/ralph/_templates/bugfix-prd.template.json`
- `/project/ralph/_templates/prd.schema.json`

## Full Documentation

See `SKILL.md` in this directory.
