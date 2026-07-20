from __future__ import annotations

import shutil
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from tests.helpers import make_config

from workbench_mcp.errors import GitServiceError
from workbench_mcp.services.git_service import GitService
from workbench_mcp.services.subprocess_capture import CapturedProcessBytes


def test_git_status_reports_repository_changes(tmp_path: Path) -> None:
    git = shutil.which("git")
    if git is None:
        pytest.skip("git is not available on PATH")
    workspace = tmp_path / "repo"
    workspace.mkdir()
    subprocess.run(  # noqa: S603
        [git, "init"],
        cwd=workspace,
        check=True,
        capture_output=True,
        shell=False,
    )
    staged = workspace / "staged.txt"
    staged.write_text("staged\n", encoding="utf-8")
    subprocess.run([git, "add", "staged.txt"], cwd=workspace, check=True, shell=False)  # noqa: S603
    modified = workspace / "modified.txt"
    modified.write_text("first\n", encoding="utf-8")
    subprocess.run([git, "add", "modified.txt"], cwd=workspace, check=True, shell=False)  # noqa: S603
    modified.write_text("changed\n", encoding="utf-8")
    (workspace / "untracked.txt").write_text("new\n", encoding="utf-8")
    service = GitService(make_config(workspace))

    status = service.status()

    assert status.is_repository is True
    assert status.branch is not None
    assert "staged.txt" in status.staged_files
    assert "modified.txt" in status.staged_files
    assert "modified.txt" in status.modified_files
    assert "untracked.txt" in status.untracked_files
    assert "file" in status.diff_statistics


def test_git_status_handles_non_repository(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    service = GitService(make_config(workspace))

    status = service.status()

    assert status.is_repository is False
    assert status.branch is None
    assert status.staged_files == ()


def test_git_status_uses_only_read_only_git_commands(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "repo"
    workspace.mkdir()
    captured_commands: list[tuple[str, ...]] = []

    def fake_which(executable: str) -> str | None:
        return "git" if executable == "git" else None

    def fake_run_bounded_subprocess(
        command: Sequence[str],
        *,
        cwd: Path,
        timeout_seconds: int,
        max_output_bytes: int,
        env: Mapping[str, str] | None = None,
        start_error_message: str,
    ) -> CapturedProcessBytes:
        assert cwd == workspace
        assert timeout_seconds > 0
        assert max_output_bytes > 0
        assert start_error_message.startswith("failed to start git")
        assert "--no-pager" in command
        assert "core.fsmonitor=false" in command
        assert "diff.external=" in command
        assert env is not None
        assert env["GIT_OPTIONAL_LOCKS"] == "0"
        assert env["GIT_TERMINAL_PROMPT"] == "0"
        git_args = _git_subcommand_args(command)
        captured_commands.append(git_args)
        stdout_by_args = {
            ("rev-parse", "--is-inside-work-tree"): "true\n",
            ("branch", "--show-current"): "main\n",
            ("status", "--porcelain=v1"): " M README.md\n?? new.txt\n",
            ("diff", "--no-ext-diff", "--shortstat"): " 1 file changed, 1 insertion(+)\n",
            ("diff", "--cached", "--no-ext-diff", "--shortstat"): "",
        }
        return CapturedProcessBytes(
            exit_code=0,
            duration_seconds=0.01,
            timed_out=False,
            stdout=stdout_by_args[git_args].encode("utf-8"),
            stderr=b"",
            stdout_truncated=False,
            stderr_truncated=False,
        )

    monkeypatch.setattr("workbench_mcp.services.git_service.shutil.which", fake_which)
    monkeypatch.setattr(
        "workbench_mcp.services.git_service.run_bounded_subprocess",
        fake_run_bounded_subprocess,
    )
    service = GitService(make_config(workspace))

    status = service.status()

    assert status.is_repository is True
    assert captured_commands == [
        ("rev-parse", "--is-inside-work-tree"),
        ("branch", "--show-current"),
        ("status", "--porcelain=v1"),
        ("diff", "--no-ext-diff", "--shortstat"),
        ("diff", "--cached", "--no-ext-diff", "--shortstat"),
    ]
    assert not any(
        command[0] in {"push", "pull", "fetch", "reset", "checkout", "clean", "commit", "add"}
        for command in captured_commands
    )


def test_git_status_reports_timeout_as_safe_service_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "repo"
    workspace.mkdir()

    def fake_which(executable: str) -> str | None:
        return "git" if executable == "git" else None

    def fake_run_bounded_subprocess(
        command: Sequence[str],
        *,
        cwd: Path,
        timeout_seconds: int,
        max_output_bytes: int,
        env: Mapping[str, str] | None = None,
        start_error_message: str,
    ) -> CapturedProcessBytes:
        assert command[0] == "git"
        assert cwd == workspace
        assert max_output_bytes > 0
        assert env is not None
        assert start_error_message.startswith("failed to start git")
        return CapturedProcessBytes(
            exit_code=None,
            duration_seconds=float(timeout_seconds),
            timed_out=True,
            stdout=b"",
            stderr=b"",
            stdout_truncated=False,
            stderr_truncated=False,
        )

    monkeypatch.setattr("workbench_mcp.services.git_service.shutil.which", fake_which)
    monkeypatch.setattr(
        "workbench_mcp.services.git_service.run_bounded_subprocess",
        fake_run_bounded_subprocess,
    )
    service = GitService(make_config(workspace))

    with pytest.raises(GitServiceError, match="timed out"):
        service.status()


def _git_subcommand_args(command: Sequence[str]) -> tuple[str, ...]:
    tokens = list(command[1:])
    while tokens:
        item = tokens.pop(0)
        if item == "--no-pager":
            continue
        if item == "-c":
            del tokens[0]
            continue
        return (item, *tokens)
    raise AssertionError(f"missing git subcommand in {command}")
