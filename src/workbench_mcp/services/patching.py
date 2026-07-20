"""Controlled text patching for workspace files."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from workbench_mcp.config import WorkbenchConfig
from workbench_mcp.errors import (
    FileTooLargeError,
    PatchPreconditionError,
    ReadOnlyModeError,
    WorkspaceFileError,
)
from workbench_mcp.security.limits import decode_text_bytes, enforce_file_size, utf8_size
from workbench_mcp.security.paths import resolve_workspace_path


@dataclass(frozen=True)
class PatchResult:
    """Concise result from a controlled text replacement."""

    path: str
    replacements: int
    size_before_bytes: int
    size_after_bytes: int
    changed: bool
    summary: str


class PatchingService:
    """Apply expected-content guarded text replacements."""

    def __init__(self, config: WorkbenchConfig) -> None:
        self._config = config

    def apply_patch(
        self,
        relative_path: str | Path,
        *,
        expected_content: str,
        replacement_content: str,
    ) -> PatchResult:
        """Replace exactly one expected text block using an atomic file swap."""

        if self._config.read_only_mode:
            msg = "writes are blocked because READ_ONLY_MODE is enabled"
            raise ReadOnlyModeError(msg)
        if expected_content == "":
            msg = "expected_content cannot be empty"
            raise PatchPreconditionError(msg)

        safe_path = resolve_workspace_path(self._config.workspace_root, relative_path)
        if not safe_path.resolved.is_file():
            msg = f"workspace path is not a file: {safe_path.display_path}"
            raise WorkspaceFileError(msg)

        size_before = enforce_file_size(safe_path.resolved, self._config.max_file_size_bytes)
        original_text = decode_text_bytes(safe_path.resolved.read_bytes())
        occurrences = original_text.count(expected_content)
        if occurrences != 1:
            msg = f"expected_content matched {occurrences} times; exactly one match is required"
            raise PatchPreconditionError(msg)

        updated_text = original_text.replace(expected_content, replacement_content, 1)
        if updated_text == original_text:
            return PatchResult(
                path=safe_path.display_path,
                replacements=0,
                size_before_bytes=size_before,
                size_after_bytes=size_before,
                changed=False,
                summary="No change was necessary.",
            )

        size_after = utf8_size(updated_text)
        if size_after > self._config.max_file_size_bytes:
            msg = (
                "patched file would exceed maximum size: "
                f"{size_after} bytes > {self._config.max_file_size_bytes} bytes"
            )
            raise FileTooLargeError(msg)
        _atomic_write_text(safe_path.resolved, updated_text)
        return PatchResult(
            path=safe_path.display_path,
            replacements=1,
            size_before_bytes=size_before,
            size_after_bytes=size_after,
            changed=True,
            summary=(
                f"Replaced one text block in {safe_path.display_path}; "
                f"size {size_before} -> {size_after} bytes."
            ),
        )


def _atomic_write_text(path: Path, content: str) -> None:
    original_mode = path.stat().st_mode
    temp_path: Path | None = None
    file_descriptor = -1
    try:
        file_descriptor, temp_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
        )
        temp_path = Path(temp_name)
        with os.fdopen(file_descriptor, "wb") as temp_file:
            file_descriptor = -1
            temp_file.write(content.encode("utf-8"))
            temp_file.flush()
            os.fsync(temp_file.fileno())
        temp_path.chmod(original_mode)
        _replace_file(temp_path, path)
    except OSError as exc:
        if file_descriptor != -1:
            os.close(file_descriptor)
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        msg = f"atomic write failed for workspace file: {path.name}"
        raise WorkspaceFileError(msg) from exc


def _replace_file(source: Path, destination: Path) -> None:
    source.replace(destination)
