from __future__ import annotations

from pathlib import Path

import pytest
from tests.helpers import create_symlink_or_skip, make_config

from workbench_mcp.errors import (
    PathEscapeError,
    PathTraversalError,
    ReadOnlyModeError,
    SymlinkEscapeError,
)
from workbench_mcp.services.patching import PatchingService


def test_apply_patch_rejects_read_only_mode(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "notes.txt"
    target.write_text("alpha\n", encoding="utf-8")
    service = PatchingService(make_config(workspace, read_only=True))

    with pytest.raises(ReadOnlyModeError, match="READ_ONLY_MODE"):
        service.apply_patch(
            "notes.txt",
            expected_content="alpha",
            replacement_content="beta",
        )

    assert target.read_text(encoding="utf-8") == "alpha\n"


def test_apply_patch_rejects_path_traversal(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    service = PatchingService(make_config(workspace, read_only=False))

    with pytest.raises(PathTraversalError, match="traversal"):
        service.apply_patch(
            "../outside.txt",
            expected_content="outside",
            replacement_content="inside",
        )

    assert outside.read_text(encoding="utf-8") == "outside\n"


def test_apply_patch_rejects_absolute_path_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    service = PatchingService(make_config(workspace, read_only=False))

    with pytest.raises(PathEscapeError, match="outside workspace"):
        service.apply_patch(
            outside,
            expected_content="outside",
            replacement_content="inside",
        )

    assert outside.read_text(encoding="utf-8") == "outside\n"


def test_apply_patch_rejects_symlink_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    create_symlink_or_skip(workspace / "escape.txt", outside, is_directory=False)
    service = PatchingService(make_config(workspace, read_only=False))

    with pytest.raises(SymlinkEscapeError, match="symbolic link"):
        service.apply_patch(
            "escape.txt",
            expected_content="outside",
            replacement_content="inside",
        )

    assert outside.read_text(encoding="utf-8") == "outside\n"
