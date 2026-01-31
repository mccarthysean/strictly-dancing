Lint and format my Python code.

First, find and fix Python errors with the following:

```bash
cd /workspaces/strictly-dancing/backend
uv run ruff check --fix .
uv run ruff format .
```

Follow Python PEP 8 and use type hints.

Finally, commit changes.
