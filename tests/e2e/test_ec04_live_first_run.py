"""EC-04 live 分支：首次真实 run（GOAL-008 / PLAN-20260920-118）。

**默认门**：本模块带 `requires_live_llm`，CI 只走 skip 路径。开门条件见
`packages/application/model_relay/live_run_gate.py`：

1. runtime **显式配置**为 `openhands`（`RESEARCHOS_AGENT_RUNTIME`，默认空串=保持 Fake）；
2. 登记端点的凭据**可解析**（`LLM_MAIN_KEY`，只问 `has`，不物化值）。

跑它（凭据由操作者注入，本文件不读值、不回显、不落盘）：

    RESEARCHOS_AGENT_RUNTIME=openhands LLM_MAIN_KEY=… pytest tests/e2e/test_ec04_live_first_run.py

跑成什么样才算数（EC-04 判定细则）：run **到终态**、运行时**指纹**可判、usage
**真归账**、制品与证据**可读**，结论口径停在「**可重复配置**」——不是「完全模型可复现」。

**如实登记的边界**：run 走的是目录里模型声明的绑定（当前所有模型都绑 `main`，
OPENAI_COMPATIBLE 面）；登记进目录的 **ANTHROPIC 端点**（`agnes-anthropic`）由本文件的
probe 段单独驱动 ⇒ 「一次 run 自身消费 anthropic 面」需要改模型→端点绑定，本轮**没做**。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from adapters.contracts.models_loaders import load_llm_endpoints, load_models
from adapters.relay.credential_resolver import EnvCredentialResolver
from adapters.relay.gateway import OpenAIChatGateway
from packages.application.model_relay.live_probe import run_live_probe
from packages.application.model_relay.live_run_gate import (
    LIVE_RUN_SWITCH,
    evaluate_live_run_gate,
    skip_record_for_gate,
)
from packages.application.model_relay.live_run_record import build_live_run_record
from packages.domain.budget import ResourceType
from packages.domain.enums import ModelReproducibilityVerdict
from services.api.runtime_support import OPENHANDS_RUNTIME

# 共享装配见 `live_run_support`：直接 import `test_ec03_*` 会让同一文件被**两个模块名**
# 加载，SDK 的 Action 子类被定义两次，判别联合随即拒绝后续事件 round-trip（fork 路径就中招）。
from tests.e2e.live_run_support import (
    openhands_deps,
    run_failures,
    start_run,
)
from tests.e2e.live_switch_support import live_e2e_switch_enabled

pytestmark = pytest.mark.requires_live_llm

_ENDPOINTS = "examples/config/llm_endpoints.yaml"
_MODELS = "examples/config/models.yaml"
_ANTHROPIC_ENDPOINT = "agnes-anthropic"
_MODEL = "agnes_flash"
_RUN_ID = "run-ec04-live"


def _registered_endpoint() -> Any:
    """登记进目录的 anthropic 兼容端点（base_url = 用户授权的那一个）。"""
    return load_llm_endpoints(_ENDPOINTS)[_ANTHROPIC_ENDPOINT]


def _registered_model() -> Any:
    return load_models(_MODELS)[_MODEL]


def _gate() -> Any:
    return evaluate_live_run_gate(
        credentials=EnvCredentialResolver(),
        endpoint=_registered_endpoint(),
        agent_runtime=os.environ.get("RESEARCHOS_AGENT_RUNTIME", ""),
        live_agent_runtime=OPENHANDS_RUNTIME,
        live_switch=live_e2e_switch_enabled(),
    )


def _live_run_facts(endpoint: Any, model: Any) -> tuple[Any, Any]:
    """段 1：登记端点上的真实 probe（ANTHROPIC 面由这一段驱动）⇒ 运行时指纹。"""
    probe = run_live_probe(
        gateway=OpenAIChatGateway(),
        credentials=EnvCredentialResolver(),
        endpoint=endpoint,
        model=model,
    )
    assert probe.verified and probe.ok, probe.to_json()
    return probe, endpoint


@dataclass(frozen=True, slots=True)
class _RunReads:
    """段 2 的读面快照：经**既有 API** 取，判据与 operator 看到的一致。"""

    run: dict[str, Any]
    failures: list[str]
    usage_entries: list[Any]
    artifacts: list[dict[str, Any]]
    evidence: list[dict[str, Any]]


def _execute_live_run(base_url: str, credential_ref: str) -> _RunReads:
    """段 2：真实 runtime 跑一次到终态（凭据值只在进程内传递，不落盘）。"""
    from services.api.app import create_app

    deps = openhands_deps(
        base_url,
        map_tools=True,
        allow_localhost=False,  # 真端点必须是公网地址：默认 deny 姿态不放松
        live_key=os.environ.get(credential_ref),
    )
    with TestClient(create_app(deps)) as client:
        created = start_run(client)
        run = client.get(f"/runs/{created['id']}").json()
        return _RunReads(
            run=run,
            failures=run_failures(client, run["id"]),
            usage_entries=[
                entry
                for entry in deps.budget.snapshot().entries
                if entry.resource_type is ResourceType.MODEL_TOKENS
            ],
            artifacts=client.get(f"/runs/{run['id']}/artifacts").json(),
            evidence=client.get(f"/runs/{run['id']}/evidence").json(),
        )


def _record_from(probe: Any, reads: _RunReads) -> Any:
    return build_live_run_record(
        run_id=reads.run["id"],
        terminal_state=reads.run["state"],
        endpoint_config_digest=probe.endpoint_config_digest,
        returned_model_identifier=probe.returned_model_identifier,
        probe_suite_digest=probe.probe_suite_digest,
        system_fingerprint=probe.system_fingerprint,
        model_tokens=sum(entry.quantity for entry in reads.usage_entries),
        usage_entries=len(reads.usage_entries),
        artifact_ids=tuple(str(item["id"]) for item in reads.artifacts),
        evidence_ids=tuple(str(item["id"]) for item in reads.evidence),
    )


def _assert_four_segments(record: Any, reads: _RunReads) -> None:
    """四段各自可判（缺哪段，记录里就点名哪段）。"""
    assert record.reached_terminal_state, (record.to_payload(), reads.failures)
    assert record.returned_model_identifier, record.reason
    assert record.usage_entries >= 1, (record.to_payload(), reads.failures)
    assert record.model_tokens > 0, record.to_payload()
    assert record.artifact_ids and record.evidence_ids, record.to_payload()
    # 口径：只能停在「可重复配置」（§4）；system_fingerprint 缺失是如实的缺口，不降级
    assert record.is_verified, record.to_payload()


def test_live_first_run_reaches_a_terminal_state(tmp_path: Path) -> None:
    """首次真实 run：到终态 + 指纹可判 + usage 归账 + 制品/证据可读。"""
    gate = _gate()
    if not gate.open:
        record = skip_record_for_gate(_RUN_ID, gate)
        pytest.skip(f"live run skipped: {record.reason}")

    endpoint = _registered_endpoint()
    probe, _ = _live_run_facts(endpoint, _registered_model())
    reads = _execute_live_run(endpoint.base_url, endpoint.credential_ref)
    record = _record_from(probe, reads)
    _assert_four_segments(record, reads)

    written = tmp_path / "live-run-record.json"
    written.write_text(
        json.dumps(record.to_payload(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    reloaded = json.loads(written.read_text(encoding="utf-8"))
    assert reloaded["verdict"] == "REPEATABLE_CONFIGURATION", reloaded
    assert reloaded["missing_fields"] == list(record.missing_fields), reloaded


def test_live_gate_stays_closed_without_configuration() -> None:
    """门的存在性：只要**三条**开门条件缺任一，门就是关的，且理由**逐条点名**缺的那些。

    D-11 之后条件是三条（显式开关 / runtime / 凭据），所以断言不能写成「点名 runtime
    或凭据」的二选一：**只用 runtime 开关、忘了 live 开关**是一个真实的操作者状态，
    那时两条都不在理由里，二选一判据会红——而门的行为是对的。
    这里**独立重算**当前哪些条件不满足，再要求理由把它们**全部**点名（比原判据更严）。
    """
    gate = _gate()
    if gate.open:
        pytest.skip("gate is open on this machine: the live branch above is the meaningful one")
    record = skip_record_for_gate(_RUN_ID, gate)
    assert record.is_verified is False
    assert record.verdict is ModelReproducibilityVerdict.NOT_VERIFIED

    endpoint = _registered_endpoint()
    expected_absent: list[str] = []
    if not live_e2e_switch_enabled():
        expected_absent.append(LIVE_RUN_SWITCH)
    if os.environ.get("RESEARCHOS_AGENT_RUNTIME", "") != OPENHANDS_RUNTIME:
        expected_absent.append("not configured")
    if not EnvCredentialResolver().has(endpoint.credential_ref):
        expected_absent.append(endpoint.credential_ref)
    reason = record.reason or ""
    assert expected_absent, "门是关的 ⇒ 至少有一条条件不满足（判据非空转）"
    for needle in expected_absent:
        assert needle in reason, (needle, reason)
