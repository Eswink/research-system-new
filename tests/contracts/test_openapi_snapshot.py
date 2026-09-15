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
    # 修复自恰快照缺陷:先取已提交字节,再再生成(_regenerate 会覆写文件),
    # 比较对象是"再生成结果 vs 提交前快照"——漂移可被发现。
    committed_bytes = SNAPSHOT.read_text(encoding="utf-8")
    committed = cast(dict[str, Any], json.loads(committed_bytes))
    regenerated = _regenerate()
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
    assert "/runs/{run_id}/telemetry" in paths
    assert "/runs/{run_id}/cost" in paths
    assert "/evaluations/trend" in paths
    # Protocol drafts（PLAN-20260908-033）
    assert "/protocol-templates" in paths
    assert "/protocol-drafts/validate" in paths
    assert "/projects/{project_id}/protocol-drafts" in paths
    assert "/protocol-drafts/{draft_id}" in paths
    assert "/protocol-drafts/{draft_id}/revisions/{revision}" in paths
    # Artifact 只读端点（PLAN-20260910-037 WP-C）
    assert "/runs/{run_id}/artifacts" in paths
    assert "/artifacts/{artifact_id}" in paths
    assert "/artifacts/{artifact_id}/content" in paths
    # 成本日序列（PLAN-20260910-037 WP-D）
    assert "/cost/daily" in paths
    # 项目级成本预测（G12 / GOAL-20260915-002 EC-02）
    assert "/projects/{project_id}/cost-forecast" in paths
    # 实验项目视图与计划（PLAN-20260910-037 WP-E）
    assert "/projects/{project_id}/experiments" in paths
    assert "/experiments/{plan_id}/archive" in paths
    # 产品 Memory 门链（PLAN-20260910-037 WP-F；无两阶段 decide，见 CONTROL_PLANE_API.md 注记）
    assert "/projects/{project_id}/memory" in paths
    assert "/memory/proposals" in paths
    assert "/memory/{memory_id}" in paths
    # 通知投影（PLAN-20260910-037 WP-G）
    assert "/notifications" in paths
    assert "/notifications/{event_id}/read" in paths
