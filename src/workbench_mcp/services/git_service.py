"""Read-only Git status inspection."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from workbench_mcp.config import WorkbenchConfig
from workbench_mcp.errors import GitServiceError, ProcessExecutionError
from workbench_mcp.services.subprocess_capture import CapturedProcessBytes, run_bounded_subprocess

SAFE_GIT_CONFIG = (
    "-c",
    "core.fsmonitor=false",
    "-c",
    "core.pager=cat",
    "-c",
    "diff.external=",
)


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
            self._run_git("diff", "--no-ext-diff", "--shortstat").strip(),
            self._run_git("diff", "--cached", "--no-ext-diff", "--shortstat").strip(),
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
        result = self._run_git_bytes("rev-parse", "--is-inside-work-tree")
        if result.timed_out:
            msg = "git rev-parse timed out"
            raise GitServiceError(msg)
        return result.exit_code == 0 and _decode_git_output(result.stdout).strip() == "true"

    def _run_git(self, *args: str) -> str:
        result = self._run_git_bytes(*args)
        stdout = _decode_git_output(result.stdout)
        stderr = _decode_git_output(result.stderr).strip()
        if result.timed_out:
            msg = f"git {' '.join(args)} timed out"
            raise GitServiceError(msg)
        if result.stdout_truncated or result.stderr_truncated:
            msg = f"git {' '.join(args)} exceeded configured output limit"
            raise GitServiceError(msg)
        if result.exit_code != 0:
            msg = f"git {' '.join(args)} failed: {stderr}"
            raise GitServiceError(msg)
        return stdout

    def _run_git_bytes(self, *args: str) -> CapturedProcessBytes:
        if self._git_executable is None:
            msg = "git executable is not available on PATH"
            raise GitServiceError(msg)
        try:
            return run_bounded_subprocess(
                [self._git_executable, "--no-pager", *SAFE_GIT_CONFIG, *args],
                cwd=self._config.workspace_root,
                timeout_seconds=self._config.max_command_seconds,
                max_output_bytes=self._config.max_output_bytes,
                env=_git_environment(self._config.workspace_root),
                start_error_message=f"failed to start git {' '.join(args)}",
            )
        except ProcessExecutionError as exc:
            msg = str(exc)
            raise GitServiceError(msg) from exc


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
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_PAGER"] = "cat"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["PAGER"] = "cat"
    return env


def _decode_git_output(output: bytes) -> str:
    return output.decode("utf-8", errors="replace")
