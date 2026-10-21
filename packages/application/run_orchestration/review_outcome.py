"""**上一轮评审的判词** → 下一轮会话提示词的一段（GOAL-20261022-093；阶梯「复检」域）。

**它补哪一格**：阶梯「复检」域的 `下一级` 逐字是「评审的判词驱动下一轮修订 —— 把分歧变成
下一轮的**修订指令**」。判定面此前只走到「两位判出不同结论且分歧可读」（GOAL-084…087/091
把判词做成可归因、可聚合、同批成组、平票也可读），而**建档实测**：那条判词**出不了本 run** —

1. `dissent` / `advisory` 在产品三根（`packages/`·`services/`·`adapters/`）里除聚合器自身
   （`evaluation/panel_verdict.py`）与读面自身（`adapters/canonical/review_read.py`）
   **零消费者**；
2. `revision_directive` / `review_directive` / `directive_from_review` / `prior_panel` /
   `remediation` 五个词在产品三根**全零命中**；
3. 四个提示词槽位（`direction` / `prior_knowledge` / `retrieval` / `review_material`）
   **没有一个**携带判词（`rg verdict` 在四个渲染器上零命中）。

⇒ 「上一轮判成什么」在**下一轮的会话里根本不可见**，模型无从据它修订。本模块是第五个
**并列**槽位的生产者：从前序 run 的落库判词读出**面板结论 + 逐条分歧**，交给提示词装配。

**五条边界**（逐条可判，全部有判据）：

1. **只读 canonical、零出网**：来源只有 `RunStore.for_program` + `ReviewFindingStore.for_run`
   —— 不建会话、不发请求、不读进程时钟；
2. **只收「同一程序内的前序 run」**：`prior_conclusion_reader` 同一入口（run → 程序归属 →
   序号最大者）。本 run 不属于任何程序 ⇒ **点名**（不猜、不跨程序读）；
3. **只认可归因的判词**：复用 `aggregate_panel` 的 `_eligible` 口径 —— 没有
   `reviewer_model` 的 finding **不进结论**，但**逐条点名**（不折算、不静默丢弃）；
4. **分歧优先于结论**：面板有**分歧**时那段必须**逐条列出双方 verdict**（「分歧可读」
   是上一轮的成果，本条不得把它压回一个多数票）；无分歧（全员同判或只有一票）时那段
   只报结论与票型 —— 两种形态**读面可区分**；
5. **缺席点名，不留空壳**：没有前序 run（程序第一轮）⇒ `reason` 有名目、条目为空；
   有前序 run 但**读不到任何可归因判词** ⇒ `reason` **点名**该 run（与「没有前序」
   严格区分：前者是事实，后者是缺项 —— 判据对两句话分别钉住）。

**它不做什么（如实登记）**：

- **不**把判词改写成「指令」：判词是评审者说的，措辞由它决定；本模块只做**搬运 + 有界
  摘录**。把「该改什么」提炼成指令是**模型**的事（下一轮的会话读这一段），不是本模块的
  文本生成 —— 在这里生成指令会造出一段**没有作者的判词**（与 §8「记忆不是自由写入的
  摘要」同一条纪律）；
- **不**改 `Decision` / 不改验收门：这一段进的是**提示词**，不是判定面（advisory 的
  既有边界不变）。

**确定性**：同一份持久状态 ⇒ 同一个视图（判词按 `(verdict, reviewed_by, id)` 排序后取；
无时钟读取）—— 与 `retrieval_context` / `prior_knowledge` / 报告汇编器同一纪律。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from packages.application.evaluation.panel_verdict import PanelVerdict, aggregate_panel
from packages.application.ports.review_finding_store import ScopedReviewFinding

#: 进提示词的**分歧条数**上限（§10 有界；超限时逐条截断并**标注**）。
DEFAULT_MAX_DISSENT = 8
#: 段内逐条 verdict 的**字符**上限（判词正文是评审者写的，可能很长）。
DEFAULT_MAX_CHARS = 400

#: 没有前序 run 时的理由（**逐字**；判据按它判「第一轮」这一形态）。
NO_PRIOR_RUN = "no prior run in this program (structurally nothing to carry)"
#: 有前序 run 但读不到可归因判词时的理由前缀（**逐字**；判据按它判「缺项」）。
NO_ATTRIBUTABLE = "prior run has no attributable review finding"
#: 本 run 的行**还没落库**时的理由前缀（**逐字**）。这不是失败：run 行由调用方在编排
#: 返回之后才写入 ⇒ 第一轮开工时必然查不到自己（与 `prior_conclusion_reader` 同一口径）。
NO_RUN_ROW = "this run's row is not persisted yet (first round of the program)"


@dataclass(frozen=True, slots=True)
class ReviewOutcomeEntry:
    """一条**分歧**（或结论）的逐字投影。"""

    #: 发言者（`reviewed_by`；缺失回落到 finding id —— 与 `_speaker` 同口径，不伪造身份）。
    speaker: str
    verdict: str
    #: 评审者跑在哪个目标上（`endpoint/model_name`；`None` = 未能归因）。
    target: str | None
    #: 该判词自述的 findings（有界拼接；超限见 `truncated`）。
    detail: str
    truncated: bool


@dataclass(frozen=True, slots=True)
class ReviewOutcomeView:
    """一次装配的结果：哪一轮、判成什么、分歧是什么。"""

    #: 判词来自哪个前序 run（`None` = 没有前序）。
    prior_run_id: str | None
    #: 面板的建议性结论（`None` = 平票 / 无票 / 单评审 —— 与 `aggregate_panel` 同口径）。
    advisory: str | None
    #: 票数（`verdict` → 计数，键序稳定）。
    votes: dict[str, int]
    #: 参与投票的判词数（**不含**未能归因的）。
    voters: int
    #: 分歧（逐条；无分歧 ⇒ 空元组）。平票时**每票都在**（与 `_dissent` 同口径）。
    dissent: tuple[ReviewOutcomeEntry, ...]
    #: 未能归因的判词（逐条点名理由；不折算成任何票）。
    ineligible: tuple[str, ...]
    #: 参与投票者的**执行目标**（去重排序；与 `PanelVerdict.targets` 同源）。
    #: 它回答「这一轮是谁判的」—— 没有它，「两个模型判出分歧」与「一个模型自言自语」
    #: 在读数上不可区分。
    targets: tuple[str, ...]
    #: 这一段的**可读理由**（第一轮 / 读不到可归因判词 / 正常搬运）。
    reason: str

    @property
    def empty(self) -> bool:
        """没有可搬运的内容（⇒ 提示词里**没有**那一段，逐字回到既有形态）。"""
        return not self.prior_run_id or (self.voters == 0 and not self.ineligible)


def _detail(finding: Any, limit: int) -> tuple[str, bool]:
    """该判词自述的 findings → 一行有界文本（**逐条**保留，不摘要）。"""
    items = tuple(str(item) for item in (getattr(finding, "findings", ()) or ()))
    text = "; ".join(items)
    if len(text) <= limit:
        return text, False
    return text[:limit], True


def _entry(finding: Any, limit: int) -> ReviewOutcomeEntry:
    detail, truncated = _detail(finding, limit)
    return ReviewOutcomeEntry(
        speaker=str(getattr(finding, "reviewed_by", None) or getattr(finding, "id", "") or ""),
        verdict=str(getattr(finding, "verdict", "") or "").strip().upper(),
        target=getattr(finding, "reviewer_model", None),
        detail=detail,
        truncated=truncated,
    )


def _dissent_entries(
    panel: PanelVerdict, findings: tuple[Any, ...], limit: int, max_dissent: int
) -> tuple[ReviewOutcomeEntry, ...]:
    """面板的分歧 → 逐条投影（**按 `dissent` 的 `speaker:verdict` 串对齐回原 finding**）。

    对齐方式：`_dissent` 吐的是 `"{speaker}:{VERDICT}"`，而 `speaker` 就是
    `reviewed_by or id` ⇒ 用同一口径反查回 finding，拿到它的 `findings` 正文。
    反查不到（理论上不该发生）⇒ 只给 `speaker`/`verdict`，**不编造正文**。
    """
    index = {
        f"{str(getattr(item, 'reviewed_by', None) or getattr(item, 'id', '') or '')}:"
        f"{str(getattr(item, 'verdict', '') or '').strip().upper()}": item
        for item in findings
    }
    entries: list[ReviewOutcomeEntry] = []
    for label in panel.dissent[:max_dissent]:
        matched = index.get(label)
        if matched is None:
            speaker, _, verdict = label.partition(":")
            entries.append(
                ReviewOutcomeEntry(
                    speaker=speaker, verdict=verdict, target=None, detail="", truncated=False
                )
            )
            continue
        entries.append(_entry(matched, limit))
    return tuple(entries)


def _empty(reason: str, prior_run_id: str | None = None) -> ReviewOutcomeView:
    """一个**没有可搬运内容**的视图（`reason` 逐字说明是哪一种「没有」）。

    三种形态共用一个构造点，但 `reason` **各不同**：没有前序 run / 有前序但读不到可归因
    判词 / 本 run 行还没落库 —— 三态**不得**合并成同一句话（合并会让读者以为
    「第一轮」与「读不到」是一件事）。
    """
    return ReviewOutcomeView(
        prior_run_id=prior_run_id,
        advisory=None,
        votes={},
        voters=0,
        dissent=(),
        ineligible=(),
        targets=(),
        reason=reason,
    )


def build_review_outcome(
    runs: Any,
    findings: Any,
    *,
    run_id: str,
    max_chars: int = DEFAULT_MAX_CHARS,
    max_dissent: int = DEFAULT_MAX_DISSENT,
) -> ReviewOutcomeView:
    """`run_id` → **它所属程序的前序 run** 的评审结论（只读 canonical；零出网）。

    **本 run 的行还没落库 ⇒ 结构上就是第一轮**（与 `prior_conclusion_reader` 同一口径）：
    run 行由调用方在编排返回**之后**才写入，所以「第一轮开工时」这次查询必然查不到自己的
    行。这里**不让它变成失败**（那会让每个程序的第一轮必然失败），而是给一个**点名的**
    「行还没落库」视图 —— 与「有前序但读不到判词」严格区分（那是缺项，要 fail-closed）。
    """
    if max_chars < 1 or max_dissent < 1:
        raise ValueError("max_chars and max_dissent must be >= 1")
    try:
        run = runs.get_run(run_id)
    except KeyError:
        return _empty(f"{NO_RUN_ROW} (run {run_id})")
    program_id = getattr(run, "program_id", None)
    if not program_id:
        raise ValueError(
            f"run {run_id} belongs to no research program "
            "(the program is the read entry for a prior panel; not guessed)"
        )
    prior = [item for item in runs.for_program(program_id) if item.id.value != run_id]
    if not prior:
        return _empty(NO_PRIOR_RUN)
    last = prior[-1]  # `for_program` 按 program_index 升序 ⇒ 末位是序号最大者。
    records: tuple[ScopedReviewFinding, ...] = findings.for_run(last.id.value)
    return view_of(last.id.value, records, max_chars=max_chars, max_dissent=max_dissent)


def view_of(
    prior_run_id: str,
    records: tuple[ScopedReviewFinding, ...],
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    max_dissent: int = DEFAULT_MAX_DISSENT,
) -> ReviewOutcomeView:
    """落库记录 → 视图（与 `build_review_outcome` 分开：判据在合成记录上取证，不建 run）。"""
    findings = tuple(record.finding for record in records)
    panel = aggregate_panel(findings)
    if panel is None or panel.voters == 0:
        # 两种形态都走同一条路：
        # - **少于两份** ⇒ 单评审不聚合（既有读面口径；单条判词仍是一票，只是没有面板）；
        # - **一份都不可归因**（`panel.voters == 0`）⇒ 这是**缺项**而不是「0 票的面板」。
        #   实测：两份都没有 `reviewer_model` 的判词会让 `aggregate_panel` 返回一个
        #   `voters=0` 的**真面板**，于是 `NO_ATTRIBUTABLE` 那句点名被一个「0 vote(s)」
        #   的普通理由顶掉 —— 「读不到」与「读到了但没人能投票」必须分得开。
        return _single_or_empty(prior_run_id, findings, max_chars, max_dissent)
    dissent = _dissent_entries(panel, findings, max_chars, max_dissent)
    reason = (
        f"carried from prior run {prior_run_id}: {panel.voters} attributable vote(s), "
        f"advisory={panel.advisory or 'none (tie or no eligible vote)'}"
    )
    return ReviewOutcomeView(
        prior_run_id=prior_run_id,
        advisory=panel.advisory,
        votes=dict(panel.votes),
        voters=panel.voters,
        dissent=dissent,
        ineligible=panel.ineligible,
        targets=panel.targets,
        reason=reason,
    )


def _single_or_empty(
    prior_run_id: str,
    findings: tuple[Any, ...],
    max_chars: int,
    max_dissent: int,
) -> ReviewOutcomeView:
    """单评审（或零条）的形态：有可归因的一票就报它，没有就**点名缺项**。"""
    attributable = [
        item
        for item in findings
        if str(getattr(item, "verdict", "") or "").strip()
        and getattr(item, "reviewer_model", None) is not None
    ]
    unattributable = [
        f"{getattr(item, 'id', '')}: reviewer model is not recorded (cannot attribute this verdict)"
        for item in findings
        if getattr(item, "reviewer_model", None) is None
    ]
    if not attributable:
        return _empty(
            f"{NO_ATTRIBUTABLE} (run {prior_run_id}); {len(findings)} finding(s) read, 0 eligible",
            prior_run_id,
        )
    single = attributable[0]
    verdict = str(getattr(single, "verdict", "")).strip().upper()
    entries = tuple(_entry(item, max_chars) for item in attributable[:max_dissent])
    return ReviewOutcomeView(
        prior_run_id=prior_run_id,
        advisory=verdict if len(attributable) == 1 else None,
        votes={verdict: len(attributable)},
        voters=len(attributable),
        dissent=entries,
        ineligible=tuple(unattributable),
        targets=tuple(
            sorted({str(item.reviewer_model) for item in attributable if item.reviewer_model})
        ),
        reason=(
            f"carried from prior run {prior_run_id}: {len(attributable)} attributable vote(s); "
            "a single reviewer is not a panel (no majority is claimed)"
        ),
    )


def with_review_outcome(deps: Any, task: Any, spec_context: Any) -> Any:
    """把**上一轮评审结论**装进本任务的 spec（求值点与检索 / 前序知识 / 被评对象同一处）。

    未接装配器（`deps.review_outcome is None`）⇒ **原样返回**（既有语义逐字节不变）；
    装配器抛错 ⇒ 让异常冒到执行循环（那里的失败路径会**点名** —— 不静默给一个空段：
    那会让「上一轮被判过」与「读不到」不可区分，正是本 GOAL 要消灭的那种含混）。
    """
    build = getattr(deps, "review_outcome", None)
    if build is None:
        return spec_context
    from dataclasses import replace

    view = build(str(task.run_id.value))
    return replace(spec_context, review_outcome=view)


__all__ = [
    "DEFAULT_MAX_CHARS",
    "DEFAULT_MAX_DISSENT",
    "NO_ATTRIBUTABLE",
    "NO_PRIOR_RUN",
    "NO_RUN_ROW",
    "ReviewOutcomeEntry",
    "ReviewOutcomeView",
    "build_review_outcome",
    "view_of",
    "with_review_outcome",
]
