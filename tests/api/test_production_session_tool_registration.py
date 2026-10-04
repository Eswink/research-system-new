"""GOAL-029 EC-01 判据：**出厂装配**真的把会话工具实现接上了（收 GOAL-028 `W-1`）。

**被测缺口（建档轮实测）**：`services/api/composition.py::_sqlite_orchestration` 与
`services/api/pg_composition.py::_build_pg_orchestration` 调 `build_agent_runtime(...)` 时
**都不传** `register_session_tools` ⇒ 生产路径上注册面是 `None`、回落空操作；
「声明了绑定就起得来」因此只是**判据侧**的事实（`tests/e2e/*` 的 `_attach_session_tools`
自己接）——这正是 `W-1` 的**装配面**形态。

**五件事逐条取证**：

1. **生产路径传了注册面**（结构事实，AST 读源码而不是 grep 字面量）；
2. **注册是懒装配的**：组合期不注册（`SessionBuilder` 在会话装配时按当次工具名注册）
   —— 断言「装配后仍可解析」会误导，必须看**会话装配**那一步；
3. **出厂绑定表 ↔ provider 声明一致**：绑定表里的每个工具名都在对应 provider 的
   `capabilities` 声明里（漏一个就是静默的承接缺口）；
4. **两条反证**（承 `MEM-20261001-180`：registry **进程级且只增不减** ⇒ 必须用**专属名字**
   或**显式摘除**，且**合跑一次**）：① 未注册的专属名字 ⇒ SDK 点名
   `ToolDefinition '<名>' is not registered`；② 有实现的名字 ⇒ 能解析出实例；
5. **provider 实例缺席时不进表**（点名失败，不静默顶替）。
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pytest

from adapters.canonical import CanonicalReadProvider
from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger
from services.api.session_tool_support import (
    DEFAULT_SESSION_TOOL_BINDINGS,
    session_tool_invokers,
    session_tool_register,
)

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

_ROOT = Path(__file__).resolve().parents[2]
_COMPOSITION = "services/api/composition.py"
_PG_COMPOSITION = "services/api/pg_composition.py"
_RUNTIME_SUPPORT = "services/api/runtime_support.py"


def _defines_call_to(path: str, function_name: str, keyword: str) -> bool:
    """`path` 里名为 `function_name` 的函数体内是否有以 `keyword=` 传的调用（AST 判定）。"""
    source = (_ROOT / path).read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(source, filename=path)):
        if not isinstance(node, ast.FunctionDef) or node.name != function_name:
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Call) and any(item.arg == keyword for item in inner.keywords):
                return True
    return False


class TestTheProductionRootsPassTheRegistrationFace:
    """①② 两个组合根都传注册面；`build_agent_runtime` 接收它。"""

    def test_the_sqlite_root_passes_the_session_tool_register(self) -> None:
        assert _defines_call_to(_COMPOSITION, "_sqlite_orchestration", "register_session_tools"), (
            "SQLite 组合根没把会话工具注册面交给 build_agent_runtime（W-1 的装配面缺口）"
        )

    def test_the_pg_root_passes_the_session_tool_register(self) -> None:
        assert _defines_call_to(
            _PG_COMPOSITION, "_build_pg_orchestration", "register_session_tools"
        ), "PG 组合根没把会话工具注册面交给 build_agent_runtime（W-1 的装配面缺口）"

    def test_the_runtime_selection_face_accepts_it(self) -> None:
        """`build_agent_runtime` 的签名里有这个关键字（否则上面两句只是文本巧合）。"""
        source = (_ROOT / _RUNTIME_SUPPORT).read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.FunctionDef) and node.name == "build_agent_runtime":
                names = {arg.arg for arg in node.args.args + node.args.kwonlyargs}
                assert "register_session_tools" in names, sorted(names)
                return
        raise AssertionError("build_agent_runtime 不存在（本判据的前提变了）")


class TestTheFactoryBindingTableMatchesTheDeclarations:
    """③ 绑定表里的每个工具名都在对应 provider 的声明里（漏一个 = 静默的承接缺口）。"""

    def test_every_bound_tool_name_is_declared_by_its_provider(self) -> None:
        from services.api.catalog import load_catalog_snapshot

        declared = load_catalog_snapshot().tool_providers
        missing: list[str] = []
        for tool_name, provider_id, _tool_id in DEFAULT_SESSION_TOOL_BINDINGS:
            spec = declared.get(provider_id)
            if spec is None:
                missing.append(f"{tool_name} -> provider {provider_id} 未在出厂目录声明")
                continue
            if tool_name not in spec.capabilities:
                missing.append(f"{tool_name} 不在 {provider_id} 的 capabilities 里")
        assert missing == [], (
            "出厂绑定表与 provider 声明不一致（工具名必须与策略面同源）",
            missing,
        )

    def test_the_table_is_not_empty(self) -> None:
        """受判面非空（MEM-156）：空的绑定表会让上一条恒真。"""
        assert len(DEFAULT_SESSION_TOOL_BINDINGS) >= 3, DEFAULT_SESSION_TOOL_BINDINGS


class TestTheImplementationTableBitesBothWays:
    """④ 两条反证**合跑**（承 MEM-20261001-180：registry 进程级只增不减）。

    本类的两个用例在**同一次运行**里合跑：前一个注册，后一个证明「未注册的名字点名失败」；
    如果只跑后一个，先前的注册残留会它假绿（反之亦然）。
    """

    #: 专属名字（别处从不使用）⇒ 断言与用例执行顺序无关。
    _OWN_NAME = "goal029.probe.present"
    _ABSENT_NAME = "goal029.probe.absent"

    def test_a_name_with_an_implementation_resolves(self) -> None:
        from openhands.sdk.tool import registry
        from openhands.sdk.tool.spec import Tool

        artifacts = FakeArtifactStore()
        invokers = session_tool_invokers(
            providers={"m12_artifact": CanonicalReadProvider(artifacts)},
            provider_specs=_declared_specs({"m12_artifact"}),
            artifacts=artifacts,
            policy=_allow_all(),
        )
        # 按专属名字造一条绑定（不依赖出厂表，使本条与本文件别处解耦）。
        from adapters.openhands.session_tools import build_session_tools

        assert self._OWN_NAME not in registry._REG, (
            "专属名字在本次运行开始前就被注册过 ⇒ 本判据不具确定性（换个别处不用的名字）"
        )
        register = build_session_tools({self._OWN_NAME: invokers["artifact.read"]})
        register([self._OWN_NAME])

        resolved = registry.resolve_tool(Tool(name=self._OWN_NAME), None)  # type: ignore[arg-type]
        assert len(resolved) == 1, resolved
        assert resolved[0].name == self._OWN_NAME, resolved[0].name

    def test_a_name_without_an_implementation_is_named(self) -> None:
        from openhands.sdk.tool import registry
        from openhands.sdk.tool.spec import Tool

        with pytest.raises(KeyError) as excinfo:
            registry.resolve_tool(Tool(name=self._ABSENT_NAME), None)  # type: ignore[arg-type]
        assert self._ABSENT_NAME in str(excinfo.value), (
            "缺实现时必须**点名**那个工具名（不静默降级）",
            str(excinfo.value),
        )

    def test_the_two_refutations_ran_in_one_process(self) -> None:
        """合跑证据：上一条注册的名字在本进程里仍可解析（registry 只增不减）。

        这不是重复断言，而是把「两条反证确实跑在一次运行里」固定下来 ——
        若有人把本文件拆成两个进程跑，「未注册」那条就会因残留而假绿。
        """
        from openhands.sdk.tool import registry

        assert self._OWN_NAME in registry._REG, (
            "前一条注册的名字不见了 ⇒ 两条反证不在同一进程里（本判据的确定性前提）"
        )
        assert self._ABSENT_NAME not in registry._REG, self._ABSENT_NAME


class TestTheFactoryRefusesToInventBackends:
    """⑤ provider 实例或声明缺席 ⇒ 该名字**不进表**（不静默顶替）。"""

    def test_a_provider_without_an_instance_is_not_registered(self) -> None:
        artifacts = FakeArtifactStore()
        invokers = session_tool_invokers(
            providers={},  # 装配方没有实例
            provider_specs=_declared_specs({"m12_artifact"}),
            artifacts=artifacts,
            policy=_allow_all(),
        )
        assert invokers == {}, "没有 provider 实例时不得造出工具名（否则等于假装可用）"

    def test_a_provider_without_a_declaration_is_not_registered(self) -> None:
        artifacts = FakeArtifactStore()
        invokers = session_tool_invokers(
            providers={"m12_artifact": CanonicalReadProvider(artifacts)},
            provider_specs={},  # 目录里没有这个声明
            artifacts=artifacts,
            policy=_allow_all(),
        )
        assert invokers == {}, "缺声明时不得造出工具名（声明面是承接的前提）"

    def test_the_full_factory_registers_the_declared_names(self) -> None:
        """正控制：实例与声明都在场 ⇒ 每个绑定的工具名都进表。"""
        artifacts = FakeArtifactStore()
        invokers = session_tool_invokers(
            providers={
                "m12_artifact": CanonicalReadProvider(artifacts, FakeEvidenceLedger()),
                "openhands_workspace": CanonicalReadProvider(artifacts),
            },
            provider_specs=_declared_specs({"m12_artifact", "openhands_workspace"}),
            artifacts=artifacts,
            policy=_allow_all(),
        )
        expected = {
            tool_name
            for tool_name, provider_id, _tool_id in DEFAULT_SESSION_TOOL_BINDINGS
            if provider_id in {"m12_artifact", "openhands_workspace"}
        }
        assert set(invokers) == expected, (sorted(invokers), sorted(expected))

    def test_the_register_callback_registers_only_table_names(self) -> None:
        """`session_tool_register` 只注册表里的名字，表外的交给 SDK 点名。"""
        from openhands.sdk.tool import registry

        artifacts = FakeArtifactStore()
        register = session_tool_register(
            providers={"m12_artifact": CanonicalReadProvider(artifacts)},
            provider_specs=_declared_specs({"m12_artifact"}),
            artifacts=artifacts,
            policy=_allow_all(),
        )
        register(["artifact.read", "goal029.not.in.the.table"])
        assert "artifact.read" in registry._REG
        assert "goal029.not.in.the.table" not in registry._REG


def _declared_specs(provider_ids: set[str]) -> dict[str, Any]:
    """出厂目录里这几个 provider 的声明（**取自产品路径**，不在判据里复制一份）。"""
    from services.api.catalog import load_catalog_snapshot

    declared = load_catalog_snapshot().tool_providers
    return {
        provider_id: declared[provider_id]
        for provider_id in provider_ids
        if provider_id in declared
    }


def _allow_all() -> Any:
    """全放行的求值器（本文件的受判对象是**装配面**，策略面另有判据）。"""
    from packages.application.ports.policy_evaluator import PolicyEvaluation
    from packages.domain.enums import PolicyDecision

    class _Allow:
        def evaluate(self, request: Any) -> PolicyEvaluation:
            return PolicyEvaluation(PolicyDecision.ALLOW, reason="probe allow-all")

    return _Allow()


def test_the_probe_helpers_are_not_vacuous() -> None:
    """受判面非空：`_declared_specs` 真的取到了出厂声明（否则上面的正控制是空真）。"""
    specs = _declared_specs({"m12_artifact", "openhands_workspace"})
    assert set(specs) == {"m12_artifact", "openhands_workspace"}, sorted(specs)
    assert json.dumps(sorted(specs))  # 名字非空（守卫 json import 不被优化掉）
