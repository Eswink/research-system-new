"""Team plan 投影值对象：role activation 与 phase assignment。

来源：docs/architecture/ROLE_MODEL.md §3-§4；编译期由
packages/application/protocol_compile/resolution.py 生成，进入 CompiledRunPlan。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RoleActivationRecord:
    """Role 激活/折叠投影：编译期确定的 role 状态与等价 Skill。"""

    role_id: str
    activated: bool
    policy: str
    reason: str
    folded_skill: str | None = None

    def __post_init__(self) -> None:
        if not self.role_id:
            raise ValueError("activation record role_id must not be empty")
        if not self.reason:
            raise ValueError("activation record reason must not be empty")


@dataclass(frozen=True, slots=True)
class PhaseAssignment:
    """phase → role → agent 绑定投影（RequiredRoles 的稳定解析结果）。"""

    phase_id: str
    role_assignments: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.phase_id:
            raise ValueError("phase assignment phase_id must not be empty")
