from __future__ import annotations

from pathlib import Path

import pytest
from tests.helpers import make_config

from workbench_mcp.errors import (
    BinaryFileError,
    FileTooLargeError,
    InvalidRangeError,
    WorkspaceFileError,
    WorkspacePathNotFoundError,
)
from workbench_mcp.services.filesystem import FileSystemService

FIRST_LINE = 1
TWO_LINES = 2
MAX_DEPTH_ZERO = 0
RESULT_LIMIT = 3
SMALL_FILE_LIMIT = 5


def test_reads_text_file_successfully(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    file_path = workspace / "notes.txt"
    file_path.write_text("alpha\nbeta\ngamma\n", encoding="utf-8", newline="\n")
    service = FileSystemService(make_config(workspace))

    result = service.read_text_file("notes.txt")

    assert result.path == "notes.txt"
    assert result.content == "alpha\nbeta\ngamma\n"
    assert result.start_line == FIRST_LINE
    assert result.returned_lines == 3
    assert result.total_lines == 3


def test_reads_text_file_with_line_range(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "notes.txt").write_text(
        "alpha\nbeta\ngamma\n",
        encoding="utf-8",
        newline="\n",
    )
    service = FileSystemService(make_config(workspace))

    result = service.read_text_file("notes.txt", start_line=TWO_LINES, line_count=TWO_LINES)

    assert result.content == "beta\ngamma\n"
    assert result.start_line == TWO_LINES
    assert result.returned_lines == TWO_LINES
    assert result.total_lines == 3


def test_read_file_reports_missing_path(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    service = FileSystemService(make_config(workspace))

    with pytest.raises(WorkspacePathNotFoundError, match="does not exist"):
        service.read_text_file("missing.txt")


def test_read_file_rejects_oversized_file(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "large.txt").write_text("too large", encoding="utf-8")
    service = FileSystemService(make_config(workspace, max_file_size_bytes=SMALL_FILE_LIMIT))

    with pytest.raises(FileTooLargeError, match="exceeds maximum size"):
        service.read_text_file("large.txt")


def test_read_file_rejects_binary_content(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "data.bin").write_bytes(b"abc\x00def")
    service = FileSystemService(make_config(workspace))

    with pytest.raises(BinaryFileError, match="binary"):
        service.read_text_file("data.bin")


def test_read_file_rejects_invalid_line_range(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "notes.txt").write_text("alpha\n", encoding="utf-8")
    service = FileSystemService(make_config(workspace))

    with pytest.raises(InvalidRangeError, match="start_line"):
        service.read_text_file("notes.txt", start_line=0)


def test_lists_directory_with_depth_limit_and_exclusions(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "README.md").write_text("hello\n", encoding="utf-8")
    (workspace / "src").mkdir()
    (workspace / "src" / "app.py").write_text("print('hi')\n", encoding="utf-8")
    (workspace / ".git").mkdir()
    (workspace / ".git" / "config").write_text("ignored\n", encoding="utf-8")
    service = FileSystemService(make_config(workspace))

    result = service.list_files(max_depth=MAX_DEPTH_ZERO)

    paths = {entry.path for entry in result.entries}
    assert paths == {"README.md", "artifacts", "src"}
    assert all(not entry.path.startswith(".git") for entry in result.entries)
    assert result.truncated is False


def test_directory_listing_honors_pattern(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "one.py").write_text("", encoding="utf-8")
    (workspace / "two.txt").write_text("", encoding="utf-8")
    service = FileSystemService(make_config(workspace))

    result = service.list_files(pattern="*.py")

    assert [entry.path for entry in result.entries] == ["one.py"]


def test_directory_listing_enforces_result_limit(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    for index in range(5):
        (workspace / f"file-{index}.txt").write_text("x\n", encoding="utf-8")
    service = FileSystemService(make_config(workspace))

    result = service.list_files(max_results=RESULT_LIMIT)

    assert len(result.entries) == RESULT_LIMIT
    assert result.truncated is True


def test_directory_listing_rejects_invalid_limits(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    service = FileSystemService(make_config(workspace))

    with pytest.raises(WorkspaceFileError, match="max_results"):
        service.list_files(max_results=0)
