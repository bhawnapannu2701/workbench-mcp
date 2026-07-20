# Failure Catalog

This file records real implementation failures encountered while building the project.

## Phase 1

### `uv sync` timed out while downloading Ruff

- Symptom: dependency installation failed while extracting `ruff==0.15.22`.
- Failing command: `python -m uv sync --all-groups`
- Root cause: network timeout during wheel download/extraction with the default `UV_HTTP_TIMEOUT=30`.
- Fix: reran the same sync with `UV_HTTP_TIMEOUT=120`.
- Regression protection: dependency installation remains part of phase and final verification commands.

### Ruff format check failed on initial files

- Symptom: Ruff reported that `src/workbench_mcp/config.py` and `tests/unit/test_config.py` would be reformatted.
- Failing command: `python -m uv run ruff format --check .`
- Root cause: initial hand-written files were not fully Ruff-formatted.
- Fix: ran `python -m uv run ruff format .`.
- Regression protection: `python -m uv run ruff format --check .` is required before commits.

### Ruff lint found style issues

- Symptom: Ruff reported import ordering, an unnecessary dict comprehension, and magic-value assertions in tests.
- Failing command: `python -m uv run ruff check .`
- Root cause: initial code used a broader import style, a redundant dict comprehension, and numeric literals directly in assertions.
- Fix: narrowed the package-version import, rewrote config-key normalization, and introduced named test constants.
- Regression protection: `python -m uv run ruff check .` is required before commits.

### Configuration tests hit Pydantic assignment recursion

- Symptom: valid configuration tests failed with `RecursionError`.
- Failing command: `python -m uv run pytest tests/unit/test_config.py`
- Root cause: `WorkbenchConfig` assigned to `artifact_directory` inside an `after` model validator while assignment validation was enabled, which re-entered the validator.
- Fix: updated the validator to set the resolved artifact directory with `object.__setattr__`.
- Regression protection: unit tests cover valid environment, TOML, override, and sanitized-summary loading paths.

## Phase 2

### PowerShell rejected an unquoted stash reference

- Symptom: applying the saved Phase 2 work failed with `error: unknown switch 'e'`.
- Failing command: `git stash apply stash@{1}`
- Root cause: PowerShell interpreted the unquoted brace expression instead of passing it as a literal Git revision.
- Fix: reran the command as `git stash apply 'stash@{1}'`.
- Regression protection: future stash references in PowerShell should be quoted.

### Ruff import-order check failed on new tests

- Symptom: Ruff reported unsorted import blocks in the new filesystem, search, patching, and security tests.
- Failing command: `python -m uv run ruff check .`
- Root cause: initial test imports were manually ordered and did not match Ruff's configured import sorter.
- Fix: ran `python -m uv run ruff check . --fix` to sort imports.
- Regression protection: `python -m uv run ruff check .` is part of phase verification.

### Filesystem and patch tests failed on Windows newline translation

- Symptom: exact-content read and patch tests expected `\n`, while service reads preserved `\r\n` bytes written by text-mode defaults on Windows.
- Failing command: `python -m uv run pytest tests/unit/test_filesystem_services.py tests/unit/test_search_service.py tests/unit/test_patching_service.py tests/security/test_path_security.py tests/security/test_patching_security.py`
- Root cause: the tests used `Path.write_text()` without an explicit newline policy for files whose exact bytes were asserted or patched.
- Fix: updated exact-content test fixtures to write with `newline="\n"`.
- Regression protection: Phase 2 tests now assert exact reads and patch preconditions using platform-stable fixture files.

## Phase 3

### Bare `uv` executable was not on PATH

- Symptom: `where.exe uv` could not find a bare `uv` executable on PATH.
- Failing command: `where.exe uv`
- Root cause: `uv.exe` was installed in the Python user Scripts directory, which this shell did not include on PATH.
- Fix: invoked the requested `uv run ...` checks through `C:\Users\hp\AppData\Roaming\Python\Python313\Scripts\uv.exe`.
- Regression protection: final Phase 3 verification records the exact executable path used for `uv run` commands.

### Ruff lint failed on recovered Phase 3 tests

- Symptom: Ruff reported import-order issues and `S603` warnings in Git setup tests.
- Failing command: `python -m uv run ruff check .`
- Root cause: recovered test files had unsorted imports, and Git test setup used `subprocess.run()` to create a temporary repository.
- Fix: ran Ruff's safe import fixer and annotated the test-only Git setup subprocess calls with `# noqa: S603` after resolving `git` with `shutil.which()`.
- Regression protection: `uv run ruff check .` is part of Phase 3 verification.

### mypy failed on POSIX-only process cleanup calls on Windows

- Symptom: mypy reported that `os.killpg` and `signal.SIGKILL` were unavailable.
- Failing command: `python -m uv run mypy src`
- Root cause: mypy ran with Windows platform stubs, where those POSIX-only APIs are not present.
- Fix: replaced direct POSIX-only attribute access with guarded dynamic lookups and a regular process termination fallback.
- Regression protection: `uv run mypy src` now passes on the current Windows environment.

### Diagnostics tried to run Git after the workspace disappeared

- Symptom: the diagnostic missing-workspace test failed with `NotADirectoryError` from `git rev-parse`.
- Failing command: `python -m uv run pytest tests/unit/test_process_runner.py tests/unit/test_test_runner.py tests/unit/test_git_service.py tests/unit/test_diagnostics.py tests/security/test_artifact_service.py`
- Root cause: `GitService` attempted to run Git with a `cwd` that no longer existed.
- Fix: `GitService` now returns non-repository status before spawning Git when the workspace path is missing or not a directory.
- Regression protection: diagnostics tests cover the disappeared-workspace error path.

## Phase 4

### PowerShell rejected Bash-style heredoc syntax

- Symptom: the first FastMCP introspection command failed before Python ran.
- Failing command: `uv run python - <<'PY'`
- Root cause: PowerShell does not support Bash heredoc redirection syntax.
- Fix: reran the introspection using a PowerShell here-string piped to `uv run python -`.
- Regression protection: Phase 4 notes record the exact PowerShell-compatible verification commands.

### Ad hoc stdio smoke test used malformed JSON configuration

- Symptom: the first real stdio client/server smoke attempt exited during startup with a `ConfigError` for `TEST_COMMANDS`.
- Failing command: PowerShell here-string script invoking `StdioTransport(sys.executable, ["-m", "workbench_mcp.server"], ...)`
- Root cause: the hand-written JSON string embedded quotes inside the test command without escaping them correctly.
- Fix: generated the `TEST_COMMANDS` environment value with `json.dumps`.
- Regression protection: `tests/e2e/test_mcp_stdio.py` builds the environment configuration with `json.dumps` and performs a real stdio MCP client/server interaction.

### Ruff failed on initial Phase 4 formatting and lint

- Symptom: Ruff reported unformatted files, import ordering, a local import in `tools/common.py`, and a Python 3.12 generic-style lint.
- Failing commands: `uv run ruff format --check .` and `uv run ruff check .`
- Root cause: new server/tool/test files were edited manually before formatter and import sorting were applied.
- Fix: moved the package version import to module scope, updated `call_safely` to Python 3.12 type-parameter syntax, ran `uv run ruff format .`, and ran `uv run ruff check . --fix`.
- Regression protection: Phase 4 verification reran Ruff format check and lint successfully.

## Phase 5

### PowerShell rejected a multi-path `Get-ChildItem` inventory command

- Symptom: the repository inventory command failed with `A positional parameter cannot be found that accepts argument 'docs'`.
- Failing command: `Get-ChildItem -Recurse -File docs src tests scripts | Select-Object -ExpandProperty FullName`
- Root cause: the PowerShell invocation did not accept the path list with that parameter set.
- Fix: used `rg --files docs src tests scripts` for repository file inventory.
- Regression protection: future audits should prefer `rg --files` for file discovery.

### Requirement audit found missing explicit Git and diagnostic test coverage

- Symptom: Phase 5 audit found no dedicated test proving Git status uses only read-only subcommands, and no diagnostic test for artifact-directory write warnings.
- Failing command: N/A; this was a checklist gap found during manual audit.
- Root cause: Phase 3 tests covered Git status behavior and diagnostic severities, but did not explicitly lock down these two narrower expectations.
- Fix: added `test_git_status_uses_only_read_only_git_commands` and `test_diagnostics_reports_warning_when_artifact_directory_is_not_writable`.
- Regression protection: the full pytest suite now includes those cases.

## Phase 6

### Response stream disconnected after partial Docker and CI edits

- Symptom: Phase 6 repository files were modified, but the prior response ended before
  verification and commit.
- Failing command: N/A; the assistant response stream disconnected.
- Root cause: external stream interruption during the implementation turn.
- Fix: resumed by inspecting `git branch --show-current`, `git status --short`,
  `git diff --stat`, `git log --oneline -7`, and `git stash list`; inspected existing
  Docker, Compose, smoke-test, and CI files before editing; preserved the partial Phase 6
  work; did not apply, drop, or delete stashes.
- Regression protection: Phase 6 final verification reruns the full Python, Docker,
  container, and Compose checks before committing.

### Docker engine was initially unavailable

- Symptom: Docker CLI was installed, but `docker info` could not connect to the Linux
  engine pipe.
- Failing command: `docker info`
- Root cause: Docker Desktop's Linux engine was not running when Phase 6 verification began.
- Fix: started Docker Desktop and reran `docker info` successfully against the
  `desktop-linux` context.
- Regression protection: Docker availability checks now precede Docker build and container
  smoke commands in the Phase 6 workflow.

### Container smoke helper had an invalid f-string during initial validation

- Symptom: the smoke helper failed Python compilation before it could run Docker.
- Failing command: `uv run python -m py_compile scripts\container-smoke-test.py scripts\run-container-smoke.py`
- Root cause: the first host-side smoke command assembled a nested JSON environment value
  inside an f-string with conflicting quote characters.
- Fix: built the `TEST_COMMANDS` value with `json.dumps` before constructing the Docker
  argument array.
- Regression protection: `uv run python -m py_compile` and Ruff checks were run after the
  fix, and the final container smoke test exercises the helper end to end.

### Ruff flagged the Docker tmpfs mount string as a hardcoded temp path

- Symptom: Ruff reported `S108` for the literal Docker tmpfs target string.
- Failing command: `uv run ruff check .`
- Root cause: the security lint rule treats `/tmp` literals as suspicious even when the
  string is a Docker runtime mount specification.
- Fix: kept the explicit tmpfs mount and added a line-specific `# noqa: S108` on that
  argument.
- Regression protection: `uv run ruff check .` is part of Phase 6 and CI verification.

### Local command guard blocked recursive smoke-directory cleanup

- Symptom: cleanup of `.workbench-demo` was rejected by the local command-safety guard even
  after resolving the path inside the repository.
- Failing commands: `Remove-Item -LiteralPath .workbench-demo -Recurse -Force` and an
  explicit absolute-path variant.
- Root cause: the local execution guard rejected recursive deletion commands in this
  environment.
- Fix: did not switch to a riskier deletion path. `.workbench-demo` remains ignored by Git
  and excluded from Docker build context.
- Regression protection: `.gitignore` and `.dockerignore` exclude `.workbench-demo`, and
  final Git status ignores it.

### Remote GitHub Actions container smoke cleanup failed on Linux

- Symptom: the first remote GitHub Actions workflow failed only at the direct container smoke
  step while `tempfile.TemporaryDirectory` was cleaning up the bind-mounted artifact tree.
- Failing command: `uv run python scripts/run-container-smoke.py --image workbench-mcp:ci`
- Error: `PermissionError: [Errno 13] Permission denied: 'container-smoke.json'`.
- Root cause: the host smoke runner made the artifact bind mount world-writable with
  `chmod 0777`, then ran the container as the image default user `10001:10001`. On Linux,
  `scripts/container-smoke-test.py` created `artifacts/diagnostics` as UID/GID
  `10001:10001` with mode `0755` and wrote `container-smoke.json` as UID/GID
  `10001:10001` with mode `0644`. The GitHub runner owned the temporary root and artifact
  mount, but it did not own the nested `diagnostics` directory and had no write permission
  there, so `shutil.rmtree` could not unlink the report.
- Why Windows did not reproduce it: Docker Desktop for Windows mediates bind-mount
  permissions through its file-sharing layer instead of exposing the same Linux host UID/GID
  ownership semantics to the Windows cleanup process.
- Fix: the direct smoke runner now runs the container as the non-root host UID/GID on POSIX
  systems, leaves Windows on the image default user, removes the `0777` chmod, and verifies
  the generated JSON report is host-readable before temporary-directory cleanup. The Compose
  CI smoke path now sets `WORKBENCH_MCP_CONTAINER_USER=$(id -u):$(id -g)` and prepares the
  demo mount as runner-private instead of world-writable.
- Regression protection: `tests/unit/test_run_container_smoke.py` covers POSIX UID/GID
  selection, Windows avoidance of POSIX UID/GID APIs, root UID rejection to preserve the
  non-root smoke requirement, report read and temp cleanup success, and non-zero propagation
  for unexpected container failures.

## Phase 7

### Public demo script had an unterminated fixture string

- Symptom: the first focused Ruff/compile check for `scripts/run-demo.py` failed with
  `missing closing quote in string literal`.
- Failing command: `uv run ruff check scripts\run-demo.py tests\e2e\test_public_demo.py`
- Root cause: the diagnostic JSON fixture string had mismatched quote characters.
- Fix: corrected the string to a valid JSON text literal.
- Regression protection: `uv run python -m py_compile scripts\run-demo.py`, Ruff, and
  `tests/e2e/test_public_demo.py` all cover the script.

### Hyphenated demo script import triggered a dataclass/importlib issue

- Symptom: `tests/e2e/test_public_demo.py` failed while importing `scripts/run-demo.py`
  because `dataclasses` could not find the dynamically loaded module in `sys.modules`.
- Failing command: `uv run pytest tests\e2e\test_public_demo.py -q`
- Root cause: the importlib test helper executed the script module without first registering
  it under `spec.name`.
- Fix: inserted the module into `sys.modules` before `exec_module`.
- Regression protection: the focused E2E demo test now imports and runs the script.

### Expected blocked demo operation logged a noisy error line

- Symptom: `uv run python scripts\run-demo.py` succeeded but printed an extra FastMCP error
  line for the intentionally blocked traversal read.
- Failing command: N/A; the demo succeeded but the human summary was noisy.
- Root cause: FastMCP logs expected `ToolError` calls unless logging is suppressed around
  the intentional negative test.
- Fix: temporarily disabled logging only while exercising the expected blocked operation.
- Regression protection: the demo command now prints a concise success summary while the
  JSON report records the blocked operation.

### Explicit stdio smoke timed out when run in parallel with other heavy checks

- Symptom: `tests/e2e/test_mcp_stdio.py` timed out during FastMCP client initialization
  when run in parallel with package build and the public demo.
- Failing command: `uv run pytest tests\e2e\test_mcp_stdio.py -q`
- Root cause: startup-sensitive stdio smoke verification was run concurrently with other
  repository checks. The full test suite had already passed, and rerunning the stdio smoke
  serially passed with `1 passed in 4.07s`.
- Fix: reran the MCP stdio smoke test serially and recorded serial execution guidance in
  `docs/debugging.md`.
- Regression protection: the complete pytest suite and explicit serial stdio smoke command
  both pass in Phase 7 verification.

### Docker Desktop engine returned API 500 after a timed-out build

- Symptom: `docker build -t workbench-mcp:local .` hit the local command timeout, and
  subsequent `docker ps`, `docker image ls`, `docker info`, and `docker version` calls
  either hung or returned Docker API 500 errors.
- Failing command: `docker build -t workbench-mcp:local .`
- Root cause: local Docker Desktop's Linux/WSL engine became unhealthy and logs showed it
  was waiting for the Linux/WSL init control API. This was an environment failure, not a
  Dockerfile failure.
- Fix: terminated stale Docker CLI/buildx processes, stopped Docker Desktop processes,
  terminated the `docker-desktop` WSL distro, ran `wsl --shutdown`, relaunched Docker
  Desktop, and waited for `docker info` to return `28.3.3 linux x86_64`.
- Regression protection: after recovery, `docker build --progress=plain -t
  workbench-mcp:local .`, direct container smoke, `docker compose config`, and
  `docker compose run --rm --build workbench-mcp-smoke` all passed.
