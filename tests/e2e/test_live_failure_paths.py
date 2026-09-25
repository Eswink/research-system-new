"""失败路径的实跑反证：**故意无效**的凭据必须**响亮失败**且**不泄露值**（GOAL-009 EC-04）。

**为什么需要一个新模块**：`test_ec04_live_first_run.py` 的判据是「live 成功」，
它在无效凭据下会**先**在 probe 段断言失败——那测的是「probe 会炸」，不是「run 会如实落终态」。
本模块只做一件事：**让 run 在无效凭据下跑到终态**，并核对失败语义与泄漏面。

**预置条件（显式开关，单条命令内联前缀，不写任何文件）**：

    RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_FAILURE_CASE=invalid-credential \
      LLM_MAIN_KEY=<故意无效的值> \
      pytest tests/e2e/test_live_failure_paths.py

未声明 `RESEARCHOS_LIVE_FAILURE_CASE` ⇒ **SKIP 并点名**。这条 skip 语义是**刻意的**：
本用例的**期望结果就是失败**，若它无条件运行，未来操作者跑整套 live 套件时会撞上一个
「期望失败」的用例，而「恒过的失败测试」什么都证明不了。

**凭据纪律**：注入值由操作者用内联前缀给出（本文件**不**写任何可用字面量），
本文件只把它从环境读出、传进解析器；失败消息与记录**不得**含该值——这正是本模块要钉的泄漏面。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from adapters.contracts.models_loaders import load_llm_endpoints
from adapters.relay.credential_resolver import EnvCredentialResolver
from packages.application.model_relay.live_run_gate import evaluate_live_run_gate
from packages.domain.budget import ResourceType
from services.api.runtime_support import OPENHANDS_RUNTIME
from tests.e2e.live_run_support import (
    openhands_deps,
    run_failures,
    start_run,
)
from tests.e2e.live_switch_support import live_e2e_switch_enabled

pytestmark = pytest.mark.requires_live_llm

_ENDPOINTS = "examples/config/llm_endpoints.yaml"
_ANTHROPIC_ENDPOINT = "agnes-anthropic"
_CASE_ENV = "RESEARCHOS_LIVE_FAILURE_CASE"
_INVALID_CREDENTIAL_CASE = "invalid-credential"
_TERMINAL_FAILURES = frozenset({"FAILED", "CANCELLED", "TIMED_OUT"})


@dataclass(frozen=True, slots=True)
class _Reads:
    """run 的读面快照（经既有 API 取）。"""

    state: str
    failures: list[str]
    tokens: int
    usage_entries: int


def _endpoint() -> Any:
    return load_llm_endpoints(_ENDPOINTS)[_ANTHROPIC_ENDPOINT]


def _declared_case() -> str:
    case = os.environ.get(_CASE_ENV, "")
    if case != _INVALID_CREDENTIAL_CASE:
        pytest.skip(
            f"{_CASE_ENV} is not set to {_INVALID_CREDENTIAL_CASE!r} — this counter-proof "
            "expects failure by construction and must not run in a normal live suite"
        )
    if not live_e2e_switch_enabled():
        pytest.skip(
            "the live run switch is off — this counter-proof never runs in the default gate "
            "(it expects failure by construction)"
        )
    return case


def _assert_gate_is_open() -> Any:
    """门只看存在性 ⇒ 值**无效**也应当开门（§7 第一格）。这条**先**判。

    否则下面的「失败」可能来自**门关着**而不是**凭据被拒**——两者语义完全不同。
    """
    endpoint = _endpoint()
    gate = evaluate_live_run_gate(
        credentials=EnvCredentialResolver(),
        endpoint=endpoint,
        agent_runtime=os.environ.get("RESEARCHOS_AGENT_RUNTIME", ""),
        live_agent_runtime=OPENHANDS_RUNTIME,
        live_switch=live_e2e_switch_enabled(),
    )
    assert gate.open is True, (
        "the gate must answer the presence question even for an invalid value; "
        f"if it is closed, this run would prove nothing about provider rejection: {gate.reason}"
    )
    return endpoint


def _run_with(endpoint: Any, submitted: str) -> _Reads:
    """发起**那一次**出站并读回终态、失败原因与用量。"""
    from services.api.app import create_app

    deps = openhands_deps(
        endpoint.base_url,
        map_tools=True,
        allow_localhost=False,  # 真端点必须是公网地址：默认 deny 姿态不放松
        live_key=submitted,
    )
    with TestClient(create_app(deps)) as client:
        created = start_run(client)
        run = client.get(f"/runs/{created['id']}").json()
        failures = run_failures(client, run["id"])
    usage = [
        entry
        for entry in deps.budget.snapshot().entries
        if entry.resource_type is ResourceType.MODEL_TOKENS
    ]
    return _Reads(
        state=str(run["state"]),
        failures=failures,
        tokens=sum(entry.quantity for entry in usage),
        usage_entries=len(usage),
    )


def test_live_invalid_credential_fails_loudly_without_leaking(tmp_path: Path) -> None:
    """无效凭据：门**开** ⇒ 发起调用 ⇒ **明确失败**并落终态；失败消息**不含**凭据值。"""
    _declared_case()
    endpoint = _assert_gate_is_open()
    submitted = os.environ.get(endpoint.credential_ref, "")
    assert submitted, "the counter-proof needs a non-empty (deliberately invalid) value"

    reads = _run_with(endpoint, submitted)

    assert reads.state in _TERMINAL_FAILURES, (
        f"an invalid credential must not look like a normal run: {reads.state}"
    )
    assert reads.failures, "a failed run must record why (an empty reason is a silent failure)"
    assert submitted not in "\n".join(reads.failures), (
        "the failure record leaked the credential value — that is a defect, not a warning"
    )
    assert reads.tokens == 0 and reads.usage_entries == 0, (
        "a rejected credential must not have billed tokens"
    )

    observed = tmp_path / "invalid-credential-observation.json"
    observed.write_text(
        f'{{"run_state": "{reads.state}", "failure_count": {len(reads.failures)}, '
        f'"usage_entries": {reads.usage_entries}, "credential_leaked": false}}\n',
        encoding="utf-8",
    )
