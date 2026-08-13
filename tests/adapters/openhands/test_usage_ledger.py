"""Usage → BudgetLedger 集成测试：run() 终态后 usage 归一化写入 ledger。

M6 复审 F-2 回归：usage_entries_from_stats / budget_ledger 必须接入 adapter
主路径（此前只测纯函数）；usage 是 signal，记账失败不阻断 run 结果。
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openhands.sdk.llm import Message, TextContent
from openhands.sdk.testing import TestLLM
from openhands.sdk.workspace.local import LocalWorkspace

import adapters.openhands.session_builder as session_builder_module
from adapters.fakes import FakeBudgetLedger, FakeCredentialResolver, FakePolicyEvaluator
from adapters.openhands.runtime_adapter import OpenHandsRuntimeAdapter
from adapters.openhands.session_types import AdapterDependencies
from packages.application.ports.agent_runtime import AgentSessionSpec
from packages.domain.budget import LedgerCostStatus, ResourceType, UsageLedgerEntry
from packages.domain.enums import PolicyDecision
from packages.domain.session_state import AgentSessionState
from tests.contracts.fixtures import agent_spec, research_task, role_definition, task_contract


def _spec() -> AgentSessionSpec:
    return AgentSessionSpec(
        task_id=research_task().id,
        task_contract=task_contract(),
        role=role_definition(),
        agent=agent_spec(),
    )


def _make_adapter(tmp_path: Path, ledger: FakeBudgetLedger) -> OpenHandsRuntimeAdapter:
    llm = TestLLM.from_messages([
        Message(role="assistant", content=[TextContent(text="Done.")]),
    ])
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir(exist_ok=True)
    deps = AdapterDependencies(
        credential_resolver=FakeCredentialResolver({"LLM_KEY": "sk-test"}),
        policy_evaluator=FakePolicyEvaluator(default=PolicyDecision.ALLOW),
        build_llm=lambda spec: llm,
        build_workspace=lambda lease, session_id: LocalWorkspace(working_dir=str(workspace_root)),
        budget_ledger=ledger,
        persistence_dir=str(tmp_path / "persist"),
    )
    return OpenHandsRuntimeAdapter(deps)


def _fake_entry(now: datetime) -> UsageLedgerEntry:
    return UsageLedgerEntry(
        entry_id="u-1:tokens",
        resource_type=ResourceType.MODEL_TOKENS,
        quantity=150,
        unit="tokens",
        cost_status=LedgerCostStatus.UNKNOWN,
        source="openhands",
        occurred_at=now,
        task_id="t-1",
        agent_id="a-1",
    )


class TestUsageLedgerIntegration:
    def test_run_records_usage_to_ledger(self, tmp_path: Path, monkeypatch: Any) -> None:
        ledger = FakeBudgetLedger()
        runtime = _make_adapter(tmp_path, ledger)
        now = datetime(2026, 8, 13, tzinfo=timezone.utc)
        monkeypatch.setattr(
            session_builder_module,
            "publish_usage",
            lambda stats, ledger, context: (
                ledger.record_usage(_fake_entry(now)) or _fake_entry(now),
            ),
        )
        handle = runtime.create_session(_spec())
        result = runtime.run(handle.session_id)
        assert result.status == AgentSessionState.State.SUCCEEDED
        entries = ledger.snapshot().entries
        assert len(entries) == 1
        assert entries[0].entry_id == "u-1:tokens"
        assert entries[0].quantity == 150
        runtime.close()

    def test_usage_failure_does_not_break_run(self, tmp_path: Path, monkeypatch: Any) -> None:
        ledger = FakeBudgetLedger()
        runtime = _make_adapter(tmp_path, ledger)

        def _boom(stats: object, ledger: object, context: object) -> None:
            raise RuntimeError("ledger write failed")

        monkeypatch.setattr(session_builder_module, "publish_usage", _boom)
        handle = runtime.create_session(_spec())
        result = runtime.run(handle.session_id)
        assert result.status == AgentSessionState.State.SUCCEEDED
        assert any(
            call["method"] == "usage" and call["error"] == "usage_report_failed"
            for call in runtime.calls
        )
        runtime.close()

    def test_run_without_ledger_is_noop(self, tmp_path: Path) -> None:
        llm = TestLLM.from_messages([
            Message(role="assistant", content=[TextContent(text="Done.")]),
        ])
        workspace_root = tmp_path / "ws"
        workspace_root.mkdir(exist_ok=True)
        deps = AdapterDependencies(
            credential_resolver=FakeCredentialResolver({"LLM_KEY": "sk-test"}),
            policy_evaluator=FakePolicyEvaluator(default=PolicyDecision.ALLOW),
            build_llm=lambda spec: llm,
            build_workspace=lambda lease, session_id: LocalWorkspace(
                working_dir=str(workspace_root)
            ),
            persistence_dir=str(tmp_path / "persist"),
        )
        runtime = OpenHandsRuntimeAdapter(deps)
        handle = runtime.create_session(_spec())
        result = runtime.run(handle.session_id)
        assert result.status == AgentSessionState.State.SUCCEEDED
        runtime.close()
