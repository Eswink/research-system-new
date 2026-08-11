"""状态机公共基础：错误类型与 terminal 判定。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InvalidTransitionError(ValueError):
    """非法状态迁移。"""

    current: str
    event: str

    def __str__(self) -> str:
        return f"invalid transition: event={self.event!r} from state={self.current!r}"


def is_terminal(state: str, terminal_states: frozenset[str]) -> bool:
    return state in terminal_states
