from __future__ import annotations

import json
from pathlib import Path

import pytest

from workbench_mcp.config import WorkbenchConfig, load_config
from workbench_mcp.errors import ConfigError

ENV_FILE_LIMIT = 2048
ENV_TIMEOUT_SECONDS = 5
ENV_OUTPUT_LIMIT = 4096
OVERRIDE_TIMEOUT_SECONDS = 3


def make_workspace(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    artifact_directory = workspace / "artifacts"
    artifact_directory.mkdir(parents=True)
    return workspace, artifact_directory


def base_environment(workspace: Path, artifact_directory: Path) -> dict[str, str]:
    return {
        "WORKSPACE_ROOT": str(workspace),
        "ARTIFACT_DIRECTORY": str(artifact_directory),
    }


def test_loads_valid_environment_configuration(tmp_path: Path) -> None:
    workspace, artifact_directory = make_workspace(tmp_path)
    test_commands = [{"name": "unit", "command": ["pytest", "tests/unit"]}]
    env = {
        **base_environment(workspace, artifact_directory),
        "READ_ONLY_MODE": "false",
        "MAX_FILE_SIZE_BYTES": str(ENV_FILE_LIMIT),
        "MAX_COMMAND_SECONDS": str(ENV_TIMEOUT_SECONDS),
        "MAX_OUTPUT_BYTES": str(ENV_OUTPUT_LIMIT),
        "ALLOWED_COMMANDS": "python,pytest",
        "TEST_COMMANDS": json.dumps(test_commands),
        "SECRET_PATTERNS": json.dumps([r"token\s*=\s*\w+"]),
        "LOG_LEVEL": "debug",
    }

    config = load_config(environ=env)

    assert config.workspace_root == workspace.resolve()
    assert config.artifact_directory == artifact_directory.resolve()
    assert config.read_only_mode is False
    assert config.max_file_size_bytes == ENV_FILE_LIMIT
    assert config.max_command_seconds == ENV_TIMEOUT_SECONDS
    assert config.max_output_bytes == ENV_OUTPUT_LIMIT
    assert [command.executable for command in config.allowed_commands] == ["python", "pytest"]
    assert config.test_commands[0].command == ("pytest", "tests/unit")
    assert config.secret_patterns == (r"token\s*=\s*\w+",)
    assert config.log_level == "DEBUG"


def test_loads_valid_toml_configuration(tmp_path: Path) -> None:
    workspace, artifact_directory = make_workspace(tmp_path)
    config_file = tmp_path / "workbench.toml"
    config_file.write_text(
        "\n".join(
            [
                "[workbench_mcp]",
                f"workspace_root = {json.dumps(str(workspace))}",
                "read_only_mode = true",
                "max_file_size_bytes = 1024",
                "max_command_seconds = 10",
                "max_output_bytes = 2048",
                'allowed_commands = [{ name = "python", executable = "python" }]',
                'test_commands = [{ name = "unit", command = ["pytest", "tests/unit"] }]',
                f"artifact_directory = {json.dumps(str(artifact_directory))}",
                'secret_patterns = ["(?i)secret\\\\s*=\\\\s*[^\\\\s]+"]',
                'log_level = "WARNING"',
            ],
        ),
        encoding="utf-8",
    )

    config = load_config(config_file, environ={})

    assert isinstance(config, WorkbenchConfig)
    assert config.workspace_root == workspace.resolve()
    assert config.read_only_mode is True
    assert config.allowed_commands[0].name == "python"
    assert config.test_commands[0].name == "unit"
    assert config.log_level == "WARNING"


def test_environment_overrides_toml_configuration(tmp_path: Path) -> None:
    workspace, artifact_directory = make_workspace(tmp_path)
    config_file = tmp_path / "workbench.toml"
    config_file.write_text(
        "\n".join(
            [
                "[workbench_mcp]",
                f"workspace_root = {json.dumps(str(workspace))}",
                f"artifact_directory = {json.dumps(str(artifact_directory))}",
                "read_only_mode = true",
                "max_command_seconds = 30",
            ],
        ),
        encoding="utf-8",
    )

    config = load_config(
        config_file,
        environ={"READ_ONLY_MODE": "false", "MAX_COMMAND_SECONDS": str(OVERRIDE_TIMEOUT_SECONDS)},
    )

    assert config.read_only_mode is False
    assert config.max_command_seconds == OVERRIDE_TIMEOUT_SECONDS


def test_invalid_numeric_limit_fails_fast(tmp_path: Path) -> None:
    workspace, artifact_directory = make_workspace(tmp_path)
    env = {
        **base_environment(workspace, artifact_directory),
        "MAX_FILE_SIZE_BYTES": "0",
    }

    with pytest.raises(ConfigError, match="max_file_size_bytes"):
        load_config(environ=env)


def test_missing_workspace_fails_fast(tmp_path: Path) -> None:
    missing_workspace = tmp_path / "missing"
    artifact_directory = tmp_path / "artifacts"
    artifact_directory.mkdir()
    env = base_environment(missing_workspace, artifact_directory)

    with pytest.raises(ConfigError, match="workspace_root does not exist"):
        load_config(environ=env)


def test_malformed_toml_fails_fast(tmp_path: Path) -> None:
    config_file = tmp_path / "broken.toml"
    config_file.write_text("[workbench_mcp\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="Malformed TOML"):
        load_config(config_file, environ={})


def test_invalid_allowed_command_configuration_fails_fast(tmp_path: Path) -> None:
    workspace, artifact_directory = make_workspace(tmp_path)
    env = {
        **base_environment(workspace, artifact_directory),
        "ALLOWED_COMMANDS": json.dumps([{"name": "bad", "executable": "python -m"}]),
    }

    with pytest.raises(ConfigError, match="executable"):
        load_config(environ=env)


def test_invalid_test_command_configuration_fails_fast(tmp_path: Path) -> None:
    workspace, artifact_directory = make_workspace(tmp_path)
    env = {
        **base_environment(workspace, artifact_directory),
        "TEST_COMMANDS": json.dumps([{"name": "unsafe", "command": ["pytest", "&&", "whoami"]}]),
    }

    with pytest.raises(ConfigError, match="shell operators"):
        load_config(environ=env)


def test_invalid_secret_pattern_fails_fast(tmp_path: Path) -> None:
    workspace, artifact_directory = make_workspace(tmp_path)
    env = {
        **base_environment(workspace, artifact_directory),
        "SECRET_PATTERNS": json.dumps(["["]),
    }

    with pytest.raises(ConfigError, match="invalid secret pattern"):
        load_config(environ=env)


def test_sanitized_summary_excludes_secret_patterns(tmp_path: Path) -> None:
    workspace, artifact_directory = make_workspace(tmp_path)
    config = load_config(environ=base_environment(workspace, artifact_directory))

    summary = config.sanitized_summary()

    assert "secret_patterns" not in summary
    assert summary["secret_pattern_count"] == 1
