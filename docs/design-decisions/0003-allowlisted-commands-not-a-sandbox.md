# 0003 - Allowlisted Commands Are Not A Sandbox

## Status

Accepted for `v0.1.0`.

## Decision

Command execution is allowed only for configured bare executable names and predefined test
commands, always with argument arrays and `shell=False`. The project explicitly documents
that this is not a complete arbitrary-code execution sandbox.

## Rationale

Allowlists, command-token validation, timeouts, output limits, and workspace-contained CWDs
reduce accidental or direct misuse. They do not make powerful interpreters safe for
untrusted code.

## Consequences

- Users must choose narrow command allowlists for their risk model.
- Public docs warn against allowlisting broad interpreters for untrusted workspaces.
- Future command features must preserve `shell=False` and explicit validation.
