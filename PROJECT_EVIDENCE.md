# Project Evidence

This file records actual repository evidence verified through Phase 5. It does not include
Docker, CI, deployment, production, or private-platform claims.

## Runtime

- Python used locally: `Python 3.13.3`
- FastMCP version: `3.4.4`
- Package version: `0.1.0`

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

Commands actually run in Phase 5:

```powershell
git branch --show-current
git status --short
git log --oneline -5
git stash list
rg -n "shell\s*=\s*True|subprocess\.|Popen\(|run\(|exec\(|eval\(|os\.system|start-process|Start-Process|TODO|FIXME|placeholder|mocked success|fake result|pass\s*(#.*)?$|password|token|api[_-]?key|secret" -S . --glob '!uv.lock' --glob '!.git/**' --glob '!.venv/**' --glob '!**/__pycache__/**'
rg -n "Path\(|joinpath|/|resolve\(|absolute|symlink|read_text\(|read_bytes\(|write_text\(|write_bytes\(|NamedTemporaryFile|mkstemp|replace\(" src tests -S --glob '!**/__pycache__/**'
rg --files docs src tests scripts
& $env:APPDATA\Python\Python313\Scripts\uv.exe run python --version
& $env:APPDATA\Python\Python313\Scripts\uv.exe run ruff format --check .
& $env:APPDATA\Python\Python313\Scripts\uv.exe run ruff check .
& $env:APPDATA\Python\Python313\Scripts\uv.exe run mypy src
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest --cov=workbench_mcp --cov-report=term-missing
& $env:APPDATA\Python\Python313\Scripts\uv.exe build
& $env:APPDATA\Python\Python313\Scripts\uv.exe run pytest tests/e2e/test_mcp_stdio.py
```

Actual results:

- Ruff format check: `43 files already formatted`
- Ruff lint: `All checks passed!`
- mypy: `Success: no issues found in 28 source files`
- Full pytest suite: `83 passed, 4 skipped`
- Coverage run: `83 passed, 4 skipped`
- Coverage display: `83%`
- Statement coverage: `1074/1254` statements covered, `85.65%`
- Branch coverage: `200/274` branches covered, `72.99%`
- Package build: succeeded
- Built artifacts:
  - `dist\workbench_mcp-0.1.0.tar.gz`
  - `dist\workbench_mcp-0.1.0-py3-none-any.whl`
- Stdio smoke test: `tests/e2e/test_mcp_stdio.py` passed
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

## Security Review Findings

Repository searches found no production use of `shell=True`, no unrestricted command runner,
no hardcoded real secret, no TODO/FIXME-only implementation, no mocked success path, and no
placeholder feature implementation. The only subprocess uses are:

- `src/workbench_mcp/services/process_runner.py`, with argument arrays, `shell=False`,
  allowlist validation, workspace-contained cwd, timeout handling, output truncation, and
  redaction.
- `src/workbench_mcp/services/git_service.py`, with read-only Git subcommands and
  `shell=False`.
- test-only subprocess calls in `tests/unit/test_git_service.py`, also using argument arrays
  and `shell=False`.

Phase 5 added tests for two audit gaps:

- `tests/unit/test_git_service.py::test_git_status_uses_only_read_only_git_commands`
- `tests/unit/test_diagnostics.py::test_diagnostics_reports_warning_when_artifact_directory_is_not_writable`

No production security defect was found during Phase 5.

## Relevant Source Paths

- `src/workbench_mcp/config.py`
- `src/workbench_mcp/server.py`
- `src/workbench_mcp/security/paths.py`
- `src/workbench_mcp/security/commands.py`
- `src/workbench_mcp/security/limits.py`
- `src/workbench_mcp/security/redaction.py`
- `src/workbench_mcp/services/filesystem.py`
- `src/workbench_mcp/services/search.py`
- `src/workbench_mcp/services/patching.py`
- `src/workbench_mcp/services/process_runner.py`
- `src/workbench_mcp/services/test_runner.py`
- `src/workbench_mcp/services/git_service.py`
- `src/workbench_mcp/services/artifact_service.py`
- `src/workbench_mcp/services/diagnostics.py`
- `src/workbench_mcp/tools/*.py`

## Known Limitations

- HTTP transport is not implemented or verified.
- Docker files and container smoke tests remain for Phase 6.
- GitHub Actions CI remains for Phase 6.
- Reproducible demo automation remains for a later phase.
- Final documentation hardening remains for a later phase.
- Four symlink security tests skip on this Windows host due `WinError 1314`; they remain
  meaningful on systems where symlink creation is allowed.

