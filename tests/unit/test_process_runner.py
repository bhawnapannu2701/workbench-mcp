from __future__ import annotations

from pathlib import Path

import pytest
from tests.helpers import make_config, python_allowed_command

from workbench_mcp.errors import CommandSecurityError, PathSecurityError
from workbench_mcp.services.process_runner import ProcessRunner

TIMEOUT_ASSERTION_SECONDS = 5
NON_ZERO_EXIT_CODE = 7
TRUNCATED_OUTPUT_BYTES = 10


def test_runs_allowed_executable_with_argument_array(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    config = make_config(workspace, allowed_commands=(python_allowed_command(),))
    runner = ProcessRunner(config)

    result = runner.run_command(("python", "-c", "print('hello')"))

    assert result.exit_code == 0
    assert result.stdout.splitlines() == ["hello"]
    assert result.stderr == ""
    assert result.timed_out is False
    assert result.cwd == "."


def test_blocks_unallowlisted_executable(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    runner = ProcessRunner(make_config(workspace, allowed_commands=(python_allowed_command(),)))

    with pytest.raises(CommandSecurityError, match="not allowlisted"):
        runner.run_command(("git", "status"))


def test_blocks_shell_operator_bypass_attempt(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    runner = ProcessRunner(make_config(workspace, allowed_commands=(python_allowed_command(),)))

    with pytest.raises(CommandSecurityError, match="shell-operator"):
        runner.run_command(("python", "&&", "whoami"))


def test_blocks_executable_path_bypass_attempt(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    runner = ProcessRunner(make_config(workspace, allowed_commands=(python_allowed_command(),)))

    with pytest.raises(CommandSecurityError, match="executable paths"):
        runner.run_command((r"C:\Windows\System32\cmd.exe", "/c", "echo no"))


def test_rejects_invalid_working_directory(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    runner = ProcessRunner(make_config(workspace, allowed_commands=(python_allowed_command(),)))

    with pytest.raises(PathSecurityError, match="traversal"):
        runner.run_command(("python", "-c", "print('no')"), cwd="../")


def test_reports_timeout_and_cleans_up_process(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    runner = ProcessRunner(
        make_config(
            workspace,
            allowed_commands=(python_allowed_command(),),
            max_command_seconds=1,
        )
    )

    result = runner.run_command(("python", "-c", "import time; time.sleep(10)"))

    assert result.timed_out is True
    assert result.exit_code is not None
    assert result.duration_seconds < TIMEOUT_ASSERTION_SECONDS


def test_reports_non_zero_exit(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    runner = ProcessRunner(make_config(workspace, allowed_commands=(python_allowed_command(),)))

    result = runner.run_command(("python", "-c", f"import sys; sys.exit({NON_ZERO_EXIT_CODE})"))

    assert result.exit_code == NON_ZERO_EXIT_CODE
    assert result.timed_out is False


def test_captures_stdout_and_stderr(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    runner = ProcessRunner(make_config(workspace, allowed_commands=(python_allowed_command(),)))

    result = runner.run_command(
        ("python", "-c", "import sys; print('out'); print('err', file=sys.stderr)")
    )

    assert result.stdout.splitlines() == ["out"]
    assert result.stderr.splitlines() == ["err"]


def test_truncates_output(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    runner = ProcessRunner(
        make_config(
            workspace,
            allowed_commands=(python_allowed_command(),),
            max_output_bytes=TRUNCATED_OUTPUT_BYTES,
        )
    )

    result = runner.run_command(("python", "-c", "print('x' * 100)"))

    assert result.output_truncated is True
    assert len(result.stdout.encode("utf-8")) == TRUNCATED_OUTPUT_BYTES


def test_redacts_configured_secrets(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    runner = ProcessRunner(make_config(workspace, allowed_commands=(python_allowed_command(),)))

    result = runner.run_command(("python", "-c", "print('SECRET=topsecret')"))

    assert "topsecret" not in result.stdout
    assert "[REDACTED]" in result.stdout
