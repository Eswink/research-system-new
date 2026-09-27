"""GOAL-20260928-022 EC-03 判据：复检脚本规范的每一条都得有东西在检查它。

**判什么**：

1. 规范页在树并**已登记**在 `docs/INDEX.md`；
2. 六条环境口径**逐条在位**（结构性锚点：条目标签）；
3. **至少 3 条**有**机械判据**（计数断言，不是散文）；
4. 每条被点名的机械判据都**指向一个存在的文件里一个存在的测试函数** ——
   用 **AST** 读**声明**（不是文本里出现过那个名字），因此**改名即判红**：
   这就是「**条款不得悬空**」的形态（承既有
   `test_record_face_is_covered_by_the_gate.py` 对 SOP 条款的钉法）；
5. 没有机械判据的那几条，必须有一条**可复跑检查**的小节（`### ③ / ⑤ 的可复跑检查`）。

**为什么要它**：规范页是散文；散文不会自己失效 —— 失效的是**它指向的东西**。
把「哪一条由谁检查」写成可解析的映射并断言其**可解析性**，
才让「规范里每条都附了判据或可复跑检查」从一句声明变成**可复核的事实**。
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs" / "architecture" / "RECHECK_SCRIPT_CONVENTIONS.md"
INDEX = ROOT / "docs" / "INDEX.md"
ENTRY_JUDGE = "tests/tooling/test_two_tree_recheck_entry.py"

#: 六条口径在规范页里的**结构性锚点**（条目标签；改文案即判红，提示复核本映射）。
ITEM_ANCHORS: tuple[str, ...] = (
    "共用解释器",
    "纯度",
    "文本 vs 二进制读写",
    "落点断言",
    "进程卫生",
    "路径无关输出",
)

#: 有**机械判据**的口径：条目标签 ⇒ (判据文件, 测试函数名)。函数名按 **AST 读声明**。
JUDGED_ITEMS: dict[str, tuple[str, str]] = {
    "共用解释器": (ENTRY_JUDGE, "test_both_trees_use_the_same_interpreter"),
    "纯度": (ENTRY_JUDGE, "test_impure_output_is_refused_not_filtered"),
    "落点断言": (ENTRY_JUDGE, "test_both_trees_agree_when_assertions_agree"),
    "路径无关输出": (ENTRY_JUDGE, "test_path_dependent_verdict_is_refused_not_normalized"),
}

#: 只有**可复跑检查**（不设判据）的口径 ⇒ 规范页里必须有对应的检查小节。
REPRODUCIBLE_CHECK_SECTIONS: tuple[str, ...] = (
    "### ③ 的可复跑检查",
    "### ⑤ 的可复跑检查",
)

#: 「至少半数有判据」的下界（六条里 ≥ 3）。
MIN_JUDGED_ITEMS = 3


def _defined_functions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_the_conventions_doc_is_in_the_tree_and_registered() -> None:
    """规范页在树，且 `docs/INDEX.md` 登记了它。"""
    assert DOC.is_file(), f"规范页不在树：{DOC}"
    index = INDEX.read_text(encoding="utf-8")
    assert "architecture/RECHECK_SCRIPT_CONVENTIONS.md" in index, (
        "规范页未登记在 docs/INDEX.md ⇒ 索引不到就等于不存在"
    )


def test_all_six_convention_items_are_present() -> None:
    """六条口径逐条在位（少了哪条就报哪条）。"""
    text = DOC.read_text(encoding="utf-8")
    missing = [anchor for anchor in ITEM_ANCHORS if anchor not in text]
    assert not missing, f"规范页缺少这些口径：{missing}"


def test_at_least_half_of_the_items_have_a_mechanical_judge() -> None:
    """**计数断言**：有机械判据的口径不少于 3 条（六条的半数）。"""
    assert len(JUDGED_ITEMS) >= MIN_JUDGED_ITEMS, (
        f"只有 {len(JUDGED_ITEMS)} 条有机械判据，规范自己的下界是 {MIN_JUDGED_ITEMS}"
    )
    unknown = sorted(set(JUDGED_ITEMS) - set(ITEM_ANCHORS))
    assert not unknown, f"映射里有不属于六条口径的键：{unknown}"


def test_every_named_judge_points_at_a_real_declaration() -> None:
    """**条款不得悬空**：每条被点名的判据都必须真的存在（按 **AST 读声明**）。

    判据文件改名、或测试函数改名 ⇒ 这里判红。**不**用文本里是否出现过那个名字来判 ——
    那会被注释 / 字符串里的同名字线喂饱（承 `MEM-20260925-141`）。
    """
    dangling: list[str] = []
    for label, (relative, function_name) in sorted(JUDGED_ITEMS.items()):
        path = ROOT / relative
        if not path.is_file():
            dangling.append(f"{label}: 判据文件不存在 {relative}")
            continue
        if function_name not in _defined_functions(path):
            dangling.append(f"{label}: {relative} 里没有测试函数 {function_name}()")
    assert not dangling, "条款悬空：" + "; ".join(dangling)


def test_items_without_a_judge_carry_a_reproducible_check() -> None:
    """没有机械判据的那几条必须有一条**可复跑检查**小节（不得只是散文）。"""
    text = DOC.read_text(encoding="utf-8")
    missing = [heading for heading in REPRODUCIBLE_CHECK_SECTIONS if heading not in text]
    assert not missing, f"缺可复跑检查小节：{missing}"


def test_every_item_is_covered_by_either_a_judge_or_a_check() -> None:
    """**覆盖断言**：六条口径逐条要么有判据、要么有可复跑检查 —— 没有第三种状态。"""
    checked_by_section = {
        "文本 vs 二进制读写": "### ③ 的可复跑检查",
        "进程卫生": "### ⑤ 的可复跑检查",
    }
    text = DOC.read_text(encoding="utf-8")
    uncovered: list[str] = []
    for anchor in ITEM_ANCHORS:
        if anchor in JUDGED_ITEMS:
            continue
        heading = checked_by_section.get(anchor)
        if heading is None or heading not in text:
            uncovered.append(anchor)
    assert not uncovered, f"这些口径没有任何检查：{uncovered}"
