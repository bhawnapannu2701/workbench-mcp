# 0001 - Stdio Only Transport

## Status

Accepted for `v0.1.0`.

## Decision

`workbench-mcp` supports and verifies only FastMCP stdio transport in `v0.1.0`.

## Rationale

Stdio is enough for local MCP client integration and avoids adding network binding,
authentication, TLS, host/port policy, and HTTP-specific smoke tests before those controls
exist in the project.

## Consequences

- The server CLI exposes `--transport stdio` only.
- README and runbook do not include HTTP startup instructions.
- Docker and Compose publish no ports.
- Diagnostics mention HTTP only as disabled/not enabled.
- Any future HTTP support must add configuration, policy, tests, and documentation before
  being claimed.
