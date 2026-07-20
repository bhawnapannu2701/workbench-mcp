# Runbook

Operational notes for running and verifying `workbench-mcp` locally.

## Local Checks

Use the project-managed uv environment:

```powershell
& $env:APPDATA\Python\Python313\Scripts\uv.exe sync --frozen --all-groups
& $env:APPDATA\Python\Python313\Scripts\uv.exe run ruff format --check .
& $env:APPDATA\Python\Python313\Scripts\uv.exe run ruff check .
& $env:APPDATA\Python\Python313\Scripts\uv.exe run mypy src
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest -rs
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest --cov=workbench_mcp --cov-report=term-missing
& $env:APPDATA\Python\Python313\Scripts\uv.exe build
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest tests\e2e\test_mcp_stdio.py
```

## Stdio Server

The project currently supports and verifies stdio transport only:

```powershell
& $env:APPDATA\Python\Python313\Scripts\uv.exe run workbench-mcp --transport stdio
```

Do not configure HTTP ports for this project until HTTP configuration, binding policy, and
smoke tests are implemented.

## Docker Build

Build the local runtime image:

```powershell
docker build -t workbench-mcp:local .
docker image inspect workbench-mcp:local
```

The runtime image uses a digest-pinned `python:3.13.3-slim-bookworm` base, installs runtime
dependencies from `uv.lock`, and runs as UID/GID `10001:10001`.

## Container Smoke Test

Run the host-side smoke helper:

```powershell
& $env:APPDATA\Python\Python313\Scripts\uv.exe run python scripts\run-container-smoke.py --image workbench-mcp:local
```

The helper creates a temporary workspace and artifact directory, then starts the container
with:

- read-only root filesystem
- tmpfs-backed `/tmp`
- all Linux capabilities dropped
- `no-new-privileges:true`
- no network
- read-only `/workspace` bind mount
- read-write `/artifacts` bind mount
- `READ_ONLY_MODE=true`

The container-local smoke script verifies package import, configuration loading, FastMCP
server construction, expected tool registration, server-information resource registration,
non-root execution, workspace read access, read-only write rejection, artifact collection,
artifact escape rejection, and workspace path escape rejection.

## Docker Compose Smoke

Prepare local demo mounts and run the Compose smoke service:

```powershell
New-Item -ItemType Directory -Force .workbench-demo\workspace, .workbench-demo\artifacts | Out-Null
Set-Content -LiteralPath .workbench-demo\workspace\smoke.txt -Value "hello compose"
docker compose config
docker compose run --rm --build workbench-mcp-smoke
```

The Compose workflow is a finite smoke command, not a persistent web service. It publishes
no ports because the project does not implement HTTP transport.

The `.workbench-demo` directory is ignored by Git and excluded from Docker build context.
Remove it only when no smoke workflow is using it.

## Mount Permissions

On Linux, run bind-mounted smoke workflows with the current host UID/GID so generated
artifacts remain removable by the host cleanup process. The direct smoke helper does this
automatically on POSIX hosts. For Compose, set
`WORKBENCH_MCP_CONTAINER_USER="$(id -u):$(id -g)"` when using host bind mounts. The workspace
mount should normally be read-only.

On Docker Desktop for Windows, bind-mount permissions are mediated by Docker Desktop. The
smoke workflows verify the effective read/write behavior rather than assuming POSIX mode
bits map exactly.

## CI

The GitHub Actions workflow runs on Ubuntu and executes the symlink security tests that may
skip locally on this Windows host due `WinError 1314`. The workflow requires no secrets and
uses `contents: read` permissions. Remote GitHub Actions status after the container-smoke
ownership fix is not yet verified.
