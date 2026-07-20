# workbench-mcp

Secure FastMCP server for controlled repository inspection, file operations, test execution
and workspace diagnostics.

This is a public portfolio/open-source project. It is not a private platform integration.

## Current Scope

The current implementation exposes the real FastMCP server surface over the secure service
layer and has completed Phase 5 testing, security review, coverage measurement, package
build, and stdio MCP smoke verification. Only stdio transport is implemented and verified.
Streamable HTTP is supported by the installed FastMCP package, but it is not enabled in this
project yet.

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

## Known Limitations

- HTTP transport is not implemented or verified yet.
- Docker, CI, and demo automation are planned for later phases and should not be treated as
  complete.
- Some symlink escape tests are skipped on this Windows machine when symlink creation fails
  with `WinError 1314`; they remain active for environments where symlinks are permitted.
