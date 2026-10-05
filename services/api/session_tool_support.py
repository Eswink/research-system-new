"""生产装配的**会话工具注册面**（GOAL-029 EC-01(b)：收 GOAL-028 `W-1` 的装配面缺口）。

**它解决什么**：GOAL-028 建成了「provider id → SDK 工具名」的声明式映射与
`build_session_tools` 的实现注册面，但**两个组合根本体都没接线**
（`services/api/composition.py::_sqlite_orchestration` /
`services/api/pg_composition.py::_build_pg_orchestration` 调
`build_agent_runtime(...)` 时都不传 `register_session_tools`）⇒ 生产路径上注册面是
`None`，回落空操作；只有**判据侧**会接。本模块把这条缝补成**出厂形态**：
装配方按「工具名 → 调用桥」造出注册函数，交给 `build_agent_runtime`。

**它与 `adapters/openhands/session_tools.py` 的分工**：那个模块提供**机制**
（`BoundSessionTool` / `build_session_tools`，SDK 类型都在 adapter 内）；
本模块是**装配决策**——「出厂时哪些工具名有实现、它们各自桥到哪个 provider 的哪个
tool_id」这件事必须在组合层说清楚（照 `runtime_support.build_agent_runtime` 的先例，
取值词表与装配决策都归组合层，不进 ports / domain）。

**默认行为逐字不变**：`session_tool_invokers()` 只对**显式登记的绑定**造桥；
没有登记的装配（含默认的 Fake runtime 路径、以及所有未声明绑定的协议）拿到的还是
今天的空操作注册面 —— 未注册的名字照旧由 SDK **点名**
（`ToolDefinition '<名>' is not registered`），不静默丢工具。

**边界**：
- 参数经 `tool-args` 制品传递、策略与执行走**同一个** `execute_tool_call`
  （桥内已保证；见 `session_tool_invocation` 的 docstring）——本模块不另开执行路径。
- 不判定能力是否被允许（那是 `policy.yaml` 与求值器的事）；本模块只说「这个名字有实现」。
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from adapters.openhands.session_tool_invocation import SessionToolSpec, make_tool_invoker
from adapters.openhands.session_tools import SessionToolInvoker, build_session_tools

#: 出厂绑定：SDK 工具名（= **能力名**，与 `policy.yaml` 同源）→ (provider id, provider 侧 tool id)。
#:
#: 为什么键是能力名而不是 provider id：会话工具名会被 `PolicyEnforcingAgent` 当作
#: **capability** 求值（`_evaluate(action_event.tool_name)`），而 registry 里的名字来自
#: 工具实现自己 —— 两者必须是**同一个**名字空间，否则「放行的是一个名字、执行的是另一个」。
#: 因此工具名照 `session_tool_bindings` 的 `tool_name` 取（能力名），provider 侧 tool id
#: 另列（它属于 provider 的接口契约，例：`m12_artifact` 的 `artifact_read`）。
DEFAULT_SESSION_TOOL_BINDINGS: tuple[tuple[str, str, str], ...] = (
    # (工具名 / 能力名, provider_id, provider 侧 tool_id)
    ("artifact.read", "m12_artifact", "artifact_read"),
    ("claim.read", "m12_artifact", "claim_read"),
    ("evidence.read", "m12_artifact", "evidence_read"),
    ("budget.read", "m12_artifact", "budget_read"),
    ("experiment.read", "m12_artifact", "experiment_read"),
    ("experiment_plan.read", "m12_artifact", "experiment_plan_read"),
    ("deliverable.read", "m12_artifact", "deliverable_read"),
    # GOAL-20261005-030 EC-02：`run.read` 的承接 —— 读 `RunStore`（既有 Port，两个组合根
    # 都持有实例），与 HTTP 读面 `GET /runs/{id}` 同一个 `get_run`（不新造第二套查询口径）。
    ("run.read", "m12_artifact", "run_read"),
    # GOAL-20261006-031 EC-02：`citation.validate` 的承接 —— provider 侧工具 id 是
    # `citation_validate`（与既有 `citation.inspect` 的 `citation_inspect` **不同名**）。
    ("citation.validate", "ncbi_citation", "citation_validate"),
    ("workspace.read", "openhands_workspace", "workspace_read"),
)


def session_tool_invokers(
    *,
    providers: Mapping[str, Any],
    provider_specs: Mapping[str, Any],
    artifacts: Any,
    policy: Any,
    bindings: Sequence[tuple[str, str, str]] = DEFAULT_SESSION_TOOL_BINDINGS,
) -> dict[str, SessionToolInvoker]:
    """按出厂绑定造「工具名 → 调用桥」表（只有**实例与声明都在场**的条目才进表）。

    **缺一即不进表、不静默顶替**：provider 实例缺失或 provider spec 缺失时，该工具名
    **不**出现在返回的表里 ⇒ 会话装配时它不会被注册 ⇒ SDK 在 agent 初始化时**点名**
    未注册。这与「provider id 未绑定」共用同一条可观测路径（都点名字），
    而不是让一个没有后端的工具名假装可用。
    """
    invokers: dict[str, SessionToolInvoker] = {}
    for tool_name, provider_id, tool_id in bindings:
        provider = providers.get(provider_id)
        provider_spec = provider_specs.get(provider_id)
        if provider is None or provider_spec is None:
            continue
        invokers[tool_name] = make_tool_invoker(
            SessionToolSpec(provider_id=provider_id, tool_id=tool_id, capability=tool_name),
            providers={provider_id: provider},
            provider_specs={provider_id: provider_spec},
            artifacts=artifacts,
            policy=policy,
        )
    return invokers


def session_tool_register(
    *,
    providers: Mapping[str, Any],
    provider_specs: Mapping[str, Any],
    artifacts: Any,
    policy: Any,
    bindings: Sequence[tuple[str, str, str]] = DEFAULT_SESSION_TOOL_BINDINGS,
) -> Any:
    """出厂形态的 `register_session_tools` 回调（`(工具名序列) -> None`）。

    接 `build_agent_runtime(..., register_session_tools=...)`；缺省绑定见
    `DEFAULT_SESSION_TOOL_BINDINGS`。**只注册表里的名字**，表外的名字交给 SDK 按既有语义
    点名拒绝（`build_session_tools` 的固有行为）。
    """
    return build_session_tools(
        session_tool_invokers(
            providers=providers,
            provider_specs=provider_specs,
            artifacts=artifacts,
            policy=policy,
            bindings=bindings,
        )
    )


def session_tool_face(  # noqa: PLR0913 - 装配面：Port 依赖就这么几件（齐了才叫承接）
    artifacts: Any,
    ledger: Any,
    policy: Any,
    budget_ledger: Any = None,
    experiment_store: Any = None,
    run_store: Any = None,
) -> Any:
    """位置参数形式的出厂注册面（组合根侧读起来最短；语义见 `canonical_read_register`）。"""
    return canonical_read_register(
        artifacts=artifacts,
        ledger=ledger,
        policy=policy,
        budget_ledger=budget_ledger,
        experiment_store=experiment_store,
        run_store=run_store,
    )


def sqlite_session_tools(faces: Any, ports: Any) -> Any:
    """SQLite 组合根的位置参数入口（`faces.policy_evaluator` + ports 的 canonical store）。

    单列一个两行包装而不是让组合根写三个关键字：`composition.py` 恰好卡在 450 行硬上限上，
    而 wiring 本身是一行 —— 包装把「读哪三个依赖」的决策留在本模块（装配决策面）。
    """
    return canonical_read_register(
        artifacts=ports.artifacts,
        ledger=ports.ledger,
        policy=faces.policy_evaluator,
        budget_ledger=ports.budget,
        experiment_store=ports.experiment_store,
        run_store=ports.runs_store,
    )


def canonical_read_register(  # noqa: PLR0913 - 装配面：Port 依赖就这么几件（齐了才叫承接）
    *,
    artifacts: Any,
    ledger: Any,
    policy: Any,
    budget_ledger: Any | None = None,
    experiment_store: Any | None = None,
    run_store: Any | None = None,
    bindings: Sequence[tuple[str, str, str]] = DEFAULT_SESSION_TOOL_BINDINGS,
) -> Any:
    """**出厂形态**的注册回调：用 canonical 读面当 provider 实例（两个组合根共用）。

    为什么实例在这儿造而不是在各组合根里各造一份：`m12_artifact` / `openhands_workspace`
    声明的**读**能力此前全仓零实现，本轮的承接面统一用 `CanonicalReadProvider`
    （它读的是 canonical state：ArtifactStore + EvidenceLedger）。两个组合根**只差 Port 实例**
    （SQLite 根与 PG 根各自的 artifacts/ledger），装配决策因此收在这一处 ——
    多一个入口就多一次漂移机会（与 `runtime_support` 收拢 runtime 选择同一个理由）。

    provider 的**声明**取自出厂目录（`tool_providers.yaml`）：目录里没有的 id **不进表**
    ⇒ 该名字不会被注册 ⇒ SDK 在 agent init 时点名 `ToolDefinition '<名>' is not registered`。
    """
    from adapters.canonical import CanonicalReadProvider
    from services.api.catalog import load_catalog_snapshot

    canonical_reader = CanonicalReadProvider(
        artifacts,
        ledger,
        budget_ledger=budget_ledger,
        experiment_store=experiment_store,
        run_store=run_store,
    )
    instance_for = {
        "m12_artifact": canonical_reader,
        "openhands_workspace": canonical_reader,
    }
    declared = load_catalog_snapshot().tool_providers
    return session_tool_register(
        providers=instance_for,
        provider_specs={
            provider_id: declared[provider_id]
            for provider_id in instance_for
            if provider_id in declared
        },
        artifacts=artifacts,
        policy=policy,
        bindings=bindings,
    )


__all__ = [
    "DEFAULT_SESSION_TOOL_BINDINGS",
    "canonical_read_register",
    "session_tool_face",
    "sqlite_session_tools",
    "session_tool_invokers",
    "session_tool_register",
]
