"""Workspace information MCP tool and resources."""

from __future__ import annotations

from fastmcp import FastMCP

from workbench_mcp.config import WorkbenchConfig
from workbench_mcp.services.git_service import GitService, GitStatus
from workbench_mcp.tools.common import (
    SERVER_INFO_RESOURCE_URI,
    call_safely,
    capability_summary,
    safety_limits,
    sanitized_workspace_metadata,
    server_information_payload,
)


def register_workspace_tools(server: FastMCP, config: WorkbenchConfig) -> None:
    """Register workspace metadata tools and resources."""

    git_service = GitService(config)

    @server.tool(name="workspace_info")
    def workspace_info() -> dict[str, object]:
        """Return sanitized workspace and server capability information."""

        git_status = call_safely(config, git_service.status)
        return {
            "workspace": sanitized_workspace_metadata(config, git_status),
            "read_only_status": config.read_only_mode,
            "safety_limits": safety_limits(config),
            "capabilities": capability_summary(config),
            "git_repository_status": _git_repository_summary(git_status),
        }

    @server.resource(
        SERVER_INFO_RESOURCE_URI,
        name="server_info",
        mime_type="application/json",
    )
    def server_info_resource() -> dict[str, object]:
        """Return safe server metadata for MCP clients."""

        return server_information_payload(config)


def _git_repository_summary(status: GitStatus) -> dict[str, object]:
    return {
        "is_repository": status.is_repository,
        "branch": status.branch,
        "staged_file_count": len(status.staged_files),
        "modified_file_count": len(status.modified_files),
        "untracked_file_count": len(status.untracked_files),
    }
