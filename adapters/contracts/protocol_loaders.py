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
    SessionToolBinding,
    StopConditions,
)


def _session_tool_bindings(raw_bindings: list[dict[str, Any]]) -> list[SessionToolBinding]:
    """读取 phase 的会话工具绑定（provider id → SDK 工具名）。

    **只读不解释**：绑定是否指向真实存在的工具、provider 是否在冻结集内，
    都在会话解析处判定（那里能看到冻结集与装配方提供的实现表）；
    本层只保证声明不在这步丢掉，且字段缺失即**空**（既有语义）。
    """
    return [
        SessionToolBinding(
            provider_id=item["provider_id"],
            tool_name=item["tool_name"],
        )
        for item in raw_bindings
    ]


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
        # 缺省空：文档不写绑定 ⇒ 既有语义（provider id 直接交给 SDK，未注册即点名失败）。
        session_tool_bindings=_session_tool_bindings(raw.get("session_tool_bindings", [])),
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
