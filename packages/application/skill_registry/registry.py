"""Skill Registry：稳定加载、版本/digest 校验与引用检查。

Skill 是纯声明资产（ADR-0005）：只声明所需 Capability，不授予权限；
capability 路由交给 ToolResolver（skill_registry/routing.py）。
本模块为纯函数层，不持有生命周期状态（lifecycle.py）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping

from packages.domain.enums import SkillStatus
from packages.domain.tools import SkillSpec, skill_content_digest


class SkillRefIssueKind(StrEnum):
    MISSING = "MISSING"
    DIGEST_MISMATCH = "DIGEST_MISMATCH"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"


@dataclass(frozen=True, slots=True)
class SkillRefIssue:
    kind: SkillRefIssueKind
    skill_id: str
    subject: str
    message: str


@dataclass(frozen=True, slots=True)
class SkillRegistry:
    skills: Mapping[str, SkillSpec] = field(default_factory=dict)

    def resolve(self, skill_id: str) -> SkillSpec | None:
        return self.skills.get(skill_id)


def build_registry(skills: Mapping[str, SkillSpec]) -> tuple[SkillRegistry, list[str]]:
    """从 catalog skills 映射构建 Registry；返回 (registry, 结构错误)。

    结构错误：key 与 spec.id 不一致（说明注册表构建方有 bug）。
    digest 与 status 的内容校验在 check_skill_refs 按引用执行。
    """
    errors = [
        f"skill key {key!r} does not match spec id {spec.id!r}"
        for key, spec in skills.items()
        if key != spec.id
    ]
    return SkillRegistry(skills=dict(skills)), errors


def check_skill_refs(
    registry: SkillRegistry,
    skill_ids: tuple[str, ...],
    subject: str,
) -> tuple[SkillRefIssue, ...]:
    """按引用检查 skill：存在性、digest 一致性、生命周期状态。"""
    issues: list[SkillRefIssue] = []
    for skill_id in skill_ids:
        spec = registry.resolve(skill_id)
        if spec is None:
            issues.append(
                SkillRefIssue(
                    SkillRefIssueKind.MISSING,
                    skill_id,
                    subject,
                    f"skill {skill_id} is not registered",
                )
            )
            continue
        if spec.digest is not None and spec.digest != skill_content_digest(spec):
            issues.append(
                SkillRefIssue(
                    SkillRefIssueKind.DIGEST_MISMATCH,
                    skill_id,
                    subject,
                    f"skill {skill_id} content does not match declared digest",
                )
            )
        if spec.status is SkillStatus.DEPRECATED:
            issues.append(
                SkillRefIssue(
                    SkillRefIssueKind.DEPRECATED,
                    skill_id,
                    subject,
                    f"skill {skill_id} is deprecated",
                )
            )
        elif spec.status is SkillStatus.RETIRED:
            issues.append(
                SkillRefIssue(
                    SkillRefIssueKind.RETIRED,
                    skill_id,
                    subject,
                    f"skill {skill_id} is retired",
                )
            )
    return tuple(issues)
