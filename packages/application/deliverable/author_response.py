"""**评审点**与**逐条应答**：把「评审判词」变成可被逐条回应的条目（GOAL-20261029-100 EC-03）。

**它补哪一格**（建档实测）：`ReviewFinding.findings` 是**扁平的判据渲染串**
（`["EVIDENCE_COVERAGE: 2 >= 1", …]`），**没有可应答的条目 id**；审稿人正文里的
`weakest_link` 从未被解析成记录；`rebuttal` 全仓零命中。于是「作者逐条回应审稿意见、
编辑据此判断返修是否到位」这条闭环**在结构上不存在** —— 不是没人写，是没有地方写。

本模块提供闭环的**底座**（不提供改稿本身）：

1. **评审点**（`ReviewPoint`）：`point_id` + `severity` + `text`。点从**本 run 已落库的
   评审产物**派生（`points_of`），不新造一条查询、也不改 `review_findings` 表；
2. **应答**（`AuthorResponse`）：`point_id` → `response` → `action_taken`；
3. **判据**（`validate_responses`）：三条各自点名 ——
   ① **漏答**：有评审点却没有任何应答；② **编造**：应答引用了不存在的 `point_id`；
   ③ **重复**：同一个 `point_id` 被应答两次（「一条意见两个互相矛盾的答复」不可执行）。

**`point_id` 的形态与稳定性**：`P{序号}`（`P1`、`P2`…），序号 = 该点在**排序后**的点表里
的位置。排序键是 `(reviewer, text)`（不是列表顺序、不是 uuid、不是时间）—— 同一份
评审产物**逐字节相同**时点表逐字节相同，而两次 run 之间不承诺 id 可比（那是「返修
闭环完整版」要的 artifact 版本/父指针，属下一轮）。

**为什么 `severity` 是闭集而不是自由文本**：`must_fix` / `should_fix` / `nice_to_have`
三档决定「返修是否到位」按哪几档核（`must_fix` 没答完就不能算返修完成）。自由文本下
「严重性」不可比较，那三档就退化成一个装饰字段。

**零出网 / 零模型 / 零时钟**：输入是已落库的字节，输出是纯文本。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

# `declared_object` 在**函数内**延迟导入（见 `parse_responses`）：它住在
# `run_orchestration` 包，而那个包的 `review_points` 又要 import 本模块（装配相需要
# 点表）。模块级互相导入会在本模块初始化途中把 `RESPONSE_ARTIFACT_NAME` 变成半初始化
# 的属性（实测 `ImportError: cannot import name … from partially initialized module`）。

#: 应答契约的评审**类型**判别：验收门的判据行**不是**评审意见（见 `points_of`）。
ACCEPTANCE_GATE_TYPE = "acceptance_gate"

#: 严重性闭集（三档；顺序即「从最要紧到最不要紧」）。
SEVERITIES: tuple[str, ...] = ("must_fix", "should_fix", "nice_to_have")

#: 应答里必须有的三个键（**逐字**；合约与判据按它们定位）。
POINT_ID_FIELD = "point_id"
RESPONSE_FIELD = "response"
ACTION_FIELD = "action_taken"
#: 应答块的顶层键。
RESPONSES_KEY = "author_responses"

#: 应答信的文件名（合约 `author_response` 声明的产物）。
RESPONSE_LETTER_NAME = "response_letter.md"
#: 作者应答**会话产物**的名字（手稿正文制品同形：`<task>:author_responses`）。
#: 应答信由它派生，所以两个名字必须分得开：一个是模型写的，一个是汇编器写的。
RESPONSE_ARTIFACT_NAME = "author_responses"
#: 评审交付物的产物名（点表的**来源**：审稿人在 `weakest_link` 里写下它的意见）。
REVIEW_DECISION_NAME = "review_decision"


class ResponseError(RuntimeError):
    """应答不可用（漏答 / 编造 id / 重复 / 越界严重性）—— **点名**，不回落。"""


@dataclass(frozen=True, slots=True)
class ReviewerRemark:
    """一位评审者写下的一条**意见**（进点表之前的那一层；`text` 是原文）。"""

    reviewer: str
    text: str
    severity: str = ""


#: 审稿人正文里承载「弱点」的那两个键（`review_decision` 的既有形状）。
WEAKEST_LINK_FIELD = "weakest_link"
#: 评审判词格（`PASS` / `REJECT`）不构成「要点」——但**判负**的那一位说出的弱点更重。
REJECT_VERDICT = "REJECT"


def remarks_of(decision_payloads: Iterable[tuple[str, Any]]) -> tuple[ReviewerRemark, ...]:
    """本 run 的**评审产物** → 逐条意见（`(审稿人, 产物载荷)` 序列进）。

    **它补的缺口（建档实测）**：`ReviewFinding.findings` 是**扁平的判据渲染串**
    （`EVIDENCE_COVERAGE: 2 >= 1`），而审稿人真正写下的那句话（`review_decision` 里的
    `weakest_link`）**从未被解析成记录**。本函数就是那条解析：审稿人说的一行弱点 →
    一条 `ReviewerRemark`。

    **两种载体都认**（同一份评审产物的两个面）：
    1. `weakest_link`（合约规定的单句弱点）—— 一定有；
    2. 判词里自述的 `findings[]`（若有）—— 逐条，也不丢。

    判负（`REJECT`）的审稿人提出的点按 `must_fix`；其余按 `should_fix`。这条映射是
    **机械的**（只看判词那个词），不读正文含义 —— 读语义是「叙述质量」那一面。
    """
    remarks: list[ReviewerRemark] = []
    for reviewer, payload in decision_payloads:
        block = payload if isinstance(payload, Mapping) else {}
        severity = (
            "must_fix"
            if str(block.get("verdict") or "").upper() == REJECT_VERDICT
            else "should_fix"
        )
        weakest = str(block.get(WEAKEST_LINK_FIELD) or "").strip()
        if weakest:
            remarks.append(ReviewerRemark(reviewer=reviewer, text=weakest, severity=severity))
        for raw in block.get("findings") or ():
            text = str(raw or "").strip()
            if text:
                remarks.append(ReviewerRemark(reviewer=reviewer, text=text, severity=severity))
    return tuple(remarks)


@dataclass(frozen=True, slots=True)
class ReviewPoint:
    """一条**可被回应**的评审点（`point_id` 稳定、`severity` 闭集、`text` 是原文）。"""

    point_id: str
    severity: str
    text: str
    #: 这条意见出自谁（`reviewed_by`；缺失 ⇒ 空串，不伪造身份）。
    reviewer: str = ""

    def as_payload(self) -> dict[str, object]:
        return {
            "point_id": self.point_id,
            "severity": self.severity,
            "text": self.text,
            "reviewer": self.reviewer,
        }


@dataclass(frozen=True, slots=True)
class AuthorResponse:
    """作者对**一个**评审点的回应（说了怎么改 + 实际做了什么）。"""

    point_id: str
    response: str
    action_taken: str


def points_of(records: Iterable[Any]) -> tuple[ReviewPoint, ...]:
    """本 run 的**评审产物** → 有序点表（`P1…Pn`；空 ⇒ 空元组，不是失败）。

    **点的来源是评审产物**（`review_decision` 的 `weakest_link` 与自述意见）：它是
    审稿人**真的说了什么**。**不**取自 `ReviewFinding` 的验收门判据行
    （`EVIDENCE_COVERAGE: 2 >= 1`）—— 那是**机读判据**，把它算成「评审点」会让作者去
    「回应」一条判据字符串，而不是回应人。

    **排序键 `(reviewer, text)`**：同一份评审产物的点表在两次装配里**逐字节相同**
    （`for_run` 的 `finding_id` 序含执行期 uuid ⇒ 不能拿它当顺序）。`point_id` 因此
    对**同一份产物**稳定，跨 run 不可比 —— 如实登记的边界。
    """
    items: list[tuple[str, str, str]] = []
    for item in records:
        reviewer = str(getattr(item, "reviewer", "") or "")
        text = str(getattr(item, "text", "") or "").strip()
        if not text:
            continue
        items.append((reviewer, text, str(getattr(item, "severity", "") or _severity_of(text))))
    items.sort(key=lambda item: (item[0], item[1]))
    return tuple(
        ReviewPoint(point_id=f"P{index}", severity=severity, text=text, reviewer=reviewer)
        for index, (reviewer, text, severity) in enumerate(items, start=1)
    )


def _severity_of(text: str) -> str:
    """判据渲染串 → 严重性（**按名字点名**，不猜语义）。

    验收门的判据行以 `FAIL` / `PASS` 开头（`EvaluationReason` 的渲染形态）——
    **不通过的那几条**是必须修的（`must_fix`）；其余按 `should_fix`。这条映射是
    **机械的**（只看行首那个词），不读正文含义 —— 读语义是「叙述质量」那一面，
    不在本模块射程内。
    """
    head = text.split(":", 1)[0].strip().upper()
    if head.startswith("FAIL") or " FAIL" in head:
        return "must_fix"
    return "should_fix"


def parse_responses(content: str | None) -> tuple[AuthorResponse, ...]:
    """模型输出 → 逐条应答（**信封 + 围栏 JSON 块**都经既有同一处解开）。"""
    if content is None or not str(content).strip():
        raise ResponseError("author response artifact is empty")
    parsed = _loads(content)
    if RESPONSES_KEY not in parsed:
        from packages.application.run_orchestration.phase_input_material import declared_object

        try:
            parsed = declared_object(parsed, key=RESPONSES_KEY)
        except Exception as error:  # noqa: BLE001 - 统一折成点名（含 InvalidInputError）
            raise ResponseError(
                f"author response carries no {RESPONSES_KEY!r} block: {error}"
            ) from error
    raw = parsed.get(RESPONSES_KEY)
    if not isinstance(raw, (list, tuple)):
        raise ResponseError(
            f"{RESPONSES_KEY} must be a list of response objects, got {type(raw).__name__}"
        )
    return tuple(_response_of(item) for item in raw)


def _loads(content: str) -> Mapping[str, Any]:
    try:
        parsed: Any = json.loads(content)
    except ValueError as error:
        raise ResponseError(f"author response is not a JSON object: {error}") from error
    if not isinstance(parsed, Mapping):
        raise ResponseError(f"author response must be a JSON object, got {type(parsed).__name__}")
    return parsed


def _response_of(item: Any) -> AuthorResponse:
    if not isinstance(item, Mapping):
        raise ResponseError(
            f"each {RESPONSES_KEY} entry must be an object, got {type(item).__name__}"
        )
    point_id = str(item.get(POINT_ID_FIELD) or "").strip()
    if not point_id:
        raise ResponseError(f"a response carries no {POINT_ID_FIELD}: it cannot be matched")
    response = str(item.get(RESPONSE_FIELD) or "").strip()
    action = str(item.get(ACTION_FIELD) or "").strip()
    if not response:
        raise ResponseError(f"response for {point_id} is empty: it says nothing about the point")
    return AuthorResponse(point_id=point_id, response=response, action_taken=action)


def validate_responses(
    points: tuple[ReviewPoint, ...], responses: tuple[AuthorResponse, ...]
) -> None:
    """三条判据各**点名**：编造 id / 重复应答 / 漏答（顺序固定，判词稳定）。

    为什么「漏答」在**有评审点**时才判：一份没有评审点的 run（评审全过）本来就没有
    要回应的东西 —— 那时空应答是**正确**读数，不是漏答。
    """
    known = {point.point_id for point in points}
    invented = sorted({item.point_id for item in responses} - known)
    if invented:
        raise ResponseError(
            f"responses reference point ids this review never raised: {invented} "
            f"(the review's points are {sorted(known)})"
        )
    seen: dict[str, int] = {}
    for item in responses:
        seen[item.point_id] = seen.get(item.point_id, 0) + 1
    duplicated = sorted(point_id for point_id, count in seen.items() if count > 1)
    if duplicated:
        raise ResponseError(
            f"points answered more than once: {duplicated} (one point, one answer — "
            "two answers to one point cannot be acted on)"
        )
    unanswered = [point.point_id for point in points if point.point_id not in seen]
    if unanswered:
        raise ResponseError(
            f"the review raised {len(points)} point(s) and {len(unanswered)} went unanswered: "
            f"{unanswered}"
        )


def response_letter(points: tuple[ReviewPoint, ...], responses: tuple[AuthorResponse, ...]) -> str:
    """点表 + 应答 → `response_letter.md`（**逐条**一条意见一段；已校验）。

    已校验是刻意的：生成一份「看起来像应答信」但漏答的文档，比不生成更糟 —— 读者会
    把它当成返修完成的证据。
    """
    validate_responses(points, responses)
    by_id = {item.point_id: item for item in responses}
    lines = ["## Response to Review", ""]
    if not points:
        lines.append("_This run's review raised no points to answer._")
        return "\n".join(lines)
    for point in points:
        answer = by_id[point.point_id]
        lines += [
            f"### {point.point_id} ({point.severity})",
            "",
            f"> {point.text}",
            "",
            f"**Response.** {answer.response}",
            "",
            f"**Action taken.** {answer.action_taken or '_(none stated)_'}",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def review_remarks(
    artifacts: Any, evidence: Iterable[Any], *, key: str = REVIEW_DECISION_NAME
) -> tuple[ReviewerRemark, ...]:
    """本 run 的**评审交付物** → 逐条意见（`(artifacts, evidence)` 两个 Port 进）。

    读取面与 `references.reference_table` 同一手法（证据投影 → 该产物名的制品 →
    **解包**信封/围栏块），**不**新造第二条查询；`declared_object` 是解包的唯一实现。

    **确定性**：制品按 id 排序后逐条读 ⇒ 同一份持久状态给出同一份意见序列（顺序无关，
    因为 `points_of` 还要按 `(reviewer, text)` 再排一次）。
    """
    from packages.application.run_orchestration.phase_input_material import declared_object

    ids = sorted({
        str(item.artifact_id)
        for item in evidence
        if str(item.artifact_id or "").endswith(f":{key}")
    })
    payloads: list[tuple[str, Any]] = []
    for artifact_id in ids:
        if artifacts.meta(artifact_id) is None:
            continue
        try:
            parsed: Any = json.loads(artifacts.get(artifact_id).decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            continue
        block = declared_object(parsed, key=key) if isinstance(parsed, Mapping) else None
        if not isinstance(block, Mapping):
            continue
        inner = block.get(key)
        reviewer = artifact_id.rsplit(":", 2)[-2] if artifact_id.count(":") >= 2 else artifact_id
        payloads.append((reviewer, inner if isinstance(inner, Mapping) else block))
    return remarks_of(payloads)


__all__ = [
    "ACTION_FIELD",
    "AuthorResponse",
    "POINT_ID_FIELD",
    "RESPONSES_KEY",
    "RESPONSE_FIELD",
    "RESPONSE_LETTER_NAME",
    "ResponseError",
    "ReviewPoint",
    "SEVERITIES",
    "parse_responses",
    "points_of",
    "response_letter",
    "validate_responses",
]
