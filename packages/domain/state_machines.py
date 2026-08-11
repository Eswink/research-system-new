"""Research OS 域状态机聚合入口。

状态集合与迁移表来自 `docs/reliability/RUN_STATE_MACHINE.md`；
terminal 状态不可回退。
"""

from __future__ import annotations

from packages.domain.phase_state import PhaseRunState
from packages.domain.run_state import ResearchRunState
from packages.domain.session_state import AgentSessionState, CancellationState
from packages.domain.state_base import InvalidTransitionError, is_terminal
from packages.domain.task_state import ResearchTaskState

__all__ = [
    "AgentSessionState",
    "CancellationState",
    "InvalidTransitionError",
    "PhaseRunState",
    "ResearchRunState",
    "ResearchTaskState",
    "is_terminal",
]
