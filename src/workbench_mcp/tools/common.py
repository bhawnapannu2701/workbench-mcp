"""Shared helpers for FastMCP tool adapters."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from fastmcp.exceptions import ToolError

from workbench_mcp import __version__
from workbench_mcp.config import WorkbenchConfig
from workbench_mcp.errors import WorkbenchMcpError
from workbench_mcp.security.redaction import Redactor
from workbench_mcp.services.git_service import GitStatus

EXPECTED_TOOL_NAMES = (
    "workspace_info",
    "list_files",
    "read_file",
    "search_text",
    "apply_patch",
    "run_command",
    "run_tests",
    "git_status",
    "collect_artifact",
    "diagnose_workspace",
)

SERVER_INFO_RESOURCE_URI = "workbench://server-info"
SUPPORTED_TRANSPORTS = ("stdio",)


def call_safely[T](config: WorkbenchConfig, operation: Callable[[], T]) -> T:
    """Convert expected service failures into safe MCP tool errors."""

    try:
        return operation()
    except WorkbenchMcpError as exc:
        raise ToolError(sanitize_message(config, str(exc))) from exc


def sanitize_message(config: WorkbenchConfig, message: str) -> str:
    """Redact secrets and configured host roots from MCP-facing text."""

    redactor = Redactor.from_patterns(config.secret_patterns)
    sanitized = redactor.redact(message)
    replacements = (
        (config.workspace_root, "<workspace_root>"),
        (config.artifact_directory, "<artifact_directory>"),
    )
    for path, label in replacements:
        sanitized = sanitized.replace(str(path), label)
        sanitized = sanitized.replace(path.as_posix(), label)
    return sanitized


def sanitize_response(config: WorkbenchConfig, payload: dict[str, object]) -> dict[str, object]:
    """Recursively redact secrets and configured roots from a structured response."""

    return cast(dict[str, object], _sanitize_value(config, payload))


def _sanitize_value(config: WorkbenchConfig, value: Any) -> object:
    if isinstance(value, str):
        return sanitize_message(config, value)
    if isinstance(value, dict):
        return {
            str(key): _sanitize_value(config, item)
            for key, item in value.items()
            if isinstance(key, str)
        }
    if isinstance(value, (list, tuple)):
        return [_sanitize_value(config, item) for item in value]
    return value


def safety_limits(config: WorkbenchConfig) -> dict[str, int]:
    """Return configured limits that are safe for clients to inspect."""

    return {
        "max_file_size_bytes": config.max_file_size_bytes,
        "max_command_seconds": config.max_command_seconds,
        "max_output_bytes": config.max_output_bytes,
    }


def capability_summary(config: WorkbenchConfig) -> dict[str, object]:
    """Return a safe capability summary without command arguments or secrets."""

    return {
        "workspace_inspection": True,
        "filesystem_read": True,
        "text_search": True,
        "controlled_text_patch": not config.read_only_mode,
        "allowlisted_commands": [command.name for command in config.allowed_commands],
        "predefined_tests": [command.name for command in config.test_commands],
        "git_status": True,
        "artifact_collection": True,
        "diagnostics": True,
    }


def sanitized_workspace_metadata(
    config: WorkbenchConfig,
    git_status: GitStatus | None = None,
) -> dict[str, object]:
    """Return workspace metadata without absolute host paths."""

    redactor = Redactor.from_patterns(config.secret_patterns)
    metadata: dict[str, object] = {
        "name": redactor.redact(config.workspace_root.name),
        "exists": config.workspace_root.exists(),
        "is_directory": config.workspace_root.is_dir(),
    }
    if git_status is not None:
        metadata.update(
            {
                "is_git_repository": git_status.is_repository,
                "git_branch": git_status.branch,
            }
        )
    return metadata


def server_information_payload(config: WorkbenchConfig) -> dict[str, object]:
    """Return the safe server-information resource payload."""

    payload: dict[str, object] = {
        "package_version": __version__,
        "server_capabilities": capability_summary(config),
        "registered_tool_names": list(EXPECTED_TOOL_NAMES),
        "active_safety_limits": safety_limits(config),
        "read_only_status": config.read_only_mode,
        "sanitized_workspace_metadata": sanitized_workspace_metadata(config),
        "supported_transports": list(SUPPORTED_TRANSPORTS),
    }
    return sanitize_response(config, payload)
