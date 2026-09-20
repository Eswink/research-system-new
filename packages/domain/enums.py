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
    # M17 GPU execution plane: device/CUDA infra failures are distinct from
    # generic EXECUTION_FAILURE and from a scientific negative result.
    GPU_UNAVAILABLE = "GPU_UNAVAILABLE"
    GPU_OOM = "GPU_OOM"
    ARTIFACT_CORRUPTION = "ARTIFACT_CORRUPTION"
    VALIDATION_FAILURE = "VALIDATION_FAILURE"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    WORKER_LOST = "WORKER_LOST"
    SYSTEM_BUG = "SYSTEM_BUG"
    SCIENTIFIC_NEGATIVE_RESULT = "SCIENTIFIC_NEGATIVE_RESULT"


class FailureAction(StrEnum):
    """失败的完成该被怎么处置（PLAN-20260915-078）。

    RETRY        重试（再排一次队），attempt 递增；
    DEAD_LETTER  不再自动重试，进死信等待人工恢复；
    FAIL         终态失败（与重试策略出现前一致的行为）。
    """

    RETRY = "RETRY"
    DEAD_LETTER = "DEAD_LETTER"
    FAIL = "FAIL"


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


class LLMProtocol(StrEnum):
    """LLMEndpoint 声明的线协议族（唯一词表）。

    - ``OPENAI_COMPATIBLE``：``/chat/completions`` 或 ``/responses``（按 ``api_style``）；
    - ``ANTHROPIC``：``/messages`` Messages 形态（``x-api-key`` + ``anthropic-version``）。

    取值名指**线协议族**而非模型厂商绑定（AGENTS.md §1 禁止的是把供应商写进 Domain）。
    执行侧（relay 网关与 OpenHands llm_factory）按本枚举选路，未知取值 fail-closed
    ——静默回退会让「配了某协议」与「跑的是另一种形态」不可区分。
    """

    OPENAI_COMPATIBLE = "OPENAI_COMPATIBLE"
    ANTHROPIC = "ANTHROPIC"


class ThinkingIntensity(StrEnum):
    """模型**声明的**思考强度级别（厂商中立词表）。

    级别是相对词，不是任何 provider 的私有取值：登记方声明意图，由执行侧的
    协议映射决定怎么落地（未实现的映射**如实登记**，不得假装生效）。
    """

    MINIMAL = "MINIMAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    MAX = "MAX"


class ModelDriftState(StrEnum):
    """模型标识漂移的三态（AGENTS.md §4：同名漂移必须可见）。

    - `MATCH`：probe 返回的模型标识与登记声明值**精确相等**（只忽略首尾空白）；
    - `DRIFT`：两者都存在但不相等（**任何**差异都算，包括只差大小写——本仓无法证明
      它们指向同一底层模型，折叠大小写等于替 provider 打包票）；
    - `UNKNOWN`：**未探到**（没探测 / provider 没回模型名 / 探测失败）。

    `UNKNOWN` **不得**被读成「无漂移」：它是「无法证明一致」，不是「已证明一致」。
    """

    MATCH = "MATCH"
    DRIFT = "DRIFT"
    UNKNOWN = "UNKNOWN"


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
