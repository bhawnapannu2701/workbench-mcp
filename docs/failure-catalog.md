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
