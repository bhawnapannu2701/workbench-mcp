# Changelog

All notable changes for this repository are documented here.

## 0.1.0 - Pending Release

Prepared:

- Python package metadata for `workbench-mcp`.
- Validated configuration loading from defaults, TOML, and environment variables.
- Secure workspace path containment helpers.
- File listing, UTF-8 file reading, text search, and controlled text patching services.
- Allowlisted subprocess execution with timeout, output limit, and redaction controls.
- Predefined test-command execution with JSON test reports.
- Read-only Git status service.
- Approved artifact collection by category.
- Workspace diagnostics.
- FastMCP stdio server with ten registered tools and one server-information resource.
- Unit, security, and E2E tests, including real stdio client/server verification.
- Dockerfile, direct container smoke test, Compose smoke workflow, and GitHub Actions CI.
- Public README, architecture docs, threat model, runbook, debugging notes, security policy,
  contributing guide, release checklist, engineering evidence, and reproducible demo.
- Final audit hardening for bounded subprocess capture, bounded artifact collection,
  read-only Git timeout/output limits, and external-diff suppression.

Not included:

- HTTP or Streamable HTTP transport.
- Production deployment.
- Published Python package.
- Published Docker image.
- Git tag or GitHub release.
- Private platform integration or compatibility claims.
