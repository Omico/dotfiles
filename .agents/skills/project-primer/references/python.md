# Python

Read before changing Python files in this repository.

## Verification

After changing Python files, run these commands from the repository root and fix every reported issue before completing the task:

```shell
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked basedpyright
```
