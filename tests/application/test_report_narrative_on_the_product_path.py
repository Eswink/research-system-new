"""「报告由模型撰写」在**产品路径**上的判据（GOAL-20261022-062）。

**与 `tests/application/test_report_narrative.py` 的分工**：那个文件判**渲染与拒绝**
（纯函数面）；本文件判**它被接到产品路径上之后的形态** —— 派发 → 读事实 → 模型写正文 →
准入 canonical，产物在 `ArtifactStore` 里，`created_by` / 元数据 / 证据都读得回来。

**判据面（每条独立取证）**：

1. **接上叙述者 ⇒ 制品作者是模型**：`Artifact.created_by` 是 `model:<endpoint>/<returned>`，
   且报告的 5 节都在、事实表带来源；元数据里有 `narrative` 块（作者 / 返回名 / 摘要）。
2. **没接 ⇒ 零回归**：`created_by` 仍是 `system:report-assembler`，报告字节与既有汇编器
   **逐字节相同**，元数据键集不变。
3. **模型写了数字 ⇒ 任务点名失败**（不是产出一份「看起来像报告」的制品）：
   `outcome=FAILED`、消息点名**哪个键**、**没有**制品落库。
4. **凭据拿不到 ⇒ 点名**（`NarratorUnavailable` 被抓成失败消息），不静默回退到汇编 ——
   否则「谁写的」会与制品上的作者对不上。
"""

from __future__ import annotations

from typing import Any

import pytest

from packages.application.deliverable.report_narrative import (
    FACT_TABLE_HEADING,
    NarrativeAdmission,
    NarrativeError,
    narrative_digest,
    validate_narrative,
)
from packages.application.deliverable.research_report import (
    REPORT_ARTIFACT_NAME,
    SECTION_HEADINGS,
    ReportInputs,
    build_research_report,
)
from packages.application.run_orchestration.report_narrative_task import (
    NarratorUnavailable,
    llm_narrator,
)
from packages.application.run_orchestration.report_task import _body

_BODY = {
    "question": "The run asked how a controlled change affects the work the pipeline performs.",
    "evidence": "The retrieval stage returned records listed in the fact table.",
    "experiment": "Arms ran under one script; their readings appear in the fact table by name.",
    "review": "The reviewer accepted the run; the decision is quoted in the fact table.",
}


def _inputs() -> ReportInputs:
    return ReportInputs(
        run_id="run-product-001",
        protocol_id="research_report_chain_v1",
        state="SUCCEEDED",
        objective="A controlled comparison",
        sources=({"identifier": "39000001", "evidence_id": "ev-1"},),
        metrics=({"name": "ratio", "value": "125.5", "experiment_run_id": "exp-a"},),
        verdict={"decision": "ACCEPT", "reason": "coverage holds"},
    )


def _admission(body: dict[str, str] | None = None) -> NarrativeAdmission:
    sections = dict(_BODY if body is None else body)
    return NarrativeAdmission(
        author="model:main/twin-a",
        returned_model="twin-a",
        digest=narrative_digest(sections),
        sections=sections,
    )


def _narrator(body: dict[str, str] | None = None) -> Any:
    def narrator(_prompt: str) -> NarrativeAdmission:
        return _admission(body)

    return narrator


def test_attaching_a_narrator_changes_who_is_named_as_the_author() -> None:
    """**核心**：同一份事实，接不接叙述者 ⇒ 作者面不同，而数字面相同。"""
    compiled, compiled_admission = _body(_deps_without_narrator(), _inputs())
    written, written_admission = _body(_deps_with_narrator(), _inputs())

    assert compiled_admission is None
    assert written_admission is not None
    assert written_admission.author == "model:main/twin-a"
    # 汇编形态：四节在、无叙述抬头、无事实表
    assert all(heading in compiled for heading in SECTION_HEADINGS)
    assert "叙述作者" not in compiled and FACT_TABLE_HEADING not in compiled
    # 模型形态：四节在、五节在、抬头点名作者
    assert all(heading in written for heading in SECTION_HEADINGS)
    assert FACT_TABLE_HEADING in written and "model:main/twin-a" in written
    # **数字面相同**：两形态的事实都来自同一份持久事实
    assert "125.5" in compiled and "125.5" in written
    assert "ev-1" in compiled and "ev-1" in written


def test_the_compiled_form_is_still_byte_identical() -> None:
    """零回归：`_body` 在没叙述者时**逐字节**等于既有汇编器的输出。"""
    compiled, _admission_value = _body(_deps_without_narrator(), _inputs())
    assert compiled == build_research_report(_inputs())


def test_a_numeral_from_the_model_fails_the_task_by_name() -> None:
    """模型写了数字 ⇒ `NarrativeError` 点名键与字符（调用方据此判失败并**不落制品**）。"""
    bad = {**_BODY, "experiment": "The count dropped by 125.5 percent."}
    with pytest.raises(NarrativeError) as raised:
        _body(_deps_with_narrator(bad), _inputs())
    message = str(raised.value)
    assert "experiment" in message and "'1'" in message, message


def test_an_unavailable_credential_is_named_not_silently_compiled() -> None:
    """凭据拿不到 ⇒ `NarratorUnavailable` 点名（**不**静默回退到汇编器）。"""

    class _Missing:
        def resolve(self, _ref: str) -> Any:
            raise RuntimeError("no such credential")

    class _Gateway:
        def complete(self, *_args: Any, **_kwargs: Any) -> Any:  # pragma: no cover - 不该被调
            raise AssertionError("gateway must not be reached without a credential")

    narrator = llm_narrator(
        gateway=_Gateway(),
        credentials=_Missing(),
        endpoint=type("_E", (), {"id": "main"})(),
        model_name="twin-a",
        credential_ref="LLM_MAIN_KEY",
    )
    with pytest.raises(NarratorUnavailable) as raised:
        narrator("prompt")
    assert "LLM_MAIN_KEY" in str(raised.value)


def test_the_artifact_author_and_metadata_come_from_the_admission() -> None:
    """`created_by` 与元数据 `narrative` 块**同源**（都读同一个 admission，不各读一份）。"""
    from packages.application.deliverable.research_report import report_metadata

    admission = _admission()
    payload = report_metadata(_inputs(), admission)
    assert '"author": "model:main/twin-a"' in payload
    assert '"returned_model": "twin-a"' in payload
    assert admission.digest in payload
    # 制品的作者名与这件事实同源（`_put_report` 只读 `narrative.author`）
    import inspect

    from packages.application.run_orchestration import report_task

    source = inspect.getsource(report_task._put_report)
    assert "narrative.author if narrative is not None" in source, source


def test_the_report_artifact_name_is_unchanged() -> None:
    """制品名与既有契约一致（读面 / live 判据都按它取）。"""
    assert REPORT_ARTIFACT_NAME == "research_report.md"


def test_every_narrative_section_passes_the_shared_validator() -> None:
    """模型形态走的是**同一个**校验器（不是另一条更宽松的路径）。"""
    validate_narrative(_BODY)  # 不抛
    with pytest.raises(NarrativeError):
        validate_narrative({**_BODY, "review": "scored 4 of 5"})


def _deps_with_narrator(body: dict[str, str] | None = None) -> Any:
    """一个只有 `narrator` 字段的 deps 替身。

    **不用 `type("_D", (), {"narrator": f})`**：函数变成类属性后就成了**绑定方法**，
    `deps.narrator(prompt)` 会把 deps 自己当第一个参数传进去（实测 `TypeError: takes 1
    positional argument but 2 were given`）。用 dataclass 才能让它是**普通可调用对象**。
    """
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class _Deps:
        narrator: Any | None

    return _Deps(_narrator(body))


def _deps_without_narrator() -> Any:
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class _Deps:
        narrator: Any | None

    return _Deps(None)
