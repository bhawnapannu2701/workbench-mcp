# Requirement Audit

This checklist maps implemented Phase 1 through Phase 4 requirements to code, tests, and
Phase 5 verification commands.

Status values:

- `Verified`: implemented and covered by tests or direct verification.
- `Deferred`: intentionally not implemented in Phases 1 through 5.
- `N/A`: searched or reviewed, with no implementation surface required.

## Foundation And Configuration

| Requirement | Source file | Test file | Verification command | Status |
| --- | --- | --- | --- | --- |
| Python package metadata and `uv` dependency management | `pyproject.toml`, `uv.lock` | N/A | `uv build` | Verified |
| Validated environment configuration | `src/workbench_mcp/config.py` | `tests/unit/test_config.py` | `uv run pytest` | Verified |
| Optional TOML configuration | `src/workbench_mcp/config.py` | `tests/unit/test_config.py` | `uv run pytest` | Verified |
| Invalid critical configuration fails fast | `src/workbench_mcp/config.py` | `tests/unit/test_config.py` | `uv run pytest` | Verified |
| Safe structured logging setup | `src/workbench_mcp/logging_config.py` | Covered by import/startup tests | `uv run mypy src`; `uv run pytest` | Verified |
| Permanent repository engineering rules | `AGENTS.md` | N/A | Manual review during Phase 5 | Verified |

## Filesystem And Path Security

| Requirement | Source file | Test file | Verification command | Status |
| --- | --- | --- | --- | --- |
| Resolved-path containment validation | `src/workbench_mcp/security/paths.py` | `tests/security/test_path_security.py` | `uv run pytest` | Verified |
| Path-traversal rejection | `src/workbench_mcp/security/paths.py` | `tests/security/test_path_security.py` | `uv run pytest` | Verified |
| Absolute-path escape rejection | `src/workbench_mcp/security/paths.py` | `tests/security/test_path_security.py` | `uv run pytest` | Verified |
| Symbolic-link escape rejection | `src/workbench_mcp/security/paths.py` | `tests/security/test_path_security.py`, `tests/security/test_patching_security.py`, `tests/security/test_artifact_service.py` | `uv run pytest -rs` | Verified; skips only when Windows blocks symlink creation |
| File-size enforcement | `src/workbench_mcp/security/limits.py` | `tests/unit/test_filesystem_services.py`, `tests/unit/test_search_service.py` | `uv run pytest` | Verified |
| Binary-file detection | `src/workbench_mcp/security/limits.py` | `tests/unit/test_filesystem_services.py`, `tests/unit/test_search_service.py` | `uv run pytest` | Verified |
| Safe directory listing with depth/result limits | `src/workbench_mcp/services/filesystem.py` | `tests/unit/test_filesystem_services.py` | `uv run pytest` | Verified |
| Safe text-file reading with line ranges | `src/workbench_mcp/services/filesystem.py` | `tests/unit/test_filesystem_services.py` | `uv run pytest` | Verified |
| Text search with glob, case sensitivity, result/output limits | `src/workbench_mcp/services/search.py` | `tests/unit/test_search_service.py` | `uv run pytest` | Verified |

## Controlled Writing

| Requirement | Source file | Test file | Verification command | Status |
| --- | --- | --- | --- | --- |
| Read-only patch rejection | `src/workbench_mcp/services/patching.py` | `tests/security/test_patching_security.py`, `tests/unit/test_mcp_server.py` | `uv run pytest` | Verified |
| Expected-content precondition | `src/workbench_mcp/services/patching.py` | `tests/unit/test_patching_service.py` | `uv run pytest` | Verified |
| Write escape rejection | `src/workbench_mcp/security/paths.py`, `src/workbench_mcp/services/patching.py` | `tests/security/test_patching_security.py` | `uv run pytest` | Verified |
| Atomic replacement behavior | `src/workbench_mcp/services/patching.py` | `tests/unit/test_patching_service.py` | `uv run pytest` | Verified |

## Command, Test, Git, Artifact, And Diagnostic Services

| Requirement | Source file | Test file | Verification command | Status |
| --- | --- | --- | --- | --- |
| Allowlisted process execution | `src/workbench_mcp/security/commands.py`, `src/workbench_mcp/services/process_runner.py` | `tests/unit/test_process_runner.py` | `uv run pytest` | Verified |
| Argument-array execution without `shell=True` | `src/workbench_mcp/services/process_runner.py` | `tests/unit/test_process_runner.py`; repository search | `uv run ruff check .`; `rg ...` | Verified |
| Workspace-contained working directory | `src/workbench_mcp/services/process_runner.py` | `tests/unit/test_process_runner.py` | `uv run pytest` | Verified |
| Timeouts and process cleanup where testable | `src/workbench_mcp/services/process_runner.py` | `tests/unit/test_process_runner.py` | `uv run pytest` | Verified |
| stdout/stderr capture | `src/workbench_mcp/services/process_runner.py` | `tests/unit/test_process_runner.py` | `uv run pytest` | Verified |
| Output truncation | `src/workbench_mcp/security/limits.py`, `src/workbench_mcp/services/process_runner.py` | `tests/unit/test_process_runner.py` | `uv run pytest` | Verified |
| Secret redaction | `src/workbench_mcp/security/redaction.py`, `src/workbench_mcp/tools/common.py` | `tests/unit/test_process_runner.py`, `tests/unit/test_mcp_server.py` | `uv run pytest` | Verified |
| Predefined test-command execution | `src/workbench_mcp/services/test_runner.py` | `tests/unit/test_test_runner.py`, `tests/unit/test_mcp_server.py` | `uv run pytest` | Verified |
| Read-only Git status and no destructive Git action | `src/workbench_mcp/services/git_service.py` | `tests/unit/test_git_service.py`, `tests/unit/test_mcp_server.py` | `uv run pytest` | Verified |
| Approved artifact collection | `src/workbench_mcp/services/artifact_service.py` | `tests/security/test_artifact_service.py`, `tests/unit/test_mcp_server.py` | `uv run pytest` | Verified |
| Artifact traversal, absolute, and symlink escape rejection | `src/workbench_mcp/services/artifact_service.py` | `tests/security/test_artifact_service.py` | `uv run pytest -rs` | Verified; symlink case depends on OS privilege |
| Workspace diagnostics with structured findings | `src/workbench_mcp/services/diagnostics.py` | `tests/unit/test_diagnostics.py`, `tests/unit/test_mcp_server.py` | `uv run pytest` | Verified |
| Missing executable detection | `src/workbench_mcp/services/diagnostics.py` | `tests/unit/test_diagnostics.py` | `uv run pytest` | Verified |
| Permission-related diagnostic finding where testable | `src/workbench_mcp/services/diagnostics.py` | `tests/unit/test_diagnostics.py` | `uv run pytest` | Verified |

## FastMCP Server

| Requirement | Source file | Test file | Verification command | Status |
| --- | --- | --- | --- | --- |
| Real FastMCP server | `src/workbench_mcp/server.py` | `tests/unit/test_mcp_server.py`, `tests/e2e/test_mcp_stdio.py` | `uv run pytest` | Verified |
| Current installed FastMCP API used | `src/workbench_mcp/server.py` | API introspection command | `uv run python -` | Verified |
| Stdio transport | `src/workbench_mcp/server.py` | `tests/e2e/test_mcp_stdio.py` | `uv run pytest tests/e2e/test_mcp_stdio.py` | Verified |
| Streamable HTTP | N/A | N/A | README and docs grep | Deferred; optional and intentionally omitted |
| Typed input validation | `src/workbench_mcp/tools/*.py` | `tests/unit/test_mcp_server.py` | `uv run pytest` | Verified |
| Safe error conversion | `src/workbench_mcp/tools/common.py` | `tests/unit/test_mcp_server.py` | `uv run pytest` | Verified |
| Expected MCP tools only | `src/workbench_mcp/tools/common.py`, `src/workbench_mcp/tools/*.py` | `tests/unit/test_mcp_server.py` | `uv run pytest` | Verified |
| Safe server-information resource | `src/workbench_mcp/tools/workspace_tools.py`, `src/workbench_mcp/tools/common.py` | `tests/unit/test_mcp_server.py` | `uv run pytest` | Verified |

## Phase 5 Verification

| Requirement | Source file | Test file | Verification command | Status |
| --- | --- | --- | --- | --- |
| Full pytest suite | `src/workbench_mcp/**` | `tests/**` | `uv run pytest` | Verified: 83 passed, 4 skipped |
| Coverage measurement | `src/workbench_mcp/**` | `tests/**` | `uv run pytest --cov=workbench_mcp --cov-report=term-missing` | Verified: combined 83%, 1074/1254 statements, 200/274 branches |
| Package build | `pyproject.toml`, `src/workbench_mcp/**` | N/A | `uv build` | Verified: sdist and wheel built |
| Security review search | Full repository | N/A | `rg ...` searches listed in `PROJECT_EVIDENCE.md` | Verified; no production security defects found |

