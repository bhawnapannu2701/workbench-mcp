"""Container-local smoke test for the workbench-mcp runtime image."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

from fastmcp import Client
from fastmcp.exceptions import ToolError

from workbench_mcp.config import load_config
from workbench_mcp.server import create_server
from workbench_mcp.tools.common import EXPECTED_TOOL_NAMES, SERVER_INFO_RESOURCE_URI


def main() -> int:
    """Run the container smoke checks and print a JSON result."""

    try:
        result = asyncio.run(_run_smoke_checks())
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


async def _run_smoke_checks() -> dict[str, Any]:
    config = load_config()
    server = create_server(config)
    euid = _effective_user_id()
    if euid == 0:
        msg = "container is running as root"
        raise RuntimeError(msg)

    workspace_file = os.environ.get("SMOKE_WORKSPACE_FILE", "smoke.txt")
    workspace_content = _read_workspace_file(config.workspace_root / workspace_file)
    artifact_path = _write_diagnostic_artifact(config.artifact_directory)

    async with Client(server) as client:
        tools = [tool.name for tool in await client.list_tools()]
        resources = [
            (resource.name, str(resource.uri)) for resource in await client.list_resources()
        ]
        info = await client.call_tool("workspace_info", {})
        read_result = await client.call_tool("read_file", {"relative_path": workspace_file})
        read_only_blocked = await _tool_call_is_blocked(
            client,
            "apply_patch",
            {
                "relative_path": workspace_file,
                "expected_content": workspace_content,
                "replacement_content": "blocked\n",
            },
            "READ_ONLY_MODE",
        )
        artifact = await client.call_tool(
            "collect_artifact",
            {"category": "diagnostic_report", "relative_path": artifact_path.name},
        )
        artifact_escape_blocked = await _tool_call_is_blocked(
            client,
            "collect_artifact",
            {"category": "diagnostic_report", "relative_path": "../escape.json"},
            "artifact path is not approved",
        )
        path_escape_blocked = await _tool_call_is_blocked(
            client,
            "read_file",
            {"relative_path": "../etc/passwd"},
            "traversal",
        )

    expected_tools = list(EXPECTED_TOOL_NAMES)
    if tools != expected_tools:
        msg = f"unexpected tool registration: {tools}"
        raise RuntimeError(msg)
    if ("server_info", SERVER_INFO_RESOURCE_URI) not in resources:
        msg = f"server information resource is missing: {resources}"
        raise RuntimeError(msg)
    if workspace_content not in read_result.data["content"]:
        msg = "workspace mount file could not be read through MCP"
        raise RuntimeError(msg)
    if not read_only_blocked:
        msg = "READ_ONLY_MODE did not block apply_patch"
        raise RuntimeError(msg)
    if not artifact_escape_blocked:
        msg = "artifact path escape was not blocked"
        raise RuntimeError(msg)
    if not path_escape_blocked:
        msg = "workspace path escape was not blocked"
        raise RuntimeError(msg)

    return {
        "status": "ok",
        "effective_user_id": euid,
        "workspace_readable": True,
        "read_only_write_blocked": read_only_blocked,
        "artifact_collected": artifact.data["path"],
        "artifact_escape_blocked": artifact_escape_blocked,
        "path_escape_blocked": path_escape_blocked,
        "registered_tools": tools,
        "registered_resources": resources,
        "workspace_info_read_only": info.data["read_only_status"],
    }


def _effective_user_id() -> int | None:
    geteuid = getattr(os, "geteuid", None)
    if callable(geteuid):
        return int(geteuid())
    return None


def _read_workspace_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").splitlines()[0]


def _write_diagnostic_artifact(artifact_directory: Path) -> Path:
    diagnostic_directory = artifact_directory / "diagnostics"
    diagnostic_directory.mkdir(parents=True, exist_ok=True)
    artifact_path = diagnostic_directory / "container-smoke.json"
    artifact_path.write_text('{"container_smoke": true}', encoding="utf-8", newline="\n")
    return artifact_path


async def _tool_call_is_blocked(
    client: Client,
    tool_name: str,
    arguments: dict[str, Any],
    expected_message: str,
) -> bool:
    logging.disable(logging.CRITICAL)
    try:
        await client.call_tool(tool_name, arguments)
    except ToolError as exc:
        return expected_message in str(exc)
    finally:
        logging.disable(logging.NOTSET)
    return False


if __name__ == "__main__":
    raise SystemExit(main())
