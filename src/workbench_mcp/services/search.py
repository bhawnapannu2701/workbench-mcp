"""Safe text search over a configured workspace."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path

from workbench_mcp.config import WorkbenchConfig
from workbench_mcp.errors import (
    BinaryFileError,
    FileTooLargeError,
    PathSecurityError,
    WorkspaceFileError,
)
from workbench_mcp.security.limits import decode_text_bytes, enforce_file_size, utf8_size
from workbench_mcp.security.paths import resolve_workspace_path
from workbench_mcp.services.filesystem import DEFAULT_EXCLUDED_DIRECTORIES


@dataclass(frozen=True)
class SearchMatch:
    """A single text-search match."""

    path: str
    line_number: int
    line_text: str


@dataclass(frozen=True)
class SearchResult:
    """A bounded text-search result set."""

    query: str
    matches: tuple[SearchMatch, ...]
    truncated: bool
    searched_files: int
    skipped_files: int
    output_bytes: int


class SearchService:
    """Search UTF-8 workspace text without leaving the configured root."""

    def __init__(self, config: WorkbenchConfig) -> None:
        self._config = config

    def search_text(
        self,
        query: str,
        *,
        relative_directory: str | Path = ".",
        glob: str | None = None,
        case_sensitive: bool = False,
        result_limit: int = 100,
        max_output_bytes: int | None = None,
    ) -> SearchResult:
        """Search text files below a workspace directory."""

        if query == "":
            msg = "query cannot be empty"
            raise WorkspaceFileError(msg)
        if result_limit < 1:
            msg = "result_limit must be greater than 0"
            raise WorkspaceFileError(msg)

        output_limit = self._effective_output_limit(max_output_bytes)
        safe_path = resolve_workspace_path(self._config.workspace_root, relative_directory)
        if not safe_path.resolved.is_dir():
            msg = f"workspace path is not a directory: {safe_path.display_path}"
            raise WorkspaceFileError(msg)

        matches: list[SearchMatch] = []
        output_bytes = 0
        searched_files = 0
        skipped_files = 0
        needle = query if case_sensitive else query.casefold()

        for path in self._iter_searchable_files(safe_path.resolved, glob):
            try:
                enforce_file_size(path, self._config.max_file_size_bytes)
                content = decode_text_bytes(path.read_bytes())
            except (BinaryFileError, FileTooLargeError):
                skipped_files += 1
                continue

            searched_files += 1
            for line_number, raw_line in enumerate(content.splitlines(), start=1):
                haystack = raw_line if case_sensitive else raw_line.casefold()
                if needle not in haystack:
                    continue

                relative = path.relative_to(self._config.workspace_root).as_posix()
                match = SearchMatch(path=relative, line_number=line_number, line_text=raw_line)
                match_size = utf8_size(f"{match.path}:{match.line_number}:{match.line_text}\n")
                if len(matches) >= result_limit or output_bytes + match_size > output_limit:
                    return SearchResult(
                        query=query,
                        matches=tuple(matches),
                        truncated=True,
                        searched_files=searched_files,
                        skipped_files=skipped_files,
                        output_bytes=output_bytes,
                    )
                matches.append(match)
                output_bytes += match_size

        return SearchResult(
            query=query,
            matches=tuple(matches),
            truncated=False,
            searched_files=searched_files,
            skipped_files=skipped_files,
            output_bytes=output_bytes,
        )

    def _iter_searchable_files(self, directory: Path, glob: str | None) -> list[Path]:
        files: list[Path] = []
        for child in sorted(directory.iterdir(), key=lambda item: item.name.lower()):
            if child.is_symlink():
                continue
            if child.is_dir():
                if child.name not in DEFAULT_EXCLUDED_DIRECTORIES:
                    files.extend(self._iter_searchable_files(child, glob))
                continue
            if child.is_file():
                try:
                    safe_child = resolve_workspace_path(
                        self._config.workspace_root,
                        child.relative_to(self._config.workspace_root),
                    )
                except PathSecurityError:
                    continue
                if glob is None or fnmatch.fnmatch(safe_child.display_path, glob):
                    files.append(safe_child.resolved)
        return files

    def _effective_output_limit(self, requested_limit: int | None) -> int:
        if requested_limit is None:
            return self._config.max_output_bytes
        if requested_limit < 1:
            msg = "max_output_bytes must be greater than 0"
            raise WorkspaceFileError(msg)
        return min(requested_limit, self._config.max_output_bytes)
