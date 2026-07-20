# 0002 - Explicit Workspace And Artifact Boundaries

## Status

Accepted for `v0.1.0`.

## Decision

Workspace operations and artifact operations use separate configured roots:

- `WORKSPACE_ROOT` for repository inspection, search, patching, command CWD, and Git status.
- `ARTIFACT_DIRECTORY` for approved report/log collection.

Both boundaries use resolved-path containment checks.

## Rationale

Keeping workspace and artifact roots separate makes it clearer which operations inspect
source files and which operations collect generated evidence. It also allows the container
model to mount the workspace read-only while leaving artifacts writable.

## Consequences

- Artifact collection requires approved categories and suffixes.
- `apply_patch` can modify workspace files only when `READ_ONLY_MODE=false`.
- Docker and Compose mount `/workspace` and `/artifacts` separately.
- Documentation and tests must cover both boundaries.
