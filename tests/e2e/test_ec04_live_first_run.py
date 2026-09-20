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
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from adapters.contracts.models_loaders import load_llm_endpoints, load_models
from adapters.relay.credential_resolver import EnvCredentialResolver
from adapters.relay.gateway import OpenAIChatGateway
from packages.application.model_relay.live_probe import run_live_probe
from packages.application.model_relay.live_run_gate import (
    evaluate_live_run_gate,
    skip_record_for_gate,
)
from packages.application.model_relay.live_run_record import build_live_run_record
from packages.domain.budget import ResourceType
from packages.domain.enums import ModelReproducibilityVerdict
from services.api.runtime_support import OPENHANDS_RUNTIME
from tests.e2e.test_ec03_real_runtime_offline_chain import _failures, _openhands_deps, _start

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
    )


def test_live_first_run_reaches_a_terminal_state(tmp_path: Path) -> None:
    """首次真实 run：到终态 + 指纹可判 + usage 归账 + 制品/证据可读。"""
    gate = _gate()
    if not gate.open:
        record = skip_record_for_gate(_RUN_ID, gate)
        pytest.skip(f"live run skipped: {record.reason}")

    endpoint = _registered_endpoint()
    model = _registered_model()
    resolver = EnvCredentialResolver()

    # 段 1：登记端点上的真实 probe ⇒ 运行时指纹（ANTHROPIC 面由这一段驱动）
    probe = run_live_probe(
        gateway=OpenAIChatGateway(),
        credentials=resolver,
        endpoint=endpoint,
        model=model,
    )
    assert probe.verified and probe.ok, probe.to_json()

    # 段 2：真实 runtime 跑一次到终态（凭据值只在进程内传递，不落盘）
    deps = _openhands_deps(
        endpoint.base_url,
        map_tools=True,
        allow_localhost=False,  # 真端点必须是公网地址：默认 deny 姿态不放松
        live_key=os.environ.get(endpoint.credential_ref),
    )
    from services.api.app import create_app

    with TestClient(create_app(deps)) as client:
        created = _start(client)
        run = client.get(f"/runs/{created['id']}").json()
        failures = _failures(client, run["id"])
        entries = [
            entry
            for entry in deps.budget.snapshot().entries
            if entry.resource_type is ResourceType.MODEL_TOKENS
        ]
        artifacts = client.get(f"/runs/{run['id']}/artifacts").json()
        evidence = client.get(f"/runs/{run['id']}/evidence").json()

    record = build_live_run_record(
        run_id=run["id"],
        terminal_state=run["state"],
        endpoint_config_digest=probe.endpoint_config_digest,
        returned_model_identifier=probe.returned_model_identifier,
        probe_suite_digest=probe.probe_suite_digest,
        system_fingerprint=probe.system_fingerprint,
        model_tokens=sum(entry.quantity for entry in entries),
        usage_entries=len(entries),
        artifact_ids=tuple(str(item["id"]) for item in artifacts),
        evidence_ids=tuple(str(item["id"]) for item in evidence),
    )

    # 判据：指纹/归账/制品/证据四段各自可判（缺哪段，记录里就点名哪段）
    assert record.reached_terminal_state, (record.to_payload(), failures)
    assert record.returned_model_identifier, record.reason
    assert record.usage_entries >= 1, (record.to_payload(), failures)
    assert record.model_tokens > 0, record.to_payload()
    assert record.artifact_ids and record.evidence_ids, record.to_payload()
    # 口径：只能停在「可重复配置」（§4）；system_fingerprint 缺失是如实的缺口，不降级
    assert record.is_verified, record.to_payload()

    written = tmp_path / "live-run-record.json"
    written.write_text(
        json.dumps(record.to_payload(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    reloaded = json.loads(written.read_text(encoding="utf-8"))
    assert reloaded["verdict"] == "REPEATABLE_CONFIGURATION", reloaded
    assert reloaded["missing_fields"] == list(record.missing_fields), reloaded


def test_live_gate_stays_closed_without_configuration() -> None:
    """门的存在性：本机默认（无 runtime 配置、无凭据）**必须**是关的。"""
    gate = _gate()
    if gate.open:
        pytest.skip("gate is open on this machine: the live branch above is the meaningful one")
    record = skip_record_for_gate(_RUN_ID, gate)
    assert record.is_verified is False
    assert record.verdict is ModelReproducibilityVerdict.NOT_VERIFIED
    # 关门理由点名未满足的条件：runtime 未配置，或缺哪个凭据
    reason = record.reason or ""
    assert "not configured" in reason or _registered_endpoint().credential_ref in reason, reason
