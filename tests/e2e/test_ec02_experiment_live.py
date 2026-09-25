"""GOAL-012 EC-02 的**真实 run** 判据：真实执行体 + 声明式沙箱实验跑到终态（PLAN-20260923-142）。

判据（一次真实 run，点名 `sort_analysis_v1.yaml`，真实执行体
`RESEARCHOS_AGENT_RUNTIME=openhands`，实验 = 既有 `research-os-sandbox:m9-test`）：

1. **冻结确已发生且可审计**（GOAL-012 EC-01 的端到端形态）：`manifest_digest` 非空，
   事件链里 `manifest.frozen` 的 payload 带 `accepted_policy_exceptions` 留痕（EXECUTE
   风险被**显式策略声明**允许的那几条，含 `code.execute`）。
2. **终态如实**：只有 `SUCCEEDED` 是成功；`FAILED` 也是终态，但**不是通过**。
3. **三项读面齐备**：实验产物（镜像/环境摘要 + `analysis_report` + 指标）、证据、预算归账。

**默认门**：与 `test_real_protocol_run_live.py` 同一道（`evaluate_live_run_gate`）：
runtime **显式配置**为 `openhands` + 登记端点的凭据**可解析**。二者缺一 ⇒ **如实 skip**。

跑它（凭据由操作者注入；本文件不读值、不回显、不落盘）：

    set -a; . ./.env; set +a
    RESEARCHOS_AGENT_RUNTIME=openhands uv run --frozen --no-sync python -B -m pytest \
        tests/e2e/test_ec02_experiment_live.py -q -rs

**反证**在离线判据里（`test_ec02_experiment_chain_offline.py` 第 2 条：撤掉显式允许 ⇒
拒冻 ⇒ 零 task / 零 experiment）。真实端点上的每一次调用都是**不可白得**的：本文件
因此只跑**一次** run，不重试、不批量。

**如实写明的两处边界**（不夸大这次的证明力）：

- 留痕里的 `decision: ALLOW` 来自**本次装配面**的策略求值器（`preflight_override` 的载体，
  与 GOAL-009/010/011 全部真实 run 同一条路径）。
  **【GOAL-20260924-014 EC-01 更新】**：本条此前登记的是「`evidence.read` 在真实控制面判
  `DENY` ⇒ 该协议在真实控制面上是 `FAIL`（`W-A`）」。用户已拍板放行 `evidence.read`
  （方案 (A)），且 `sort_analysis_v1` 引用的两份 task contract 已补进出厂目录 ⇒
  **真实控制面现在对该协议判 `WARN`、可冻结**，与本节装配结论**一致**（`W-C` 已消灭；
  判据 `tests/application/preflight/test_policy_surface_consistency.py`）。
  本节仍如实标注：**留痕来自 override 这一侧的求值器**——本文件本身不因上述修复而改变
  它证明的东西。
- 实验那一步**另经真实策略求值器**的执行期检查（`GovernedExperimentExecutor._enforce_policy`，
  `policy_bindings()` 的 `NativePolicyEvaluator`）：`code.execute` 在 `policy.yaml` 里是
  `allow_with_constraints`（`sandbox_required` / `max_seconds`）⇒ 这一环确由**产品策略**放行。
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
from tests.e2e.live_run_support import (
    EXPERIMENT_IMAGE,
    EXPERIMENT_SCRIPT,
    openhands_deps,
    run_failures,
    start_run,
    with_sandbox_experiment,
)
from tests.e2e.live_switch_support import live_e2e_switch_enabled

pytestmark = pytest.mark.requires_live_llm

_ENDPOINTS = "examples/config/llm_endpoints.yaml"
_ENDPOINT = "agnes-anthropic"
_RUN_ID = "run-goal012-ec02"
_PROTOCOL = "sort_analysis_v1.yaml"
#: 字面量（判据不 import 被测实现）：协议 id / 留痕里必须点名的那条能力 / 交付物名
_PROTOCOL_ID = "sort_analysis_v1_0_1"
_TRACED_CAPABILITY = "code.execute"
_DECLARED = "analysis_report"


def _registered_endpoint() -> Any:
    return load_llm_endpoints(_ENDPOINTS)[_ENDPOINT]


def _gate() -> Any:
    return evaluate_live_run_gate(
        credentials=EnvCredentialResolver(),
        endpoint=_registered_endpoint(),
        agent_runtime=os.environ.get("RESEARCHOS_AGENT_RUNTIME", ""),
        live_agent_runtime=OPENHANDS_RUNTIME,
        live_switch=live_e2e_switch_enabled(),
    )


def _frozen_payload(client: TestClient, run_id: str) -> dict[str, Any]:
    """事件链里 `manifest.frozen` 的 payload（找不到即空 dict ⇒ 判据点名失败）。"""
    events = client.get(f"/runs/{run_id}/events").json()
    return next(
        (dict(event["payload"]) for event in events if event["type"] == "manifest.frozen"), {}
    )


def _execute(endpoint: Any) -> dict[str, Any]:
    """一次真实 run：真实执行体 + 声明式沙箱实验，取回读面快照（凭据值不落盘）。"""
    from services.api.app import create_app

    deps = openhands_deps(
        endpoint.base_url,
        map_tools=True,
        allow_localhost=False,  # 真端点必须是公网地址：默认 deny 姿态不放松
        live_key=os.environ.get(endpoint.credential_ref),
    )
    with_sandbox_experiment(deps, script=EXPERIMENT_SCRIPT, image=EXPERIMENT_IMAGE)
    with TestClient(create_app(deps)) as client:
        created = start_run(client, _PROTOCOL)
        run_id = str(created["id"])
        run = client.get(f"/runs/{run_id}").json()
        return {
            "run_id": run_id,
            "state": run["state"],
            "protocol_id": run["protocol_id"],
            "manifest_digest": run["manifest_digest"],
            "failures": run_failures(client, run_id),
            "frozen": _frozen_payload(client, run_id),
            "experiments": client.get(f"/runs/{run_id}/experiments").json(),
            "evidence": client.get(f"/runs/{run_id}/evidence").json(),
            "usage": client.get(f"/runs/{run_id}/usage").json(),
        }


def _assert_live_experiment_chain(sample: dict[str, Any]) -> None:
    """判据本体：冻结留痕 → 终态 → 三项读面，逐条各自点名缺哪一条。"""
    assert sample["protocol_id"] == _PROTOCOL_ID, sample
    assert sample["manifest_digest"], ("冻结必须真的发生（EC-01）", sample)

    trace = sample["frozen"].get("accepted_policy_exceptions") or []
    capabilities = {str(item.get("capability")) for item in trace}
    assert _TRACED_CAPABILITY in capabilities, ("留痕必须点名被允许的 EXECUTE 能力", trace)
    assert all(item.get("accepted_at") for item in trace), trace
    assert all(item.get("decision") in ("ALLOW", "ALLOW_WITH_CONSTRAINTS") for item in trace), trace

    assert sample["state"] == "SUCCEEDED", ("只有 SUCCEEDED 是成功", sample)
    assert not sample["failures"], sample

    experiments = sample["experiments"]["experiments"]
    assert len(experiments) == 1, sample["experiments"]
    experiment = experiments[0]
    assert experiment["image_digest"], experiment
    names = {str(item).rsplit(":", 1)[-1] for item in experiment["artifact_ids"]}
    assert _DECLARED in names, ("验收门判的就是它", names)
    assert {"corpus_size", "worst_case_comparisons"} <= set(experiment["metrics"]), experiment

    assert sample["evidence"], "实验证据必须可读"
    assert all(item["artifact_id"] for item in sample["evidence"]), sample["evidence"]
    usage = sample["usage"]
    assert isinstance(usage["entries"], list), usage


def test_the_real_run_freezes_traces_and_executes_the_declared_experiment(
    tmp_path: Path,
) -> None:
    """一次真实 run 到终态：冻结留痕在场、实验真的跑了、三项读面齐备。"""
    gate = _gate()
    if not gate.open:
        record = skip_record_for_gate(_RUN_ID, gate)
        pytest.skip(f"live run skipped: {record.reason}")

    sample = _execute(_registered_endpoint())
    written = tmp_path / "ec02-live-experiment-chain.json"
    written.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")
    reloaded = json.loads(written.read_text(encoding="utf-8"))
    _assert_live_experiment_chain(reloaded)
