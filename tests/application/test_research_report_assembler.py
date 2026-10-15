"""研究报告汇编器的判据（GOAL-20261014-077 EC-01）。

判据面（每条都能独立取证）：

1. **四节齐全** —— 报告必须含 `SECTION_HEADINGS` 的四条二级标题（节的**存在**是契约）；
2. **事实来自输入** —— 来源标识 / 指标值 / 判词**逐字**出现在报告里（不是重新编造）；
3. **缺事实要说明，不得省略** —— 没有检索 / 没有实验 / 没有评审时，该节仍须在，
   且写明**为什么**没有（`_（无：…）_` 形态）；
4. **确定性** —— 同一份输入 ⇒ 逐字节相同的报告（这是「汇编」而非「生成」的判据）；
5. **空 run_id 点名拒绝** —— 不得静默产出一份没有归属的报告；
6. **局限节** —— 报告必须自陈它是汇编而非撰写，并在缺来源 / 缺指标时明写
   「结论没有外部证据 / 实验支持」。
"""

from __future__ import annotations

from packages.application.deliverable.research_report import (
    REPORT_ARTIFACT_NAME,
    REPORT_MIME,
    SECTION_HEADINGS,
    ReportBuildError,
    ReportInputs,
    build_research_report,
)

_FULL = ReportInputs(
    run_id="run-report-001",
    protocol_id="p_v1",
    state="SUCCEEDED",
    objective="评估排序算法在受控条件下的比较次数下降幅度",
    sources=(
        {"pmid": "39000001", "evidence_id": "ev-1"},
        {"pmid": "39000002", "evidence_id": "ev-2"},
    ),
    metrics=(
        {"name": "comparison_reduction_ratio", "value": "125.5", "unit": "ratio"},
        {"name": "wall_clock_seconds", "value": "1.83", "unit": "s"},
    ),
    verdict={
        "decision": "ACCEPT",
        "reason": "证据覆盖成立且指标达到合约阈值",
        "cited_facts": ["metric=comparison_reduction_ratio value=125.5"],
    },
    budget={"consumed": "1200", "limit": "5000"},
)

_BARE = ReportInputs(
    run_id="run-report-002",
    protocol_id="p_v1",
    state="SUCCEEDED",
    objective=None,
    sources=(),
    metrics=(),
    verdict=None,
)


def test_all_four_sections_are_present() -> None:
    report = build_research_report(_FULL)
    for heading in SECTION_HEADINGS:
        assert heading in report, f"报告缺少小节：{heading}"


def test_facts_are_carried_verbatim_from_the_inputs() -> None:
    """来源 / 指标 / 判词**逐字**进报告 —— 报告不得重算或编造数字。"""
    report = build_research_report(_FULL)
    for pmid in ("39000001", "39000002"):
        assert pmid in report, f"来源 {pmid} 没进报告"
    for evidence_id in ("ev-1", "ev-2"):
        assert evidence_id in report, f"证据 id {evidence_id} 没进报告"
    assert "comparison_reduction_ratio" in report
    assert "125.5" in report, "指标值必须逐字出现（不得四舍五入或重算）"
    assert "ACCEPT" in report
    assert "证据覆盖成立且指标达到合约阈值" in report


def test_missing_facts_are_declared_not_omitted() -> None:
    """没有检索 / 实验 / 评审时：该节**仍在**，且写明「无 + 原因」（不得整节省略）。"""
    report = build_research_report(_BARE)
    for heading in SECTION_HEADINGS:
        assert heading in report, f"缺事实时不得省略小节：{heading}"
    assert report.count("_（无：") >= 3, (
        "三个可能为空的小节（检索 / 实验 / 评审）各须写明「无 + 原因」"
    )
    assert "本 run 没有检索阶段" in report
    assert "本 run 没有实验阶段" in report
    assert "本 run 没有评审阶段" in report


def test_the_report_is_deterministic() -> None:
    """同一份输入 ⇒ **逐字节相同**（汇编是确定性的；这条把「生成」与「汇编」分开）。"""
    first = build_research_report(_FULL)
    second = build_research_report(_FULL)
    assert first == second, "同一份输入产出不同报告 ⇒ 不是确定性汇编"
    assert build_research_report(_BARE) == build_research_report(_BARE)


def test_an_empty_run_id_is_refused_by_name() -> None:
    """空 run_id ⇒ **点名拒绝**（不得静默产出一份没有归属的报告）。"""
    bad = ReportInputs(
        run_id="   ",
        protocol_id="p_v1",
        state="SUCCEEDED",
        objective=None,
        sources=(),
        metrics=(),
        verdict=None,
    )
    try:
        build_research_report(bad)
    except ReportBuildError as error:
        assert "run_id" in str(error), f"拒绝理由应点名 run_id：{error}"
    else:  # pragma: no cover - 只在判据失效时到达
        raise AssertionError("空 run_id 应被点名拒绝")


def test_the_limitations_section_is_honest() -> None:
    """局限节自陈「汇编而非撰写」，并在缺来源 / 缺指标时明写「没有外部证据 / 实验支持」。"""
    report = build_research_report(_BARE)
    assert "确定性汇编" in report and "不是**模型的叙述性撰写" in report.replace("**", "**"), (
        "限制节必须自陈它是汇编而非撰写"
    )
    assert "本 run 没有真实检索来源" in report, "缺来源时必须明写「结论没有外部证据支持」"
    assert "本 run 没有实测指标" in report, "缺指标时必须明写「结论没有实验支持」"

    full = build_research_report(_FULL)
    assert "本 run 没有真实检索来源" not in full, "有来源时不得误报「没有来源」"


def test_the_declared_artifact_name_is_markdown() -> None:
    """制品名与 MIME 是合约的一部分（改即改契约）。"""
    assert REPORT_ARTIFACT_NAME.endswith(".md"), REPORT_ARTIFACT_NAME
    assert REPORT_MIME == "text/markdown"


def test_multiple_arms_appear_as_separate_rows_with_a_stable_table_shape() -> None:
    """GOAL-20261015-079 EC-04：**多臂**时指标表逐臂一行，且表格**列数一致**。

    为什么单列这一条：本 GOAL 的 live 取证**实测**到一个真缺陷 —— 两个臂的同名指标曾被
    并进**同一格**（用分隔符连接），而 markdown 表头只有 3 列 ⇒ 那一行**变成 4 列**、
    渲染直接坏掉。本条把正确形态钉住：每个 (指标, 实验) **一行**，表头随之多一列
    「实验」，且**所有行与分隔行的 `|` 计数一致**（表格结构的机械判据）。
    """
    multi = ReportInputs(
        run_id="run-report-multi",
        protocol_id="p_v1",
        state="SUCCEEDED",
        objective=None,
        sources=(),
        metrics=(
            {"name": "ratio", "value": "2.0", "experiment_run_id": "exp-control"},
            {"name": "ratio", "value": "9.0", "experiment_run_id": "exp-treatment"},
        ),
        verdict=None,
    )
    report = build_research_report(multi)

    # **两臂的值都在**（不得丢任何一臂）。
    assert "2.0" in report and "9.0" in report, report
    assert "exp-control" in report and "exp-treatment" in report, report
    # 表格**逐臂一行**：该指标恰两行数据行（不是一格两值）。
    rows = [line for line in report.splitlines() if line.startswith("| `ratio`")]
    assert len(rows) == 2, rows
    # 表格形态**一致**：表头 / 分隔 / 数据行的管道符计数相同（渲染不会坏）。
    table = [line for line in report.splitlines() if line.startswith("|")]
    assert len({line.count("|") for line in table}) == 1, table


def test_a_single_arm_keeps_the_original_three_column_table() -> None:
    """单臂（无实验标识）⇒ **既有三列表格逐字不变**（零回归）。"""
    single = ReportInputs(
        run_id="run-report-single",
        protocol_id="p_v1",
        state="SUCCEEDED",
        objective=None,
        sources=(),
        metrics=({"name": "ratio", "value": "2.0"},),
        verdict=None,
    )
    report = build_research_report(single)
    assert "| 指标 | 值 | 单位 |" in report, report
    assert "| `ratio` | 2.0 | — |" in report, report
    table = [line for line in report.splitlines() if line.startswith("|")]
    assert {line.count("|") for line in table} == {4}, table
