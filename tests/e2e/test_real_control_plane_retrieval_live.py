"""GOAL-20260924-014 EC-02 的**可达半边**：真实控制面（无 override）上的真实检索闭环。

**判什么**：run 经**产品组合根 + 既有 API** 启动（`preflight_override` 必须为 `None`），
所以控制面的判词全部由 `_live_preflight` 现场求值——policy 走
`NativePolicyEvaluator` + **产品** `examples/config/policy.yaml`，provider 健康由
**真适配器真探测**得出（不是夹具给出的常量）。到终态 `SUCCEEDED`，检索真的打到
provider 声明的 `network_domains`，证据面 / 预算面可读。

**不判什么**（如实边界，不夸大）：**实验面**。带真实实验的 run 今天在**验收门**上到不了
`SUCCEEDED`——出厂目录里两份声明了 `experiment` 的合约（`experiment_execution` /
`m12_experiment_execution`）都带 `TEST_PASSES` + `POLICY_COMPLIANT`，而产品路径的
`EvaluationInputs`（`evaluation_gate.py`）**没有** `tests` / `policy_decision` 两个维度
⇒ 两条判据 fail-closed（实测：`scratch/goal014_c2_acceptance_probe.py` 的输出）。
那条缺口正是 GOAL-011 登记的下一轮拍板项 ①②③，本判据**不**绕过它、也**不**为此造
一份判据更弱的合约（那会变成「放宽验收门以强行成功」）⇒ EC-02 本体 BLOCKED，
证据与选项见 `GOAL-20260924-014` 的 EC-02 段与 `F-10` / `F-11`。

**跑法**（凭据只在 gitignored `.env`；单条命令内联前缀开真实执行体；跑完不留开关）：

    set -a; . ./.env; set +a
    RESEARCHOS_AGENT_RUNTIME=openhands uv run --frozen --no-sync python -B -m pytest \
        tests/e2e/test_real_control_plane_retrieval_live.py -q -rs

**真实调用取最小必要**：本文件只跑**一次** run（1 个 phase、1 次真实 LLM 会话、
2 次真实 NCBI 调用——`retmax=3`），不重试、不批量。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from adapters.contracts.models_loaders import load_llm_endpoints
from adapters.relay.credential_resolver import EnvCredentialResolver
from packages.application.model_relay.live_run_gate import (
    evaluate_live_run_gate,
    skip_record_for_gate,
)
from services.api.runtime_support import OPENHANDS_RUNTIME
from tests.e2e.live_control_plane_support import ENDPOINT_ID, PROVIDER_ID, product_control_plane_deps

pytestmark = pytest.mark.requires_live_llm

_ENDPOINTS = "examples/config/llm_endpoints.yaml"
_PROTOCOL = "real_retrieval_research_v1.yaml"
_RUN_ID = "run-goal014-ec02-real-plane"
_PROTOCOL_ID = "real_retrieval_research_v1_0_1"
_SAMPLE = Path("scratch") / "goal014-c2-real-plane-sample.json"


def _endpoint() -> Any:
    return load_llm_endpoints(_ENDPOINTS)[ENDPOINT_ID]


def _gate() -> Any:
    return evaluate_live_run_gate(
        credentials=EnvCredentialResolver(),
        endpoint=_endpoint(),
        agent_runtime=os.environ.get("RESEARCHOS_AGENT_RUNTIME", ""),
        live_agent_runtime=OPENHANDS_RUNTIME,
    )


def _control_plane_faces(deps: Any) -> dict[str, Any]:
    """控制面**自己的**判词来源（读的就是这次 run 用到的那两个实例）。"""
    from packages.application.policy.native import NativePolicyEvaluator
    from services.api.catalog_merge import merged_catalog_snapshot
    from services.api.preflight_support import build_provider_health

    catalog = merged_catalog_snapshot(deps)
    health = build_provider_health(deps, catalog)
    return {
        "override": None if deps.preflight_override is None else "PRESENT",
        "evaluator": type(deps.policy_evaluator).__name__,
        "is_native": isinstance(deps.policy_evaluator, NativePolicyEvaluator),
        "policy_version": catalog.policy.version.text if catalog.policy else None,
        "provider_health": {key: value.value for key, value in sorted(health.items())},
        "adapter": type(deps.tool_providers.get(PROVIDER_ID)).__name__,
    }


def _execute(deps: Any) -> dict[str, Any]:
    """一次真实 run（产品组合根 + 既有 API），取回三项读面；凭据值不落盘。"""
    from services.api.app import create_app

    with TestClient(create_app(deps)) as client:
        created = client.post(
            "/projects/example-project/runs",
            json={"protocol_path": _PROTOCOL},
            headers={"Idempotency-Key": "goal014-ec02-real-plane"},
        )
        assert created.status_code == 200, created.text
        run_id = str(created.json()["id"])
        run = client.get(f"/runs/{run_id}").json()
        events = client.get(f"/runs/{run_id}/events").json()
        return {
            "run_id": run_id,
            "state": run["state"],
            "protocol_id": run["protocol_id"],
            "manifest_digest": run["manifest_digest"],
            "failures": [
                event["payload"].get("message", "")
                for event in events
                if event["type"] in ("run.failed", "task.failed")
            ],
            "evidence": client.get(f"/runs/{run_id}/evidence").json(),
            "experiments": client.get(f"/runs/{run_id}/experiments").json(),
            "usage": client.get(f"/runs/{run_id}/usage").json(),
        }


def _assert_real_plane(sample: dict[str, Any]) -> None:
    """控制面是产品自己的那一套（不是夹具给的判词）。"""
    faces = sample["plane"]
    assert faces["override"] is None, ("必须不带任何 preflight_override", faces)
    assert faces["is_native"] and faces["evaluator"] == "NativePolicyEvaluator", faces
    assert faces["provider_health"].get(PROVIDER_ID) == "HEALTHY", (
        "provider 健康必须由真适配器真探测得出（UNKNOWN 会拒冻）",
        faces,
    )
    assert faces["adapter"] == "NcbiEutilsProvider", faces


def _assert_terminal_and_faces(sample: dict[str, Any]) -> None:
    """终态恰为 SUCCEEDED + 证据面 / 预算面各自点名。"""
    assert sample["protocol_id"] == _PROTOCOL_ID, sample
    assert sample["state"] == "SUCCEEDED", ("只有 SUCCEEDED 是成功", sample["failures"], sample)
    assert sample["manifest_digest"], "冻结必须真的发生"
    assert not sample["failures"], sample["failures"]

    evidence = sample["evidence"]
    assert evidence, "证据面必须有内容"
    retrieved = [item for item in evidence if item.get("source_trust_label") == "RETRIEVED"]
    assert retrieved, ("至少一条来源必须是系统检索取得", evidence)
    assert all(item["artifact_id"] for item in retrieved), retrieved
    assert all(item["tool_refs"] for item in retrieved), ("工具来源，不是模型自述", retrieved)

    usage = sample["usage"]
    assert isinstance(usage["entries"], list), usage
    assert usage["entries"] or usage["unknown_cost_entries"] > 0, usage


def test_the_product_control_plane_runs_real_retrieval_to_a_successful_terminal(
    tmp_path: Path,
) -> None:
    """真实控制面 + 真适配器：终态 `SUCCEEDED`、检索真发生、三项读面中两项齐备。"""
    gate = _gate()
    if not gate.open:
        pytest.skip(f"live run skipped: {skip_record_for_gate(_RUN_ID, gate).reason}")

    deps = product_control_plane_deps(str(tmp_path / "control-plane.db"))
    sample = _execute(deps)
    sample["plane"] = _control_plane_faces(deps)

    _SAMPLE.parent.mkdir(parents=True, exist_ok=True)
    _SAMPLE.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")
    reloaded = json.loads(_SAMPLE.read_text(encoding="utf-8"))
    _assert_real_plane(reloaded)
    _assert_terminal_and_faces(reloaded)
