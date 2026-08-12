"""RolePool selection strategy 的编译期确定性选择。

来源：docs/architecture/ROLE_MODEL.md §7（SelectionStrategy）。

- FIXED：字典序前 N。
- ROUND_ROBIN：字典序 + 稳定轮转偏移（offset 由调用方按 role 聚合序提供），
  编译期输出确定，运行期轮转由执行层继续。
- CAPABILITY_BEST_FIT：按 agent.capability_refs 与 phase 所需 capabilities 的交集
  降序稳定排序。
- COST_AWARE / EVAL_SCORE_AWARE：依赖运行时成本/评分数据，编译期不可得，
  确定性退化为 FIXED，并产生 `SELECTION_STRATEGY_DEGRADED`（INFO）finding 使退化
  可见（运行时数据源 M5+ 接入后回填真实选择）。
"""

from __future__ import annotations

from packages.domain.enums import SelectionStrategy
from packages.domain.protocols import CompileFindingCode, FindingSeverity, PreflightFinding
from packages.domain.roles import AgentSpec, RolePool

_DEGRADING_STRATEGIES = frozenset({
    SelectionStrategy.COST_AWARE,
    SelectionStrategy.EVAL_SCORE_AWARE,
})


def degradation_findings(pool: RolePool, role_id: str) -> list[PreflightFinding]:
    """COST_AWARE / EVAL_SCORE_AWARE 编译期无数据源时的可见退化 finding。"""
    if pool.selection_strategy not in _DEGRADING_STRATEGIES:
        return []
    return [
        PreflightFinding(
            CompileFindingCode.SELECTION_STRATEGY_DEGRADED.value,
            FindingSeverity.INFO,
            (
                f"role {role_id} selection strategy {pool.selection_strategy.value} "
                "has no compile-time data source; deterministically degraded to FIXED"
            ),
            f"role:{role_id}",
        )
    ]


def select_agents(
    agents: list[AgentSpec],
    pool: RolePool,
    limit: int,
    *,
    offset: int = 0,
    required_capabilities: set[str] | None = None,
) -> list[str]:
    """从候选 agents 中按 pool.selection_strategy 选出至多 limit 个 agent id。"""
    if limit <= 0:
        return []
    if not agents:
        return []
    strategy = pool.selection_strategy
    if strategy is SelectionStrategy.ROUND_ROBIN:
        ordered_ids = sorted(agent.id for agent in agents)
        shift = offset % len(ordered_ids)
        ordered_ids = ordered_ids[shift:] + ordered_ids[:shift]
    elif strategy is SelectionStrategy.CAPABILITY_BEST_FIT:
        requested = required_capabilities or set()
        ranked = sorted(
            agents,
            key=lambda agent: (
                -len(set(agent.capability_refs) & requested),
                agent.id,
            ),
        )
        ordered_ids = [agent.id for agent in ranked]
    else:
        # FIXED / COST_AWARE / EVAL_SCORE_AWARE（退化）
        ordered_ids = sorted(agent.id for agent in agents)
    return ordered_ids[:limit]
