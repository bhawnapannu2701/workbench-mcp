from __future__ import annotations

import importlib.util
import subprocess
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType

import pytest

RUNNER_PATH = Path(__file__).resolve().parents[2] / "scripts" / "run-container-smoke.py"
NON_ROOT_UID = 1234
NON_ROOT_GID = 5678
CONTAINER_FAILURE_EXIT_CODE = 37


def load_smoke_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("run_container_smoke_script", RUNNER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_posix_smoke_runner_uses_host_uid_gid(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = load_smoke_runner()
    monkeypatch.setattr(runner.os, "geteuid", lambda: NON_ROOT_UID, raising=False)
    monkeypatch.setattr(runner.os, "getegid", lambda: NON_ROOT_GID, raising=False)

    user_args = runner._host_compatible_user_args(platform_name="posix")

    assert user_args == ["--user", f"{NON_ROOT_UID}:{NON_ROOT_GID}"]


def test_windows_smoke_runner_does_not_call_posix_id_apis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = load_smoke_runner()

    def unavailable_posix_id() -> int:
        raise AssertionError("POSIX UID/GID APIs should not be called on Windows")

    monkeypatch.setattr(runner.os, "geteuid", unavailable_posix_id, raising=False)
    monkeypatch.setattr(runner.os, "getegid", unavailable_posix_id, raising=False)

    assert runner._host_compatible_user_args(platform_name="nt") == []


def test_posix_root_uid_is_rejected_to_keep_container_non_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = load_smoke_runner()
    monkeypatch.setattr(runner.os, "geteuid", lambda: 0, raising=False)
    monkeypatch.setattr(runner.os, "getegid", lambda: 0, raising=False)

    with pytest.raises(RuntimeError, match="non-root POSIX host UID"):
        runner._host_compatible_user_args(platform_name="posix")


def test_successful_smoke_report_is_read_and_temporary_directory_is_cleaned_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = load_smoke_runner()
    temporary_roots: list[Path] = []
    observed_command: list[str] = []
    monkeypatch.setattr(
        runner,
        "_host_compatible_user_args",
        lambda: ["--user", f"{NON_ROOT_UID}:{NON_ROOT_GID}"],
    )

    def fake_subprocess_run(
        args: Sequence[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        assert check is False
        assert capture_output is True
        assert text is True
        command = list(args)
        observed_command.extend(command)
        artifacts = _mount_source(command, "/artifacts")
        temporary_roots.append(artifacts.parent)
        report = artifacts / "diagnostics" / "container-smoke.json"
        report.parent.mkdir()
        report.write_text('{"container_smoke": true}', encoding="utf-8", newline="\n")
        return subprocess.CompletedProcess(
            command,
            0,
            stdout='{"effective_user_id": 1234, "status": "ok"}\n',
            stderr="",
        )

    result = runner.run_container_smoke(
        docker="docker",
        image="workbench-mcp:test",
        subprocess_run=fake_subprocess_run,
    )

    assert result.returncode == 0
    assert _option_value(observed_command, "--user") == f"{NON_ROOT_UID}:{NON_ROOT_GID}"
    assert _option_value(observed_command, "--user").split(":", maxsplit=1)[0] != "0"
    assert temporary_roots
    assert not temporary_roots[0].exists()


def test_unexpected_container_failure_remains_non_zero_and_cleans_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = load_smoke_runner()
    temporary_roots: list[Path] = []
    monkeypatch.setattr(runner, "_host_compatible_user_args", lambda: [])

    def fake_subprocess_run(
        args: Sequence[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        assert check is False
        assert capture_output is True
        assert text is True
        command = list(args)
        artifacts = _mount_source(command, "/artifacts")
        temporary_roots.append(artifacts.parent)
        return subprocess.CompletedProcess(
            command,
            CONTAINER_FAILURE_EXIT_CODE,
            stdout="",
            stderr="boom\n",
        )

    result = runner.run_container_smoke(
        docker="docker",
        image="workbench-mcp:test",
        subprocess_run=fake_subprocess_run,
    )

    assert result.returncode == CONTAINER_FAILURE_EXIT_CODE
    assert temporary_roots
    assert not temporary_roots[0].exists()


def _mount_source(command: Sequence[str], target: str) -> Path:
    prefix = "type=bind,source="
    target_marker = f",target={target}"
    for value in command:
        if value.startswith(prefix) and target_marker in value:
            return Path(value.removeprefix(prefix).split(target_marker, maxsplit=1)[0])
    raise AssertionError(f"missing bind mount for {target}")


def _option_value(command: Sequence[str], option: str) -> str:
    index = command.index(option)
    return command[index + 1]
