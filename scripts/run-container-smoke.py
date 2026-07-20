"""Host-side Docker smoke runner for the workbench-mcp image."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

CONTAINER_SMOKE_REPORT = Path("diagnostics") / "container-smoke.json"


class SubprocessRunner(Protocol):
    def __call__(
        self,
        args: Sequence[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]: ...


def main() -> int:
    """Run the container smoke test with temporary host mounts."""

    parser = argparse.ArgumentParser(description="Run workbench-mcp container smoke test.")
    parser.add_argument("--image", default="workbench-mcp:local", help="Docker image tag to test.")
    args = parser.parse_args()

    docker = shutil.which("docker")
    if docker is None:
        raise SystemExit("docker executable is not available on PATH")

    try:
        result = run_container_smoke(docker=docker, image=args.image)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=os.sys.stderr)
    return result.returncode


def run_container_smoke(
    *,
    docker: str,
    image: str,
    subprocess_run: SubprocessRunner = subprocess.run,
) -> subprocess.CompletedProcess[str]:
    """Run the smoke container and verify host ownership of generated reports."""

    with tempfile.TemporaryDirectory(prefix="workbench-mcp-smoke-") as temporary_directory:
        root = Path(temporary_directory)
        workspace = root / "workspace"
        artifacts = root / "artifacts"
        workspace.mkdir()
        artifacts.mkdir()
        (workspace / "smoke.txt").write_text(
            "hello container\n",
            encoding="utf-8",
            newline="\n",
        )
        test_commands = json.dumps([{"name": "smoke", "command": ["python", "-c", "print('ok')"]}])
        container_user_args = _host_compatible_user_args()

        command = [
            docker,
            "run",
            "--rm",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,nodev,size=64m",  # noqa: S108
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            *container_user_args,
            "--network",
            "none",
            "--mount",
            f"type=bind,source={workspace},target=/workspace,readonly",
            "--mount",
            f"type=bind,source={artifacts},target=/artifacts",
            "-e",
            "WORKSPACE_ROOT=/workspace",
            "-e",
            "ARTIFACT_DIRECTORY=/artifacts",
            "-e",
            "READ_ONLY_MODE=true",
            "-e",
            "ALLOWED_COMMANDS=python",
            "-e",
            f"TEST_COMMANDS={test_commands}",
            "-e",
            "LOG_LEVEL=ERROR",
            "-e",
            "SMOKE_WORKSPACE_FILE=smoke.txt",
            "--entrypoint",
            "python",
            image,
            "/app/scripts/container-smoke-test.py",
        ]
        result = subprocess_run(command, check=False, capture_output=True, text=True)
        if result.returncode == 0:
            _verify_host_can_manage_report(artifacts)
        return result


def _host_compatible_user_args(platform_name: str | None = None) -> list[str]:
    if platform_name is None:
        platform_name = os.name
    if platform_name == "nt":
        return []
    uid = _read_posix_id("geteuid", "getuid")
    gid = _read_posix_id("getegid", "getgid")
    if uid is None or gid is None:
        return []
    if uid == 0:
        msg = "container smoke runner requires a non-root POSIX host UID"
        raise RuntimeError(msg)
    return ["--user", f"{uid}:{gid}"]


def _read_posix_id(primary_name: str, fallback_name: str) -> int | None:
    for name in (primary_name, fallback_name):
        getter = getattr(os, name, None)
        if callable(getter):
            return int(getter())
    return None


def _verify_host_can_manage_report(artifacts: Path) -> None:
    report = artifacts / CONTAINER_SMOKE_REPORT
    if not report.is_file():
        msg = f"container smoke report was not created: {report}"
        raise RuntimeError(msg)
    try:
        json.loads(report.read_text(encoding="utf-8"))
    except OSError as exc:
        msg = f"container smoke report is not readable by the host: {report}"
        raise RuntimeError(msg) from exc
    except json.JSONDecodeError as exc:
        msg = f"container smoke report is not valid JSON: {report}"
        raise RuntimeError(msg) from exc

    probe = report.with_name(".host-cleanup-probe")
    try:
        probe.write_text("ok\n", encoding="utf-8", newline="\n")
        probe.unlink()
    except OSError as exc:
        msg = f"container smoke report directory is not writable by the host: {report.parent}"
        raise RuntimeError(msg) from exc


if __name__ == "__main__":
    raise SystemExit(main())
