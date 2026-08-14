"""M8 Skill Registry：稳定加载、digest 校验、能力路由与生命周期。"""

from __future__ import annotations

from packages.application.skill_registry.lifecycle import (
    deprecate_skill,
    retire_skill,
    transition_skill_status,
)
from packages.application.skill_registry.registry import (
    SkillRefIssue,
    SkillRefIssueKind,
    SkillRegistry,
    build_registry,
    check_skill_refs,
)
from packages.application.skill_registry.routing import (
    active_skill_ids,
    capability_union_for_skills,
    capability_union_of_specs,
    is_deprecated_only,
)

__all__ = [
    "SkillRefIssue",
    "SkillRefIssueKind",
    "SkillRegistry",
    "active_skill_ids",
    "build_registry",
    "capability_union_for_skills",
    "capability_union_of_specs",
    "check_skill_refs",
    "deprecate_skill",
    "is_deprecated_only",
    "retire_skill",
    "transition_skill_status",
]
