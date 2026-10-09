"""GOAL-20261009-042 EC-03/EC-04 判据：**记忆时效门驱动运行链步**（实跑 + 两时点）。

配套单元判据在 `test_memory_validity_gate.py`（纯判定：三态不混用 / 点名 / 缺省不变）。
本文件跑**运行链**（`execute_run_chain_capabilities`），证明门**真的**决定工具跑不跑：

- **该跳过时必跳过**：过期记忆在场 ⇒ 声明门的第二步**不调用** provider（调用次数 = 1）；
- **不该跳过时不跳**：只有待复核 ⇒ 两步都执行，且走**标注**通道（与跳过**不同通道**）；
- **不该红时不红**：全 `USE` ⇒ 两步都执行，两条通道都空；
- **缺省逐字节不变**：未声明门 ⇒ 过期记忆**不**阻止执行，两通道都空；
- **两时点（EC-04a）**：**同一份**记忆在 `expires_at` 两侧 ⇒ 行为可区分，且两个方向的
  判词都**点名**状态与被引的声明值。
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, cast

import pytest

import tests.application.run_orchestration.test_memory_validity_gate as _unit
from adapters.canonical.memory_read import memory_read
from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger, FakePolicyEvaluator
from adapters.fakes.memory_store import FakeMemoryStore
from packages.application.run_orchestration.phase_capabilities import (
    CapabilityDeps,
    CapabilityStepOutcome,
    RunChainCall,
    execute_run_chain_capabilities,
)
from packages.application.run_orchestration.task_executor import SessionSpecContext
from packages.domain.artifacts import Artifact
from packages.domain.core import ID, Digest, Timestamp
from packages.domain.enums import (
    ActivationPolicy,
    MemoryTier,
    MemoryType,
    ModelBindingMode,
    ProviderType,
    RoleCategory,
)
from packages.domain.memory import MemoryWriteProposal
from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition
from packages.domain.tasks import ResearchTask
from packages.domain.tools import ToolProviderSpec

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

_SOURCE = "test:goal042-gate"
_EPOCH = "2026-10-09T00:00:00+00:00"
_ARTIFACTS = FakeArtifactStore()


def _memory_store(*proposals: MemoryWriteProposal) -> FakeMemoryStore:
    store = FakeMemoryStore(allowed_sources=(_SOURCE,))
    for proposal in proposals:
        store.commit(proposal)
    return store


def _with_expiry(memory_id: str, expires_at: datetime) -> MemoryWriteProposal:
    return MemoryWriteProposal(
        id=memory_id,
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content=f"内容 {memory_id}",
        provenance=_SOURCE,
        confidence=0.9,
        expires_at=Timestamp(expires_at),
    )


def _expired(memory_id: str) -> MemoryWriteProposal:
    return _with_expiry(memory_id, datetime(2026, 10, 8, tzinfo=timezone.utc))


def _due(memory_id: str) -> MemoryWriteProposal:
    return MemoryWriteProposal(
        id=memory_id,
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content=f"内容 {memory_id}",
        provenance=_SOURCE,
        confidence=0.9,
        review_after=Timestamp(datetime(2026, 10, 8, tzinfo=timezone.utc)),
    )


def _plain(memory_id: str) -> MemoryWriteProposal:
    return MemoryWriteProposal(
        id=memory_id,
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content=f"内容 {memory_id}",
        provenance=_SOURCE,
        confidence=0.9,
    )


def _spill(store: FakeArtifactStore, artifact_id: str, content: bytes, digest: Any) -> None:
    store.put(
        Artifact(
            id=artifact_id,
            digest=digest,
            size_bytes=len(content),
            media_type="application/json",
            created_by="test:goal042",
            source_refs=["task:test"],
            classification="tool-result",
        ),
        content,
    )


class _MemoryProvider:
    """按**本次调用给到的时点**产出读面载荷，并记录调用次数（反证：该不该被调用）。"""

    def __init__(self, store: FakeMemoryStore) -> None:
        self._store = store
        self.calls: list[str] = []

    def execute(self, spec: Any, call: Any) -> Any:
        from packages.domain.enums import ToolResultStatus
        from packages.domain.tools import ToolResultRecord

        self.calls.append(call.tool_id)
        artifact_id = f"tool-args:{call.task_id}:{call.operation_key}"
        args = json.loads(_ARTIFACTS.get(artifact_id).decode("utf-8"))
        payload = memory_read(self._store, {"now": str(args.get("now", ""))})
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        digest = Digest.of_bytes(content)
        # 制品 id 的形状与 `fetch_spilled_result` 的重建式**同源**（逐字）。
        _spill(
            _ARTIFACTS,
            f"tool-result:{call.task_id}:{call.operation_key}:{call.tool_id}",
            content,
            digest,
        )
        return ToolResultRecord(
            task_id=call.task_id,
            attempt=1,
            operation_key=call.operation_key,
            tool_id=call.tool_id,
            status=ToolResultStatus.SUCCEEDED,
            output_digest=digest,
            recorded_at=Timestamp.now(),
        )


def _spec() -> SessionSpecContext:
    return SessionSpecContext(
        role=RoleDefinition(
            id="domain_researcher",
            role_type="domain_researcher",
            category=RoleCategory.DISCOVERY,
            activation_default=ActivationPolicy.ALWAYS,
        ),
        agent=AgentSpec(
            id="agent-1",
            role="domain_researcher",
            model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value="model-1"),
        ),
        frozen_manifest_digest="manifest-digest",
        frozen_tool_set=("m12_artifact",),
        run_chain_tool_ids=("m12_artifact",),
    )


def _task() -> ResearchTask:
    return ResearchTask(id=ID.generate(), run_id=ID.generate(), contract_id="memory_gate")


def _run(
    store: FakeMemoryStore, *, declared: bool, moment: str = _EPOCH
) -> tuple[CapabilityStepOutcome, _MemoryProvider]:
    """两步：① 读面（产出载荷）；② 门（按第一步结果分派）—— 共两条同 provider 的声明。"""
    global _ARTIFACTS
    _ARTIFACTS = FakeArtifactStore()
    provider = _MemoryProvider(store)
    spec = ToolProviderSpec(
        id="m12_artifact",
        kind=ProviderType.NATIVE,
        trust_level="BUILT_IN",  # type: ignore[arg-type]
        capabilities=["memory.read"],
        effect_class="READ_ONLY",  # type: ignore[arg-type]
    )
    first = RunChainCall(
        provider_id="m12_artifact",
        tool_id="memory_read",
        capability="memory.read",
        fixed_arguments={"now": moment},
    )
    second = replace(first, memory_validity_gate=declared)
    deps = CapabilityDeps(
        calls=(first, second),
        providers={"m12_artifact": cast("Any", provider)},
        provider_specs={"m12_artifact": spec},
        policy=FakePolicyEvaluator(),
        artifacts=_ARTIFACTS,
        ledger=FakeEvidenceLedger(),
    )
    return execute_run_chain_capabilities(deps, _task(), _spec()), provider


class TestTheGateDrivesTheRunChainStep:
    """门**真的**决定工具跑不跑（调用次数是可判事实，不是措辞）。"""

    def test_an_expired_record_prevents_the_declared_step_from_running(self) -> None:
        outcome, provider = _run(_memory_store(_expired("m-old")), declared=True)
        assert outcome.failure_message is None, outcome.failure_message
        assert provider.calls == ["memory_read"], ("门必须挡住第二次调用", provider.calls)
        assert outcome.skipped and "m-old" in outcome.skipped[0], outcome.skipped
        assert outcome.annotations == (), ("跳过与标注不得混用", outcome.annotations)

    def test_a_due_review_runs_the_step_and_annotates(self) -> None:
        outcome, provider = _run(_memory_store(_due("m-due")), declared=True)
        assert outcome.failure_message is None, outcome.failure_message
        assert provider.calls == ["memory_read", "memory_read"], (
            "待复核 ⇒ 照常执行",
            provider.calls,
        )
        assert outcome.annotations and "m-due" in outcome.annotations[0], outcome.annotations
        assert outcome.skipped == (), ("待复核不得进跳过通道", outcome.skipped)

    def test_usable_records_keep_both_channels_empty(self) -> None:
        outcome, provider = _run(_memory_store(_plain("m-ok")), declared=True)
        assert provider.calls == ["memory_read", "memory_read"], provider.calls
        assert outcome.skipped == () and outcome.annotations == (), outcome

    def test_without_the_declaration_an_expired_record_does_not_stop_the_call(self) -> None:
        outcome, provider = _run(_memory_store(_expired("m-old")), declared=False)
        assert provider.calls == ["memory_read", "memory_read"], (
            "缺省不得改变行为",
            provider.calls,
        )
        assert outcome.skipped == () and outcome.annotations == (), outcome


class TestTheSameRecordBehavesDifferentlyAcrossTwoMoments:
    """EC-04(a)：**同一份**记忆在 `expires_at` 两侧 ⇒ 行为可区分且判词点名。"""

    def test_before_the_declared_boundary_the_step_runs(self) -> None:
        store = _memory_store(
            _with_expiry("m-boundary", datetime(2026, 10, 9, tzinfo=timezone.utc))
        )
        outcome, provider = _run(store, declared=True, moment="2026-10-08T23:59:59+00:00")
        assert outcome.failure_message is None, outcome.failure_message
        assert provider.calls == ["memory_read", "memory_read"], (
            "未到期 ⇒ 两步都执行",
            provider.calls,
        )
        assert outcome.skipped == (), outcome.skipped

    def test_after_the_declared_boundary_the_step_is_skipped_and_named(self) -> None:
        store = _memory_store(
            _with_expiry("m-boundary", datetime(2026, 10, 9, tzinfo=timezone.utc))
        )
        outcome, provider = _run(store, declared=True, moment="2026-10-09T00:00:01+00:00")
        assert outcome.failure_message is None, outcome.failure_message
        assert provider.calls == ["memory_read"], ("已过期 ⇒ 门挡住第二步", provider.calls)
        assert outcome.skipped, outcome
        assert "m-boundary" in outcome.skipped[0], outcome.skipped
        assert "EXPIRED" in outcome.skipped[0], outcome.skipped
        assert "2026-10-09" in outcome.skipped[0], ("判词点名被引的声明值", outcome.skipped)


def test_the_memory_row_shape_matches_the_read_face() -> None:
    """一致性：单元判据的夹具形态与 `memory_read` 的**真实**产物同形（不是自造形状）。"""
    store = _memory_store(_expired("m-shape"))
    produced = memory_read(store, {"now": _EPOCH})
    rows = produced["memories"]
    assert isinstance(rows, list) and rows, rows
    item = rows[0]
    assert isinstance(item, dict), item
    row: dict[str, Any] = dict(item)
    assert set(row) >= {"memory_id", "disposition", "validity", "reason"}, row
    fixture: dict[str, Any] = _unit._row("m-shape", "SKIP")
    assert set(fixture) == {"memory_id", "disposition", "validity", "reason"}, fixture
