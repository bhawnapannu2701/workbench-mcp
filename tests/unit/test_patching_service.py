from __future__ import annotations

from pathlib import Path

import pytest
from tests.helpers import make_config

from workbench_mcp.errors import FileTooLargeError, PatchPreconditionError, WorkspaceFileError
from workbench_mcp.services import patching
from workbench_mcp.services.patching import PatchingService


def test_apply_patch_replaces_expected_content(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "notes.txt"
    target.write_text("alpha\nbeta\n", encoding="utf-8", newline="\n")
    service = PatchingService(make_config(workspace, read_only=False))

    result = service.apply_patch(
        "notes.txt",
        expected_content="beta\n",
        replacement_content="gamma\n",
    )

    assert target.read_text(encoding="utf-8") == "alpha\ngamma\n"
    assert result.path == "notes.txt"
    assert result.replacements == 1
    assert result.changed is True


def test_apply_patch_fails_when_expected_content_differs(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "notes.txt"
    target.write_text("alpha\nbeta\n", encoding="utf-8", newline="\n")
    service = PatchingService(make_config(workspace, read_only=False))

    with pytest.raises(PatchPreconditionError, match="matched 0 times"):
        service.apply_patch(
            "notes.txt",
            expected_content="missing",
            replacement_content="replacement",
        )

    assert target.read_text(encoding="utf-8") == "alpha\nbeta\n"


def test_apply_patch_rejects_ambiguous_expected_content(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "notes.txt").write_text("repeat\nrepeat\n", encoding="utf-8", newline="\n")
    service = PatchingService(make_config(workspace, read_only=False))

    with pytest.raises(PatchPreconditionError, match="exactly one"):
        service.apply_patch(
            "notes.txt",
            expected_content="repeat\n",
            replacement_content="once\n",
        )


def test_apply_patch_rejects_oversized_result(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "notes.txt"
    target.write_text("alpha\n", encoding="utf-8", newline="\n")
    service = PatchingService(make_config(workspace, read_only=False, max_file_size_bytes=10))

    with pytest.raises(FileTooLargeError, match="patched file would exceed"):
        service.apply_patch(
            "notes.txt",
            expected_content="alpha",
            replacement_content="replacement that is too large",
        )

    assert target.read_text(encoding="utf-8") == "alpha\n"


def test_apply_patch_preserves_original_on_atomic_replace_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "notes.txt"
    target.write_text("alpha\nbeta\n", encoding="utf-8", newline="\n")
    service = PatchingService(make_config(workspace, read_only=False))

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError(f"blocked replace from {source} to {destination}")

    monkeypatch.setattr(patching, "_replace_file", fail_replace)

    with pytest.raises(WorkspaceFileError, match="atomic write failed"):
        service.apply_patch(
            "notes.txt",
            expected_content="beta\n",
            replacement_content="gamma\n",
        )

    assert target.read_text(encoding="utf-8") == "alpha\nbeta\n"
    assert list(workspace.glob(".notes.txt.*.tmp")) == []
