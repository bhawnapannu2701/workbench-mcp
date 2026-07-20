from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from tests.helpers import make_config

from workbench_mcp.services.git_service import GitService


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

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured_commands.append(tuple(command[1:]))
        assert kwargs["cwd"] == workspace
        assert kwargs["shell"] is False
        git_args = tuple(command[1:])
        stdout_by_args = {
            ("rev-parse", "--is-inside-work-tree"): "true\n",
            ("branch", "--show-current"): "main\n",
            ("status", "--porcelain=v1"): " M README.md\n?? new.txt\n",
            ("diff", "--shortstat"): " 1 file changed, 1 insertion(+)\n",
            ("diff", "--cached", "--shortstat"): "",
        }
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=stdout_by_args[git_args],
            stderr="",
        )

    monkeypatch.setattr("workbench_mcp.services.git_service.shutil.which", fake_which)
    monkeypatch.setattr("workbench_mcp.services.git_service.subprocess.run", fake_run)
    service = GitService(make_config(workspace))

    status = service.status()

    assert status.is_repository is True
    assert captured_commands == [
        ("rev-parse", "--is-inside-work-tree"),
        ("branch", "--show-current"),
        ("status", "--porcelain=v1"),
        ("diff", "--shortstat"),
        ("diff", "--cached", "--shortstat"),
    ]
    assert not any(
        command[0] in {"push", "pull", "fetch", "reset", "checkout", "clean", "commit", "add"}
        for command in captured_commands
    )
