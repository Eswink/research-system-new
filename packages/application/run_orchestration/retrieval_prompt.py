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

from packages.application.deliverable.references import numbered_records

#: 提示词里那一段的标题（**逐字**；判据按它定位）。
#: GOAL-20261029-100 EC-01 改字面（`cite these by number`）：编号现在**随行给到**，
#: 模型不再需要自己数「这是第几条」。标题是契约的一部分 —— 改字 = 改契约，判据按它定位。
PROMPT_SECTION_TITLE = "RETRIEVED SOURCES (system-fetched; cite these by number)"

#: GOAL-20261018-082 EC-01：**前序知识**那一段的标题（与检索段**并列**，不替换）。
PRIOR_SECTION_TITLE = "PRIOR KNOWLEDGE (from earlier runs in this project; build on it)"

#: GOAL-20261019-089 EC-02：**研究方向**那一段的标题（与另两段**并列**）。
DIRECTION_SECTION_TITLE = "PROJECT DIRECTION (the operator's stated research direction)"

#: GOAL-20261020-091 EC-02：**被评对象**那一段的标题（与另三段**并列**）。
REVIEW_MATERIAL_SECTION_TITLE = "UNDER REVIEW (the artifact you are asked to judge)"

#: GOAL-20261022-093：**上一轮评审结论**那一段的标题（与另四段**并列**）。
#: 逐字取自阶梯「复检」域的下一级（「评审的判词驱动下一轮修订」）：这一段把上一轮
#: 判成什么**送达下一轮的会话**，模型据此决定这一轮改什么。
REVIEW_OUTCOME_SECTION_TITLE = "PRIOR REVIEW (how the last round was judged; revise against it)"

#: GOAL-20261029-100 EC-03：**本次评审的逐条点表**那一段的标题（与另五段**并列**）。
#:
#: 与 `REVIEW_OUTCOME_SECTION_TITLE` 是两件事（刻意分开）：那一段是「**上一轮**被判成
#: 什么」（跨 run 搬运），这一段是「**这一轮的评审**提出了哪几条、编号是什么」（本 run 内）。
#: 应答相要逐条回应，就必须看到编号 —— 否则它得自己数「这是第几条」，
#: 与 GOAL-099 `W-1` 的引用编号是同一类缺陷。
REVIEW_POINTS_SECTION_TITLE = "REVIEW POINTS (answer every id below, one entry each)"

#: 被截断条目的标注（**逐字**；判据按它判「截断可见」）。
TRUNCATED_MARK = "[truncated]"
#: 待复核条目的标注（**逐字**）。
REVIEW_DUE_MARK = "[review-due]"
#: **不可引用**条目的标注（**逐字**；GOAL-20261029-100 EC-01）。
#:
#: 用于 `ids[]` 形状的记录：它没有著录字段（作者 / 刊名 / 年份）⇒ 进不了 References。
#: 标注它而**不**给它编号，是为了让「这一条不占编号」在提示词里**可见** ——
#: 静默略过会让模型以为列表少了一行。
NOT_CITABLE_MARK = "[not citable]"


def render_retrieval_prompt(view: Any) -> str:
    """`RetrievalContextView` → 提示词那一段（**空集合 ⇒ 空串**）。

    **为什么空集合渲染成空串而不是「没有来源」的说明**：那一段的语义是「你手上有什么」；
    手上没有东西时**加一段说「没有」**会把「没检索」写进每一份提示词（既有行为里
    没有这种东西），而「没有检索」这件事的可判定性由**读面制品**（GOAL-078 EC-03：
    空集合也写盘、带 `reason`）承担 —— 两处各司其职，不互相冒充。

    **GOAL-20261029-100 EC-01：每一行**以引用编号开头**（`- [1] 39284801: <excerpt>`）。
    编号由 `references.numbered_records` 给出 —— 与 `## References` 的序号**同源**
    （同一个函数、同一条规则：去重后首次出现顺序、从 1 起）。此前这里是裸标识，
    模型必须自己数「这是第几条」；那个数错了没有任何判据会红（GOAL-099 `W-1`）。

    **只给可引用的条目编号**（`entry.citable`）：`ids[]` 形状（esearch 的命中列表）没有
    著录字段 ⇒ `reference_table` 永远跳过它 ⇒ 若它占了编号，其后每一条都会整体错位。
    不可引用的条目仍然**逐条列出**（`[not citable]` 标注，见 `NOT_CITABLE_MARK`）——
    「模型看到了什么」不变，变的只是「谁占了编号」。
    """
    entries = tuple(getattr(view, "entries", ()) or ())
    if not entries:
        return ""
    numbered = numbered_records(
        tuple(
            str(getattr(entry, "identifier", "") or "")
            for entry in entries
            if getattr(entry, "citable", True)
        )
    )
    numbers = {identifier: index for index, identifier in numbered}
    lines = [PROMPT_SECTION_TITLE, ""]
    for entry in entries:
        identifier = str(getattr(entry, "identifier", "") or "")
        shown = str(getattr(entry, "shown", "") or "")
        # 前缀只是**编号**（不可引用时是标注）—— 标识与截断标记的相对位置逐字不变，
        # 使读面按 `{identifier}{[truncated]}: {shown}` 重建那一行仍然成立。
        prefix = f"[{numbers[identifier]}] " if identifier in numbers else f"{NOT_CITABLE_MARK} "
        mark = f" {TRUNCATED_MARK}" if getattr(entry, "truncated", False) else ""
        lines.append(f"- {prefix}{identifier}{mark}: {shown}")
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


def _section_of(value: Any, render: Any) -> str:
    """一段的值 → **那段文本**（已渲染的 `str` 原样用，视图对象交给 `render`）。

    **为什么必须两种都认**（GOAL-20261020-091 实测到的既有缺陷）：
    `task_executor._run_session` 把 **已渲染好的 `str`** 放进 `AgentSessionSpec`
    （`session_prompts.*_prompt` 的返回），而 `SessionBuilder` 又把它交给 `compose_prompt`
    —— 若这里只按**视图对象**渲染，`render_retrieval_prompt("<已渲染的 str>")` 会去找
    `entries` 属性、拿不到 ⇒ 返回**空串** ⇒ **那一段被静默丢弃**。实测读数：真实 run 的
    reviewer 会话收到的提示词长度 1082、内容只有合约文本（被评对象段整个不见），
    两位模型都如实报告「UNDER REVIEW 段不存在」。同一条缝对检索段 / 前序段一直存在。
    """
    if isinstance(value, str):
        return value
    return str(render(value) or "")


def prompt_with_retrieval(purpose: str, view: Any) -> str:
    """合约 purpose + 检索那一段（**无摘录 ⇒ 逐字返回 purpose**）。

    顺序：**先任务后来源** —— 模型先知道要做什么，再看到手上的材料。
    """
    section = _section_of(view, render_retrieval_prompt)
    if not section:
        return purpose
    return f"{purpose}\n\n{section}"


def prompt_with_prior_knowledge(purpose: str, view: Any) -> str:
    """合约 purpose + **前序知识**那一段（**无条目 ⇒ 逐字返回 purpose**）。

    单独一个入口（不复用 `prompt_with_retrieval`）：两段可以**同时**在场，也可以各自缺席；
    把「拼接顺序」写在一处（`compose_prompt`）而不是散在调用点。
    """
    section = _section_of(view, render_prior_knowledge_prompt)
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


def render_review_material_prompt(view: Any) -> str:
    """`ReviewMaterialView` → **被评对象**那一段（**空集合 ⇒ 空串**）。

    与另三段**并列**、不替换：那三段说的是「被要求做什么 / 已经知道什么 / 取回了什么」，
    这一段说的是「你要评的是这一件东西」—— 混进任何一段都会让「模型看到的被评对象」
    与「落库的那份制品」不可分辨。

    逐条带**产物名 + 内容摘要**：前者是「这是谁的哪件产物」，后者让读面能把提示词里
    的那段字节与 canonical 制品对上（截断后也一样 —— 摘要是**展示出去的那些字节**的摘要）。
    """
    entries = tuple(getattr(view, "entries", ()) or ())
    if not entries:
        return ""
    lines = [REVIEW_MATERIAL_SECTION_TITLE, ""]
    for entry in entries:
        name = str(getattr(entry, "artifact_name", "") or "")
        digest = str(getattr(entry, "digest", "") or "")
        shown = str(getattr(entry, "shown", "") or "")
        mark = f" {TRUNCATED_MARK}" if getattr(entry, "truncated", False) else ""
        lines.append(f"- {name}{mark} (content digest: {digest}):")
        lines.append(shown)
        lines.append("")
    return "\n".join(lines)


def prompt_with_review_material(purpose: str, view: Any) -> str:
    """合约 purpose + **被评对象**那一段（**无条目 ⇒ 逐字返回 purpose**）。"""
    section = _section_of(view, render_review_material_prompt)
    if not section:
        return purpose
    return f"{purpose}\n\n{section}"


def render_review_outcome_prompt(view: Any) -> str:
    """`ReviewOutcomeView` → **上一轮评审结论**那一段（**无可搬运内容 ⇒ 空串**）。

    与另四段**并列**、各有语义：方向 = 被要求研究什么；前序知识 = 已经知道什么；
    检索 = 这一轮取回了什么；被评对象 = 你要判的那件东西；**本段 = 上一轮被判成什么**。

    **分歧优先**：面板有分歧时逐条列出**每一位**的 verdict（含未被采纳的那些），
    并在抬头写明建议性结论 —— 只报多数票会把上一轮刚做出来的「分歧可读」压回一个
    数字，那正是 GOAL-087 修掉的那件事。无分歧时只报结论与票型。

    逐条带**发言者 + 执行目标**：前者让「谁说的」可追（`gate:<agent>`），后者让「哪个
    模型说的」可追（`endpoint/model_name`）—— 两者缺一，读者就无法判断这条分歧是不是
    同一个模型自言自语。
    """
    if getattr(view, "empty", True):
        return ""
    lines = [REVIEW_OUTCOME_SECTION_TITLE, ""]
    prior = str(getattr(view, "prior_run_id", "") or "")
    advisory = getattr(view, "advisory", None)
    votes = dict(getattr(view, "votes", {}) or {})
    voters = int(getattr(view, "voters", 0) or 0)
    lines.append(f"- carried from prior run: {prior}")
    lines.append(f"- reviewers who voted: {voters}")
    targets = tuple(getattr(view, "targets", ()) or ())
    if targets:
        # **谁判的**与**判成什么**分两行：只看票数时，「两个模型分歧」与「一个模型
        # 自言自语」不可区分 —— 目标集合把归因面钉在提示词里（与 `PanelVerdict.targets`
        # 同源）。
        lines.append(f"- reviewer targets: {', '.join(targets)}")
    lines.append(f"- advisory verdict: {advisory or 'none (tie or no eligible vote)'}")
    if votes:
        tally = ", ".join(f"{key}={votes[key]}" for key in sorted(votes))
        lines.append(f"- votes: {tally}")
    dissent = tuple(getattr(view, "dissent", ()) or ())
    lines.extend(_dissent_lines(dissent))
    ineligible = tuple(getattr(view, "ineligible", ()) or ())
    if ineligible:
        lines.append("- findings that could not vote (named, not folded into any tally):")
        lines.extend(f"  - {item}" for item in ineligible)
    lines.append("")
    return "\n".join(lines)


def _dissent_lines(dissent: tuple[Any, ...]) -> list[str]:
    """分歧逐条（**每位**未采纳者的 verdict + 执行目标 + 它自己写的正文）。

    单列的理由是**可读性 + 规模门**：这一段的形状（发言者 / 目标 / 截断标记 / 正文
    缩进）与上半段的票型是两件事，混在一个函数里会同时撞 50 行门与可读性。
    """
    if not dissent:
        return []
    lines = ["- dissent (every verdict that is not the advisory; read these):"]
    for item in dissent:
        speaker = str(getattr(item, "speaker", "") or "")
        verdict = str(getattr(item, "verdict", "") or "")
        target = str(getattr(item, "target", "") or "unknown target")
        detail = str(getattr(item, "detail", "") or "")
        mark = f" {TRUNCATED_MARK}" if getattr(item, "truncated", False) else ""
        lines.append(f"  - {speaker} on {target}: {verdict}{mark}")
        if detail:
            lines.append(f"    {detail}")
    return lines


def render_review_points_prompt(points: Any) -> str:
    """本 run 的**评审点表** → 提示词那一段（**空 ⇒ 空串**）。

    逐条 `- P1 (must_fix): <text>`：编号在前、严重性在括号里、原文在后 —— 读者（与判据）
    都能一眼核对「这条意见是第几条、有多要紧」。编号由 `author_response.points_of` 给出
    （**唯一**构造点），本渲染器不再造第二套编号。
    """
    items = tuple(points or ())
    if not items:
        return ""
    lines = [REVIEW_POINTS_SECTION_TITLE, ""]
    for point in items:
        point_id = str(getattr(point, "point_id", "") or "")
        severity = str(getattr(point, "severity", "") or "")
        text = str(getattr(point, "text", "") or "")
        lines.append(f"- {point_id} ({severity}): {text}")
    lines.append("")
    return "\n".join(lines)


def prompt_with_review_points(purpose: str, points: Any) -> str:
    """合约 purpose + **评审点表**那一段（**无点 ⇒ 逐字返回 purpose**）。

    **已渲染的 `str` 原样用**（与 `_section_of` 同一条缝、同一个理由）：会话创建点把
    `session_prompts.review_points_prompt(...)` 的**返回值**（已是那段文本）放进
    `AgentSessionSpec`，`compose_prompt` 又把它交回本函数 —— 若这里只按点对象渲染，
    `render_review_points_prompt("<一段文本>")` 会去迭代字符串的**每个字符**、拿不到
    `point_id` ⇒ 那一段变成 `-  (): ` 的空白行（本轮实测到的形态：19 行空点）。
    """
    if isinstance(points, str):
        section = points
    else:
        section = render_review_points_prompt(points)
    if not section:
        return purpose
    return f"{purpose}\n\n{section}"


def prompt_with_review_outcome(purpose: str, view: Any) -> str:
    """合约 purpose + **上一轮评审结论**那一段（**无可搬运内容 ⇒ 逐字返回 purpose**）。"""
    section = _section_of(view, render_review_outcome_prompt)
    if not section:
        return purpose
    return f"{purpose}\n\n{section}"


def compose_prompt(  # noqa: PLR0913 - 提示词六段并列：少一个形参就得让所有调用点先拼对象
    purpose: str,
    *,
    direction: str | None = None,
    prior_knowledge: Any = None,
    retrieval: Any = None,
    review_material: Any = None,
    review_outcome: Any = None,
    review_points: Any = None,
) -> str:
    """合约 purpose + [方向] + [前序知识] + [检索摘录] + [上一轮评审] + [评审点表] + [被评对象]。

    **顺序 = 先方向、再前序、再检索、再上一轮评审、再本次评审点表、最后被评对象**：
    模型先知道**被要求研究什么**，再知道自己**已经**知道什么（起点），再看到这一轮新取回
    的材料（对起点的更新），再看到**上一轮被判成什么**（要改什么），再看到**这一轮评审
    提出了哪几条**（要逐条回应什么），最后看到**它这一轮要判的那件东西**
    （`GOAL-20261020-091 EC-02`）—— 被评对象放在最后读，紧贴它要给出的判词。

    **上一轮评审排在检索之后、被评对象之前**（`GOAL-20261022-093`）：它是「这一轮该改
    什么」的依据，而它依据的是**上一轮**的被评对象 —— 与被评对象段（**本轮**要判的东西）
    是两件事，故分列且先读评审结论（先知道要改什么，再读要判什么）。

    **本次评审点表排在上一轮评审之后、被评对象之前**（`GOAL-20261029-100 EC-03`）：
    它是「这一轮要**逐条回应**什么」，紧跟着「上一轮被改判成什么」读 —— 两者是同一条
    返修线上的两个时点（上一轮的结论 / 这一轮的点表）。

    **全缺 ⇒ 逐字返回 purpose**（六段各自的零回归口径在本函数里合成一条）。
    """
    text = prompt_with_direction(purpose, direction)
    for view, render in (
        (prior_knowledge, prompt_with_prior_knowledge),
        (retrieval, prompt_with_retrieval),
        (review_outcome, prompt_with_review_outcome),
        (review_points, prompt_with_review_points),
        (review_material, prompt_with_review_material),
    ):
        if view is not None:
            text = render(text, view)
    return text


__all__ = [
    "DIRECTION_SECTION_TITLE",
    "NOT_CITABLE_MARK",
    "PROMPT_SECTION_TITLE",
    "PRIOR_SECTION_TITLE",
    "REVIEW_DUE_MARK",
    "REVIEW_MATERIAL_SECTION_TITLE",
    "REVIEW_OUTCOME_SECTION_TITLE",
    "REVIEW_POINTS_SECTION_TITLE",
    "TRUNCATED_MARK",
    "compose_prompt",
    "prompt_with_direction",
    "prompt_with_prior_knowledge",
    "prompt_with_retrieval",
    "prompt_with_review_material",
    "prompt_with_review_outcome",
    "prompt_with_review_points",
    "render_direction_prompt",
    "render_prior_knowledge_prompt",
    "render_retrieval_prompt",
    "render_review_material_prompt",
    "render_review_outcome_prompt",
    "render_review_points_prompt",
]
