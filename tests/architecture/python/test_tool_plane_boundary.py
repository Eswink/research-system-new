"""工具面边界（GOAL-20260919-007 cycle 5 = EC-05）：唯一门控入口 + 会话内 Tool Set 冻结。

判据全部是**结构判据**（AST 扫描生产源码树）或**纯函数/数据面判据**，不靠 grep 字面量：

1. 直达 SDK 的 `conversation.execute_tool` 在生产源码里**只有一处**，且它是作为参数交给
   `PolicyWrappedToolExecutor.execute`（先裁决后执行）——不是直接调用；
2. agent loop 侧的 SDK 执行点被 `PolicyEnforcingAgent._execute_action_event` 覆盖，
   先 `_evaluate` 再委托；
3. 组合根不构造任何工具执行体（唯一装配点是 `build_agent_runtime`）；
4. `AgentRuntime` Port 的公开面里没有"直接执行工具"的方法；
5. 有效 Tool Set 装配后不可改写：spec 是 frozen dataclass、生产源码里没有给会话条目
   重新赋 spec/conversation 的语句。

反证（记录在 RECHECK-20260919-111）：把 `runtime_adapter.py` 第 285 行改成直接调用
`entry.conversation.execute_tool(...)` 后本文件即红——白名单不是"谁都能进"的集合，
而是"只有这一处、且必须经包装"的断言。
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PRODUCTION_ROOTS = ("services", "packages/application", "adapters")
COMPOSITION_ROOTS = (
    ROOT / "services" / "api" / "composition.py",
    ROOT / "services" / "api" / "pg_composition.py",
    ROOT / "services" / "api" / "runtime_support.py",
)

#: 允许**提及** SDK 直达执行点的文件（相对仓库根）。任何新增项都必须自带门禁理由。
GATED_FACES = {
    "adapters/openhands/runtime_adapter.py": (
        "唯一一处：把 `conversation.execute_tool` 交给 PolicyWrappedToolExecutor"
    ),
}
#: agent loop 侧的 SDK 执行点覆盖（第二个门控面）。
AGENT_LOOP_FACE = "adapters/openhands/policy_enforcing_agent.py"
SDK_EXECUTION_POINT = "_execute_action_event"
WRAPPER_METHOD = "execute"

#: 会话条目上不可被生产代码重新赋值的属性（改写有效 Tool Set 的入口）。
SEALED_ATTRIBUTES = ("spec", "conversation", "frozen_tool_set")


def _production_files() -> list[Path]:
    files: list[Path] = []
    for root in PRODUCTION_ROOTS:
        files.extend(sorted((ROOT / root).rglob("*.py")))
    return files


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _direct_execution_sites(path: Path) -> list[int]:
    """文件里 `<something>.execute_tool` 属性访问的行号（只认属性名，不认字符串）。"""
    hits: list[int] = []
    for node in ast.walk(_parse(path)):
        if isinstance(node, ast.Attribute) and node.attr == "execute_tool":
            hits.append(node.lineno)
    return hits


def _tool_executor_constructions(path: Path) -> list[str]:
    """文件里构造"会执行工具的东西"的调用名（组合根出现即违反唯一装配点）。"""
    banned = {"Agent", "Conversation", "LocalConversation", "PolicyWrappedToolExecutor", "Tool"}
    hits: list[str] = []
    for node in ast.walk(_parse(path)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if name in banned:
            hits.append(f"{name}@{node.lineno}")
    return hits


def _sealed_attribute_writes(path: Path) -> list[str]:
    """对会话条目的 `<x>.spec = ...` / `<x>.conversation = ...` 等赋值（有效集改写面）。"""
    hits: list[str] = []
    for node in ast.walk(_parse(path)):
        if isinstance(node, ast.Assign):
            targets: list[ast.expr] = list(node.targets)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            targets = [node.target]
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Attribute) and target.attr in SEALED_ATTRIBUTES:
                hits.append(f"{target.attr}@{node.lineno}")
    return hits


def test_direct_sdk_execution_is_confined_to_the_gated_faces() -> None:
    """AC-01：生产源码里只有一处提及 SDK 直达执行点，且它必须交给策略包装。"""
    mentions: dict[str, list[int]] = {}
    for path in _production_files():
        relative = path.relative_to(ROOT).as_posix()
        if lines := _direct_execution_sites(path):
            mentions[relative] = lines
    assert set(mentions) == set(GATED_FACES), f"ungated direct execution sites: {mentions}"
    for relative, lines in mentions.items():
        assert len(lines) == 1, f"{relative} mentions the SDK entry at {lines}"
        assert _hands_the_entry_to_the_wrapper(ROOT / relative), (
            f"{relative} does not pass the SDK entry into the policy wrapper"
        )


def _hands_the_entry_to_the_wrapper(path: Path) -> bool:
    """该文件里 `conversation.execute_tool` 是否**只作为参数**进了策略包装的方法。"""
    for node in ast.walk(_parse(path)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == WRAPPER_METHOD:
            if any(
                isinstance(argument, ast.Attribute) and argument.attr == "execute_tool"
                for argument in node.args
            ):
                return True
    return False


def test_agent_loop_execution_point_is_overridden_behind_a_gate() -> None:
    """AC-01'：agent loop 的 SDK 执行点被覆盖，且先裁决再委托。"""
    path = ROOT / AGENT_LOOP_FACE
    overrides = [
        node
        for node in ast.walk(_parse(path))
        if isinstance(node, ast.FunctionDef) and node.name == SDK_EXECUTION_POINT
    ]
    assert overrides, f"{AGENT_LOOP_FACE} no longer overrides {SDK_EXECUTION_POINT}"
    calls = [
        getattr(node.func, "attr", None)
        for node in ast.walk(overrides[0])
        if isinstance(node, ast.Call)
    ]
    assert "_evaluate" in calls, "the SDK execution point is not gated by a policy decision"
    assert calls.index("_evaluate") < calls.index(SDK_EXECUTION_POINT), (
        "the policy decision must be taken before delegating to the SDK"
    )


def test_composition_roots_build_no_tool_executor() -> None:
    """AC-02：组合根不构造任何会执行工具的 Agent/Conversation/执行体。"""
    offenders = {
        path.name: hits
        for path in COMPOSITION_ROOTS
        if (hits := _tool_executor_constructions(path))
    }
    assert offenders == {}, f"composition roots build tool executors inline: {offenders}"


def test_agent_runtime_port_exposes_no_direct_execution_entry() -> None:
    """AC-02'：Port 的公开面里没有"直接执行工具"——门控入口只在 adapter 上。"""
    from packages.application.ports.agent_runtime import AgentRuntime

    names = {name for name in dir(AgentRuntime) if not name.startswith("_")}
    assert not {name for name in names if "execute" in name}, names


def test_effective_tool_set_has_no_writer_in_production() -> None:
    """AC-04（ii）：生产源码里没有重新赋值会话条目 spec/conversation 的语句。"""
    offenders: dict[str, list[str]] = {}
    for path in _production_files():
        if hits := _sealed_attribute_writes(path):
            offenders[path.relative_to(ROOT).as_posix()] = hits
    assert offenders == {}, f"tool set is rewritten in place: {offenders}"


def test_session_spec_rejects_in_place_rewrite() -> None:
    """AC-04（i）：spec 是 frozen dataclass ⇒ 改写有效 Tool Set 直接抛。"""
    import dataclasses

    from packages.application.ports.agent_runtime import AgentSessionSpec
    from tests.contracts.fixtures import agent_spec, research_task, role_definition, task_contract

    spec = AgentSessionSpec(
        task_id=research_task().id,
        task_contract=task_contract(),
        role=role_definition(),
        agent=agent_spec(),
        frozen_tool_set=("m12_artifact",),
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(spec, "frozen_tool_set", ())
    assert spec.frozen_tool_set == ("m12_artifact",)
