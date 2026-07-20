from __future__ import annotations

from pathlib import Path

import pytest
from tests.helpers import make_config

from workbench_mcp.errors import WorkspaceFileError
from workbench_mcp.services.search import SearchService

RESULT_LIMIT_ONE = 1
OUTPUT_LIMIT_TEN = 10


def test_search_text_finds_plain_text_matches(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "alpha.txt").write_text("Needle\nother\nneedle\n", encoding="utf-8")
    service = SearchService(make_config(workspace))

    result = service.search_text("needle")

    assert [match.line_number for match in result.matches] == [1, 3]
    assert result.searched_files == 1
    assert result.skipped_files == 0
    assert result.truncated is False


def test_search_text_honors_case_sensitivity(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "alpha.txt").write_text("Needle\nneedle\n", encoding="utf-8")
    service = SearchService(make_config(workspace))

    result = service.search_text("needle", case_sensitive=True)

    assert [match.line_text for match in result.matches] == ["needle"]


def test_search_text_honors_glob(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "alpha.py").write_text("needle\n", encoding="utf-8")
    (workspace / "alpha.txt").write_text("needle\n", encoding="utf-8")
    service = SearchService(make_config(workspace))

    result = service.search_text("needle", glob="*.py")

    assert [match.path for match in result.matches] == ["alpha.py"]


def test_search_text_enforces_result_limit(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "alpha.txt").write_text("needle\nneedle\n", encoding="utf-8")
    service = SearchService(make_config(workspace))

    result = service.search_text("needle", result_limit=RESULT_LIMIT_ONE)

    assert len(result.matches) == RESULT_LIMIT_ONE
    assert result.truncated is True


def test_search_text_enforces_output_limit(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "alpha.txt").write_text("needle with a long surrounding line\n", encoding="utf-8")
    service = SearchService(make_config(workspace, max_output_bytes=OUTPUT_LIMIT_TEN))

    result = service.search_text("needle")

    assert result.matches == ()
    assert result.output_bytes == 0
    assert result.truncated is True


def test_search_text_skips_binary_and_oversized_files(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "ok.txt").write_text("needle\n", encoding="utf-8")
    (workspace / "bad.bin").write_bytes(b"needle\x00")
    (workspace / "large.txt").write_text("needle in a large file\n", encoding="utf-8")
    service = SearchService(make_config(workspace, max_file_size_bytes=10))

    result = service.search_text("needle")

    assert [match.path for match in result.matches] == ["ok.txt"]
    assert result.skipped_files == 2


def test_search_text_rejects_empty_query(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    service = SearchService(make_config(workspace))

    with pytest.raises(WorkspaceFileError, match="query"):
        service.search_text("")
