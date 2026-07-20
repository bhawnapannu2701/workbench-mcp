"""Bounded subprocess capture with best-effort process-tree cleanup."""

from __future__ import annotations

import os
import platform
import shutil
import signal
import subprocess
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, cast

from workbench_mcp.errors import ProcessExecutionError

READ_CHUNK_BYTES = 8192
OUTPUT_JOIN_TIMEOUT_SECONDS = 2
TASKKILL_TIMEOUT_SECONDS = 5


@dataclass(frozen=True)
class CapturedProcessBytes:
    """Raw bounded subprocess capture result."""

    exit_code: int | None
    duration_seconds: float
    timed_out: bool
    stdout: bytes
    stderr: bytes
    stdout_truncated: bool
    stderr_truncated: bool


@dataclass
class _PipeCapture:
    chunks: list[bytes] = field(default_factory=list)
    captured_bytes: int = 0
    truncated: bool = False
    error: BaseException | None = None


class _OutputCollector:
    """Drain stdout/stderr concurrently while storing only a bounded prefix."""

    def __init__(self, process: subprocess.Popen[bytes], max_bytes_per_stream: int) -> None:
        if process.stdout is None or process.stderr is None:
            msg = "subprocess output pipes were not configured"
            raise ProcessExecutionError(msg)
        self._pipes = (process.stdout, process.stderr)
        self._stdout = _PipeCapture()
        self._stderr = _PipeCapture()
        self._threads = (
            threading.Thread(
                target=_read_limited_pipe,
                args=(process.stdout, max_bytes_per_stream, self._stdout),
                daemon=True,
            ),
            threading.Thread(
                target=_read_limited_pipe,
                args=(process.stderr, max_bytes_per_stream, self._stderr),
                daemon=True,
            ),
        )
        for thread in self._threads:
            thread.start()

    def finish(self) -> tuple[bytes, bytes, bool, bool]:
        """Return captured bytes after process termination."""

        for thread in self._threads:
            thread.join(timeout=OUTPUT_JOIN_TIMEOUT_SECONDS)

        if any(thread.is_alive() for thread in self._threads):
            for pipe in self._pipes:
                with suppress(OSError):
                    pipe.close()
            for thread in self._threads:
                thread.join(timeout=OUTPUT_JOIN_TIMEOUT_SECONDS)

        if any(thread.is_alive() for thread in self._threads):
            msg = "subprocess output capture did not finish after process termination"
            raise ProcessExecutionError(msg)

        for capture in (self._stdout, self._stderr):
            if capture.error is not None:
                msg = "failed while reading subprocess output"
                raise ProcessExecutionError(msg) from capture.error

        return (
            b"".join(self._stdout.chunks),
            b"".join(self._stderr.chunks),
            self._stdout.truncated,
            self._stderr.truncated,
        )


def run_bounded_subprocess(
    command: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: int,
    max_output_bytes: int,
    env: Mapping[str, str] | None = None,
    start_error_message: str,
) -> CapturedProcessBytes:
    """Run a subprocess without a shell and bound captured output memory."""

    started_at = time.monotonic()
    timed_out = False

    try:
        process = _start_process(command, cwd, env)
    except OSError as exc:
        raise ProcessExecutionError(start_error_message) from exc

    collector = _OutputCollector(process, max_output_bytes)

    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        _terminate_process_tree(process)
        try:
            process.wait(timeout=OUTPUT_JOIN_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    duration = time.monotonic() - started_at
    stdout_bytes, stderr_bytes, stdout_truncated, stderr_truncated = collector.finish()
    return CapturedProcessBytes(
        exit_code=process.returncode,
        duration_seconds=duration,
        timed_out=timed_out,
        stdout=stdout_bytes,
        stderr=stderr_bytes,
        stdout_truncated=stdout_truncated,
        stderr_truncated=stderr_truncated,
    )


def _start_process(
    command: Sequence[str],
    cwd: Path,
    env: Mapping[str, str] | None,
) -> subprocess.Popen[bytes]:
    process_env = dict(env) if env is not None else None
    if _is_windows():
        return subprocess.Popen(  # noqa: S603
            list(command),
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            env=process_env,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
    return subprocess.Popen(  # noqa: S603
        list(command),
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        env=process_env,
        start_new_session=True,
    )


def _read_limited_pipe(pipe: BinaryIO, max_bytes: int, capture: _PipeCapture) -> None:
    try:
        while True:
            chunk = pipe.read(READ_CHUNK_BYTES)
            if not chunk:
                break
            remaining = max(max_bytes - capture.captured_bytes, 0)
            if remaining > 0:
                captured = chunk[:remaining]
                capture.chunks.append(captured)
                capture.captured_bytes += len(captured)
            if len(chunk) > remaining:
                capture.truncated = True
    except OSError as exc:
        capture.error = exc
    finally:
        with suppress(OSError):
            pipe.close()


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if _is_windows():
        taskkill = shutil.which("taskkill")
        if taskkill is not None:
            try:
                subprocess.run(  # noqa: S603
                    [taskkill, "/PID", str(process.pid), "/T", "/F"],
                    check=False,
                    capture_output=True,
                    shell=False,
                    timeout=TASKKILL_TIMEOUT_SECONDS,
                )
                return
            except subprocess.TimeoutExpired:
                process.kill()
                return
        process.kill()
        return

    try:
        _terminate_posix_process_group(process)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=OUTPUT_JOIN_TIMEOUT_SECONDS)
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
