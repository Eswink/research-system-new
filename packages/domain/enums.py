"""Research OS 跨领域稳定枚举。

来源（权威）：
- FailureCategory: docs/reliability/FAILURE_MODEL.md
- ModelCapability: docs/architecture/MODEL_COMPATIBILITY.md + schemas/model-definition.schema.json
- PolicyDecision: docs/architecture/CAPABILITY_SECURITY.md
- EffectClass / ProviderType: docs/architecture/TOOL_RUNTIME.md
- ToolCallStatus / ToolResultStatus / RiskClass: packages/domain/tool_enums.py
- CredentialScope / SkillStatus / ToolPackState: packages/domain/tool_enums.py
- TrustProfile: docs/architecture/WORKSPACE_RUNTIME.md
- GateType / AutonomyLevel: docs/configuration/AUTONOMY_AND_GATES.md
- TrustLabel: docs/architecture/CAPABILITY_SECURITY.md
- QualityGateVerdict: docs/architecture/EVALUATION.md
- MemoryTier / MemoryType: docs/architecture/CONTEXT_ENGINE.md
- ArtifactState: docs/architecture/DATA_LIFECYCLE.md
- BackendKind: docs/architecture/AGENT_BACKENDS.md
- BudgetThreshold: docs/architecture/BUDGET_QUOTA.md
- RoleCategory / ActivationPolicy / WorkspacePolicy: schemas/role-definition.schema.json
- SelectionStrategy: docs/architecture/ROLE_MODEL.md
- ComparisonOperator: schemas/task-contract.schema.json
- TaskKind: docs/adr/ADR-0027-distributed-execution-plane.md（M16）
"""

from __future__ import annotations

from enum import StrEnum

from packages.domain.tool_enums import (
    CredentialScope as CredentialScope,
)
from packages.domain.tool_enums import (
    RiskClass as RiskClass,
)
from packages.domain.tool_enums import (
    SkillStatus as SkillStatus,
)
from packages.domain.tool_enums import (
    ToolCallStatus as ToolCallStatus,
)
from packages.domain.tool_enums import (
    ToolPackState as ToolPackState,
)
from packages.domain.tool_enums import (
    ToolResultStatus as ToolResultStatus,
)


class FailureCategory(StrEnum):
    CONFIGURATION = "CONFIGURATION"
    MODEL_AUTH = "MODEL_AUTH"
    MODEL_RATE_LIMIT = "MODEL_RATE_LIMIT"
    MODEL_TIMEOUT = "MODEL_TIMEOUT"
    MODEL_RELAY_UNAVAILABLE = "MODEL_RELAY_UNAVAILABLE"
    MODEL_INCOMPATIBLE = "MODEL_INCOMPATIBLE"
    MODEL_DRIFT = "MODEL_DRIFT"
    TOOL_UNAVAILABLE = "TOOL_UNAVAILABLE"
    TOOL_SCHEMA_MISMATCH = "TOOL_SCHEMA_MISMATCH"
    TOOL_TIMEOUT = "TOOL_TIMEOUT"
    POLICY_DENIED = "POLICY_DENIED"
    APPROVAL_REJECTED = "APPROVAL_REJECTED"
    WORKSPACE_FAILURE = "WORKSPACE_FAILURE"
    EXECUTION_FAILURE = "EXECUTION_FAILURE"
    ARTIFACT_CORRUPTION = "ARTIFACT_CORRUPTION"
    VALIDATION_FAILURE = "VALIDATION_FAILURE"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    WORKER_LOST = "WORKER_LOST"
    SYSTEM_BUG = "SYSTEM_BUG"
    SCIENTIFIC_NEGATIVE_RESULT = "SCIENTIFIC_NEGATIVE_RESULT"


class ModelCapability(StrEnum):
    CHAT = "CHAT"
    STREAMING = "STREAMING"
    TOOL_CALLING_NATIVE = "TOOL_CALLING_NATIVE"
    TOOL_CALLING_EMULATED = "TOOL_CALLING_EMULATED"
    STRUCTURED_OUTPUT_NATIVE = "STRUCTURED_OUTPUT_NATIVE"
    STRUCTURED_OUTPUT_PROMPTED = "STRUCTURED_OUTPUT_PROMPTED"
    VISION = "VISION"
    REASONING = "REASONING"
    EMBEDDING = "EMBEDDING"
    SEED = "SEED"
    USAGE_REPORTING = "USAGE_REPORTING"
    SYSTEM_FINGERPRINT = "SYSTEM_FINGERPRINT"


class CapabilityStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"
    DEGRADED = "DEGRADED"


class CapabilitySource(StrEnum):
    USER_DECLARED = "USER_DECLARED"
    DISCOVERED = "DISCOVERED"
    PROBED = "PROBED"
    ADMIN_OVERRIDE = "ADMIN_OVERRIDE"
    RUNTIME_OBSERVED = "RUNTIME_OBSERVED"


class EndpointHealth(StrEnum):
    UNKNOWN = "UNKNOWN"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    OPEN_CIRCUIT = "OPEN_CIRCUIT"
    DISABLED = "DISABLED"


class PolicyDecision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    ALLOW_WITH_CONSTRAINTS = "ALLOW_WITH_CONSTRAINTS"


class EffectClass(StrEnum):
    READ_ONLY = "READ_ONLY"
    WRITE = "WRITE"
    EXECUTE = "EXECUTE"
    NETWORK = "NETWORK"
    SECRET_USE = "SECRET_USE"
    DESTRUCTIVE = "DESTRUCTIVE"
    EXTERNAL_PUBLISH = "EXTERNAL_PUBLISH"


class ProviderType(StrEnum):
    NATIVE = "NATIVE"
    MCP = "MCP"
    REST = "REST"
    CLI = "CLI"
    REMOTE_WORKER = "REMOTE_WORKER"


class TrustLevel(StrEnum):
    BUILT_IN = "BUILT_IN"
    VERIFIED = "VERIFIED"
    USER_APPROVED = "USER_APPROVED"
    UNTRUSTED = "UNTRUSTED"
    REVOKED = "REVOKED"


class TrustProfile(StrEnum):
    TRUSTED_LOCAL = "TRUSTED_LOCAL"
    SANDBOXED_STANDARD = "SANDBOXED_STANDARD"
    SANDBOXED_RESTRICTED = "SANDBOXED_RESTRICTED"
    HARDENED_UNTRUSTED = "HARDENED_UNTRUSTED"


class GateType(StrEnum):
    POLICY_GATE = "POLICY_GATE"
    BUDGET_GATE = "BUDGET_GATE"
    QUALITY_GATE = "QUALITY_GATE"
    HUMAN_GATE = "HUMAN_GATE"
    SECURITY_GATE = "SECURITY_GATE"
    PUBLISH_GATE = "PUBLISH_GATE"


class AutonomyLevel(StrEnum):
    OBSERVE_ONLY = "OBSERVE_ONLY"
    SUPERVISED = "SUPERVISED"
    GUARDED_AUTONOMOUS = "GUARDED_AUTONOMOUS"
    FULLY_AUTONOMOUS = "FULLY_AUTONOMOUS"


class TrustLabel(StrEnum):
    TRUSTED_INTERNAL = "TRUSTED_INTERNAL"
    VERIFIED_SOURCE = "VERIFIED_SOURCE"
    UNTRUSTED_EXTERNAL = "UNTRUSTED_EXTERNAL"
    GENERATED = "GENERATED"
    USER_PROVIDED = "USER_PROVIDED"


class QualityGateVerdict(StrEnum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    REVISE = "REVISE"
    BLOCK = "BLOCK"


class MemoryTier(StrEnum):
    SESSION = "SESSION"
    RUN = "RUN"
    PROJECT = "PROJECT"
    ORGANIZATION = "ORGANIZATION"


class MemoryType(StrEnum):
    FACT = "FACT"
    DECISION = "DECISION"
    NEGATIVE_RESULT = "NEGATIVE_RESULT"
    LESSON = "LESSON"
    PROCEDURE = "PROCEDURE"
    PREFERENCE = "PREFERENCE"
    OPEN_QUESTION = "OPEN_QUESTION"


class ArtifactState(StrEnum):
    STAGED = "STAGED"
    VERIFIED = "VERIFIED"
    QUARANTINED = "QUARANTINED"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DELETED_TOMBSTONE = "DELETED_TOMBSTONE"


class BackendKind(StrEnum):
    OPENHANDS_NATIVE = "OPENHANDS_NATIVE"
    SPECIALIZED_LANGGRAPH = "SPECIALIZED_LANGGRAPH"
    EXTERNAL_AGENT_ACP = "EXTERNAL_AGENT_ACP"
    CLINE_SDK = "CLINE_SDK"
    CUSTOM_RUNTIME = "CUSTOM_RUNTIME"


class BudgetThreshold(StrEnum):
    SOFT_WARNING = "SOFT_WARNING"
    AUTO_DEGRADE = "AUTO_DEGRADE"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    HARD_STOP = "HARD_STOP"


class RoleCategory(StrEnum):
    MANAGEMENT = "management"
    DISCOVERY = "discovery"
    EXPLORATION = "exploration"
    EXPERIMENT = "experiment"
    EVALUATION = "evaluation"
    DELIVERABLE = "deliverable"


class ActivationPolicy(StrEnum):
    ALWAYS = "ALWAYS"
    REQUIRED_BY_PROTOCOL = "REQUIRED_BY_PROTOCOL"
    ON_DEMAND = "ON_DEMAND"
    BUDGET_PERMITTING = "BUDGET_PERMITTING"
    DISABLED = "DISABLED"


class WorkspacePolicy(StrEnum):
    READ_ONLY = "read_only"
    NOTES_ONLY = "notes_only"
    ISOLATED_WRITABLE = "isolated_writable"
    DELIVERABLE_ONLY = "deliverable_only"


class SelectionStrategy(StrEnum):
    FIXED = "FIXED"
    ROUND_ROBIN = "ROUND_ROBIN"
    CAPABILITY_BEST_FIT = "CAPABILITY_BEST_FIT"
    COST_AWARE = "COST_AWARE"
    EVAL_SCORE_AWARE = "EVAL_SCORE_AWARE"


class ComparisonOperator(StrEnum):
    GT = "GT"
    GTE = "GTE"
    EQ = "EQ"
    LTE = "LTE"
    LT = "LT"


class AcceptanceCriterionType(StrEnum):
    SCHEMA_VALID = "SCHEMA_VALID"
    ARTIFACT_EXISTS = "ARTIFACT_EXISTS"
    TEST_PASSES = "TEST_PASSES"
    METRIC_THRESHOLD = "METRIC_THRESHOLD"
    EVIDENCE_COVERAGE = "EVIDENCE_COVERAGE"
    REVIEW_SCORE = "REVIEW_SCORE"
    POLICY_COMPLIANT = "POLICY_COMPLIANT"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    CUSTOM_EVALUATOR = "CUSTOM_EVALUATOR"


class ModelBindingMode(StrEnum):
    EXPLICIT_MODEL = "EXPLICIT_MODEL"
    MODEL_PROFILE = "MODEL_PROFILE"
    INHERIT = "INHERIT"


class ReviewPanelRole(StrEnum):
    """Role 在评审面板中的角色（异构评审约束按此属性聚合，不依赖 role id）。"""

    WRITER = "WRITER"
    REVIEWER = "REVIEWER"
    NONE = "NONE"


class TaskKind(StrEnum):
    """任务类型（M16）：默认 AGENT_SESSION 保持既有语义向后兼容；
    EXECUTION 为远程 worker 可 claim 的一次性执行作业（ADR-0027）。"""

    AGENT_SESSION = "AGENT_SESSION"
    EXECUTION = "EXECUTION"
