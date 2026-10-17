"""GOAL-20261018-082 EC-01 / EC-02 判据：**前序知识进立题会话的提示词**，且有界。

**它判什么**：建档实测确认三处缺口（23 份协议零声明 `memory.read` / 记忆写入缺省 `RUN` 档 /
提示词装配面对 `memory` 零消费者）⇒ 即便记忆在库，**也没有消费者把它写成提示词**。
本文件判那条新接的读取面：

1. **有前序记忆 ⇒ 在提示词里**（逐条 `memory_id` 出现在那一段）；
2. **没有 ⇒ 没有那一段**（不伪造、不留空壳；空集合渲染成空串）；
3. **只收跨 run 档位**（`PROJECT` / `ORGANIZATION`；`RUN` / `SESSION` **不进**提示词）；
4. **有界**（§10）：逐条字符上限 + 条数上限，且**截断可见**（标注）；
5. **上限同源**：与 `retrieval_context.DEFAULT_MAX_*` **是同一个值**（不新造第二份）；
6. **时效可见**：`expires_at` 已过 ⇒ 排除；`review_after` 已过 ⇒ 收但**标注**。

判据只读**装配结果 + 渲染文本**（纯函数），不需要起会话 —— 会话创建点的那一段由
`tests/application/test_retrieval_prompt_renderer.py` 的形态覆盖（同一条
`compose_prompt`）。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from adapters.fakes import FakeMemoryStore
from packages.application.run_orchestration import retrieval_context
from packages.application.run_orchestration.prior_knowledge import (
    PRIOR_TIERS,
    REVIEW_DUE_MARK,
    build_prior_knowledge,
)
from packages.application.run_orchestration.retrieval_prompt import (
    PRIOR_SECTION_TITLE,
    PROMPT_SECTION_TITLE,
    TRUNCATED_MARK,
    compose_prompt,
    render_prior_knowledge_prompt,
)
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal

_NOW = Timestamp(datetime(2026, 10, 18, 12, 0, 0, tzinfo=timezone.utc))


def _commit(
    store: FakeMemoryStore,
    memory_id: str,
    content: str,
    *,
    tier: MemoryTier = MemoryTier.PROJECT,
    provenance: str = "run:prior-run:claim:c1",
    **extra: object,
) -> None:
    # 记忆库是 **deny-by-default**（未登记来源一律拒）—— 判据要造「已提交的记忆」，
    # 因此显式登记这一个来源；**不改** store 的白名单语义（那是既有安全面）。
    store.allow_source(provenance)
    store.commit(
        MemoryWriteProposal(
            id=memory_id,
            tier=tier,
            kind=MemoryType.FACT,
            content=content,
            provenance=provenance,
            confidence=0.9,
            scope="project",
            **extra,  # type: ignore[arg-type]
        )
    )


def test_prior_memory_reaches_the_prompt() -> None:
    """**有前序记忆 ⇒ 在提示词里**：每条 `memory_id` 逐字出现在那一段。"""
    store = FakeMemoryStore()
    _commit(store, "mem-a", "Earlier runs showed the FAIR pipelines reproduce better.")
    view = build_prior_knowledge(store, now=_NOW, run_id="run-2")

    section = render_prior_knowledge_prompt(view)

    assert PRIOR_SECTION_TITLE in section
    assert "mem-a" in section
    assert "Earlier runs showed the FAIR pipelines reproduce better." in section
    # 来源可见（跨 run 判据的锚点）。
    assert "run:prior-run:claim:c1" in section


def test_no_prior_memory_means_no_section() -> None:
    """**没有 ⇒ 没有那一段**：空视图渲染成空串，`compose_prompt` 逐字返回 purpose。"""
    store = FakeMemoryStore()
    view = build_prior_knowledge(store, now=_NOW, run_id="run-2")

    assert view.entries == ()
    assert view.reason, "空集合必须有可读理由（不是静默空）"
    assert render_prior_knowledge_prompt(view) == ""
    assert compose_prompt("do the task", prior_knowledge=view) == "do the task"


def test_only_cross_run_tiers_are_read() -> None:
    """**只收跨 run 档位**：`RUN` / `SESSION` 即便在库也不进提示词。"""
    store = FakeMemoryStore()
    _commit(store, "mem-run", "this run only", tier=MemoryTier.RUN)
    _commit(store, "mem-session", "this session only", tier=MemoryTier.SESSION)
    _commit(store, "mem-project", "cross-run knowledge", tier=MemoryTier.PROJECT)

    view = build_prior_knowledge(store, now=_NOW, run_id="run-2")
    section = render_prior_knowledge_prompt(view)

    assert [entry.memory_id for entry in view.entries] == ["mem-project"]
    assert "mem-run" not in section
    assert "mem-session" not in section
    assert set(PRIOR_TIERS) == {MemoryTier.PROJECT, MemoryTier.ORGANIZATION}


def test_entries_are_clipped_and_the_clip_is_visible() -> None:
    """**截断可见**：超长正文被截且带标注（不静默变短）。"""
    store = FakeMemoryStore()
    _commit(store, "mem-long", "x" * 5000)
    view = build_prior_knowledge(store, now=_NOW, run_id="run-2")

    entry = view.entries[0]
    assert entry.truncated is True
    assert len(entry.shown) == retrieval_context.DEFAULT_MAX_CHARS
    assert TRUNCATED_MARK in render_prior_knowledge_prompt(view)


def test_item_limit_is_named() -> None:
    """**条数上限**：超上限只取前 N 条（按 `(tier, id)` 确定性排序）。"""
    store = FakeMemoryStore()
    for index in range(retrieval_context.DEFAULT_MAX_ITEMS + 3):
        _commit(store, f"mem-{index:02d}", f"knowledge {index}")

    view = build_prior_knowledge(store, now=_NOW, run_id="run-2")

    assert len(view.entries) == retrieval_context.DEFAULT_MAX_ITEMS
    ids = [entry.memory_id for entry in view.entries]
    assert ids == sorted(ids), ("取前 N 条必须按确定性顺序", ids)


def test_the_limits_are_the_same_constants_as_the_retrieval_context() -> None:
    """**上限同源**：本模块的默认值与 `retrieval_context.DEFAULT_MAX_*` 是同一个值。

    判据直接比较**行为**（传入默认值时的截断长度与条数），而不是只读常量名 ——
    后者在「新造一份同值常量」时也会绿。
    """
    import inspect

    from packages.application.run_orchestration import prior_knowledge

    params = inspect.signature(prior_knowledge.build_prior_knowledge).parameters
    assert params["max_items"].default is retrieval_context.DEFAULT_MAX_ITEMS
    assert params["max_chars"].default is retrieval_context.DEFAULT_MAX_CHARS
    # 两个常量必须是**同一个对象**（`is`）—— 新造一份同值常量会让上一条仍绿。
    assert prior_knowledge.DEFAULT_MAX_ITEMS is retrieval_context.DEFAULT_MAX_ITEMS
    assert prior_knowledge.DEFAULT_MAX_CHARS is retrieval_context.DEFAULT_MAX_CHARS


def test_expired_memory_is_excluded_and_review_due_is_marked() -> None:
    """**时效**：`expires_at` 已过 ⇒ 排除；`review_after` 已过 ⇒ 收但**标注**。"""
    store = FakeMemoryStore()
    _commit(
        store,
        "mem-expired",
        "stale",
        expires_at=Timestamp(_NOW.value - timedelta(days=1)),
    )
    _commit(
        store,
        "mem-review",
        "needs review",
        review_after=Timestamp(_NOW.value - timedelta(days=1)),
    )

    view = build_prior_knowledge(store, now=_NOW, run_id="run-2")
    section = render_prior_knowledge_prompt(view)

    assert [entry.memory_id for entry in view.entries] == ["mem-review"]
    assert view.entries[0].review_due is True
    assert REVIEW_DUE_MARK in section


def test_both_sections_coexist_in_the_prompt() -> None:
    """**两段并列**：前序知识与检索摘录**同时**在场（不互相替代）。

    顺序是**先前序、后检索**（先知道自己已知什么，再看这一轮取回什么）。
    """
    store = FakeMemoryStore()
    _commit(store, "mem-a", "prior knowledge text")
    prior = build_prior_knowledge(store, now=_NOW, run_id="run-2")

    class _Entry:
        identifier = "PMID:1"
        shown = "a retrieved title"
        truncated = False
        artifact_id = "tool-result:x"
        evidence_id = "ev-1"

    class _View:
        entries = (_Entry(),)

    text = compose_prompt("task purpose", prior_knowledge=prior, retrieval=_View())

    assert PRIOR_SECTION_TITLE in text
    assert PROMPT_SECTION_TITLE in text
    assert text.index(PRIOR_SECTION_TITLE) < text.index(PROMPT_SECTION_TITLE)
    assert "mem-a" in text and "PMID:1" in text


def test_no_memory_store_wired_is_named_not_silent() -> None:
    """装配没接记忆面 ⇒ **点名理由**（与「没有记忆」是两件事）。"""
    view = build_prior_knowledge(None, now=_NOW, run_id="run-2")

    assert view.entries == ()
    assert "no memory store" in (view.reason or "")
