"""实体不变量测试：枚举唯一、冻结实体不变量、跨模块引用。"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from packages.domain.budget import LedgerCostStatus, ResourceType, UsageLedger, UsageLedgerEntry
from packages.domain.core import ID, Digest, Timestamp, Version
from packages.domain.enums import (
    AcceptanceCriterionType,
    FailureCategory,
    ModelBindingMode,
    ModelCapability,
    PolicyDecision,
    TrustLabel,
)
from packages.domain.evidence import Claim, ClaimStatus, Evidence, EvidenceRelationType
from packages.domain.manifest import RunManifest, RunManifestRevision
from packages.domain.models import (
    CapabilityAssertion,
    LLMEndpoint,
    ModelBinding,
    ModelDefinition,
    ModelProfile,
)
from packages.domain.roles import RolePool, TeamTemplate
from packages.domain.tasks import AcceptanceCriterion, HandoffBundle, ResearchTask, TaskContract
from packages.domain.tools import ToolPackManifest
from packages.domain.workspace import WorkspaceLease


def test_failure_categories_cover_document() -> None:
    expected = {
        "CONFIGURATION",
        "MODEL_AUTH",
        "MODEL_RATE_LIMIT",
        "MODEL_INCOMPATIBLE",
        "MODEL_DRIFT",
        "TOOL_UNAVAILABLE",
        "TOOL_SCHEMA_MISMATCH",
        "TOOL_TIMEOUT",
        "POLICY_DENIED",
        "APPROVAL_REJECTED",
        "WORKSPACE_FAILURE",
        "EXECUTION_FAILURE",
        "ARTIFACT_CORRUPTION",
        "VALIDATION_FAILURE",
        "BUDGET_EXHAUSTED",
        "WORKER_LOST",
        "SYSTEM_BUG",
        "SCIENTIFIC_NEGATIVE_RESULT",
    }
    assert {item.value for item in FailureCategory} == expected


def test_enum_members_are_unique() -> None:
    for enum_cls in (
        FailureCategory,
        ModelCapability,
        PolicyDecision,
        TrustLabel,
        AcceptanceCriterionType,
    ):
        values = [item.value for item in enum_cls]
        assert len(values) == len(set(values)), enum_cls.__name__


def test_llm_endpoint_invariants() -> None:
    endpoint = LLMEndpoint(
        id="relay-1",
        name="user-relay",
        protocol="OPENAI_COMPATIBLE",
        base_url="https://relay.example.com/v1",
        credential_ref="cred:relay-1",
    )
    assert endpoint.protocol == "OPENAI_COMPATIBLE"
    with pytest.raises(ValueError):
        LLMEndpoint(
            id="bad",
            name="bad",
            protocol="ANTHROPIC",
            base_url="https://x.example.com",
            credential_ref="c",
        )
    with pytest.raises(ValueError):
        LLMEndpoint(
            id="bad",
            name="bad",
            protocol="OPENAI_COMPATIBLE",
            base_url="file:///tmp",
            credential_ref="c",
        )
    with pytest.raises(ValueError):
        LLMEndpoint(
            id="bad",
            name="bad",
            protocol="OPENAI_COMPATIBLE",
            base_url="https://x.example.com",
            credential_ref="",
        )


def test_model_definition_capabilities_validate_confidence() -> None:
    with pytest.raises(ValueError):
        CapabilityAssertion(confidence=1.5)
    with pytest.raises(ValueError):
        CapabilityAssertion(confidence=-0.1)
    assert CapabilityAssertion(confidence=0.5).status.value == "UNKNOWN"
    definition = ModelDefinition(id="m1", endpoint_id="e1", model_name="gpt-5")
    assert definition.model_name == "gpt-5"


def test_model_profile_requires_primary() -> None:
    assert ModelProfile(id="p1", primary="m1").primary == "m1"
    with pytest.raises(ValueError):
        ModelProfile(id="p1", primary="")
    with pytest.raises(ValueError):
        ModelProfile(id="", primary="m1")


def test_model_binding_modes() -> None:
    explicit = ModelBinding(mode=ModelBindingMode.EXPLICIT_MODEL, model_id="m1")
    assert explicit.model_id == "m1"
    with pytest.raises(ValueError):
        ModelBinding(mode=ModelBindingMode.EXPLICIT_MODEL)
    with pytest.raises(ValueError):
        ModelBinding(mode=ModelBindingMode.INHERIT, model_id="m1")


def test_role_pool_instances_invariants() -> None:
    with pytest.raises(ValueError):
        RolePool(min_instances=-1, max_instances=2)
    with pytest.raises(ValueError):
        RolePool(min_instances=3, max_instances=2)
    with pytest.raises(ValueError):
        RolePool(min_instances=1, max_instances=2, concurrency=0)


def test_team_template_requires_roles() -> None:
    with pytest.raises(ValueError):
        TeamTemplate(id="t1", display_name="empty")
    assert TeamTemplate(id="t1", display_name="lean", roles={"scout": RolePool(1, 2)}).roles


def test_task_contract_requires_acceptance() -> None:
    with pytest.raises(ValueError):
        TaskContract(id="c1", version="1.0.0", purpose="p")
    contract = TaskContract(
        id="c1",
        version="1.0.0",
        purpose="p",
        acceptance_criteria=[
            AcceptanceCriterion(type=AcceptanceCriterionType.SCHEMA_VALID, description="d")
        ],
        retry_policy=None,
    )
    assert contract.acceptance_criteria[0].type is AcceptanceCriterionType.SCHEMA_VALID


def test_research_task_attempt_requires_lease() -> None:
    run_id = ID.generate()
    with pytest.raises(ValueError):
        ResearchTask(id=ID.generate(), run_id=run_id, attempt=2)
    task = ResearchTask(id=ID.generate(), run_id=run_id, attempt=1)
    assert task.status == "CREATED"


def test_handoff_bundle_requires_digest() -> None:
    with pytest.raises(ValueError):
        HandoffBundle(task_id=ID.generate(), producer="", summary="s", digest=Digest("ab" * 32))


def test_workspace_lease_heartbeat_not_after_expiry() -> None:
    expires = Timestamp(datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc))
    heartbeat = Timestamp(datetime(2026, 8, 11, 13, 0, tzinfo=timezone.utc))
    with pytest.raises(ValueError):
        WorkspaceLease(
            workspace_id="w1", agent_session_id="s1", expires_at=expires, heartbeat=heartbeat
        )


def test_claim_verified_requires_evidence_relation() -> None:
    claim = Claim(id="cl1", statement="s", status=ClaimStatus.DRAFT)
    assert claim.status is ClaimStatus.DRAFT
    with pytest.raises(ValueError):
        Evidence(id="", source_ref="s", content_digest="d")
    # RESEARCH_INTEGRITY Hard Rule 1: VERIFIED Claim 必须有 Evidence
    with pytest.raises(ValueError, match="evidence relation"):
        Claim(id="cl2", statement="s2", status=ClaimStatus.VERIFIED)
    verified = Claim(
        id="cl3",
        statement="s3",
        status=ClaimStatus.VERIFIED,
        evidence_relations=[("ev-1", EvidenceRelationType.SUPPORTS)],
    )
    assert verified.evidence_relations[0][0] == "ev-1"


def test_run_manifest_digest_deterministic() -> None:
    manifest = RunManifest(run_id="r1", project_id="p1", protocol_version=Version("0.4.0"))
    first = manifest.digest()
    second = manifest.digest()
    assert first == second
    assert str(first).startswith("sha256:")
    assert len(first.hex_value) == 64


def test_run_manifest_immutability_through_frozen_dataclass() -> None:
    manifest = RunManifest(run_id="r1", project_id="p1", protocol_version=Version("0.4.0"))
    with pytest.raises(Exception):
        manifest.run_id = "changed"  # type: ignore[misc]


def test_revision_requires_digest_change() -> None:
    base = RunManifest(run_id="r1", project_id="p1", protocol_version=Version("0.4.0"))
    digest = base.digest()
    approved_at = Timestamp(datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc))
    with pytest.raises(ValueError):
        RunManifestRevision(
            manifest_digest=digest,
            base_digest=digest,
            revision_number=1,
            reason="no change",
            changes={},
            approved_by="human",
            approved_at=approved_at,
            audit_ref="audit-1",
        )
    revision = RunManifestRevision(
        manifest_digest=Digest("cd" * 32),
        base_digest=digest,
        revision_number=1,
        reason="model change",
        changes={"model": {"from": "a", "to": "b"}},
        approved_by="human",
        approved_at=approved_at,
        audit_ref="audit-1",
    )
    assert revision.revision_number == 1


def test_ledger_append_only() -> None:
    ledger = UsageLedger()
    entry = UsageLedgerEntry(
        entry_id="e1",
        resource_type=ResourceType.MODEL_TOKENS,
        quantity=100,
        unit="tokens",
        cost_status=LedgerCostStatus.UNKNOWN,
        source="relay",
        occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc),
    )
    ledger.append(entry)
    assert len(ledger) == 1
    with pytest.raises(ValueError):
        ledger.append(entry)
    assert len(ledger) == 1


def test_ledger_unknown_cost_is_allowed_without_amount() -> None:
    entry = UsageLedgerEntry(
        entry_id="e2",
        resource_type=ResourceType.MODEL_COST,
        quantity=1,
        unit="usd-minor",
        cost_status=LedgerCostStatus.UNKNOWN,
        source="relay",
        occurred_at=datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc),
    )
    assert entry.estimated_cost_minor is None


def test_tool_pack_manifest_requires_supply_chain_fields() -> None:
    with pytest.raises(ValueError):
        ToolPackManifest(
            id="tp1",
            version=Version("1.0.0"),
            source="",
            resolved_revision="rev",
            digest=Digest("ab" * 32),
            license="MIT",
        )
