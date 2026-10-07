"""GOAL-20261008-033 EC-03 判据：**续跑覆盖度的声明集与源码对账**。

GOAL-032 EC-03 把 `rebuild_and_resume` 的覆盖度落成八行矩阵，但「不处理」清单**是代表而非
穷尽**（该轮 `W-4`）。本判据把那张表推进到**声明集穷尽枚举**，并让「声明」与「源码」
**双向对账** —— 五件事（缺一即判红）：

1. **判据落点真实存在**：声明集里每条 `evidence` 点名的 `文件::用例名` 必须**真的存在**
   （`ast` 解析目标文件找函数定义）⇒ 幽灵引用（指着一个不存在的用例）判红。
   本条是**自查**：建档首版我就写过 7 个不存在的用例名，跑一次这条判据即全部抓出。
2. **理由非空且不空洞**：带 `reason` 的条目（而非 `evidence`）理由长度有下界。
3. **受判面 = 声明集**（承 `MEM-20260928-160`）：断言的是声明集的**规模下界**与
   **三面各自的下界**，不是 `declared ∩ evidence` 之类的交集 —— 交集会让
   「声明了但没判据」在构造上不可能被报出。
4. **与入口源码对账**：`services/api/run_resume.py` 的**拒绝面**字面量（`ResumeAttempt`
   的 refusal 串）必须**逐条**在声明集里有归属；源码新增一条而声明集没跟上 ⇒ 判红。
5. **反向**：声明集里标为 `REFUSED` 的条目，其 `situation` 不得描述一个源码**不可能**
   产生的结局（幽灵条目）⇒ 由 4 的映射与 1 的存在性共同承担，另加一条下界断言。

**射程边界（如实登记）**：本文件判「声明集与源码/判据文件对得上账」，**不**重跑那些
行为判据（它们各自的文件就是判据）。第 4 条对账的是**拒绝面的字面量**，不是「所有可能
的异常」—— 入口的异常路径前缀是拼装的（`dependency_prefix` + 异常名），没有可枚举的
字面量集合，这条边界写在下面 `_SOURCE_REFUSALS` 的注释里。
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.tooling.resume_coverage_declaration import (
    DECLARED_CASES,
    HANDLED,
    MIN_DECLARED_CASES,
    MIN_HANDLED,
    MIN_NOT_THIS_ENTRY,
    MIN_REFUSED,
    NOT_THIS_ENTRY,
    REFUSED,
    findings,
)

_ROOT = Path(__file__).resolve().parents[2]
_ENTRY = "services/api/run_resume.py"

#: 入口里**可枚举**的拒绝字面量（`ResumeAttempt(refusal="…")`）。异常路径（`dependency_prefix`
#: + 异常名）**不在此列**：它是拼装的，没有穷尽的字面量集合 —— 那条边界由
#: `test_the_declared_set_covers_every_refusal_literal_in_the_entry` 的说明承担。
_SOURCE_REFUSALS: tuple[str, ...] = (
    "run orchestration service is not configured",
    "rebuilt preflight does not pass; refusing to resume",
)

#: `reason`（而非 `evidence`）类条目的理由长度下界。
_MIN_REASON = 30


def _source_text(relative: str) -> str:
    path = _ROOT / relative
    assert path.is_file(), f"声明集点名的文件不存在: {relative}"
    return path.read_text(encoding="utf-8")


def _defined_functions(relative: str) -> set[str]:
    """目标文件里**定义**的（同步/异步）函数名（模块级与类内都算）。"""
    tree = ast.parse(_source_text(relative))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }


def _split_evidence(evidence: str) -> tuple[str, str]:
    assert "::" in evidence, f"判据落点必须写成 `文件::用例名`: {evidence!r}"
    path, name = evidence.split("::", 1)
    return path.strip(), name.strip()


def test_the_declared_set_is_well_formed() -> None:
    """声明集自审：无重复 id / 情形非空 / 判据与理由恰好一个 / 三面下界。"""
    problems = findings()
    assert problems == [], "声明集自审未通过:\n" + "\n".join(problems)
    assert len(DECLARED_CASES) >= MIN_DECLARED_CASES
    counts = {
        verdict: sum(1 for c in DECLARED_CASES if c.verdict == verdict)
        for verdict in (HANDLED, REFUSED, NOT_THIS_ENTRY)
    }
    assert counts[HANDLED] >= MIN_HANDLED, counts
    assert counts[REFUSED] >= MIN_REFUSED, counts
    assert counts[NOT_THIS_ENTRY] >= MIN_NOT_THIS_ENTRY, counts


def test_every_declared_evidence_really_exists() -> None:
    """**幽灵引用判红**：每条 `evidence` 的文件存在**且**其中的用例名真的被定义。

    这条是本判据的**自查面**：建档首版我写了 7 个不存在的用例名（凭印象拼的），
    全被这一条抓出 ⇒ 声明集不得引用不存在的证据。
    """
    problems: list[str] = []
    for case in DECLARED_CASES:
        if not case.evidence:
            continue
        relative, name = _split_evidence(case.evidence)
        if not (_ROOT / relative).is_file():
            problems.append(f"{case.id}: 判据文件不存在 {relative}")
            continue
        if name not in _defined_functions(relative):
            problems.append(f"{case.id}: {relative} 里没有用例 {name}")
    assert problems == [], "声明集引用了不存在的证据:\n" + "\n".join(problems)


def test_entries_with_a_reason_instead_of_evidence_say_something_substantive() -> None:
    """带 `reason` 的条目理由必须够长（不许用「见文档」这类占位）。"""
    thin = [case.id for case in DECLARED_CASES if case.reason and len(case.reason) < _MIN_REASON]
    assert thin == [], f"理由过短的声明条目: {thin}"
    assert any(case.reason for case in DECLARED_CASES), (
        "声明集必须至少有一条走 `reason` 面（否则那条分支是死代码）"
    )


def test_the_entry_really_exposes_every_outcome_shape_the_set_claims() -> None:
    """入口源码必须真的**存在**声明集所描述的那几种形态（不是想当然）。"""
    text = _source_text(_ENTRY)
    for needle in ("ResumeAttempt(", "early_refusal()", "dependency_prefix()"):
        assert needle in text, f"入口源码里找不到声明集依赖的形态: {needle}"
    # 成功面：outcome 与 refusal 是同一个值对象的两个字段（声明集的 HANDLED/REFUSED 源自此）
    assert "outcome" in text and "refusal" in text


def test_every_source_literal_is_bound_to_exactly_one_declared_case() -> None:
    """**按字段对账**（不是按散文猜关键词）：每个可枚举字面量**恰好一条**声明条目认领。

    首版这条用「关键词在散文里出现」判覆盖 —— 结果是英文口径与中文情形描述对不上，
    判据红了但那是**判据自己的形态**问题（换了措辞就会误判）。改成 `source_literals`
    字段后，绑定是显式的：漏了判红、重复认领也判红。
    """
    claimed: dict[str, list[str]] = {}
    for case in DECLARED_CASES:
        for literal in case.source_literals:
            claimed.setdefault(literal, []).append(case.id)

    missing = [literal for literal in _SOURCE_REFUSALS if literal not in claimed]
    assert missing == [], f"源码拒绝字面量没有声明条目认领: {missing}"
    duplicated = {literal: owners for literal, owners in claimed.items() if len(owners) > 1}
    assert duplicated == {}, f"同一字面量被多条声明认领（归属不清）: {duplicated}"
    # 反向：声明的绑定必须真的在源码里
    for case in DECLARED_CASES:
        for literal in case.source_literals:
            assert literal in _source_text(_ENTRY), (
                f"{case.id} 绑定的字面量在入口里不存在: {literal!r}"
            )


def test_the_overlay_is_not_an_intersection() -> None:
    """**反掩蔽**（承 MEM-160 / MEM-20261005-187）：受判面是**声明集本身**。

    断言形态：按**声明集逐条**遍历，每条要么有判据、要么有理由 ——
    而不是先取「有判据的」再断言它们都有判据（那是在交集上恒真）。
    `findings()` 就是那个逐条遍历器；本条另断言它对**规模缩水**与**面缩水**会报出问题
    （否则上面的空集是空真）。

    **受判面自证**：合成面的构造被 `DeclaredCase.__post_init__` 挡住（「恰好一个非空」是
    构造期不变量）⇒ 这里改用**规模/面**两个维度做自证：把声明集截短或抽掉一整面，
    `findings()` 必须报出问题。
    """
    from tests.tooling.resume_coverage_declaration import REFUSED as _REFUSED

    assert findings() == [], "声明集不得有未认领条目"

    truncated = DECLARED_CASES[:2]
    assert findings(truncated), "截短的声明集必须被报出（规模下界在起作用）"

    no_refused = tuple(case for case in DECLARED_CASES if case.verdict != _REFUSED)
    assert findings(no_refused), "抽掉整个 REFUSED 面必须被报出（三面下界在起作用）"

    # 构造期不变量本身也自证一次：无判据无理由的条目**构造不出来**
    from tests.tooling.resume_coverage_declaration import DeclaredCase

    with pytest.raises(ValueError):
        DeclaredCase(id="synthetic", situation="x", verdict=NOT_THIS_ENTRY)
