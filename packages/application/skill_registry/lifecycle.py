"""Skill 生命周期：ACTIVE → DEPRECATED → RETIRED 状态迁移。

Skill 只有声明性生命周期；退役不自动撤销 Capability（授权面由
Role/Policy 控制），但引用 RETIRED skill 会被 Skill Registry 拒绝。
digest 随内容变化，与状态无关。
"""

from __future__ import annotations

from dataclasses import replace

from packages.domain.enums import SkillStatus
from packages.domain.tools import SkillSpec

_VALID_TRANSITIONS: dict[SkillStatus, frozenset[SkillStatus]] = {
    SkillStatus.ACTIVE: frozenset({SkillStatus.DEPRECATED, SkillStatus.RETIRED}),
    SkillStatus.DEPRECATED: frozenset({SkillStatus.RETIRED}),
    SkillStatus.RETIRED: frozenset(),
}


def transition_skill_status(spec: SkillSpec, target: SkillStatus) -> SkillSpec:
    """状态迁移；非法迁移（含反向、自迁移）抛 ValueError。"""
    allowed = _VALID_TRANSITIONS[spec.status]
    if target not in allowed:
        raise ValueError(f"invalid skill status transition: {spec.status.value} -> {target.value}")
    return replace(spec, status=target)


def retire_skill(spec: SkillSpec) -> SkillSpec:
    return transition_skill_status(spec, SkillStatus.RETIRED)


def deprecate_skill(spec: SkillSpec) -> SkillSpec:
    return transition_skill_status(spec, SkillStatus.DEPRECATED)
