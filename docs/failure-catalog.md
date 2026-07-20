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
