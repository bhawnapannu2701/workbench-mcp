"""Approved artifact MCP tools."""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated, Literal

from fastmcp import FastMCP
from pydantic import Field

from workbench_mcp.config import WorkbenchConfig
from workbench_mcp.services.artifact_service import ArtifactService
from workbench_mcp.tools.common import call_safely, sanitize_response

ArtifactCategory = Literal["test_report", "coverage_report", "structured_log", "diagnostic_report"]


def register_artifact_tools(server: FastMCP, config: WorkbenchConfig) -> None:
    """Register approved artifact collection tools."""

    artifact_service = ArtifactService(config)

    @server.tool(name="collect_artifact")
    def collect_artifact(
        category: ArtifactCategory,
        relative_path: Annotated[str, Field(min_length=1, max_length=500)],
    ) -> dict[str, object]:
        """Collect an approved artifact from the artifact root."""

        result = call_safely(
            config,
            lambda: artifact_service.collect_artifact(category, relative_path),
        )
        return sanitize_response(config, asdict(result))
