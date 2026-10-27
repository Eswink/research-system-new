"""GOAL-20261027-098 EC-02 的**判负路径**判据：创新点不成立时门真的判负，且不崩。

**它补哪一格**（真跑抓到的真缺陷，不是推想）：`novelty_claim_step.with_novelty` 原先写

    return replace(gate, passed=False, verdicts=(*gate.verdicts, rejection))

而 `GateOutcome` 既**没有** `verdicts` 字段（它叫 `evaluations`），`passed` 也只是**只读
property**（不是 dataclass 字段）⇒ 这一行在**任何一次判负**时都抛 `AttributeError`：
「创新点不成立」被变成「运行时崩」。

**为什么既有判据全绿而它没被发现**：`tests/contracts/test_direction_to_report_v2_novelty.py`
只判了**直通面**（非创新点合约 ⇒ 原 gate 原样返回）与 `novelty_verdict` 自己返回非空，
**没有**一条把非空判词真的喂进 `with_novelty`。而真跑此前在检索相就停了（上游 503）⇒
判负路径**一次都没执行过**。这是「只判一半路径」的典型假绿：**判据覆盖了函数的一半**。

**本文件判四件事**：

1. **判负不崩**：`with_novelty` 在判负时返回 `GateOutcome`（不抛 `AttributeError`）；
2. **门真的不过**：返回的 `verdict` 是 `REJECT`、`passed` 为假、`decision` 是 `REJECT`；
3. **判词进得去且可读**：那句点名判词出现在 `findings` 与 `decision.rationale` 里，
   且判据条数 = 原有条数 + 1（**并列**，不是覆盖既有判据）；
4. **归因不被这一步改写**：`reviewed_by` / `reviewer_model` 与传入的 gate 逐字相同
   （归因是执行事实，重建时读回，不重算）。

**反证臂**：把实现改回 `replace(gate, passed=False, ...)`（真文件）⇒ (1) 判红；
按 raw `sha256` 逐字节复原。
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from packages.application.run_orchestration.evaluation_gate import (
    GateAttribution,
    _gate_outcome,
)
from packages.application.run_orchestration.novelty_claim_step import (
    NOVELTY_CONTRACT_ID,
    with_novelty,
)
from packages.domain.acceptance import CriterionEvaluation
from packages.domain.core import ID
from packages.domain.enums import AcceptanceCriterionType
from packages.domain.tasks import ResearchTask

_ROOT = Path(__file__).resolve().parents[2]
_STEP = "packages/application/run_orchestration/novelty_claim_step.py"

_RUN_ID = "9a8b7c6d-5e4f-4a3b-8c2d-1e0f3a5b7c9d"
_TASK_ID = "1b2c3d4e-5f6a-4b7c-8d9e-0f1a2b3c4d5e"


def _task() -> ResearchTask:
    return ResearchTask(id=ID(_TASK_ID), run_id=ID(_RUN_ID))


def _gate() -> Any:
    """一个**通过的**既有 gate（带一条既有判据 + 归因面）。"""
    evaluations = [
        CriterionEvaluation(
            criterion_type=AcceptanceCriterionType.ARTIFACT_EXISTS,
            passed=True,
            reason="ARTIFACT_EXISTS(novelty_claim) satisfied",
        )
    ]
    return _gate_outcome(
        _task(),
        evaluations,
        True,
        GateAttribution(reviewer="gate:novelty_writer", reviewer_model="main/deepseek-v4-pro-0813"),
    )


def _novelty_tctx() -> Any:
    """创新点合约的 `tctx`；`deps=None` ⇒ 读取器无从取证据 ⇒ **判负**（不是放行）。"""
    return SimpleNamespace(
        contract=SimpleNamespace(id=NOVELTY_CONTRACT_ID),
        task=SimpleNamespace(
            run_id=SimpleNamespace(value=_RUN_ID), id=SimpleNamespace(value=_TASK_ID)
        ),
    )


# --- 1/2/3/4 ----------------------------------------------------------------


def test_a_rejected_claim_turns_the_gate_red_without_crashing() -> None:
    """(1)+(2) 判负**不崩**，且门真的不过（`REJECT` / `passed` 假 / `decision` `REJECT`）。"""
    outcome = with_novelty(None, _novelty_tctx(), _gate())
    assert outcome.verdict == "REJECT", outcome.verdict
    assert outcome.passed is False
    assert outcome.decision.decision == "REJECT", outcome.decision.decision


def test_the_rejection_reason_is_readable_in_the_findings() -> None:
    """(3) 那句点名判词真的进得去（`findings` 与 `decision.rationale` 都能读到）。"""
    outcome = with_novelty(None, _novelty_tctx(), _gate())
    joined = "\n".join(outcome.review_finding.findings)
    assert "NOVELTY_CLAIM_GROUNDED" in joined, joined
    assert "NOVELTY_CLAIM_GROUNDED" in outcome.decision.rationale, outcome.decision.rationale


def test_the_novelty_criterion_is_appended_not_substituted() -> None:
    """(3) 判据是**并列追加**：原有那条逐字还在，条数 +1（不覆盖既有判据）。"""
    before = _gate()
    after = with_novelty(None, _novelty_tctx(), before)
    assert len(after.evaluations) == len(before.evaluations) + 1, after.evaluations
    assert after.evaluations[0] == before.evaluations[0]
    added = after.evaluations[-1]
    assert added.criterion_type is AcceptanceCriterionType.CUSTOM_EVALUATOR
    assert added.passed is False


def test_the_attribution_of_the_original_gate_is_preserved() -> None:
    """(4) 归因**不被这一步改写**（`reviewed_by` / `reviewer_model` 逐字相同）。"""
    before = _gate()
    after = with_novelty(None, _novelty_tctx(), before)
    assert after.review_finding.reviewed_by == before.review_finding.reviewed_by
    assert after.review_finding.reviewer_model == before.review_finding.reviewer_model


def test_a_passing_or_unrelated_contract_returns_the_same_gate() -> None:
    """零回归：非创新点合约 ⇒ **同一个对象**原样返回（既有语义逐字不变）。"""
    sentinel = object()
    other = SimpleNamespace(contract=SimpleNamespace(id="research_report_plan"))
    assert with_novelty(None, other, sentinel) is sentinel


# --- 反证臂 -----------------------------------------------------------------


def test_reverting_the_fix_makes_the_reject_path_crash_again() -> None:
    """**按压在真文件上**：改回 `replace(gate, passed=False, ...)` ⇒ 判负路径真的崩。

    这条判的是「本文件第 1 组用例的存在意义」：把实现改回旧写法之后，
    `with_novelty` 在判负时抛 `AttributeError`（`passed` 是只读 property）。
    按 raw `sha256` 逐字节复原。
    """
    path = _ROOT.joinpath(*_STEP.split("/"))
    original = path.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    text = original.decode("utf-8")
    marker = "    evaluations = (\n        *gate.evaluations,"
    assert marker in text, "按压锚点不在（实现已经换形 ⇒ 本条判据需要跟着改）"
    # 用**修复前那一行**替换整段重建逻辑（保留函数头与 early return）。
    start = text.index(marker)
    end = text.index("def _attribution_of(gate: Any) -> Any:")
    legacy = (
        "    from dataclasses import replace\n"
        "\n"
        "    return replace(gate, passed=False, verdicts=(*gate.verdicts, rejection))\n"
        "\n"
        "\n"
    )
    pressed = (text[:start] + legacy + text[end:]).encode("utf-8")
    assert hashlib.sha256(pressed).hexdigest() != digest
    try:
        path.write_bytes(pressed)
        import importlib

        import packages.application.run_orchestration.novelty_claim_step as step

        reloaded = importlib.reload(step)
        try:
            reloaded.with_novelty(None, _novelty_tctx(), _gate())
        except AttributeError as error:
            assert "verdicts" in str(error), str(error)
        else:  # pragma: no cover - 修复被回退时必然走到这里
            raise AssertionError(
                "the pre-fix implementation did not crash on the reject path — "
                "the judge cannot see the defect it exists to catch"
            )
    finally:
        path.write_bytes(original)
        import importlib

        import packages.application.run_orchestration.novelty_claim_step as step

        importlib.reload(step)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, "press restore failed"


@pytest.mark.parametrize("name", ["novelty_verdict", "with_novelty"])
def test_the_two_entry_points_are_still_exported(name: str) -> None:
    """射程非空：两个入口都还在 `__all__` 里（删掉任一个 ⇒ 接线面失联）。"""
    import packages.application.run_orchestration.novelty_claim_step as step

    assert name in step.__all__, step.__all__
