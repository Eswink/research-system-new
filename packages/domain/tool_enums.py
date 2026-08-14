"""M8 Tool Plane / Skill Registry 稳定枚举。

来源（权威）：
- ToolCallStatus / ToolResultStatus / RiskClass: docs/architecture/TOOL_RUNTIME.md
- CredentialScope: docs/architecture/CAPABILITY_SECURITY.md §4
- SkillStatus: docs/architecture/TOOL_RUNTIME.md（Skill 生命周期）
- ToolPackState: docs/security/PLUGIN_TOOL_SUPPLY_CHAIN.md（install/update/revoke）

为避免 packages/domain/enums.py 超出 300 行硬阈值，M8 新增枚举放在本模块；
`enums.py` re-export 保持既有 import 路径不变。
"""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "CredentialScope",
    "RiskClass",
    "SkillStatus",
    "ToolCallStatus",
    "ToolPackState",
    "ToolResultStatus",
]


class ToolCallStatus(StrEnum):
    REQUESTED = "REQUESTED"
    IN_FLIGHT = "IN_FLIGHT"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ToolResultStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"


class CredentialScope(StrEnum):
    """凭据信任域（docs/architecture/CAPABILITY_SECURITY.md §4 四分离）。"""

    LLM = "LLM"
    TOOL = "TOOL"
    WORKSPACE = "WORKSPACE"
    USER_OAUTH = "USER_OAUTH"


class RiskClass(StrEnum):
    """effect/risk 分层（docs/architecture/TOOL_RUNTIME.md §2）。"""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SkillStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"


class ToolPackState(StrEnum):
    INSTALLED = "INSTALLED"
    SUPERSEDED = "SUPERSEDED"
    REVOKED = "REVOKED"
