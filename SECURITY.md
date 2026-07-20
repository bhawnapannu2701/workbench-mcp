# Security Policy

## Supported Version

`workbench-mcp` is preparing `v0.1.0`. Security documentation and tests apply to the code on
branch `codex/workbench-mcp-v1`.

No package, Docker image, Git tag, or GitHub release has been published as part of Phase 7.

## Security Model

The server exposes typed MCP tools over stdio and delegates operations to bounded service
modules. The main controls are:

- `WORKSPACE_ROOT` containment for workspace file, search, patch, command CWD, and Git
  status operations.
- `ARTIFACT_DIRECTORY` containment for approved artifact collection.
- `READ_ONLY_MODE=true` by default.
- Bare executable allowlists for client-requested commands.
- Named predefined test commands.
- `subprocess` argument arrays with `shell=False`.
- File-size, output-size, and process-timeout limits.
- Secret-pattern and configured-root redaction before MCP-facing responses.
- Read-only Git status behavior.
- Non-root Docker runtime image and smoke workflows without Docker socket, privileged mode,
  host networking, or published ports.

See [docs/threat-model.md](docs/threat-model.md) for source and test mappings.

## Non-Goals

This project is not a complete arbitrary-code execution sandbox. If you allowlist a broad
interpreter or test runner, that executable can still run code with the permissions granted
by the host OS or container runtime.

This project does not implement HTTP, authentication, TLS, public hosting, or production
deployment.

This project does not claim integration or compatibility with Mercor, RL Studio, or any
private platform.

## Reporting Security Issues

For public repository work, open a GitHub issue with a minimal reproduction unless doing so
would disclose an active secret or exploit path. Do not include real tokens, passwords,
private keys, credentials, or proprietary workspace contents in reports.

Include:

- Operating system and Python version.
- Commit hash.
- Configuration shape with secrets removed.
- Exact command or MCP tool call.
- Expected behavior and observed behavior.
- Whether Docker or local stdio mode was used.

## Secret Handling

Never commit real secrets. `.env` files are ignored, and `.env.example` intentionally uses
non-secret sample values. Configure `SECRET_PATTERNS` for local secret formats that differ
from the default token/password/API-key pattern.

Redaction is best effort and regex based. It cannot guarantee removal of secrets that do
not match configured patterns.

## Security Verification

Relevant local commands:

```bash
uv run ruff check .
uv run mypy src
uv run pytest -rs
uv run pytest --cov=workbench_mcp --cov-report=term-missing
uv run python scripts/run-demo.py
docker build -t workbench-mcp:local .
uv run python scripts/run-container-smoke.py --image workbench-mcp:local
docker compose config
docker compose run --rm --build workbench-mcp-smoke
```

Linux CI explicitly runs symlink security tests that may skip on Windows when symlink
creation is denied by the OS.
