"""M8 Tool Plane 单元测试（执行面）：lifecycle / execution / results / preflight risk。

与 test_tool_plane.py（catalog/resolver/health）共享
tests/application/tool_plane_support.py fixture 构造器。
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from adapters.fakes import (
    FakeArtifactStore,
    FakeEventPublisher,
    FakePolicyEvaluator,
    FakeToolPackStore,
    FakeToolProvider,
)
from packages.application.ports.errors import InvalidInputError, PermanentPortError
from packages.application.preflight.checks import check_tools
from packages.application.preflight.preflight import run_preflight
from packages.application.tool_plane import (
    ToolPackLifecycle,
    execute_tool_call,
    permission_diff,
    require_frozen_tool_set,
    spill_large_result,
)
from packages.application.tool_plane.results import fetch_spilled_result
from packages.domain.core import Digest
from packages.domain.enums import (
    CredentialScope,
    EffectClass,
    FailureCategory,
    PolicyDecision,
    ToolPackState,
)
from packages.domain.tools import CredentialRequirement, toolpack_content_digest
from tests.application import protocol_fixtures
from tests.application.tool_plane_support import (
    make_call,
    make_manifest,
    make_provider,
    make_tool,
)


class TestLifecycle:
    def _fixtures(
        self,
    ) -> tuple[ToolPackLifecycle, FakePolicyEvaluator, FakeEventPublisher, FakeToolPackStore]:
        policy = FakePolicyEvaluator()
        events = FakeEventPublisher()
        store = FakeToolPackStore()
        lifecycle = ToolPackLifecycle(store, policy, events)
        return lifecycle, policy, events, store

    def test_submit_verifies_digest(self) -> None:
        lifecycle, _, _, _ = self._fixtures()
        pack = make_manifest(tools=(make_tool(),))
        tampered = replace(pack, requested_capabilities=["extra.evil"])
        with pytest.raises(PermanentPortError, match="digest mismatch"):
            lifecycle.submit(tampered)
        outcome = lifecycle.submit(pack)
        assert outcome.status == "installed"
        assert outcome.record.state is ToolPackState.INSTALLED

    def test_install_policy_deny(self) -> None:
        lifecycle, policy, _, _ = self._fixtures()
        policy.set_decision("tool_pack.install", PolicyDecision.DENY)
        with pytest.raises(PermanentPortError, match="policy denied"):
            lifecycle.submit(make_manifest(tools=(make_tool(),)))

    def test_expanding_update_waits_for_approval_and_is_not_effective(self) -> None:
        """权限扩张不立即生效：待批准期间生效版本仍是旧 manifest，批准后才替换。"""
        lifecycle, _, events, store = self._fixtures()
        pack_v1 = make_manifest(tools=(make_tool(),))
        lifecycle.submit(pack_v1)
        pack_v2 = make_manifest(
            tools=(make_tool(),),
            capabilities=("search.academic", "citation.parse"),
        )
        diff = permission_diff(pack_v1, pack_v2)
        assert diff.added_capabilities == ("citation.parse",)
        outcome = lifecycle.submit(pack_v2)
        assert outcome.status == "pending_approval"
        assert outcome.diff is not None and outcome.diff.added_capabilities == ("citation.parse",)
        pending = store.get(pack_v1.id)
        assert pending is not None
        assert pending.manifest.digest == pack_v1.digest  # 生效版本仍是 v1
        assert pending.pending_manifest is not None
        assert events.method_calls("publish") == 2  # install + pending 事件

        approved = lifecycle.approve_update(pack_v1.id)
        assert approved.manifest.digest == pack_v2.digest
        assert approved.pending_manifest is None
        assert events.method_calls("publish") == 3

    def test_approve_update_requires_expansion_policy(self) -> None:
        lifecycle, policy, _, store = self._fixtures()
        pack_v1 = make_manifest(tools=(make_tool(),))
        lifecycle.submit(pack_v1)
        pack_v2 = make_manifest(tools=(make_tool(),), capabilities=("search.academic", "extra.x"))
        lifecycle.submit(pack_v2)
        policy.set_decision("tool_pack.update.expanded", PolicyDecision.DENY)
        with pytest.raises(PermanentPortError, match="policy denied"):
            lifecycle.approve_update(pack_v1.id)
        still_pending = store.get(pack_v1.id)
        assert still_pending is not None and still_pending.manifest.digest == pack_v1.digest

    def test_approve_update_without_pending_is_rejected(self) -> None:
        lifecycle, _, _, _ = self._fixtures()
        pack = make_manifest(tools=(make_tool(),))
        lifecycle.submit(pack)
        with pytest.raises(InvalidInputError, match="no pending update"):
            lifecycle.approve_update(pack.id)

    def test_non_expanding_update_applies_immediately(self) -> None:
        lifecycle, _, events, _ = self._fixtures()
        pack_v1 = make_manifest(tools=(make_tool(),))
        lifecycle.submit(pack_v1)
        pack_v2 = replace(pack_v1, resolved_revision="def456")
        pack_v2 = replace(pack_v2, digest=toolpack_content_digest(pack_v2))
        outcome = lifecycle.submit(pack_v2)
        assert outcome.status == "updated"
        assert outcome.record.manifest.digest != pack_v1.digest
        assert outcome.record.pending_manifest is None
        assert events.method_calls("publish") == 2

    def test_identical_manifest_is_unchanged_not_an_update(self) -> None:
        lifecycle, _, events, _ = self._fixtures()
        pack = make_manifest(tools=(make_tool(),))
        lifecycle.submit(pack)
        outcome = lifecycle.submit(pack)
        assert outcome.status == "unchanged"
        assert outcome.record.manifest.digest == pack.digest
        assert events.method_calls("publish") == 1  # 只发布过 install

    def test_revoke_requires_reason_and_denies_repeat(self) -> None:
        lifecycle, _, events, _ = self._fixtures()
        pack = make_manifest(tools=(make_tool(),))
        lifecycle.submit(pack)
        with pytest.raises(InvalidInputError):
            lifecycle.revoke(pack.id, "")
        revoked = lifecycle.revoke(pack.id, "license violation")
        assert revoked.state is ToolPackState.REVOKED
        assert revoked.revoked_reason == "license violation"
        with pytest.raises(InvalidInputError):
            lifecycle.revoke(pack.id, "again")
        assert events.method_calls("publish") == 2

    def test_revoke_clears_pending_update(self) -> None:
        lifecycle, _, _, store = self._fixtures()
        pack_v1 = make_manifest(tools=(make_tool(),))
        lifecycle.submit(pack_v1)
        lifecycle.submit(
            make_manifest(tools=(make_tool(),), capabilities=("search.academic", "x.y"))
        )
        revoked = lifecycle.revoke(pack_v1.id, "compromised")
        assert revoked.pending_manifest is None
        assert store.get(pack_v1.id) is not None

    def test_revoked_pack_is_terminal(self) -> None:
        lifecycle, _, _, _ = self._fixtures()
        pack = make_manifest(tools=(make_tool(),))
        lifecycle.submit(pack)
        lifecycle.revoke(pack.id, "compromised")
        with pytest.raises(InvalidInputError, match="terminal"):
            lifecycle.submit(make_manifest(tools=(make_tool(),)))
        with pytest.raises(InvalidInputError):
            lifecycle.approve_update(pack.id)


class TestLifecycleCredentialGate:
    """required 凭据必须 TOOL 域（CAPABILITY_SECURITY.md §4 凭据域隔离）。"""

    def _fixtures(self) -> tuple[ToolPackLifecycle, FakePolicyEvaluator, FakeEventPublisher]:
        policy = FakePolicyEvaluator()
        events = FakeEventPublisher()
        lifecycle = ToolPackLifecycle(FakeToolPackStore(), policy, events)
        return lifecycle, policy, events

    def test_required_credential_outside_tool_domain_rejected(self) -> None:
        lifecycle, _, _ = self._fixtures()
        pack = make_manifest(
            tools=(make_tool(),),
            credentials=(
                CredentialRequirement(name="LLM_TOKEN", scope=CredentialScope.LLM, required=True),
            ),
        )
        with pytest.raises(PermanentPortError, match="TOOL-scoped"):
            lifecycle.submit(pack)

    def test_optional_or_tool_scoped_credentials_accepted(self) -> None:
        lifecycle, _, events = self._fixtures()
        pack = make_manifest(
            tools=(make_tool(),),
            credentials=(
                CredentialRequirement(name="MCP_TOKEN", scope=CredentialScope.TOOL, required=True),
                CredentialRequirement(name="OPT_TOKEN", scope=CredentialScope.LLM, required=False),
            ),
        )
        outcome = lifecycle.submit(pack)
        assert outcome.record.state is ToolPackState.INSTALLED
        assert events.method_calls("publish") == 1


class TestExecution:
    def test_execution_time_policy_deny(self) -> None:
        provider = FakeToolProvider(registered_tools=("lit_search",))
        policy = FakePolicyEvaluator()
        policy.set_decision("search.academic", PolicyDecision.DENY)
        with pytest.raises(PermanentPortError, match="policy denied"):
            execute_tool_call(
                provider,
                make_provider(),
                make_call(),
                policy,
                actor="agent-1",
            )
        assert provider.method_calls("execute") == 0

    def test_execution_time_requires_approval_blocks(self) -> None:
        """execution-time REQUIRE_APPROVAL 必须阻塞（与 Policy Wrapper 同语义）。

        审批通道接通前不得静默放行：不触达 provider，抛 APPROVAL_REJECTED。
        """
        provider = FakeToolProvider(registered_tools=("lit_search",))
        policy = FakePolicyEvaluator()
        policy.set_decision("search.academic", PolicyDecision.REQUIRE_APPROVAL)
        with pytest.raises(PermanentPortError) as exc_info:
            execute_tool_call(
                provider,
                make_provider(),
                make_call(),
                policy,
                actor="agent-1",
            )
        assert exc_info.value.failure_category is FailureCategory.APPROVAL_REJECTED
        assert provider.method_calls("execute") == 0

    def test_execution_allowed_calls_provider(self) -> None:
        provider = FakeToolProvider(registered_tools=("lit_search",))
        policy = FakePolicyEvaluator()
        outcome = execute_tool_call(provider, make_provider(), make_call(), policy, actor="agent-1")
        assert outcome.decision is PolicyDecision.ALLOW
        assert outcome.result is not None
        assert provider.method_calls("execute") == 1

    def test_frozen_tool_set_enforcement(self) -> None:
        with pytest.raises(PermanentPortError, match="frozen tool set"):
            require_frozen_tool_set(("other-provider",), "mcp-lit")
        require_frozen_tool_set(("mcp-lit",), "mcp-lit")


class TestResults:
    def test_small_result_stays_inline(self) -> None:
        store = FakeArtifactStore()
        outcome = spill_large_result(store, make_call(), b'{"ok": true}', threshold_bytes=1024)
        assert outcome.spilled is False
        assert outcome.artifact_ref is None
        assert store.method_calls("put") == 0

    def test_large_result_spills_to_artifact(self) -> None:
        store = FakeArtifactStore()
        payload = b"x" * 4096
        outcome = spill_large_result(store, make_call(), payload, threshold_bytes=1024)
        assert outcome.spilled is True
        assert outcome.artifact_ref is not None
        fetched = fetch_spilled_result(store, outcome.record)
        assert fetched == payload
        assert Digest.of_bytes(payload) == outcome.record.output_digest

    def test_spilled_result_digest_mismatch_detected(self) -> None:
        store = FakeArtifactStore()
        outcome = spill_large_result(store, make_call(), b"y" * 4096, threshold_bytes=1024)
        tampered = replace(outcome.record, output_digest=Digest.of_bytes(b"other"))
        with pytest.raises(ValueError, match="digest mismatch"):
            fetch_spilled_result(store, tampered)

    def test_threshold_must_be_positive(self) -> None:
        with pytest.raises(ValueError):
            spill_large_result(FakeArtifactStore(), make_call(), b"{}", threshold_bytes=0)


class TestPreflightRiskWiring:
    """preflight check_tools 的 effect/risk 挂接（M8）。"""

    def test_elevated_risk_provider_emits_warning(self) -> None:
        plan, context = protocol_fixtures.compiled()
        risky = replace(
            protocol_fixtures._tool_providers()["fixture-tools"],
            effect_class=EffectClass.EXECUTE,
        )
        catalog = replace(context.catalog, tool_providers={"fixture-tools": risky})
        context = replace(context, catalog=catalog)
        report = run_preflight(plan, context)
        assert "TOOL_RISK_ELEVATED" in {item.code for item in report.findings}
        elevated = next(item for item in report.findings if item.code == "TOOL_RISK_ELEVATED")
        assert elevated.severity.value == "WARNING"

    def test_low_risk_provider_no_warning(self) -> None:
        plan, context = protocol_fixtures.compiled()
        findings = check_tools(plan, context)
        assert all(item.code != "TOOL_RISK_ELEVATED" for item in findings)
