"""GOAL-029 后续 cycle 承接的读能力判据（与 `test_canonical_read_provider.py` 拆分）。

**为什么拆**：`test_canonical_read_provider.py` 有 **450 行硬上限**（规模门），而本 GOAL 的
EC-01/EC-03 又逐轮往它上面加能力组的判据（workspace / 两条新承接 / claim / 端到端桥 / 工具面）
⇒ 401 → 501 行**越界**（既有门禁当场判红）。拆分的切法：
**共享夹具与「最初的读面」判据留在原文件**（`artifact.read` / `evidence.read` 与四个辅助函数），
**后续 cycle 新增的能力组判据移到这里** —— 两组共用同一批夹具，不重复造。

辅助函数（`_call` / `_spilled_content` / `_allow_all` / `_write_artifact` / `_PROVIDER` /
`_RUN_ID`）从原文件 import：它们是**夹具**而不是被测对象，两处各写一份会漂移。
"""

from __future__ import annotations

import json
from typing import Any, cast

import pytest

from adapters.canonical import CanonicalReadProvider
from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger
from packages.application.ports.errors import InvalidInputError

# 共享夹具与常量（原文件里定义；这两份判据共用同一批，避免各写一份漂移）
from tests.adapters.canonical.test_canonical_read_provider import (
    _PROVIDER,
    _PROVIDER_ID,
    _RUN_ID,
    _allow_all,
    _call,
    _spilled_content,
    _write_artifact,
)

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


class TestWorkspaceReadStaysRunScoped:
    """④ `workspace.read` 只报本 run 的制品（别的 run 不出现）。"""

    def test_only_this_runs_artifacts_are_listed(self) -> None:
        artifacts = FakeArtifactStore()
        _write_artifact(artifacts, f"{_RUN_ID}:deliverable.json", {"ok": True})
        _write_artifact(artifacts, "other-run:deliverable.json", {"ok": False})
        provider = CanonicalReadProvider(artifacts)
        record = _call("workspace_read", {"run_id": _RUN_ID}, artifacts)

        payload = _spilled_content(artifacts, provider.execute(_PROVIDER, record))
        assert isinstance(payload, dict), payload
        ids = [item["id"] for item in payload["artifacts"]]
        assert ids == [f"{_RUN_ID}:deliverable.json"], ids

    def test_the_probe_fixture_is_not_empty(self) -> None:
        """受判面非空（MEM-156）：上一条必须是「在非空集合上筛对了」，不是「读的空集」。"""
        artifacts = FakeArtifactStore()
        _write_artifact(artifacts, f"{_RUN_ID}:deliverable.json", {"ok": True})
        _write_artifact(artifacts, "other-run:deliverable.json", {"ok": False})
        assert len(artifacts.list_refs()) >= 2, "夹具必须真的写入了两个 run 的制品"


class TestTheTwoNewlyCarriedReads:
    """cycle 2 承接的两条：`budget.read` / `deliverable.read`（都读 canonical state）。"""

    def test_budget_read_returns_the_ledger_snapshot(self) -> None:
        """账本在场 ⇒ 读出预留与用量（字段取自真实 `LedgerSnapshot`）。"""
        from adapters.fakes import FakeBudgetLedger
        from packages.domain.budget import BudgetPolicy, BudgetReservation, ResourceType

        artifacts = FakeArtifactStore()
        budget = FakeBudgetLedger()
        budget.reserve(
            (
                BudgetReservation(
                    id="res-goal029",
                    scope="run:run-goal029-probe",
                    resource_type=ResourceType.MODEL_TOKENS,
                    quantity=1000,
                    unit="tokens",
                ),
            ),
            BudgetPolicy(id="goal029-probe"),
        )
        provider = CanonicalReadProvider(artifacts, None, budget_ledger=budget)
        record = _call("budget_read", {"run_id": "run-goal029-probe"}, artifacts)

        payload = _spilled_content(artifacts, provider.execute(_PROVIDER, record))
        assert isinstance(payload, dict), payload
        assert payload["reservations"], ("预留必须被读到（受判面非空）", payload)
        assert payload["reservations"][0]["resource_type"] == ResourceType.MODEL_TOKENS.value, (
            payload
        )

    def test_budget_read_without_a_ledger_is_named(self) -> None:
        """账本缺失 ⇒ 点名拒绝（**不**返回空账本冒充「没有用量」）。"""
        artifacts = FakeArtifactStore()
        provider = CanonicalReadProvider(artifacts, None, budget_ledger=None)
        record = _call("budget_read", {"run_id": "r"}, artifacts)
        with pytest.raises(InvalidInputError, match="BudgetLedger"):
            provider.execute(_PROVIDER, record)

    def test_deliverable_read_returns_the_persisted_payload(self) -> None:
        """交付物在场 ⇒ 读出 payload 与 digest（落点与读面路由**同一**约定）。"""
        artifacts = FakeArtifactStore()
        payload = {"summary": "probe deliverable", "claims": ["c1"]}
        _write_artifact(artifacts, f"{_RUN_ID}:deliverable.json", payload)
        provider = CanonicalReadProvider(artifacts)
        record = _call("deliverable_read", {"run_id": _RUN_ID}, artifacts)

        read_back = _spilled_content(artifacts, provider.execute(_PROVIDER, record))
        assert isinstance(read_back, dict), read_back
        assert read_back["artifact_id"] == f"{_RUN_ID}:deliverable.json", read_back
        assert read_back["deliverable"] == payload, read_back
        assert read_back["artifact_digest"].startswith("sha256:"), read_back

    def test_deliverable_read_names_a_missing_deliverable(self) -> None:
        """未产出 ⇒ 点名（不生成空报告冒充；与读面路由的 `available=false` 同一事实）。"""
        artifacts = FakeArtifactStore()
        provider = CanonicalReadProvider(artifacts)
        record = _call("deliverable_read", {"run_id": "run-without-deliverable"}, artifacts)
        with pytest.raises(InvalidInputError, match="no persisted deliverable"):
            provider.execute(_PROVIDER, record)


class TestClaimReadCarriesTheAGroupRead:
    """`claim.read`（cycle 2 收口审计补上的第二条 A 组读；此前**声明了却没实现**）。"""

    def _ledger(self) -> Any:
        from adapters.fakes import FakeEvidenceLedger
        from packages.domain.evidence import (
            Claim,
            Evidence,
            EvidenceRelation,
            EvidenceRelationType,
            SourceRecord,
        )

        ledger = FakeEvidenceLedger()
        ledger.register_source(
            SourceRecord(origin="probe:src", content_digest="sha256:" + "a" * 64)
        )
        ledger.register_evidence(
            Evidence(
                id="ev-claim",
                source_ref="probe:src",
                content_digest="sha256:" + "b" * 64,
                run_id=_RUN_ID,
            )
        )
        ledger.register_claim(Claim(id="cl-1", statement="probe statement"))
        ledger.attach_relation(
            EvidenceRelation(
                claim_id="cl-1",
                evidence_id="ev-claim",
                relation=EvidenceRelationType.SUPPORTS,
            )
        )
        return ledger

    def test_claims_come_back_with_their_relations(self) -> None:
        artifacts = FakeArtifactStore()
        provider = CanonicalReadProvider(artifacts, self._ledger())
        record = _call("claim_read", {"run_id": _RUN_ID}, artifacts)

        payload = _spilled_content(artifacts, provider.execute(_PROVIDER, record))
        assert isinstance(payload, dict), payload
        assert [item["id"] for item in payload["claims"]] == ["cl-1"], payload
        claim = payload["claims"][0]
        assert claim["statement"] == "probe statement", claim
        assert claim["relations"] == [{"evidence_id": "ev-claim", "relation": "SUPPORTS"}], claim

    def test_a_run_filter_excludes_claims_without_its_evidence(self) -> None:
        """给了 `run_id` ⇒ 只列**引用到该 run 证据**的 claim（与 evidence_read 同一口径）。"""
        artifacts = FakeArtifactStore()
        provider = CanonicalReadProvider(artifacts, self._ledger())
        record = _call("claim_read", {"run_id": "some-other-run"}, artifacts)

        raw = _spilled_content(artifacts, provider.execute(_PROVIDER, record))
        assert isinstance(raw, dict), raw
        assert raw["claims"] == [], raw

    def test_without_a_ledger_it_is_named(self) -> None:
        artifacts = FakeArtifactStore()
        provider = CanonicalReadProvider(artifacts, None)
        record = _call("claim_read", {"run_id": _RUN_ID}, artifacts)
        with pytest.raises(InvalidInputError, match="EvidenceLedger"):
            provider.execute(_PROVIDER, record)


class TestTheExperimentReadsAreStoreBacked:
    """`experiment.read` / `experiment_plan.read`（A 组补足到 5 条的两条）。"""

    def _store(self) -> Any:
        """一个真装了计划的 store（用 `ID.generate()` —— `ID` 强制 UUID4 规范形态）。"""
        from adapters.fakes.experiment_store import FakeExperimentStore
        from packages.domain.core import ID
        from packages.domain.experiments import ExperimentPlan

        store = FakeExperimentStore()
        store.save_plan(ExperimentPlan(id=ID.generate(), name="probe plan", hypothesis="h1"))
        return store

    def test_experiment_plan_read_lists_the_canonical_plans(self) -> None:
        artifacts = FakeArtifactStore()
        provider = CanonicalReadProvider(artifacts, None, experiment_store=self._store())
        record = _call("experiment_plan_read", {}, artifacts)

        payload = _spilled_content(artifacts, provider.execute(_PROVIDER, record))
        assert isinstance(payload, dict), payload
        assert [item["name"] for item in payload["plans"]] == ["probe plan"], payload
        assert payload["plans"][0]["id"], payload  # 真 id 在场（不写死字面量）

    def test_experiment_plan_read_without_a_store_is_named(self) -> None:
        """store 缺失 ⇒ 点名（**不**返回空列表冒充「没有计划」）。"""
        artifacts = FakeArtifactStore()
        provider = CanonicalReadProvider(artifacts, None, experiment_store=None)
        record = _call("experiment_plan_read", {}, artifacts)
        with pytest.raises(InvalidInputError, match="ExperimentStore"):
            provider.execute(_PROVIDER, record)

    def test_experiment_read_projects_from_evidence_like_the_http_face(self) -> None:
        """与 HTTP 读面**同源**：证据里发现 `experiment_run_id` → store 取域事实。"""
        from packages.domain.evidence import (
            Claim,
            Evidence,
            EvidenceRelation,
            EvidenceRelationType,
            SourceRecord,
        )

        artifacts = FakeArtifactStore()
        ledger = FakeEvidenceLedger()
        ledger.register_source(
            SourceRecord(origin="probe:exp", content_digest="sha256:" + "e" * 64)
        )
        ledger.register_evidence(
            Evidence(
                id="ev-exp",
                source_ref="probe:exp",
                content_digest="sha256:" + "f" * 64,
                run_id=_RUN_ID,
                experiment_run_id="exp-run-1",
                artifact_id="metrics-artifact",
            )
        )
        ledger.register_claim(Claim(id="cl-exp", statement="exp claim"))
        ledger.attach_relation(
            EvidenceRelation(
                claim_id="cl-exp",
                evidence_id="ev-exp",
                relation=EvidenceRelationType.SUPPORTS,
            )
        )
        provider = CanonicalReadProvider(artifacts, ledger, experiment_store=self._store())
        record = _call("experiment_read", {"run_id": _RUN_ID}, artifacts)

        payload = _spilled_content(artifacts, provider.execute(_PROVIDER, record))
        assert isinstance(payload, dict), payload
        assert len(payload["experiments"]) == 1, payload
        item = payload["experiments"][0]
        assert item["experiment_run_id"] == "exp-run-1", item
        assert item["artifact_id"] == "metrics-artifact", item
        # store 里没有这个 run 域记录 ⇒ 如实标注（不编造 state/plan_id）
        assert item["domain_record"] is None, item
        assert "no ExperimentRun" in str(item["domain_record_reason"]), item

    def test_experiment_read_requires_a_run_id(self) -> None:
        artifacts = FakeArtifactStore()
        provider = CanonicalReadProvider(
            artifacts, FakeEvidenceLedger(), experiment_store=self._store()
        )
        record = _call("experiment_read", {}, artifacts)
        with pytest.raises(InvalidInputError, match="run_id"):
            provider.execute(_PROVIDER, record)


class TestTheRealBridgeReturnsContent:
    """**端到端**：canonical 读面 → 会话工具桥 → 内容回到调用方（真链条，非空壳）。

    这一臂钉住一条实测过的真缺陷：`spill_large_result` 的缺省阈值是 32 KiB，低于阈值的结果
    **不落盘**（只留 digest），而桥**必须**把内容交回模型 ⇒ 默认阈值下**任何**小结果都会走到
    `produced no spilled output` 的点名拒绝 —— 也就是绝大多数读。修法是把「内容必须可取回」
    作为**消费者的要求**在 provider 侧表达（`spill_threshold_bytes=1`，与运行链
    `tests/e2e/literature_chain_support.py` 的既有约定同源）。
    """

    def test_the_bridge_hands_the_content_back(self) -> None:
        from adapters.openhands.session_tool_invocation import SessionToolSpec, make_tool_invoker

        artifacts = FakeArtifactStore()
        payload = {"hello": "world", "n": 1}
        _write_artifact(artifacts, f"{_RUN_ID}:deliverable.json", payload)
        provider = CanonicalReadProvider(artifacts)

        invoker = make_tool_invoker(
            SessionToolSpec(
                provider_id=_PROVIDER_ID, tool_id="artifact_read", capability="artifact.read"
            ),
            providers={_PROVIDER_ID: cast(Any, provider)},
            provider_specs={_PROVIDER_ID: _PROVIDER},
            artifacts=artifacts,
            policy=_allow_all(),
        )
        text = invoker({"artifact_id": f"{_RUN_ID}:deliverable.json"}, None)
        assert json.loads(text)["content"] == payload, text

    def test_a_small_result_is_still_retrievable(self) -> None:
        """受判面非空且**尺寸无关**：小于 32 KiB 的结果同样必须可取回。

        若这里红了，说明阈值被改回了「只在超大结果落盘」——那会让桥不可用。
        """
        from packages.application.tool_plane.results import fetch_spilled_result

        artifacts = FakeArtifactStore()
        _write_artifact(artifacts, f"{_RUN_ID}:tiny.json", {"tiny": True})
        provider = CanonicalReadProvider(artifacts)
        record = _call("artifact_read", {"artifact_id": f"{_RUN_ID}:tiny.json"}, artifacts)
        result = provider.execute(_PROVIDER, record)
        assert fetch_spilled_result(artifacts, result) is not None, (
            "小结果也必须落在 ArtifactStore 里 —— 桥靠 fetch_spilled_result 取回内容"
        )


class TestTheDeclaredToolSurfaceMatchesTheBindingTable:
    """工具面 ↔ 出厂绑定表一致（漏一个工具名就是静默的承接缺口）。"""

    def test_list_tools_covers_the_declared_capabilities(self) -> None:
        from services.api.session_tool_support import DEFAULT_SESSION_TOOL_BINDINGS

        artifacts = FakeArtifactStore()
        provider = CanonicalReadProvider(artifacts, FakeEvidenceLedger())
        tools = provider.list_tools(_PROVIDER)
        declared_caps = {capability for tool in tools for capability in tool.capabilities}
        bound_for_this_provider = {
            tool_name
            for tool_name, provider_id, _tool_id in DEFAULT_SESSION_TOOL_BINDINGS
            if provider_id == _PROVIDER_ID
        }
        assert bound_for_this_provider <= declared_caps, (
            "绑定表声明的工具名必须有 provider 侧工具承载（否则该名字永远读不到数据）",
            sorted(bound_for_this_provider - declared_caps),
        )

    def test_an_unknown_tool_id_is_named(self) -> None:
        artifacts = FakeArtifactStore()
        provider = CanonicalReadProvider(artifacts)
        record = _call("artifact_read", {"artifact_id": "x"}, artifacts)
        object.__setattr__(record, "tool_id", "not_a_tool")
        with pytest.raises(InvalidInputError, match="not_a_tool"):
            provider.execute(_PROVIDER, record)
