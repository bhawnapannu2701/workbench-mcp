"""Approved artifact collection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from workbench_mcp.config import WorkbenchConfig
from workbench_mcp.errors import ArtifactAccessError, PathSecurityError
from workbench_mcp.security.limits import truncate_text
from workbench_mcp.security.paths import SafePath, resolve_contained_path
from workbench_mcp.security.redaction import Redactor

APPROVED_ARTIFACT_CATEGORIES: dict[str, tuple[str, frozenset[str]]] = {
    "test_report": ("test-reports", frozenset({".json", ".xml", ".txt", ".log"})),
    "coverage_report": ("coverage", frozenset({".json", ".xml", ".html", ".txt"})),
    "structured_log": ("logs", frozenset({".json", ".jsonl", ".log"})),
    "diagnostic_report": ("diagnostics", frozenset({".json"})),
}


@dataclass(frozen=True)
class Artifact:
    """Collected approved artifact content."""

    category: str
    path: str
    size_bytes: int
    content: str
    truncated: bool


class ArtifactService:
    """Collect only approved files under the configured artifact directory."""

    def __init__(self, config: WorkbenchConfig) -> None:
        self._config = config
        self._redactor = Redactor.from_patterns(config.secret_patterns)

    def collect_artifact(self, category: str, relative_path: str | Path) -> Artifact:
        """Read an approved text artifact with traversal and symlink protection."""

        if category not in APPROVED_ARTIFACT_CATEGORIES:
            msg = f"artifact category is not approved: {category}"
            raise ArtifactAccessError(msg)
        category_directory, allowed_suffixes = APPROVED_ARTIFACT_CATEGORIES[category]
        category_root = self._config.artifact_directory / category_directory
        safe_path = _resolve_existing_artifact(category_root, relative_path)
        if safe_path.resolved.suffix.lower() not in allowed_suffixes:
            msg = f"artifact suffix is not approved for {category}: {safe_path.resolved.suffix}"
            raise ArtifactAccessError(msg)
        if not safe_path.resolved.is_file():
            msg = f"artifact path is not a file: {relative_path}"
            raise ArtifactAccessError(msg)

        content_bytes = safe_path.resolved.read_bytes()
        if b"\x00" in content_bytes[:4096]:
            msg = "artifact appears to be binary and cannot be collected as text"
            raise ArtifactAccessError(msg)
        content = self._redactor.redact(content_bytes.decode("utf-8", errors="replace"))
        content, truncated = truncate_text(content, self._config.max_output_bytes)
        return Artifact(
            category=category,
            path=f"{category_directory}/{safe_path.display_path}",
            size_bytes=len(content_bytes),
            content=content,
            truncated=truncated,
        )


def _resolve_existing_artifact(category_root: Path, relative_path: str | Path) -> SafePath:
    try:
        return resolve_contained_path(category_root, relative_path)
    except PathSecurityError as exc:
        msg = f"artifact path is not approved: {relative_path}"
        raise ArtifactAccessError(msg) from exc
