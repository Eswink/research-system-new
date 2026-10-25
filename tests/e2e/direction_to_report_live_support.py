"""GOAL-20261024-096 EC-04 的**live 装配支持件**（自 `test_direction_to_report_live.py` 拆出）。

**为什么单列**：判据文件与装配函数都贴着规模门（单文件 450 行、单函数 50 行），而
「产品组合根 + 四段执行体缝 + 真实 runtime」是可独立读的一段装配。

**边界**：本模块**不含用例**；与生产路径的差别只有「装配方补执行体缝」这一处
（产品组合根今天不自己接这些缝，是既有如实登记的缺口）。
"""

from __future__ import annotations

import json
import os
from typing import Any

from services.api.runtime_support import OPENHANDS_RUNTIME

ENDPOINTS = "examples/config/llm_endpoints.yaml"
ENDPOINT = "main"
PROTOCOL = "direction_to_report_v1.yaml"
DIRECTION = "retrieval augmentation for scientific hypothesis generation"
EXPERIMENT_SCRIPT = "examples/experiments/exact_match_index_benchmark.py"
EXPERIMENT_IMAGE = "research-os-sandbox:m9-test"
SEARCH_TOOL_ID = "literature_search"
READ_TOOL_ID = "literature_read"


def wired_deps() -> Any:
    """产品组合根 + 四段**执行体**缝（检索 / 沙箱实验 / 报告汇编 / 被评对象）。

    `preflight_override is None` 是本判据的直接前提：它证的是**真**控制面的装配。
    """
    deps = _assembled()
    _attach_capabilities(deps)
    _attach_runtime(deps)
    _declare_direction(deps)
    return deps


def _assembled() -> Any:
    """产品组合根（生产 `assemble`），断言它没有带任何 preflight override。"""
    from dataclasses import replace

    from adapters.research_tools import EuropePmcProvider, NcbiEutilsProvider
    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.composition import assemble
    from services.api.report_support import report_task_runner
    from services.api.retrieval_context_support import retrieval_context_builder
    from services.api.review_material_support import review_material_builder
    from services.api.settings import ApiSettings
    from tests.e2e.live_run_support import LIVE_CREDENTIAL_REF, register_live_key

    deps = assemble(ApiSettings(db_path=f"data/goal096-live-{os.getpid()}.db"))
    assert deps.preflight_override is None, "live 判据不得带任何 preflight_override"
    assert deps.artifacts is not None and deps.runs is not None
    register_live_key(deps, os.environ.get(LIVE_CREDENTIAL_REF))
    deps.tool_providers = {
        "europe_pmc": EuropePmcProvider(deps.artifacts, spill_threshold_bytes=1),
        "ncbi_eutils": NcbiEutilsProvider(
            deps.artifacts, credentials=deps.credentials, spill_threshold_bytes=1
        ),
    }
    inner = deps.runs._deps
    deps.runs = RunOrchestrationService(
        replace(
            inner,
            experiment_task=_sandbox_runner(deps),
            report_task=report_task_runner(
                artifacts=deps.artifacts,
                ledger=deps.ledger,
                review_findings=deps.review_findings,
            ),
            retrieval_context=retrieval_context_builder(
                artifacts=deps.artifacts, ledger=deps.ledger
            ),
            review_material=review_material_builder({
                "workflow": inner.workflow,
                "artifacts": deps.artifacts,
            }),
        )
    )
    return deps


def _sandbox_runner(deps: Any) -> Any:
    """沙箱实验执行体：**臂来自计划产物**（`design_source="plan"`；GOAL-080 同款）。"""
    from services.api.experiment_support import (
        DESIGN_SOURCE_PLAN,
        docker_experiment_assembly,
        sandbox_experiment_runner,
    )

    return sandbox_experiment_runner(
        docker_experiment_assembly(
            artifacts=deps.artifacts,
            ledger=deps.ledger,
            policy=deps.policy_evaluator,
            script=EXPERIMENT_SCRIPT,
            image=EXPERIMENT_IMAGE,
            experiment_store=deps.experiment_store,
            design_source=DESIGN_SOURCE_PLAN,
        )
    )


def _attach_capabilities(deps: Any) -> None:
    """运行链两步：检索词来自**上游问题产物**，收窄在检索相（GOAL-089 同款）。"""
    from dataclasses import replace

    from packages.application.run_orchestration.phase_capabilities import (
        CapabilityDeps,
        RunChainCall,
    )
    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.catalog_merge import merged_catalog_snapshot

    spec = merged_catalog_snapshot(deps).tool_providers["europe_pmc"]
    provider = deps.tool_providers["europe_pmc"]
    deps.runs = RunOrchestrationService(
        replace(
            deps.runs._deps,
            capabilities=CapabilityDeps(
                calls=(
                    RunChainCall(
                        provider_id="europe_pmc",
                        tool_id=SEARCH_TOOL_ID,
                        capability="literature.search",
                        arguments_from_input=("research_question.query",),
                        fixed_arguments={"retmax": 3},
                        phase_id="retrieval",
                    ),
                    RunChainCall(
                        provider_id="europe_pmc",
                        tool_id=READ_TOOL_ID,
                        capability="literature.read",
                        ids_from_previous="ids",
                        phase_id="retrieval",
                    ),
                ),
                providers={"europe_pmc": provider},
                provider_specs={"europe_pmc": spec},
                policy=deps.policy_evaluator,
                artifacts=deps.artifacts,
                ledger=deps.ledger,
            ),
        )
    )


def _attach_runtime(deps: Any) -> None:
    """真实 runtime（OpenHands）+ 评审格四条绑定的会话工具实现。

    `workspace_allow_host_shell=True` 只影响这一次受判 run 的装配（AGENTS §9 的默认
    deny 未改）：本协议有真实会话格，不显式打开就建不起会话（既有 live 判据同款）。
    """
    from dataclasses import replace

    from adapters.openhands.session_tools import build_session_tools
    from packages.application.model_relay.endpoint_policy import EndpointUrlPolicy
    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.assembly import policy_bindings
    from services.api.runtime_support import build_agent_runtime, resolve_runtime_selection
    from services.api.settings import ApiSettings
    from tests.e2e.live_run_support import register_inert_tools

    bindings = {
        "m12_artifact": "artifact.read",
        "openhands_workspace": "workspace.read",
        "ncbi_eutils": "literature.search",
        "europe_pmc": "literature.read",
    }
    invokers = {
        name: (lambda arguments, conversation=None, _n=name: f"{_n} ok")
        for name in bindings.values()
    }
    settings = ApiSettings(agent_runtime=OPENHANDS_RUNTIME, workspace_allow_host_shell=True)
    policy = EndpointUrlPolicy(allow_localhost=False)
    runtime = build_agent_runtime(
        settings,
        credentials=deps.credentials,
        policy_evaluator=policy_bindings().get("policy_evaluator"),
        budget_ledger=deps.budget,
        register_session_tools=build_session_tools(invokers),
    )
    register_inert_tools(("m12_artifact", "openhands_workspace"))
    deps.runs = RunOrchestrationService(replace(deps.runs._deps, runtime=runtime))
    deps.runtime_selection = resolve_runtime_selection(settings)
    deps.endpoint_url_policy = policy


def _declare_direction(deps: Any) -> None:
    """方向：产品读面（`ProjectStore`）上声明一句话（与 PUT /projects/{id}/direction 同路）。"""
    from packages.domain.core import Timestamp
    from packages.domain.projects import ProjectDefinition, ProjectStatus
    from services.api.catalog import load_project_name

    assert deps.project_store is not None
    deps.project_store.save_project(
        ProjectDefinition(
            id="example-project",
            name=load_project_name(),
            status=ProjectStatus.ACTIVE,
            created_at=Timestamp.now(),
            updated_at=Timestamp.now(),
            direction=DIRECTION,
        )
    )


def question_block(text: str) -> dict[str, Any]:
    """问题正文里带 `research_question` 键的那个 JSON 对象（判据自己找，不用产品代码）。"""
    for candidate in (text.strip(), _fenced(text)):
        if candidate is None:
            continue
        try:
            parsed = json.loads(candidate)
        except ValueError:
            continue
        if isinstance(parsed, dict) and isinstance(parsed.get("research_question"), dict):
            block: dict[str, Any] = parsed["research_question"]
            return block
    raise AssertionError(f"the question artifact carries no research_question block: {text[:400]}")


def question_text(store: Any, artifact_id: str) -> str:
    """问题的正文（交付物信封的 `content`；直形态则整份 JSON）。"""
    raw = store.get(artifact_id).decode("utf-8")
    payload = json.loads(raw)
    content = payload.get("content")
    return content if isinstance(content, str) else raw


def _fenced(text: str) -> str | None:
    if "```" not in text:
        return None
    parts = text.split("```")
    if len(parts) < 3:
        return None
    body = parts[1]
    newline = body.find("\n")
    return body[newline + 1 :] if newline != -1 else body


def strings_in(payload: Any) -> list[str]:
    """载荷里的**全部字符串值**（递归；判据按印迹取证，不绑定属性名）。"""
    if isinstance(payload, str):
        return [payload]
    if isinstance(payload, dict):
        return [item for value in payload.values() for item in strings_in(value)]
    if isinstance(payload, list):
        return [entry for value in payload for entry in strings_in(value)]
    return []


def search_terms(deps: Any, *, tool_args_classification: str) -> list[str]:
    """检索调用参数制品里的**全部字符串值**（制品面枚举，不看 run 是否成功）。"""
    ids = sorted(
        item.id
        for item in deps.artifacts.list_refs()
        if item.classification == tool_args_classification
        and item.id.endswith(f":{SEARCH_TOOL_ID}")
    )
    return [
        value
        for artifact_id in ids
        for value in strings_in(json.loads(deps.artifacts.get(artifact_id).decode("utf-8")))
    ]


def read_identifiers(evidence: list[dict[str, Any]], pattern: Any) -> list[str]:
    """读取步 `source_ref` 末段的真实标识（**只从末段取**：task id 本身是十六进制）。"""
    steps = [item for item in evidence if READ_TOOL_ID in item["source_ref"]]
    return sorted({
        part
        for item in steps
        for part in item["source_ref"].rsplit(":", 1)[-1].split("+")
        if pattern.fullmatch(part)
    })
