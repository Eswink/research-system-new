"""GOAL-029 EC-01 判据：canonical 读面**真去读**（A 组承接面的可执行证据）。

**被测对象**：`adapters/canonical/read_provider.py` 的 `CanonicalReadProvider` —— 把
canonical state（`ArtifactStore` / `EvidenceLedger`）接成**可执行**的 ToolProvider。
建档轮实测的事实是：`tool_providers.yaml` 声明的两件 NATIVE provider
（`m12_artifact` / `openhands_workspace`）**全仓没有实现**（只有 Fake 与两个 REST adapter），
所以「声明了能力」与「有可执行的承接面」在出厂配置下是两件事。

**四件事逐条取证**（不读「调用成功」这类弱信号）：

1. **真读出内容**：`artifact.read` 返回的 `content` 与写进去的**逐字相等**（digest 重算相等）；
2. **未知 id 点名拒绝**：不存在的 artifact ⇒ `InvalidInputError` 点名该 id（**不**返回空壳
   冒充"查到了但没内容"）；
3. **`evidence.read` 按 relation 投影**（承 `MEM: evidence-read-face-claim-relation`）：
   只 `register_evidence` **不** `attach_relation` ⇒ **读不到**；`attach_relation` 后 ⇒ 读得到；
4. **`workspace.read` 只报本 run 的制品**（run 隔离：别的 run 的 id 不出现）。

**受判面非空**（MEM-156）：本文件先断言夹具里真的写了东西（否则「读到了」可能是读的空集）。
"""

from __future__ import annotations

import json
from typing import Any, cast

import pytest

from adapters.canonical import CanonicalReadProvider
from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger
from packages.application.ports.errors import InvalidInputError
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import EffectClass, ProviderType, ToolCallStatus, TrustLevel
from packages.domain.evidence import (
    Claim,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)
from packages.domain.tools import ToolCallRecord, ToolProviderSpec

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

_PROVIDER_ID = "m12_artifact"
_RUN_ID = "run-goal029-probe"

#: 出厂形态（与 `examples/config/tool_providers.yaml` 的 m12_artifact 声明同源字面量）。
_PROVIDER = ToolProviderSpec(
    id=_PROVIDER_ID,
    kind=ProviderType.NATIVE,
    trust_level=TrustLevel.BUILT_IN,
    # GOAL-029 EC-01（cycle 2）：承接面扩到五条 A 组读能力
    # （budget.read / deliverable.read 由 `CanonicalReadProvider` 的
    # `budget_read` / `deliverable_read` 承载）。
    capabilities=[
        "artifact.read",
        "claim.read",
        "evidence.read",
        "workspace.read",
        "budget.read",
        "deliverable.read",
    ],
    effect_class=EffectClass.READ_ONLY,
)


def _call(
    tool_id: str, arguments: dict[str, object], artifacts: FakeArtifactStore
) -> ToolCallRecord:
    """把参数经 `tool-args` 制品交给 provider（与运行链 / REST / MCP 同一口径）。"""
    content = json.dumps(arguments, ensure_ascii=False, sort_keys=True).encode("utf-8")
    task_id = "task-goal029"
    operation_key = f"probe:{tool_id}"
    artifact_id = f"tool-args:{task_id}:{operation_key}"
    artifacts.put(
        Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            created_by="probe",
            source_refs=[f"task:{task_id}"],
            classification="tool-args",
        ),
        content,
    )
    return ToolCallRecord(
        task_id=task_id,
        attempt=1,
        operation_key=operation_key,
        tool_id=tool_id,
        capability={
            "artifact_read": "artifact.read",
            "claim_read": "claim.read",
            "evidence_read": "evidence.read",
            "workspace_read": "workspace.read",
            "budget_read": "budget.read",
            "deliverable_read": "deliverable.read",
        }[tool_id],
        argument_digest=Digest.of_bytes(content),
        status=ToolCallStatus.REQUESTED,
        recorded_at=Timestamp.now(),
    )


def _spilled_content(artifacts: FakeArtifactStore, record: object) -> object:
    """把 provider 的结果从 ArtifactStore 读回来（spill 语义与运行链一致）。"""
    from packages.application.tool_plane.results import fetch_spilled_result

    raw = fetch_spilled_result(artifacts, record)  # type: ignore[arg-type]
    assert raw is not None, "provider 必须把结果 spill 到 ArtifactStore（TOOL_RUNTIME §7）"
    return json.loads(raw.decode("utf-8"))


def _allow_all() -> Any:
    """全放行的求值器（本文件的受判对象是读面数据，不是策略面；策略面另有判据）。"""
    from packages.application.ports.policy_evaluator import PolicyEvaluation
    from packages.domain.enums import PolicyDecision

    class _Allow:
        def evaluate(self, request: Any) -> PolicyEvaluation:
            return PolicyEvaluation(PolicyDecision.ALLOW, reason="probe allow-all")

    return _Allow()


def _write_artifact(artifacts: FakeArtifactStore, artifact_id: str, payload: object) -> bytes:
    content = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    artifacts.put(
        Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            created_by="probe",
            source_refs=[f"run:{_RUN_ID}"],
            classification="research_deliverable",
        ),
        content,
    )
    return content


class TestArtifactReadReallyReads:
    """① 真读出内容 + ② 未知 id 点名拒绝。"""

    def test_the_content_round_trips_byte_for_byte(self) -> None:
        artifacts = FakeArtifactStore()
        payload = {"claim": "probe", "value": 42, "nested": {"text": "中文"}}
        content = _write_artifact(artifacts, f"{_RUN_ID}:deliverable.json", payload)
        provider = CanonicalReadProvider(artifacts)

        record = _call("artifact_read", {"artifact_id": f"{_RUN_ID}:deliverable.json"}, artifacts)
        result = provider.execute(_PROVIDER, record)
        read_back = _spilled_content(artifacts, result)

        assert isinstance(read_back, dict), read_back
        assert read_back["artifact_id"] == f"{_RUN_ID}:deliverable.json"
        assert read_back["content"] == payload, "读回的 content 必须与写入的 payload 相等"
        assert read_back["digest"] == str(Digest.of_bytes(content)), "digest 必须重算相等"
        assert read_back["size_bytes"] == len(content)

    def test_an_unknown_artifact_is_named_not_faked(self) -> None:
        """没有这个 artifact ⇒ 点名拒绝；**不得**返回空壳冒充「查到了但没内容」。"""
        artifacts = FakeArtifactStore()
        provider = CanonicalReadProvider(artifacts)
        record = _call("artifact_read", {"artifact_id": "does-not-exist"}, artifacts)
        with pytest.raises(InvalidInputError, match="does-not-exist"):
            provider.execute(_PROVIDER, record)

    def test_a_missing_argument_is_refused(self) -> None:
        artifacts = FakeArtifactStore()
        provider = CanonicalReadProvider(artifacts)
        record = _call("artifact_read", {}, artifacts)
        with pytest.raises(InvalidInputError, match="artifact_id"):
            provider.execute(_PROVIDER, record)


class TestEvidenceReadFollowsRelations:
    """③ 读面按 relation 投影：只 register 不 attach_relation ⇒ **读不到**。"""

    def _ledger_with(self, *, attach: bool) -> FakeEvidenceLedger:
        ledger = FakeEvidenceLedger()
        ledger.register_source(
            SourceRecord(origin="probe:source", content_digest="sha256:" + "a" * 64)
        )
        ledger.register_evidence(
            Evidence(
                id="ev-goal029",
                source_ref="probe:source",
                content_digest="sha256:" + "b" * 64,
                run_id=_RUN_ID,
            )
        )
        ledger.register_claim(Claim(id="claim-goal029", statement="probe claim"))
        if attach:
            ledger.attach_relation(
                EvidenceRelation(
                    claim_id="claim-goal029",
                    evidence_id="ev-goal029",
                    relation=EvidenceRelationType.SUPPORTS,
                )
            )
        return ledger

    def test_registered_but_unrelated_evidence_is_invisible(self) -> None:
        """承 `MEM: evidence-read-face-claim-relation`：登记 ≠ 可见。"""
        artifacts = FakeArtifactStore()
        ledger = self._ledger_with(attach=False)
        provider = CanonicalReadProvider(artifacts, ledger)
        record = _call("evidence_read", {"run_id": _RUN_ID}, artifacts)

        payload = _spilled_content(artifacts, provider.execute(_PROVIDER, record))
        assert isinstance(payload, dict), payload
        assert payload["claims"] == [], (
            "只 register_evidence 不 attach_relation ⇒ 读面必须看不到它（claim 侧也空）"
        )
        assert payload["evidence"] == [], payload["evidence"]

    def test_attached_relations_become_visible(self) -> None:
        """接上 relation 后同一次读就能看到 —— 与上一条是**同一份夹具**的两种状态。"""
        artifacts = FakeArtifactStore()
        ledger = self._ledger_with(attach=True)
        provider = CanonicalReadProvider(artifacts, ledger)
        record = _call("evidence_read", {"run_id": _RUN_ID}, artifacts)

        payload = _spilled_content(artifacts, provider.execute(_PROVIDER, record))
        assert isinstance(payload, dict), payload
        assert [item["id"] for item in payload["evidence"]] == ["ev-goal029"], payload
        assert payload["claims"][0]["id"] == "claim-goal029", payload
        assert payload["claims"][0]["evidence_ids"] == ["ev-goal029"], payload
        assert payload["evidence"][0]["content_digest"] == "sha256:" + "b" * 64, payload

    def test_another_runs_evidence_does_not_leak(self) -> None:
        """run 隔离：别的 run 的证据不出现在本次读面里。"""
        artifacts = FakeArtifactStore()
        ledger = FakeEvidenceLedger()
        ledger.register_source(
            SourceRecord(origin="probe:other", content_digest="sha256:" + "c" * 64)
        )
        ledger.register_evidence(
            Evidence(
                id="ev-other",
                source_ref="probe:other",
                content_digest="sha256:" + "d" * 64,
                run_id="some-other-run",
            )
        )
        ledger.register_claim(Claim(id="claim-other", statement="other"))
        ledger.attach_relation(
            EvidenceRelation(
                claim_id="claim-other",
                evidence_id="ev-other",
                relation=EvidenceRelationType.SUPPORTS,
            )
        )
        provider = CanonicalReadProvider(artifacts, ledger)
        record = _call("evidence_read", {"run_id": _RUN_ID}, artifacts)

        raw = _spilled_content(artifacts, provider.execute(_PROVIDER, record))
        assert isinstance(raw, dict), raw
        assert raw["claims"] == [] and raw["evidence"] == [], raw

    def test_without_a_ledger_the_tool_is_named_unavailable(self) -> None:
        """装配缺 ledger ⇒ 点名拒绝（不静默返回空集冒充"没有证据"）。"""
        artifacts = FakeArtifactStore()
        provider = CanonicalReadProvider(artifacts, None)
        record = _call("evidence_read", {"run_id": _RUN_ID}, artifacts)
        with pytest.raises(InvalidInputError, match="EvidenceLedger"):
            provider.execute(_PROVIDER, record)

        health = provider.check_health(_PROVIDER)
        assert health.detail.startswith("evidence_read unavailable"), health.detail


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
