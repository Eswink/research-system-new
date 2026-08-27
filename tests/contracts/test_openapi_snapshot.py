"""M13 OpenAPI snapshot 契约：生成结果必须与仓库内 schema 一致。

前端 TS 类型从 docs/api/openapi.m13.json 生成；本测试防止 API DTO 变更
后 schema 漂移（单一 schema truth，禁止两套手写类型）。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "docs" / "api" / "openapi.m13.json"
GEN_SCRIPT = ROOT / "tools" / "gen_openapi.py"


def _regenerate() -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, "-B", str(GEN_SCRIPT)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return cast(dict[str, Any], json.loads(SNAPSHOT.read_text(encoding="utf-8")))


def test_openapi_snapshot_is_current() -> None:
    regenerated = _regenerate()
    committed = cast(dict[str, Any], json.loads(SNAPSHOT.read_text(encoding="utf-8")))
    assert regenerated == committed, (
        "docs/api/openapi.m13.json drifted from generated OpenAPI; "
        "run tools/gen_openapi.py and commit the result"
    )


def test_openapi_contains_control_plane_paths() -> None:
    schema = cast(dict[str, Any], json.loads(SNAPSHOT.read_text(encoding="utf-8")))
    paths = schema["paths"]
    assert "/llm-endpoints" in paths
    assert "/llm-endpoints/{endpoint_id}/test" in paths
    assert "/llm-endpoints/{endpoint_id}/discover-models" in paths
    assert "/llm-endpoints/{endpoint_id}/health" in paths
    assert "/models" in paths
    assert "/models/{model_id}/probe" in paths
    assert "/models/{model_id}/compatibility" in paths
    assert "/runs/{run_id}/events" in paths
    assert "/approvals/{approval_id}/decide" in paths
    assert "/runs/{run_id}/claims" in paths
    assert "/runs/{run_id}/export" in paths
