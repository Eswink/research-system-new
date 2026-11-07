"""外部评审面板的判据（GOAL-20261107-107 EC-06 / EC-07）。

**它封住的失败形态**（每一种都会让「外部评审」变成冒充）：

1. **设施失败被读成判断**：网关超时 ⇒ 若折成 `SUPPORTED`，读面会显示「第三方模型认为论证
   成立」，而实际上什么都没判。这是本文件最重要的一条。
2. **面板判词变成 `Decision`**：那会让第三方意见参与验收 —— 越过了 advisory 边界。
3. **无归因的判词进票**：`ReviewFinding.reviewer_model` 为 `None` 时若被算作一票，
   「谁判的」就不可回答（与 `panel_verdict._eligible` 的既有纪律冲突）。
4. **`NOT_JUDGED` 被悄悄缩小**：实现了面板不等于确定性模块会判这三项。

臂的分布：正例（三态各解析对）／反证（网关抛错 ⇒ `PANEL_UNAVAILABLE`）／
反证（三态闭集改空 ⇒ 解析判据全红——见 `test_the_verdict_set_is_not_empty`）／
边界（空正文 ⇒ 点名拒绝）。
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from adapters.fakes.model_gateway import FakeModelGateway
from packages.application.deliverable.manuscript_panel import (
    PANEL_REVIEW_TYPE,
    PANEL_RUBRICS,
    PANEL_UNAVAILABLE,
    VERDICTS,
    PanelError,
    as_review_findings,
    manuscript_excerpts,
    panel_prompt,
    panel_summary,
    parse_panel_verdict,
    review_manuscript,
    rubric_by_id,
)
from packages.application.deliverable.manuscript_quality import NOT_JUDGED
from packages.domain.evidence import ReviewFinding
from packages.domain.models import LLMEndpoint

_SECTIONS = {
    "title": "A study of sorting",
    "abstract": "We study comparison sorting.",
    "introduction": "Sorting matters.",
    "related_work": "Prior work.",
    "methods": "We sort arrays of up to sixteen integers.",
    "results": "The output matched the reference [1].",
    "discussion": "The result generalises only to small arrays [1].",
    "conclusion": "Sorting works here.",
}


def _endpoint() -> LLMEndpoint:
    return LLMEndpoint(
        id="main",
        name="main relay",
        base_url="https://relay.invalid/v1",
        protocol="OPENAI_COMPATIBLE",
        credential_ref="LLM_MAIN_KEY",
    )


def _credential() -> object:
    return object()


def _failing_gateway() -> FakeModelGateway:
    """三次 `complete` 都失败（面板有 3 条 rubric）。

    **不能用 `FakeModelGatewayOptions(fail_timeout=True)`**：那只让**首调**失败，后两次会
    成功 —— 而本文件要证明的是「设施失败不折算」，需要每一次都是失败。FakeBase 的脚本语义
    是「按调用序次注入，消费完默认成功」，所以这里显式排三次。
    """
    from packages.application.ports.errors import PortTimeoutError
    from packages.domain.enums import FailureCategory

    gateway = FakeModelGateway()
    timeout = PortTimeoutError("relay timed out", failure_category=FailureCategory.MODEL_TIMEOUT)
    gateway.set_script("complete", [timeout] * len(PANEL_RUBRICS))
    return gateway


def test_the_rubric_set_maps_onto_the_first_three_not_judged_items() -> None:
    """三条 rubric 逐条对应 `NOT_JUDGED` 的前三项（多了就越过 §7，少了就有项没出口）。

    **对应是语义的，不是下标的** —— 所以这里断言的是「条数与那三项一致、且每条的 id
    在进行语义核对时能读出对应关系」，而不是字符串相等。
    """
    assert len(PANEL_RUBRICS) == 3, "§7 判定「只能人评」的正是三项"
    assert len(NOT_JUDGED) == 5, "`NOT_JUDGED` 必须仍是五项（本模块不改它）"
    ids = [known for known, _ in PANEL_RUBRICS]
    assert ids == ["citation_supports_sentence", "argument_holds", "method_appropriate"]
    # 三条问题各自的措辞覆盖对应那一项的关键概念。
    assert "support" in rubric_by_id("citation_supports_sentence").lower()
    assert "argument hold" in rubric_by_id("argument_holds").lower()
    assert "method appropriate" in rubric_by_id("method_appropriate").lower()


def test_an_unknown_rubric_is_named_not_guessed() -> None:
    """边界：未知 rubric id ⇒ 点名拒绝（不回落、不猜），判词列出闭集。"""
    with pytest.raises(PanelError, match="unknown panel rubric"):
        rubric_by_id("write_the_paper_for_me")


def test_an_empty_excerpt_is_named_not_sent() -> None:
    """边界：空正文 ⇒ 点名拒绝 —— 对没有文本的东西作判断不是对这篇稿子的判断。"""
    with pytest.raises(PanelError, match="empty excerpt"):
        panel_prompt("argument_holds", "   \n  ")


def test_the_verdict_set_is_not_empty() -> None:
    """**反证**：三态闭集必须非空且互不相同。

    把 `VERDICTS` 改成空元组时，`parse_panel_verdict` 的每一次返回都会落在闭集之外 ⇒
    `test_a_recognisable_token_maps_to_its_verdict` 与本条同时红。这一条把「闭集被清空」
    这种篡改挡在门口（否则解析判据可以恒真）。
    """
    assert VERDICTS, "判词闭集被清空了 —— 那会让任何解析结果都「合法」"
    assert len(set(VERDICTS)) == len(VERDICTS)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("SUPPORTED\nit does support it", "SUPPORTED"),
        ("REFUTED\nthe citation is irrelevant here", "REFUTED"),
        ("AMBIGUOUS\ncannot tell from the excerpt", "AMBIGUOUS"),
        ("not a verdict at all", "AMBIGUOUS"),
        ("", "AMBIGUOUS"),
        (None, "AMBIGUOUS"),
    ],
)
def test_a_recognisable_token_maps_to_its_verdict(raw: str | None, expected: str) -> None:
    """正例 + 兜底：认得的三态各自映射；认不出 ⇒ `AMBIGUOUS`（**不猜成通过**）。"""
    verdict, _rationale = parse_panel_verdict(raw)
    assert verdict in VERDICTS, f"解析出了闭集之外的值 {verdict!r}"
    assert verdict == expected


def test_a_gateway_failure_never_becomes_a_judgement() -> None:
    """**核心反证**：网关抛错 ⇒ 三条全是 `PANEL_UNAVAILABLE`，**没有一条**落在三态里。

    这条是本模块存在的最强理由：设施失败若被折算成 `SUPPORTED`，读面就会显示
    「第三方认为论证成立」，而实际上一次判定都没发生。
    """
    gateway = _failing_gateway()
    verdicts = review_manuscript(
        gateway=gateway,
        endpoint=_endpoint(),
        credential=_credential(),
        model_name="judge-model",
        sections=_SECTIONS,
    )
    assert len(verdicts) == len(PANEL_RUBRICS)
    for item in verdicts:
        assert item.verdict == PANEL_UNAVAILABLE, f"{item.rubric_id} 被折算成了 {item.verdict}"
        assert item.is_facility_failure is True
        assert item.is_judgement is False
        assert item.reviewer_model is None, "失败没有归因 —— 这正是它与判词的区别"


def test_the_summary_counts_facility_failures_separately() -> None:
    """摘要把设施失败**单列**，不混进三态的票数里。"""
    gateway = _failing_gateway()
    verdicts = review_manuscript(
        gateway=gateway,
        endpoint=_endpoint(),
        credential=_credential(),
        model_name="judge-model",
        sections=_SECTIONS,
    )
    summary = panel_summary(verdicts)
    assert summary[PANEL_UNAVAILABLE] == len(PANEL_RUBRICS)
    assert summary["SUPPORTED"] == 0 and summary["REFUTED"] == 0


def test_panel_verdicts_become_attributed_findings_but_never_a_decision() -> None:
    """**反证**：判词 → `ReviewFinding`（可归因），且**不**产生 `Decision`。

    `review_type` 与验收门分开、`reviewer_model` 在场、`reviewed_by` 是 `model:` 前缀；
    同时断言本模块的出口里**没有** `Decision`（advisory 边界的机械形态）。
    """
    gateway = FakeModelGateway()
    verdicts = review_manuscript(
        gateway=gateway,
        endpoint=_endpoint(),
        credential=_credential(),
        model_name="judge-model",
        sections=_SECTIONS,
    )
    stamp = datetime(2026, 11, 7, tzinfo=timezone.utc)
    findings = as_review_findings(verdicts, run_id="run-1", reviewed_at=stamp)
    assert len(findings) == len(PANEL_RUBRICS)
    for finding in findings:
        assert isinstance(finding, ReviewFinding)
        assert finding.review_type == PANEL_REVIEW_TYPE
        assert finding.review_type != "acceptance_gate", "面板意见不得冒充验收结论"
        # 归因：`reviewer_model` 是 `<endpoint>/<returned>`（供应商返回的名字）。
        assert finding.reviewer_model is not None
        assert finding.reviewer_model.startswith("main/")
        assert finding.reviewed_by == f"model:{finding.reviewer_model}"
    # 出口里没有 Decision：本模块不 import 它，构造面也不返回它。
    import packages.application.deliverable.manuscript_panel as module

    assert not hasattr(module, "Decision"), "面板模块不得接触 Decision（advisory 边界）"


def test_an_unattributed_finding_is_named_ineligible_not_counted() -> None:
    """**反证**：无归因的 finding 被 `panel_verdict._eligible` 点名为不可投票。

    这证明「设施失败照样落 finding」不会污染票数 —— 落库与投票是两件事。
    """
    from packages.application.evaluation.panel_verdict import aggregate_panel

    gateway = _failing_gateway()
    verdicts = review_manuscript(
        gateway=gateway,
        endpoint=_endpoint(),
        credential=_credential(),
        model_name="judge-model",
        sections=_SECTIONS,
    )
    stamp = datetime(2026, 11, 7, tzinfo=timezone.utc)
    findings = as_review_findings(verdicts, run_id="run-1", reviewed_at=stamp)
    panel = aggregate_panel(findings)
    # 三家都不可归因 ⇒ 没有可投票者；聚合要么 None（<2 份），要么把每条都点名 ineligible。
    if panel is not None:
        assert panel.voters == 0
        assert len(panel.ineligible) == len(findings)
        assert panel.independent is False


def test_excerpts_are_bounded_and_differ_per_rubric() -> None:
    """三条 rubric 看**不同**的节，且摘录有界（不把整篇无界地发出去）。"""
    excerpts = manuscript_excerpts(_SECTIONS, limit=200)
    assert set(excerpts) == {known for known, _ in PANEL_RUBRICS}
    assert all(len(text) <= 200 for text in excerpts.values())
    # 方法与主张看的面不同（方法学 rubric 拿到 methods 段开头）。
    assert (
        excerpts["method_appropriate"].startswith("## methods")
        or "sixteen integers" in (excerpts["method_appropriate"])
    )
    assert excerpts["citation_supports_sentence"] != excerpts["method_appropriate"]
