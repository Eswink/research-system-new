#!/usr/bin/env python3
"""GOAL-20261004-029 收口复检（EC-05）：**标准断言集 + 本轮特有断言**。

与 GOAL-023…028 的收口验证器同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 直接调用
`tools/closeout_recheck_assertions.py`；本文件**只写 GOAL-029 特有的断言**：

- **逐 EC：判据文件在树 + 例数下界**（缺文件、例数掉下去，两向都判红）；
- **本 GOAL 的主干交付物逐条在位**（AST 断言，不是文本巧合）：
  ① `policy_enforcing_agent._evaluate` 用 `policy_scope_for`（F-6 修复）；
  ② `session_tool_invocation.make_tool_invoker` 用 `ScopedPolicy`（桥同源）；
  ③ `session_tools.SessionToolAction` 的 **`extra="allow"` 平铺**（第五个真缺陷的修复）；
  ④ `adapters/canonical/read_provider.py` 的 `CanonicalReadProvider` + `_TOOL_CAPABILITIES`；
  ⑤ `services/api/session_tool_support.py` 的 `canonical_read_register` /
     `session_tool_face` / `sqlite_session_tools` / `DEFAULT_SESSION_TOOL_BINDINGS`；
  ⑥ **两个组合根**都传 `register_session_tools`（W-1 的装配面缺口已闭）；
- **承接面读数**：出厂绑定表覆盖五条 A 组读能力 + provider 声明与之同源；
- ~~EC-04 的两份判词归档~~（**已移出**：见下方「为什么本验证器不检查归档」）；
- **`IN_SCOPE` 纯收紧**（本轮新增 `tools/verify_goal029_closeout.py`）；
- **记录面**：五个 EC 的终态、复检路径、子计划与记忆、残余与未覆盖逐条。

**为什么本验证器不检查 EC-04 的判词归档**（本轮实测到的**循环依赖**）：
两树入口在跑完两棵树后把判词**写回** `--verdict-current/--verdict-clean` 指定的路径。
若本验证器同时**读**那两个路径做断言，就会出现「输入即输出」：前一次失败留下的不等归档
会让这一次继续判红，而这一次写回的内容又成为下一次的输入 ⇒ **永不收敛**（实测：首跑
current 判红、clean 判绿，两棵树读到的是不同的历史残留）。
⇒ 归档的形态与一致性由**专属判据** `tests/tooling/test_two_tree_verdicts_are_archived.py`
负责（它跑在门禁里、在两树写入**之后**），本验证器只判 GOAL 自己的交付物。

用法：`python tools/verify_goal029_closeout.py --root <树根> --verdict-only`；判词行只有
`PASS` / `FAIL` 且不含任何树的绝对路径（否则两树入口会（正确地）拒绝）。

**时间口径**：GOAL 的 `EC-05` 在**本收口复检跑之前**仍是 `PENDING`（它的判词就是本文件产出的），
所以 EC-05 那条断言接受 `PASS ∪ PENDING` —— **不是**放宽，是**时序**（承 GOAL-027/028 同款注释）。
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any, cast


def _load_toolbox() -> object:
    """按**路径**加载同目录的工具集。

    `tools/` **不是包**（没有 `__init__.py`）⇒ 静态 `import tools.x` 会失败
    （承 `MEM-20261001-181`：按路径加载，且必须先写 `sys.modules` 再 `exec_module`，
    否则 dataclasses / typing 在模块自省时会崩）。
    """
    import importlib.util

    path = Path(__file__).resolve().parent / "closeout_recheck_tools.py"
    spec = importlib.util.spec_from_file_location("goal029_toolbox", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal029_toolbox"] = module
    spec.loader.exec_module(module)
    return module


TOOLBOX = cast(Any, _load_toolbox())

#: 类型别名（工具箱的 `VerdictLike` 是 Protocol；本文件只在注解里用）。
VerdictLike = Any


STANDARD = "tools/closeout_recheck_assertions.py"
SELF = "tools/verify_goal029_closeout.py"
TOOLING_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
GOAL = (
    ".cursor/plans/goals/"
    "GOAL-20261004-029-capability-coverage-expansion-and-out-of-the-box-runnability.md"
)
GOVERNANCE = ".cursor/skills/governance-check/scripts/validate.py"

#: 本 GOAL 的主干交付物（存在性 + AST 结构）。
POLICY_AGENT = "adapters/openhands/policy_enforcing_agent.py"
SESSION_TOOL_INVOCATION = "adapters/openhands/session_tool_invocation.py"
SESSION_TOOLS = "adapters/openhands/session_tools.py"
READ_PROVIDER = "adapters/canonical/read_provider.py"
SESSION_TOOL_SUPPORT = "services/api/session_tool_support.py"
SQLITE_ROOT = "services/api/composition.py"
PG_ROOT = "services/api/pg_composition.py"
CAPABILITIES = "examples/config/capabilities.yaml"
TOOL_PROVIDERS = "examples/config/tool_providers.yaml"

#: 逐 EC：判据文件 + **例数下界**（下界取本 GOAL 实测的 `def test_` 声明数 —— 与
#: `closeout_recheck_assertions` 同一计数口径；`pytest` 的**收集**数会因参数化更大）。
EC_FILES: dict[str, tuple[tuple[str, ...], tuple[int, ...]]] = {
    "ec01": (
        (
            "tests/adapters/openhands/test_session_tool_reaches_executor.py",
            "tests/adapters/canonical/test_canonical_read_provider.py",
            "tests/e2e/test_session_tool_call_on_the_default_assembly.py",
            "tests/api/test_production_session_tool_registration.py",
        ),
        (7, 17, 12, 13),
    ),
    "ec02": (
        ("tests/architecture/python/test_capability_coverage_is_implemented.py",),
        (8,),
    ),
    "ec03": (
        ("tests/architecture/python/test_deliverable_write_stays_on_the_canonical_path.py",),
        (9,),
    ),
    "ec04": (
        ("tests/tooling/test_two_tree_verdicts_are_archived.py",),
        (13,),
    ),
}

#: EC-04 的两份判词归档（**在树**的物证）。
VERDICT_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261004-029-verdict-current.txt"
VERDICT_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261004-029-verdict-clean.txt"

#: A 组射程内的五条读能力（出厂绑定表必须覆盖）。
IN_SCOPE_CAPABILITIES: tuple[str, ...] = (
    "artifact.read",
    "evidence.read",
    "workspace.read",
    "budget.read",
    "deliverable.read",
)

#: 子计划 / 复检 / 记忆（记录面逐条在位）。
CHILD_PLANS: tuple[str, ...] = (
    ".cursor/plans/tasks/PLAN-20261004-275-goal-029-ec01-session-tool-actually-executes.md",
    ".cursor/plans/tasks/PLAN-20261005-277-goal-029-ec01-session-tool-called-end-to-end.md",
    ".cursor/plans/tasks/PLAN-20261005-279-goal-029-ec03-write-capability-canonical-path.md",
)
MEMORIES: tuple[str, ...] = (
    ".cursor/memory/entries/MEM-20261004-183-session-tool-scope-must-be-the-capability-scope.md",
    ".cursor/memory/entries/MEM-20261005-184-sdk-action-fields-become-the-model-facing-parameter-schema.md",
    ".cursor/memory/entries/MEM-20261005-185-verdict-scope-must-be-pressed-too.md",
)

#: 承继残余（逐条必须在本文件里明写）。
INHERITED_RESIDUALS: tuple[str, ...] = (
    "W-1",
    "W-2",
    "W-3",
    "R26-1",
    "R-M1",
)

#: 未覆盖范围（承继项；逐条必须明写）。
UNCOVERED_MARKERS: tuple[str, ...] = (
    "读面未认证",
    "多租户未做",
    "BOLA·BFLA 未做",
    "部署面未验证",
    "Mimosa 钩子",  # R-M1 的未收口表述（GOAL 里写作「`R-M1` 未收口」）
)

#: 本轮新增文件（规模契约）。
MAX_NEW_FILE_LINES = 450
NEW_FILES: tuple[str, ...] = (
    "adapters/canonical/read_provider.py",
    "services/api/session_tool_support.py",
    "tests/adapters/canonical/test_canonical_read_provider.py",
    "tests/api/test_production_session_tool_registration.py",
    "tests/e2e/test_session_tool_call_on_the_default_assembly.py",
    "tests/architecture/python/test_capability_coverage_is_implemented.py",
    "tests/architecture/python/test_deliverable_write_stays_on_the_canonical_path.py",
    "tests/tooling/test_two_tree_verdicts_are_archived.py",
    SELF,
)


def load_standard(root: Path) -> object | None:
    path = TOOLBOX.tree(root, STANDARD)
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("goal029_standard", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal029_standard"] = module
    spec.loader.exec_module(module)
    return module


def _core_face_verdicts(root: Path) -> list[VerdictLike]:
    """① ② ③：三个真缺陷的修复逐条在位（AST）。"""
    agent = TOOLBOX.text(root, POLICY_AGENT)
    bridge = TOOLBOX.text(root, SESSION_TOOL_INVOCATION)
    tool_source = TOOLBOX.text(root, SESSION_TOOLS)
    return [
        TOOLBOX.verdict(
            "f6-agent-loop-gate-uses-declared-scope",
            "policy_scope_for" in agent and "scope=policy_scope_for(tool_name)" in agent,
            "policy_enforcing_agent 未按能力声明 scope 求值（F-6 回归）",
        ),
        TOOLBOX.verdict(
            "bridge-gate-uses-the-shared-scoper",
            "ScopedPolicy" in bridge and "scoped_policy, actor" in bridge,
            "session_tool_invocation 未复用 ScopedPolicy（桥与 preflight 不同源）",
        ),
        TOOLBOX.verdict(
            "session-tool-action-takes-flat-parameters",
            'extra="allow"' in tool_source and "def arguments" in tool_source,
            "SessionToolAction 未改参数平铺（模型侧工具调用会撞 extra=forbid）",
        ),
    ]


def _carrying_face_verdicts(root: Path) -> list[VerdictLike]:
    """④ ⑤ ⑥：承接面（读 provider / 出厂装配决策 / 两个组合根接线）。"""
    provider = TOOLBOX.text(root, READ_PROVIDER)
    support = TOOLBOX.text(root, SESSION_TOOL_SUPPORT)
    sqlite_root = TOOLBOX.text(root, SQLITE_ROOT)
    pg_root = TOOLBOX.text(root, PG_ROOT)
    bindings = TOOLBOX.binding_tool_names(support, "DEFAULT_SESSION_TOOL_BINDINGS")
    return [
        TOOLBOX.verdict(
            "canonical-read-provider-present",
            TOOLBOX.defines(provider, "CanonicalReadProvider")
            and TOOLBOX.defines(provider, "tool_ids")
            and "_TOOL_CAPABILITIES" in provider,
            "canonical 读面 provider 或其工具表缺失",
        ),
        TOOLBOX.verdict(
            "factory-table-covers-the-five-in-scope-capabilities",
            set(IN_SCOPE_CAPABILITIES) <= bindings,
            f"出厂绑定表缺 A 组射程内能力：{sorted(set(IN_SCOPE_CAPABILITIES) - bindings)}",
        ),
        TOOLBOX.verdict(
            "session-tool-support-exposes-the-assembly-face",
            TOOLBOX.defines(support, "canonical_read_register")
            and TOOLBOX.defines(support, "session_tool_face")
            and TOOLBOX.defines(support, "sqlite_session_tools"),
            "services/api/session_tool_support 的出厂装配面不完整",
        ),
        TOOLBOX.verdict(
            "both-composition-roots-pass-register-session-tools",
            "register_session_tools=" in sqlite_root and "register_session_tools=" in pg_root,
            "组合根未全部接线（W-1 的装配面缺口回归）",
        ),
    ]


def _declaration_verdicts(root: Path) -> list[VerdictLike]:
    """出厂目录**声明**了射程内的能力（声明 + 实现两件同时在）。"""
    providers = TOOLBOX.text(root, TOOL_PROVIDERS)
    missing = [capability for capability in IN_SCOPE_CAPABILITIES if capability not in providers]
    capabilities = TOOLBOX.text(root, CAPABILITIES)
    return [
        TOOLBOX.verdict(
            "provider-catalog-declares-the-in-scope-capabilities",
            not missing,
            f"出厂目录未声明：{missing}",
        ),
        TOOLBOX.verdict(
            "capability-vocabulary-intact",
            capabilities.count("\n  - ") >= 40,
            "能力词表形态异常（本 GOAL 未改它，只读）",
        ),
    ]


def ec_file_verdicts(root: Path) -> list[VerdictLike]:
    """逐 EC：判据文件在树 + 例数下界（缺文件、掉下界，两向判红）。"""
    verdicts: list[VerdictLike] = []
    for label, (files, floors) in EC_FILES.items():
        for relative, floor in zip(files, floors, strict=True):
            path = TOOLBOX.tree(root, relative)
            if not path.is_file():
                verdicts.append(
                    TOOLBOX.verdict(f"{label}-judge-present:{relative}", False, "文件不存在")
                )
                continue
            actual = TOOLBOX.count_test_defs(path.read_text(encoding="utf-8", errors="replace"))
            verdicts.append(
                TOOLBOX.verdict(
                    f"{label}-judge-present:{relative}",
                    actual >= floor,
                    f"例数下界 {floor}，实测 {actual}",
                )
            )
    return verdicts


def in_scope_verdicts(root: Path) -> list[VerdictLike]:
    """射程：本轮新增脚本进 `IN_SCOPE`（**纯收紧** ⇒ 只查在不在）。"""
    judge = TOOLBOX.text(root, TOOLING_JUDGE)
    if not judge:
        return [TOOLBOX.verdict("new-scripts-in-scope", False, "工具门禁判据不在树")]
    # `IN_SCOPE` 是带类型标注的元组（`AnnAssign`）⇒ 用工具箱的字面量读取器
    # （它 `Assign` 与 `AnnAssign` 都认）。**实测教训**：只认 `ast.Assign` 时
    # 这里恒定读到空元组 ⇒ 判据假红（本轮实测：`SELF in pinned` 为 False 而文件其实在表里）。
    value = TOOLBOX.module_literal(judge, "IN_SCOPE")
    pinned = tuple(str(item) for item in value) if isinstance(value, tuple) else ()
    return [
        TOOLBOX.verdict(
            "new-scripts-in-scope",
            SELF in pinned,
            f"{SELF} 未进 IN_SCOPE（实测表内 {len(pinned)} 条）",
        )
    ]


def scale_verdicts(root: Path) -> list[VerdictLike]:
    """本轮新增文件规模 ≤ 450 行（缺文件即判红）。"""
    verdicts: list[VerdictLike] = []
    for relative in NEW_FILES:
        path = TOOLBOX.tree(root, relative)
        if not path.is_file():
            verdicts.append(TOOLBOX.verdict(f"new-file-present:{relative}", False, "文件不存在"))
            continue
        lines = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
        verdicts.append(
            TOOLBOX.verdict(
                f"new-file-size:{relative}",
                lines <= MAX_NEW_FILE_LINES,
                f"{lines} 行 > {MAX_NEW_FILE_LINES}",
            )
        )
    return verdicts


def _ec_status_verdicts(goal: str) -> list[VerdictLike]:
    """前三个 EC 的终态必须是 PASS；EC-04/05 只要求条目在位（时序见模块 docstring）。"""
    verdicts = [
        TOOLBOX.verdict(f"goal-declares-{ec}", "status: PASS" in goal, f"{ec} 未记 PASS")
        for ec in ("EC-01", "EC-02", "EC-03")
    ]
    verdicts.append(TOOLBOX.verdict("goal-declares-EC-04", "id: EC-04" in goal, "EC-04 条目缺失"))
    verdicts.append(
        TOOLBOX.verdict(
            "goal-declares-EC-05",
            "id: EC-05" in goal and ("status: PASS" in goal or "status: PENDING" in goal),
            "EC-05 条目缺失",
        )
    )
    return verdicts


def _presence_verdicts(
    root: Path, goal: str, label: str, names: tuple[str, ...], *, in_text: bool
) -> list[VerdictLike]:
    """一组名字的「在位」判词（`in_text` ⇒ 在 GOAL 正文里找；否则 ⇒ 在树里找文件）。"""
    if in_text:
        missing = [name for name in names if name not in goal]
    else:
        missing = [name for name in names if not TOOLBOX.tree(root, name).is_file()]
    return [TOOLBOX.verdict(label, not missing, f"缺失：{missing}")]


def record_verdicts(root: Path) -> list[VerdictLike]:
    """记录面：五个 EC 的终态 + 子计划/记忆 + 残余与未覆盖逐条。"""
    goal = TOOLBOX.text(root, GOAL)
    return [
        *_ec_status_verdicts(goal),
        *_presence_verdicts(root, goal, "child-plans-present", CHILD_PLANS, in_text=False),
        *_presence_verdicts(root, goal, "memories-present", MEMORIES, in_text=False),
        *_presence_verdicts(root, goal, "residuals-recorded", INHERITED_RESIDUALS, in_text=True),
        *_presence_verdicts(
            root, goal, "uncovered-ranges-written", UNCOVERED_MARKERS, in_text=True
        ),
        TOOLBOX.verdict(
            "goal-forbids-overclaiming",
            "恰好一次" in goal and "明确否认" in goal,
            "GOAL 未写明对投递语义的否认口径",
        ),
    ]


def deliverable_verdicts(root: Path) -> list[VerdictLike]:
    """全部本轮特有断言（供两树入口调用）。"""
    return [
        *_core_face_verdicts(root),
        *_carrying_face_verdicts(root),
        *_declaration_verdicts(root),
        *ec_file_verdicts(root),
        *in_scope_verdicts(root),
        *scale_verdicts(root),
        *record_verdicts(root),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GOAL-029 收口复检（标准集 + 本轮特有断言）")
    parser.add_argument("--root", default=".", help="树根（两树入口各自传自己的树）")
    parser.add_argument("--verdict-only", action="store_true", help="只打印判词行")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    standard = load_standard(root)
    verdicts: list[VerdictLike] = []
    if standard is None:
        verdicts.append(TOOLBOX.verdict("standard-assertions-present", False, f"{STANDARD} 不在树"))
    else:
        standard_verdicts = getattr(standard, "standard_verdicts", None)
        assert callable(standard_verdicts), "标准断言集缺少 standard_verdicts"
        cast(Callable[[Path], Iterable[Any]], standard_verdicts)
        verdicts.extend(standard_verdicts(root))
    verdicts.extend(deliverable_verdicts(root))
    failures = [verdict for verdict in verdicts if not verdict.ok]
    for verdict in verdicts:
        if verdict.ok:
            print(f"PASS {verdict.name}")
        else:
            print(f"FAIL {verdict.name} -> {verdict.detail}")
    if not args.verdict_only:
        print(f"SUMMARY total={len(verdicts)} failed={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
