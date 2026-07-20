"""Validated configuration loading for workbench-mcp."""

from __future__ import annotations

import json
import os
import re
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from workbench_mcp.errors import ConfigError

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

DEFAULT_MAX_FILE_SIZE_BYTES = 1_048_576
DEFAULT_MAX_COMMAND_SECONDS = 30
DEFAULT_MAX_OUTPUT_BYTES = 1_048_576
DEFAULT_SECRET_PATTERNS = (r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*[^\s]+",)

CONFIG_PATH_ENV = "WORKBENCH_MCP_CONFIG"

ENV_FIELD_MAP = {
    "WORKSPACE_ROOT": "workspace_root",
    "READ_ONLY_MODE": "read_only_mode",
    "MAX_FILE_SIZE_BYTES": "max_file_size_bytes",
    "MAX_COMMAND_SECONDS": "max_command_seconds",
    "MAX_OUTPUT_BYTES": "max_output_bytes",
    "ALLOWED_COMMANDS": "allowed_commands",
    "TEST_COMMANDS": "test_commands",
    "ARTIFACT_DIRECTORY": "artifact_directory",
    "SECRET_PATTERNS": "secret_patterns",
    "LOG_LEVEL": "log_level",
}

SHELL_OPERATOR_TOKENS = frozenset({"&&", "||", ";", "|", ">", ">>", "<", "<<", "$(", "`"})
EXECUTABLE_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


def _reject_control_characters(value: str, field_name: str) -> str:
    if "\x00" in value or "\n" in value or "\r" in value:
        msg = f"{field_name} cannot contain control characters"
        raise ValueError(msg)
    return value


def _validate_executable_name(value: str) -> str:
    value = _reject_control_characters(value.strip(), "executable")
    if not value:
        msg = "executable cannot be empty"
        raise ValueError(msg)
    if not EXECUTABLE_PATTERN.fullmatch(value):
        msg = "executable must be a bare allowlisted command name, not a path or shell expression"
        raise ValueError(msg)
    if value in SHELL_OPERATOR_TOKENS:
        msg = "executable cannot be a shell operator"
        raise ValueError(msg)
    return value


def _validate_argument_token(value: str) -> str:
    value = _reject_control_characters(value, "command argument")
    if value in SHELL_OPERATOR_TOKENS:
        msg = "command arguments cannot be shell operators"
        raise ValueError(msg)
    return value


class AllowedCommand(BaseModel):
    """A command executable that MCP clients may request in later phases."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, pattern=r"^[A-Za-z0-9_.-]+$")
    executable: str = Field(min_length=1)
    default_args: tuple[str, ...] = ()

    @field_validator("executable")
    @classmethod
    def validate_executable(cls, value: str) -> str:
        return _validate_executable_name(value)

    @field_validator("default_args")
    @classmethod
    def validate_default_args(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_validate_argument_token(item) for item in value)


class TestCommand(BaseModel):
    """A predefined test command that MCP clients may select in later phases."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, pattern=r"^[A-Za-z0-9_.-]+$")
    command: tuple[str, ...] = Field(min_length=1)

    @field_validator("command")
    @classmethod
    def validate_command(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        executable = _validate_executable_name(value[0])
        args = tuple(_validate_argument_token(item) for item in value[1:])
        return (executable, *args)


class WorkbenchConfig(BaseModel):
    """Validated runtime configuration for the MCP server."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    workspace_root: Path = Field(default_factory=Path.cwd)
    read_only_mode: bool = True
    max_file_size_bytes: int = Field(
        default=DEFAULT_MAX_FILE_SIZE_BYTES,
        ge=1,
        le=100_000_000,
    )
    max_command_seconds: int = Field(default=DEFAULT_MAX_COMMAND_SECONDS, ge=1, le=600)
    max_output_bytes: int = Field(default=DEFAULT_MAX_OUTPUT_BYTES, ge=1, le=100_000_000)
    allowed_commands: tuple[AllowedCommand, ...] = ()
    test_commands: tuple[TestCommand, ...] = ()
    artifact_directory: Path = Path("artifacts")
    secret_patterns: tuple[str, ...] = DEFAULT_SECRET_PATTERNS
    log_level: LogLevel = "INFO"

    @field_validator("workspace_root")
    @classmethod
    def validate_workspace_root(cls, value: Path) -> Path:
        resolved = Path(value).expanduser().resolve()
        if not resolved.exists():
            msg = f"workspace_root does not exist: {resolved}"
            raise ValueError(msg)
        if not resolved.is_dir():
            msg = f"workspace_root is not a directory: {resolved}"
            raise ValueError(msg)
        return resolved

    @field_validator("secret_patterns")
    @classmethod
    def validate_secret_patterns(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for pattern in value:
            try:
                re.compile(pattern)
            except re.error as exc:
                msg = f"invalid secret pattern {pattern!r}: {exc}"
                raise ValueError(msg) from exc
        return value

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()

    @field_validator("allowed_commands")
    @classmethod
    def validate_allowed_command_names(
        cls,
        value: tuple[AllowedCommand, ...],
    ) -> tuple[AllowedCommand, ...]:
        names = [command.name for command in value]
        if len(names) != len(set(names)):
            msg = "allowed command names must be unique"
            raise ValueError(msg)
        return value

    @field_validator("test_commands")
    @classmethod
    def validate_test_command_names(cls, value: tuple[TestCommand, ...]) -> tuple[TestCommand, ...]:
        names = [command.name for command in value]
        if len(names) != len(set(names)):
            msg = "test command names must be unique"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def validate_artifact_directory(self) -> WorkbenchConfig:
        artifact_directory = self.artifact_directory.expanduser()
        if not artifact_directory.is_absolute():
            artifact_directory = self.workspace_root / artifact_directory
        resolved = artifact_directory.resolve()
        if not resolved.exists():
            msg = f"artifact_directory does not exist: {resolved}"
            raise ValueError(msg)
        if not resolved.is_dir():
            msg = f"artifact_directory is not a directory: {resolved}"
            raise ValueError(msg)
        object.__setattr__(self, "artifact_directory", resolved)
        return self

    def sanitized_summary(self) -> dict[str, object]:
        """Return non-secret configuration information suitable for diagnostics."""

        return {
            "workspace_root": str(self.workspace_root),
            "read_only_mode": self.read_only_mode,
            "max_file_size_bytes": self.max_file_size_bytes,
            "max_command_seconds": self.max_command_seconds,
            "max_output_bytes": self.max_output_bytes,
            "allowed_command_names": [command.name for command in self.allowed_commands],
            "test_command_names": [command.name for command in self.test_commands],
            "artifact_directory": str(self.artifact_directory),
            "secret_pattern_count": len(self.secret_patterns),
            "log_level": self.log_level,
        }


def load_config(
    config_path: str | Path | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> WorkbenchConfig:
    """Load configuration from optional TOML and environment variables."""

    env = os.environ if environ is None else environ
    raw_config: dict[str, Any] = {}

    configured_path = config_path if config_path is not None else env.get(CONFIG_PATH_ENV)
    if configured_path:
        raw_config.update(_load_toml_config(Path(configured_path)))

    for env_name, field_name in ENV_FIELD_MAP.items():
        if env_name in env:
            raw_config[field_name] = _parse_env_value(field_name, env[env_name])

    try:
        return WorkbenchConfig.model_validate(raw_config)
    except ValidationError as exc:
        raise ConfigError(_format_validation_error(exc)) from exc


def _load_toml_config(path: Path) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    try:
        with resolved.open("rb") as config_file:
            loaded = tomllib.load(config_file)
    except FileNotFoundError as exc:
        msg = f"Configuration file not found: {resolved}"
        raise ConfigError(msg) from exc
    except tomllib.TOMLDecodeError as exc:
        msg = f"Malformed TOML configuration in {resolved}: {exc}"
        raise ConfigError(msg) from exc

    config_table = loaded.get("workbench_mcp", loaded)
    if not isinstance(config_table, dict):
        msg = "TOML configuration must be a table"
        raise ConfigError(msg)
    return _normalize_config_keys(config_table)


def _normalize_config_keys(values: Mapping[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    reverse_env_map = dict(ENV_FIELD_MAP)
    for field_name in ENV_FIELD_MAP.values():
        reverse_env_map[field_name] = field_name

    for key, value in values.items():
        field_name = reverse_env_map.get(key, reverse_env_map.get(key.upper(), key))
        normalized[field_name] = value
    return normalized


def _parse_env_value(field_name: str, value: str) -> Any:
    if field_name == "allowed_commands":
        return _parse_allowed_commands(value)
    if field_name == "test_commands":
        return _parse_json_list(value, field_name)
    if field_name == "secret_patterns":
        return _parse_secret_patterns(value)
    return value


def _parse_allowed_commands(value: str) -> list[dict[str, object]]:
    stripped = value.strip()
    if not stripped:
        return []
    if stripped.startswith("["):
        parsed = _parse_json_list(stripped, "allowed_commands")
        return _require_dict_list(parsed, "allowed_commands")

    commands: list[dict[str, object]] = []
    for item in stripped.split(","):
        executable = item.strip()
        if executable:
            commands.append({"name": executable, "executable": executable})
    return commands


def _parse_secret_patterns(value: str) -> list[str]:
    stripped = value.strip()
    if not stripped:
        return []
    if stripped.startswith("["):
        parsed = _parse_json_list(stripped, "secret_patterns")
        if not all(isinstance(item, str) for item in parsed):
            msg = "SECRET_PATTERNS must be a JSON list of strings"
            raise ConfigError(msg)
        return parsed
    return [item.strip() for item in stripped.split(",") if item.strip()]


def _parse_json_list(value: str, field_name: str) -> list[Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        msg = f"{field_name} must be valid JSON when structured values are used: {exc}"
        raise ConfigError(msg) from exc
    if not isinstance(parsed, list):
        msg = f"{field_name} must be a JSON list"
        raise ConfigError(msg)
    return parsed


def _require_dict_list(values: list[Any], field_name: str) -> list[dict[str, object]]:
    if not all(isinstance(item, dict) for item in values):
        msg = f"{field_name} must be a list of objects"
        raise ConfigError(msg)
    return values


def _format_validation_error(exc: ValidationError) -> str:
    parts = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"])
        parts.append(f"{location}: {error['msg']}")
    return "Invalid workbench-mcp configuration: " + "; ".join(parts)
