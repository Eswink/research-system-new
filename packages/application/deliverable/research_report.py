"""研究报告**汇编器**（GOAL-20261014-077 EC-02 / 报告域 L0 → L1）。

**它做什么**：把一次 run 的**正式持久事实**汇成一页人类可读的 markdown ——
问题与动机 / 检索与证据 / 实验与指标 / 评审与结论（含局限）。

**它不做什么**（边界，与既有 `deliverable/builder.py` 同一条纪律）：

- **只 render truth，不创造 truth**：每个数字 / 标识 / 判词都 **SELECT 自**持久状态，
  代码里**不得**出现任何被当作结论的常量；
- **读不到就点名**，不得 fallback 到合成值 —— 报告里缺哪一节要说清楚为什么缺；
- **不调模型**：本模块是**确定性汇编**（同一份持久状态 ⇒ 逐字节相同的报告）。
  模型的叙述性撰写是**另一件事**（阶梯上「报告」域的再下一级）。

**为什么需要它**：会话交付物经 `redact_text` 后**截断 500 字符**
（`adapters/openhands/event_mapping.py`），`deliverable.json` 是结构化 JSON ——
两者都**不是**人能直接读的研究报告。本模块补上这一格。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

#: 报告的四个小节标题（判据按这四条核）。
SECTION_HEADINGS: tuple[str, ...] = (
    "## 1. 问题与动机",
    "## 2. 检索与证据",
    "## 3. 实验与指标",
    "## 4. 评审与结论",
)

#: 报告制品的文件名（合约 `research_report_deliverable` 声明的名字）。
REPORT_ARTIFACT_NAME = "research_report.md"

#: 报告制品的 MIME 类型。
REPORT_MIME = "text/markdown"


class ReportBuildError(RuntimeError):
    """报告无法从正式状态构造（输入缺失 / 不一致）——**点名**，不静默降级。"""


@dataclass(frozen=True, slots=True)
class ReportInputs:
    """报告的全部正式输入（参数对象，避免函数参数超限）。

    全部字段都是**已经落库的事实**；`sources` / `metrics` / `verdict` 由调用方
    经**既有读面**取得（不是本模块去查库 —— 那会让本模块依赖具体适配器）。
    """

    run_id: str
    protocol_id: str
    state: str
    #: 检索到的来源（每条 = 一个真标识 + 它的证据 id）。
    sources: tuple[Mapping[str, str], ...]
    #: 实验指标（每条 = 名字 / 值 / 单位）。空 tuple 表示本 run 没有实验阶段。
    metrics: tuple[Mapping[str, str], ...]
    #: 评审结论（判词 + 决定）。None 表示本 run 没有评审阶段。
    verdict: Mapping[str, Any] | None
    #: 第 1 节的问题正文。GOAL-20261024-096 EC-03 起：生产路径取自**本 run 自己**的
    #: `research_question` 制品（`report_question.py` 读取面，逐字引用）；
    #: `None` = 本 run 没有该制品（渲染器把那一节写成「无 + 原因」）。
    objective: str | None
    #: 预算读数（已消费 / 上限），来自账本。
    budget: Mapping[str, str] | None = None


def _bullet_list(items: tuple[Mapping[str, str], ...], empty_reason: str) -> list[str]:
    if not items:
        return [f"- _（无：{empty_reason}）_"]
    return [f"- {dict(item)}" for item in items]


def _header_lines(inputs: ReportInputs) -> list[str]:
    """报告抬头（run / 协议 / 状态 / 目标 / 预算）。

    `state` 标成**汇编时状态**（不是「终态」）：报告是**在 run 内**汇编的，那时 run 的
    终态**尚未产生**（它由所有 phase 跑完后才定）。把它写成「终态」会让读者以为这是
    最终读数——那就把「汇编时的读数」冒充成了「结论时刻的事实」。
    """
    lines = [
        "# 研究报告",
        "",
        f"- **run**: `{inputs.run_id}`",
        f"- **协议**: `{inputs.protocol_id}`",
        f"- **汇编时状态**: `{inputs.state}`",
    ]
    if inputs.objective:
        # GOAL-20261024-096 EC-03 起，生产路径的 `objective` 来自**本 run 自己**的
        # `research_question` 制品（`report_question.py` 读取面）；逐字引用，不重述。
        lines.append(f"- **研究问题（本 run 自提；逐字引用）**: {inputs.objective}")
    if inputs.budget:
        lines.append(
            f"- **预算**: 已用 `{inputs.budget.get('consumed', '?')}` / "
            f"上限 `{inputs.budget.get('limit', '?')}`"
        )
    return [*lines, ""]


def _question_section(inputs: ReportInputs) -> list[str]:
    """第 1 节：问题与动机（GOAL-20261024-096 EC-03：问题由本 run 自己提出）。"""
    section = [SECTION_HEADINGS[0], ""]
    if inputs.objective:
        section += [
            "本 run 的研究问题由**本 run 自己**在问题相提出"
            "（逐字取自落库的 `research_question` 制品；不是操作者预填的简报，"
            "也不是汇编器改写）：",
            "",
            f"> {inputs.objective}",
        ]
    else:
        section.append(
            "_（无：本 run 没有 research_question 制品 —— 问题相未跑或未产出；"
            "本 run 也未声明协议级目标）_"
        )
    return [*section, ""]


def _evidence_section(inputs: ReportInputs) -> list[str]:
    """第 2 节：检索与证据（逐条来源 + 复核路径）。"""
    section = [
        SECTION_HEADINGS[1],
        "",
        f"经系统检索取得 **{len(inputs.sources)}** 条来源（真标识 + 内容寻址证据）：",
        "",
        *_bullet_list(inputs.sources, "本 run 没有检索阶段，或检索返回零命中"),
        "",
    ]
    if inputs.sources:
        section += [
            "> 每条来源的 `evidence_id` 可在 `GET /runs/{run_id}/evidence` 逐条复核；"
            "内容按 digest 寻址，**可重算**。",
            "",
        ]
    return section


def _experiment_section(inputs: ReportInputs) -> list[str]:
    """第 3 节：实验与指标（值取自 canonical，本报告不重算）。

    **多臂（GOAL-20261015-079 EC-02 起）**：指标行带实验标识时，表格**多一列「实验」**
    —— 一个 (指标, 实验) 一行。**为什么不能挤在一格里**：把两臂的值用分隔符连成一格
    会把表格**撑成 4 列**（markdown 表头只有 3 列）⇒ 渲染直接坏掉（本 GOAL 的 live
    取证**实测**到这一点）。逐行才是既保**可读**又保**不丢臂**的形态。
    """
    section = [SECTION_HEADINGS[2], ""]
    if inputs.metrics:
        multi_arm = any(metric.get("experiment_run_id") for metric in inputs.metrics)
        headers = "| 指标 | 值 | 单位 |" if not multi_arm else "| 指标 | 实验 | 值 | 单位 |"
        rule = "| --- | --- | --- |" if not multi_arm else "| --- | --- | --- | --- |"
        section += [
            "实验阶段产出的**实测指标**（值取自 canonical，非本报告计算）：",
            "",
            headers,
            rule,
        ]
        for metric in inputs.metrics:
            name = metric.get("name", "?")
            value = metric.get("value", "?")
            unit = metric.get("unit", "—")
            experiment = metric.get("experiment_run_id")
            if not multi_arm:
                section.append(f"| `{name}` | {value} | {unit} |")
            else:
                section.append(f"| `{name}` | `{experiment or '?'}` | {value} | {unit} |")
    else:
        section.append("_（无：本 run 没有实验阶段，或实验未产出指标）_")
    return [*section, ""]


def _review_section(inputs: ReportInputs) -> list[str]:
    """第 4 节：评审与结论 + 局限（自陈汇编而非撰写；缺来源/缺指标时明写）。"""
    section = [SECTION_HEADINGS[3], ""]
    if inputs.verdict:
        verdict = dict(inputs.verdict)
        section.append(f"- **决定**: `{verdict.get('decision', '?')}`")
        if verdict.get("reason"):
            section.append(f"- **判词**: {verdict['reason']}")
        for fact in verdict.get("cited_facts") or ():
            section.append(f"- **依据**: `{fact}`")
    else:
        section.append("_（无：本 run 没有评审阶段）_")
    section += [
        "",
        "**局限（如实登记）**：",
        "",
        "- 本报告是**确定性汇编**（同一份持久状态 ⇒ 逐字节相同），**不是**模型的叙述性撰写。",
        "- 报告只覆盖**本 run**：跨 run 的结论不在其中。",
        "- 发现 / 结论的**可靠性**取决于上游各 phase 的判据，本报告不重新判定它们。",
    ]
    if not inputs.sources:
        section.append("- **本 run 没有真实检索来源** ⇒ 上述结论没有外部证据支持。")
    if not inputs.metrics:
        section.append("- **本 run 没有实测指标** ⇒ 上述结论没有实验支持。")
    return [*section, ""]


def build_research_report(inputs: ReportInputs) -> str:
    """把正式事实汇成 markdown 报告（确定性：同输入 ⇒ 逐字节相同）。

    **每一节都必须能读出来**：读不到的事实写成「无 + 原因」，**不得**省略该节
    （节的存在本身就是契约的一部分 —— 判据按四条标题核）。
    """
    if not inputs.run_id.strip():
        raise ReportBuildError("report requires a non-empty run_id")
    if not SECTION_HEADINGS[0].startswith("## "):  # pragma: no cover - 契约自检
        raise ReportBuildError("section headings must be level-2 markdown")
    lines = (
        _header_lines(inputs)
        + _question_section(inputs)
        + _evidence_section(inputs)
        + _experiment_section(inputs)
        + _review_section(inputs)
    )
    return "\n".join(lines).rstrip("\n") + "\n"


def report_digest_payload(report: str) -> bytes:
    """报告制品的字节（供 ArtifactStore 内容寻址）。"""
    return report.encode("utf-8")


def report_metadata(inputs: ReportInputs, narrative: Any | None = None) -> str:
    """报告的同源元数据（JSON；供读面与判据核对，不进报告正文）。

    `narrative`（GOAL-20261022-062）：模型撰写正文时的归因面；缺省 `None` ⇒ 键集
    **逐字不变**（既有确定性汇编的元数据零回归）。
    """
    payload: dict[str, Any] = {
        "run_id": inputs.run_id,
        "protocol_id": inputs.protocol_id,
        "source_count": len(inputs.sources),
        "metric_count": len(inputs.metrics),
        "has_verdict": inputs.verdict is not None,
        "sections": list(SECTION_HEADINGS),
    }
    if narrative is not None:
        payload["narrative"] = {
            "author": narrative.author,
            "returned_model": narrative.returned_model,
            "digest": narrative.digest,
        }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


__all__ = [
    "REPORT_ARTIFACT_NAME",
    "REPORT_MIME",
    "SECTION_HEADINGS",
    "ReportBuildError",
    "ReportInputs",
    "build_research_report",
    "report_digest_payload",
    "report_metadata",
]
