# Project Evidence

This file records actual evidence for `workbench-mcp` Phase 7. It does not claim HTTP
support, production deployment, package publishing, Docker image publishing, private
platform integration, Git tags, GitHub releases, or completion of the independent final
audit.

## Runtime

- Local Python: `Python 3.13.3`
- Local uv: `uv 0.11.29 (901092ee1 2026-07-15 x86_64-pc-windows-msvc)`
- Package version: `0.1.0`
- Local FastMCP import: `3.4.4`
- Docker: `Docker version 28.3.3, build 980b856`
- Docker Compose: `Docker Compose version v2.39.2-desktop.1`
- Docker engine after recovery: `28.3.3 linux x86_64`
- Local branch at start of Phase 7: `codex/workbench-mcp-v1`
- Upstream branch: `origin/codex/workbench-mcp-v1`

## MCP Surface

Exact registered tools:

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

Exact registered resource:

- Name: `server_info`
- URI: `workbench://server-info`
- MIME type: `application/json`

Supported transport in this project:

- `stdio`

Not implemented:

- HTTP and Streamable HTTP. This project has no validated HTTP configuration, host/port
  policy, authentication policy, or HTTP smoke verification.

## Source And Test Mapping

| Behavior | Source | Tests/evidence |
| --- | --- | --- |
| Configuration loading and validation | `src/workbench_mcp/config.py` | `tests/unit/test_config.py` |
| Workspace path containment | `src/workbench_mcp/security/paths.py` | `tests/security/test_path_security.py` |
| File size, binary detection, output truncation | `src/workbench_mcp/security/limits.py` | `tests/unit/test_filesystem_services.py`, `tests/unit/test_search_service.py`, `tests/unit/test_process_runner.py` |
| Command validation | `src/workbench_mcp/security/commands.py` | `tests/unit/test_config.py`, `tests/unit/test_process_runner.py` |
| Redaction | `src/workbench_mcp/security/redaction.py`, `src/workbench_mcp/tools/common.py` | `tests/unit/test_process_runner.py`, `tests/unit/test_mcp_server.py` |
| Filesystem listing and reads | `src/workbench_mcp/services/filesystem.py` | `tests/unit/test_filesystem_services.py` |
| Text search | `src/workbench_mcp/services/search.py` | `tests/unit/test_search_service.py` |
| Controlled patching | `src/workbench_mcp/services/patching.py` | `tests/unit/test_patching_service.py`, `tests/security/test_patching_security.py` |
| Subprocess execution | `src/workbench_mcp/services/process_runner.py` | `tests/unit/test_process_runner.py` |
| Predefined tests | `src/workbench_mcp/services/test_runner.py` | `tests/unit/test_test_runner.py`, `tests/unit/test_mcp_server.py` |
| Read-only Git status | `src/workbench_mcp/services/git_service.py` | `tests/unit/test_git_service.py`, `tests/unit/test_mcp_server.py` |
| Artifact collection | `src/workbench_mcp/services/artifact_service.py` | `tests/security/test_artifact_service.py`, `tests/unit/test_mcp_server.py` |
| Diagnostics | `src/workbench_mcp/services/diagnostics.py` | `tests/unit/test_diagnostics.py`, `tests/unit/test_mcp_server.py` |
| MCP registration and stdio | `src/workbench_mcp/server.py`, `src/workbench_mcp/tools/*.py` | `tests/unit/test_mcp_server.py`, `tests/e2e/test_mcp_stdio.py` |
| Public demo | `scripts/run-demo.py` | `tests/e2e/test_public_demo.py`, `uv run python scripts/run-demo.py` |
| Container smoke | `scripts/container-smoke-test.py`, `scripts/run-container-smoke.py`, `Dockerfile`, `compose.yaml` | `tests/unit/test_run_container_smoke.py`, direct container smoke, Compose smoke |

## Local Verification Commands

Because bare `uv` is not on PATH in this Windows shell, local verification used
`$env:APPDATA\Python\Python313\Scripts\uv.exe`.

Commands actually run:

```powershell
git branch --show-current
git status --short
git log --oneline -8
git stash list
git remote -v
git branch -vv
git rev-parse --abbrev-ref --symbolic-full-name '@{u}'
git rev-parse '4efddd8^{commit}'
git ls-remote --heads origin codex/workbench-mcp-v1
gh run view 29775378084 --json databaseId,headSha,status,conclusion,createdAt,updatedAt,event,url,jobs
& $env:APPDATA\Python\Python313\Scripts\uv.exe sync --frozen --all-groups
& $env:APPDATA\Python\Python313\Scripts\uv.exe lock --check
& $env:APPDATA\Python\Python313\Scripts\uv.exe --version
& $env:APPDATA\Python\Python313\Scripts\uv.exe run python --version
& $env:APPDATA\Python\Python313\Scripts\uv.exe run python -c "import fastmcp, workbench_mcp; print(workbench_mcp.__version__); print(fastmcp.__version__)"
& $env:APPDATA\Python\Python313\Scripts\uv.exe run workbench-mcp --version
& $env:APPDATA\Python\Python313\Scripts\uv.exe run python -m workbench_mcp.server --version
& $env:APPDATA\Python\Python313\Scripts\uv.exe run ruff format --check .
& $env:APPDATA\Python\Python313\Scripts\uv.exe run ruff check .
& $env:APPDATA\Python\Python313\Scripts\uv.exe run mypy src
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest -rs
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest --cov=workbench_mcp --cov-report=term-missing
& $env:APPDATA\Python\Python313\Scripts\uv.exe run coverage json -o artifacts\coverage\coverage.json
& $env:APPDATA\Python\Python313\Scripts\uv.exe build
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest tests\unit\test_mcp_server.py::test_server_startup_succeeds -q
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest tests\e2e\test_mcp_stdio.py -q
& $env:APPDATA\Python\Python313\Scripts\uv.exe run python scripts\run-demo.py
docker --version
docker compose version
docker info --format '{{.ServerVersion}} {{.OSType}} {{.Architecture}}'
docker build --progress=plain -t workbench-mcp:local .
docker image inspect workbench-mcp:local --format '{{.Id}} {{.Config.User}} {{json .Config.Entrypoint}} {{json .Config.Cmd}}'
docker run --rm --entrypoint python workbench-mcp:local -c "import os; print(os.geteuid())"
docker run --rm --entrypoint python workbench-mcp:local -c "import workbench_mcp, fastmcp; print(workbench_mcp.__version__); print(fastmcp.__version__)"
& $env:APPDATA\Python\Python313\Scripts\uv.exe run python scripts\run-container-smoke.py --image workbench-mcp:local
New-Item -ItemType Directory -Force .workbench-demo\workspace, .workbench-demo\artifacts | Out-Null
Set-Content -LiteralPath .workbench-demo\workspace\smoke.txt -Value "hello compose"
docker compose config
docker compose run --rm --build workbench-mcp-smoke
rg -n -S "TODO|FIXME|placeholder|mocked success|unsupported HTTP references|unsupported HTTP|Mercor|RL Studio|production deployment|hardcoded secrets" .
rg -n -S "password|token|api[_-]?key|secret|PRIVATE KEY|BEGIN .* KEY|gho_|github_pat|sk-[A-Za-z0-9]" .
```

## Quality Results

- Dependency sync: `Checked 84 packages in 19ms`
- Lockfile check: `Resolved 86 packages in 3ms`
- Ruff format: `48 files already formatted`
- Ruff lint: `All checks passed!`
- mypy: `Success: no issues found in 28 source files`
- Full pytest suite: `93 items collected`, `89 passed, 4 skipped in 15.75s`
- Coverage command: `89 passed, 4 skipped in 17.03s`
- Coverage display: `84%`
- Covered statements/lines: `1076/1254`
- Statement coverage: `85.8054226475279%` (`86` display)
- Covered branches: `202/274`
- Branch coverage: `73.72262773722628%` (`74` display)
- Package build: succeeded
- Built artifacts:
  - `dist\workbench_mcp-0.1.0.tar.gz`
  - `dist\workbench_mcp-0.1.0-py3-none-any.whl`

## Skipped Tests On Windows

Exactly four tests skipped locally because this Windows environment denied symlink creation
with `WinError 1314`.

- `tests/security/test_artifact_service.py::test_rejects_artifact_symlink_escape`
- `tests/security/test_patching_security.py::test_apply_patch_rejects_symlink_escape`
- `tests/security/test_path_security.py::test_read_file_rejects_symlink_escape`
- `tests/security/test_path_security.py::test_list_files_rejects_symlink_directory_escape`

The tests remain active where symlink creation is available.

## Linux Symlink Test Result

Remote GitHub Actions run `29775378084` completed the step
`Run symlink security tests explicitly on Linux` successfully for commit
`4efddd89c8aed22310f3dc14a74ed1e215ec21e1`.

## MCP Results

- Construction smoke command:
  `uv run pytest tests\unit\test_mcp_server.py::test_server_startup_succeeds -q`
- Construction smoke result: `1 passed in 6.65s`
- Real stdio MCP client/server command:
  `uv run pytest tests\e2e\test_mcp_stdio.py -q`
- Real stdio MCP client/server result after serial rerun: `1 passed in 4.07s`
- The stdio E2E test starts `python -m workbench_mcp.server` through FastMCP
  `StdioTransport`, lists tools, and reads a workspace file through a real MCP
  client/server interaction.

## Demo Result

- Command: `uv run python scripts\run-demo.py`
- Result: `Demo status: ok`
- JSON report: `artifacts/demo/workbench-demo-report.json`
- Reported tools: all ten expected MCP tools.
- Approved test: `passed`
- Controlled patch: `docs/guide.txt changed=True`
- Expected blocked operation: `read_file {'relative_path': '../outside.txt'}`
- Cleanup: temporary demo workspace removed.

## Docker Evidence

Docker Desktop initially became unhealthy during Phase 7 verification. The first Docker
build attempt hit the local command timeout, and Docker then returned API 500 errors until
the Docker Desktop/WSL engine was restarted. This environment failure and recovery are
documented in `docs/debugging.md` and `docs/failure-catalog.md`.

After recovery:

- Docker engine probe: `28.3.3 linux x86_64`
- Docker build command: `docker build --progress=plain -t workbench-mcp:local .`
- Docker build result: succeeded
- Final local image ID after Compose rebuild:
  `sha256:4182951e671d2f982b96afaf112535fdf41b6ec1d4d6550e5ec12335d8254d6d`
- Runtime user from image config: `10001:10001`
- Runtime entry point: `["workbench-mcp"]`
- Runtime command: `["--transport","stdio"]`
- Non-root verification: `10001`
- Container package import/version check:
  - `workbench_mcp.__version__ == 0.1.0`
  - `fastmcp.__version__ == 3.4.4`
- Direct container smoke result: JSON status `ok`
- Container smoke verified expected tools, `workbench://server-info`, non-root execution,
  workspace read access, read-only patch blocking, diagnostic artifact collection, artifact
  escape blocking, and workspace path escape blocking.
- Compose config result: passed
- Compose smoke result: JSON status `ok`

## Remote CI Evidence

- Workflow: `.github/workflows/ci.yml`
- Run ID: `29775378084`
- Run URL: `https://github.com/bhawnapannu2701/workbench-mcp/actions/runs/29775378084`
- Branch: `codex/workbench-mcp-v1`
- Event: `push`
- Head SHA: `4efddd89c8aed22310f3dc14a74ed1e215ec21e1`
- Status: `completed`
- Conclusion: `success`
- Created: `2026-07-20T20:15:36Z`
- Updated: `2026-07-20T20:16:47Z`
- Job: `Verify package, security tests, and containers`
- Job conclusion: `success`

Successful remote steps included locked dependency installation, lockfile check, Ruff
format/lint, mypy, tests with coverage, explicit Linux symlink security tests, package
build, MCP stdio smoke, Docker image build, container smoke, Compose config, and Compose
smoke workflow.

## Documentation And Search Audit

Repository searches were run for:

- `TODO`
- `FIXME`
- `placeholder`
- `mocked success`
- unsupported HTTP phrases
- `Mercor`
- `RL Studio`
- `production deployment`
- hardcoded secret indicators
- `shell=True`
- destructive/unregistered tool names

Search hits were reviewed. Remaining hits are repository rules, explicit non-claims,
security documentation, test fixtures, dependency package names such as `secretstorage`, or
implemented redaction/configuration terms. No real secret, Mercor/RL Studio compatibility
claim, HTTP instruction, production deployment claim, fake success statement, or registered
tool documentation gap was found after the Phase 7 documentation update.

## Known Limitations

- Only stdio transport is implemented and verified.
- HTTP and Streamable HTTP are not configured, exposed, or tested.
- This project is not a complete arbitrary-code execution sandbox.
- Windows symlink tests skip when the OS denies symlink creation.
- Command safety depends on careful allowlists and controlled workspaces.
- Artifact collection is limited to approved text categories and suffixes.
- Docker and Compose workflows verify local packaging/runtime behavior but do not publish
  images or deploy a production service.
- Remote CI evidence currently applies to commit `4efddd89c8aed22310f3dc14a74ed1e215ec21e1`;
  Phase 7 documentation/demo changes are verified locally before commit.

## Claims That Must Not Be Made

- Do not claim HTTP support.
- Do not claim production deployment.
- Do not claim package or Docker image publication.
- Do not claim a Git tag or GitHub release exists.
- Do not claim integration or compatibility with Mercor, RL Studio, or any private platform.
- Do not claim this is a complete arbitrary-code execution sandbox.
- Do not claim the independent final audit has started or completed.
