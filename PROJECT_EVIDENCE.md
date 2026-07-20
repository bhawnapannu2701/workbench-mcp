# Project Evidence

This file records actual evidence for `workbench-mcp` Phase 7 and the final pre-release
audit. It does not claim HTTP support, production deployment, package publishing, Docker
image publishing, private platform integration, Git tags, or GitHub releases.

## Runtime

- Local Python: `Python 3.13.3`
- Local uv: `uv 0.11.29 (901092ee1 2026-07-15 x86_64-pc-windows-msvc)`
- Package version: `0.1.0`
- Local FastMCP import: `3.4.4`
- Docker: `Docker version 28.3.3, build 980b856`
- Docker Compose: `Docker Compose version v2.39.2-desktop.1`
- Docker engine: `28.3.3 linux x86_64`
- Audit branch: `codex/workbench-mcp-v1`
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

## Final Audit Findings Fixed

- Subprocess output was previously truncated only after `communicate()` captured full
  stdout/stderr. Added bounded concurrent pipe readers in
  `src/workbench_mcp/services/subprocess_capture.py`.
- Artifact collection previously read whole artifact files before truncation. It now reads
  a bounded prefix plus a fixed binary-detection sample.
- Git inspection previously used unbounded `subprocess.run()` and `git diff --shortstat`
  without `--no-ext-diff`. It now uses bounded subprocess execution, timeout/output
  limits, disabled prompts/global/system config/optional locks, and `--no-ext-diff`.
- Diagnostics now reports Git inspection failures as warnings.
- Stale documentation references to the previous Phase 7 CI run were corrected.

## Source And Test Mapping

| Behavior | Source | Tests/evidence |
| --- | --- | --- |
| Configuration loading and validation | `src/workbench_mcp/config.py` | `tests/unit/test_config.py` |
| Workspace path containment | `src/workbench_mcp/security/paths.py` | `tests/security/test_path_security.py` |
| File size, binary detection, truncation | `src/workbench_mcp/security/limits.py` | `tests/unit/test_filesystem_services.py`, `tests/unit/test_search_service.py` |
| Bounded subprocess capture | `src/workbench_mcp/services/subprocess_capture.py` | `tests/unit/test_process_runner.py`, `tests/unit/test_git_service.py` |
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

## Commands Run In Final Audit

Bare `uv` is not on PATH in this Windows PowerShell session; the exact requested
`uv sync --frozen` command failed with `uv : The term 'uv' is not recognized`. Actual uv
verification used `$env:APPDATA\Python\Python313\Scripts\uv.exe`.

```powershell
git branch --show-current
git status --short
git log --oneline -12
git stash list
git remote -v
git fetch origin +refs/heads/codex/workbench-mcp-v1:refs/remotes/origin/codex/workbench-mcp-v1
git rev-parse HEAD
git rev-parse origin/codex/workbench-mcp-v1
git rev-list --left-right --count HEAD...origin/codex/workbench-mcp-v1
gh run list --branch codex/workbench-mcp-v1 --limit 10 --json databaseId,headSha,status,conclusion,createdAt,updatedAt,event,url,displayTitle
gh run view 29778875177 --json databaseId,headSha,status,conclusion,createdAt,updatedAt,event,url,jobs
uv sync --frozen
& $env:APPDATA\Python\Python313\Scripts\uv.exe sync --frozen
& $env:APPDATA\Python\Python313\Scripts\uv.exe run ruff format --check .
& $env:APPDATA\Python\Python313\Scripts\uv.exe run ruff check .
& $env:APPDATA\Python\Python313\Scripts\uv.exe run mypy src
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest -rs
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest --cov=workbench_mcp --cov-report=term-missing
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest tests\unit\test_mcp_server.py::test_server_startup_succeeds -q
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest tests\e2e\test_mcp_stdio.py -q
& $env:APPDATA\Python\Python313\Scripts\uv.exe run python scripts\run-demo.py
& $env:APPDATA\Python\Python313\Scripts\uv.exe build
docker --version
docker compose version
docker info --format '{{.ServerVersion}} {{.OSType}} {{.Architecture}}'
docker build --progress=plain -t workbench-mcp:local .
docker image inspect workbench-mcp:local --format '{{.Id}} {{.Config.User}} {{json .Config.Entrypoint}} {{json .Config.Cmd}}'
docker run --rm --entrypoint python workbench-mcp:local -c "import os; print(os.geteuid())"
docker run --rm --entrypoint python workbench-mcp:local -c "import workbench_mcp, fastmcp; print(workbench_mcp.__version__); print(fastmcp.__version__)"
& $env:APPDATA\Python\Python313\Scripts\uv.exe run python scripts\run-container-smoke.py --image workbench-mcp:local
New-Item -ItemType Directory -Force .workbench-demo\workspace, .workbench-demo\artifacts
Set-Content -LiteralPath .workbench-demo\workspace\smoke.txt -Value "hello compose"
docker compose config
docker compose run --rm --build workbench-mcp-smoke
```

## Quality Results

- Dependency sync: `Checked 84 packages in 8ms`
- Ruff format: `49 files already formatted`
- Ruff lint: `All checks passed!`
- mypy: `Success: no issues found in 29 source files`
- Full pytest suite: `98 items collected`, `94 passed, 4 skipped in 11.29s`
- Coverage command: `94 passed, 4 skipped in 24.05s`
- Coverage display: `83%`
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

The tests remain active where symlink creation is available. Remote Linux CI run
`29778875177` completed the explicit symlink security test step successfully.

## MCP Results

- Construction smoke:
  `1 passed in 2.59s`
- Real stdio MCP client/server:
  `1 passed in 3.56s`
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
- Report audit: no demo temp prefix, repository root, or common secret markers found.

## Docker Evidence

- Docker engine probe: `28.3.3 linux x86_64`
- Docker build command: `docker build --progress=plain -t workbench-mcp:local .`
- Docker build result: succeeded
- Final local image ID after Compose rebuild:
  `sha256:9c98166db5cfe4675160a3a0fdbe6ae1c41eca49f893ad2155d526d845ecb5a7`
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
- Compose config result: passed; no ports, no network, read-only root filesystem, dropped
  capabilities, `no-new-privileges:true`, and no Docker socket mount.
- Compose smoke result: JSON status `ok`.
- Host artifact probe after Compose smoke was writable and removable by the host.

## Remote CI Evidence

- Workflow: `.github/workflows/ci.yml`
- Run ID: `29778875177`
- Run URL: `https://github.com/bhawnapannu2701/workbench-mcp/actions/runs/29778875177`
- Branch: `codex/workbench-mcp-v1`
- Event: `push`
- Head SHA: `34fc81ae32e4404f01f3f460b43e6508e108421d`
- Status: `completed`
- Conclusion: `success`
- Created: `2026-07-20T21:06:37Z`
- Updated: `2026-07-20T21:07:45Z`
- Job: `Verify package, security tests, and containers`
- Job conclusion: `success`

Successful remote steps included locked dependency installation, lockfile check, Ruff
format/lint, mypy, tests with coverage, explicit Linux symlink security tests, package
build, MCP stdio smoke, Docker image build, container smoke, Compose config, and Compose
smoke workflow.

Local final-audit fixes in this working tree are newer than that pushed CI run and require
a new CI run after push.

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
tool documentation gap was found after the final audit documentation update.

## Known Limitations

- Only stdio transport is implemented and verified.
- HTTP and Streamable HTTP are not configured, exposed, or tested.
- This project is not a complete arbitrary-code execution sandbox.
- Windows symlink tests skip when the OS denies symlink creation.
- Command safety depends on careful allowlists and controlled workspaces.
- Artifact collection is limited to approved text categories and suffixes.
- Docker and Compose workflows verify local packaging/runtime behavior but do not publish
  images or deploy a production service.
- Remote CI evidence applies to the latest pushed Phase 7 commit. Local final-audit fixes
  need a fresh CI run after push.

## Claims That Must Not Be Made

- Do not claim HTTP support.
- Do not claim production deployment.
- Do not claim package or Docker image publication.
- Do not claim a Git tag or GitHub release exists.
- Do not claim integration or compatibility with Mercor, RL Studio, or any private platform.
- Do not claim this is a complete arbitrary-code execution sandbox.
