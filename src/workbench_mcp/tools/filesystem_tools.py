"""Filesystem and patching MCP tools."""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from workbench_mcp.config import WorkbenchConfig
from workbench_mcp.services.filesystem import FileSystemService
from workbench_mcp.services.patching import PatchingService
from workbench_mcp.services.search import SearchService
from workbench_mcp.tools.common import call_safely, sanitize_response


def register_filesystem_tools(server: FastMCP, config: WorkbenchConfig) -> None:
    """Register safe filesystem MCP tools."""

    filesystem_service = FileSystemService(config)
    search_service = SearchService(config)
    patching_service = PatchingService(config)

    @server.tool(name="list_files")
    def list_files(
        relative_directory: Annotated[str, Field(min_length=1, max_length=500)] = ".",
        max_depth: Annotated[int, Field(ge=0, le=25)] = 2,
        pattern: Annotated[str | None, Field(min_length=1, max_length=200)] = None,
        max_results: Annotated[int, Field(ge=1, le=5000)] = 1000,
    ) -> dict[str, object]:
        """List files in a workspace-contained directory."""

        result = call_safely(
            config,
            lambda: filesystem_service.list_files(
                relative_directory,
                max_depth=max_depth,
                pattern=pattern,
                max_results=max_results,
            ),
        )
        return sanitize_response(config, asdict(result))

    @server.tool(name="read_file")
    def read_file(
        relative_path: Annotated[str, Field(min_length=1, max_length=500)],
        start_line: Annotated[int | None, Field(ge=1)] = None,
        line_count: Annotated[int | None, Field(ge=0)] = None,
    ) -> dict[str, object]:
        """Read a workspace-contained UTF-8 text file."""

        result = call_safely(
            config,
            lambda: filesystem_service.read_text_file(
                relative_path,
                start_line=start_line,
                line_count=line_count,
            ),
        )
        return sanitize_response(config, asdict(result))

    @server.tool(name="search_text")
    def search_text(
        query: Annotated[str, Field(min_length=1, max_length=1000)],
        relative_directory: Annotated[str, Field(min_length=1, max_length=500)] = ".",
        glob: Annotated[str | None, Field(min_length=1, max_length=200)] = None,
        case_sensitive: bool = False,
        result_limit: Annotated[int, Field(ge=1, le=1000)] = 100,
        max_output_bytes: Annotated[int | None, Field(ge=1)] = None,
    ) -> dict[str, object]:
        """Search workspace text files with bounded results."""

        result = call_safely(
            config,
            lambda: search_service.search_text(
                query,
                relative_directory=relative_directory,
                glob=glob,
                case_sensitive=case_sensitive,
                result_limit=result_limit,
                max_output_bytes=max_output_bytes,
            ),
        )
        return sanitize_response(config, asdict(result))

    @server.tool(name="apply_patch")
    def apply_patch(
        relative_path: Annotated[str, Field(min_length=1, max_length=500)],
        expected_content: Annotated[str, Field(min_length=1)],
        replacement_content: str,
    ) -> dict[str, object]:
        """Apply one expected-content guarded replacement."""

        result = call_safely(
            config,
            lambda: patching_service.apply_patch(
                relative_path,
                expected_content=expected_content,
                replacement_content=replacement_content,
            ),
        )
        return sanitize_response(config, asdict(result))
