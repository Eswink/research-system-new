"""Skill → Capability 纯声明路由（ADR-0005）。

Skill 只声明所需 Capability，不能自行授予权限：本模块只把 skill 的
capabilities 声明并集交给 ToolResolver，绝不产生 CapabilityGrant；
授权面仍由 Role 的 requested/forbidden capabilities 与 PolicyEvaluator
决定。只有 ACTIVE 且 digest 一致的 skill 参与路由。
"""

from __future__ import annotations

from packages.application.skill_registry.registry import (
    SkillRefIssue,
    SkillRegistry,
    check_skill_refs,
)
from packages.domain.enums import SkillStatus


def active_skill_ids(
    registry: SkillRegistry,
    skill_ids: tuple[str, ...],
    issues: tuple[SkillRefIssue, ...],
) -> tuple[str, ...]:
    """过滤出可参与路由的 ACTIVE skill（存在且 digest 一致）。"""
    blocked = {issue.skill_id for issue in issues if issue.kind.value != "DEPRECATED"}
    return tuple(
        skill_id
        for skill_id in skill_ids
        if skill_id not in blocked and registry.resolve(skill_id) is not None
    )


def capability_union_for_skills(
    registry: SkillRegistry,
    skill_ids: tuple[str, ...],
    subject: str,
) -> tuple[tuple[str, ...], tuple[SkillRefIssue, ...]]:
    """skill 声明的 capability 并集（确定性排序）。

    返回 (capabilities, issues)；DEPRECATED skill 仍参与能力路由但
    issues 中标记（调用方决定是否降级）；MISSING / DIGEST_MISMATCH /
    RETIRED 不参与路由。
    """
    issues = check_skill_refs(registry, skill_ids, subject)
    usable = active_skill_ids(registry, skill_ids, issues)
    capabilities: set[str] = set()
    for skill_id in usable:
        spec = registry.resolve(skill_id)
        if spec is not None:
            capabilities.update(spec.capabilities)
    return tuple(sorted(capabilities)), issues


def capability_union_of_specs(specs: tuple[object, ...]) -> tuple[str, ...]:
    """纯声明并集（不含注册检查）；输入必须是 SkillSpec 兼容对象。"""
    capabilities: set[str] = set()
    for spec in specs:
        declared = getattr(spec, "capabilities", ())
        if isinstance(declared, (list, tuple)):
            capabilities.update(str(item) for item in declared)
    return tuple(sorted(capabilities))


def is_deprecated_only(
    registry: SkillRegistry,
    skill_ids: tuple[str, ...],
) -> bool:
    """全部 skill 均为 DEPRECATED 时返回 True（供调用方降级提示）。"""
    return bool(skill_ids) and all(
        (spec := registry.resolve(skill_id)) is not None and spec.status is SkillStatus.DEPRECATED
        for skill_id in skill_ids
    )
