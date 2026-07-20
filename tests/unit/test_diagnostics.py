from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from tests.helpers import make_config

from workbench_mcp.config import AllowedCommand
from workbench_mcp.services import diagnostics
from workbench_mcp.services.diagnostics import DiagnosticsService


def test_diagnostics_reports_info_and_warnings(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    config = make_config(
        workspace,
        allowed_commands=(
            AllowedCommand(name="missing", executable="definitely-missing-workbench-command"),
        ),
    )
    service = DiagnosticsService(config)

    report = service.diagnose_workspace()

    severities = {finding.severity for finding in report.findings}
    evidence = "\n".join(finding.evidence for finding in report.findings)
    assert "info" in severities
    assert "warning" in severities
    assert "Executable is not on PATH" in evidence
    assert "not a Git repository" in evidence


def test_diagnostics_reports_error_when_workspace_disappears(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    config = make_config(workspace)
    shutil.rmtree(workspace)
    service = DiagnosticsService(config)

    report = service.diagnose_workspace()

    assert "error" in {finding.severity for finding in report.findings}
    assert any("Workspace root does not exist" in finding.evidence for finding in report.findings)


def test_diagnostics_reports_warning_when_artifact_directory_is_not_writable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    config = make_config(workspace)

    def fake_can_write_directory(path: Path) -> bool:
        return path != config.artifact_directory

    monkeypatch.setattr(diagnostics, "_can_write_directory", fake_can_write_directory)
    service = DiagnosticsService(config)

    report = service.diagnose_workspace()

    assert any(
        finding.severity == "warning" and "Artifact directory is not writable" in finding.evidence
        for finding in report.findings
    )
