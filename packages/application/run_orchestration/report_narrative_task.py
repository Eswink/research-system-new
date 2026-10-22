"""报告叙述的**执行缝**（GOAL-20261022-062；与 `report_task.py` 的汇编面并列）。

**为什么单列**：`report_task.py` 贴 450 行硬上限，而「让模型写正文」这件事有它自己的
一组失败形态（模型不可用 / 输出畸形 / 写了数字），把它们塞进汇编面会让两件事的
判据糊在一起。本模块只做三件：

1. **`narrate`**：把已读好的 `ReportInputs` 交给一个**可注入的叙述者**，取回
   `NarrativeAdmission` + 报告正文；叙述者的异常**原样上抛**（由派发面归类失败）。
2. **`llm_narrator`**：产品闭包 —— 经 `ModelGateway` + `CredentialResolver` 调一次模型，
   把返回值收成 `NarrativeAdmission`（**执行者身份与返回名都记下来**，见 AGENTS.md §4）。
3. **`NarratorUnavailable`**：装配方拿不到端点 / 凭据时的**点名**形态（不是编造一个空的
   叙述者，也不是静默回退到确定性汇编 —— 那会让「谁写的」不可判）。

**边界**：本模块**不读** canonical（事实由 `report_facts` 读出后传进来），
**不判**叙述的科学质量（那需要人评），也**不重算**任何数字。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from packages.application.deliverable.report_narrative import (
    NarrativeAdmission,
    build_narrative_report,
    narrative_digest,
    narrative_prompt,
    parse_narrative,
    validate_narrative,
)
from packages.application.deliverable.research_report import ReportInputs

#: 叙述者：给任务书，回一份**已归因**的叙述。
Narrator = Callable[[str], NarrativeAdmission]


class NarratorUnavailable(RuntimeError):
    """装配面拿不到模型 / 凭据 —— **点名**（不静默回退到确定性汇编）。"""


@dataclass(frozen=True, slots=True)
class NarratedReport:
    """一次模型撰写的成品：报告字节 + 它的归因面。"""

    report: str
    admission: NarrativeAdmission


def narrate(inputs: ReportInputs, narrator: Narrator) -> NarratedReport:
    """读好的事实 → （模型叙述）→ 报告正文。叙述者抛错 ⇒ 原样上抛。"""
    admission = narrator(narrative_prompt(inputs, _names_only(inputs)))
    return NarratedReport(report=build_narrative_report(inputs, admission), admission=admission)


def _names_only(inputs: ReportInputs) -> tuple[dict[str, str], ...]:
    """任务书里只给**类别与名称**（标识符与值都不发给模型 ⇒ 它无从复述一个数字）。"""
    from packages.application.deliverable.report_narrative import fact_ledger

    return tuple({"类别": row["类别"], "名称": row["名称"]} for row in fact_ledger(inputs))


def llm_narrator(
    *,
    gateway: Any,
    credentials: Any,
    endpoint: Any,
    model_name: str,
    credential_ref: str,
) -> Narrator:
    """产品闭包：一次 `complete` 调用 → `NarrativeAdmission`。

    **不吞异常**：网关故障（鉴权 / 限流 / 中转站不可用）由调用方归类 —— 在这里把它
    变成一句话会让失败类别丢失（AGENTS.md §4 要求 drift 可见，失败类别同理）。
    凭据解析失败 ⇒ `NarratorUnavailable`（装配面的问题，不是模型的问题）。
    """

    def narrator(prompt: str) -> NarrativeAdmission:
        from packages.application.ports.model_gateway import CompletionRequest

        try:
            secret = credentials.resolve(credential_ref)
        except Exception as error:  # noqa: BLE001 - 装配面缺件，点名后交给调用方
            raise NarratorUnavailable(
                f"narrative credential {credential_ref!r} cannot be resolved: {error}"
            ) from error
        result = gateway.complete(
            endpoint,
            secret,
            CompletionRequest(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            ),
        )
        sections = parse_narrative(result.content)
        validate_narrative(sections)
        returned = result.returned_model_name or model_name
        return NarrativeAdmission(
            author=f"model:{endpoint.id}/{returned}",
            returned_model=returned,
            digest=narrative_digest(sections),
            sections=sections,
        )

    return narrator


__all__ = [
    "NarratedReport",
    "Narrator",
    "NarratorUnavailable",
    "llm_narrator",
    "narrate",
]
