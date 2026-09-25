"""GOAL-014 EC-02 的**判据本体**：无 `preflight_override` 的真实控制面跑到 `SUCCEEDED`。

**判什么**（一次真实 run，用户判词 §四）：产品组合根（`services.api.composition.assemble`）
+ 既有 API 启动，`preflight_override` **必须为 `None`**（policy 求值器、endpoint/provider
健康、预算预留全部由 `_live_preflight` 在同一份合并目录上现场求值），而这次 run 的**实验**
由**出厂目录**声明（`examples/contracts/task_contracts.yaml` 的 `experiment_execution`，
本协议 `real_experiment_research_v1.yaml` 的 `execution` 相位引用它）⇒

1. 终态**恰为** `SUCCEEDED`（`FAILED` 不得写成成功）；
2. **实验面 ≥ 1 条**（此前 GOAL-014 cycle 2 的样张里实验面是空的 —— 那正是 EC-02 的缺口）；
3. **证据面可读**、**预算面归账**；
4. 控制面是**产品自己的那一套**（`override is None` + `NativePolicyEvaluator` + 真适配器探测的
   `HEALTHY`）。

**不判什么**（如实边界，不夸大）：`TEST_PASSES` 的来源是**实验自报**（合约判据判的是实验
自己产出的受控报告：`status` / `metrics` / `stderr`），**不是**独立跑测框架——ECO-02 的 A 项
随行披露写死在这里，判据不把它读成独立验证。

**跑法**（凭据只在 gitignored `.env`；单条命令内联前缀开真实执行体；跑完不留开关）：

    set -a; . ./.env; set +a
    RESEARCHOS_AGENT_RUNTIME=openhands uv run --frozen --no-sync python -B -m pytest \
        tests/e2e/test_real_control_plane_experiment_live.py -q -rs

**真实调用取最小必要**：本文件只跑**一次** run（1 个真实 LLM 会话、2 次真实 NCBI 调用
`retmax=3`、1 次真实沙箱实验），不重试、不批量。
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
from tests.e2e.live_control_plane_support import (
    ENDPOINT_ID,
    PROVIDER_ID,
    product_control_plane_deps,
    with_contract_declared_experiment,
)
from tests.e2e.live_switch_support import live_e2e_switch_enabled

pytestmark = pytest.mark.requires_live_llm

_ENDPOINTS = "examples/config/llm_endpoints.yaml"
_PROTOCOL = "real_experiment_research_v1.yaml"
_PROTOCOL_ID = "real_experiment_research_v1_0_0"
_RUN_ID = "run-goal014-ec02-real-experiment"
_EXPERIMENT_CONTRACT = "experiment_execution"
#: 装配方给出的脚本与镜像（合约**不** pin 这两个量：`experiment: {}` 正是这个意思）。
_EXPERIMENT_SCRIPT = "examples/experiments/exact_match_index_benchmark.py"
_EXPERIMENT_IMAGE = "research-os-sandbox:m9-test"
_SAMPLE = Path("scratch") / "goal014-c6-real-experiment-sample.json"


def _endpoint() -> Any:
    return load_llm_endpoints(_ENDPOINTS)[ENDPOINT_ID]


def _gate() -> Any:
    return evaluate_live_run_gate(
        credentials=EnvCredentialResolver(),
        endpoint=_endpoint(),
        agent_runtime=os.environ.get("RESEARCHOS_AGENT_RUNTIME", ""),
        live_agent_runtime=OPENHANDS_RUNTIME,
        live_switch=live_e2e_switch_enabled(),
    )


def _execute(deps: Any) -> dict[str, Any]:
    """一次真实 run（产品组合根 + 既有 API）：取回三读面 + 控制面自身的事实。"""
    from services.api.app import create_app

    with TestClient(create_app(deps)) as client:
        created = client.post(
            "/projects/example-project/runs",
            json={"protocol_path": _PROTOCOL},
            headers={"Idempotency-Key": "goal014-ec02-real-experiment"},
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
            # 门的判词痕迹：PASS 时 claim 被升级为 VERIFIED 的那条 canonical 事件。
            "judged": [
                event["payload"]
                for event in events
                if event["type"] in ("manifest.frozen", "claim.verified")
            ],
            "experiments": client.get(f"/runs/{run_id}/experiments").json(),
            "evidence": client.get(f"/runs/{run_id}/evidence").json(),
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
    """终态恰为 `SUCCEEDED` + 三读面齐备（实验 / 证据 / 预算，逐面点名缺哪一条）。"""
    assert sample["protocol_id"] == _PROTOCOL_ID, sample
    assert sample["manifest_digest"], "冻结必须真的发生"
    assert sample["state"] == "SUCCEEDED", ("只有 SUCCEEDED 是成功", sample["failures"], sample)
    assert not sample["failures"], sample["failures"]

    experiments = sample["experiments"]["experiments"]
    assert len(experiments) >= 1, ("实验面必须 ≥1 条（此前为 0 条）", sample["experiments"])
    experiment = experiments[0]
    assert experiment["experiment_run_id"], experiment
    assert experiment["image_digest"], ("制品来自容器，不是桩", experiment)
    names = {str(item).rsplit(":", 1)[-1] for item in experiment["artifact_ids"]}
    assert "metrics" in names, ("合约判的就是这件产物", names)
    assert experiment["metrics"], experiment

    evidence = sample["evidence"]
    assert evidence, "证据面必须有内容"
    retrieved = [item for item in evidence if item.get("source_trust_label") == "RETRIEVED"]
    assert retrieved and all(item["tool_refs"] for item in retrieved), (
        "真实检索取得的来源，不是模型自述",
        evidence,
    )

    usage = sample["usage"]
    assert isinstance(usage["entries"], list), usage
    assert usage["entries"] or usage["unknown_cost_entries"] > 0, usage


def test_the_real_run_executes_the_declared_experiment_to_a_successful_terminal(
    tmp_path: Path,
) -> None:
    """一次真实 run 到终态：真实 LLM + 真实检索 + **真实实验**，三读面齐备。"""
    gate = _gate()
    if not gate.open:
        pytest.skip(f"live run skipped: {skip_record_for_gate(_RUN_ID, gate).reason}")

    deps = product_control_plane_deps(str(tmp_path / "control-plane.db"))
    with_contract_declared_experiment(deps, script=_EXPERIMENT_SCRIPT, image=_EXPERIMENT_IMAGE)
    sample = _execute(deps)
    sample["plane"] = _control_plane_faces(deps)
    sample["experiment_contract"] = _EXPERIMENT_CONTRACT

    _SAMPLE.parent.mkdir(parents=True, exist_ok=True)
    _SAMPLE.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")
    reloaded = json.loads(_SAMPLE.read_text(encoding="utf-8"))
    _assert_real_plane(reloaded)
    _assert_terminal_and_faces(reloaded)


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
        "experiment_task": type(deps.runs._deps.experiment_task).__name__,
    }
