"""Read-only Git MCP tools."""

from __future__ import annotations

from dataclasses import asdict

from fastmcp import FastMCP

from workbench_mcp.config import WorkbenchConfig
from workbench_mcp.services.git_service import GitService
from workbench_mcp.tools.common import call_safely, sanitize_response


def register_git_tools(server: FastMCP, config: WorkbenchConfig) -> None:
    """Register read-only Git inspection tools."""

    git_service = GitService(config)

    @server.tool(name="git_status")
    def git_status() -> dict[str, object]:
        """Return read-only Git status for the configured workspace."""

        result = call_safely(config, git_service.status)
        return sanitize_response(config, asdict(result))
