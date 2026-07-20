"""Command execution MCP tools."""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from workbench_mcp.config import WorkbenchConfig
from workbench_mcp.services.process_runner import ProcessRunner
from workbench_mcp.tools.common import call_safely, sanitize_response


def register_command_tools(server: FastMCP, config: WorkbenchConfig) -> None:
    """Register allowlisted process execution tools."""

    process_runner = ProcessRunner(config)

    @server.tool(name="run_command")
    def run_command(
        command: Annotated[list[str], Field(min_length=1, max_length=64)],
        cwd: Annotated[str, Field(min_length=1, max_length=500)] = ".",
    ) -> dict[str, object]:
        """Run one allowlisted command using argument-array execution."""

        result = call_safely(config, lambda: process_runner.run_command(command, cwd=cwd))
        return sanitize_response(config, asdict(result))
