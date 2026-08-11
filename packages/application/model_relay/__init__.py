"""Model Relay application 层。

use cases + inward-owned Ports + DTO/Domain 映射。
本层只依赖 packages.domain，不依赖任何 adapter。
"""

from packages.application.model_relay.eligibility import EligibilityDecision, decide_eligibility
from packages.application.model_relay.endpoint_policy import (
    EndpointUrlPolicy,
    validate_endpoint_url,
)
from packages.application.model_relay.fallback import FallbackPlan, plan_fallback
from packages.application.model_relay.fingerprint import build_fingerprint, endpoint_config_digest
from packages.application.model_relay.health import evaluate_endpoint_health
from packages.application.model_relay.ports import (
    CompletionRequest,
    CompletionResult,
    CredentialResolver,
    EndpointStore,
    ModelRelayGateway,
    ModelsListResult,
    SecretValue,
    ToolCallDraft,
)
from packages.application.model_relay.probe import ProbeOptions, run_endpoint_test, run_probe
from packages.application.model_relay.suite import DiscoveredModels, default_probe_suite

__all__ = [
    "CompletionRequest",
    "CompletionResult",
    "CredentialResolver",
    "DiscoveredModels",
    "EligibilityDecision",
    "EndpointStore",
    "EndpointUrlPolicy",
    "FallbackPlan",
    "ModelsListResult",
    "ModelRelayGateway",
    "ProbeOptions",
    "SecretValue",
    "ToolCallDraft",
    "build_fingerprint",
    "decide_eligibility",
    "default_probe_suite",
    "endpoint_config_digest",
    "evaluate_endpoint_health",
    "plan_fallback",
    "run_endpoint_test",
    "run_probe",
    "validate_endpoint_url",
]
