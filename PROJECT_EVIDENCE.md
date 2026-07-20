# Project Evidence

This file records actual repository evidence verified locally through Phase 6. It does not
claim production deployment, private-platform integration, remote GitHub Actions success, or
HTTP support.

## Runtime

- Python used locally: `Python 3.13.3`
- FastMCP version: `3.4.4`
- Package version: `0.1.0`
- Docker version: `Docker version 28.3.3, build 980b856`
- Docker Compose version: `Docker Compose version v2.39.2-desktop.1`
- Docker engine: Docker Desktop Linux engine, server `28.3.3`, context `desktop-linux`,
  `OSType=linux`, `Architecture=x86_64`

## MCP Surface

Registered tools:

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

Implemented resource:

- Name: `server_info`
- URI: `workbench://server-info`

Transports genuinely supported by this project:

- `stdio`

Transport not implemented:

- HTTP and Streamable HTTP. FastMCP `3.4.4` supports HTTP transports, but this project has
  not added validated HTTP configuration, host/port policy, or HTTP smoke verification.

## Test And Quality Results

Commands actually run in Phase 6:

```powershell
git branch --show-current
git status --short
git diff --stat
git log --oneline -7
git stash list
docker --version
docker compose version
docker info --format '{{json .}}'
& $env:APPDATA\Python\Python313\Scripts\uv.exe sync --frozen --all-groups
& $env:APPDATA\Python\Python313\Scripts\uv.exe run ruff format --check .
& $env:APPDATA\Python\Python313\Scripts\uv.exe run ruff check .
& $env:APPDATA\Python\Python313\Scripts\uv.exe run mypy src
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest -rs
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest --cov=workbench_mcp --cov-report=term-missing
& $env:APPDATA\Python\Python313\Scripts\uv.exe build
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest tests\e2e\test_mcp_stdio.py
& $env:APPDATA\Python\Python313\Scripts\uv.exe run python --version
& $env:APPDATA\Python\Python313\Scripts\uv.exe run python -m workbench_mcp.server --version
& $env:APPDATA\Python\Python313\Scripts\uv.exe lock --check
docker build -t workbench-mcp:local .
docker image inspect workbench-mcp:local --format '{{.Id}} {{.Config.User}} {{json .Config.Entrypoint}} {{json .Config.Cmd}}'
docker run --rm --entrypoint python workbench-mcp:local -c "import os; print(os.geteuid())"
docker run --rm --entrypoint python workbench-mcp:local -c "import workbench_mcp, fastmcp; print(workbench_mcp.__version__); print(fastmcp.__version__)"
& $env:APPDATA\Python\Python313\Scripts\uv.exe run python scripts\run-container-smoke.py --image workbench-mcp:local
New-Item -ItemType Directory -Force .workbench-demo\workspace, .workbench-demo\artifacts | Out-Null
Set-Content -LiteralPath .workbench-demo\workspace\smoke.txt -Value "hello compose"
docker compose config
docker compose run --rm --build workbench-mcp-smoke
```

Actual results:

- Dependency sync: `Checked 84 packages in 22ms`
- Lockfile check: `Resolved 86 packages in 1ms`
- Ruff format check: `45 files already formatted`
- Ruff lint: `All checks passed!`
- mypy: `Success: no issues found in 28 source files`
- Full pytest suite: `87 items collected`, `83 passed, 4 skipped in 10.60s`
- Coverage run: `83 passed, 4 skipped in 18.81s`
- Coverage display: `83%`
- Statement coverage: `1074/1254` statements covered, `85.65%`
- Branch coverage: `200/274` branches covered, `72.99%`
- Package build: succeeded
- Built artifacts:
  - `dist\workbench_mcp-0.1.0.tar.gz`
  - `dist\workbench_mcp-0.1.0-py3-none-any.whl`
- Stdio smoke test: `tests/e2e/test_mcp_stdio.py` passed with `1 passed in 8.44s`
- Real MCP client/server E2E: `tests/e2e/test_mcp_stdio.py` starts
  `python -m workbench_mcp.server` with FastMCP `StdioTransport`, lists tools, and reads a
  workspace file through a real MCP client/server interaction.

## Skipped Tests

Exactly four tests skipped locally, all because this Windows environment lacks symlink
creation privilege (`WinError 1314`). The tests are not weakened or deleted and will execute
normally on Linux CI or Windows environments that permit symlink creation.

- `tests/security/test_artifact_service.py::test_rejects_artifact_symlink_escape`
- `tests/security/test_patching_security.py::test_apply_patch_rejects_symlink_escape`
- `tests/security/test_path_security.py::test_read_file_rejects_symlink_escape`
- `tests/security/test_path_security.py::test_list_files_rejects_symlink_directory_escape`

## Docker Evidence

- Docker build command: `docker build -t workbench-mcp:local .`
- Final local image tag: `workbench-mcp:local`
- Final local image ID after Compose rebuild:
  `sha256:7d9c3d91048921e816fae2e35cda6723e437384bd07cae808fd95b4bfc995786`
- Runtime user from image config: `10001:10001`
- Runtime entry point: `["workbench-mcp"]`
- Runtime command: `["--transport","stdio"]`
- Non-root verification command returned: `10001`
- Package import/version check inside container returned:
  - `workbench_mcp.__version__ == 0.1.0`
  - `fastmcp.__version__ == 3.4.4`
- Host-side container smoke command:
  `uv run python scripts\run-container-smoke.py --image workbench-mcp:local`
- Container smoke result: status `ok`; effective UID `10001`; expected MCP tools and
  `workbench://server-info` registered; mounted workspace read succeeded; read-only
  `apply_patch` was blocked; diagnostic artifact collection succeeded; artifact escape and
  workspace path escape were blocked.
- Compose validation command: `docker compose config`
- Compose smoke command: `docker compose run --rm --build workbench-mcp-smoke`
- Compose smoke result: status `ok` with the same MCP registration, non-root, read-only,
  artifact, and path-escape checks as the direct container smoke test.

## CI Evidence

Created workflow:

- `.github/workflows/ci.yml`

Configured checks:

- Checkout
- Python `3.13.3` setup
- uv `0.11.29` setup with dependency cache
- Locked dependency installation
- Lockfile consistency check
- Ruff format check
- Ruff lint
- mypy
- Full pytest suite with coverage, JUnit XML, coverage XML, and coverage HTML
- Explicit Linux execution of symlink security tests that skip locally on this Windows host
- Package build
- MCP stdio smoke test
- Docker image build
- Container smoke test
- Docker Compose configuration validation
- Docker Compose smoke workflow
- Test and coverage artifact upload

Remote GitHub Actions status has not been verified because the branch has not been pushed and
the workflow has not run on GitHub.

## Security Controls And Supporting Tests

- Workspace containment: `src/workbench_mcp/security/paths.py`;
  `tests/security/test_path_security.py`
- File size and binary detection: `src/workbench_mcp/security/limits.py`;
  `tests/unit/test_filesystem_services.py`, `tests/unit/test_search_service.py`
- Controlled patching: `src/workbench_mcp/services/patching.py`;
  `tests/unit/test_patching_service.py`, `tests/security/test_patching_security.py`
- Command allowlisting and argument-array execution: `src/workbench_mcp/security/commands.py`,
  `src/workbench_mcp/services/process_runner.py`; `tests/unit/test_process_runner.py`
- Output limits and timeouts: `src/workbench_mcp/services/process_runner.py`;
  `tests/unit/test_process_runner.py`
- Secret redaction: `src/workbench_mcp/security/redaction.py`,
  `src/workbench_mcp/tools/common.py`; `tests/unit/test_process_runner.py`,
  `tests/unit/test_mcp_server.py`
- Read-only Git status: `src/workbench_mcp/services/git_service.py`;
  `tests/unit/test_git_service.py`
- Artifact containment: `src/workbench_mcp/services/artifact_service.py`;
  `tests/security/test_artifact_service.py`, `tests/unit/test_mcp_server.py`
- Structured diagnostics: `src/workbench_mcp/services/diagnostics.py`;
  `tests/unit/test_diagnostics.py`
- MCP registration and stdio E2E: `src/workbench_mcp/server.py`,
  `src/workbench_mcp/tools/*.py`; `tests/unit/test_mcp_server.py`,
  `tests/e2e/test_mcp_stdio.py`
- Container smoke controls: `scripts/container-smoke-test.py`,
  `scripts/run-container-smoke.py`, `compose.yaml`

## Docker Security Decisions

- Digest-pinned `python:3.13.3-slim-bookworm` base image.
- `uv==0.11.29` installed in the build stage.
- Runtime dependencies installed from `uv.lock` with `uv sync --frozen --no-dev
  --no-editable`.
- Multi-stage build copies only the prepared virtual environment and container smoke script
  into the runtime stage.
- Non-root runtime user `10001:10001`.
- No Docker socket mount.
- No privileged mode.
- No host networking.
- No published HTTP port.
- Compose drops all Linux capabilities and uses `no-new-privileges:true`.
- Compose uses `read_only: true` plus tmpfs-backed `/tmp`.
- Workspace mount is read-only by default; artifact mount is explicitly writable.

## Known Limitations

- HTTP transport is not implemented or verified.
- Remote GitHub Actions execution is configured but not yet verified on GitHub.
- Reproducible demo automation remains for a later phase.
- Final documentation hardening remains for a later phase.
- Four symlink security tests skip on this Windows host due `WinError 1314`; they remain
  meaningful on systems where symlink creation is allowed and are explicitly run on Linux CI.
- The ignored `.workbench-demo` smoke directory may remain locally if cleanup is blocked by
  local command-safety policy; it is not included in Git or Docker build context.
