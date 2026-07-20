from __future__ import annotations

from pathlib import Path

import pytest
from tests.helpers import create_symlink_or_skip, make_config

from workbench_mcp.errors import PathEscapeError, PathTraversalError, SymlinkEscapeError
from workbench_mcp.security.paths import resolve_workspace_path
from workbench_mcp.services.filesystem import FileSystemService
from workbench_mcp.services.search import SearchService


def test_resolved_path_containment_accepts_workspace_file(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "safe.txt"
    target.write_text("safe\n", encoding="utf-8")

    result = resolve_workspace_path(workspace, "safe.txt")

    assert result.resolved == target.resolve()
    assert result.display_path == "safe.txt"


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (tmp_path / "outside.txt").write_text("outside\n", encoding="utf-8")

    with pytest.raises(PathTraversalError, match="traversal"):
        resolve_workspace_path(workspace, "../outside.txt")


def test_absolute_path_escape_is_rejected(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")

    with pytest.raises(PathEscapeError, match="outside workspace"):
        resolve_workspace_path(workspace, outside)


def test_read_file_rejects_symlink_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    create_symlink_or_skip(workspace / "escape.txt", outside, is_directory=False)
    service = FileSystemService(make_config(workspace))

    with pytest.raises(SymlinkEscapeError, match="symbolic link"):
        service.read_text_file("escape.txt")


def test_read_file_rejects_absolute_path_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    service = FileSystemService(make_config(workspace))

    with pytest.raises(PathEscapeError, match="outside workspace"):
        service.read_text_file(outside)


def test_list_files_rejects_symlink_directory_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside_directory = tmp_path / "outside"
    outside_directory.mkdir()
    create_symlink_or_skip(workspace / "escape-dir", outside_directory, is_directory=True)
    service = FileSystemService(make_config(workspace))

    with pytest.raises(SymlinkEscapeError, match="symbolic link"):
        service.list_files("escape-dir")


def test_search_rejects_path_traversal(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    service = SearchService(make_config(workspace))

    with pytest.raises(PathTraversalError, match="traversal"):
        service.search_text("needle", relative_directory="../")


def test_search_rejects_absolute_directory_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    service = SearchService(make_config(workspace))

    with pytest.raises(PathEscapeError, match="outside workspace"):
        service.search_text("needle", relative_directory=outside)
