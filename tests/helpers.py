from __future__ import annotations

from pathlib import Path

import pytest

from workbench_mcp.config import AllowedCommand, TestCommand, WorkbenchConfig


def make_config(
    workspace: Path,
    *,
    read_only: bool = True,
    max_file_size_bytes: int = 1_048_576,
    max_output_bytes: int = 1_048_576,
    allowed_commands: tuple[AllowedCommand, ...] = (),
    test_commands: tuple[TestCommand, ...] = (),
    max_command_seconds: int = 30,
    secret_patterns: tuple[str, ...] = (r"SECRET=\w+",),
) -> WorkbenchConfig:
    artifact_directory = workspace / "artifacts"
    artifact_directory.mkdir(exist_ok=True)
    return WorkbenchConfig(
        workspace_root=workspace,
        read_only_mode=read_only,
        max_file_size_bytes=max_file_size_bytes,
        max_command_seconds=max_command_seconds,
        max_output_bytes=max_output_bytes,
        allowed_commands=allowed_commands,
        test_commands=test_commands,
        artifact_directory=artifact_directory,
        secret_patterns=secret_patterns,
    )


def python_allowed_command() -> AllowedCommand:
    return AllowedCommand(name="python", executable="python")


def create_symlink_or_skip(link_path: Path, target_path: Path, *, is_directory: bool) -> None:
    try:
        link_path.symlink_to(target_path, target_is_directory=is_directory)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symbolic links are not available in this environment: {exc}")
