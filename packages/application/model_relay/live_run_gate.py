"""live run 的门（GOAL-008 EC-04）。

门回答一个问题：**此刻能不能跑一次真实 run？** 两个条件，都不满足就不开门：

1. **runtime 显式配置**：默认 runtime 是 Fake（AGENTS.md §11 / 用户授权 (4)）——
   Fake 跑出来的不是真实 run，所以门看的是「配置项等于 live runtime」；
2. **凭据可解析**：用 `CredentialResolver.has()`——它是**存在性检查**，
   **不物化明文**（`resolve` 才要值）。门只需要知道「能不能」，不需要知道「是什么」。

门不开时**不发起任何网络请求**：本模块不接收 gateway、不构造 URL、不碰 socket，
只做上面两条判断。因此「门关着 ⇒ 零出站」是**结构性**保证，并由离线判据实测钉住。

门不开的产物是一条如实的 `NOT_VERIFIED` 记录（`skip_record_for_gate`）——
**skip 不是 PASS**。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.model_relay.live_run_record import (
    LiveRunRecord,
    not_verified_live_run_record,
)
from packages.application.ports import CredentialResolver
from packages.domain.models import LLMEndpoint


@dataclass(frozen=True, slots=True)
class LiveRunGate:
    """门的判定结果：开/关 + 理由（关时**点名所有**未满足的条件）。"""

    open: bool
    reason: str
    credential_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.open and not self.reason:
            raise ValueError("a closed gate must name why it is closed")


def evaluate_live_run_gate(
    *,
    credentials: CredentialResolver,
    endpoint: LLMEndpoint,
    agent_runtime: str,
    live_agent_runtime: str,
) -> LiveRunGate:
    """判定 live run 的门（无网络、无凭据值）。

    理由里列出**全部**未满足条件：只报一条会让操作者多跑一个来回。
    """
    unmet: list[str] = []
    if not agent_runtime:
        unmet.append(
            f"agent runtime is not configured (need {live_agent_runtime!r}; default stays fake)"
        )
    elif agent_runtime != live_agent_runtime:
        unmet.append(
            f"agent runtime {agent_runtime!r} is not the live runtime {live_agent_runtime!r}"
        )
    credential_ok = credentials.has(endpoint.credential_ref)
    if not credential_ok:
        unmet.append(f"credential {endpoint.credential_ref!r} is not resolvable")

    if unmet:
        return LiveRunGate(
            open=False,
            reason="; ".join(unmet),
            credential_ref=None if credential_ok else endpoint.credential_ref,
        )
    return LiveRunGate(open=True, reason="live run gate is open")


def skip_record_for_gate(run_id: str, gate: LiveRunGate) -> LiveRunRecord:
    """门关着时的记录：如实写明「没跑」以及**缺哪一个凭据**。"""
    if gate.open:
        raise ValueError("an open gate is not a skip")
    return not_verified_live_run_record(
        run_id=run_id,
        reason=f"live run skipped: {gate.reason}",
        credential_ref=gate.credential_ref,
    )


__all__ = ["LiveRunGate", "evaluate_live_run_gate", "skip_record_for_gate"]
