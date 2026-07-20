"""Read-only Git status inspection."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from workbench_mcp.config import WorkbenchConfig
from workbench_mcp.errors import GitServiceError


@dataclass(frozen=True)
class GitStatus:
    """Concise read-only Git status."""

    is_repository: bool
    branch: str | None
    staged_files: tuple[str, ...]
    modified_files: tuple[str, ...]
    untracked_files: tuple[str, ...]
    diff_statistics: str


class GitService:
    """Inspect Git state without credential or destructive operations."""

    def __init__(self, config: WorkbenchConfig) -> None:
        self._config = config
        self._git_executable = shutil.which("git")

    def status(self) -> GitStatus:
        """Return read-only Git status for the configured workspace."""

        if not self._is_repository():
            return GitStatus(
                is_repository=False,
                branch=None,
                staged_files=(),
                modified_files=(),
                untracked_files=(),
                diff_statistics="",
            )
        branch = self._run_git("branch", "--show-current").strip() or None
        porcelain = self._run_git("status", "--porcelain=v1")
        staged_files, modified_files, untracked_files = _parse_porcelain(porcelain)
        diff_statistics = _join_non_empty(
            self._run_git("diff", "--shortstat").strip(),
            self._run_git("diff", "--cached", "--shortstat").strip(),
        )
        return GitStatus(
            is_repository=True,
            branch=branch,
            staged_files=staged_files,
            modified_files=modified_files,
            untracked_files=untracked_files,
            diff_statistics=diff_statistics,
        )

    def _is_repository(self) -> bool:
        if not self._config.workspace_root.exists() or not self._config.workspace_root.is_dir():
            return False
        if self._git_executable is None:
            return False
        result = subprocess.run(  # noqa: S603
            [self._git_executable, "rev-parse", "--is-inside-work-tree"],
            cwd=self._config.workspace_root,
            check=False,
            capture_output=True,
            shell=False,
            text=True,
            env=_git_environment(self._config.workspace_root),
        )
        return result.returncode == 0 and result.stdout.strip() == "true"

    def _run_git(self, *args: str) -> str:
        if self._git_executable is None:
            msg = "git executable is not available on PATH"
            raise GitServiceError(msg)
        result = subprocess.run(  # noqa: S603
            [self._git_executable, *args],
            cwd=self._config.workspace_root,
            check=False,
            capture_output=True,
            shell=False,
            text=True,
            env=_git_environment(self._config.workspace_root),
        )
        if result.returncode != 0:
            msg = f"git {' '.join(args)} failed: {result.stderr.strip()}"
            raise GitServiceError(msg)
        return result.stdout


def _parse_porcelain(porcelain: str) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    staged: list[str] = []
    modified: list[str] = []
    untracked: list[str] = []
    for line in porcelain.splitlines():
        if not line:
            continue
        status = line[:2]
        path = line[3:]
        if status == "??":
            untracked.append(path)
            continue
        if status[0] != " ":
            staged.append(path)
        if status[1] != " ":
            modified.append(path)
    return tuple(staged), tuple(modified), tuple(untracked)


def _join_non_empty(*parts: str) -> str:
    return "; ".join(part for part in parts if part)


def _git_environment(workspace_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_CEILING_DIRECTORIES"] = str(workspace_root.parent)
    return env
