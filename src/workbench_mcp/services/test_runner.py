"""Repository-defined test command execution."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from workbench_mcp.config import TestCommand, WorkbenchConfig
from workbench_mcp.errors import CommandSecurityError
from workbench_mcp.services.process_runner import ProcessResult, ProcessRunner


@dataclass(frozen=True)
class TestRunResult:
    """Structured result from one configured test command."""

    name: str
    command: tuple[str, ...]
    status: str
    exit_code: int | None
    duration_seconds: float
    timed_out: bool
    output_summary: str
    report_path: str


class TestRunner:
    """Run only predefined repository test commands."""

    def __init__(self, config: WorkbenchConfig) -> None:
        self._config = config
        self._process_runner = ProcessRunner(config)

    def run_tests(self, test_name: str) -> TestRunResult:
        """Run a named predefined test command."""

        test_command = self._find_test_command(test_name)
        process_result = self._process_runner.run_predefined_command(test_command.command)
        status = _status_from_process(process_result)
        report_path = self._write_report(test_command, status, process_result)
        return TestRunResult(
            name=test_command.name,
            command=test_command.command,
            status=status,
            exit_code=process_result.exit_code,
            duration_seconds=process_result.duration_seconds,
            timed_out=process_result.timed_out,
            output_summary=_summarize_output(process_result),
            report_path=report_path,
        )

    def _find_test_command(self, test_name: str) -> TestCommand:
        for test_command in self._config.test_commands:
            if test_command.name == test_name:
                return test_command
        msg = f"unknown predefined test command: {test_name}"
        raise CommandSecurityError(msg)

    def _write_report(
        self,
        test_command: TestCommand,
        status: str,
        process_result: ProcessResult,
    ) -> str:
        report_directory = self._config.artifact_directory / "test-reports"
        report_directory.mkdir(parents=True, exist_ok=True)
        report_path = report_directory / f"{test_command.name}.json"
        payload = {
            "name": test_command.name,
            "command": list(test_command.command),
            "status": status,
            "created_at": datetime.now(tz=UTC).isoformat(),
            "process": asdict(process_result),
        }
        report_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return report_path.relative_to(self._config.artifact_directory).as_posix()


def _status_from_process(result: ProcessResult) -> str:
    if result.timed_out:
        return "timeout"
    if result.exit_code == 0:
        return "passed"
    return "failed"


def _summarize_output(result: ProcessResult) -> str:
    combined = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    if not combined:
        return ""
    return combined[:1000]
