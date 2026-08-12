"""CompiledRunPlan → schema 兼容序列化 payload 的测试辅助。"""

from __future__ import annotations

from packages.domain.protocols import CompiledRunPlan


def _phases_payload(plan: CompiledRunPlan) -> list[dict[str, object]]:
    return [
        {
            "id": phase.id,
            "strategy": phase.strategy.value,
            "depends_on": list(phase.depends_on),
            "task_contract_refs": list(phase.task_contract_refs),
            "timeout_seconds": phase.timeout_seconds,
        }
        for phase in plan.phases
    ]


def _eligibility_payload(plan: CompiledRunPlan) -> list[dict[str, object]]:
    return [
        {
            "agent_id": item.agent_id,
            "role_id": item.role_id,
            "model_id": item.model_id,
            "eligible": item.eligible,
            "hard_capabilities": [c.value for c in item.hard_capabilities],
            "missing_capabilities": [c.value for c in item.missing_capabilities],
        }
        for item in plan.model_eligibility
    ]


def _requirements_payload(plan: CompiledRunPlan) -> dict[str, object]:
    return {
        "tool_requirements": [
            {
                "phase_id": item.phase_id,
                "capability": item.capability,
                "provider_ids": list(item.provider_ids),
            }
            for item in plan.tool_requirements
        ],
        "workspace_requirements": [
            {
                "phase_id": item.phase_id,
                "workspace_backend": item.workspace_backend,
                "trust_profile": item.trust_profile,
                "compute_profile": item.compute_profile,
            }
            for item in plan.workspace_requirements
        ],
        "budget_reservations": [
            {
                "id": item.id,
                "scope": item.scope,
                "resource_type": item.resource_type.value,
                "quantity": item.quantity,
                "unit": item.unit,
            }
            for item in plan.budget_reservations
        ],
    }


def _gates_payload(plan: CompiledRunPlan) -> dict[str, object]:
    return {
        "gates": [{"phase_id": item.phase_id, "gate": item.gate.value} for item in plan.gates],
        "stop_conditions": [
            {
                "phase_id": item.phase_id,
                "max_iterations": item.max_iterations,
                "budget_exhausted": item.budget_exhausted,
            }
            for item in plan.stop_conditions
        ],
    }


def compiled_plan_payload(plan: CompiledRunPlan) -> dict[str, object]:
    """CompiledRunPlan → compiled-run-plan.schema.json 兼容的 payload。"""
    return {
        "protocol_id": plan.protocol_id,
        "protocol_version": plan.protocol_version.text,
        "protocol_digest": str(plan.protocol_digest),
        "phase_dag": plan.phase_dag,
        "phases": _phases_payload(plan),
        "task_contract_refs": list(plan.task_contract_refs),
        "role_pools": plan.role_pools,
        "agent_candidates": plan.agent_candidates,
        "resolved_models": plan.resolved_models,
        "agent_workspace_policies": dict(plan.agent_workspace_policies),
        "model_eligibility": _eligibility_payload(plan),
        **(_requirements_payload(plan)),
        "tool_pack_digests": dict(plan.tool_pack_digests),
        **_gates_payload(plan),
    }
