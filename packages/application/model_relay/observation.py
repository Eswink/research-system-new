"""一次会话的运行时观测（GOAL-010 EC-04）。

把「这次会话**实际用到的**执行目标」与「provider 侧 usage 度量**报告的** model 名」
配成一对：前者是**配置**事实（端点头 = 端点配置的确定性 digest，本模块不触网），
后者是**观测**事实（来自 `ConversationStats`，不是请求里写的那个 id）。

边界（写死）：

- **不产生空观测**：没有观测到任何 model 名 ⇒ `session_observation` 返回 `None`。
  「没观测到」在读面是缺项，不是「无漂移」（AGENTS.md §4）。
- **不编造端点头**：会话没有执行目标（`endpoint is None`）时端点头留 `None`，
  **不**拿别的 endpoint 顶上。
- **不判结论**：本模块只搬运事实；两态结论由 `build_live_run_record` 的既有规则判。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from packages.application.model_relay.fingerprint import endpoint_config_digest
from packages.application.ports.agent_runtime import AgentSessionResult
from packages.domain.models import LLMEndpoint


@dataclass(frozen=True, slots=True)
class RunSessionObservation:
    """一次会话的观测：端点头 + provider 侧报告的 model 名（至少一个）。"""

    endpoint_config_digest: str | None
    observed_model_identifiers: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.observed_model_identifiers:
            raise ValueError("an observation must carry at least one observed model name")


def session_observation(
    endpoint: LLMEndpoint | None,
    observed_model_identifiers: tuple[str, ...],
) -> RunSessionObservation | None:
    """会话终态时的观测；**没有观测到 model 名 ⇒ `None`**（不产生空观测）。"""
    if not observed_model_identifiers:
        return None
    return RunSessionObservation(
        endpoint_config_digest=(
            str(endpoint_config_digest(endpoint)) if endpoint is not None else None
        ),
        observed_model_identifiers=observed_model_identifiers,
    )


def observe_session(
    on_observation: Callable[[RunSessionObservation], None] | None,
    endpoint: LLMEndpoint | None,
    session_result: AgentSessionResult | None,
) -> None:
    """把一次会话的观测交给收集方；**没有观测 ⇒ 不调用**（空调用不是一条事实）。

    调用点是执行循环里「这次会话实际用到了哪个端点」可见的地方：端点取自会话 spec
    携带的执行目标，model 名取自会话结果（provider 侧报告的那个）。两者缺一都不发。
    """
    if on_observation is None or session_result is None:
        return
    observation = session_observation(endpoint, session_result.observed_model_identifiers)
    if observation is not None:
        on_observation(observation)


__all__ = ["RunSessionObservation", "observe_session", "session_observation"]
