# Contributing

## Setup

Use the locked uv environment:

```bash
uv sync --frozen --all-groups
uv run python --version
uv run workbench-mcp --version
```

If `uv` is not on PATH in PowerShell, use the installed `uv.exe` path for the same commands.

## Development Rules

- Keep modules small, typed, and testable.
- Keep configuration, security checks, services, MCP registration, and transport startup
  separate.
- Do not add unrestricted command execution.
- Do not use `shell=True`.
- Do not access files outside configured workspace or artifact roots.
- Validate paths with resolved containment checks.
- Keep `READ_ONLY_MODE=true` as the safe default.
- Do not document a feature until it is implemented and verified.
- Do not claim HTTP support unless this project adds and tests it.
- Do not commit real secrets.

## Checks Before Commit

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest -rs
uv run pytest --cov=workbench_mcp --cov-report=term-missing
uv build
uv run pytest tests/e2e/test_mcp_stdio.py
uv run python scripts/run-demo.py
```

When Docker is available:

```bash
docker build -t workbench-mcp:local .
uv run python scripts/run-container-smoke.py --image workbench-mcp:local
docker compose config
docker compose run --rm --build workbench-mcp-smoke
```

## Documentation

Public docs must be evidence based. If a command was not run, say so. If a feature is
deferred, mark it as deferred. Do not add production deployment claims, private platform
compatibility claims, invented metrics, fake success statements, or placeholder
implementations.

## Tests

Use temporary directories for filesystem, Git, artifact, Docker-mount, and demo tests. Do
not modify unrelated developer files. Tests may skip symlink-specific cases only when the
host OS denies symlink creation.

## Release Preparation

For `v0.1.0`, follow [docs/release-checklist-v0.1.0.md](docs/release-checklist-v0.1.0.md).
Phase 7 prepares release documentation and evidence only; it does not merge, tag, publish,
or start the independent final audit.
