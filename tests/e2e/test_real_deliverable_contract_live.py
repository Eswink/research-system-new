"""EC-01 live 分支：真实交付物契约（GOAL-20260921-010 / PLAN-20260921-127 WP5）。

**判据**：一次真实 run 在**真实执行体**下（`RESEARCHOS_AGENT_RUNTIME=openhands`）验收门
**PASS** 且终态**恰为 `SUCCEEDED`**。GOAL-009 在同一路径上观察到的终点是 `FAILED`
（协议 acceptance gate 对 `session_message` / `analysis_report` 的**设计内判拒**）；
本判据要跨过的正是那一步，而**验收门一字未改**（仍按**字面名**匹配）——改变的是交付物
的**键名由合约声明决定**（见 `adapters/openhands/runtime_adapter._declared_deliverable_name`）。

**默认门**：与 `test_ec04_live_first_run.py` 同一道门（`evaluate_live_run_gate`）：
runtime **显式配置**为 `openhands` + 登记端点的凭据**可解析**。二者缺一 ⇒ **如实 skip**。

跑它（凭据由操作者注入，本文件不读值、不回显、不落盘）：

    set -a; . ./.env; set +a
    RESEARCHOS_AGENT_RUNTIME=openhands uv run --frozen --no-sync python -B -m pytest \
        tests/e2e/test_real_deliverable_contract_live.py -v

**与 `test_ec04_live_first_run.py` 的分工**：那一份判「到**终态** + 指纹 + 归账 + 制品与证据
可读」（`FAILED` 也算过）；本份判**契约被满足**——终态**必须**是 `SUCCEEDED`、验收门
**必须** PASS、交付物**必须**用合约声明的名字登记。两份都留着，因为「到终态」与「契约被满足」
是两个不同的判据，合并会让后者失去区分力。

**失败如何落终态**：失败**也是**终态。跑不绿就如实归类（端点面 / 协议面 / 装配面）并按
fix_policy 纠错——**不得**把 `FAILED` 写成成功、**不得**降低判据迁就实现。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
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
from tests.e2e.live_run_support import openhands_deps, run_failures, start_run

pytestmark = pytest.mark.requires_live_llm

_ENDPOINTS = "examples/config/llm_endpoints.yaml"
_ENDPOINT = "agnes-anthropic"
_RUN_ID = "run-goal010-ec01"
#: 示例合约 `console_demo_deliverable` 声明的 artifact 名（字面量：判据不 import 被测实现）
_DECLARED = "analysis_report"
_FACT_NAME = "session_message"


def _registered_endpoint() -> Any:
    """登记进目录的端点（`base_url` = 用户授权的那一个）。"""
    return load_llm_endpoints(_ENDPOINTS)[_ENDPOINT]


def _gate() -> Any:
    return evaluate_live_run_gate(
        credentials=EnvCredentialResolver(),
        endpoint=_registered_endpoint(),
        agent_runtime=os.environ.get("RESEARCHOS_AGENT_RUNTIME", ""),
        live_agent_runtime=OPENHANDS_RUNTIME,
    )


@dataclass(frozen=True, slots=True)
class _ContractReads:
    """契约判据的读面快照：都经**既有 API** 取，与操作者看到的一致。"""

    run: dict[str, Any]
    failures: list[str]
    artifacts: list[dict[str, Any]]
    deliverable: dict[str, Any] | None
    deliverable_id: str | None

    def to_payload(self) -> dict[str, Any]:
        return {
            "run_id": self.run["id"],
            "state": self.run["state"],
            "failures": self.failures,
            "artifact_ids": [str(item["id"]) for item in self.artifacts],
            "deliverable_id": self.deliverable_id,
            "declared_artifact": (self.deliverable or {}).get("declared_artifact"),
            "fact_name": (self.deliverable or {}).get("fact_name"),
            "contract_id": (self.deliverable or {}).get("contract_id"),
        }


def _deliverable_of(client: TestClient, artifacts: list[dict[str, Any]]) -> tuple[Any, Any]:
    """取**按合约声明命名**的那件交付物及其载荷（取不到就是 `(None, None)`）。"""
    found = next(
        (item for item in artifacts if str(item["id"]).endswith(f":{_DECLARED}")),
        None,
    )
    if found is None:
        return None, None
    return found["id"], client.get(f"/artifacts/{found['id']}/content").json()


def _execute(endpoint: Any) -> _ContractReads:
    """真实 runtime 跑一次到终态（凭据值只在进程内传递，不落盘）。"""
    from services.api.app import create_app

    deps = openhands_deps(
        endpoint.base_url,
        map_tools=True,
        allow_localhost=False,  # 真端点必须是公网地址：默认 deny 姿态不放松
        live_key=os.environ.get(endpoint.credential_ref),
    )
    with TestClient(create_app(deps)) as client:
        created = start_run(client)
        run = client.get(f"/runs/{created['id']}").json()
        failures = run_failures(client, run["id"])
        artifacts = client.get(f"/runs/{run['id']}/artifacts").json()
        deliverable_id, payload = _deliverable_of(client, artifacts)
        return _ContractReads(
            run=run,
            failures=failures,
            artifacts=artifacts,
            deliverable=payload if isinstance(payload, dict) else None,
            deliverable_id=deliverable_id,
        )


def _assert_contract_satisfied(reads: _ContractReads) -> None:
    """EC-01 的判据本体：终态**恰为 `SUCCEEDED`** + 验收门 **PASS** + 交付物用声明名。

    三条各自点名缺哪一条；`FAILED` 在这里**不是**通过——那正是 GOAL-009 的起点。
    """
    payload = reads.to_payload()
    assert reads.run["state"] == "SUCCEEDED", payload
    assert not any("acceptance gate" in message for message in reads.failures), payload
    assert not reads.failures, payload
    assert reads.deliverable_id is not None, payload
    assert reads.deliverable is not None, payload
    assert reads.deliverable.get("declared_artifact") == _DECLARED, payload
    assert reads.deliverable.get("fact_name") == _FACT_NAME, payload
    assert reads.deliverable.get("contract_id") == "console_demo_deliverable", payload


def test_real_run_satisfies_the_declared_contract(tmp_path: Path) -> None:
    """一次真实 run：验收门 PASS、终态 `SUCCEEDED`、交付物按合约声明的名字登记。"""
    gate = _gate()
    if not gate.open:
        record = skip_record_for_gate(_RUN_ID, gate)
        pytest.skip(f"live run skipped: {record.reason}")

    endpoint = _registered_endpoint()
    reads = _execute(endpoint)
    _assert_contract_satisfied(reads)

    written = tmp_path / "ec01-live-contract.json"
    written.write_text(
        json.dumps(reads.to_payload(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    reloaded = json.loads(written.read_text(encoding="utf-8"))
    assert reloaded["state"] == "SUCCEEDED", reloaded
    assert reloaded["declared_artifact"] == _DECLARED, reloaded
