"""provider 凭据绑定：`credential_ref` 的**存在性**判定与四态（PLAN-20260915-074）。

`ToolProviderSpec` 此前**无法表达**"这个 provider 需要哪个凭据"：要求只存在于
adapter 的构造参数里（`adapters/mcp/provider.py:63` 的 streamable_http 甚至要求
必须有），注册面写不了、读面看不见、健康探测也从不问。本模块把它变成
**准入条件 + 可见状态**：

    NOT_DECLARED  未声明 credential_ref —— 与从前一致，不做任何判断
    ABSENT        声明了，但该凭据此刻不可解析 —— provider 不可用
    PRESENT       声明了且可解析 —— 可用
    UNCHECKED     声明了，但存在性检查本身不可用（凭据边界抛错）—— 不猜，如实标注

**只查存在性，不碰明文**：判定走 `CredentialResolver.has`，**不调用 `resolve`**、
不物化 `SecretValue`、不落盘、不进日志/异常/repr。读面只有 `state` /
`credential_ref` / `present` 三样，**没有值**——要知道值是什么，去看凭据来源本身。

**语义是"声明即必需"**：写了 `credential_ref` 就表示"没有它这个 provider 不可用"
（MCP streamable_http 就是这样）。因此**可选**凭据不声明——例如 NCBI E-utilities
无 key 也能用（只是限速更严），它的 `credential_ref` 是构造参数而不是必需性声明，
示例配置按此对齐（见 examples/config/tool_providers.yaml 注释）。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.ports.credential_resolver import CredentialResolver
from packages.domain.tools import ToolProviderSpec

NOT_DECLARED = "NOT_DECLARED"
ABSENT = "ABSENT"
PRESENT = "PRESENT"
UNCHECKED = "UNCHECKED"
STATES = (NOT_DECLARED, ABSENT, PRESENT, UNCHECKED)


@dataclass(frozen=True, slots=True)
class CredentialBinding:
    """凭据绑定的可读投影：状态 + 引用名 + 是否在场；**永不**携带凭据值。"""

    state: str
    credential_ref: str | None = None
    present: bool = False

    def __post_init__(self) -> None:
        if self.state not in STATES:
            raise ValueError(f"unknown credential binding state: {self.state!r}")
        # 只有 PRESENT 才允许 present=True：否则读面会把"没凭据"误读成"有凭据"
        if self.present != (self.state == PRESENT):
            raise ValueError("present is only set for the PRESENT state")
        if (self.credential_ref is not None) == (self.state == NOT_DECLARED):
            raise ValueError("credential ref is set exactly when one was declared")


def resolve_credential_binding(
    spec: ToolProviderSpec, *, resolver: CredentialResolver
) -> CredentialBinding:
    """按 `spec.credential_ref` 判定绑定状态；**只查存在性**，不解析明文。

    存在性检查抛错时不猜：返回 `UNCHECKED` 并让调用方按"不可证明"处理
    （探测门把 UNCHECKED 也判 UNKNOWN，读面如实显示 UNCHECKED）。
    """
    ref = spec.credential_ref
    if ref is None or ref == "":
        return CredentialBinding(state=NOT_DECLARED)
    try:
        present = bool(resolver.has(ref))
    except Exception:  # noqa: BLE001 - 存在性检查不可用按 UNCHECKED 收敛，不伪装在场
        return CredentialBinding(state=UNCHECKED, credential_ref=ref)
    return CredentialBinding(
        state=PRESENT if present else ABSENT, credential_ref=ref, present=present
    )


def missing_reason(binding: CredentialBinding) -> str | None:
    """不可用时的**可读原因**（点名引用，不点值）；PRESENT/未声明返回 None。"""
    if binding.state == ABSENT:
        return (
            f"provider 声明必需凭据 {binding.credential_ref!r}，"
            "但凭据边界当前解析不到它（provider 不可用）"
        )
    if binding.state == UNCHECKED:
        return (
            f"provider 声明必需凭据 {binding.credential_ref!r}，"
            "但凭据存在性检查不可用（已按不可证明收敛）"
        )
    return None
