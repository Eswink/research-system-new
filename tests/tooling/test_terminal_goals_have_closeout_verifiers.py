"""GOAL-20261024-096 EC-05(iii)：**每个受判终态 GOAL 都必须有收口验证器**。

**它补哪一道缝**（本轮实测）：`tools/verify_goal{076,090,095}_closeout.py` **从未存在**，
而分类判据（`test_closeout_verifiers_run_their_own_assertions.py`）只查「**磁盘上存在的**
验证器是否被分类」⇒ 缺失的文件**两头都不报**：它不在 `_VERIFIERS` 里（没有人看），
也不在 `LEGACY_INLINE` / `_EXCLUDED` 里（没有人问「为什么不在」）。于是「每轮新建收口
验证器」这件固定交付一直靠人记 —— 091…094 有、090/095/076 没有，而没有任何判据在意。

**判什么**（缺一即判红）：

1. 受判面内每个**终态** GOAL 的编号 `NNN`，`tools/verify_goal<NNN>_closeout.py` 必须在树；
2. 它必须被分类：要么在 `_VERIFIERS`（外部断言集形态），要么在 `LEGACY_INLINE`
   （断言内联的旧一代 + 理由非空）—— 不在任何一边 = 没人看的验证器；
3. 受判面**非空**（空真不算通过：一个都没有 GOAL 时本判据失去对象，必须点名）。

**受判面**与 `test_goal_ledger_covers_every_commit.py` **同一套推导**（`_program_seq` +
`_CUTOFF_SEQ` + `_CUTOFF_DATE`）：那边判「台账是否穷尽提交」，这边判「收口资产是否齐备」，
受判对象不同、受判面必须同一个 —— 两套范围会让「谁在管内」本身不可判。

**祖父条款**：`_CUTOFF_SEQ = 64`（本轮）。更早的 GOAL 里 `090` / `095` / `076` 缺验证器
这件事**如实登记在 GOAL 的残余节，不追认成当时的义务**（回填旧记录等于把今天的要求
追认成历史义务，且会让本轮为凑绿去补一批旧文件 —— 那正是 GOAL-092 诊断出的反面）。

**两向按压**（在本 PLAN 里取证）：
① 从 `_VERIFIERS` 删掉 096 那一行 ⇒ 判红并**点名** 096（「未分类」分支）；
② 把 `_CUTOFF_SEQ` 抬到 97（受判面为空）⇒ 判红并点名「受判面为空」（空真守卫）。
"""

from __future__ import annotations

import ast
import importlib.util
import re
import sys
from pathlib import Path
from typing import Any, cast

_ROOT = Path(__file__).resolve().parents[2]
_TOOLS = _ROOT / "tools"
_GOALS = _ROOT / ".cursor" / "plans" / "goals"
_CHARTER = _GOALS / "MAINLINE.md"
REGISTRY = _ROOT / "tests" / "tooling" / "test_closeout_verifiers_run_their_own_assertions.py"

#: 受判面下界（本轮）：更早的缺口登记在残余节，不追认（见模块 docstring）。
_CUTOFF_SEQ = 64

#: 终态状态（与台账判据同一词表）。
_TERMINAL = frozenset({"ACHIEVED", "BLOCKED", "ABANDONED"})


def _load_registry() -> Any:
    """按路径加载注册判据模块（取它的两份清单；`tests/` 不是包）。"""
    spec = importlib.util.spec_from_file_location("goal096_registry", REGISTRY)
    assert spec is not None and spec.loader is not None, REGISTRY
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal096_registry"] = module
    spec.loader.exec_module(module)
    return module


def _module_literal(text: str, name: str) -> object:
    """模块级常量 `name` 的**字面量值**（按 AST 取，不执行模块）。"""
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name and node.value is not None:
                return ast.literal_eval(node.value)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"{REGISTRY.name} 里没有模块级常量 {name}")


def _program_rows() -> dict[str, int]:
    """宪章程序表 → `{GOAL id: 序}`（只认 `| 序 | GOAL-… |` 形态的行）。"""
    rows: dict[str, int] = {}
    pattern = re.compile(r"^\|\s*(\d+)\s*\|\s*(GOAL-\d{8}-\d{3})\s*\|")
    for line in _CHARTER.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            rows[match.group(2)] = int(match.group(1))
    return rows


def _frontmatter_value(text: str, key: str) -> str:
    """frontmatter 里某个键的值（只扫首个 `---` 块）。"""
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    block = text[: end if end != -1 else len(text)]
    prefix = f"{key}:"
    for line in block.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return ""


def _terminal_goals_in_scope() -> list[tuple[str, int]]:
    """受判面内的终态 GOAL ⇒ `[(id, 序)]`（序 < 下界 ⇒ 祖父条款，不进面）。"""
    rows = _program_rows()
    found: list[tuple[str, int]] = []
    for path in sorted(_GOALS.glob("GOAL-*.md")):
        text = path.read_text(encoding="utf-8")
        goal_id = _frontmatter_value(text, "id")
        if _frontmatter_value(text, "status") not in _TERMINAL:
            continue
        seq = rows.get(goal_id)
        if seq is not None and seq >= _CUTOFF_SEQ:
            found.append((goal_id, seq))
    return found


def _number(goal_id: str) -> str:
    """GOAL id 的编号（`GOAL-20261024-096` ⇒ `096`；文件名用的是三位数）。"""
    return goal_id.rsplit("-", 1)[-1]


def _classified(verifiers: set[str], legacy: set[str]) -> set[str]:
    """两份清单点名的验证器文件名（去目录前缀）。"""
    names = {item.rsplit("/", 1)[-1] for item in verifiers}
    names |= {item.rsplit("/", 1)[-1] for item in legacy}
    return names


def test_the_scope_is_not_empty() -> None:
    """**空真不算通过**：受判面为空 ⇒ 本判据失去对象，必须点名判红。"""
    in_scope = _terminal_goals_in_scope()
    assert in_scope, (
        f"受判面为空（下界序 {_CUTOFF_SEQ}）⇒ 本条失去判据对象；"
        "要么下界写错，要么程序表没有登记本轮 GOAL"
    )


def test_every_terminal_goal_in_scope_has_a_closeout_verifier() -> None:
    """每个受判终态 GOAL 的 `tools/verify_goal<NNN>_closeout.py` 必须在树。"""
    missing: list[str] = []
    for goal_id, seq in _terminal_goals_in_scope():
        name = f"verify_goal{_number(goal_id)}_closeout.py"
        if not (_TOOLS / name).is_file():
            missing.append(f"{goal_id}（序 {seq}）缺 tools/{name}")
    assert not missing, ("收口验证器是每轮的固定交付；缺了要当轮补", missing)


def test_every_closeout_verifier_is_classified() -> None:
    """每个受判终态 GOAL 的验证器都必须被**分类**（外部断言集 / 内联旧一代）。"""
    registry_text = REGISTRY.read_text(encoding="utf-8")
    verifiers = set(cast(list[str], _module_literal(registry_text, "_VERIFIERS")))
    legacy_entries = cast(list[tuple[str, str]], _module_literal(registry_text, "LEGACY_INLINE"))
    legacy = {entry[0] for entry in legacy_entries}
    classified = _classified(verifiers, legacy)
    unclassified: list[str] = []
    for goal_id, seq in _terminal_goals_in_scope():
        name = f"verify_goal{_number(goal_id)}_closeout.py"
        if (_TOOLS / name).is_file() and name not in classified:
            unclassified.append(f"{goal_id}（序 {seq}）的 {name} 不在任何一份清单里")
    assert not unclassified, (
        "未分类的验证器**没有人看**（分类判据的射程只覆盖清单成员）",
        unclassified,
    )


def test_the_registry_lists_every_verifier_the_scope_requires() -> None:
    """受判面点名的那几个验证器必须逐个在 `_VERIFIERS`（两份清单的分区判据同形）。"""
    registry_text = REGISTRY.read_text(encoding="utf-8")
    verifiers = set(cast(list[str], _module_literal(registry_text, "_VERIFIERS")))
    expected = {
        f"tools/verify_goal{_number(goal_id)}_closeout.py"
        for goal_id, _seq in _terminal_goals_in_scope()
    }
    missing = sorted(expected - verifiers)
    assert not missing, ("这些验证器没有被 `_VERIFIERS` 收录（分类判据看不见它们）", missing)


def test_legacy_entries_carry_a_reason() -> None:
    """`LEGACY_INLINE` 的每一条都带**非空理由**（与两份清单的分区同形）。"""
    registry_text = REGISTRY.read_text(encoding="utf-8")
    legacy = cast(list[tuple[str, str]], _module_literal(registry_text, "LEGACY_INLINE"))
    empty = [entry[0] for entry in legacy if not entry[1].strip()]
    assert not empty, ("内联旧一代必须逐条写理由（否则它就是「没人看的例外」）", empty)


def test_this_rounds_verifier_is_registered() -> None:
    """本轮的验证器在册（防止「本轮建了但没登记」这种半成品）。"""
    registry_text = REGISTRY.read_text(encoding="utf-8")
    verifiers = set(cast(list[str], _module_literal(registry_text, "_VERIFIERS")))
    assert "tools/verify_goal096_closeout.py" in verifiers, sorted(verifiers)[-6:]
