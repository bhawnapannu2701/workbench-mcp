"""Safe allowlisted subprocess execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from workbench_mcp.config import WorkbenchConfig
from workbench_mcp.errors import PathSecurityError
from workbench_mcp.security.commands import validate_allowlisted_command, validate_command_tokens
from workbench_mcp.security.limits import truncate_output_pair
from workbench_mcp.security.paths import resolve_workspace_path
from workbench_mcp.security.redaction import Redactor
from workbench_mcp.services.subprocess_capture import run_bounded_subprocess


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
        captured = run_bounded_subprocess(
            command,
            cwd=safe_cwd.resolved,
            timeout_seconds=self._config.max_command_seconds,
            max_output_bytes=self._config.max_output_bytes,
            start_error_message=f"failed to start approved command: {command[0]}",
        )
        stdout = self._redactor.redact(captured.stdout.decode("utf-8", errors="replace"))
        stderr = self._redactor.redact(captured.stderr.decode("utf-8", errors="replace"))
        stdout, stderr, stdout_truncated, stderr_truncated = truncate_output_pair(
            stdout,
            stderr,
            self._config.max_output_bytes,
        )

        return ProcessResult(
            command=command,
            cwd=safe_cwd.display_path,
            exit_code=captured.exit_code,
            duration_seconds=captured.duration_seconds,
            timed_out=captured.timed_out,
            stdout=stdout,
            stderr=stderr,
            stdout_truncated=stdout_truncated or captured.stdout_truncated,
            stderr_truncated=stderr_truncated or captured.stderr_truncated,
        )
