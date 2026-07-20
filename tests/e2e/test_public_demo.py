from __future__ import annotations

import asyncio
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from types import ModuleType

import pytest

DEMO_PATH = Path(__file__).resolve().parents[2] / "scripts" / "run-demo.py"


def load_demo_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("run_demo_script", DEMO_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_public_demo_writes_success_report_without_temp_path_leak(tmp_path: Path) -> None:
    if shutil.which("git") is None:
        pytest.skip("git executable is required for the public demo")
    if shutil.which("python") is None:
        pytest.skip("python executable is required for the configured demo test command")
    demo = load_demo_module()
    report_path = tmp_path / "demo-report.json"

    result = asyncio.run(demo.run_demo(report_path=report_path))

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    serialized = json.dumps(payload, sort_keys=True)
    assert result["status"] == "ok"
    assert payload["status"] == "ok"
    assert payload["operations"]["run_tests"]["status"] == "passed"
    assert payload["operations"]["apply_patch"]["changed"] is True
    assert payload["operations"]["expected_blocked_unsafe_operation"]["blocked"] is True
    assert payload["cleanup"]["temporary_workspace_removed"] is True
    assert "workbench-mcp-demo-" not in serialized
