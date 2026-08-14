"""Preflight 的 Skill Registry 检查（M8）。

`_skill_issue_findings` 把 Skill Registry 的引用校验结果映射为
preflight findings；`check_role_skills` 校验 Role default_skills 引用；
agent 面的 skill 引用由 role_checks._check_agent 复用
`skill_issue_findings`（skip_missing=True 避免重复 finding）。
"""

from __future__ import annotations

from typing import Mapping

from packages.application.ports import PreflightContext
from packages.application.skill_registry import (
    SkillRefIssueKind,
    build_registry,
    check_skill_refs,
)
from packages.domain.protocols import (
    CompiledRunPlan,
    FindingSeverity,
    PreflightFinding,
    PreflightFindingCode,
)
from packages.domain.tools import SkillSpec


def _finding(code: str, message: str, subject: str | None = None) -> PreflightFinding:
    return PreflightFinding(code, FindingSeverity.ERROR, message, subject)


def _warning(code: str, message: str, subject: str | None = None) -> PreflightFinding:
    return PreflightFinding(code, FindingSeverity.WARNING, message, subject)


def skill_issue_findings(
    registry_skills: Mapping[str, SkillSpec],
    skill_ids: tuple[str, ...],
    subject: str,
    missing_code: str,
    *,
    skip_missing: bool = False,
) -> list[PreflightFinding]:
    """Skill Registry 引用检查 → preflight findings（M8）。

    MISSING 使用调用方指定的 code（agent 面保持 AGENT_PERMISSION_DENIED
    向后兼容，role 面用 SKILL_MISSING）；digest/status 用 SKILL_* 码。
    skip_missing=True 时由调用方自行处理 MISSING（避免重复 finding）。
    """
    findings: list[PreflightFinding] = []
    for issue in check_skill_refs(
        build_registry(registry_skills)[0],
        skill_ids,
        subject,
    ):
        if issue.kind is SkillRefIssueKind.MISSING:
            if not skip_missing:
                findings.append(_finding(missing_code, issue.message, subject))
        elif issue.kind is SkillRefIssueKind.DIGEST_MISMATCH:
            findings.append(
                _finding(PreflightFindingCode.SKILL_DIGEST_MISMATCH.value, issue.message, subject)
            )
        elif issue.kind is SkillRefIssueKind.DEPRECATED:
            findings.append(
                _warning(PreflightFindingCode.SKILL_DEPRECATED.value, issue.message, subject)
            )
        elif issue.kind is SkillRefIssueKind.RETIRED:
            findings.append(
                _finding(PreflightFindingCode.SKILL_RETIRED.value, issue.message, subject)
            )
    return findings


def check_role_skills(plan: CompiledRunPlan, context: PreflightContext) -> list[PreflightFinding]:
    """Role default_skills 引用必须在 Skill Registry 内（M8）。"""
    findings: list[PreflightFinding] = []
    assigned_roles = {
        role_id for assignment in plan.phase_assignments for role_id in assignment.role_assignments
    }
    for role_id in sorted(assigned_roles):
        role = context.catalog.roles.get(role_id)
        if role is None or not role.default_skills:
            continue
        findings.extend(
            skill_issue_findings(
                context.catalog.skills,
                tuple(role.default_skills),
                f"role:{role_id}",
                PreflightFindingCode.SKILL_MISSING.value,
            )
        )
    return findings
