"""TaskContract / HandoffBundle 契约加载器。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from adapters.contracts.base import (
    ContractLoadError,
    load_flat_collection,
    load_json_schema,
    load_yaml,
    validate_instance,
)
from packages.domain.core import ID, Digest, Timestamp
from packages.domain.enums import AcceptanceCriterionType, ComparisonOperator, FailureCategory
from packages.domain.tasks import AcceptanceCriterion, HandoffBundle, RetryPolicy, TaskContract


def _load_criterion(item: dict[str, object]) -> AcceptanceCriterion:
    threshold = item.get("threshold")
    return AcceptanceCriterion(
        type=AcceptanceCriterionType(str(item["type"])),
        description=str(item.get("description", "")),
        target=_as_optional_str(
            item.get("artifact") or item.get("metric") or item.get("evaluator")
        ),
        artifact=_as_optional_str(item.get("artifact")),
        minimum_sources=_as_optional_int(item.get("minimum_sources")),
        minimum_retrieved_sources=_as_optional_int(item.get("minimum_retrieved_sources")),
        metric=_as_optional_str(item.get("metric")),
        operator=ComparisonOperator(str(item["operator"])) if item.get("operator") else None,
        threshold=Decimal(str(threshold)) if threshold is not None else None,
        evaluator=_as_optional_str(item.get("evaluator")),
    )


def _as_optional_str(value: object) -> str | None:
    return str(value) if value is not None else None


def _as_optional_int(value: object) -> int | None:
    return int(value) if isinstance(value, int) else None


def _load_budget(raw: object) -> dict[str, Decimal | None]:
    if not isinstance(raw, dict):
        return {}
    budget: dict[str, Decimal | None] = {}
    for key, value in raw.items():
        budget[str(key)] = Decimal(str(value)) if value is not None else None
    return budget


def _load_failure_policy(raw: object) -> dict[str, str | bool | int | list[str]]:
    if not isinstance(raw, dict):
        return {}
    policy: dict[str, str | bool | int | list[str]] = {}
    for key, value in raw.items():
        if isinstance(value, list):
            policy[str(key)] = [str(item) for item in value]
        elif isinstance(value, (str, bool, int)):
            policy[str(key)] = value
        else:
            raise ContractLoadError(f"unsupported failure_policy value for {key!r}: {value!r}")
    return policy


def load_task_contracts(relative_path: str) -> dict[str, TaskContract]:
    collection: dict[str, TaskContract] = {}
    for key, raw in load_flat_collection(
        relative_path, "task_contracts", "task-contract.schema.json"
    ).items():
        criteria = [_load_criterion(item) for item in raw.get("acceptance_criteria", [])]
        retry = raw.get("retry_policy")
        retry_policy = (
            RetryPolicy(
                max_attempts=retry["max_attempts"],
                retryable_categories=[
                    FailureCategory(item) for item in retry.get("retryable_categories", [])
                ],
                # 退避（PLAN-20260915-079）：省略即"立即重排"，既有契约不受影响。
                backoff_seconds=retry.get("backoff_seconds"),
                max_backoff_seconds=retry.get("max_backoff_seconds"),
            )
            if retry
            else None
        )
        collection[key] = TaskContract(
            id=raw["id"],
            version=raw["version"],
            purpose=raw["purpose"],
            required_capabilities=list(raw.get("required_capabilities", [])),
            input_schema=raw.get("input_schema"),
            output_schema=raw.get("output_schema"),
            required_artifacts=list(raw.get("required_artifacts", [])),
            acceptance_criteria=criteria,
            budget=_load_budget(raw.get("budget")),
            timeout_seconds=raw.get("timeout_seconds"),
            retry_policy=retry_policy,
            failure_policy=_load_failure_policy(raw.get("failure_policy")),
            idempotency_scope=raw.get("idempotency_scope", "task"),
        )
    return collection


def load_handoff_bundles(relative_path: str) -> HandoffBundle:
    """加载单条 HandoffBundle；顶层字段按 handoff-bundle.schema.json 校验后构造 domain 对象。"""
    body = load_yaml(relative_path)
    if not isinstance(body, dict):
        raise ContractLoadError(f"{relative_path} must be a mapping")
    validate_instance(load_json_schema("handoff-bundle.schema.json"), body, relative_path)
    created_at = body.get("created_at")
    return HandoffBundle(
        task_id=ID(body["task_id"]),
        producer=body["producer"],
        producer_agent_id=body.get("producer_agent_id"),
        producer_role_id=body.get("producer_role_id"),
        summary=body["summary"],
        digest=Digest.parse(body["digest"]),
        created_at=Timestamp(datetime.fromisoformat(created_at)) if created_at else Timestamp.now(),
        structured_output=dict(body.get("structured_output") or {}),
        artifact_refs=list(body.get("artifact_refs", [])),
        claim_refs=list(body.get("claim_refs", [])),
        evidence_refs=list(body.get("evidence_refs", [])),
        decision_refs=list(body.get("decision_refs", [])),
        open_questions=list(body.get("open_questions", [])),
        known_failures=list(body.get("known_failures", [])),
        recommended_next_actions=list(body.get("recommended_next_actions", [])),
    )
