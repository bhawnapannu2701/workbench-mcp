"""Workspace diagnostics."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from workbench_mcp.config import WorkbenchConfig
from workbench_mcp.services.git_service import GitService

Severity = Literal["info", "warning", "error"]


@dataclass(frozen=True)
class DiagnosticFinding:
    """A diagnostic finding with remediation guidance."""

    severity: Severity
    evidence: str
    probable_cause: str
    recommended_remediation: str


@dataclass(frozen=True)
class DiagnosticReport:
    """Workspace diagnostic report."""

    findings: tuple[DiagnosticFinding, ...]


class DiagnosticsService:
    """Diagnose common configuration, permission, and workspace problems."""

    def __init__(self, config: WorkbenchConfig) -> None:
        self._config = config

    def diagnose_workspace(self) -> DiagnosticReport:
        findings: list[DiagnosticFinding] = []
        self._check_workspace(findings)
        self._check_artifact_directory(findings)
        self._check_executables(findings)
        self._check_git(findings)
        findings.append(
            DiagnosticFinding(
                severity="info",
                evidence="Streamable HTTP mode is not enabled in the current server configuration.",
                probable_cause=("Phase 4 implements and verifies stdio transport only."),
                recommended_remediation=(
                    "Only check HTTP port conflicts after HTTP mode is added and enabled."
                ),
            )
        )
        return DiagnosticReport(findings=tuple(findings))

    def _check_workspace(self, findings: list[DiagnosticFinding]) -> None:
        root = self._config.workspace_root
        if not root.exists():
            findings.append(
                DiagnosticFinding(
                    severity="error",
                    evidence=f"Workspace root does not exist: {root}",
                    probable_cause="WORKSPACE_ROOT points to a missing directory.",
                    recommended_remediation=(
                        "Set WORKSPACE_ROOT to an existing repository directory."
                    ),
                )
            )
            return
        if not root.is_dir():
            findings.append(
                DiagnosticFinding(
                    severity="error",
                    evidence=f"Workspace root is not a directory: {root}",
                    probable_cause="WORKSPACE_ROOT points to a file.",
                    recommended_remediation="Set WORKSPACE_ROOT to a directory.",
                )
            )
            return
        if not _is_readable_directory(root):
            findings.append(
                DiagnosticFinding(
                    severity="error",
                    evidence=f"Workspace root is not readable: {root}",
                    probable_cause="The current OS user lacks directory read permissions.",
                    recommended_remediation="Grant read access to the workspace directory.",
                )
            )
        else:
            findings.append(
                DiagnosticFinding(
                    severity="info",
                    evidence=f"Workspace root is readable: {root}",
                    probable_cause="Workspace root is configured and accessible.",
                    recommended_remediation="No action required.",
                )
            )

        if not self._config.read_only_mode and not _can_write_directory(root):
            findings.append(
                DiagnosticFinding(
                    severity="error",
                    evidence=f"Workspace root is not writable: {root}",
                    probable_cause=(
                        "READ_ONLY_MODE is disabled but write permission is unavailable."
                    ),
                    recommended_remediation=(
                        "Enable READ_ONLY_MODE or grant workspace write permission."
                    ),
                )
            )

    def _check_artifact_directory(self, findings: list[DiagnosticFinding]) -> None:
        artifact_directory = self._config.artifact_directory
        if not artifact_directory.exists() or not artifact_directory.is_dir():
            findings.append(
                DiagnosticFinding(
                    severity="error",
                    evidence=f"Artifact directory is unavailable: {artifact_directory}",
                    probable_cause="ARTIFACT_DIRECTORY points to a missing or non-directory path.",
                    recommended_remediation=(
                        "Create the artifact directory or update ARTIFACT_DIRECTORY."
                    ),
                )
            )
            return
        if not _can_write_directory(artifact_directory):
            findings.append(
                DiagnosticFinding(
                    severity="warning",
                    evidence=f"Artifact directory is not writable: {artifact_directory}",
                    probable_cause="The current OS user cannot write reports or diagnostics.",
                    recommended_remediation=(
                        "Grant write access or choose a writable artifact directory."
                    ),
                )
            )
        else:
            findings.append(
                DiagnosticFinding(
                    severity="info",
                    evidence=f"Artifact directory is writable: {artifact_directory}",
                    probable_cause="Artifact directory is configured and usable.",
                    recommended_remediation="No action required.",
                )
            )

    def _check_executables(self, findings: list[DiagnosticFinding]) -> None:
        executable_names = {command.executable for command in self._config.allowed_commands} | {
            command.command[0] for command in self._config.test_commands
        }
        for executable in sorted(executable_names):
            if shutil.which(executable) is None:
                findings.append(
                    DiagnosticFinding(
                        severity="warning",
                        evidence=f"Executable is not on PATH: {executable}",
                        probable_cause=(
                            "An allowlisted or test executable is not installed or not on PATH."
                        ),
                        recommended_remediation=(
                            "Install the executable or update the configured command."
                        ),
                    )
                )
            else:
                findings.append(
                    DiagnosticFinding(
                        severity="info",
                        evidence=f"Executable is available on PATH: {executable}",
                        probable_cause="Configured executable can be resolved.",
                        recommended_remediation="No action required.",
                    )
                )

    def _check_git(self, findings: list[DiagnosticFinding]) -> None:
        status = GitService(self._config).status()
        if not status.is_repository:
            findings.append(
                DiagnosticFinding(
                    severity="warning",
                    evidence=f"Workspace is not a Git repository: {self._config.workspace_root}",
                    probable_cause="The workspace has no Git metadata.",
                    recommended_remediation=(
                        "Run inside a Git repository if Git status is required."
                    ),
                )
            )
            return
        findings.append(
            DiagnosticFinding(
                severity="info",
                evidence=f"Git repository detected on branch: {status.branch or '(detached)'}",
                probable_cause="Read-only Git inspection succeeded.",
                recommended_remediation="No action required.",
            )
        )


def _is_readable_directory(path: Path) -> bool:
    try:
        next(path.iterdir(), None)
    except OSError:
        return False
    return True


def _can_write_directory(path: Path) -> bool:
    try:
        with tempfile.NamedTemporaryFile(dir=path, prefix=".workbench-check-", delete=True):
            return True
    except OSError:
        return False
