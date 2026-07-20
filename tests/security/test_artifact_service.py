from __future__ import annotations

from pathlib import Path

import pytest
from tests.helpers import create_symlink_or_skip, make_config

from workbench_mcp.errors import ArtifactAccessError
from workbench_mcp.services.artifact_service import ArtifactService


def test_collects_valid_approved_artifact(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    config = make_config(workspace)
    report_directory = config.artifact_directory / "test-reports"
    report_directory.mkdir()
    (report_directory / "smoke.json").write_text('{"status": "passed"}', encoding="utf-8")
    service = ArtifactService(config)

    artifact = service.collect_artifact("test_report", "smoke.json")

    assert artifact.category == "test_report"
    assert artifact.path == "test-reports/smoke.json"
    assert artifact.content == '{"status": "passed"}'
    assert artifact.truncated is False


def test_collect_artifact_truncates_large_text_without_full_output(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    config = make_config(workspace, max_output_bytes=5)
    report_directory = config.artifact_directory / "test-reports"
    report_directory.mkdir()
    (report_directory / "large.txt").write_text("abcdef", encoding="utf-8")
    service = ArtifactService(config)

    artifact = service.collect_artifact("test_report", "large.txt")

    assert artifact.size_bytes == 6
    assert artifact.content == "abcde"
    assert artifact.truncated is True


def test_collect_artifact_keeps_binary_sample_when_output_limit_is_small(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    config = make_config(workspace, max_output_bytes=5)
    report_directory = config.artifact_directory / "test-reports"
    report_directory.mkdir()
    (report_directory / "binary.log").write_bytes(b"abcde\x00hidden")
    service = ArtifactService(config)

    with pytest.raises(ArtifactAccessError, match="binary"):
        service.collect_artifact("test_report", "binary.log")


def test_rejects_artifact_path_traversal(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    config = make_config(workspace)
    service = ArtifactService(config)

    with pytest.raises(ArtifactAccessError, match="not approved"):
        service.collect_artifact("test_report", "../outside.json")


def test_rejects_absolute_artifact_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    config = make_config(workspace)
    service = ArtifactService(config)

    with pytest.raises(ArtifactAccessError, match="not approved"):
        service.collect_artifact("test_report", outside)


def test_rejects_artifact_symlink_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    config = make_config(workspace)
    report_directory = config.artifact_directory / "test-reports"
    report_directory.mkdir()
    create_symlink_or_skip(report_directory / "escape.json", outside, is_directory=False)
    service = ArtifactService(config)

    with pytest.raises(ArtifactAccessError, match="not approved"):
        service.collect_artifact("test_report", "escape.json")


def test_rejects_unapproved_artifact_category(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    service = ArtifactService(make_config(workspace))

    with pytest.raises(ArtifactAccessError, match="category"):
        service.collect_artifact("unknown", "file.json")
