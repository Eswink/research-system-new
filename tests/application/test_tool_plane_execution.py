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
from packages.domain.tools import CredentialRequirement
from tests.application import protocol_fixtures
from tests.application.tool_plane_support import (
    make_call,
    make_manifest,
    make_provider,
    make_tool,
)


class TestLifecycle:
    def _fixtures(self) -> tuple[ToolPackLifecycle, FakePolicyEvaluator, FakeEventPublisher]:
        policy = FakePolicyEvaluator()
        events = FakeEventPublisher()
        lifecycle = ToolPackLifecycle(FakeToolPackStore(), policy, events)
        return lifecycle, policy, events

    def test_install_verifies_digest(self) -> None:
        lifecycle, _, _ = self._fixtures()
        pack = make_manifest(tools=(make_tool(),))
        tampered = replace(pack, requested_capabilities=["extra.evil"])
        with pytest.raises(PermanentPortError, match="digest mismatch"):
            lifecycle.install(tampered)
        record = lifecycle.install(pack)
        assert record.state is ToolPackState.INSTALLED

    def test_install_policy_deny(self) -> None:
        lifecycle, policy, _ = self._fixtures()
        policy.set_decision("tool_pack.install", PolicyDecision.DENY)
        with pytest.raises(PermanentPortError, match="policy denied"):
            lifecycle.install(make_manifest(tools=(make_tool(),)))

    def test_update_expanded_permissions_requires_approval_policy(self) -> None:
        lifecycle, policy, events = self._fixtures()
        policy.set_decision("tool_pack.update.expanded", PolicyDecision.DENY)
        pack_v1 = make_manifest(tools=(make_tool(),))
        lifecycle.install(pack_v1)
        pack_v2 = make_manifest(
            tools=(make_tool(),),
            capabilities=("search.academic", "citation.parse"),
        )
        diff = permission_diff(pack_v1, pack_v2)
        assert diff.added_capabilities == ("citation.parse",)
        with pytest.raises(PermanentPortError, match="policy denied"):
            lifecycle.update(pack_v2)
        assert events.method_calls("publish") == 1  # 仅 install 事件

    def test_update_without_permission_change(self) -> None:
        lifecycle, _, events = self._fixtures()
        pack_v1 = make_manifest(tools=(make_tool(),))
        lifecycle.install(pack_v1)
        pack_v2 = make_manifest(tools=(make_tool("lit_search", capabilities=("search.academic",)),))
        assert lifecycle.update(pack_v2).manifest.id == "lit-pack"
        assert events.method_calls("publish") == 2

    def test_revoke_requires_reason_and_denies_repeat(self) -> None:
        lifecycle, _, events = self._fixtures()
        pack = make_manifest(tools=(make_tool(),))
        lifecycle.install(pack)
        with pytest.raises(InvalidInputError):
            lifecycle.revoke(pack.id, "")
        revoked = lifecycle.revoke(pack.id, "license violation")
        assert revoked.state is ToolPackState.REVOKED
        assert revoked.revoked_reason == "license violation"
        with pytest.raises(InvalidInputError):
            lifecycle.revoke(pack.id, "again")
        assert events.method_calls("publish") == 2

    def test_update_revoked_pack_rejected(self) -> None:
        lifecycle, _, _ = self._fixtures()
        pack = make_manifest(tools=(make_tool(),))
        lifecycle.install(pack)
        lifecycle.revoke(pack.id, "compromised")
        with pytest.raises(InvalidInputError):
            lifecycle.update(make_manifest(tools=(make_tool(),)))


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
            lifecycle.install(pack)

    def test_optional_or_tool_scoped_credentials_accepted(self) -> None:
        lifecycle, _, events = self._fixtures()
        pack = make_manifest(
            tools=(make_tool(),),
            credentials=(
                CredentialRequirement(name="MCP_TOKEN", scope=CredentialScope.TOOL, required=True),
                CredentialRequirement(name="OPT_TOKEN", scope=CredentialScope.LLM, required=False),
            ),
        )
        record = lifecycle.install(pack)
        assert record.state is ToolPackState.INSTALLED
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
