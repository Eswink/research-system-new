"""SQLite 持久化的确定性序列化助手。

持久化载荷使用 domain canonical JSON（docs/architecture/
DETERMINISTIC_SERIALIZATION.md），保证同构输入产生同构字节，
digest 语义与 domain 一致。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from packages.domain.core import ID, Timestamp
from packages.domain.enums import (
    AcceptanceCriterionType,
    ComparisonOperator,
    FailureCategory,
    TaskKind,
)
from packages.domain.events import EventEnvelope, EventType
from packages.domain.serialization import canonical_json_bytes, digest_of
from packages.domain.tasks import (
    AcceptanceCriterion,
    ExperimentExecutionSpec,
    ResearchTask,
    RetryPolicy,
    TaskContract,
)


@dataclass(frozen=True, slots=True)
class TaskRow:
    task: ResearchTask
    contract: TaskContract


def encode_task(task: ResearchTask, contract: TaskContract) -> tuple[str, str]:
    """ResearchTask + TaskContract → canonical JSON 文本对。"""
    return (
        canonical_json_bytes(task).decode("utf-8"),
        canonical_json_bytes(contract).decode("utf-8"),
    )


def decode_task(task_json: str, contract_json: str) -> TaskRow:
    """canonical JSON 文本 → ResearchTask + TaskContract。"""
    return TaskRow(
        task=_decode_research_task(json.loads(task_json)),
        contract=_decode_task_contract(json.loads(contract_json)),
    )


def decode_contract(contract_json: str) -> TaskContract:
    """只有 contract_json 时解出 TaskContract（完成路径要读 retry_policy，PLAN-20260915-078）。"""
    return _decode_task_contract(json.loads(contract_json))


def _decode_research_task(payload: dict[str, Any]) -> ResearchTask:
    phase_run_id = payload.get("phase_run_id")
    return ResearchTask(
        id=ID(payload["id"]["value"]),
        run_id=ID(payload["run_id"]["value"]),
        phase_run_id=ID(phase_run_id["value"]) if phase_run_id else None,
        contract_id=payload.get("contract_id"),
        assigned_agent_id=payload.get("assigned_agent_id"),
        status=payload["status"],
        priority=payload["priority"],
        attempt=payload["attempt"],
        idempotency_key=payload.get("idempotency_key"),
        lease_id=payload.get("lease_id"),
        kind=TaskKind(payload.get("kind", TaskKind.AGENT_SESSION.value)),
        partition=payload.get("partition"),
        required_capability=payload.get("required_capability"),
    )


def _decode_task_contract(payload: dict[str, Any]) -> TaskContract:
    retry = payload.get("retry_policy")
    return TaskContract(
        id=payload["id"],
        version=payload["version"],
        purpose=payload["purpose"],
        required_capabilities=list(payload.get("required_capabilities", [])),
        input_schema=payload.get("input_schema"),
        output_schema=payload.get("output_schema"),
        required_artifacts=list(payload.get("required_artifacts", [])),
        acceptance_criteria=[
            _decode_criterion(item) for item in payload.get("acceptance_criteria", [])
        ],
        budget=_decode_budget(payload.get("budget", {})),
        timeout_seconds=payload.get("timeout_seconds"),
        retry_policy=_decode_retry_policy(retry) if retry else None,
        failure_policy=payload.get("failure_policy", {}),
        idempotency_scope=payload.get("idempotency_scope", "task"),
        # GOAL-011 EC-03：`experiment` 声明往返（缺省 None ⇒ 会话语义）。
        experiment=_decode_experiment(payload.get("experiment")),
    )


def _decode_experiment(payload: dict[str, Any] | None) -> ExperimentExecutionSpec | None:
    if payload is None:
        return None
    return ExperimentExecutionSpec(
        script=str(payload.get("script", "")),
        image=str(payload.get("image", "")),
        command=str(payload.get("command", "python experiment.py")),
        timeout_seconds=int(payload.get("timeout_seconds", 180)),
    )


def _decode_criterion(payload: dict[str, Any]) -> AcceptanceCriterion:
    threshold = payload.get("threshold")
    return AcceptanceCriterion(
        type=AcceptanceCriterionType(payload["type"]),
        description=payload.get("description", ""),
        target=payload.get("target"),
        artifact=payload.get("artifact"),
        minimum_sources=payload.get("minimum_sources"),
        minimum_retrieved_sources=payload.get("minimum_retrieved_sources"),
        metric=payload.get("metric"),
        operator=ComparisonOperator(payload["operator"]) if payload.get("operator") else None,
        threshold=Decimal(threshold) if threshold is not None else None,
        evaluator=payload.get("evaluator"),
    )


def _decode_budget(payload: dict[str, Any]) -> dict[str, Decimal | None]:
    return {key: Decimal(value) if value is not None else None for key, value in payload.items()}


def _decode_retry_policy(payload: dict[str, Any]) -> RetryPolicy:
    return RetryPolicy(
        max_attempts=payload["max_attempts"],
        retryable_categories=[
            FailureCategory(item) for item in payload.get("retryable_categories", [])
        ],
        # 退避（PLAN-20260915-079）：退避字段之前落盘的契约没有这两个键 ⇒ 缺省 = 立即重排。
        backoff_seconds=payload.get("backoff_seconds"),
        max_backoff_seconds=payload.get("max_backoff_seconds"),
    )


def encode_envelope(envelope: EventEnvelope) -> str:
    """EventEnvelope → canonical JSON 文本。"""
    return canonical_json_bytes(envelope).decode("utf-8")


def decode_envelope(text: str) -> EventEnvelope:
    """canonical JSON 文本 → EventEnvelope（payload_digest 重新校验）。"""
    payload = json.loads(text)
    return EventEnvelope(
        event_id=payload["event_id"],
        event_type=EventType(payload["event_type"]),
        schema_version=payload["schema_version"],
        occurred_at=decode_timestamp(payload["occurred_at"]["value"]),
        actor=payload["actor"],
        scope=payload["scope"],
        payload=payload["payload"],
        payload_digest=digest_of(payload["payload"]),
        project_id=payload.get("project_id"),
        run_id=payload.get("run_id"),
        phase_run_id=payload.get("phase_run_id"),
        task_id=payload.get("task_id"),
        agent_session_id=payload.get("agent_session_id"),
        trace_id=payload.get("trace_id"),
    )


def decode_timestamp(text: str) -> Timestamp:
    """ISO 文本 → domain Timestamp（UTC）。"""
    return Timestamp(datetime.fromisoformat(text.replace("Z", "+00:00")))
