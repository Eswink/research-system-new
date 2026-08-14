"""M8 Skill Registry 测试：稳定加载、digest、生命周期、路由、Role/Agent 集成。"""

from __future__ import annotations

from dataclasses import replace

import pytest

from packages.application.skill_registry import (
    SkillRefIssueKind,
    build_registry,
    capability_union_for_skills,
    check_skill_refs,
    deprecate_skill,
    retire_skill,
    transition_skill_status,
)
from packages.domain.core import Digest, Version
from packages.domain.enums import SkillStatus
from packages.domain.tools import SkillSpec, skill_content_digest


def _skill(
    skill_id: str = "literature_scouting",
    *,
    capabilities: tuple[str, ...] = ("search.academic", "citation.parse"),
    status: SkillStatus = SkillStatus.ACTIVE,
    declared_digest: bool = True,
) -> SkillSpec:
    base = SkillSpec(
        id=skill_id,
        version=Version("1.2.0"),
        capabilities=list(capabilities),
        description="scout literature",
        status=status,
    )
    if not declared_digest:
        return base
    return replace(base, digest=skill_content_digest(base))


class TestRegistryBuild:
    def test_key_id_mismatch_is_structural_error(self) -> None:
        registry, errors = build_registry({"other-key": _skill()})
        assert errors == ["skill key 'other-key' does not match spec id 'literature_scouting'"]
        assert registry.resolve("other-key") is not None

    def test_resolve_roundtrip(self) -> None:
        spec = _skill()
        registry, errors = build_registry({"literature_scouting": spec})
        assert errors == []
        assert registry.resolve("literature_scouting") == spec
        assert registry.resolve("ghost") is None


class TestCheckSkillRefs:
    def test_clean_reference_has_no_issues(self) -> None:
        registry, _ = build_registry({"literature_scouting": _skill()})
        assert check_skill_refs(registry, ("literature_scouting",), "agent:a") == ()

    def test_missing_skill(self) -> None:
        registry, _ = build_registry({})
        issues = check_skill_refs(registry, ("ghost",), "agent:a")
        assert issues[0].kind is SkillRefIssueKind.MISSING

    def test_digest_mismatch_detected(self) -> None:
        spec = _skill()
        tampered = replace(spec, description="tampered")
        registry, _ = build_registry({"literature_scouting": tampered})
        issues = check_skill_refs(registry, ("literature_scouting",), "agent:a")
        assert issues[0].kind is SkillRefIssueKind.DIGEST_MISMATCH

    def test_undigested_skill_passes(self) -> None:
        registry, _ = build_registry({"literature_scouting": _skill(declared_digest=False)})
        assert check_skill_refs(registry, ("literature_scouting",), "agent:a") == ()

    def test_deprecated_and_retired_flags(self) -> None:
        registry, _ = build_registry({
            "old_skill": _skill("old_skill", status=SkillStatus.DEPRECATED),
            "dead_skill": _skill("dead_skill", status=SkillStatus.RETIRED),
        })
        deprecated = check_skill_refs(registry, ("old_skill",), "agent:a")
        assert deprecated[0].kind is SkillRefIssueKind.DEPRECATED
        retired = check_skill_refs(registry, ("dead_skill",), "agent:a")
        assert retired[0].kind is SkillRefIssueKind.RETIRED


class TestLifecycle:
    def test_active_to_deprecated_to_retired(self) -> None:
        spec = _skill()
        deprecated = deprecate_skill(spec)
        assert deprecated.status is SkillStatus.DEPRECATED
        retired = retire_skill(deprecated)
        assert retired.status is SkillStatus.RETIRED

    def test_active_direct_retire_allowed(self) -> None:
        assert retire_skill(_skill()).status is SkillStatus.RETIRED

    def test_reverse_and_self_transition_rejected(self) -> None:
        retired = retire_skill(_skill())
        with pytest.raises(ValueError):
            transition_skill_status(retired, SkillStatus.ACTIVE)
        with pytest.raises(ValueError):
            transition_skill_status(retired, SkillStatus.RETIRED)
        with pytest.raises(ValueError):
            deprecate_skill(retired)

    def test_status_change_keeps_digest(self) -> None:
        spec = _skill()
        retired = retire_skill(spec)
        assert retired.digest == spec.digest
        assert skill_content_digest(retired) == skill_content_digest(spec)


class TestRouting:
    def test_union_of_declared_capabilities(self) -> None:
        registry, _ = build_registry({
            "scouting": _skill(
                "scouting",
                capabilities=("search.academic", "citation.parse"),
            ),
            "audit": _skill("audit", capabilities=("citation.validate", "citation.parse")),
        })
        capabilities, issues = capability_union_for_skills(
            registry, ("scouting", "audit"), "agent:a"
        )
        assert capabilities == (
            "citation.parse",
            "citation.validate",
            "search.academic",
        )
        assert issues == ()

    def test_skill_does_not_grant_permissions(self) -> None:
        """负面测试：Skill 只声明 capability，不得产生 CapabilityGrant。"""
        from packages.domain.tools import CapabilityGrant

        registry, _ = build_registry({"scouting": _skill("scouting")})
        capabilities, _ = capability_union_for_skills(registry, ("scouting",), "agent:a")
        assert capabilities == ("citation.parse", "search.academic")
        # 路由输出是纯声明集合；授权面必须由 Role/PolicyEvaluator 单独裁决。
        assert not isinstance(capabilities, CapabilityGrant)

    def test_missing_and_retired_do_not_contribute(self) -> None:
        registry, _ = build_registry({
            "active": _skill("active", capabilities=("a.cap",)),
            "dead": _skill("dead", status=SkillStatus.RETIRED, capabilities=("b.cap",)),
        })
        capabilities, issues = capability_union_for_skills(
            registry, ("active", "dead", "ghost"), "agent:a"
        )
        assert capabilities == ("a.cap",)
        assert {issue.kind for issue in issues} == {
            SkillRefIssueKind.RETIRED,
            SkillRefIssueKind.MISSING,
        }

    def test_deprecated_skill_still_routes_with_flag(self) -> None:
        registry, _ = build_registry({
            "old": _skill("old", status=SkillStatus.DEPRECATED, capabilities=("a.cap",))
        })
        capabilities, issues = capability_union_for_skills(registry, ("old",), "agent:a")
        assert capabilities == ("a.cap",)
        assert issues[0].kind is SkillRefIssueKind.DEPRECATED


class TestMultiRoleReuse:
    def test_same_skill_referenced_by_multiple_subjects(self) -> None:
        registry, _ = build_registry({"scouting": _skill("scouting")})
        for subject in ("agent:a1", "agent:a2", "role:researcher"):
            assert check_skill_refs(registry, ("scouting",), subject) == ()

    def test_deprecated_skill_flagged_for_every_subject(self) -> None:
        registry, _ = build_registry({"old": _skill("old", status=SkillStatus.DEPRECATED)})
        for subject in ("agent:a1", "role:r1"):
            issues = check_skill_refs(registry, ("old",), subject)
            assert issues[0].kind is SkillRefIssueKind.DEPRECATED


class TestDigestStability:
    def test_version_change_alters_digest(self) -> None:
        base = _skill()
        bumped = replace(base, version=Version("1.3.0"))
        assert skill_content_digest(base) != skill_content_digest(bumped)

    def test_digest_value_is_valid(self) -> None:
        digest = skill_content_digest(_skill(declared_digest=False))
        assert Digest.parse(str(digest)) == digest
