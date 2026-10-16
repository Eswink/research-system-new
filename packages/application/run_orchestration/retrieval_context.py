"""检索内容 → **会话上下文**的装配（GOAL-20261014-078 EC-01；阶梯「检索」域 L1 → L2）。

**它补哪一环**：`ContextSnapshot`（`selected_refs` / `retrieval_digest` /
`token_allocation` / `trust_labels`）在域层**早就声明**，`AgentSessionSpec.context_snapshot`
也一直在 —— 但**建档实测：全仓零构造点**（`context_snapshot=` 在 `packages/`·`services/`
零命中）⇒ 会话上下文里**没有任何检索内容**，模型读不到上游取回的文献
（GOAL-077 只把它做进了**报告**）。本模块就是这个槽位的**生产者**。

**四条边界**（本模块不越界）：

1. **只读 canonical，零出网**：来源只有 `EvidenceLedger` 的证据与 `ArtifactStore` 里
   `tool-result:` 命名的制品 —— 本模块**不调用任何工具**、不构造 URL、不碰 socket；
2. **只收系统取得**：来源性质由 `SourceRecord.trust_label` 判（与
   `count_retrieved_sources` **同一处口径**）—— 声明输入（`USER_PROVIDED`）与
   自产件（`GENERATED`）**不算**检索内容；
3. **内容有界**（AGENTS.md §10）：进上下文的是**文本摘录**（逐条截断 + 条数上限），
   超限**点名**（`truncated`），**不**把原始字节或完整正文塞进会话；
4. **空集合点名**：没有检索证据时 `selected_refs` 为空 —— 这**不是**失败
   （多数协议没有检索），但必须有**可读的理由**，不静默空。

**求值点**（为什么由 `phase_runner` 在**每个任务开始前**调）：上游 phase 的检索证据是
**逐步落库**的 —— 下游 phase 开始时会话上下文里应当含**它开始时已经取回**的全部内容。
放在 plan 期（run 开始时算一次）只会拿到第一轮的内容，那正是本 GOAL 要消灭的
「模型读不到」。

**确定性**：同一份持久状态 ⇒ 同一个 `ContextSnapshot`（摘录按证据 id 排序后拼，
digest 由**拼出来的字节**算）—— 与报告汇编器同一条纪律。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.domain.core import Digest
from packages.domain.enums import TrustLabel
from packages.domain.evidence import Evidence
from packages.domain.memory import ContextSnapshot

#: 逐条摘录的**字符**上限（§10 的有界口径：内容进上下文但不进完整正文）。
DEFAULT_MAX_CHARS = 240
#: 最多几条进上下文（条数上限同样是 §10 的一部分）。
DEFAULT_MAX_ITEMS = 12
#: 只认工具结果的制品前缀（与 `tool_evidence._spilled_artifact_id` 同源）。
_TOOL_RESULT_PREFIX = "tool-result:"
#: 上下文制品的 `created_by`（编排层写的**装配事实**，不是任何 agent 的产出）。
_CONTEXT_CREATOR = "system:retrieval-context"


@dataclass(frozen=True, slots=True)
class RetrievalEntry:
    """进上下文的一条检索内容（**摘录**，不是原始字节）。"""

    evidence_id: str
    artifact_id: str
    identifier: str
    title: str
    shown: str
    #: 本条被截断过（`shown` 比原文短）—— 超限**点名**，不静默丢。
    truncated: bool


@dataclass(frozen=True, slots=True)
class RetrievalContextView:
    """装配结果：快照 + 逐条读数 + **空集合的理由**（可判事实）。"""

    snapshot: ContextSnapshot
    entries: tuple[RetrievalEntry, ...]
    #: 本次装配的 run 标识（EC-03 的读面载荷要它 —— 读面必须能回答「哪个 run 的上下文」）。
    run_id: str = ""
    #: 空集合时的**点名**理由（非空集合时为 `None`）。
    reason: str | None = None


def build_retrieval_context(
    artifacts: ArtifactStore,
    ledger: EvidenceLedger,
    run_id: str,
    *,
    max_items: int = DEFAULT_MAX_ITEMS,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> RetrievalContextView:
    """本 run 的检索证据 → `ContextSnapshot`（只读 canonical；零出网）。"""
    if max_items < 1:
        raise ValueError("max_items must be >= 1")
    if max_chars < 1:
        raise ValueError("max_chars must be >= 1")
    retrieved = _retrieved_evidence(ledger, run_id)
    if not retrieved:
        return _empty(run_id)
    entries = tuple(
        entry
        for evidence in retrieved
        for entry in _entries_for(artifacts, evidence, max_chars=max_chars)
    )[:max_items]
    if not entries:
        # 有检索证据、但**读不出内容**（`tool-result` 制品不在场 / 不是 JSON 对象）——
        # 与「没有检索证据」是**两件事**，判词必须分开（否则「读不到」会被读成「没有」）。
        return _empty(
            run_id,
            reason=(
                f"run {run_id} has {len(retrieved)} retrieved evidence record(s) but none of "
                "their artifacts yields readable content"
            ),
        )
    return RetrievalContextView(
        snapshot=_snapshot(run_id, entries),
        entries=entries,
        run_id=run_id,
    )


def _empty(run_id: str, *, reason: str | None = None) -> RetrievalContextView:
    """空上下文（**点名**理由；空集合不是静默）。"""
    return RetrievalContextView(
        snapshot=ContextSnapshot(
            selected_refs=[],
            retrieval_digest=None,
            token_allocation=0,
            trust_labels=[],
        ),
        entries=(),
        run_id=run_id,
        reason=reason or f"run {run_id} has no retrieved evidence to place in the context",
    )


def context_payload(run_id: str, entries: tuple[RetrievalEntry, ...]) -> dict[str, object]:
    """上下文的**载荷**（唯一构造点）。

    GOAL-20261014-078 EC-03：读面写出的**就是这些字节** —— 因此
    `ArtifactStore` 里那份制品的 digest 与 `ContextSnapshot.retrieval_digest`
    **同源**（同一份字节算两次必然相等），读面值与装配点的值不可能分叉。

    **GOAL-20261016-081 EC-03 补一列 `truncated`**（实测缺口）：提示词那一段会把被截的
    条目**标注**出来（`[truncated]`），而载荷原本**不记**`truncated` ⇒ 读者拿读面**重建不出**
    「模型看到的到底是哪一行」（对未截条目无碍，对被截条目必然对不上）。⇒ 加这一列，
    使「模型拿到了什么」**逐字**可复核（少这一列时，那条判据只在**无截断**的夹具里假绿）。
    """
    return {
        "run_id": run_id,
        "entries": [
            {
                "identifier": entry.identifier,
                "evidence_id": entry.evidence_id,
                "artifact_id": entry.artifact_id,
                "shown": entry.shown,
                "truncated": entry.truncated,
            }
            for entry in entries
        ],
    }


def payload_bytes(payload: dict[str, object]) -> bytes:
    """载荷 → 规范字节（**唯一**编码点；`retrieval_digest` 与写盘的字节都来自它）。"""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")


def _snapshot(run_id: str, entries: tuple[RetrievalEntry, ...]) -> ContextSnapshot:
    """逐条摘录 → `ContextSnapshot`（`retrieval_digest` 由**拼出来的字节**算）。"""
    raw = payload_bytes(context_payload(run_id, entries))
    return ContextSnapshot(
        selected_refs=[entry.artifact_id for entry in entries],
        retrieval_digest=str(Digest.of_bytes(raw)),
        # token 估算：本模块**不**引 tokenizer（那会是新依赖）⇒ 用字符数的**上界近似**
        # （一个字符最多一个 token 的量级）；字段语义是「为这份上下文预留的额度」，
        # 判据断言它**不超过**由摘录长度算出的上界（见判据文件）。
        token_allocation=sum(len(entry.shown) for entry in entries),
        trust_labels=sorted({TrustLabel.RETRIEVED.value for _ in entries}),
    )


def _retrieved_evidence(ledger: EvidenceLedger, run_id: str) -> tuple[Evidence, ...]:
    """本 run 的**系统取得**证据（性质由 `SourceRecord.trust_label` 判；与覆盖计数同源）。

    只经 claim→relation 投影走（与 `GET /runs/{id}/evidence` 同一口径）：只登记不挂关系的
    证据读不到 —— 既有语义，本处不另开一条。
    """
    found: list[Evidence] = []
    seen: set[str] = set()
    for claim in ledger.claims():
        for relation in ledger.relations_for_claim(claim.id):
            evidence_id = relation.evidence_id
            if evidence_id in seen:
                continue
            seen.add(evidence_id)
            try:
                item = ledger.get_evidence(evidence_id)
            except Exception:  # noqa: BLE001 - 引用可能已删除（视觉态：missing evidence）
                continue
            if item.run_id != run_id or not item.artifact_id:
                continue
            if not str(item.artifact_id).startswith(_TOOL_RESULT_PREFIX):
                continue
            if not _is_retrieved(ledger, item):
                continue
            found.append(item)
    return tuple(sorted(found, key=lambda item: item.id))


def _is_retrieved(ledger: EvidenceLedger, evidence: Evidence) -> bool:
    """该证据的来源**性质**是否「系统取得」（声明输入与自产件都不算）。"""
    if not ledger.has_source(evidence.source_ref):
        return False
    return ledger.get_source(evidence.source_ref).trust_label is TrustLabel.RETRIEVED


def _entries_for(
    artifacts: ArtifactStore, evidence: Evidence, *, max_chars: int
) -> tuple[RetrievalEntry, ...]:
    """一条工具证据 → 它的制品内容里的逐条记录（读不到 ⇒ 空，不编造）。"""
    assert evidence.artifact_id is not None
    payload = _json_object(artifacts, evidence.artifact_id)
    if payload is None:
        return ()
    records = _records_of(payload)
    entries: list[RetrievalEntry] = []
    for identifier, title in records:
        shown, truncated = _clip(title, max_chars)
        entries.append(
            RetrievalEntry(
                evidence_id=evidence.id,
                artifact_id=evidence.artifact_id,
                identifier=identifier,
                title=title,
                shown=shown,
                truncated=truncated,
            )
        )
    return tuple(entries)


def _records_of(payload: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    """工具结果内容 → `(标识, 标题)` 序列（两种既有形状都认）。"""
    articles = payload.get("articles")
    if isinstance(articles, list):
        pairs = [
            (_identifier_of(article), str(article.get("title") or ""))
            for article in articles
            if isinstance(article, Mapping)
        ]
        return tuple((identifier, title) for identifier, title in pairs if identifier)
    ids = payload.get("ids")
    if isinstance(ids, list):
        return tuple((str(item), "") for item in ids if str(item))
    return ()


def _identifier_of(article: Mapping[str, Any]) -> str:
    """单条记录的主标识（PMID 优先、退化到 DOI；都缺 ⇒ 空串）。"""
    for key in ("pmid", "doi"):
        value = article.get(key)
        if value:
            return str(value)
    return ""


def _clip(text: str, max_chars: int) -> tuple[str, bool]:
    """有界摘录：超限即截断并**点名**（`truncated=True`）。"""
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars], True


def _json_object(artifacts: ArtifactStore, artifact_id: str) -> Mapping[str, Any] | None:
    """制品内容 → JSON 对象（不在场 / 非 JSON / 非对象 ⇒ `None`，由调用方如实处置）。"""
    if artifacts.meta(artifact_id) is None:
        return None
    try:
        parsed: Any = json.loads(artifacts.get(artifact_id).decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    return parsed if isinstance(parsed, Mapping) else None


def with_retrieval_context(deps: Any, task: Any, spec_context: Any) -> Any:
    """把**此刻已取回**的检索内容装进本任务的 spec（GOAL-20261014-078 EC-01）。

    未接装配器（`deps.retrieval_context is None`）⇒ **原样返回**（既有语义逐字节不变）。
    接了 ⇒ 调装配器并把结果放进 spec；装配器**抛错** ⇒ 让异常冒到执行循环
    （那里的失败路径会**点名** —— 不静默给一个空上下文：那会让「读不到」与「没有」
    不可区分，正是本 GOAL 要消灭的那种含混）。

    EC-03：会话任务的上下文**同时落成制品**（可读面见 `persist_retrieval_context`）。
    """
    build = getattr(deps, "retrieval_context", None)
    if build is None:
        return spec_context
    from dataclasses import replace

    view = build(str(task.run_id.value))
    _persist_for_session_task(deps, task, view)
    return replace(spec_context, retrieval_context=view)


def context_artifact_id(task_id: str) -> str:
    """上下文制品的 id（**task 前缀** ⇒ 它天然落在 `GET /runs/{id}/artifacts` 上）。"""
    return f"{task_id}:retrieval_context"


def _persist_for_session_task(deps: Any, task: Any, view: "RetrievalContextView") -> None:
    """会话任务的上下文 → 制品（EC-03 的读面；**只对会建会话的任务**做）。

    为什么只对会话任务：`context_snapshot` 的去处就是**会话**。实验 / 报告格不建会话
    ⇒ 为它们写一件「进了什么上下文」的制品会**答非所问**（那两格没有「进去」这回事）。

    **缺 store / 缺 task id ⇒ 不做**（装配方没接 ⇒ 读面**如实**为空，不伪造）。
    """
    artifacts = getattr(deps, "artifacts", None)
    contract = getattr(task, "contract", None)
    if artifacts is None or task is None:
        return
    from packages.domain.tasks import TaskContract

    if isinstance(contract, TaskContract) and (
        contract.experiment is not None or contract.report is not None
    ):
        return
    persist_retrieval_context(artifacts, task.id.value, view)


def persist_retrieval_context(artifacts: Any, task_id: str, view: "RetrievalContextView") -> str:
    """上下文载荷 → 内容寻址制品（**写出的字节 = digest 的源**）。返回制品 id。

    空集合也写（理由在载荷里）—— 「没有内容进去」本身是**要读得出来的事实**，
    而不是「读面缺一条」。
    """
    from packages.domain.artifacts import Artifact
    from packages.domain.enums import ArtifactState

    content = payload_bytes(_payload_for(view))
    artifact_id = context_artifact_id(task_id)
    artifact = Artifact(
        id=artifact_id,
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type="application/json",
        created_by=_CONTEXT_CREATOR,
        source_refs=[f"task:{task_id}"],
        classification="retrieval_context",
    )
    artifacts.put(artifact, content)
    artifacts.mark(artifact_id, ArtifactState.VERIFIED)
    return artifact_id


def _payload_for(view: "RetrievalContextView") -> dict[str, object]:
    """视图 → 写盘载荷（非空 ⇒ 与 `retrieval_digest` **同一份字节**的源；空 ⇒ 带理由）。"""
    payload = context_payload(view.run_id, view.entries)
    if not view.entries and view.reason:
        payload["reason"] = view.reason
    return payload


__all__ = [
    "DEFAULT_MAX_CHARS",
    "DEFAULT_MAX_ITEMS",
    "RetrievalContextView",
    "RetrievalEntry",
    "build_retrieval_context",
    "with_retrieval_context",
]
