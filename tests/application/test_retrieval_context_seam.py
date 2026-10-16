"""GOAL-20261014-078 EC-01 判据：**检索内容 → 会话上下文**的接缝可判定。

**被测对象**：`run_orchestration/retrieval_context.build_retrieval_context` —— 把本 run
**系统取得**（`TrustLabel.RETRIEVED`）的检索证据的**内容摘录**汇成 `ContextSnapshot`
（`selected_refs` / `retrieval_digest` / `token_allocation` / `trust_labels`）。

**为什么这条判据是这一格的靶子**（建档实测）：`ContextSnapshot` 在域层早就声明、
`AgentSessionSpec.context_snapshot` 也一直在，但**全仓零构造点**
（`context_snapshot=` 在 `packages/`·`services/` 零命中）⇒ 会话上下文里没有任何检索内容。
本文件把那个槽位的生产者钉死。

**五件事逐条取证**：

1. **逐条 ref 在场**：`selected_refs` 与证据的 `artifact_id` **逐条对应**（不是「非空」了事）；
2. **digest 由内容重算**：`retrieval_digest` 必须等于「按同一份摘录拼出的字节」的 sha256
   —— 判据**独立重算**（不 import 产品的拼接函数），否则实现漂了判据会静默跟随；
3. **上界生效**（§10 有界口径）：超长标题被**截断**，且 `token_allocation` ≤ 摘录长度之和；
4. **空集合点名**：没有检索证据 ⇒ refs 为空**且** `reason` 非空并**点名**（不是静默空）；
   并且**「有证据但读不出内容」与「没有证据」是两句不同的判词**；
5. **只收系统取得**：声明输入（`USER_PROVIDED`）与自产件（`GENERATED`）**不进**上下文。

**离线纪律**：本文件只用 `FakeArtifactStore` + `FakeEvidenceLedger`，**零 HTTP 客户端**
⇒ 它测的是「读出既有事实并装配」，不是网络可达性（真出网那一段由 live 判据承担）。
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.evidence_ledger import FakeEvidenceLedger
from packages.application.run_orchestration.retrieval_context import (
    DEFAULT_MAX_CHARS,
    RetrievalContextView,
    build_retrieval_context,
)
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import ArtifactState, TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)

_RUN = "run-ctx-0001"
_TASK = "task-ctx-0001"
_LONG_TITLE = "T" * (DEFAULT_MAX_CHARS + 50)


def _store_with_tool_result(artifact_id: str, payload: dict[str, Any]) -> FakeArtifactStore:
    """工具结果制品的受控内容（内容寻址：digest 由字节算）。"""
    store = FakeArtifactStore()
    content = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    store.put(
        Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            created_by="tool:literature_read",
        ),
        content,
    )
    store.mark(artifact_id, ArtifactState.VERIFIED)
    return store


def _ledger_with(
    *,
    artifact_id: str,
    trust: TrustLabel,
    source_ref: str,
    run_id: str = _RUN,
) -> FakeEvidenceLedger:
    """一条证据 + 它的来源性质（**性质由 `SourceRecord` 决定**，与覆盖计数同源）。"""
    ledger = FakeEvidenceLedger()
    ledger.register_source(
        SourceRecord(
            origin=source_ref,
            content_digest="sha256:" + "0" * 64,
            trust_label=trust,
            access_time=Timestamp.now(),
        )
    )
    evidence = Evidence(
        id=f"evidence:{artifact_id}",
        source_ref=source_ref,
        content_digest="sha256:" + "0" * 64,
        artifact_id=artifact_id,
        run_id=run_id,
    )
    ledger.register_evidence(evidence)
    claim = Claim(
        id=f"claim:{_TASK}:result",
        statement="assembled from tool evidence",
        status=ClaimStatus.PROPOSED,
        author="system:test",
        evidence_relations=[(evidence.id, EvidenceRelationType.SUPPORTS)],
    )
    ledger.register_claim(claim)
    ledger.attach_relation(
        EvidenceRelation(
            claim_id=claim.id,
            evidence_id=evidence.id,
            relation=EvidenceRelationType.SUPPORTS,
        )
    )
    return ledger


def _retrieved_view(*, title: str = "A real paper title") -> tuple[Any, RetrievalContextView]:
    """一条 `RETRIEVED` 工具证据 + 它的装配结果（两条记录的常见形状）。"""
    artifact_id = f"tool-result:{_TASK}:literature_read:39284801:literature_read"
    payload = {
        "articles": [
            {"pmid": "39284801", "doi": "10.1/x", "title": title},
            {"pmid": "40601758", "doi": "10.1/y", "title": "Second paper"},
        ]
    }
    store = _store_with_tool_result(artifact_id, payload)
    ledger = _ledger_with(
        artifact_id=artifact_id,
        trust=TrustLabel.RETRIEVED,
        source_ref=f"tool:literature_read:{_TASK}",
    )
    return store, build_retrieval_context(store, ledger, _RUN)


class TestTheRefsArePerEntry:
    """① 逐条 ref 在场（不是「非空」了事）。"""

    def test_every_entry_contributes_its_artifact_ref(self) -> None:
        _store, view = _retrieved_view()
        assert view.entries, ("受判面非空：本用例不能空转", view.reason)
        # 逐条断言：每条 entry 的 artifact_id 都在 selected_refs 里。
        for entry in view.entries:
            assert entry.artifact_id in view.snapshot.selected_refs, (entry, view.snapshot)

    def test_the_identifiers_and_titles_are_carried(self) -> None:
        _store, view = _retrieved_view()
        identifiers = {entry.identifier for entry in view.entries}
        assert identifiers == {"39284801", "40601758"}, identifiers
        assert any("Second paper" in entry.shown for entry in view.entries), view.entries

    def test_the_trust_labels_say_system_retrieved(self) -> None:
        _store, view = _retrieved_view()
        assert view.snapshot.trust_labels == ["RETRIEVED"], view.snapshot.trust_labels


class TestTheDigestIsRecomputedFromContent:
    """② digest 由内容**重算**（判据独立重算，不 import 产品的拼接函数）。"""

    def test_the_digest_matches_a_freshly_built_payload(self) -> None:
        _store, view = _retrieved_view()
        payload = {
            "run_id": _RUN,
            "entries": [
                {
                    "identifier": entry.identifier,
                    "evidence_id": entry.evidence_id,
                    "artifact_id": entry.artifact_id,
                    "shown": entry.shown,
                    # GOAL-20261016-081 EC-03：载荷新增这一列（读面必须能读出「被截过」，
                    # 否则提示词那行的 `[truncated]` 标注**重建不出来**）。
                    "truncated": entry.truncated,
                }
                for entry in view.entries
            ],
        }
        expected = Digest.of_bytes(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        )
        assert view.snapshot.retrieval_digest == str(expected), view.snapshot.retrieval_digest

    def test_the_digest_is_deterministic(self) -> None:
        _store, first = _retrieved_view()
        _store2, second = _retrieved_view()
        assert first.snapshot.retrieval_digest == second.snapshot.retrieval_digest


class TestTheBoundsActuallyApply:
    """③ §10 的有界口径：超长内容被截断，且额度不超摘录长度之和。"""

    def test_a_long_title_is_clipped_and_named(self) -> None:
        _store, view = _retrieved_view(title=_LONG_TITLE)
        clipped = [entry for entry in view.entries if entry.truncated]
        assert clipped, ("超长标题必须被截断并点名", view.entries)
        for entry in clipped:
            assert len(entry.shown) == DEFAULT_MAX_CHARS, len(entry.shown)
            assert entry.title == _LONG_TITLE, "原文保留在 `title` 里（可判「截了多少」）"

    def test_the_token_allocation_is_bounded_by_the_excerpt(self) -> None:
        _store, view = _retrieved_view(title=_LONG_TITLE)
        ceiling = sum(len(entry.shown) for entry in view.entries)
        assert 0 < view.snapshot.token_allocation <= ceiling, (
            view.snapshot.token_allocation,
            ceiling,
        )

    def test_the_item_count_is_bounded(self) -> None:
        artifact_id = f"tool-result:{_TASK}:literature_search:q:literature_search"
        payload = {"articles": [{"pmid": f"4000000{i}", "title": f"paper {i}"} for i in range(50)]}
        store = _store_with_tool_result(artifact_id, payload)
        ledger = _ledger_with(
            artifact_id=artifact_id,
            trust=TrustLabel.RETRIEVED,
            source_ref=f"tool:literature_search:{_TASK}",
        )
        view = build_retrieval_context(store, ledger, _RUN, max_items=5)
        assert len(view.entries) == 5, len(view.entries)
        assert len(view.snapshot.selected_refs) == 5, view.snapshot.selected_refs


class TestTheEmptySetIsNamed:
    """④ 空集合**点名**；且「没有证据」与「读不出内容」是**两句**判词。"""

    def test_no_evidence_gives_an_empty_context_with_a_reason(self) -> None:
        store = FakeArtifactStore()
        ledger = FakeEvidenceLedger()
        view = build_retrieval_context(store, ledger, _RUN)
        assert view.snapshot.selected_refs == []
        assert view.snapshot.retrieval_digest is None
        assert view.snapshot.token_allocation == 0
        assert view.reason and "no retrieved evidence" in view.reason, view.reason

    def test_evidence_without_readable_content_says_so_differently(self) -> None:
        """**两件事必须分得开**：没有检索证据 vs 有证据但内容读不出来。"""
        missing = "tool-result:task-x:op:literature_read"
        store = FakeArtifactStore()  # 制品**不在场**
        ledger = _ledger_with(
            artifact_id=missing,
            trust=TrustLabel.RETRIEVED,
            source_ref="tool:literature_read:task-x",
        )
        view = build_retrieval_context(store, ledger, _RUN)
        assert view.snapshot.selected_refs == []
        assert view.reason and "retrieved evidence record(s)" in view.reason, view.reason
        assert "no retrieved evidence" not in view.reason, (
            "「读不出内容」不得被读成「没有证据」",
            view.reason,
        )


class TestOnlySystemRetrievedSourcesEnter:
    """⑤ 只收系统取得：声明输入与自产件不进上下文（与覆盖计数同源的性质口径）。"""

    def _view_for(self, trust: TrustLabel) -> RetrievalContextView:
        artifact_id = f"tool-result:{_TASK}:literature_search:q:literature_search"
        store = _store_with_tool_result(
            artifact_id, {"articles": [{"pmid": "39284801", "title": "t"}]}
        )
        ledger = _ledger_with(
            artifact_id=artifact_id, trust=trust, source_ref=f"tool:literature_search:{_TASK}"
        )
        return build_retrieval_context(store, ledger, _RUN)

    def test_a_user_provided_source_does_not_enter(self) -> None:
        view = self._view_for(TrustLabel.USER_PROVIDED)
        assert view.snapshot.selected_refs == [], view.snapshot.selected_refs
        assert view.reason and "no retrieved evidence" in view.reason, view.reason

    def test_a_generated_source_does_not_enter(self) -> None:
        view = self._view_for(TrustLabel.GENERATED)
        assert view.snapshot.selected_refs == [], view.snapshot.selected_refs


#: 另一个 run 的工具结果制品与它的 run 标识（跨 run 隔离用例的「别人」）。
_OTHER_ARTIFACT = "tool-result:task-other:literature_search:q:literature_search"
_OTHER_RUN = "run-ctx-0002"


def _two_run_store(mine: str, theirs: str) -> FakeArtifactStore:
    """同一个库里放**两个 run** 的工具结果（隔离用例的夹具；单列以守住函数长度门）。"""
    store = _store_with_tool_result(mine, {"articles": [{"pmid": "39284801", "title": "mine"}]})
    content = json.dumps(
        {"articles": [{"pmid": "99999999", "title": "theirs"}]},
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    store.put(
        Artifact(
            id=theirs,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            created_by="tool:literature_search",
        ),
        content,
    )
    store.mark(theirs, ArtifactState.VERIFIED)
    return store


class TestTheRunFilterBites:
    """**跨 run 的隔离**：别的 run 的检索证据不得进本 run 的上下文。

    为什么单列：**按压实测**（GOAL-078 cycle 2）—— 把 `_retrieved_evidence` 的
    `run_id` 过滤去掉时，e2e 的射程判据**没有变红**（那个夹具里只有一个 run ⇒
    「按 run 过滤」这条性质**根本没被覆盖**）。本条把它补上：两个 run 的证据同时在库。
    """

    def _two_run_ledger_and_store(self) -> tuple[Any, Any]:
        mine = f"tool-result:{_TASK}:literature_search:q:literature_search"
        theirs = _OTHER_ARTIFACT
        store = _two_run_store(mine, theirs)
        ledger = _ledger_with(
            artifact_id=mine,
            trust=TrustLabel.RETRIEVED,
            source_ref=f"tool:literature_search:{_TASK}",
        )
        ledger = _ledger_with(
            artifact_id=mine,
            trust=TrustLabel.RETRIEVED,
            source_ref=f"tool:literature_search:{_TASK}",
        )
        ledger.register_source(
            SourceRecord(
                origin="tool:literature_search:task-other",
                content_digest="sha256:" + "0" * 64,
                trust_label=TrustLabel.RETRIEVED,
                access_time=Timestamp.now(),
            )
        )
        other_evidence = Evidence(
            id=f"evidence:{theirs}",
            source_ref="tool:literature_search:task-other",
            content_digest="sha256:" + "0" * 64,
            artifact_id=theirs,
            run_id=_OTHER_RUN,
        )
        ledger.register_evidence(other_evidence)
        other_claim = Claim(
            id="claim:task-other:result",
            statement="other run",
            status=ClaimStatus.PROPOSED,
            author="system:test",
            evidence_relations=[(other_evidence.id, EvidenceRelationType.SUPPORTS)],
        )
        ledger.register_claim(other_claim)
        ledger.attach_relation(
            EvidenceRelation(
                claim_id=other_claim.id,
                evidence_id=other_evidence.id,
                relation=EvidenceRelationType.SUPPORTS,
            )
        )
        return store, ledger

    def test_another_runs_evidence_does_not_enter(self) -> None:
        store, ledger = self._two_run_ledger_and_store()
        view = build_retrieval_context(store, ledger, _RUN)
        assert view.entries, ("本 run 的证据必须仍然进上下文（否则本用例空转）", view.reason)
        identifiers = {entry.identifier for entry in view.entries}
        assert identifiers == {"39284801"}, (
            "别的 run 的证据不得进本 run 的上下文",
            identifiers,
        )


class TestAToolResultWithoutTheRetrievedLabelDoesNotEnter:
    """**性质与命名是两件事**：`tool-result:` 前缀只说明「谁产出的」，不说明「系统取得」。

    为什么单列：**按压实测**（GOAL-078 cycle 2）—— 把性质判据改成恒真时 e2e **没有变红**
    （那个协议的声明输入不带 `tool-result:` 前缀 ⇒ 被前缀过滤先挡住了）。但**真实现里**
    「带 `tool-result:` 前缀而性质不是 `RETRIEVED`」是存在的：canonical 读面 provider
    （`m12_artifact`）的工具结果就是这一形态（它不声明 `network_domains` ⇒ `GENERATED`）。
    """

    def _view_for(self, trust: TrustLabel) -> RetrievalContextView:
        """同一条**可读**的工具结果（`ids` 形状），只改**性质**标签。

        为什么用 `ids` 形状：本用例的靶子是**性质分派**，不是「内容形状」——
        两者混在一个夹具里会让「性质判据坏了」与「形状没认出来」给出同一条红。
        「形状不认识就不进」另有一条（见 `_records_of` 的覆盖）。
        """
        artifact_id = f"tool-result:{_TASK}:tool_bridge:q:artifact_read"
        store = _store_with_tool_result(artifact_id, {"ids": ["artifact:some-id"]})
        ledger = _ledger_with(
            artifact_id=artifact_id, trust=trust, source_ref=f"tool:tool_bridge:{_TASK}"
        )
        return build_retrieval_context(store, ledger, _RUN)

    def test_a_generated_tool_result_does_not_enter(self) -> None:
        view = self._view_for(TrustLabel.GENERATED)
        assert view.snapshot.selected_refs == [], (
            "本地计算/读取（`GENERATED`）不得冒充「系统取得」——即使它的制品前缀是 `tool-result:`",
            view.snapshot.selected_refs,
        )
        assert view.reason and "no retrieved evidence" in view.reason, view.reason

    def test_a_retrieved_tool_result_still_enters(self) -> None:
        """正向对照：同一条路径、只把性质换成 `RETRIEVED` ⇒ 进上下文（否则上一条可能空转）。"""
        view = self._view_for(TrustLabel.RETRIEVED)
        assert view.snapshot.selected_refs == [
            f"tool-result:{_TASK}:tool_bridge:q:artifact_read"
        ], (view.snapshot.selected_refs, view.reason)


def test_the_seam_is_zero_egress_by_construction() -> None:
    """**零出网的构造性证据**：本模块的源码里没有任何网络/HTTP 记号。

    它比「跑的时候没出网」更强：代码里**没有能力**出网（判据按 AST 取属性名，
    不靠文本子串 —— 子串会被 docstring 里的说明命中）。
    """
    import ast
    from pathlib import Path

    source = Path("packages/application/run_orchestration/retrieval_context.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    # 只判**传输层**的名字（不把 `dict.get` 这类同名方法算进来 —— 那会误报；
    # 承 MEM: 判据不许用会误伤的词表）。
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    forbidden = {
        "urlopen",
        "socket",
        "connect",
        "Client",
        "Session",
        "request",
        "urlencode",
    }
    offenders = sorted(forbidden & (names | attributes))
    assert offenders == [], ("本模块不得有任何出网能力", offenders)
    # 它也不得 import 任何网络库（按 AST 的 import 节点判）。
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not ({"httpx", "requests", "socket", "urllib"} & imported), imported
    assert hashlib.sha256(b"x").hexdigest()  # 判据自身的 sha 依赖被真实使用
