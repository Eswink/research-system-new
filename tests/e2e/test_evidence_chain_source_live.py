"""EC-02 live 分支：证据链真实性（GOAL-20260921-010 / PLAN-20260921-128 WP4）。

**判据**：真实 run 里满足 `EVIDENCE_COVERAGE` 的那条来源，其 `SourceRecord` 经**既有读面**
（`GET /runs/{id}/evidence`）可取，且指向一个**非模型自述**的对象——即本 phase **声明的
输入制品**（内容寻址、digest 可重算、`created_by` 是组合根而不是任何 agent）。

**反证（同一条真实执行体路径）**：把协议里的 `inputs:` 声明去掉 ⇒ 该 task 的
`evidence_source_count` 归零、`EVIDENCE_COVERAGE` 判 `False` ⇒ run `FAILED`。
该反证在 `tests/e2e/test_ec03_real_runtime_offline_chain.py` 一侧压过（同 adapter、同装配，
端点用替身），**不**为它再发一次真实调用——live 调用取**最小必要**。

**默认门**：与 EC-01 同一道门（runtime 显式配置为 `openhands` + 登记端点凭据可解析）；
缺一 ⇒ **如实 skip**（skip 不是 PASS）。

跑它（凭据由操作者注入，本文件不读值、不回显、不落盘）：

    set -a; . ./.env; set +a
    RESEARCHOS_AGENT_RUNTIME=openhands uv run --frozen --no-sync python -B -m pytest \
        tests/e2e/test_evidence_chain_source_live.py -v
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
from tests.e2e.live_run_support import (
    openhands_deps,
    run_failures,
    start_run,
)
from tests.e2e.live_switch_support import live_e2e_switch_enabled

pytestmark = pytest.mark.requires_live_llm

_ENDPOINTS = "examples/config/llm_endpoints.yaml"
_ENDPOINT = "agnes-anthropic"
_RUN_ID = "run-goal010-ec02"
#: 协议**声明**的输入制品 id（字面量：判据不 import 被测实现）
_DECLARED_INPUT = "input-corpus:console_demo_v1"
#: 该输入在库里的来源标（组合根种入 ⇒ 不是任何 agent）
_EXPECTED_CREATOR = "composition-root"


@dataclass(frozen=True, slots=True)
class _EvidenceReads:
    """证据读面快照：全部经既有 API 取，与操作者看到的一致。"""

    run_id: str
    state: str
    failures: list[str]
    sources: list[dict[str, Any]]
    declared_input_source: dict[str, Any] | None
    input_meta: dict[str, Any]

    def to_payload(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "state": self.state,
            "failures": self.failures,
            "source_origins": [str(item.get("source_origin")) for item in self.sources],
            "source_trust_labels": [str(item.get("source_trust_label")) for item in self.sources],
            "declared_input_source": self.declared_input_source,
            "declared_input_created_by": self.input_meta.get("created_by"),
            "declared_input_digest": self.input_meta.get("digest"),
        }


def _read(client: TestClient, run_id: str) -> _EvidenceReads:
    """真实 run 跑一次到终态，再把**读面**取全（一次调用只发一次真实请求）。"""
    created = start_run(client)
    run = client.get(f"/runs/{created['id']}").json()
    payload = client.get(f"/runs/{run['id']}/evidence").json()
    items = payload if isinstance(payload, list) else payload.get("items", [])
    sources = [item for item in items if isinstance(item, dict)]
    found = next(
        (item for item in sources if str(item.get("source_origin")) == _DECLARED_INPUT),
        None,
    )
    return _EvidenceReads(
        run_id=str(run["id"]),
        state=str(run["state"]),
        failures=run_failures(client, str(run["id"])),
        sources=sources,
        declared_input_source=found,
        input_meta=client.get(f"/artifacts/{_DECLARED_INPUT}").json(),
    )


def _assert_not_self_report(reads: _EvidenceReads) -> None:
    """EC-02 判据本体：来源可读 + 指向非模型自述的对象 + run 未被判拒。"""
    payload = reads.to_payload()
    assert reads.state == "SUCCEEDED", payload
    assert not reads.failures, payload
    assert reads.sources, "证据读面必须非空——空读面说明连自述证据都没登记"
    assert reads.declared_input_source is not None, payload
    source = reads.declared_input_source
    assert source.get("source_origin") == _DECLARED_INPUT, payload
    assert source.get("source_trust_label") == "USER_PROVIDED", payload
    assert source.get("content_digest"), payload
    # 被引用的对象是操作者供应的输入，而不是任何 agent 的产出。
    assert reads.input_meta.get("created_by") == _EXPECTED_CREATOR, payload


def test_the_real_run_covers_evidence_with_a_declared_input(tmp_path: Path) -> None:
    """一次真实 run：覆盖由**声明的输入**满足，且该来源经既有读面可取。"""
    gate = evaluate_live_run_gate(
        credentials=EnvCredentialResolver(),
        endpoint=load_llm_endpoints(_ENDPOINTS)[_ENDPOINT],
        agent_runtime=os.environ.get("RESEARCHOS_AGENT_RUNTIME", ""),
        live_agent_runtime=OPENHANDS_RUNTIME,
        live_switch=live_e2e_switch_enabled(),
    )
    if not gate.open:
        pytest.skip(f"live run skipped: {skip_record_for_gate(_RUN_ID, gate).reason}")

    endpoint = load_llm_endpoints(_ENDPOINTS)[_ENDPOINT]
    from services.api.app import create_app

    deps = openhands_deps(
        endpoint.base_url,
        map_tools=True,
        allow_localhost=False,  # 真端点必须是公网地址：默认 deny 姿态不放松
        live_key=os.environ.get(endpoint.credential_ref),
    )
    with TestClient(create_app(deps)) as client:
        reads = _read(client, _RUN_ID)

    _assert_not_self_report(reads)

    written = tmp_path / "ec02-live-source.json"
    written.write_text(
        json.dumps(reads.to_payload(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    reloaded = json.loads(written.read_text(encoding="utf-8"))
    assert reloaded["state"] == "SUCCEEDED", reloaded
    assert reloaded["declared_input_source"]["source_origin"] == _DECLARED_INPUT, reloaded
