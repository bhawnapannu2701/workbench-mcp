from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from tests.helpers import make_config, python_allowed_command

from workbench_mcp.config import TestCommand as ConfigTestCommand
from workbench_mcp.config import WorkbenchConfig
from workbench_mcp.server import create_server
from workbench_mcp.services.filesystem import DirectoryListing, FileSystemService, TextFile
from workbench_mcp.services.git_service import GitService, GitStatus
from workbench_mcp.services.process_runner import ProcessResult, ProcessRunner
from workbench_mcp.tools.common import EXPECTED_TOOL_NAMES, SERVER_INFO_RESOURCE_URI

DESTRUCTIVE_TOOL_NAMES = {
    "push",
    "git_push",
    "reset",
    "hard_reset",
    "delete_file",
    "delete_branch",
    "run_shell",
}


@pytest.mark.asyncio
async def test_exact_expected_mcp_tools_are_registered(tmp_path: Path) -> None:
    server = create_server(make_configured_workspace(tmp_path))

    async with Client(server) as client:
        tools = await client.list_tools()

    assert {tool.name for tool in tools} == set(EXPECTED_TOOL_NAMES)


@pytest.mark.asyncio
async def test_no_unexpected_destructive_tool_is_registered(tmp_path: Path) -> None:
    server = create_server(make_configured_workspace(tmp_path))

    async with Client(server) as client:
        tool_names = {tool.name for tool in await client.list_tools()}

    assert tool_names.isdisjoint(DESTRUCTIVE_TOOL_NAMES)


def test_server_startup_succeeds(tmp_path: Path) -> None:
    server = create_server(make_configured_workspace(tmp_path))

    assert isinstance(server, FastMCP)


@pytest.mark.asyncio
async def test_tool_inputs_are_validated(tmp_path: Path) -> None:
    server = create_server(make_configured_workspace(tmp_path))

    async with Client(server) as client:
        with pytest.raises(ToolError, match="minimum of 0"):
            await client.call_tool("list_files", {"max_depth": -1})


@pytest.mark.asyncio
async def test_invalid_inputs_return_safe_errors(tmp_path: Path) -> None:
    config = make_configured_workspace(tmp_path)
    server = create_server(config)

    async with Client(server) as client:
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("read_file", {"relative_path": "../secret.txt"})

    assert str(config.workspace_root) not in str(exc_info.value)
    assert "traversal" in str(exc_info.value)


@pytest.mark.asyncio
async def test_workspace_info_returns_sanitized_data(tmp_path: Path) -> None:
    workspace = tmp_path / "topsecret-workspace"
    workspace.mkdir()
    config = make_config(workspace, secret_patterns=(r"topsecret",))
    server = create_server(config)

    async with Client(server) as client:
        result = await client.call_tool("workspace_info", {})

    payload = json.dumps(result.data)
    assert str(config.workspace_root) not in payload
    assert "topsecret" not in payload
    assert result.data["workspace"]["name"] == "[REDACTED]-workspace"


@pytest.mark.asyncio
async def test_list_files_calls_secure_filesystem_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: dict[str, object] = {}

    def fake_list_files(
        _self: FileSystemService,
        relative_directory: str | Path = ".",
        *,
        max_depth: int = 2,
        pattern: str | None = None,
        max_results: int = 1000,
    ) -> DirectoryListing:
        called.update(
            {
                "relative_directory": relative_directory,
                "max_depth": max_depth,
                "pattern": pattern,
                "max_results": max_results,
            }
        )
        return DirectoryListing(directory=".", entries=(), truncated=False)

    monkeypatch.setattr(FileSystemService, "list_files", fake_list_files)
    server = create_server(make_configured_workspace(tmp_path))

    async with Client(server) as client:
        result = await client.call_tool(
            "list_files",
            {
                "relative_directory": "src",
                "max_depth": 3,
                "pattern": "*.py",
                "max_results": 7,
            },
        )

    assert called == {
        "relative_directory": "src",
        "max_depth": 3,
        "pattern": "*.py",
        "max_results": 7,
    }
    assert result.data == {"directory": ".", "entries": [], "truncated": False}


@pytest.mark.asyncio
async def test_read_file_calls_secure_filesystem_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: dict[str, object] = {}

    def fake_read_text_file(
        _self: FileSystemService,
        relative_path: str | Path,
        *,
        start_line: int | None = None,
        line_count: int | None = None,
    ) -> TextFile:
        called.update(
            {
                "relative_path": relative_path,
                "start_line": start_line,
                "line_count": line_count,
            }
        )
        return TextFile(
            path="notes.txt",
            content="line two\n",
            start_line=2,
            returned_lines=1,
            total_lines=3,
            size_bytes=20,
        )

    monkeypatch.setattr(FileSystemService, "read_text_file", fake_read_text_file)
    server = create_server(make_configured_workspace(tmp_path))

    async with Client(server) as client:
        result = await client.call_tool(
            "read_file",
            {"relative_path": "notes.txt", "start_line": 2, "line_count": 1},
        )

    assert called == {"relative_path": "notes.txt", "start_line": 2, "line_count": 1}
    assert result.data["content"] == "line two\n"


@pytest.mark.asyncio
async def test_read_file_response_redacts_configured_secrets(tmp_path: Path) -> None:
    config = make_configured_workspace(tmp_path)
    (config.workspace_root / "secrets.txt").write_text(
        "SECRET=topsecret\n",
        encoding="utf-8",
        newline="\n",
    )
    server = create_server(config)

    async with Client(server) as client:
        result = await client.call_tool("read_file", {"relative_path": "secrets.txt"})

    assert "topsecret" not in result.data["content"]
    assert "[REDACTED]" in result.data["content"]


@pytest.mark.asyncio
async def test_search_text_enforces_limits(tmp_path: Path) -> None:
    config = make_configured_workspace(tmp_path)
    (config.workspace_root / "one.txt").write_text(
        "needle\nneedle\n",
        encoding="utf-8",
        newline="\n",
    )
    server = create_server(config)

    async with Client(server) as client:
        result = await client.call_tool(
            "search_text",
            {"query": "needle", "result_limit": 1},
        )

    assert result.data["truncated"] is True
    assert len(result.data["matches"]) == 1


@pytest.mark.asyncio
async def test_apply_patch_respects_read_only_mode(tmp_path: Path) -> None:
    config = make_configured_workspace(tmp_path, read_only=True)
    (config.workspace_root / "notes.txt").write_text(
        "before\n",
        encoding="utf-8",
        newline="\n",
    )
    server = create_server(config)

    async with Client(server) as client:
        with pytest.raises(ToolError, match="READ_ONLY_MODE"):
            await client.call_tool(
                "apply_patch",
                {
                    "relative_path": "notes.txt",
                    "expected_content": "before",
                    "replacement_content": "after",
                },
            )


@pytest.mark.asyncio
async def test_run_command_uses_secure_process_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: dict[str, object] = {}

    def fake_run_command(
        _self: ProcessRunner,
        command: tuple[str, ...] | list[str],
        *,
        cwd: str | Path = ".",
    ) -> ProcessResult:
        called.update({"command": tuple(command), "cwd": cwd})
        return ProcessResult(
            command=tuple(command),
            cwd=".",
            exit_code=0,
            duration_seconds=0.01,
            timed_out=False,
            stdout="ok",
            stderr="",
            stdout_truncated=False,
            stderr_truncated=False,
        )

    monkeypatch.setattr(ProcessRunner, "run_command", fake_run_command)
    server = create_server(make_configured_workspace(tmp_path))

    async with Client(server) as client:
        result = await client.call_tool(
            "run_command",
            {"command": ["python", "-c", "print('ok')"], "cwd": "."},
        )

    assert called == {"command": ("python", "-c", "print('ok')"), "cwd": "."}
    assert result.data["stdout"] == "ok"


@pytest.mark.asyncio
async def test_run_tests_accepts_only_predefined_commands(tmp_path: Path) -> None:
    server = create_server(make_configured_workspace(tmp_path))

    async with Client(server) as client:
        result = await client.call_tool("run_tests", {"test_name": "smoke"})
        with pytest.raises(ToolError, match="unknown predefined test command"):
            await client.call_tool("run_tests", {"test_name": "python"})

    assert result.data["status"] == "passed"
    assert result.data["command"] == ["python", "-c", "print('ok')"]


@pytest.mark.asyncio
async def test_git_status_remains_read_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = {"status": 0}

    def fake_status(_self: GitService) -> GitStatus:
        called["status"] += 1
        return GitStatus(
            is_repository=True,
            branch="main",
            staged_files=(),
            modified_files=("README.md",),
            untracked_files=(),
            diff_statistics="1 file changed",
        )

    monkeypatch.setattr(GitService, "status", fake_status)
    server = create_server(make_configured_workspace(tmp_path))

    async with Client(server) as client:
        result = await client.call_tool("git_status", {})

    assert called["status"] == 1
    assert result.data["branch"] == "main"
    assert result.data["modified_files"] == ["README.md"]


@pytest.mark.asyncio
async def test_collect_artifact_rejects_escaped_paths(tmp_path: Path) -> None:
    config = make_configured_workspace(tmp_path)
    report_dir = config.artifact_directory / "test-reports"
    report_dir.mkdir(parents=True)
    (report_dir / "result.json").write_text('{"ok": true}', encoding="utf-8")
    server = create_server(config)

    async with Client(server) as client:
        valid = await client.call_tool(
            "collect_artifact",
            {"category": "test_report", "relative_path": "result.json"},
        )
        with pytest.raises(ToolError, match="artifact path is not approved"):
            await client.call_tool(
                "collect_artifact",
                {"category": "test_report", "relative_path": "../outside.json"},
            )

    assert valid.data["path"] == "test-reports/result.json"


@pytest.mark.asyncio
async def test_diagnose_workspace_returns_structured_sanitized_findings(tmp_path: Path) -> None:
    config = make_configured_workspace(tmp_path)
    server = create_server(config)

    async with Client(server) as client:
        result = await client.call_tool("diagnose_workspace", {})

    findings = result.data["findings"]
    assert findings
    assert {finding["severity"] for finding in findings} <= {"info", "warning", "error"}
    assert str(config.workspace_root) not in json.dumps(result.data)


@pytest.mark.asyncio
async def test_server_information_resource_is_registered_and_safe(tmp_path: Path) -> None:
    workspace = tmp_path / "topsecret-workspace"
    workspace.mkdir()
    config = make_config(workspace, secret_patterns=(r"topsecret",))
    server = create_server(config)

    async with Client(server) as client:
        resources = await client.list_resources()
        resource_contents = await client.read_resource(SERVER_INFO_RESOURCE_URI)

    resource_names = {str(resource.uri) for resource in resources}
    payload = json.loads(resource_contents[0].text)
    assert SERVER_INFO_RESOURCE_URI in resource_names
    assert payload["registered_tool_names"] == list(EXPECTED_TOOL_NAMES)
    assert payload["supported_transports"] == ["stdio"]
    assert str(config.workspace_root) not in resource_contents[0].text
    assert "topsecret" not in resource_contents[0].text


@pytest.mark.asyncio
async def test_real_in_memory_mcp_client_server_interaction(tmp_path: Path) -> None:
    config = make_configured_workspace(tmp_path)
    (config.workspace_root / "demo.txt").write_text(
        "hello mcp\n",
        encoding="utf-8",
        newline="\n",
    )
    server = create_server(config)

    async with Client(server) as client:
        result = await client.call_tool("read_file", {"relative_path": "demo.txt"})

    assert result.data["content"] == "hello mcp\n"


def make_configured_workspace(tmp_path: Path, *, read_only: bool = True) -> WorkbenchConfig:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return make_config(
        workspace,
        read_only=read_only,
        allowed_commands=(python_allowed_command(),),
        test_commands=(ConfigTestCommand(name="smoke", command=("python", "-c", "print('ok')")),),
    )
