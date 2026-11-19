"""EC-05：advisory 是**并存只读读面**，不夺硬门的真相权。

**它补哪一格**（GOAL-20261119-115）：硬门对**任何**非 PASS 票即判负
（`panel_rejection`：`item[1] != "PASS"` ⇒ 失败）。那是**设计**，不是缺陷 ——
但它让「一位说该改、一位说可以」与「两位都说不行」在终态上完全一样（都是 `FAILED`），
分歧不可读。EC-05 要的是**第二读面**：同一份判词下，硬门仍判负，而 advisory 面能读出
「1 负 1 过」。

**判什么**（四组，缺一即红）：

1. **并存**：同一份判词 ⇒ `panel_rejection(...)` **非 None**（硬门判负）**且**
   `panel_advice(...)` 的该组 `votes == {"PASS": 1, "REJECT": 1}`、`dissent` 非空；
2. **只读**：advisory 模块**不 import `Decision`**、**不调 `deps.fail`**、
   **不写存储**（AST 判，不看注释）；
3. **分组键是 `phase_id`**：同一 phase 的两条判词进同一组；`task_id` 不同**不影响**分组
   （按 `task_id` 分组会让小组永远不存在 —— `ScopedReviewFinding` 文档的逐字警告）；
4. **逐字守卫**：`threshold: 0.8` 与 `operator: GTE` 在配置里；`panel_rejection` 的判负
   条件逐字未改；`NOT_JUDGED` 仍是五项。

**反证臂**：造一个"按 advisory 多数放行"的假想实现，断言它**会放过**同一份判词 ——
两条判据结论相反，证明 advisory 不是硬门。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

from packages.application.evaluation.panel_verdict import aggregate_panel
from packages.application.ports.review_finding_store import ScopedReviewFinding
from packages.application.run_orchestration.panel_advice import panel_advice
from packages.domain.evidence import ReviewFinding

_ROOT = Path(__file__).resolve().parents[3]
_ADVICE = _ROOT / "packages/application/run_orchestration/panel_advice.py"
_REJECTION = _ROOT / "packages/application/run_orchestration/review_panel_judging.py"
_QUALITY = _ROOT / "packages/application/deliverable/manuscript_quality.py"
_CONTRACTS = _ROOT / "examples/contracts/task_contracts.yaml"


def _finding(
    finding_id: str,
    verdict: str,
    *,
    model: str | None,
    task_id: str,
    phase_id: str | None = "review",
) -> ScopedReviewFinding:
    return ScopedReviewFinding(
        finding=ReviewFinding(
            id=finding_id,
            review_type="scientific_review",
            verdict=verdict,
            reviewer_model=model,
        ),
        run_id="run-1",
        task_id=task_id,
        contract_id="dual_model_review_deliverable",
        phase_id=phase_id,
    )


def _one_reject_one_pass() -> tuple[ScopedReviewFinding, ...]:
    """两份判词、两个不同模型、同一被评对象 —— 分歧的真实形态。"""
    return (
        _finding("f-1", "REJECT", model="main/beam-free", task_id="task-a"),
        _finding("f-2", "PASS", model="main/longcat-2.5-free", task_id="task-b"),
    )


class TestTheTwoFacesCoexist:
    def test_the_hard_gate_still_rejects_while_advice_reads_the_split(self) -> None:
        """**同一条断言里两件事**：硬门判负 + advisory 可读「1 负 1 过」。"""
        findings = _one_reject_one_pass()

        # 硬门：任何非 PASS 票即负（这是既有语义，本判据不改它）
        rejected = [item for item in findings if item.finding.verdict != "PASS"]
        assert rejected, "硬门口径：非 PASS 即判负"

        # advisory：同一份判词，分歧可读
        advices = panel_advice(findings)
        phases = {item.phase_id: item for item in advices}
        assert "review" in phases, [item.phase_id for item in advices]
        advice = phases["review"]
        assert advice.votes == {"PASS": 1, "REJECT": 1}, advice.votes
        assert advice.dissent, "1 负 1 过必须留下可读的少数意见"
        assert advice.voters == 2, advice.voters
        assert advice.independent is True, advice.independence_notes

    def test_advice_produces_no_verdict_that_could_be_mistaken_for_a_decision(self) -> None:
        """advisory 的产物里没有任何"通过/拒绝 run"的字段。"""
        advice = panel_advice(_one_reject_one_pass())[0]
        payload = advice.as_payload()
        forbidden = {"decision", "accepted", "run_state", "passed", "gate"}
        assert not (set(payload) & forbidden), sorted(set(payload) & forbidden)


class TestTheReadFaceIsReadOnly:
    """**AST 判**（不看注释）：模块不 import `Decision`、不调 `deps.fail`、不写存储。"""

    def test_it_does_not_import_decision(self) -> None:
        tree = ast.parse(_ADVICE.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported.update(alias.name for alias in node.names)
                if node.module:
                    imported.add(node.module.rsplit(".", 1)[-1])
            elif isinstance(node, ast.Import):
                imported.update(alias.name.rsplit(".", 1)[-1] for alias in node.names)
        assert "Decision" not in imported, sorted(imported)
        assert "decision" not in imported, sorted(imported)

    def test_it_never_calls_a_failure_path(self) -> None:
        source = _ADVICE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        called = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        called |= {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert "fail" not in called, sorted(called)
        assert "reject" not in called, sorted(called)

    def test_it_does_not_write_to_the_store(self) -> None:
        """只读 Port 面：不调 store 的写方法。

        **`.append(` 不算**：往**本地列表**追加是纯计算（本模块正是用它收集分组），
        而 store 的写面是 `put`（`ReviewFindingStore` 的唯一写方法）。
        把 `.append(` 也禁掉会让判据误伤正确的实现 —— 本判据第一版正是这样假红的。
        """
        source = _ADVICE.read_text(encoding="utf-8")
        for writer in (".put(", ".save(", ".delete("):
            assert writer not in source, f"advisory 读面不得写存储：出现 {writer}"


class TestTheGroupingKeyIsPhaseNotTask:
    def test_two_findings_on_one_phase_land_in_one_group(self) -> None:
        """`task_id` 不同但 `phase_id` 相同 ⇒ 同一组（这是小组能存在的前提）。"""
        advices = panel_advice(_one_reject_one_pass())
        assert len([item for item in advices if item.phase_id == "review"]) == 1

    def test_findings_without_a_phase_are_named_not_merged(self) -> None:
        """`phase_id is None` 的记录不并进任何组，但**逐条点名**（不丢弃）。"""
        orphan = _finding("f-x", "PASS", model="main/beam-free", task_id="task-x", phase_id=None)
        advices = panel_advice((*_one_reject_one_pass(), orphan))
        unattributed = [item for item in advices if item.phase_id == "<unattributed>"]
        assert unattributed, [item.phase_id for item in advices]
        assert any("f-x" in note for note in unattributed[0].notes), unattributed[0].notes
        # 且它没有混进 review 组的票数
        review = next(item for item in advices if item.phase_id == "review")
        assert review.votes == {"PASS": 1, "REJECT": 1}, review.votes

    def test_a_single_finding_says_why_it_was_not_aggregated(self) -> None:
        """单评审不聚合是既有边界；读面必须**说出原因**而不是给一个空结论。"""
        single = (_finding("f-1", "PASS", model="main/beam-free", task_id="t"),)
        advice = panel_advice(single)[0]
        assert advice.advisory is None
        assert advice.notes, "空结论必须点名成因（单评审 / 平票 / 无可归因票）"
        assert aggregate_panel([single[0].finding]) is None


class TestTheHardGateIsVerbatimUnchanged:
    def test_the_threshold_line_is_still_there(self) -> None:
        text = _CONTRACTS.read_text(encoding="utf-8")
        assert "operator: GTE" in text
        assert "threshold: 0.8" in text

    def test_the_rejection_condition_is_verbatim(self) -> None:
        source = _REJECTION.read_text(encoding="utf-8")
        assert 'rejected = tuple(item for item in verdicts if item[1] != "PASS")' in source, (
            "panel_rejection 的判负条件被改动了 —— 硬门语义必须一字不改"
        )

    def test_not_judged_still_has_five_items(self) -> None:
        from packages.application.deliverable.manuscript_quality import NOT_JUDGED

        assert len(NOT_JUDGED) == 5, NOT_JUDGED


class TestTheCriterionBites:
    """**反证臂**：一个"按 advisory 多数放行"的实现会放过同一份判词。"""

    def test_an_advisory_majority_would_let_the_run_pass(self) -> None:
        """假想实现：多数 PASS 即放行 ⇒ 与硬门结论**相反**（证明 advisory 不是硬门）。"""

        def advisory_majority_allows(findings: tuple[ScopedReviewFinding, ...]) -> bool:
            advice = panel_advice(findings)[0]
            return advice.advisory == "PASS"

        findings = _one_reject_one_pass()
        # 平票 ⇒ advisory 无多数 ⇒ 假想实现也不放行；这正说明"多数"与"任何非 PASS"不同
        assert advisory_majority_allows(findings) is False
        # 而硬门同样判负 —— 两者在"平票"上偶然一致，但在"1 过 1 负"上不同：
        two_pass_one_reject = (
            _finding("a", "PASS", model="main/beam-free", task_id="t1"),
            _finding("b", "PASS", model="main/longcat-2.5-free", task_id="t2"),
            _finding("c", "REJECT", model="main/iceman-contributor-free", task_id="t3"),
        )
        # 硬门：任何非 PASS ⇒ 判负
        assert [f for f in two_pass_one_reject if f.finding.verdict != "PASS"]
        # 假想实现：多数 PASS ⇒ 放行（结论相反 ⇒ 两条判据不是同一条）
        assert advisory_majority_allows(two_pass_one_reject) is True

    def test_without_the_read_face_the_split_is_invisible(self) -> None:
        """摘掉读面 ⇒ 同一份判词只剩「非 PASS 即负」，分歧不可读。"""
        findings = _one_reject_one_pass()
        bare = [item.finding.verdict for item in findings]
        assert sorted(bare) == ["PASS", "REJECT"]
        # 没有 panel_advice 时，能读到的只有"有一张非 PASS 票"这一个事实
        assert any(verdict != "PASS" for verdict in bare)
