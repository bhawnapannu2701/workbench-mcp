"""Host-side Docker smoke runner for the workbench-mcp image."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def main() -> int:
    """Run the container smoke test with temporary host mounts."""

    parser = argparse.ArgumentParser(description="Run workbench-mcp container smoke test.")
    parser.add_argument("--image", default="workbench-mcp:local", help="Docker image tag to test.")
    args = parser.parse_args()

    docker = shutil.which("docker")
    if docker is None:
        raise SystemExit("docker executable is not available on PATH")

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
        _make_writable_for_container(artifacts)
        test_commands = json.dumps([{"name": "smoke", "command": ["python", "-c", "print('ok')"]}])

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
            args.image,
            "/app/scripts/container-smoke-test.py",
        ]
        result = subprocess.run(command, check=False, capture_output=True, text=True)  # noqa: S603

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=os.sys.stderr)
    return result.returncode


def _make_writable_for_container(path: Path) -> None:
    if os.name != "nt":
        path.chmod(0o777)


if __name__ == "__main__":
    raise SystemExit(main())
