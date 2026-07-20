# Debugging

This file records real troubleshooting notes from implementation and verification.

## `uv` Is Not On PATH In This Windows Shell

Symptom:

```powershell
Get-Command uv
```

failed with `The term 'uv' is not recognized`.

Resolution:

Use the installed executable path in this environment:

```powershell
& $env:APPDATA\Python\Python313\Scripts\uv.exe run python --version
```

The public docs still show standard `uv ...` commands because that is the intended command
form after uv is installed on PATH.

## PowerShell Brace Expressions In Git Revisions

PowerShell treats unquoted brace expressions as syntax. Quote Git revs such as:

```powershell
git rev-parse '4efddd8^{commit}'
git rev-parse --abbrev-ref --symbolic-full-name '@{u}'
```

## PowerShell Multi-Path `Get-ChildItem`

The command:

```powershell
Get-ChildItem -Recurse -File docs src tests scripts
```

failed with `A positional parameter cannot be found that accepts argument 'docs'`.

Use `rg --files docs src tests scripts` for repository inventory instead.

## Expected Blocked Tool Calls Can Log Error Lines

FastMCP may log expected `ToolError` failures during security demonstrations. The public
demo disables logging only around the intentionally blocked traversal call so the human
summary stays concise while the JSON report still records the blocked behavior.

Supporting source: `scripts/run-demo.py`.

## Stdio Smoke Should Run Serially In Final Verification

During Phase 7, the explicit stdio E2E smoke test timed out once when it was run in
parallel with package build and the public demo. The complete pytest suite had already
passed, and rerunning `uv run pytest tests/e2e/test_mcp_stdio.py -q` by itself passed with
`1 passed`.

Final verification should run startup-sensitive MCP smoke tests serially.

## Docker Bind-Mount Ownership

On Linux, files created by a non-root container user inside a bind mount can become
unremovable by the host cleanup process if UID/GID ownership does not match. The direct
container smoke runner uses the host UID/GID on POSIX hosts, and CI sets
`WORKBENCH_MCP_CONTAINER_USER=$(id -u):$(id -g)` for Compose.

Supporting source: `scripts/run-container-smoke.py`, `compose.yaml`,
`.github/workflows/ci.yml`.

## Docker Desktop Engine API 500

During Phase 7 Docker verification, an initial `docker build -t workbench-mcp:local .`
timed out and left stale Docker CLI/buildx child processes. After clearing those children,
Docker Desktop returned API 500 errors for both `desktop-linux` and `default` contexts. Logs
showed Docker Desktop was still waiting for the Linux/WSL init control API.

Recovery that worked:

```powershell
$dockerProcesses = Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'docker' } | Select-Object -ExpandProperty ProcessId
if ($dockerProcesses) { Stop-Process -Id $dockerProcesses -Force }
wsl --terminate docker-desktop
wsl --shutdown
Start-Process -FilePath 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
```

After waiting for Docker Desktop startup, `docker info --format '{{.ServerVersion}} {{.OSType}} {{.Architecture}}'`
returned `28.3.3 linux x86_64`, and Docker build, container smoke, Compose config, and
Compose smoke all passed.

## Windows Symlink Test Skips

Some Windows environments deny symlink creation with `WinError 1314`. The affected tests
skip locally in that case and are run explicitly on Linux CI:

- `tests/security/test_artifact_service.py::test_rejects_artifact_symlink_escape`
- `tests/security/test_patching_security.py::test_apply_patch_rejects_symlink_escape`
- `tests/security/test_path_security.py::test_read_file_rejects_symlink_escape`
- `tests/security/test_path_security.py::test_list_files_rejects_symlink_directory_escape`
