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
from typing import Any

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
        "experiment.read",
        "experiment_plan.read",
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
            "experiment_read": "experiment.read",
            "experiment_plan_read": "experiment_plan.read",
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
