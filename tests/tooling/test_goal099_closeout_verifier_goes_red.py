"""GOAL-20261028-099 EC-05 的判据：**收口验证器真的会红**（两向，按压在真文件上）。

**它补哪一格**：`test_closeout_verifiers_run_their_own_assertions.py` 保证「声明 == 实载」与
「断言集跑得动」；`test_terminal_goals_have_closeout_verifiers.py` 保证「终态 GOAL 有验证器且
被分类」。两份都不判**这条验证器会不会红** —— 一个恒绿的验证器与「没有验证器」在收口账上
等价（GOAL-096 的教训）。本文件补这一格，用**三种真实的缺陷形态**按压本轮的验证器：

1. 从宪章阶梯「报告」行**摘掉** `GOAL-20261028-099` ⇒ `ladder-报告-records-this-goal` 必须红；
2. 把阶梯 `下一级` 改成「叙述质量已判」⇒ `...-keeps-the-next-level-unchanged` 必须红
   （这正是本 GOAL 明令禁止的冒认）；
3. 从手稿合约**加上** `report: {}` ⇒ `manuscript-contract-declares-no-report-executor` 必须红。

三次按压都改**真文件**、跑**真验证器**（子进程，`--verdict-only`）、按 raw `sha256` 逐字节复原。
**按压后必须确认判据真的红了** —— 本轮把这件事做成了断言（`_run_verifier` 的返回值必须含
那条 `FAIL`），否则「按压了」与「按压生效」是两件事。
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_VERIFIER = _ROOT / "tools" / "verify_goal099_closeout.py"
_CHARTER = _ROOT / ".cursor" / "plans" / "goals" / "MAINLINE.md"
_CONTRACTS = _ROOT / "examples" / "contracts" / "task_contracts.yaml"

_GOAL = "GOAL-20261028-099"


def _run_verifier() -> str:
    """跑本轮验证器（子进程；判词行原样返回）。"""
    completed = subprocess.run(
        [sys.executable, "-B", str(_VERIFIER), "--root", str(_ROOT), "--verdict-only"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    return completed.stdout


def _green(text: str) -> dict[str, bool]:
    """判词行 → `{name: ok}`（`FAIL name -> detail` 与 `PASS name` 两种形态）。"""
    state: dict[str, bool] = {}
    for line in text.splitlines():
        if line.startswith("PASS "):
            state[line.split(" ", 1)[1].strip()] = True
        elif line.startswith("FAIL "):
            state[line.split(" ", 1)[1].split(" -> ", 1)[0].strip()] = False
    return state


def _write_and_restore(path: Path, pressed: bytes) -> str:
    """按压：改字节 → 跑验证器 → 复原（`sha256` 逐字节核对）。"""
    original = path.read_bytes()
    before = hashlib.sha256(original).hexdigest()
    assert pressed != original, "pressed bytes identical to the original — the press is a no-op"
    try:
        path.write_bytes(pressed)
        return _run_verifier()
    finally:
        path.write_bytes(original)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before, "press restore failed"


def _restore_check(path: Path, digest: str) -> None:
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, "press restore failed"


@pytest.fixture(scope="module")
def baseline() -> dict[str, bool]:
    """未按压时的判词（每条按压都必须**只**让它自己那条翻红）。"""
    state = _green(_run_verifier())
    assert state, "验证器没有产出任何判词 ⇒ 按压没有基线可比"
    return state


def test_the_verifier_is_green_on_the_real_tree(baseline: dict[str, bool]) -> None:
    """基线：真树上全部 PASS（否则后面的按压分不清「本来红」与「按压让它红」）。"""
    reds = sorted(name for name, ok in baseline.items() if not ok)
    assert not reds, reds


def test_dropping_the_goals_goalid_from_the_ladder_turns_it_red(baseline: dict[str, bool]) -> None:
    """按压 (1)：阶梯「报告」行摘掉本 GOAL ⇒ `ladder-报告-records-this-goal` 判红。"""
    original = _CHARTER.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    text = original.decode("utf-8")
    assert _GOAL in text
    pressed_text = text.replace(f"、{_GOAL}", "", 1)
    assert pressed_text != text, "阶梯行里没有「、GOAL-...-099」这种形态 ⇒ 按压锚点要改"
    state = _green(_write_and_restore(_CHARTER, pressed_text.encode("utf-8")))
    _restore_check(_CHARTER, digest)
    assert baseline.get("ladder-报告-records-this-goal") is True
    assert state.get("ladder-报告-records-this-goal") is False, (
        "摘掉本 GOAL 的 id 之后那条判据仍然绿 ⇒ 它看不见它存在的理由"
    )


def test_claiming_the_next_level_is_done_turns_it_red(baseline: dict[str, bool]) -> None:
    """按压 (2)：把 `下一级` 改成「叙述质量已判」⇒ 那条边界判据判红（本轮明令禁止的冒认）。"""
    original = _CHARTER.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    text = original.decode("utf-8")
    anchor = "**叙述质量与事实一致性可判**"
    assert anchor in text, "阶梯「报告」行的 `下一级` 锚点不在 ⇒ 按压要重新取锚"
    pressed = text.replace(anchor, "**叙述质量已判**", 1).encode("utf-8")
    state = _green(_write_and_restore(_CHARTER, pressed))
    _restore_check(_CHARTER, digest)
    assert baseline.get("ladder-报告-keeps-the-next-level-unchanged") is True
    assert state.get("ladder-报告-keeps-the-next-level-unchanged") is False, (
        "把 `下一级` 冒认成「已判」之后那条判据仍然绿 ⇒ 阶梯边界无人把守"
    )


def test_a_report_executor_on_the_manuscript_contract_turns_it_red(
    baseline: dict[str, bool],
) -> None:
    """按压 (3)：给手稿合约加 `report: {}` ⇒ 声明面那条判据判红。

    这一条防的是**死局**形态：合约一旦声明 `report:`，手稿相的跨相 `inputs` 会被编译期
    拒绝（`CROSS_PHASE_INPUT_INVALID`）⇒ 整条链起不来。收口账上必须有一条判据看着它。
    """
    original = _CONTRACTS.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    text = original.decode("utf-8")
    anchor = "  research_manuscript:\n    version: 1.0.0\n"
    assert anchor in text, "contract anchor missing"
    pressed = text.replace(
        anchor, "  research_manuscript:\n    version: 1.0.0\n    report: {}\n", 1
    ).encode("utf-8")
    state = _green(_write_and_restore(_CONTRACTS, pressed))
    _restore_check(_CONTRACTS, digest)
    assert baseline.get("manuscript-contract-declares-no-report-executor") is True
    assert state.get("manuscript-contract-declares-no-report-executor") is False, (
        "合约声明了 report: 之后那条判据仍然绿 ⇒ 死局形态无人把守"
    )
