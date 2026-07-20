"""Safe allowlisted subprocess execution."""

from __future__ import annotations

import os
import platform
import shutil
import signal
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from workbench_mcp.config import WorkbenchConfig
from workbench_mcp.errors import PathSecurityError, ProcessExecutionError
from workbench_mcp.security.commands import validate_allowlisted_command, validate_command_tokens
from workbench_mcp.security.limits import truncate_output_pair
from workbench_mcp.security.paths import resolve_workspace_path
from workbench_mcp.security.redaction import Redactor


@dataclass(frozen=True)
class ProcessResult:
    """Structured subprocess execution result."""

    command: tuple[str, ...]
    cwd: str
    exit_code: int | None
    duration_seconds: float
    timed_out: bool
    stdout: str
    stderr: str
    stdout_truncated: bool
    stderr_truncated: bool

    @property
    def output_truncated(self) -> bool:
        return self.stdout_truncated or self.stderr_truncated


class ProcessRunner:
    """Run subprocesses with no shell and strict workspace boundaries."""

    def __init__(self, config: WorkbenchConfig) -> None:
        self._config = config
        self._redactor = Redactor.from_patterns(config.secret_patterns)

    def run_command(
        self,
        command: tuple[str, ...] | list[str],
        *,
        cwd: str | Path = ".",
    ) -> ProcessResult:
        """Run an MCP-client requested command after allowlist validation."""

        validated = validate_allowlisted_command(command, self._config.allowed_commands)
        return self._run_validated(validated, cwd=cwd)

    def run_predefined_command(
        self,
        command: tuple[str, ...] | list[str],
        *,
        cwd: str | Path = ".",
    ) -> ProcessResult:
        """Run a repository-defined command after token and cwd validation."""

        validated = validate_command_tokens(command)
        return self._run_validated(validated, cwd=cwd)

    def _run_validated(self, command: tuple[str, ...], *, cwd: str | Path) -> ProcessResult:
        safe_cwd = resolve_workspace_path(self._config.workspace_root, cwd)
        if not safe_cwd.resolved.is_dir():
            msg = f"working directory is not a directory: {safe_cwd.display_path}"
            raise PathSecurityError(msg)
        started_at = time.monotonic()
        timed_out = False
        exit_code: int | None
        stdout_bytes: bytes
        stderr_bytes: bytes

        try:
            process = _start_process(command, safe_cwd.resolved)
        except OSError as exc:
            msg = f"failed to start approved command: {command[0]}"
            raise ProcessExecutionError(msg) from exc

        try:
            stdout_bytes, stderr_bytes = process.communicate(
                timeout=self._config.max_command_seconds
            )
            exit_code = process.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            _terminate_process_tree(process)
            try:
                stdout_bytes, stderr_bytes = process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout_bytes, stderr_bytes = process.communicate()
            exit_code = process.returncode

        duration = time.monotonic() - started_at
        stdout = self._redactor.redact(stdout_bytes.decode("utf-8", errors="replace"))
        stderr = self._redactor.redact(stderr_bytes.decode("utf-8", errors="replace"))
        stdout, stderr, stdout_truncated, stderr_truncated = truncate_output_pair(
            stdout,
            stderr,
            self._config.max_output_bytes,
        )

        return ProcessResult(
            command=command,
            cwd=safe_cwd.display_path,
            exit_code=exit_code,
            duration_seconds=duration,
            timed_out=timed_out,
            stdout=stdout,
            stderr=stderr,
            stdout_truncated=stdout_truncated,
            stderr_truncated=stderr_truncated,
        )


def _start_process(command: tuple[str, ...], cwd: Path) -> subprocess.Popen[bytes]:
    if _is_windows():
        return subprocess.Popen(  # noqa: S603
            list(command),
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
    return subprocess.Popen(  # noqa: S603
        list(command),
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        start_new_session=True,
    )


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if _is_windows():
        taskkill = shutil.which("taskkill")
        if taskkill is not None:
            subprocess.run(  # noqa: S603
                [taskkill, "/PID", str(process.pid), "/T", "/F"],
                check=False,
                capture_output=True,
                shell=False,
            )
            return
        process.kill()
        return

    try:
        _terminate_posix_process_group(process)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        _kill_posix_process_group(process)


def _is_windows() -> bool:
    return platform.system() == "Windows"


def _terminate_posix_process_group(process: subprocess.Popen[bytes]) -> None:
    _signal_posix_process_group(process, signal.SIGTERM)


def _kill_posix_process_group(process: subprocess.Popen[bytes]) -> None:
    kill_signal = cast(int, getattr(signal, "SIGKILL", signal.SIGTERM))
    _signal_posix_process_group(process, kill_signal)


def _signal_posix_process_group(process: subprocess.Popen[bytes], signal_number: int) -> None:
    killpg = getattr(os, "killpg", None)
    getpgid = getattr(os, "getpgid", None)
    if not callable(killpg) or not callable(getpgid):
        process.terminate()
        return

    typed_killpg = cast(Callable[[int, int], None], killpg)
    typed_getpgid = cast(Callable[[int], int], getpgid)
    typed_killpg(typed_getpgid(process.pid), signal_number)
