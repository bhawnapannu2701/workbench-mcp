"""Run the public reproducible workbench-mcp demo."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastmcp import Client
from fastmcp.exceptions import ToolError

from workbench_mcp.config import AllowedCommand, TestCommand, WorkbenchConfig
from workbench_mcp.server import create_server
from workbench_mcp.tools.common import EXPECTED_TOOL_NAMES, SERVER_INFO_RESOURCE_URI

DEFAULT_REPORT = Path("artifacts") / "demo" / "workbench-demo-report.json"


@dataclass(frozen=True)
class DemoPaths:
    """Filesystem paths used by one isolated demo run."""

    temporary_root: Path
    workspace: Path
    artifacts: Path


def main(argv: Sequence[str] | None = None) -> int:
    """Run the demo and return a process exit code."""

    parser = argparse.ArgumentParser(description="Run the reproducible workbench-mcp demo.")
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT),
        help="JSON report path. CLI usage is restricted to the repository artifacts directory.",
    )
    args = parser.parse_args(argv)
    report_path = _resolve_cli_report_path(args.report, parser)

    try:
        report = asyncio.run(run_demo(report_path=report_path))
    except Exception as exc:
        failure_report = {"status": "failed", "error": _safe_error(str(exc))}
        _write_report(report_path, failure_report)
        print("Demo status: failed", file=sys.stderr)
        print(f"Report: {_display_report_path(report_path)}", file=sys.stderr)
        print(f"Error: {failure_report['error']}", file=sys.stderr)
        return 1

    _print_summary(report_path, report)
    return 0


async def run_demo(report_path: Path) -> dict[str, Any]:
    """Exercise the real server against a temporary Git workspace."""

    temporary_root_text = ""
    with tempfile.TemporaryDirectory(prefix="workbench-mcp-demo-") as temporary_directory:
        paths = _prepare_demo_workspace(Path(temporary_directory))
        temporary_root_text = str(paths.temporary_root.resolve())
        operations = await _exercise_mcp_server(paths)

    report: dict[str, Any] = {
        "status": "ok",
        "demo": "workbench-mcp reproducible public demo",
        "server": {
            "construction": "create_server(WorkbenchConfig(...))",
            "client": "fastmcp.Client(server)",
            "transport": "in-process FastMCP client/server",
        },
        "workspace": {
            "created_temporary_git_workspace": True,
            "deterministic_sample_files": [
                "README.md",
                "demo_test.py",
                "docs/guide.txt",
                "src/app.py",
            ],
        },
        "operations": operations,
        "cleanup": {
            "temporary_workspace_removed": not Path(temporary_root_text).exists(),
        },
    }
    sanitized = _sanitize_payload(
        report,
        replacements=((temporary_root_text, "<temporary_demo_root>"),),
    )
    _write_report(report_path, sanitized)
    return sanitized


def _prepare_demo_workspace(temporary_root: Path) -> DemoPaths:
    workspace = temporary_root / "workspace"
    artifacts = temporary_root / "artifacts"
    (workspace / "docs").mkdir(parents=True)
    (workspace / "src").mkdir(parents=True)
    (artifacts / "diagnostics").mkdir(parents=True)
    (workspace / "README.md").write_text(
        "# Demo Workspace\n\nA deterministic needle appears here.\n",
        encoding="utf-8",
        newline="\n",
    )
    (workspace / "src" / "app.py").write_text(
        'VALUE = "demo"\n',
        encoding="utf-8",
        newline="\n",
    )
    (workspace / "docs" / "guide.txt").write_text(
        "status: draft\n",
        encoding="utf-8",
        newline="\n",
    )
    (workspace / "demo_test.py").write_text(
        "\n".join(
            [
                "from pathlib import Path",
                "",
                "assert Path('src/app.py').read_text(encoding='utf-8') == 'VALUE = \"demo\"\\n'",
                "print('demo tests passed')",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )
    (artifacts / "diagnostics" / "demo.json").write_text(
        '{"diagnostic": "demo"}\n',
        encoding="utf-8",
        newline="\n",
    )
    _initialize_git_repository(workspace)
    return DemoPaths(temporary_root=temporary_root, workspace=workspace, artifacts=artifacts)


def _initialize_git_repository(workspace: Path) -> None:
    git = shutil.which("git")
    if git is None:
        msg = "git executable is required for the reproducible demo"
        raise RuntimeError(msg)
    init = _run_git([git, "init", "-b", "main"], workspace)
    if init.returncode != 0:
        _run_git([git, "init"], workspace, check=True)
        _run_git([git, "branch", "-M", "main"], workspace, check=True)
    _run_git([git, "add", "README.md", "demo_test.py", "docs/guide.txt", "src/app.py"], workspace)
    _run_git(
        [
            git,
            "-c",
            "user.name=Workbench Demo",
            "-c",
            "user.email=demo@example.invalid",
            "commit",
            "-m",
            "Initial demo workspace",
        ],
        workspace,
        check=True,
    )


def _run_git(
    command: Sequence[str],
    cwd: Path,
    *,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(  # noqa: S603
        list(command),
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        shell=False,
    )
    if check and result.returncode != 0:
        msg = "git command failed while preparing the demo workspace"
        raise RuntimeError(msg)
    return result


async def _exercise_mcp_server(paths: DemoPaths) -> dict[str, Any]:
    config = WorkbenchConfig(
        workspace_root=paths.workspace,
        read_only_mode=False,
        max_file_size_bytes=1_048_576,
        max_command_seconds=10,
        max_output_bytes=32_768,
        allowed_commands=(AllowedCommand(name="python", executable="python"),),
        test_commands=(TestCommand(name="demo", command=("python", "demo_test.py")),),
        artifact_directory=paths.artifacts,
        log_level="ERROR",
    )
    server = create_server(config)

    async with Client(server) as client:
        tools = [tool.name for tool in await client.list_tools()]
        resources = [
            {"name": resource.name, "uri": str(resource.uri)}
            for resource in await client.list_resources()
        ]
        server_info = json.loads((await client.read_resource(SERVER_INFO_RESOURCE_URI))[0].text)
        workspace_info = (await client.call_tool("workspace_info", {})).data
        listing = (
            await client.call_tool(
                "list_files",
                {"relative_directory": ".", "max_depth": 2, "max_results": 50},
            )
        ).data
        read_file = (
            await client.call_tool("read_file", {"relative_path": "README.md", "line_count": 3})
        ).data
        search = (
            await client.call_tool(
                "search_text",
                {
                    "query": "needle",
                    "relative_directory": ".",
                    "glob": "*.md",
                    "result_limit": 5,
                },
            )
        ).data
        run_tests = (await client.call_tool("run_tests", {"test_name": "demo"})).data
        collected_test_report = (
            await client.call_tool(
                "collect_artifact",
                {"category": "test_report", "relative_path": "demo.json"},
            )
        ).data
        git_status_before_patch = (await client.call_tool("git_status", {})).data
        patch = (
            await client.call_tool(
                "apply_patch",
                {
                    "relative_path": "docs/guide.txt",
                    "expected_content": "status: draft\n",
                    "replacement_content": "status: reviewed\n",
                },
            )
        ).data
        patched_file = (
            await client.call_tool("read_file", {"relative_path": "docs/guide.txt"})
        ).data
        expected_blocked = await _expect_blocked_unsafe_operation(client)
        diagnostics = (await client.call_tool("diagnose_workspace", {})).data
        git_status_after_patch = (await client.call_tool("git_status", {})).data

    _verify_demo_results(tools, resources, run_tests, patch, expected_blocked)
    return {
        "registered_tools": tools,
        "registered_resources": resources,
        "server_info_resource": server_info,
        "workspace_info": workspace_info,
        "list_files": listing,
        "read_file": read_file,
        "search_text": search,
        "run_tests": run_tests,
        "collect_artifact": collected_test_report,
        "git_status_before_patch": git_status_before_patch,
        "apply_patch": patch,
        "patched_file": patched_file,
        "expected_blocked_unsafe_operation": expected_blocked,
        "diagnose_workspace": diagnostics,
        "git_status_after_patch": git_status_after_patch,
    }


async def _expect_blocked_unsafe_operation(client: Client[Any]) -> dict[str, Any]:
    arguments = {"relative_path": "../outside.txt"}
    logging.disable(logging.CRITICAL)
    try:
        await client.call_tool("read_file", arguments)
    except ToolError as exc:
        message = str(exc)
        if "traversal" not in message:
            msg = "unsafe operation failed, but not with the expected traversal guard"
            raise RuntimeError(msg) from exc
        return {
            "tool": "read_file",
            "arguments": arguments,
            "blocked": True,
            "message": message,
        }
    finally:
        logging.disable(logging.NOTSET)
    msg = "unsafe traversal read unexpectedly succeeded"
    raise RuntimeError(msg)


def _verify_demo_results(
    tools: Sequence[str],
    resources: Sequence[dict[str, str]],
    run_tests: dict[str, Any],
    patch: dict[str, Any],
    expected_blocked: dict[str, Any],
) -> None:
    if list(tools) != list(EXPECTED_TOOL_NAMES):
        msg = "demo observed unexpected MCP tool registration"
        raise RuntimeError(msg)
    if {"name": "server_info", "uri": SERVER_INFO_RESOURCE_URI} not in resources:
        msg = "demo did not observe the server-information resource"
        raise RuntimeError(msg)
    if run_tests.get("status") != "passed":
        msg = "demo approved test command did not pass"
        raise RuntimeError(msg)
    if patch.get("changed") is not True:
        msg = "demo controlled patch did not report a change"
        raise RuntimeError(msg)
    if expected_blocked.get("blocked") is not True:
        msg = "demo unsafe operation was not blocked as expected"
        raise RuntimeError(msg)


def _resolve_cli_report_path(report: str, parser: argparse.ArgumentParser) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    artifact_root = (repo_root / "artifacts").resolve()
    raw_path = Path(report)
    candidate = raw_path if raw_path.is_absolute() else repo_root / raw_path
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(artifact_root)
    except ValueError:
        parser.error("--report must resolve inside this repository's artifacts directory")
    return resolved


def _write_report(report_path: Path, payload: dict[str, Any]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _sanitize_payload(
    value: Any,
    *,
    replacements: Sequence[tuple[str, str]],
) -> Any:
    if isinstance(value, str):
        sanitized = value
        for needle, replacement in replacements:
            if needle:
                sanitized = sanitized.replace(needle, replacement)
                sanitized = sanitized.replace(needle.replace("\\", "/"), replacement)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_payload(item, replacements=replacements) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_payload(item, replacements=replacements) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _sanitize_payload(item, replacements=replacements)
            for key, item in value.items()
            if isinstance(key, str)
        }
    return value


def _safe_error(message: str) -> str:
    return message.replace(str(Path.cwd()), "<repository_root>")


def _display_report_path(report_path: Path) -> str:
    repo_root = Path(__file__).resolve().parents[1]
    try:
        return report_path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(report_path)


def _print_summary(report_path: Path, report: dict[str, Any]) -> None:
    operations = report["operations"]
    tools = operations["registered_tools"]
    patch = operations["apply_patch"]
    blocked = operations["expected_blocked_unsafe_operation"]
    print("Demo status: ok")
    print(f"Report: {_display_report_path(report_path)}")
    print(f"Tools: {', '.join(tools)}")
    print(f"Approved test: {operations['run_tests']['status']}")
    print(f"Patch: {patch['path']} changed={patch['changed']}")
    print(f"Blocked unsafe operation: {blocked['tool']} {blocked['arguments']}")


if __name__ == "__main__":
    raise SystemExit(main())
