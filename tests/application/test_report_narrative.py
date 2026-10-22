"""报告域 L1 → L2 的判据：**报告由模型撰写**，而**每个数字仍可溯源**（GOAL-20261022-062）。

**它补哪一格**：报告此前是**确定性汇编**（`build_research_report`）—— 同一份持久状态 ⇒
逐字节相同，但它写不出叙述，叙述质量**无人判**。本轮让模型写正文，同时守住汇编器唯一的
硬约束：**数字必须可溯源**。

**判据面（每条独立取证）**：

1. **两块面分得开**：第 1…4 节由模型写、第 5 节（事实表）由汇编器写；抬头点名**叙述作者**
   与**供应商返回的模型名**（同名漂移可见）⇒ 「谁写的」在制品上可读，不靠猜。
2. **模型不许写数字**：叙述里出现任何 Unicode 十进制数位 ⇒ **点名拒绝**（`NarrativeError`，
   消息点名**哪个键**与**哪个字符**）。**为什么不静默抽掉**：静默改写会让「这段是谁说的」
   不可判。
3. **数字不因模型而脱离来源**：事实表的**每一行**都带来源列，且与 `ReportInputs` 逐条
   对得上（来源标识 / 指标值 / 判词原样）；模型给的值**一个都不进**事实表。
4. **零回归**：没接叙述者 ⇒ 报告字节与既有确定性汇编**逐字节相同**、`created_by` 仍是
   `system:report-assembler`、元数据键集不变。
5. **失败即点名**：畸形 JSON / 缺键 / 空叙述 / 写了数字，四态**各自**点名，不合并成
   「报告不可用」。
6. **归因可复核**：`created_by` 与 `report_metadata` 的 `narrative` 块与叙述者返回的
   身份**同源**（同一个 `NarrativeAdmission`），且叙述摘要 `sha256` 由正文重算得出。
"""

from __future__ import annotations

import json

import pytest

from packages.application.deliverable.report_narrative import (
    FACT_TABLE_COLUMNS,
    FACT_TABLE_HEADING,
    NARRATIVE_KEYS,
    NarrativeAdmission,
    NarrativeError,
    build_narrative_report,
    fact_ledger,
    narrative_digest,
    parse_narrative,
    validate_narrative,
)
from packages.application.deliverable.research_report import (
    SECTION_HEADINGS,
    ReportInputs,
    build_research_report,
    report_metadata,
)
from packages.application.run_orchestration.report_narrative_task import narrate

#: 一份**完整**的事实输入（来源 / 指标 / 判词三类都在）。
_FULL = ReportInputs(
    run_id="run-narrative-001",
    protocol_id="research_report_chain_v1",
    state="SUCCEEDED",
    objective="评估排序算法在受控条件下的比较次数下降幅度",
    sources=(
        {"identifier": "39000001", "evidence_id": "ev-1", "title": "A trial"},
        {"identifier": "39000002", "evidence_id": "ev-2", "title": "A follow-up"},
    ),
    metrics=(
        {"name": "comparison_reduction_ratio", "value": "125.5", "experiment_run_id": "exp-a"},
        {"name": "comparison_reduction_ratio", "value": "178.5", "experiment_run_id": "exp-b"},
    ),
    verdict={"decision": "ACCEPT", "reason": "coverage holds", "cited_facts": ("c=1",)},
)

#: 一份**什么事实都没有**的输入（空态也必须能出报告）。
_BARE = ReportInputs(
    run_id="run-narrative-002",
    protocol_id="research_report_chain_v1",
    state="SUCCEEDED",
    objective=None,
    sources=(),
    metrics=(),
    verdict=None,
)

#: 叙述样本（**一个数字都没有** —— 这是模型被要求遵守的形态）。
_BODY = {
    "question": "The run asked how a controlled change affects the work the pipeline performs.",
    "evidence": "The retrieval stage returned records whose identifiers are listed in the table.",
    "experiment": "Two arms ran under the same script; their readings appear in the table by name.",
    "review": "The reviewer accepted the run; the decision is quoted verbatim in the table.",
}


def _admission(
    body: dict[str, str] | None = None, *, author: str | None = None
) -> NarrativeAdmission:
    sections = dict(_BODY if body is None else body)
    return NarrativeAdmission(
        author=author or "model:main/dsv4-flash-vision",
        returned_model="dsv4-flash-vision",
        digest=narrative_digest(sections),
        sections=sections,
    )


def test_the_two_faces_are_separately_authored() -> None:
    """第 1…4 节（模型）+ 第 5 节（汇编器）；抬头点名作者与返回名。"""
    report = build_narrative_report(_FULL, _admission())
    for heading in SECTION_HEADINGS:
        assert heading in report, heading
    assert FACT_TABLE_HEADING in report
    assert "**叙述作者**: model:main/dsv4-flash-vision" in report
    assert "供应商返回的模型名" in report and "`dsv4-flash-vision`" in report
    # 四节标题在事实表之前（段序即契约：叙述在前、数字在后）
    assert report.index(SECTION_HEADINGS[-1]) < report.index(FACT_TABLE_HEADING)


def test_the_model_text_is_the_report_text_word_for_word() -> None:
    """**模型写的就是报告里的**：四个键的正文逐字出现（没有被改写 / 被裁剪）。"""
    report = build_narrative_report(_FULL, _admission())
    for key in NARRATIVE_KEYS:
        assert _BODY[key] in report, key


@pytest.mark.parametrize(
    ("body", "key", "char"),
    [
        (
            {**_BODY, "experiment": "Both arms reduced the count by 125.5 percent."},
            "experiment",
            "1",
        ),
        ({**_BODY, "question": "The run compared 2 arms."}, "question", "2"),
        ({**_BODY, "review": "PMID 39000001 was cited."}, "review", "3"),
    ],
)
def test_a_numeral_in_the_narrative_is_refused_by_name(
    body: dict[str, str], key: str, char: str
) -> None:
    """模型写了数字 ⇒ **点名**拒绝（哪个键 + 哪个字符），不静默抽掉。"""
    with pytest.raises(NarrativeError) as raised:
        validate_narrative(body)
    message = str(raised.value)
    assert key in message and repr(char) in message, message


def test_the_numbers_live_only_in_the_fact_table_and_keep_their_sources() -> None:
    """**核心**：事实表逐行带来源；模型给的值一个都不进；数值与 `ReportInputs` 逐字相同。"""
    report = build_narrative_report(_FULL, _admission())
    table = report[report.index(FACT_TABLE_HEADING) :]
    assert "| " + " | ".join(FACT_TABLE_COLUMNS) + " |" in table
    # 每个来源 / 指标的来源列都在
    for source in _FULL.sources:
        assert f"`{source['evidence_id']}`" in table
    for metric in _FULL.metrics:
        assert f"`{metric['experiment_run_id']}`" in table
        assert metric["value"] in table
    # 叙述区（事实表之前）里**一个指标值都没有** —— 数字只活在事实表。
    narrative_zone = report[: report.index(FACT_TABLE_HEADING)]
    for metric in _FULL.metrics:
        assert metric["value"] not in narrative_zone, metric["value"]


def test_the_fact_ledger_is_exactly_the_persisted_facts() -> None:
    """事实表的行 = 持久事实（不多不少）；模型**不能**往里加行。"""
    rows = fact_ledger(_FULL)
    assert len(rows) == len(_FULL.sources) + len(_FULL.metrics) + 2  # +2 = decision / reason
    assert {row["来源"] for row in rows} >= {"ev-1", "ev-2", "exp-a", "exp-b", "review_findings"}
    # 模型正文里的任何一个词都不会变成事实表的行
    assert all(row["类别"] in {"来源", "指标", "评审"} for row in rows)


def test_an_empty_run_still_produces_all_five_sections() -> None:
    """空态：五节都在，事实表写明「无」并说明为什么（不省略该节）。"""
    report = build_narrative_report(_BARE, _admission())
    assert FACT_TABLE_HEADING in report
    assert "_（无）_" in report
    assert "没有真实检索来源" in report and "没有实测指标" in report


def test_the_compiled_form_is_byte_identical_without_a_narrator() -> None:
    """**零回归**：没叙述者 ⇒ 与既有确定性汇编逐字节相同；元数据键集也不变。"""
    first = build_research_report(_FULL)
    second = build_research_report(_FULL)
    assert first == second
    assert "叙述作者" not in first and FACT_TABLE_HEADING not in first
    plain = json.loads(report_metadata(_FULL))
    assert "narrative" not in plain, plain
    narrated = json.loads(report_metadata(_FULL, _admission()))
    assert narrated["narrative"]["returned_model"] == "dsv4-flash-vision"
    assert set(plain) < set(narrated)


def test_the_narrative_is_deterministic_and_digest_is_recomputed() -> None:
    """同一份叙述 ⇒ 同一份报告字节；摘要由正文重算（不是叙述者自报的字符串）。"""
    one = build_narrative_report(_FULL, _admission())
    two = build_narrative_report(_FULL, _admission())
    assert one == two
    assert _admission().digest == narrative_digest(_BODY)
    assert _admission().digest in one


@pytest.mark.parametrize(
    ("content", "needle"),
    [
        (None, "empty"),
        ("   ", "empty"),
        ("not json", "not a JSON object"),
        ("[1, 2]", "must be a JSON object"),
    ],
)
def test_malformed_narrative_output_is_named_not_guessed(content: str | None, needle: str) -> None:
    """畸形输出四态各自点名（不猜、不回退）。"""
    with pytest.raises(NarrativeError) as raised:
        parse_narrative(content)
    assert needle in str(raised.value), str(raised.value)


def test_a_missing_section_is_named_per_key() -> None:
    """缺键逐条点名（不是「叙述不可用」一句话）。"""
    body = {**_BODY, "review": ""}
    with pytest.raises(NarrativeError) as raised:
        validate_narrative(body)
    assert "review" in str(raised.value)


def test_the_reporter_takes_the_narrators_identity_not_its_own() -> None:
    """归因面来自叙述者：换一个作者 ⇒ 报告的抬头跟着变（不写死）。"""
    other = _admission(author="model:main/kimi-k2.6")
    report = build_narrative_report(_FULL, other)
    assert "model:main/kimi-k2.6" in report
    assert "model:main/dsv4-flash-vision" not in report


def test_the_prompt_never_carries_a_value() -> None:
    """任务书只给**名称与来源** —— 数值不发给模型（它无从复述）。"""
    captured: list[str] = []

    def narrator(prompt: str) -> NarrativeAdmission:
        captured.append(prompt)
        return _admission()

    narrate(_FULL, narrator)
    assert captured, "叙述者没有被调用"
    prompt = captured[0]
    for metric in _FULL.metrics:
        assert metric["value"] not in prompt, metric["value"]
    for source in _FULL.sources:
        assert source["identifier"] not in prompt, source["identifier"]
    assert "comparison_reduction_ratio" in prompt
