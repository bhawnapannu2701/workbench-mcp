"""Resolved-path containment checks for workspace operations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from workbench_mcp.errors import (
    PathEscapeError,
    PathSecurityError,
    PathTraversalError,
    SymlinkEscapeError,
    WorkspacePathNotFoundError,
)


@dataclass(frozen=True)
class SafePath:
    """A path proven to resolve inside an approved root."""

    root: Path
    resolved: Path
    relative: Path
    requested: str

    @property
    def display_path(self) -> str:
        """Return a stable POSIX-style relative path for responses."""

        return "." if str(self.relative) == "." else self.relative.as_posix()


ContainedPath = SafePath


def ensure_within_root(root: Path, candidate: Path) -> Path:
    """Resolve a candidate path and ensure it remains inside root."""

    resolved_root = root.expanduser().resolve()
    try:
        resolved_candidate = candidate.expanduser().resolve()
    except RuntimeError as exc:
        msg = f"path cannot be resolved safely: {candidate}"
        raise PathSecurityError(msg) from exc

    if not _is_relative_to(resolved_candidate, resolved_root):
        msg = f"path resolves outside approved root: {candidate}"
        raise PathEscapeError(msg)
    return resolved_candidate


def resolve_workspace_path(
    workspace_root: Path,
    requested_path: str | Path,
    *,
    must_exist: bool = True,
) -> SafePath:
    """Resolve a requested workspace path and prove containment."""

    root = workspace_root.expanduser().resolve()
    requested = _coerce_requested_path(requested_path)
    _reject_parent_traversal(requested)

    candidate = requested if requested.is_absolute() else root / requested

    had_symlink = _has_symlink_component(root, candidate)
    try:
        resolved = candidate.expanduser().resolve(strict=must_exist)
    except FileNotFoundError as exc:
        msg = f"workspace path does not exist: {_display_requested(requested_path)}"
        raise WorkspacePathNotFoundError(msg) from exc
    except RuntimeError as exc:
        msg = f"workspace path cannot be resolved safely: {_display_requested(requested_path)}"
        raise PathSecurityError(msg) from exc

    if not _is_relative_to(resolved, root):
        if had_symlink:
            msg = f"symbolic link resolves outside workspace: {_display_requested(requested_path)}"
            raise SymlinkEscapeError(msg)
        if requested.is_absolute():
            msg = f"absolute path resolves outside workspace: {_display_requested(requested_path)}"
            raise PathEscapeError(msg)
        msg = f"path resolves outside workspace: {_display_requested(requested_path)}"
        raise PathEscapeError(msg)

    return SafePath(
        root=root,
        resolved=resolved,
        relative=resolved.relative_to(root),
        requested=_display_requested(requested_path),
    )


def resolve_contained_path(
    root: Path,
    requested_path: str | Path,
    *,
    must_exist: bool = True,
    reject_traversal: bool = True,
) -> ContainedPath:
    """Resolve a requested path inside an arbitrary approved root."""

    if reject_traversal:
        return resolve_workspace_path(root, requested_path, must_exist=must_exist)

    # Phase 3 callers currently use traversal rejection. This branch exists for future
    # service code that may need to validate generated paths without rechecking segments.
    resolved_root = root.expanduser().resolve()
    requested = _coerce_requested_path(requested_path)
    candidate = requested if requested.is_absolute() else resolved_root / requested
    resolved = candidate.expanduser().resolve(strict=must_exist)
    if not _is_relative_to(resolved, resolved_root):
        msg = f"path resolves outside approved root: {_display_requested(requested_path)}"
        raise PathEscapeError(msg)
    return SafePath(
        root=resolved_root,
        resolved=resolved,
        relative=resolved.relative_to(resolved_root),
        requested=_display_requested(requested_path),
    )


def _coerce_requested_path(requested_path: str | Path) -> Path:
    requested_text = _display_requested(requested_path)
    if "\x00" in requested_text or "\n" in requested_text or "\r" in requested_text:
        msg = "path cannot contain control characters"
        raise PathSecurityError(msg)
    if requested_text.strip() == "":
        return Path()
    return Path(requested_text)


def _reject_parent_traversal(path: Path) -> None:
    if any(part == ".." for part in path.parts):
        msg = f"path traversal is not allowed: {path}"
        raise PathTraversalError(msg)


def _has_symlink_component(root: Path, candidate: Path) -> bool:
    try:
        if not candidate.is_absolute():
            candidate = root / candidate
        relative = candidate.relative_to(root)
    except ValueError:
        return False

    current = root
    for part in relative.parts:
        current = current / part
        try:
            if current.is_symlink():
                return True
        except OSError:
            return False
    return False


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _display_requested(requested_path: str | Path) -> str:
    return str(requested_path)
