"""Predefined test-command MCP tools."""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from workbench_mcp.config import WorkbenchConfig
from workbench_mcp.services.test_runner import TestRunner
from workbench_mcp.tools.common import call_safely, sanitize_response


def register_test_tools(server: FastMCP, config: WorkbenchConfig) -> None:
    """Register repository-defined test execution tools."""

    test_runner = TestRunner(config)

    @server.tool(name="run_tests")
    def run_tests(
        test_name: Annotated[str, Field(min_length=1, max_length=100)],
    ) -> dict[str, object]:
        """Run a named predefined test command."""

        result = call_safely(config, lambda: test_runner.run_tests(test_name))
        return sanitize_response(config, asdict(result))
