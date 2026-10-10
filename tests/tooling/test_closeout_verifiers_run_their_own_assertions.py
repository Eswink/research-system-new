"""GOAL-20261010-043 EC-04 判据：**收口验证器必须跑自己的断言集**（形态在构造上不可能再通过）。

**它把什么变成机械事实**（两条，逐条）：

1. **声明 == 实载**：每个 `tools/verify_goal0NN_closeout.py` 里 `ASSERTIONS` 常量声明的路径，
   必须**等于** `_load_assertions()` 实际加载的路径 —— **按 AST 读**（不靠文本巧合）。
   实测的历史缺陷：`verify_goal038/039/040_closeout.py` 声明自己的断言集却加载
   `goal037_closeout_assertions.py` ⇒ 三处**自有断言从未在收口复检里运行**。
2. **被点名的断言集必须可执行**：每个被点名的 `goal0NN_closeout_assertions.py` 必须能
   在本树调通 `assertion_verdicts(root, toolbox)` **不抛异常**。
   实测的历史缺陷：`goal040_closeout_assertions.py` 按**文本**匹配
   `_non_success_terminal(program, existing, last)`，而 GOAL-041 已正当给该函数加了
   `programs` 形参 ⇒ 调用它直接**崩溃**（`ValueError: substring not found`）——
   **崩了就不是判据**。

**两向反证**：① 合成一个「声明 A、实载 B」的验证器 ⇒ 判据**必须报红**；
② 合成一个「断言集会抛异常」的形态 ⇒ 判据**必须报红**；③ 真实树 ⇒ 绿。
没有 ①②，「声明 == 实载」可能只是两个都在场（**不该绿时绿**）。

**射程边界（如实登记）**：本判据钉的是「**加载对**、**跑得动**」两件事；
它**不**禁止断言集内部使用文本锚点（`U-2`：其它历史断言集的同类脆弱性未普查），
也**不**重跑历史收口复检（`U-1`）。
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_TOOLS = _ROOT / "tools"
_TOOLBOX = _TOOLS / "closeout_recheck_tools.py"

#: 收口验证器的**全量清单**（逐条写死；新增验证器必须显式登记 —— 与 `IN_SCOPE` 同一纪律）。
#: **射程的世代边界（如实登记）**：GOAL-031 起收口验证器用「外部断言集」形态
#: （`ASSERTIONS` + `_load_assertions()` + `goal0NN_closeout_assertions.py`）；
#: GOAL-015/023…030 属**更早的一代**（断言内联在验证器里、**没有**断言集文件）⇒
#: 「声明 == 实载」这条规矩对它们**不适用**（无声明面可对拍），它们由
#: `LEGACY_INLINE` 逐条登记（不是遗漏，是**形态不同**）。
_VERIFIERS: tuple[str, ...] = (
    "tools/verify_goal031_closeout.py",
    "tools/verify_goal032_closeout.py",
    "tools/verify_goal033_closeout.py",
    "tools/verify_goal034_closeout.py",
    "tools/verify_goal035_closeout.py",
    "tools/verify_goal036_closeout.py",
    "tools/verify_goal037_closeout.py",
    "tools/verify_goal038_closeout.py",
    "tools/verify_goal039_closeout.py",
    "tools/verify_goal040_closeout.py",
    "tools/verify_goal041_closeout.py",
    "tools/verify_goal042_closeout.py",
    "tools/verify_goal043_closeout.py",
    "tools/verify_goal044_closeout.py",
)
#: 断言**内联**的旧一代验证器（逐条登记 + 理由非空；与 `_VERIFIERS` 的分区判据同形）。
LEGACY_INLINE: tuple[tuple[str, str], ...] = (
    ("tools/verify_goal015_closeout.py", "旧一代：断言内联，无外部断言集（该形态尚未引入）"),
    ("tools/verify_goal023_closeout.py", "旧一代：断言内联，无外部断言集"),
    ("tools/verify_goal024_closeout.py", "旧一代：断言内联，无外部断言集"),
    ("tools/verify_goal025_closeout.py", "旧一代：断言内联，无外部断言集"),
    ("tools/verify_goal026_closeout.py", "旧一代：断言内联，无外部断言集"),
    ("tools/verify_goal027_closeout.py", "旧一代：断言内联，无外部断言集"),
    ("tools/verify_goal028_closeout.py", "旧一代：断言内联，无外部断言集"),
    ("tools/verify_goal029_closeout.py", "旧一代：断言内联，无外部断言集"),
    ("tools/verify_goal030_closeout.py", "旧一代：断言内联，无外部断言集"),
)
#: 清单下界（射程非空 ⇒ 断言不空转；与全仓「受判面非空」同一条纪律）。
_MIN_VERIFIERS = 14

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


def _declared_assertions(source: str) -> str | None:
    """验证器里 `ASSERTIONS = "..."` 的取值（AST 读模块级赋值）。"""
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return None
    for node in parsed.body:
        if isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "ASSERTIONS" in names and isinstance(node.value, ast.Constant):
                return str(node.value.value)
    return None


def _loaded_assertions(source: str) -> str | None:
    """`_load_assertions()` 里 `Path(...) / "<file>"` 的那个文件名（AST 读调用链）。

    判法：找 `_load_assertions` 函数体里的 `BinOp`（`Div`），其右操作数是字符串常量
    ⇒ 它就是被加载的文件名。**按 AST 读**而不是文本搜索 —— 后者会被注释里的同一串骗过。
    """
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return None
    for node in ast.walk(parsed):
        if not isinstance(node, ast.FunctionDef) or node.name != "_load_assertions":
            continue
        for inner in ast.walk(node):
            if not isinstance(inner, ast.BinOp) or not isinstance(inner.op, ast.Div):
                continue
            right = inner.right
            if isinstance(right, ast.Constant) and isinstance(right.value, str):
                return right.value
    return None


def _load_module(path: Path, name: str) -> Any:
    """按路径加载（`tools/` 不是包；**先写 `sys.modules` 再 `exec_module`**，
    否则 dataclasses 解析注解时会崩）。"""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _toolbox() -> Any:
    return _load_module(_TOOLBOX, "goal043_toolbox")


#: 没有 `ASSERTIONS` 常量的验证器（常量是 GOAL-033 起的写法）—— **实载对拍仍然适用**
#: （实载必须等于**本 GOAL 自己的**断言集，按文件名前缀判）；逐条登记，理由非空。
_NO_ASSERTIONS_CONSTANT: dict[str, str] = {
    "tools/verify_goal031_closeout.py": "断言集路径直接写在 _load_assertions 里（该常量尚未引入）",
    "tools/verify_goal032_closeout.py": "同上（常量自 GOAL-033 起才有）",
}


def _expected_assertion_file(relative: str) -> str:
    """该验证器**应当**加载的断言集文件名（由验证器自身的 GOAL 编号推出）。"""
    tail = relative.split("verify_goal", 1)[1].split("_", 1)[0]
    digits = "".join(ch for ch in tail if ch.isdigit())
    return f"goal{digits}_closeout_assertions.py"


def test_every_verifier_declares_the_assertion_set_it_actually_loads() -> None:
    """**声明 == 实载**（本 GOAL 的靶子形态；逐条对拍，缺一即判红）。

    两种写法都接受，但都要求「实际加载的**就是自己的**」：
    ① 有 `ASSERTIONS` 常量 ⇒ 它与实载必须**逐字相同**；
    ② 无常量（`_NO_ASSERTIONS_CONSTANT` 逐条登记）⇒ 实载必须等于**该 GOAL 自己的**断言集名。
    """
    assert len(_VERIFIERS) >= _MIN_VERIFIERS, "射程过小 ⇒ 受判面不成立"
    mismatched: list[str] = []
    unreadable: list[str] = []
    for relative in _VERIFIERS:
        path = _ROOT.joinpath(*relative.split("/"))
        assert path.is_file(), f"清单点名的验证器不在树：{relative}"
        source = path.read_text(encoding="utf-8")
        declared = _declared_assertions(source)
        loaded = _loaded_assertions(source)
        expected = _expected_assertion_file(relative)
        if declared is None and relative in _NO_ASSERTIONS_CONSTANT:
            # ② 无常量：直接对拍「实载 == 自己那份」
            if loaded != expected:
                mismatched.append(f"{relative}: 无 ASSERTIONS 常量；实载 {loaded!r} ≠ {expected!r}")
            elif loaded is None:
                unreadable.append(f"{relative}（loaded=None）")
            continue
        if declared is None or loaded is None:
            unreadable.append(f"{relative}（declared={declared!r} loaded={loaded!r}）")
            continue
        if declared.rsplit("/", 1)[-1] != loaded:
            mismatched.append(f"{relative}: 声明 {declared!r} 但实载 {loaded!r}")
    assert not unreadable, ("这两个读法必须能从验证器里取到值（形状假设失效）", unreadable)
    assert not mismatched, (
        "收口验证器必须加载**自己的**断言集（否则自有断言从未运行）",
        mismatched,
    )


def test_every_named_assertion_set_is_executable_on_this_tree() -> None:
    """**被点名的断言集必须可执行**（崩了就不是判据；本 GOAL 的第二个靶子形态）。"""
    toolbox = _toolbox()
    broken: list[str] = []
    for relative in _VERIFIERS:
        path = _ROOT.joinpath(*relative.split("/"))
        loaded = _loaded_assertions(path.read_text(encoding="utf-8"))
        assert loaded is not None, relative
        target = _TOOLS / loaded
        assert target.is_file(), f"{relative} 加载的 {loaded} 不在树"
        module = _load_module(target, f"goal043_{loaded.removesuffix('.py')}")
        verdicts_fn = getattr(module, "assertion_verdicts", None)
        assert callable(verdicts_fn), f"{loaded} 缺少 assertion_verdicts（公开面变了）"
        try:
            verdicts = verdicts_fn(_ROOT, toolbox)
        except Exception as error:  # noqa: BLE001 - 判据必须把**任何**崩溃报成红
            broken.append(f"{loaded}: {type(error).__name__}: {error}")
            continue
        assert verdicts, f"{loaded} 的断言集为空 ⇒ 受判面不成立"
    assert not broken, ("这些断言集在本树上**不可执行**（崩溃不是判负，是资产坏了）", broken)


def test_every_named_assertion_set_reports_no_negative_on_this_tree() -> None:
    """**断言集在本树上不得有判负**（把 `U-2` 的「同类脆弱性」变成机器的）。

    **为什么需要**（GOAL-20261010-043 收口后**新实测**到的第三个实例）：`goal031` 的
    `ec03-run-completed-carries-the-skip-facts` 按**文本**要求在 `phase_runner.py` 里出现
    `"skipped"` 字面量；而 GOAL-20261009-042 EC-03 把该载荷抽成**唯一构造点**
    ⇒ 字面量**搬了家**（行为逐字保持）⇒ 该判据**盯错位置**判负。
    ⇒ 「可执行」还不够：**跑出判负**同样是资产坏了（被引代码演进 ⇒ 断言失配）。

    **射程（如实登记）**：本条要求「**判负数为 0**」；它**不**要求「断言条数不变」，
    也**不**禁止断言集内部使用文本锚点（只要求它们当前**没有**失配）。
    """
    toolbox = _toolbox()
    negative: list[str] = []
    for relative in _VERIFIERS:
        path = _ROOT.joinpath(*relative.split("/"))
        loaded = _loaded_assertions(path.read_text(encoding="utf-8"))
        assert loaded is not None, relative
        module = _load_module(_TOOLS / loaded, f"goal043_neg_{loaded.removesuffix('.py')}")
        verdicts = module.assertion_verdicts(_ROOT, toolbox)
        failed = [item.name for item in verdicts if not item.ok]
        if failed:
            negative.append(f"{loaded}: {failed}")
    assert not negative, (
        "这些断言集在本树上**有判负** ⇒ 被引代码演进导致失配（资产坏了，不是产品缺陷）",
        negative,
    )


def test_the_verifiers_list_partitions_every_verifier_explicitly() -> None:
    """**清单不得漏项**：`tools/` 下的 `verify_goal0NN_closeout.py` 要么在射程内、要么登记在案。

    为什么（与 `IN_SCOPE` 同一纪律）：清单是把「必须跑自己的断言」这条规矩**钉在射程上**，
    漏一个 = 给新验证器留了一个**默认不覆盖**的空档。**登记项必须有非空理由**
    （「登记了」与「说明了为什么」是两件事），且**分区不得重叠**（既在射程又登记 = 自相矛盾）。
    """
    on_disk = sorted(f"tools/{path.name}" for path in _TOOLS.glob("verify_goal*_closeout.py"))
    in_scope = set(_VERIFIERS)
    legacy = dict(LEGACY_INLINE)
    overlap = sorted(in_scope & set(legacy))
    assert not overlap, ("同一条既在射程内又被登记为旧一代", overlap)
    missing = [item for item in on_disk if item not in in_scope and item not in legacy]
    assert not missing, ("这些验证器没被分类（新增时必须显式决定）", missing)
    stale = sorted((in_scope | set(legacy)) - set(on_disk))
    assert not stale, ("清单引用了不存在的验证器（清单已陈旧）", stale)
    empty = sorted(path for path, reason in LEGACY_INLINE if not reason.strip())
    assert not empty, ("旧一代登记必须给非空理由", empty)
    assert len(legacy) >= 5, f"旧一代清单只有 {len(legacy)} 条 ⇒ 疑似被清空"


class TestTheCriterionBitesInBothDirections:
    """两向反证：判据在合成缺陷上**必须报红**（否则它只是「都在场」的同义反复）。"""

    def test_a_declared_but_differently_loaded_verifier_is_reported(self, tmp_path: Path) -> None:
        """反向①：声明 A、实载 B ⇒ `_declared_assertions` / `_loaded_assertions` 的差必被看见。"""
        source = (
            'ASSERTIONS = "tools/goal999_closeout_assertions.py"\n\n\n'
            "def _load_assertions():\n"
            '    path = Path(__file__).resolve().parent / "goal037_closeout_assertions.py"\n'
            "    return path\n"
        )
        declared = _declared_assertions(source)
        loaded = _loaded_assertions(source)
        assert declared is not None and loaded is not None
        assert declared.rsplit("/", 1)[-1] != loaded, "（这条合成例本身必须是「不一致」的）"

    def test_a_matching_verifier_is_accepted(self) -> None:
        """正控制：声明与实载一致 ⇒ 两个读法给出同一个名字（判法本身成立）。"""
        source = (
            'ASSERTIONS = "tools/goal999_closeout_assertions.py"\n\n\n'
            "def _load_assertions():\n"
            '    path = Path(__file__).resolve().parent / "goal999_closeout_assertions.py"\n'
            "    return path\n"
        )
        declared = _declared_assertions(source)
        loaded = _loaded_assertions(source)
        assert declared is not None and loaded is not None
        assert declared.rsplit("/", 1)[-1] == loaded

    def test_an_assertion_set_that_raises_is_reported(self, tmp_path: Path) -> None:
        """反向②：断言集**抛异常** ⇒ 可执行性判据必须报红（崩了不是判负）。"""
        broken = tmp_path / "goal999_closeout_assertions.py"
        broken.write_text(
            'def assertion_verdicts(root, toolbox):\n    raise ValueError("substring not found")\n',
            encoding="utf-8",
            newline="\n",
        )
        module = _load_module(broken, "goal043_broken_probe")
        with pytest.raises(ValueError, match="substring not found"):
            module.assertion_verdicts(_ROOT, _toolbox())

    def test_the_readers_are_not_fooled_by_a_comment(self) -> None:
        """反面：注释里出现同一串**不得**被读成实载（AST 读，不靠文本巧合）。"""
        source = (
            'ASSERTIONS = "tools/goal999_closeout_assertions.py"\n'
            '# 曾经加载过 "goal037_closeout_assertions.py"（注释里的说明不是实载）\n\n\n'
            "def _load_assertions():\n"
            '    path = Path(__file__).resolve().parent / "goal999_closeout_assertions.py"\n'
            "    return path\n"
        )
        assert _loaded_assertions(source) == "goal999_closeout_assertions.py"
