from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

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
