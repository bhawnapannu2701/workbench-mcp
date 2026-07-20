# workbench-mcp

Secure FastMCP server for controlled repository inspection, file operations, test execution
and workspace diagnostics.

This is a public portfolio/open-source project. It is not a private platform integration.

## Current Scope

The current implementation exposes the real FastMCP server surface over the secure service
layer and has completed local Phase 6 testing, security review, coverage measurement,
package build, stdio MCP smoke verification, Docker packaging, container smoke testing, and
Docker Compose smoke testing. Only stdio transport is implemented and verified. Streamable
HTTP is supported by the installed FastMCP package, but it is not enabled in this project yet.

## MCP Surface

Resource:

- `workbench://server-info`

Tools:

- `workspace_info`
- `list_files`
- `read_file`
- `search_text`
- `apply_patch`
- `run_command`
- `run_tests`
- `git_status`
- `collect_artifact`
- `diagnose_workspace`

## Verified Phase 4 Commands

This Windows verification shell did not have bare `uv` on `PATH`, so `uv` was invoked from
the Python user scripts directory:

```powershell
& $env:APPDATA\Python\Python313\Scripts\uv.exe run python --version
& $env:APPDATA\Python\Python313\Scripts\uv.exe run python -m workbench_mcp.server --version
& $env:APPDATA\Python\Python313\Scripts\uv.exe run workbench-mcp --version
& $env:APPDATA\Python\Python313\Scripts\uv.exe run ruff format --check .
& $env:APPDATA\Python\Python313\Scripts\uv.exe run ruff check .
& $env:APPDATA\Python\Python313\Scripts\uv.exe run mypy src
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest tests/unit/test_mcp_server.py tests/e2e/test_mcp_stdio.py
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest tests/unit tests/security tests/e2e
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest tests/e2e/test_mcp_stdio.py
```

The stdio E2E test starts `python -m workbench_mcp.server` through FastMCP's
`StdioTransport`, lists registered tools, and reads a workspace file through a real MCP
client/server interaction.

## Verified Phase 5 Commands

```powershell
& $env:APPDATA\Python\Python313\Scripts\uv.exe run ruff format --check .
& $env:APPDATA\Python\Python313\Scripts\uv.exe run ruff check .
& $env:APPDATA\Python\Python313\Scripts\uv.exe run mypy src
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest --cov=workbench_mcp --cov-report=term-missing
& $env:APPDATA\Python\Python313\Scripts\uv.exe build
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest tests/e2e/test_mcp_stdio.py
```

Latest measured results:

- Full pytest suite: `83 passed, 4 skipped`
- Coverage display: `83%`
- Statement coverage: `1074/1254`
- Branch coverage: `200/274`
- Package build: `dist\workbench_mcp-0.1.0.tar.gz` and
  `dist\workbench_mcp-0.1.0-py3-none-any.whl`

## Docker Quick Start

The container defaults to stdio transport, read-only workspace mode, a non-root runtime user,
and no published HTTP port.

```powershell
docker build -t workbench-mcp:local .
docker run --rm --entrypoint python workbench-mcp:local -c "import os; print(os.geteuid())"
& $env:APPDATA\Python\Python313\Scripts\uv.exe run python scripts\run-container-smoke.py --image workbench-mcp:local
```

To run the Compose smoke workflow:

```powershell
New-Item -ItemType Directory -Force .workbench-demo\workspace, .workbench-demo\artifacts | Out-Null
Set-Content -LiteralPath .workbench-demo\workspace\smoke.txt -Value "hello compose"
docker compose config
docker compose run --rm --build workbench-mcp-smoke
```

Compose mounts `.workbench-demo/workspace` read-only at `/workspace` and
`.workbench-demo/artifacts` read-write at `/artifacts`. It runs without a published port,
without host networking, without the Docker socket, with all Linux capabilities dropped, and
with `no-new-privileges:true`.

On Linux hosts, ensure the artifact mount is writable by UID/GID `10001` or mode-compatible
with that user. On Docker Desktop for Windows, bind-mount permission behavior is mediated by
Docker Desktop; the Phase 6 smoke workflow verifies the artifact directory can be written by
the container before reporting success.

Verified local Phase 6 container results:

- Docker build: succeeded for `workbench-mcp:local`
- Runtime user: `10001:10001`
- Container smoke: status `ok`
- Compose config: passed
- Compose smoke workflow: status `ok`

## CI

`.github/workflows/ci.yml` is configured for `pull_request` and pushes to `main` or
`codex/**`. It installs locked dependencies with uv, runs Ruff format/lint, mypy, the full
pytest suite with coverage, explicit Linux symlink security tests, package build, stdio MCP
smoke tests, Docker image build, container smoke tests, and Compose validation. Remote
GitHub Actions execution has not been verified yet.

## Known Limitations

- HTTP transport is not implemented or verified yet.
- Remote GitHub Actions status is not verified until the workflow is pushed and run on
  GitHub.
- Reproducible demo automation remains for a later phase.
- Some symlink escape tests are skipped on this Windows machine when symlink creation fails
  with `WinError 1314`; they remain active for environments where symlinks are permitted.
