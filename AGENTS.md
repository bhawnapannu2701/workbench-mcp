# Repository Rules

These rules are permanent guidance for all work in this repository.

## Engineering

- Use small, typed, testable modules.
- Prefer clear boundaries between configuration, security checks, services, MCP tool registration, and transport startup.
- Keep changes scoped to the requested phase or feature.
- Use reproducible setup, pinned important dependencies, and documented commands.
- Run formatting, linting, type checking, and relevant tests after meaningful changes.
- Investigate root causes instead of hiding failures or weakening tests.
- Document platform-specific limitations honestly.

## Security

- Use secure defaults.
- Never use `shell=True`.
- Never expose unrestricted command execution.
- Never access files outside configured workspace or artifact roots.
- Validate paths with `pathlib` and resolved-path containment checks.
- Block path traversal, absolute-path escape, symbolic-link escape, command injection, executable-path bypass, and shell-operator bypass.
- Enforce file-size, output-size, and command-timeout limits.
- Redact configured secret patterns from logs, diagnostics, and tool responses.
- Never commit passwords, tokens, API keys, private credentials, or real secrets.
- Never mount the Docker socket or require privileged containers.

## Truthfulness

- Never say a command, test, build, feature, or integration works unless it was actually run or verified.
- Never invent metrics, coverage, production users, performance improvements, or deployment claims.
- Do not leave placeholder functions, fake success responses, or TODO-only implementations.
- Do not weaken meaningful tests just to make them pass.
- Record real implementation failures and their fixes.
- Document unresolved limitations honestly.
- Do not claim integration with Mercor, RL Studio, or any private platform.
