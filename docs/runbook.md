# Runbook

Operational notes for local verification and release preparation.

## Preconditions

- Python compatible with `>=3.12,<3.14`.
- `uv` installed. In this Windows shell, use
  `$env:APPDATA\Python\Python313\Scripts\uv.exe` because bare `uv` is not on PATH.
- Git available on PATH for Git status tests and the public demo.
- Docker Desktop or Docker Engine available for container checks.

## Local Quality Checks

Standard command form:

```bash
uv sync --frozen --all-groups
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest -rs
uv run pytest --cov=workbench_mcp --cov-report=term-missing
uv build
uv run pytest tests/e2e/test_mcp_stdio.py
uv run python scripts/run-demo.py
```

Windows command prefix used in this repository verification:

```powershell
& $env:APPDATA\Python\Python313\Scripts\uv.exe run ruff check .
```

## Stdio Server

The project supports stdio only:

```bash
uv run workbench-mcp --transport stdio
```

This command starts a long-running MCP stdio server for an MCP client. For an automated
local smoke test, run:

```bash
uv run pytest tests/e2e/test_mcp_stdio.py
```

Do not configure HTTP ports for this project until HTTP configuration, binding policy, and
HTTP smoke tests are implemented.

## Public Demo

```bash
uv run python scripts/run-demo.py
```

The demo writes `artifacts/demo/workbench-demo-report.json`. It creates and removes a
temporary Git workspace; it does not require private credentials. The expected blocked
traversal attempt is recorded as a successful security check, not as a demo failure.

## Docker Build

```bash
docker build -t workbench-mcp:local .
docker image inspect workbench-mcp:local
```

The runtime image uses a digest-pinned `python:3.13.3-slim-bookworm` base, installs locked
runtime dependencies from `uv.lock`, and runs as UID/GID `10001:10001`.

## Container Smoke Test

```bash
uv run python scripts/run-container-smoke.py --image workbench-mcp:local
```

The helper creates temporary host mounts and starts the container with:

- read-only root filesystem
- tmpfs-backed `/tmp`
- all Linux capabilities dropped
- `no-new-privileges:true`
- no network
- read-only `/workspace` bind mount
- read-write `/artifacts` bind mount
- `READ_ONLY_MODE=true`

It verifies package import, configuration loading, server construction, expected tool
registration, server-information resource registration, non-root execution, workspace read
access, read-only write rejection, artifact collection, artifact escape rejection, and
workspace path escape rejection.

## Docker Compose Smoke

Linux/macOS shell:

```bash
mkdir -p .workbench-demo/workspace .workbench-demo/artifacts
printf 'hello compose\n' > .workbench-demo/workspace/smoke.txt
docker compose config
docker compose run --rm --build workbench-mcp-smoke
```

PowerShell mount preparation:

```powershell
New-Item -ItemType Directory -Force .workbench-demo\workspace, .workbench-demo\artifacts | Out-Null
Set-Content -LiteralPath .workbench-demo\workspace\smoke.txt -Value "hello compose"
docker compose config
docker compose run --rm --build workbench-mcp-smoke
```

The Compose workflow is a finite smoke command, not a persistent service. It publishes no
ports because this project does not implement HTTP transport.

The `.workbench-demo` directory is ignored by Git and excluded from Docker build context.

## Mount Permissions

On Linux, run bind-mounted smoke workflows with the current host UID/GID so generated
artifacts remain removable by the host cleanup process. The direct smoke helper does this
automatically on POSIX hosts. For Compose in CI or local Linux shells, set:

```bash
export WORKBENCH_MCP_CONTAINER_USER="$(id -u):$(id -g)"
```

Docker Desktop for Windows mediates bind-mount permissions differently. The smoke workflows
verify actual read/write behavior instead of assuming POSIX mode bits map exactly.

## CI

`.github/workflows/ci.yml` runs on Ubuntu 24.04 with Python `3.13.3` and uv `0.11.29`. It
installs locked dependencies, checks the lockfile, runs Ruff format/lint, mypy, pytest with
coverage, explicit Linux symlink security tests, package build, stdio MCP smoke test,
Docker build, direct container smoke, Compose config, and Compose smoke.

Remote evidence: GitHub Actions run `29775378084` completed successfully for commit
`4efddd89c8aed22310f3dc14a74ed1e215ec21e1` on branch `codex/workbench-mcp-v1`.

## Release Preparation Rules

- Do not merge into `main` during Phase 7.
- Do not create a Git tag or GitHub release during Phase 7.
- Do not publish a package or Docker image during Phase 7.
- Do not apply, drop, or delete existing stashes.
- Do not start the independent final audit until Phase 7 is committed.
