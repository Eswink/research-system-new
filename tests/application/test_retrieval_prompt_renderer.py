"""GOAL-20261016-081 EC-01 / EC-02 判据：**检索摘录进提示词**，且有界、截断可见、同源。

判据成对（正向 / 反证 / 上限 / 同源 / 零回归）：

- **正向**：给了摘录 ⇒ 那一段在提示词里，且**逐条标识在场**（PMID / DOI 形态）；
- **反证**：没给摘录 ⇒ 提示词里**没有**那一段（不留空壳）；
- **上限**（EC-02）：超长/超条数由**既有** `retrieval_context` 摘录点约束 ——
  本判据断言渲染器**不放大**（它只排 `shown`），且被截的条目**带标注**；
- **同源**（EC-03 的前半）：渲染出的逐条文本 == `entry.shown`（**逐字**）——
  那是读面制品里的同一个字段；
- **零回归**：`prompt_with_retrieval` 在空视图上**逐字**返回 purpose。
"""

from __future__ import annotations

from packages.application.run_orchestration.retrieval_context import (
    DEFAULT_MAX_CHARS,
    DEFAULT_MAX_ITEMS,
    RetrievalContextView,
    RetrievalEntry,
)
from packages.application.run_orchestration.retrieval_prompt import (
    PROMPT_SECTION_TITLE,
    TRUNCATED_MARK,
    prompt_with_retrieval,
    render_retrieval_prompt,
)
from packages.domain.memory import ContextSnapshot

_RUN_ID = "33333333-3333-4333-8333-333333333333"
_PURPOSE = "TASK — write the research plan for this study."


def _entry(
    identifier: str,
    shown: str = "a title",
    *,
    truncated: bool = False,
    tag: str = "e1",
) -> RetrievalEntry:
    return RetrievalEntry(
        evidence_id=f"evidence:{tag}",
        artifact_id=f"tool-result:{tag}",
        identifier=identifier,
        title=shown,
        shown=shown,
        truncated=truncated,
    )


def _view(
    entries: tuple[RetrievalEntry, ...], *, reason: str | None = None
) -> RetrievalContextView:
    return RetrievalContextView(
        snapshot=ContextSnapshot(retrieval_digest="sha256:" + "0" * 64),
        entries=entries,
        run_id=_RUN_ID,
        reason=reason,
    )


class TestTheExcerptsReachThePrompt:
    """正向：有摘录 ⇒ 那一段在提示词里，**逐条标识在场**。"""

    def test_every_identifier_appears_in_the_prompt(self) -> None:
        view = _view((_entry("42781891"), _entry("10.12688/f1000research.180013.2", tag="e2")))
        prompt = prompt_with_retrieval(_PURPOSE, view)
        assert "42781891" in prompt, prompt
        assert "10.12688/f1000research.180013.2" in prompt, prompt

    def test_the_section_carries_its_title(self) -> None:
        """那一段**有标题**（读者与判据都能一眼定位它）。"""
        prompt = prompt_with_retrieval(_PURPOSE, _view((_entry("42781891"),)))
        assert PROMPT_SECTION_TITLE in prompt, prompt

    def test_the_task_comes_before_the_sources(self) -> None:
        """**先任务后来源**（模型先知道要做什么，再看到手上的材料）。"""
        prompt = prompt_with_retrieval(_PURPOSE, _view((_entry("42781891"),)))
        assert prompt.index(_PURPOSE) < prompt.index(PROMPT_SECTION_TITLE), prompt

    def test_the_prompt_starts_with_the_contract_purpose_verbatim(self) -> None:
        """合约文本**逐字保留**（前缀不被改写）。"""
        prompt = prompt_with_retrieval(_PURPOSE, _view((_entry("42781891"),)))
        assert prompt.startswith(_PURPOSE), prompt[:80]


class TestTheNegativeArmIsReal:
    """反证：没有摘录 ⇒ **没有那一段**（不留空壳、不写「没有来源」）。"""

    def test_an_empty_view_adds_nothing(self) -> None:
        assert render_retrieval_prompt(_view(())) == ""

    def test_the_prompt_is_the_purpose_verbatim_when_empty(self) -> None:
        """**逐字**：空视图上提示词 == purpose（零回归的机械含义）。"""
        assert prompt_with_retrieval(_PURPOSE, _view(())) == _PURPOSE

    def test_an_empty_view_does_not_write_a_no_sources_note(self) -> None:
        """空集合**不**写「没有来源」那一句 —— 那会把「没检索」写进每份提示词。"""
        prompt = prompt_with_retrieval(_PURPOSE, _view((), reason="no retrieved evidence"))
        assert PROMPT_SECTION_TITLE not in prompt, prompt
        assert "no retrieved evidence" not in prompt, prompt


class TestTheBoundsAndTruncationAreVisible:
    """EC-02：**有界**且**截断可见**；上限与既有摘录点**同源**（不新造第二份）。"""

    def test_a_truncated_entry_is_marked(self) -> None:
        prompt = prompt_with_retrieval(
            _PURPOSE, _view((_entry("42781891", "a very long title", truncated=True),))
        )
        assert TRUNCATED_MARK in prompt, prompt

    def test_an_untruncated_entry_carries_no_mark(self) -> None:
        """反向：没被截的条目不标注（标注要有信息量，不能一律打）。"""
        prompt = prompt_with_retrieval(_PURPOSE, _view((_entry("42781891"),)))
        assert TRUNCATED_MARK not in prompt, prompt

    def test_the_renderer_does_not_enlarge_what_was_excerpted(self) -> None:
        """渲染器**只排 `shown`**：提示词里不出现 `title` 之外的更长文本。

        本判据的构造性含义：渲染器**没有**第二次截断/放大 —— 上限属于**摘录点**
        （`retrieval_context`），本模块不再设界限（否则会有两份上限互相矛盾）。

        逐字形态在 GOAL-20261029-100 EC-01 改了**前缀**：那一行现在以引用编号开头
        （`- [1] 42781891: short shown`）。改的是前缀，`{identifier}: {shown}` 的后半段
        逐字不变 —— 本判据仍然判「渲染器不放大」，并把编号一并钉住。
        """
        entry = _entry("42781891", "short shown")
        prompt = prompt_with_retrieval(_PURPOSE, _view((entry,)))
        assert "short shown" in prompt
        # 渲染器不引入超出条目字段的内容（逐字比对那一段里的条目行）
        line = next(item for item in prompt.splitlines() if "42781891" in item)
        assert line.strip() == f"- [1] {entry.identifier}: {entry.shown}", line

    def test_the_bounds_live_in_the_excerpt_point_not_here(self) -> None:
        """上限常量**仍只在** `retrieval_context`（本模块不复制它们）。"""
        import packages.application.run_orchestration.retrieval_prompt as module

        source = module.__doc__ or ""
        assert DEFAULT_MAX_ITEMS >= 1 and DEFAULT_MAX_CHARS >= 1
        for name in ("DEFAULT_MAX_ITEMS", "DEFAULT_MAX_CHARS"):
            assert not hasattr(module, name), f"渲染器不得自带第二份上限：{name}（{source[:0]}）"


class TestTheRenderingIsSameSourcedWithTheReadFace:
    """EC-03 的前半：渲染出的逐条文本 == `entry.shown`（读面制品里的同一字段）。"""

    def test_the_shown_text_is_verbatim(self) -> None:
        entry = _entry("10.31234/osf.io/w7xpq_v2", "Reproducibility of computational research")
        prompt = prompt_with_retrieval(_PURPOSE, _view((entry,)))
        assert entry.shown in prompt, prompt

    def test_every_entry_contributes_exactly_one_line(self) -> None:
        """**逐条一行**（条数与行数一致 —— 不合并、不丢条）。"""
        entries = tuple(_entry(f"id-{index}", tag=f"e{index}") for index in range(5))
        prompt = prompt_with_retrieval(_PURPOSE, _view(entries))
        item_lines = [line for line in prompt.splitlines() if line.startswith("- ")]
        assert len(item_lines) == len(entries), (item_lines, len(entries))

    def test_the_identifier_is_not_rewritten(self) -> None:
        """标识**不被改写**（读面里是那串，提示词里也是那串）。"""
        for identifier in ("42781891", "10.12688/f1000research.180013.2"):
            prompt = prompt_with_retrieval(_PURPOSE, _view((_entry(identifier),)))
            assert identifier in prompt, identifier
