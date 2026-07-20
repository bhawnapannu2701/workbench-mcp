# 0004 - Container Smoke Runtime

## Status

Accepted for `v0.1.0`.

## Decision

The Docker image runs stdio by default as non-root UID/GID `10001:10001`. Smoke workflows
use read-only root filesystems, tmpfs `/tmp`, no network, dropped capabilities,
`no-new-privileges:true`, read-only workspace mounts, and writable artifact mounts.

## Rationale

The container is a packaging and verification target for the stdio server. It should avoid
privileged defaults and should test the same boundaries used by the local service layer.

## Consequences

- No Docker socket mount.
- No privileged mode.
- No host networking.
- No published HTTP ports.
- Linux bind-mount ownership needs host-compatible UID/GID handling for cleanup.
