"""手稿的**外部评审面板**（GOAL-20261107-107 EC-06 / EC-07；`MANUSCRIPT_QUALITY.md` §7 的出路 ①）。

**它补哪一格**：§7 用 P1–P4 四条依据把 `NOT_JUDGED` 的五项逐项判过 —— 第 1/2/3 项
（引用是否**支持**那句话 / 论证是否成立 / 方法学是否合适）被判定为**只能人评**，理由都是
缺 P3（需要被引全文、需要形式化整篇论证、需要领域知识）。§7 自己写的出路是：把它们交给
真人或**独立模型**，并在读面标注**谁**判的（与 `ReviewFinding.reviewer_model` 同一口径）。

**本模块只做这条出路的第一步**：给“独立模型判一次”提供**机制**。

**三条硬边界**（逐条可判，缺一条这个模块就变成冒充）：

1. **不产生 `Decision`**。面板判词是 advisory：它落 `ReviewFinding`，**不**写 `Decision`、
   **不**参与验收门。通过也不是「论证成立」（P4：必要不充分）。
2. **设施失败不折算**。网关超时 / 鉴权 / 中转站不可用 ⇒ `PANEL_UNAVAILABLE`，
   **绝不**变成 `SUPPORTED` 或 `REFUTED`（照 `evaluation/reviewer.py` 的既有纪律：
   评测设施失败不是被评对象不合格）。
3. **不改 `NOT_JUDGED`**。五项逐字不动 —— 确定性模块 `manuscript_quality` 仍然不判这三项；
   面板是**另一个**判者，不是确定性判据上线。

**为什么直调 `ModelGateway.complete` 而不走 AgentRuntime**：这是**一次判定调用**，没有工具、
没有多轮、没有工作区。照 `report_narrative_task.llm_narrator` 已验证的形态：一个闭包、
一次 `complete`、把返回的模型名记进归因面（同名漂移可见，AGENTS.md §4）。
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

#: 面板判据的**闭集**（三条，逐条对应 `NOT_JUDGED` 的第 1/2/3 项）。
#:
#: 与那三项的对应关系是**按语义**而不是按下标：`NOT_JUDGED` 是给读者的射程声明，本闭集是
#: 给模型的提问面 —— 两者的措辞可以不同，但**不得**多出第四条（那会越过 §7 的判定）。
PANEL_RUBRICS: tuple[tuple[str, str], ...] = (
    (
        "citation_supports_sentence",
        "Does each cited reference actually SUPPORT the sentence it is attached to, "
        "rather than merely sharing vocabulary with it?",
    ),
    (
        "argument_holds",
        "Does the argument hold: are the premises sufficient, the inference valid, "
        "and the conclusion supported by what was shown?",
    ),
    (
        "method_appropriate",
        "Is the method appropriate for the question this manuscript asks?",
    ),
)

#: 判词闭集（三态）。**设施失败不在这里** —— 它是另一类（见 `PANEL_UNAVAILABLE`）。
VERDICTS: tuple[str, ...] = ("SUPPORTED", "REFUTED", "AMBIGUOUS")

#: 设施失败的点名值（**不是**一个判词态）。
PANEL_UNAVAILABLE = "PANEL_UNAVAILABLE"

_VERDICT_BY_TOKEN: Mapping[str, str] = {
    "SUPPORTED": "SUPPORTED",
    "SUPPORTS": "SUPPORTED",
    "REFUTED": "REFUTED",
    "REFUTES": "REFUTED",
    "AMBIGUOUS": "AMBIGUOUS",
    "UNCLEAR": "AMBIGUOUS",
}


class PanelError(ValueError):
    """面板输入不可用（未知 rubric / 空正文）—— **点名**，不猜。"""


@dataclass(frozen=True, slots=True)
class PanelVerdict:
    """一条面板判词（三条 rubric 各一条）。"""

    #: 判据 id（`PANEL_RUBRICS` 里的第一个元素）。
    rubric_id: str
    #: 三态之一，或 `PANEL_UNAVAILABLE`（设施失败）。
    verdict: str
    #: 模型自己写的一句话理由（原文，不改写）。
    rationale: str
    #: **谁判的**：`<endpoint>/<model_name>`（供应商**返回**的名字，不是我们请求的名字）。
    reviewer_model: str | None

    @property
    def is_facility_failure(self) -> bool:
        """是否是**设施**失败（而不是对稿子的判断）。"""
        return self.verdict == PANEL_UNAVAILABLE

    @property
    def is_judgement(self) -> bool:
        """是否是一条真正的判断（三态之一）。"""
        return self.verdict in VERDICTS


def rubric_by_id(rubric_id: str) -> str:
    """rubric id → 提示词问题；未知 id ⇒ **点名拒绝**（不回落、不猜）。"""
    for known, question in PANEL_RUBRICS:
        if known == rubric_id:
            return question
    raise PanelError(
        f"unknown panel rubric {rubric_id!r}; the closed set is "
        f"{[known for known, _ in PANEL_RUBRICS]}"
    )


def panel_prompt(rubric_id: str, manuscript_excerpt: str) -> str:
    """一条 rubric 的完整提示词（**只发相关节 + 问题**，不发整份产物）。

    `manuscript_excerpt` 由调用方给（`manuscript_excerpts` 从正文切）；空正文 ⇒ 点名拒绝 ——
    拿空字符串去问模型，答案只反映模型的先验，不反映这篇稿子。
    """
    question = rubric_by_id(rubric_id)
    if not manuscript_excerpt.strip():
        raise PanelError(
            f"panel rubric {rubric_id!r} received an empty excerpt: "
            "a judgement about no text is not a judgement about this manuscript"
        )
    return (
        "You are an independent reviewer of a scientific manuscript. "
        "Judge ONLY what is written below; do not assume facts that are not there.\n\n"
        f"Question: {question}\n\n"
        "Answer with exactly one verdict token on the first line "
        "(SUPPORTED, REFUTED or AMBIGUOUS), then a one-sentence rationale.\n\n"
        "--- MANUSCRIPT EXCERPT ---\n"
        f"{manuscript_excerpt.strip()}\n"
        "--- END EXCERPT ---\n"
    )


def parse_panel_verdict(text: str | None) -> tuple[str, str]:
    """模型正文 → `(verdict, rationale)`；认不出判词 ⇒ `AMBIGUOUS`（**不猜成通过**）。

    三态之外的任何输出都落到 `AMBIGUOUS`：那是「模型没给出可用判断」，与「模型说论证成立」
    是两件事。设施失败由调用方用 `PANEL_UNAVAILABLE` 表达，**不经过本函数**。
    """
    body = (text or "").strip()
    if not body:
        return "AMBIGUOUS", ""
    lines = body.splitlines()
    head = lines[0].upper()
    for token, verdict in _VERDICT_BY_TOKEN.items():
        if token in head:
            rationale = " ".join(lines[1:]).strip()
            return verdict, rationale
    return "AMBIGUOUS", body


def manuscript_excerpts(sections: Mapping[str, str], *, limit: int = 4000) -> Mapping[str, str]:
    """按 rubric 切出**有界**摘录（三条 rubric 看不同的节）。

    **为什么分开切**：三个问题看的面不同 —— 引用支持看 Results/Discussion（主张与证据），
    论证成立看全文，方法学看 Methods。把整篇发给每条 rubric 会让「判词」与「哪一段」脱钩。
    """
    joined = "\n\n".join(f"## {key}\n{value}" for key, value in sections.items() if value.strip())
    claims = "\n\n".join(
        f"## {key}\n{sections.get(key, '')}"
        for key in ("results", "discussion")
        if sections.get(key)
    )
    methods = str(sections.get("methods") or "")
    return {
        "citation_supports_sentence": claims[:limit],
        "argument_holds": joined[:limit],
        "method_appropriate": (methods or joined)[:limit],
    }


def review_manuscript(
    *,
    gateway: Any,
    endpoint: Any,
    credential: Any,
    model_name: str,
    sections: Mapping[str, str],
) -> tuple[PanelVerdict, ...]:
    """三条 rubric 各调一次模型 ⇒ 三条判词（**永不抛**，失败落 `PANEL_UNAVAILABLE`）。

    `gateway.complete` 的任何异常都折成 `PANEL_UNAVAILABLE` + 例外文本，理由与
    `evaluation/reviewer.py` 相同：**设施失败不得被读成对稿子的判断**。

    `reviewer_model` 取**返回**的模型名（供应商可能替换真实模型 ⇒ 同名漂移必须可见，
    AGENTS.md §4）；返回名缺席 ⇒ `None`（**不**回落到我们请求的名字 —— 那会把漂移藏起来）。
    """
    from packages.application.ports.model_gateway import CompletionRequest

    excerpts = manuscript_excerpts(sections)
    endpoint_id = getattr(endpoint, "id", None)
    verdicts: list[PanelVerdict] = []
    for rubric_id, _question in PANEL_RUBRICS:
        verdicts.append(
            _one_verdict(
                gateway=gateway,
                endpoint=endpoint,
                credential=credential,
                model_name=model_name,
                rubric_id=rubric_id,
                excerpt=excerpts[rubric_id],
                endpoint_id=endpoint_id,
                request_type=CompletionRequest,
            )
        )
    return tuple(verdicts)


def _one_verdict(  # noqa: PLR0913 - 一次调用的全部输入；缺一个就得让调用方先拼对象
    *,
    gateway: Any,
    endpoint: Any,
    credential: Any,
    model_name: str,
    rubric_id: str,
    excerpt: str,
    endpoint_id: Any,
    request_type: Any,
) -> PanelVerdict:
    """一条 rubric 的一次调用（失败 ⇒ `PANEL_UNAVAILABLE`，**绝不**折算成判词）。"""
    try:
        prompt = panel_prompt(rubric_id, excerpt)
        result = gateway.complete(
            endpoint,
            credential,
            request_type(model=model_name, messages=[{"role": "user", "content": prompt}]),
        )
    except Exception as error:  # noqa: BLE001 - 设施失败单独一类，绝不折算成判词
        return PanelVerdict(
            rubric_id=rubric_id,
            verdict=PANEL_UNAVAILABLE,
            rationale=f"{type(error).__name__}: {error}",
            reviewer_model=None,
        )
    verdict, rationale = parse_panel_verdict(result.content)
    returned = result.returned_model_name
    return PanelVerdict(
        rubric_id=rubric_id,
        verdict=verdict,
        rationale=rationale,
        reviewer_model=f"{endpoint_id}/{returned}" if endpoint_id and returned else None,
    )


def panel_summary(verdicts: Sequence[PanelVerdict]) -> Mapping[str, int]:
    """票数摘要（**含设施失败那一类**，分开数 —— 它不进票）。"""
    counts: dict[str, int] = {verdict: 0 for verdict in VERDICTS}
    counts[PANEL_UNAVAILABLE] = 0
    for item in verdicts:
        counts[item.verdict] = counts.get(item.verdict, 0) + 1
    return counts


class PanelState(StrEnum):
    """一条面板判词的稳定读面形态（落 `ReviewFinding.verdict` 用）。"""

    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    AMBIGUOUS = "AMBIGUOUS"
    UNAVAILABLE = PANEL_UNAVAILABLE


#: 面板判词的 `ReviewFinding.review_type`（读面据此与验收门 `acceptance_gate` 分开）。
PANEL_REVIEW_TYPE = "manuscript_panel"


def as_review_findings(
    verdicts: Sequence[PanelVerdict], *, run_id: str, reviewed_at: Any
) -> tuple[Any, ...]:
    """面板判词 → `ReviewFinding` 元组（**只构造对象，不落库**）。

    **为什么只构造**：落库要 `EvidenceLedger`，那是调用方的装配面；本模块保持纯函数，
    才可跨树复现。落库点由装配方决定（与 `review_outcome` 读同一个投影）。

    三条口径：

    1. `review_type = "manuscript_panel"` —— 与验收门（`acceptance_gate`）分开，读面不会
       把第三方意见读成验收结论。
    2. `reviewed_by = "model:<endpoint>/<returned>"` —— 与 `Artifact.created_by` 同形态，
       「谁判的」在人读面上直接可见。
    3. 设施失败（`PANEL_UNAVAILABLE`）**照样落一条 finding**，但 `verdict` 是它自己，
       `reviewer_model` 为 `None` —— 「无归因」与「判了」分得开（`panel_verdict._eligible`
       会把它点名为不可投票，而不是折算成任何一态）。
    """
    from packages.domain.evidence import ReviewFinding

    findings: list[Any] = []
    for item in verdicts:
        speaker = item.reviewer_model
        findings.append(
            ReviewFinding(
                id=f"finding:{run_id}:panel:{item.rubric_id}",
                review_type=PANEL_REVIEW_TYPE,
                verdict=item.verdict,
                findings=[f"{item.rubric_id}: {item.rationale}"],
                reviewed_by=f"model:{speaker}" if speaker else None,
                reviewed_at=reviewed_at,
                reviewer_model=speaker,
            )
        )
    return tuple(findings)


__all__ = [
    "PANEL_REVIEW_TYPE",
    "PANEL_RUBRICS",
    "PANEL_UNAVAILABLE",
    "VERDICTS",
    "PanelError",
    "PanelState",
    "PanelVerdict",
    "as_review_findings",
    "manuscript_excerpts",
    "panel_prompt",
    "panel_summary",
    "parse_panel_verdict",
    "review_manuscript",
    "rubric_by_id",
]
