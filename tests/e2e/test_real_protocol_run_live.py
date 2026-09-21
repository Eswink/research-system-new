"""EC-03 live 分支：**选定的真实协议**在真实执行体下跑到 `SUCCEEDED`（GOAL-010 / PLAN-129 WP4）。

**判据**（一次真实 run，点名 `real_research_task_v1.yaml`，真实执行体
`RESEARCHOS_AGENT_RUNTIME=openhands`）：canonical 身份**恰为**该协议的 id、终态**恰为**
`SUCCEEDED`、交付物按**新合约声明的名字**（`real_research_deliverable` → `analysis_report`）
登记、失败面为空。**只有 `SUCCEEDED` 是成功**——`FAILED` 也算一种终态，但在这里**不是**通过。

**为什么单列一份**（而不是改 EC-01 那份的协议）：EC-01 的证据是在 `console_demo_deliverable`
上取的，**不追溯改写**既有证据（PLAN-129 的边界条款）；本份是**对新合约的另行取样**，
两份判据互不替代。

**默认门**：与 `test_real_deliverable_contract_live.py` 同一道（`evaluate_live_run_gate`）：
runtime **显式配置**为 `openhands` + 登记端点的凭据**可解析**。二者缺一 ⇒ **如实 skip**。

跑它（凭据由操作者注入；本文件不读值、不回显、不落盘）：

    set -a; . ./.env; set +a
    RESEARCHOS_AGENT_RUNTIME=openhands uv run --frozen --no-sync python -B -m pytest \
        tests/e2e/test_real_protocol_run_live.py -v

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
from tests.e2e.live_run_support import REAL_PROTOCOL, openhands_deps, run_failures, start_run

pytestmark = pytest.mark.requires_live_llm

_ENDPOINTS = "examples/config/llm_endpoints.yaml"
_ENDPOINT = "agnes-anthropic"
_RUN_ID = "run-goal010-ec03"
#: 字面量（判据不 import 被测实现）：新合约声明的 artifact 名 / 事实名 / 合约 id / 协议 id
_DECLARED = "analysis_report"
_FACT_NAME = "session_message"
_CONTRACT = "real_research_deliverable"
_PROTOCOL_ID = "real_research_task_v1_0_1"


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
class _RunReads:
    """读面快照：都经**既有 API** 取，与操作者看到的一致。"""

    run: dict[str, Any]
    failures: list[str]
    artifacts: list[dict[str, Any]]
    deliverable: dict[str, Any] | None
    deliverable_id: str | None

    def to_payload(self) -> dict[str, Any]:
        return {
            "run_id": self.run["id"],
            "state": self.run["state"],
            "protocol_id": self.run["protocol_id"],
            "protocol_body_digest": self.run["protocol_body_digest"],
            "failures": self.failures,
            "artifact_ids": [str(item["id"]) for item in self.artifacts],
            "deliverable_id": self.deliverable_id,
            "declared_artifact": (self.deliverable or {}).get("declared_artifact"),
            "fact_name": (self.deliverable or {}).get("fact_name"),
            "contract_id": (self.deliverable or {}).get("contract_id"),
        }


def _deliverable_of(client: TestClient, artifacts: list[dict[str, Any]]) -> tuple[Any, Any]:
    """取**按合约声明命名**的那件交付物及其载荷（取不到就是 `(None, None)`）。"""
    found = next((item for item in artifacts if str(item["id"]).endswith(f":{_DECLARED}")), None)
    if found is None:
        return None, None
    return found["id"], client.get(f"/artifacts/{found['id']}/content").json()


def _execute(endpoint: Any) -> _RunReads:
    """真实 runtime 跑一次到终态（凭据值只在进程内传递，不落盘）。"""
    from services.api.app import create_app

    deps = openhands_deps(
        endpoint.base_url,
        map_tools=True,
        allow_localhost=False,  # 真端点必须是公网地址：默认 deny 姿态不放松
        live_key=os.environ.get(endpoint.credential_ref),
    )
    with TestClient(create_app(deps)) as client:
        created = start_run(client, REAL_PROTOCOL)
        run = client.get(f"/runs/{created['id']}").json()
        artifacts = client.get(f"/runs/{run['id']}/artifacts").json()
        deliverable_id, payload = _deliverable_of(client, artifacts)
        return _RunReads(
            run=run,
            failures=run_failures(client, run["id"]),
            artifacts=artifacts,
            deliverable=payload if isinstance(payload, dict) else None,
            deliverable_id=deliverable_id,
        )


def _assert_real_protocol_run(reads: _RunReads) -> None:
    """EC-03 的判据本体：**身份** + **终态** + **交付物**，三条各自点名缺哪一条。"""
    payload = reads.to_payload()
    assert reads.run["protocol_id"] == _PROTOCOL_ID, payload
    assert reads.run["state"] == "SUCCEEDED", payload
    assert not any("acceptance gate" in message for message in reads.failures), payload
    assert not reads.failures, payload
    assert reads.deliverable_id is not None, payload
    assert reads.deliverable is not None, payload
    assert reads.deliverable.get("declared_artifact") == _DECLARED, payload
    assert reads.deliverable.get("fact_name") == _FACT_NAME, payload
    assert reads.deliverable.get("contract_id") == _CONTRACT, payload


def test_real_protocol_run_succeeds_under_the_real_runtime(tmp_path: Path) -> None:
    """一次真实 run：点名真实协议 ⇒ canonical 身份可判、验收门 PASS、终态 `SUCCEEDED`。"""
    gate = _gate()
    if not gate.open:
        record = skip_record_for_gate(_RUN_ID, gate)
        pytest.skip(f"live run skipped: {record.reason}")

    reads = _execute(_registered_endpoint())
    _assert_real_protocol_run(reads)

    written = tmp_path / "ec03-live-real-protocol.json"
    written.write_text(
        json.dumps(reads.to_payload(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    reloaded = json.loads(written.read_text(encoding="utf-8"))
    assert reloaded["state"] == "SUCCEEDED", reloaded
    assert reloaded["protocol_id"] == _PROTOCOL_ID, reloaded
