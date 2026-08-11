"""TaskContract 契约加载器。"""

from __future__ import annotations

from adapters.contracts.base import load_flat_collection
from packages.domain.enums import AcceptanceCriterionType, FailureCategory
from packages.domain.tasks import AcceptanceCriterion, RetryPolicy, TaskContract


def load_task_contracts(relative_path: str) -> dict[str, TaskContract]:
    collection: dict[str, TaskContract] = {}
    for key, raw in load_flat_collection(
        relative_path, "task_contracts", "task-contract.schema.json"
    ).items():
        criteria = [
            AcceptanceCriterion(
                type=AcceptanceCriterionType(item["type"]),
                description=item.get("description", ""),
                target=item.get("artifact") or item.get("metric") or item.get("evaluator"),
            )
            for item in raw.get("acceptance_criteria", [])
        ]
        retry = raw.get("retry_policy")
        retry_policy = (
            RetryPolicy(
                max_attempts=retry["max_attempts"],
                retryable_categories=[
                    FailureCategory(item) for item in retry.get("retryable_categories", [])
                ],
            )
            if retry
            else None
        )
        collection[key] = TaskContract(
            id=raw["id"],
            version=raw["version"],
            purpose=raw["purpose"],
            required_capabilities=list(raw.get("required_capabilities", [])),
            output_schema=raw.get("output_schema"),
            required_artifacts=list(raw.get("required_artifacts", [])),
            acceptance_criteria=criteria,
            timeout_seconds=raw.get("timeout_seconds"),
            retry_policy=retry_policy,
            idempotency_scope=raw.get("idempotency_scope", "task"),
        )
    return collection
