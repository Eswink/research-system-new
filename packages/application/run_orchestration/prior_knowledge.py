"""前序知识 → **会话上下文**的装配（GOAL-20261018-082 EC-01；阶梯「迭代」域）。

**它补哪一格**：记忆在 M10 起就能写（`MemoryWriteProposal → gate → commit`）、`memory.read`
也能读 —— 但**建档实测**：`examples/protocols/*.yaml`（23 份）与全部合约里
`required_capabilities` 出现 `memory.read` 的 **0 份**，且提示词装配面
（`session_resolution` / `session_carry` / `retrieval_context`）对 `memory` 的提及为
**0 / 0 / 1（仅类型）** ⇒ **即便记忆在库，也没有消费者把它写成提示词**。
本模块就是这个槽位的生产者（与 `retrieval_context` 对 `ContextSnapshot` 的关系**同形**）。

**五条边界**（本模块不越界）：

1. **只读 canonical、零出网**：来源只有 `MemoryStore.query(...)` —— 不建会话、不发请求；
2. **只收跨 run 的档位**：`PROJECT` / `ORGANIZATION`。`RUN` 档是**本 run 内**的东西，
   不构成「前序知识」（`SESSION` 更不是）；
3. **只收仍有效的记录**：`expires_at` 已过 ⇒ 排除；`review_after` 已过 ⇒ 收但**标注**
   （「待复核」是可判事实，不是丢弃理由）；
4. **内容有界**（AGENTS.md §10）：逐条**截断**（上限**复用** `retrieval_context` 的
   `DEFAULT_MAX_CHARS` / `DEFAULT_MAX_ITEMS`，**不新造第二份**）+ 条数上限 + 截断**标注**；
5. **空集合点名**：没有记忆 ⇒ 条目为空、`reason` 有名目 —— **不是**失败（多数项目没有记忆），
   但必须有可读理由，不静默空。

**确定性**：同一份持久状态 ⇒ 同一个视图（按 `(tier, id)` 排序后取前 N 条；时间比较用
调用方传进来的 `now`，**不读进程时钟**）—— 与 `retrieval_context` / 报告汇编器同一纪律。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from packages.application.ports.memory_store import MemoryStore

#: 上限**复用** `retrieval_context` 的常量（``不``新造第二份 —— GOAL-082 EC-02 的判据钉这条）。
from packages.application.run_orchestration.retrieval_context import (
    DEFAULT_MAX_CHARS,
    DEFAULT_MAX_ITEMS,
)
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier
from packages.domain.memory import MemoryRecord

#: 进上下文的记忆档位（跨 run 的那两档；`RUN` / `SESSION` **不在**其中）。
PRIOR_TIERS: tuple[MemoryTier, ...] = (MemoryTier.PROJECT, MemoryTier.ORGANIZATION)

#: 待复核记录的标注（**逐字**；判据按它判「时效标注可见」）。
REVIEW_DUE_MARK = "[review-due]"
#: 被截断条目的标注（与 `retrieval_prompt.TRUNCATED_MARK` 同一记号）。
TRUNCATED_MARK = "[truncated]"


@dataclass(frozen=True, slots=True)
class MemoryEntry:
    """进上下文的一条前序知识（**摘录**，不是原始正文）。"""

    memory_id: str
    tier: str
    kind: str
    #: 来源（这条知识从哪来）—— 跨 run 判据读它（`EC-04`：必须指向前一轮的落库结论）。
    provenance: str
    shown: str
    truncated: bool
    #: `review_after` 已过（执行了，但需复核）—— 与「被丢弃」是两件事。
    review_due: bool


@dataclass(frozen=True, slots=True)
class PriorKnowledgeView:
    """装配结果：逐条读数 + **空集合的理由**（可判事实）。"""

    entries: tuple[MemoryEntry, ...]
    run_id: str = ""
    reason: str | None = None


def build_prior_knowledge(
    memories: MemoryStore | None,
    *,
    now: Timestamp,
    run_id: str = "",
    max_items: int = DEFAULT_MAX_ITEMS,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> PriorKnowledgeView:
    """前序（跨 run）记忆 → `PriorKnowledgeView`（只读 canonical；零出网）。"""
    if max_items < 1:
        raise ValueError("max_items must be >= 1")
    if max_chars < 1:
        raise ValueError("max_chars must be >= 1")
    if memories is None:
        # 装配没接记忆面 ⇒ **如实为空并点名理由**（不是「没有记忆」—— 那是另一件事）。
        return PriorKnowledgeView(entries=(), run_id=run_id, reason="no memory store is wired")
    records = _prior_records(memories, now)
    if not records:
        return PriorKnowledgeView(
            entries=(),
            run_id=run_id,
            reason=(
                f"no active {'/'.join(tier.value for tier in PRIOR_TIERS)} memory is in the store"
            ),
        )
    entries = tuple(_entry(record, now, max_chars=max_chars) for record in records)[:max_items]
    return PriorKnowledgeView(entries=entries, run_id=run_id)


def _prior_records(memories: MemoryStore, now: Timestamp) -> tuple[MemoryRecord, ...]:
    """跨档位的有效记录（按 `(tier, id)` 排序 ⇒ 确定性）。"""
    found: list[MemoryRecord] = []
    for tier in PRIOR_TIERS:
        found.extend(record for record in memories.query(tier=tier) if not _expired(record, now))
    return tuple(sorted(found, key=lambda item: (item.tier.value, item.id)))


def _entry(record: MemoryRecord, now: Timestamp, *, max_chars: int) -> MemoryEntry:
    shown, truncated = _clip(record.content, max_chars)
    return MemoryEntry(
        memory_id=record.id,
        tier=record.tier.value,
        kind=record.kind.value,
        provenance=record.provenance,
        shown=shown,
        truncated=truncated,
        review_due=_review_due(record, now),
    )


def _expired(record: MemoryRecord, now: Timestamp) -> bool:
    return record.expires_at is not None and record.expires_at.value <= now.value


def _review_due(record: MemoryRecord, now: Timestamp) -> bool:
    return record.review_after is not None and record.review_after.value <= now.value


def _clip(text: str, max_chars: int) -> tuple[str, bool]:
    """有界摘录：超限即截断并**点名**（`truncated=True`）。"""
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars], True


def with_prior_knowledge(deps: Any, task: Any, spec_context: Any) -> Any:
    """把**此刻已落库**的前序知识装进本任务的 spec（GOAL-20261018-082 EC-01）。

    未接装配器（`deps.prior_knowledge is None`）⇒ **原样返回**（既有语义逐字节不变）。
    接了 ⇒ 调装配器并把结果放进 spec；装配器**抛错** ⇒ 让异常冒到执行循环
    （那里的失败路径会**点名** —— 不静默给一个空知识面：那会让「读不到」与「没有」
    不可区分，与 `retrieval_context.with_retrieval_context` 同一条纪律）。
    """
    build = getattr(deps, "prior_knowledge", None)
    if build is None:
        return spec_context
    from dataclasses import replace

    view = build(str(task.run_id.value))
    return replace(spec_context, prior_knowledge=view)


def context_payload(view: PriorKnowledgeView) -> dict[str, object]:
    """上下文的**载荷**（唯一构造点；读面写出的就是这些字节）。"""
    payload: dict[str, object] = {
        "run_id": view.run_id,
        "entries": [
            {
                "memory_id": entry.memory_id,
                "tier": entry.tier,
                "kind": entry.kind,
                "provenance": entry.provenance,
                "shown": entry.shown,
                "truncated": entry.truncated,
                "review_due": entry.review_due,
            }
            for entry in view.entries
        ],
    }
    if not view.entries and view.reason:
        payload["reason"] = view.reason
    return payload


__all__ = [
    "DEFAULT_MAX_CHARS",
    "DEFAULT_MAX_ITEMS",
    "PRIOR_TIERS",
    "REVIEW_DUE_MARK",
    "TRUNCATED_MARK",
    "MemoryEntry",
    "PriorKnowledgeView",
    "build_prior_knowledge",
    "with_prior_knowledge",
    "context_payload",
]
