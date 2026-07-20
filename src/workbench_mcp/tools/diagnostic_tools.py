"""Workspace diagnostic MCP tools."""

from __future__ import annotations

from dataclasses import asdict

from fastmcp import FastMCP

from workbench_mcp.config import WorkbenchConfig
from workbench_mcp.services.diagnostics import DiagnosticsService
from workbench_mcp.tools.common import call_safely, sanitize_response


def register_diagnostic_tools(server: FastMCP, config: WorkbenchConfig) -> None:
    """Register workspace diagnostic tools."""

    diagnostics_service = DiagnosticsService(config)

    @server.tool(name="diagnose_workspace")
    def diagnose_workspace() -> dict[str, object]:
        """Return structured diagnostic findings."""

        result = call_safely(config, diagnostics_service.diagnose_workspace)
        return sanitize_response(config, asdict(result))
