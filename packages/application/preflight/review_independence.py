"""评审独立性的**解析面**（GOAL-20261018-084 EC-01；阶梯「复检」域的 `下一级`）。

**它补哪一格**：`check_heterogeneity`（`preflight/role_checks.py`）**已存在**且语义正确 ——
「同一模型不得同时承担 Writer 与 Reviewer」。但它比的是 **`plan.resolved_models` 里的 model id**：

    research_strong (primary research_alpha)  vs  reviewer_gamma

两个 id **不同** ⇒ 判绿。而建档实测：`examples/config/models.yaml` 里
**四个** ModelDefinition（`agnes_flash` / `research_alpha` / `coding_beta` / `reviewer_gamma`）
**全部** `model_name: deepseek-v4-flash-vision` 且 `endpoint: main`
⇒ **底层是同一个模型**，「独立复核」在产品上**不可判**。

**更进一步**（`EC-03`）：profile 的 `fallback` 让问题更深 ——
`research_strong.fallback = [reviewer_gamma]`、`critic_independent.fallback = [research_alpha]`：
一个**名字就叫「独立评审者」** 的 profile，可以回落到**生产者用的模型**。
只比 primary 会漏掉这条路径。

**本模块的职责**：把「一个 agent **可能**落到哪些执行目标」解析成一个**集合**
（`(endpoint_id, model_name)`），供判定面比较。**确定性纯函数、零出网、零模型调用。**

**三条边界**：

1. **只认解析后的目标**：`(endpoint_id, model_name)` —— 不认 agent 名 / 绑定 id / profile 名；
2. **含全部 fallback**：`MODEL_PROFILE` 的 `primary` + **每一个** `fallback` 都进集合
   （那是「可能落到」的完整面，不是「首选」）；
3. **解析不了就点名**：缺模型 / profile 不存在 / `INHERIT` 无从解析 ⇒ 返回带**理由**的空集，
   **不**静默当成「独立」（静默空集会让判据假绿 —— 与 GOAL-078 的「空 vs 读不到」同一纪律）。
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from packages.application.ports import CatalogSnapshot
from packages.domain.enums import ModelBindingMode
from packages.domain.models import ModelDefinition
from packages.domain.roles import AgentSpec

#: 一个**执行目标**的稳定标识：同一个 `(endpoint, model_name)` = 同一个底层模型。
Target = tuple[str, str]


@dataclass(frozen=True, slots=True)
class ResolvedTargets:
    """一个 agent 的**全部可能执行目标** + 解析过程中的问题（逐条点名）。"""

    agent_id: str
    targets: frozenset[Target] = frozenset()
    problems: tuple[str, ...] = ()

    @property
    def resolved(self) -> bool:
        """至少解析出一个目标且没有问题（判据只在 `resolved` 为真时比较）。"""
        return bool(self.targets) and not self.problems


def _target_of(model: ModelDefinition) -> Target:
    """ModelDefinition → 执行目标（**同一个 model_name + endpoint ⇒ 同一个底层模型**）。"""
    return (model.endpoint_id, model.model_name)


def _model_ids_for(binding: object, catalog: CatalogSnapshot) -> tuple[tuple[str, ...], list[str]]:
    """绑定 → `(候选 model id 序列, 问题列表)`。

    `MODEL_PROFILE` ⇒ `primary` + **全部** `fallback`（顺序保留：primary 在前）。
    `EXPLICIT_MODEL` ⇒ 单个 id。`INHERIT` ⇒ **无从解析**（点名）。
    """
    mode = getattr(binding, "mode", None)
    problems: list[str] = []
    if mode is ModelBindingMode.INHERIT:
        return (), ["binding mode INHERIT cannot be resolved to a model"]
    if mode is ModelBindingMode.EXPLICIT_MODEL:
        model_id = _bound_value(binding)
        return ((model_id,) if model_id else ()), (
            [] if model_id else ["EXPLICIT_MODEL binding has no value"]
        )
    profile_id = _bound_value(binding)
    if not profile_id:
        return (), ["MODEL_PROFILE binding has no value"]
    profile = catalog.model_profiles.get(str(profile_id))
    if profile is None:
        return (), [f"model profile {profile_id!r} is not registered"]
    return (str(profile.primary), *(str(item) for item in profile.fallback)), problems


def _bound_value(binding: object) -> str | None:
    """绑定的目标名（`AgentBinding.value`；兼容带 `model_id` / `profile_id` 的形态）。"""
    for name in ("value", "model_id", "profile_id"):
        raw = getattr(binding, name, None)
        if raw:
            return str(raw)
    return None


def resolve_agent_targets(
    agent_id: str,
    agent: AgentSpec,
    catalog: CatalogSnapshot,
) -> ResolvedTargets:
    """一个 agent 的**全部可能执行目标**（确定性；零出网）。"""
    model_ids, problems = _model_ids_for(getattr(agent, "model_binding", None), catalog)
    targets: set[Target] = set()
    for model_id in model_ids:
        model = catalog.models.get(model_id)
        if model is None:
            problems.append(f"model {model_id!r} is not registered")
            continue
        targets.add(_target_of(model))
    return ResolvedTargets(agent_id=agent_id, targets=frozenset(targets), problems=tuple(problems))


def resolve_targets_by_role(
    role_ids: set[str],
    agents_of_role: Mapping[str, tuple[str, ...]],
    catalog: CatalogSnapshot,
) -> tuple[dict[str, set[Target]], dict[str, tuple[str, ...]]]:
    """按 role 聚合**全部可能目标** + 解析问题。

    返回 `(role → 目标集合, role → 问题串)`。**未解析的 role 不出现在第一张表里**
    （由调用方按问题串**点名** —— 空集不能被读成「独立」）。
    """
    by_role: dict[str, set[Target]] = {}
    problems: dict[str, list[str]] = {}
    for role_id in sorted(role_ids):
        for agent_id in agents_of_role.get(role_id, ()):
            agent = catalog.agents.get(agent_id)
            if agent is None:
                problems.setdefault(role_id, []).append(f"agent {agent_id!r} is not registered")
                continue
            resolved = resolve_agent_targets(agent_id, agent, catalog)
            if resolved.problems:
                problems.setdefault(role_id, []).extend(
                    f"{agent_id}: {item}" for item in resolved.problems
                )
            if resolved.targets:
                by_role.setdefault(role_id, set()).update(resolved.targets)
    return by_role, {role: tuple(items) for role, items in problems.items()}


def describe_target(target: Target) -> str:
    """执行目标 → **可读判词**（`endpoint/model_name`；判据与 finding 共用这一处）。"""
    endpoint_id, model_name = target
    return f"{endpoint_id}/{model_name}"


__all__ = [
    "ResolvedTargets",
    "Target",
    "describe_target",
    "resolve_agent_targets",
    "resolve_targets_by_role",
]
