"""ProtocolDefinition 契约加载器。"""

from __future__ import annotations

from typing import Any

from adapters.contracts.base import (
    ContractLoadError,
    load_json_schema,
    load_yaml,
    validate_instance,
)
from packages.domain.core import Version
from packages.domain.enums import GateType
from packages.domain.protocols import (
    CapabilityExecution,
    PhaseStrategy,
    ProtocolDefinition,
    ProtocolPhase,
    RoleRequirement,
    StopConditions,
)


def _role_requirements(raw_roles: list[dict[str, Any]]) -> list[RoleRequirement]:
    return [
        RoleRequirement(
            role=item["role"],
            min_instances=item["min_instances"],
            max_instances=item["max_instances"],
        )
        for item in raw_roles
    ]


def _stop_conditions(raw: dict[str, Any] | None) -> StopConditions | None:
    if raw is None:
        return None
    return StopConditions(
        max_iterations=raw.get("max_iterations"),
        budget_exhausted=bool(raw.get("budget_exhausted", False)),
    )


def _phase_from_mapping(raw: dict[str, Any]) -> ProtocolPhase:
    task_contract = raw.get("task_contract")
    task_contracts = list(raw.get("task_contracts", []))
    if task_contract is not None and task_contract not in task_contracts:
        task_contracts.insert(0, task_contract)
    gate = GateType(raw["gate"]) if raw.get("gate") else None
    return ProtocolPhase(
        id=raw["id"],
        name=raw.get("name"),
        strategy=PhaseStrategy(raw["strategy"]),
        depends_on=list(raw.get("depends_on", [])),
        inputs=list(raw.get("inputs", [])),
        outputs=list(raw.get("outputs", [])),
        required_roles=_role_requirements(raw.get("required_roles", [])),
        required_capabilities=list(raw.get("required_capabilities", [])),
        task_contract=task_contract,
        task_contracts=task_contracts,
        timeout_seconds=raw.get("timeout_seconds"),
        gate=gate,
        stop_conditions=_stop_conditions(raw.get("stop_conditions")),
        # 缺省 "session"：文档不写该字段 ⇒ 逐字节保持既有语义（会话工具）。
        capability_execution=CapabilityExecution(raw.get("capability_execution", "session")),
    )


def load_protocol(relative_path: str) -> ProtocolDefinition:
    """读取并校验单个 protocol 文件。"""
    data = load_yaml(relative_path)
    schema = load_json_schema("protocol.schema.json")
    try:
        validate_instance(schema, data, relative_path)
        if not isinstance(data, dict):
            raise ContractLoadError(f"{relative_path} must be a mapping")
        phases = [_phase_from_mapping(item) for item in data["phases"]]
        return ProtocolDefinition(
            id=data["id"],
            version=Version(data["version"]),
            phases=phases,
        )
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ContractLoadError):
            raise
        raise ContractLoadError(f"cannot load protocol at {relative_path}: {exc}") from exc
