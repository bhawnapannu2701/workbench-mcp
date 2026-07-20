"""FastMCP server bootstrap and command-line entry point."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from fastmcp import FastMCP

from workbench_mcp import __version__
from workbench_mcp.config import WorkbenchConfig, load_config
from workbench_mcp.logging_config import configure_logging
from workbench_mcp.tools.artifact_tools import register_artifact_tools
from workbench_mcp.tools.command_tools import register_command_tools
from workbench_mcp.tools.diagnostic_tools import register_diagnostic_tools
from workbench_mcp.tools.filesystem_tools import register_filesystem_tools
from workbench_mcp.tools.git_tools import register_git_tools
from workbench_mcp.tools.test_tools import register_test_tools
from workbench_mcp.tools.workspace_tools import register_workspace_tools


def load_runtime_config() -> WorkbenchConfig:
    """Load configuration and configure structured logging for startup."""

    config = load_config()
    configure_logging(config.log_level)
    return config


def create_server(config: WorkbenchConfig | None = None) -> FastMCP:
    """Create the configured FastMCP server and register all Phase 4 tools."""

    runtime_config = load_runtime_config() if config is None else config
    configure_logging(runtime_config.log_level)
    server = FastMCP(
        name="workbench-mcp",
        version=__version__,
        instructions=(
            "Secure workspace inspection and controlled development operations. "
            "All file, command, Git, artifact, and diagnostic actions are bounded "
            "by the configured workspace, artifact root, allowlists, and limits."
        ),
        strict_input_validation=True,
        mask_error_details=True,
    )
    register_workspace_tools(server, runtime_config)
    register_filesystem_tools(server, runtime_config)
    register_command_tools(server, runtime_config)
    register_test_tools(server, runtime_config)
    register_git_tools(server, runtime_config)
    register_artifact_tools(server, runtime_config)
    register_diagnostic_tools(server, runtime_config)
    return server


def main(argv: Sequence[str] | None = None) -> int:
    """Run the MCP server from the console script."""

    parser = argparse.ArgumentParser(description="Run the secure workbench-mcp server.")
    parser.add_argument(
        "--transport",
        choices=("stdio",),
        default="stdio",
        help="MCP transport to run. Phase 4 implements and verifies stdio only.",
    )
    parser.add_argument(
        "--show-banner",
        action="store_true",
        help="Show the FastMCP startup banner.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"workbench-mcp {__version__}",
    )
    args = parser.parse_args(argv)
    server = create_server()
    server.run(transport=args.transport, show_banner=args.show_banner)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
