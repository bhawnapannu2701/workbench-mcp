from __future__ import annotations

from pathlib import Path

import pytest

from workbench_mcp.config import WorkbenchConfig


def make_config(
    workspace: Path,
    *,
    read_only: bool = True,
    max_file_size_bytes: int = 1_048_576,
    max_output_bytes: int = 1_048_576,
) -> WorkbenchConfig:
    artifact_directory = workspace / "artifacts"
    artifact_directory.mkdir(exist_ok=True)
    return WorkbenchConfig(
        workspace_root=workspace,
        read_only_mode=read_only,
        max_file_size_bytes=max_file_size_bytes,
        max_output_bytes=max_output_bytes,
        artifact_directory=artifact_directory,
    )


def create_symlink_or_skip(link_path: Path, target_path: Path, *, is_directory: bool) -> None:
    try:
        link_path.symlink_to(target_path, target_is_directory=is_directory)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symbolic links are not available in this environment: {exc}")
