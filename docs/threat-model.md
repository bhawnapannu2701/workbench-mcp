# Threat Model

`workbench-mcp` reduces the blast radius of common MCP development operations, but it is
not a complete arbitrary-code execution sandbox. It relies on application checks, OS
permissions, and optional container isolation. Do not treat it as a VM, kernel sandbox, or
container escape prevention system.

## Scope

Protected assets:

- Files outside `WORKSPACE_ROOT`.
- Files outside approved artifact category directories under `ARTIFACT_DIRECTORY`.
- Secrets matching configured redaction patterns.
- Host resources that could be affected by unrestricted shell commands, uncontrolled output,
  runaway processes, or unsafe Docker mounts.

Trusted inputs:

- The server configuration owner.
- The host OS and installed dependency versions.
- The Docker daemon when container checks are used.

Untrusted or semi-trusted inputs:

- MCP client tool arguments.
- Repository contents inside `WORKSPACE_ROOT`.
- Artifact contents inside `ARTIFACT_DIRECTORY`.
- Output from allowlisted commands and predefined tests.

## Threat Matrix

| Threat | Current mitigation | Supporting source | Supporting test | Remaining risk |
| --- | --- | --- | --- | --- |
| Path traversal with `..` | Rejects parent segments before path resolution. | `src/workbench_mcp/security/paths.py` | `tests/security/test_path_security.py` | Does not protect code inside an allowlisted interpreter from doing its own filesystem access. |
| Absolute-path escape | Resolves absolute paths and requires containment inside the approved root. | `src/workbench_mcp/security/paths.py` | `tests/security/test_path_security.py` | Platform path edge cases still rely on `pathlib` and OS semantics. |
| Symlink escape | Detects symlink components and rejects resolved paths outside the approved root. | `src/workbench_mcp/security/paths.py` | `tests/security/test_path_security.py`, `tests/security/test_patching_security.py`, `tests/security/test_artifact_service.py` | Windows tests skip when symlink creation is denied by the OS; Linux CI runs them. |
| Command injection through shell metacharacters | Commands are lists, never shell strings; shell operator tokens are rejected. | `src/workbench_mcp/security/commands.py`, `src/workbench_mcp/services/process_runner.py` | `tests/unit/test_process_runner.py` | An allowed executable may interpret its own arguments in dangerous ways. |
| Executable-path bypass | Executables must be bare names, not paths or names containing slashes, backslashes, or whitespace. | `src/workbench_mcp/security/commands.py`, `src/workbench_mcp/config.py` | `tests/unit/test_config.py`, `tests/unit/test_process_runner.py` | PATH resolution is still performed by the OS. Keep PATH controlled in sensitive environments. |
| Malicious arguments | Control characters, shell-operator tokens, command substitutions, and backticks are rejected. | `src/workbench_mcp/security/commands.py`, `src/workbench_mcp/config.py` | `tests/unit/test_config.py`, `tests/unit/test_process_runner.py` | Application-specific dangerous flags cannot be exhaustively understood by this server. |
| Secret leakage in responses | Configured regex redaction is applied to command output, artifact content, errors, and structured MCP responses. | `src/workbench_mcp/security/redaction.py`, `src/workbench_mcp/tools/common.py` | `tests/unit/test_process_runner.py`, `tests/unit/test_mcp_server.py` | Regex redaction cannot catch secrets that do not match configured patterns. |
| Host path leakage | Configured workspace and artifact roots are replaced with placeholders in MCP-facing strings. | `src/workbench_mcp/tools/common.py` | `tests/unit/test_mcp_server.py`, `tests/e2e/test_public_demo.py` | Other host paths emitted by allowlisted tools may still appear unless covered by redaction. |
| Output exhaustion | stdout/stderr are drained through bounded readers, artifact reads collect only a bounded prefix plus a binary sample, and MCP-facing text is truncated to configured byte limits. Search has result and output limits. | `src/workbench_mcp/security/limits.py`, `src/workbench_mcp/services/subprocess_capture.py`, `src/workbench_mcp/services/process_runner.py`, `src/workbench_mcp/services/search.py`, `src/workbench_mcp/services/artifact_service.py` | `tests/unit/test_process_runner.py`, `tests/unit/test_search_service.py`, `tests/security/test_artifact_service.py` | Very large directory trees can still cost traversal time until limits are reached. |
| Oversized file reads | Text read/search enforce `MAX_FILE_SIZE_BYTES`; binary-looking files are rejected or skipped. | `src/workbench_mcp/security/limits.py`, `src/workbench_mcp/services/filesystem.py`, `src/workbench_mcp/services/search.py` | `tests/unit/test_filesystem_services.py`, `tests/unit/test_search_service.py` | Large numbers of small files can still consume time. |
| Process timeout and cleanup | Commands use a configured timeout; POSIX process groups and Windows taskkill are used where available. | `src/workbench_mcp/services/process_runner.py` | `tests/unit/test_process_runner.py` | Process-tree cleanup is best effort and depends on OS behavior and child process cooperation. |
| Artifact exfiltration | Artifact collection is category and suffix bounded under `ARTIFACT_DIRECTORY`; binary artifacts are blocked. | `src/workbench_mcp/services/artifact_service.py` | `tests/security/test_artifact_service.py`, `tests/unit/test_mcp_server.py` | If sensitive data is intentionally written into approved artifacts, redaction must match it. |
| Malicious workspaces | Workspace reads/searches avoid traversal and common generated directories; command CWD remains inside workspace; Git inspection disables prompts, optional locks, global/system config, and external diff for diff stats. | `src/workbench_mcp/services/filesystem.py`, `src/workbench_mcp/services/search.py`, `src/workbench_mcp/services/process_runner.py`, `src/workbench_mcp/services/git_service.py` | `tests/security/test_path_security.py`, `tests/unit/test_filesystem_services.py`, `tests/unit/test_git_service.py` | Running allowlisted commands in a malicious workspace can execute untrusted code. |
| Unsafe container mounts | Docker and Compose smoke workflows do not mount the Docker socket, do not use privileged mode, drop capabilities, disable networking for smoke, and run as non-root. | `Dockerfile`, `compose.yaml`, `scripts/run-container-smoke.py` | `tests/unit/test_run_container_smoke.py`; container smoke command | Container isolation depends on Docker/host configuration and is not a formal sandbox guarantee. |
| Dependency risks | Important dependencies are pinned in `pyproject.toml`, `uv.lock`, Docker build args, and CI setup. | `pyproject.toml`, `uv.lock`, `Dockerfile`, `.github/workflows/ci.yml` | `uv sync --frozen --all-groups`, `uv lock --check`, package build, CI | Pinning improves reproducibility but does not eliminate vulnerable dependency risk. |
| Git mutation or config-triggered execution | Only read-only Git status and diff-stat commands are implemented; no destructive Git tools are registered; diff stats use `--no-ext-diff` and bounded execution. | `src/workbench_mcp/services/git_service.py`, `src/workbench_mcp/tools/git_tools.py` | `tests/unit/test_git_service.py`, `tests/unit/test_mcp_server.py` | Future Git operations must be reviewed carefully, and Git itself remains a large dependency with platform-specific behavior. |

## Explicit Non-Goals

- This project does not provide a complete arbitrary-code execution sandbox.
- This project does not safely run untrusted code just because a command is allowlisted.
- This project does not implement HTTP authentication, TLS, port binding, or web deployment.
- This project does not prevent Docker daemon or host kernel vulnerabilities.
- This project does not claim compatibility with Mercor, RL Studio, or any private platform.
