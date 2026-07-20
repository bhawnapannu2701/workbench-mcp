from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from workbench_mcp.tools.common import EXPECTED_TOOL_NAMES


@pytest.mark.asyncio
async def test_stdio_startup_and_real_mcp_client_interaction(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    artifact_directory = workspace / "artifacts"
    artifact_directory.mkdir()
    (workspace / "hello.txt").write_text(
        "hello over stdio\n",
        encoding="utf-8",
        newline="\n",
    )
    repo_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env.update(
        {
            "WORKSPACE_ROOT": str(workspace),
            "ARTIFACT_DIRECTORY": str(artifact_directory),
            "READ_ONLY_MODE": "true",
            "ALLOWED_COMMANDS": "python",
            "TEST_COMMANDS": json.dumps(
                [{"name": "smoke", "command": ["python", "-c", "print('ok')"]}]
            ),
            "LOG_LEVEL": "ERROR",
            "FASTMCP_SHOW_SERVER_BANNER": "false",
        }
    )
    transport = StdioTransport(
        sys.executable,
        ["-m", "workbench_mcp.server"],
        env=env,
        cwd=str(repo_root),
    )

    async with Client(transport, timeout=10, init_timeout=10) as client:
        tools = await client.list_tools()
        read_result = await client.call_tool("read_file", {"relative_path": "hello.txt"})

    assert {tool.name for tool in tools} == set(EXPECTED_TOOL_NAMES)
    assert read_result.data["content"] == "hello over stdio\n"
