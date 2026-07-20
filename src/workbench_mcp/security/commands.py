"""Command validation helpers for subprocess execution."""

from __future__ import annotations

from pathlib import Path

from workbench_mcp.config import AllowedCommand
from workbench_mcp.errors import CommandSecurityError

SHELL_OPERATOR_TOKENS = frozenset({"&&", "||", ";", "|", ">", ">>", "<", "<<", "$(", "`"})


def validate_command_tokens(command: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Validate a command array without invoking a shell."""

    if not command:
        msg = "command must contain at least one executable"
        raise CommandSecurityError(msg)
    normalized = tuple(command)
    executable = normalized[0]
    _validate_executable_token(executable)
    for token in normalized[1:]:
        _validate_argument_token(token)
    return normalized


def validate_allowlisted_command(
    command: tuple[str, ...] | list[str],
    allowed_commands: tuple[AllowedCommand, ...],
) -> tuple[str, ...]:
    """Validate that a command array uses an allowlisted executable."""

    normalized = validate_command_tokens(command)
    allowed_executables = {allowed.executable for allowed in allowed_commands}
    if normalized[0] not in allowed_executables:
        msg = f"executable is not allowlisted: {normalized[0]}"
        raise CommandSecurityError(msg)
    return normalized


def _validate_executable_token(token: str) -> None:
    _reject_control_characters(token)
    if token.strip() != token or token == "":
        msg = "executable must be a non-empty bare command name"
        raise CommandSecurityError(msg)
    if token in SHELL_OPERATOR_TOKENS:
        msg = "shell operators cannot be used as executables"
        raise CommandSecurityError(msg)
    if any(separator in token for separator in ("/", "\\")) or Path(token).is_absolute():
        msg = "executable paths are not allowed; use a configured bare executable name"
        raise CommandSecurityError(msg)
    if any(character.isspace() for character in token):
        msg = "executable cannot contain whitespace"
        raise CommandSecurityError(msg)


def _validate_argument_token(token: str) -> None:
    _reject_control_characters(token)
    if token in SHELL_OPERATOR_TOKENS or token.startswith("$(") or "`" in token:
        msg = "shell-operator bypass attempts are not allowed in command arguments"
        raise CommandSecurityError(msg)


def _reject_control_characters(token: str) -> None:
    if "\x00" in token or "\n" in token or "\r" in token:
        msg = "command tokens cannot contain control characters"
        raise CommandSecurityError(msg)
