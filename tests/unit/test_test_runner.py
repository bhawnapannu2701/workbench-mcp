from __future__ import annotations

import json
from pathlib import Path

import pytest
from tests.helpers import make_config

from workbench_mcp.config import TestCommand as ConfigTestCommand
from workbench_mcp.errors import CommandSecurityError
from workbench_mcp.services.test_runner import TestRunner as RepositoryTestRunner

FAILED_EXIT_CODE = 3


def test_runs_only_predefined_test_command_and_writes_report(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    config = make_config(
        workspace,
        test_commands=(ConfigTestCommand(name="smoke", command=("python", "-c", "print('ok')")),),
    )
    runner = RepositoryTestRunner(config)

    result = runner.run_tests("smoke")

    assert result.status == "passed"
    assert result.exit_code == 0
    assert result.output_summary == "ok"
    report_path = config.artifact_directory / result.report_path
    assert report_path.exists()
    assert json.loads(report_path.read_text(encoding="utf-8"))["status"] == "passed"


def test_rejects_unknown_test_command_name(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    runner = RepositoryTestRunner(make_config(workspace))

    with pytest.raises(CommandSecurityError, match="unknown"):
        runner.run_tests("not-configured")


def test_reports_failed_predefined_test_command(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    config = make_config(
        workspace,
        test_commands=(
            ConfigTestCommand(
                name="fail",
                command=("python", "-c", f"import sys; sys.exit({FAILED_EXIT_CODE})"),
            ),
        ),
    )
    runner = RepositoryTestRunner(config)

    result = runner.run_tests("fail")

    assert result.status == "failed"
    assert result.exit_code == FAILED_EXIT_CODE
