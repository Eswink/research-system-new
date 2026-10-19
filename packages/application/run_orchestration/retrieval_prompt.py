"""检索摘录 → **提示词的一段**（GOAL-20261016-081 EC-01）。

**它补哪一格**：GOAL-20261014-078 让活检索的内容进了**会话上下文**（`ContextSnapshot`
在 spec 上、逐条摘录落成可读制品）—— 但会话的**唯一**出站消息是
`send_message(spec.task_contract.purpose)`（`adapters/openhands/session_builder.py:83`）
⇒ **模型看不见那些内容**。实测证据（GOAL-080 EC-04 的真实 run）：模型自陈

    This session did **not** receive the retrieved literature records referenced in the task
    … I have no source list, abstracts, or retrieved records in my context, so I cannot
    honestly cite a specific retrieved source by name … doing so would require inventing a
    citation, which I won't do.

⇒ 缺口不是「检索没发生」（GOAL-027/029 已通）也不是「内容没进上下文」（078 已通），
而是「**上下文没进模型的眼睛**」。

**三条纪律**（逐条可判）：

1. **有界**（§10）：只渲染**已被 `retrieval_context` 有界摘录过**的那些条目
   （它自己的 `DEFAULT_MAX_ITEMS` / `DEFAULT_MAX_CHARS` 已生效）—— 本模块**不新造**
   第二份上限，也不读原始字节；
2. **截断可见**：条目被截过（`truncated`）⇒ 逐条**标注**（不得静默变短）；
3. **同源**：渲染的文本**就是** `entry.shown`（读面制品里同一字段）—— 因此
   「模型拿到了什么」对着既有读面**逐字**可核对。

**零回归**：没有人给摘录（`entries` 为空）⇒ 渲染成**空串**，调用方据此不加那一段。
"""

from __future__ import annotations

from typing import Any

#: 提示词里那一段的标题（**逐字**；判据按它定位）。
PROMPT_SECTION_TITLE = "RETRIEVED SOURCES (system-fetched; cite these by identifier)"

#: GOAL-20261018-082 EC-01：**前序知识**那一段的标题（与检索段**并列**，不替换）。
PRIOR_SECTION_TITLE = "PRIOR KNOWLEDGE (from earlier runs in this project; build on it)"

#: GOAL-20261019-089 EC-02：**研究方向**那一段的标题（与另两段**并列**）。
DIRECTION_SECTION_TITLE = "PROJECT DIRECTION (the operator's stated research direction)"

#: 被截断条目的标注（**逐字**；判据按它判「截断可见」）。
TRUNCATED_MARK = "[truncated]"
#: 待复核条目的标注（**逐字**）。
REVIEW_DUE_MARK = "[review-due]"


def render_retrieval_prompt(view: Any) -> str:
    """`RetrievalContextView` → 提示词那一段（**空集合 ⇒ 空串**）。

    **为什么空集合渲染成空串而不是「没有来源」的说明**：那一段的语义是「你手上有什么」；
    手上没有东西时**加一段说「没有」**会把「没检索」写进每一份提示词（既有行为里
    没有这种东西），而「没有检索」这件事的可判定性由**读面制品**（GOAL-078 EC-03：
    空集合也写盘、带 `reason`）承担 —— 两处各司其职，不互相冒充。
    """
    entries = tuple(getattr(view, "entries", ()) or ())
    if not entries:
        return ""
    lines = [PROMPT_SECTION_TITLE, ""]
    for entry in entries:
        identifier = str(getattr(entry, "identifier", "") or "")
        shown = str(getattr(entry, "shown", "") or "")
        mark = f" {TRUNCATED_MARK}" if getattr(entry, "truncated", False) else ""
        lines.append(f"- {identifier}{mark}: {shown}")
    lines.append("")
    return "\n".join(lines)


def render_prior_knowledge_prompt(view: Any) -> str:
    """`PriorKnowledgeView` → **前序知识**那一段（**空集合 ⇒ 空串**）。

    与检索段**并列**：两段的语义不同（「这次取回了什么」vs「前几轮已经知道什么」），
    因此不合并、不互相替代 —— 合并会让「模型是因检索还是因前序知识而改变了立题」不可判。

    逐条带 **`memory_id`（逐字标识）+ 来源 `provenance`**：前者是 EC-04 判「模型引用了
    前序知识」的锚点，后者让「这条知识来自哪一轮」在提示词里就可见（不是靠外部台账猜）。
    """
    entries = tuple(getattr(view, "entries", ()) or ())
    if not entries:
        return ""
    lines = [PRIOR_SECTION_TITLE, ""]
    for entry in entries:
        memory_id = str(getattr(entry, "memory_id", "") or "")
        provenance = str(getattr(entry, "provenance", "") or "")
        shown = str(getattr(entry, "shown", "") or "")
        marks = ""
        if getattr(entry, "truncated", False):
            marks += f" {TRUNCATED_MARK}"
        if getattr(entry, "review_due", False):
            marks += f" {REVIEW_DUE_MARK}"
        lines.append(f"- {memory_id}{marks}: {shown} (source: {provenance})")
    lines.append("")
    return "\n".join(lines)


def prompt_with_retrieval(purpose: str, view: Any) -> str:
    """合约 purpose + 检索那一段（**无摘录 ⇒ 逐字返回 purpose**）。

    顺序：**先任务后来源** —— 模型先知道要做什么，再看到手上的材料。
    """
    section = render_retrieval_prompt(view)
    if not section:
        return purpose
    return f"{purpose}\n\n{section}"


def prompt_with_prior_knowledge(purpose: str, view: Any) -> str:
    """合约 purpose + **前序知识**那一段（**无条目 ⇒ 逐字返回 purpose**）。

    单独一个入口（不复用 `prompt_with_retrieval`）：两段可以**同时**在场，也可以各自缺席；
    把「拼接顺序」写在一处（`compose_prompt`）而不是散在调用点。
    """
    section = render_prior_knowledge_prompt(view)
    if not section:
        return purpose
    return f"{purpose}\n\n{section}"


def render_direction_prompt(direction: str | None) -> str:
    """研究方向 → 提示词那一段（**未声明 ⇒ 空串**：既有提示词逐字不变）。

    **为什么它是一段而不是塞进 purpose**：purpose 是**合约**的一部分（同一条合约的
    所有 run 共用同一段文本）；方向是**这个项目**的事实。混在一起会让「合约改了什么」
    与「项目研究什么」不可区分（与 GOAL-010 的「声明化命名」同一条纪律）。
    """
    text = (direction or "").strip()
    if not text:
        return ""
    return chr(10).join([DIRECTION_SECTION_TITLE, "", text, ""])


def prompt_with_direction(purpose: str, direction: str | None) -> str:
    """合约 purpose + **方向**那一段（未声明 ⇒ **逐字**返回 purpose）。"""
    section = render_direction_prompt(direction)
    if not section:
        return purpose
    return chr(10).join([purpose, "", section])


def compose_prompt(
    purpose: str,
    *,
    direction: str | None = None,
    prior_knowledge: Any = None,
    retrieval: Any = None,
) -> str:
    """合约 purpose + [方向] + [前序知识] + [检索摘录]（全缺 ⇒ **逐字**返回 purpose）。

    **顺序 = 先方向、再前序、最后检索**：模型先知道**被要求研究什么**，再知道自己
    **已经**知道什么（立题的起点），最后看到这一轮新取回的材料（对起点的更新）。
    """
    text = prompt_with_direction(purpose, direction)
    for view, render in (
        (prior_knowledge, prompt_with_prior_knowledge),
        (retrieval, prompt_with_retrieval),
    ):
        if view is not None:
            text = render(text, view)
    return text


__all__ = [
    "DIRECTION_SECTION_TITLE",
    "PROMPT_SECTION_TITLE",
    "PRIOR_SECTION_TITLE",
    "REVIEW_DUE_MARK",
    "TRUNCATED_MARK",
    "compose_prompt",
    "prompt_with_direction",
    "prompt_with_prior_knowledge",
    "prompt_with_retrieval",
    "render_direction_prompt",
    "render_prior_knowledge_prompt",
    "render_retrieval_prompt",
]
