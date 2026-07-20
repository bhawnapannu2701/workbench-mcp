"""Safe workspace filesystem operations."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from workbench_mcp.config import WorkbenchConfig
from workbench_mcp.errors import InvalidRangeError, WorkspaceFileError
from workbench_mcp.security.limits import decode_text_bytes, enforce_file_size
from workbench_mcp.security.paths import resolve_workspace_path

DEFAULT_EXCLUDED_DIRECTORIES = frozenset(
    {
        ".git",
        ".hg",
        ".mypy_cache",
        ".nox",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "htmlcov",
        "node_modules",
    }
)

FileKind = Literal["file", "directory", "symlink"]


@dataclass(frozen=True)
class FileEntry:
    """A directory-listing entry."""

    path: str
    kind: FileKind
    size_bytes: int | None


@dataclass(frozen=True)
class DirectoryListing:
    """A bounded directory-listing result."""

    directory: str
    entries: tuple[FileEntry, ...]
    truncated: bool


@dataclass(frozen=True)
class TextFile:
    """A bounded text-file read result."""

    path: str
    content: str
    start_line: int
    returned_lines: int
    total_lines: int
    size_bytes: int


class FileSystemService:
    """Read-only safe filesystem service for configured workspaces."""

    def __init__(self, config: WorkbenchConfig) -> None:
        self._config = config

    def list_files(
        self,
        relative_directory: str | Path = ".",
        *,
        max_depth: int = 2,
        pattern: str | None = None,
        max_results: int = 1000,
    ) -> DirectoryListing:
        """List files below a workspace directory without following symlink escapes."""

        if max_depth < 0:
            msg = "max_depth must be greater than or equal to 0"
            raise WorkspaceFileError(msg)
        if max_results < 1:
            msg = "max_results must be greater than 0"
            raise WorkspaceFileError(msg)

        safe_path = resolve_workspace_path(self._config.workspace_root, relative_directory)
        if not safe_path.resolved.is_dir():
            msg = f"workspace path is not a directory: {safe_path.display_path}"
            raise WorkspaceFileError(msg)

        entries: list[FileEntry] = []
        truncated = self._walk_directory(
            safe_path.resolved,
            depth=0,
            max_depth=max_depth,
            pattern=pattern,
            max_results=max_results,
            entries=entries,
        )
        return DirectoryListing(
            directory=safe_path.display_path,
            entries=tuple(entries),
            truncated=truncated,
        )

    def read_text_file(
        self,
        relative_path: str | Path,
        *,
        start_line: int | None = None,
        line_count: int | None = None,
    ) -> TextFile:
        """Read a UTF-8 text file from the workspace with optional line slicing."""

        safe_path = resolve_workspace_path(self._config.workspace_root, relative_path)
        if not safe_path.resolved.is_file():
            msg = f"workspace path is not a file: {safe_path.display_path}"
            raise WorkspaceFileError(msg)

        size_bytes = enforce_file_size(safe_path.resolved, self._config.max_file_size_bytes)
        content = decode_text_bytes(safe_path.resolved.read_bytes())
        selected_content, effective_start, returned_lines, total_lines = _slice_lines(
            content,
            start_line=start_line,
            line_count=line_count,
        )
        return TextFile(
            path=safe_path.display_path,
            content=selected_content,
            start_line=effective_start,
            returned_lines=returned_lines,
            total_lines=total_lines,
            size_bytes=size_bytes,
        )

    def _walk_directory(
        self,
        directory: Path,
        *,
        depth: int,
        max_depth: int,
        pattern: str | None,
        max_results: int,
        entries: list[FileEntry],
    ) -> bool:
        try:
            children = sorted(directory.iterdir(), key=lambda child: child.name.lower())
        except OSError as exc:
            msg = f"cannot list workspace directory: {directory}"
            raise WorkspaceFileError(msg) from exc

        truncated = False
        for child in children:
            if (
                child.name in DEFAULT_EXCLUDED_DIRECTORIES
                and not child.is_symlink()
                and child.is_dir()
            ):
                continue

            entry = self._entry_for_path(child)
            if pattern is None or fnmatch.fnmatch(child.name, pattern):
                if len(entries) >= max_results:
                    return True
                entries.append(entry)

            if entry.kind == "directory" and depth < max_depth:
                child_truncated = self._walk_directory(
                    child,
                    depth=depth + 1,
                    max_depth=max_depth,
                    pattern=pattern,
                    max_results=max_results,
                    entries=entries,
                )
                truncated = truncated or child_truncated
                if len(entries) >= max_results and child_truncated:
                    return True
        return truncated

    def _entry_for_path(self, path: Path) -> FileEntry:
        if path.is_symlink():
            relative = path.relative_to(self._config.workspace_root).as_posix()
            return FileEntry(path=relative, kind="symlink", size_bytes=None)
        relative = path.resolve().relative_to(self._config.workspace_root).as_posix()
        if path.is_dir():
            return FileEntry(path=relative, kind="directory", size_bytes=None)
        return FileEntry(path=relative, kind="file", size_bytes=path.stat().st_size)


def _slice_lines(
    content: str,
    *,
    start_line: int | None,
    line_count: int | None,
) -> tuple[str, int, int, int]:
    effective_start = 1 if start_line is None else start_line
    if effective_start < 1:
        msg = "start_line must be greater than or equal to 1"
        raise InvalidRangeError(msg)
    if line_count is not None and line_count < 0:
        msg = "line_count must be greater than or equal to 0"
        raise InvalidRangeError(msg)

    lines = content.splitlines(keepends=True)
    total_lines = len(lines)
    start_index = effective_start - 1
    end_index = None if line_count is None else start_index + line_count
    selected = lines[start_index:end_index]
    return "".join(selected), effective_start, len(selected), total_lines
