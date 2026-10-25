"""GOAL-20261024-096 的**离线装配支持件**（自 `test_direction_to_report_arc_offline.py` 拆出）。

**为什么单列**：那个判据文件贴着 450 行硬上限（规模门），而「mock 中转站 + 参数化离线
Europe PMC + 四段执行体缝」是**可独立读**的一段装配，与用例分开（与
`literature_chain_support` / `retrieval_context_support` 同一手法）。

**边界**：本模块**不含用例**；它给的装配与生产路径的差别只有「传输层换 mock」这一处
（真解析、真编排、真容器实验）。

**两个变体**：`VARIANT_A` / `VARIANT_B` 让「改上游产出 ⇒ 下游材料变」的两向判据在
两个不同的记录集上各跑一次。
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any

import httpx

from adapters.research_tools import EuropePmcConfig, EuropePmcProvider
from tests.e2e.literature_chain_support import EUROPE_PMC_ID, europepmc_record
from tests.e2e.live_run_support import openhands_deps

PROTOCOL = "direction_to_report_v1.yaml"
DIRECTION = "retrieval augmentation for scientific hypothesis generation"
EXPERIMENT_SCRIPT = "examples/experiments/exact_match_index_benchmark.py"
EXPERIMENT_IMAGE = "research-os-sandbox:m9-test"
OUTPUT_NAMES = (
    "research_question",
    "retrieval_report",
    "research_plan",
    "review_decision",
    "research_report.md",
)

VARIANT_A = ("retrieval augmented planning", "39284801", "ENCORE")
VARIANT_B = ("systematic review automation", "40601758", "FAIR biomedical")

RECORD_POOL: dict[str, dict[str, str]] = {
    "39284801": {
        "pmid": "39284801",
        "doi": "10.1038/s41467-024-52446-8",
        "title": (
            "ENCORE: a practical implementation to improve reproducibility and "
            "transparency of computational research."
        ),
        "journal": "Nat Commun",
        "year": "2024",
        "author_string": "Hoffmann C, Djerroud S, et al.",
    },
    "40601758": {
        "pmid": "40601758",
        "doi": "10.1371/journal.pcbi.1013215",
        "title": (
            "Fundamentals of FAIR biomedical data analyses in the cloud using custom pipelines."
        ),
        "journal": "PLoS Comput Biol",
        "year": "2025",
        "author_string": "Kanitz A, Gürsoy G, et al.",
    },
}


def question_reply(query: str) -> str:
    """问题格的受控回复（形状照合约 `research_question_proposal` 的规定）。"""
    block = (
        '{"research_question": {"query": "'
        + query
        + '", "rationale": "the direction implies this"}}'
    )
    return (
        "The question this run pursues follows from the project direction."
        + "\n\n```json\n"
        + block
        + "\n```\n"
    )


def plan_reply(pmid: str) -> str:
    """计划格的受控回复（设计块在前：设计读取器只看第一个围栏块）。"""
    design = '{"experiment_design": {"arms": {"control": {}, "treatment": {"n_items": 120}}}}'
    plan = (
        '{"research_plan": {"question": "does retrieval augmentation improve planning '
        "(retrieved PMID " + pmid + ')", '
        '"hypothesis": "retrieval-grounded plans execute better"}}'
    )
    return (
        "The study stands on the retrieved record "
        + pmid
        + ": it motivates the comparison below."
        + "\n\n```json\n"
        + design
        + "\n```\n\n```json\n"
        + plan
        + "\n```\n"
    )


def review_reply() -> str:
    """评审格的受控回复（判词 + 分数）。"""
    block = (
        '{"review_decision": {"verdict": "ACCEPT", "score": 0.9, '
        '"weakest_link": "the rationale is thin"}}'
    )
    return (
        "The plan is grounded in the retrieved material and the design is decidable."
        + "\n\n```json\n"
        + block
        + "\n```\n"
    )


class RelayHandler(BaseHTTPRequestHandler):
    """契约感知的 mock 中转站：按提示词里的**合约指纹**回各自形状的正文。"""

    requests: list[dict[str, Any]] = []
    query_of_question: str = VARIANT_A[0]

    def do_GET(self) -> None:  # noqa: N802
        payload = json.dumps({"data": [{"id": "relay-model", "object": "model"}]}).encode()
        self._respond(payload)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
        RelayHandler.requests.append(body)
        prompt = json.dumps(body.get("messages", []), ensure_ascii=False)
        content = _content_for(prompt)
        response = {
            "id": "chatcmpl-mock-1",
            "object": "chat.completion",
            "created": 1755000000,
            "model": body.get("model", "relay-model"),
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15},
        }
        self._respond(json.dumps(response).encode())

    def _respond(self, payload: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return


def _content_for(prompt: str) -> str:
    """按提示词里的合约指纹分派回复（四个会话格各自的形状）。"""
    if "turn the operator's stated research direction" in prompt:
        return question_reply(RelayHandler.query_of_question)
    if "GOAL-20261019-089 EC-01 / GOAL-20261020-090" in prompt:
        return "Retrieved the material for the question above."
    if "write the research plan for this study" in prompt:
        return plan_reply(pmid_of_prompt(prompt))
    if "独立复核" in prompt:
        return review_reply()
    return "Done."


def pmid_of_prompt(prompt: str) -> str:
    """计划回复里引用的 PMID（来自本 run 实际取回的那条记录）。"""
    for pmid in (VARIANT_A[1], VARIANT_B[1]):
        if pmid in prompt:
            return pmid
    return VARIANT_A[1]


class RelayFixture:
    """本机 mock 端点（threading HTTP 服务器；不出公网）。"""

    def __init__(self) -> None:
        self._server = HTTPServer(("127.0.0.1", 0), RelayHandler)
        self._thread = Thread(target=self._server.serve_forever, daemon=True)

    def __enter__(self) -> str:
        RelayHandler.requests = []
        self._thread.start()
        return f"http://127.0.0.1:{self._server.server_port}/v1"

    def __exit__(self, *args: Any) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


class OfflineEuropePmc:
    """参数化的离线 Europe PMC 传输（两个变体回**不同的记录集**）。"""

    def __init__(self, pmids: tuple[str, ...]) -> None:
        self.requests: list[str] = []
        self._records = tuple(RECORD_POOL[pmid] for pmid in pmids)

    def handler(self, request: httpx.Request) -> httpx.Response:
        term = request.url.params.get("query", "")
        self.requests.append(term)
        if term.startswith("EXT_ID:"):
            pmid = term.split(":", 1)[1]
            matched = tuple(record for record in self._records if record["pmid"] == pmid)
            payload: dict[str, object] = {
                "version": "6.9",
                "hitCount": len(matched),
                "resultList": {"result": [europepmc_record(record) for record in matched]},
            }
        else:
            payload = {
                "version": "6.9",
                "hitCount": len(self._records),
                "resultList": {"result": [europepmc_record(record) for record in self._records]},
            }
        return httpx.Response(200, json=payload)


def deps_for(relay_url: str, pmids: tuple[str, ...], query: str) -> Any:
    """产品组合根 + 四段执行体缝 + 上下文/被评对象装配 + spec 记录器（只观察）。"""
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.report_support import report_task_runner
    from services.api.retrieval_context_support import retrieval_context_builder
    from services.api.review_material_support import review_material_builder
    from tests.e2e.retrieval_context_support import install_spec_recorder

    deps = openhands_deps(relay_url, map_tools=False)
    offline = OfflineEuropePmc(pmids)
    provider = EuropePmcProvider(
        deps.artifacts,
        config=EuropePmcConfig(min_request_interval_seconds=0.0),
        http_client=httpx.Client(transport=httpx.MockTransport(offline.handler)),
        spill_threshold_bytes=1,
    )
    deps.tool_providers = {EUROPE_PMC_ID: provider}
    inner = deps.runs._deps
    deps.runs = RunOrchestrationService(
        replace(
            inner,
            capabilities=capability_step(deps, provider),
            experiment_task=sandbox_runner(deps),
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
    attach_session_tools(deps)
    install_spec_recorder(deps)
    RelayHandler.query_of_question = query
    return deps, offline


def capability_step(deps: Any, provider: Any) -> Any:
    """运行链两步：检索词来自**上游问题产物**，读取步的标识来自检索结果（GOAL-089 同款）。"""
    from packages.application.run_orchestration.phase_capabilities import (
        CapabilityDeps,
        RunChainCall,
    )
    from services.api.catalog_merge import merged_catalog_snapshot

    spec = merged_catalog_snapshot(deps).tool_providers[EUROPE_PMC_ID]
    return CapabilityDeps(
        calls=(
            RunChainCall(
                provider_id=EUROPE_PMC_ID,
                tool_id="literature_search",
                capability="literature.search",
                arguments_from_input=("research_question.query",),
                fixed_arguments={"retmax": 2},
                phase_id="retrieval",
            ),
            RunChainCall(
                provider_id=EUROPE_PMC_ID,
                tool_id="literature_read",
                capability="literature.read",
                ids_from_previous="ids",
                phase_id="retrieval",
            ),
        ),
        providers={EUROPE_PMC_ID: provider},
        provider_specs={EUROPE_PMC_ID: spec},
        policy=deps.policy_evaluator,
        artifacts=deps.artifacts,
        ledger=deps.ledger,
    )


def sandbox_runner(deps: Any) -> Any:
    """沙箱实验执行体：**臂来自计划产物**（`design_source="plan"`；GOAL-080 同款）。"""
    from services.api.assembly import policy_bindings
    from services.api.experiment_support import (
        DESIGN_SOURCE_PLAN,
        docker_experiment_assembly,
        sandbox_experiment_runner,
    )

    policy_evaluator = policy_bindings().get("policy_evaluator")
    assert policy_evaluator is not None
    return sandbox_experiment_runner(
        docker_experiment_assembly(
            artifacts=deps.artifacts,
            ledger=deps.ledger,
            policy=policy_evaluator,
            script=EXPERIMENT_SCRIPT,
            image=EXPERIMENT_IMAGE,
            experiment_store=deps.experiment_store,
            design_source=DESIGN_SOURCE_PLAN,
        )
    )


REVIEW_BINDINGS = {
    "m12_artifact": "artifact.read",
    "openhands_workspace": "workspace.read",
    "ncbi_eutils": "literature.search",
    "europe_pmc": "literature.read",
}


def attach_session_tools(deps: Any) -> None:
    """把评审格四条绑定的**会话工具实现**接进真实 runtime（arc 离线同款）。"""
    from dataclasses import replace

    from adapters.openhands.session_tools import build_session_tools
    from packages.application.model_relay.endpoint_policy import EndpointUrlPolicy
    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.assembly import policy_bindings
    from services.api.runtime_support import build_agent_runtime, resolve_runtime_selection
    from services.api.settings import ApiSettings

    invokers = {
        tool_name: (lambda arguments, conversation=None, _n=tool_name: f"{_n} ok")
        for tool_name in REVIEW_BINDINGS.values()
    }
    settings = ApiSettings(
        agent_runtime="openhands",
        allow_localhost_endpoints=True,
        workspace_allow_host_shell=True,
    )
    policy = EndpointUrlPolicy(allow_localhost=True)
    runtime = build_agent_runtime(
        settings,
        credentials=deps.credentials,
        policy_evaluator=policy_bindings().get("policy_evaluator"),
        budget_ledger=deps.budget,
        register_session_tools=build_session_tools(invokers),
    )
    deps.runs = RunOrchestrationService(replace(deps.runs._deps, runtime=runtime))
    deps.runtime_selection = resolve_runtime_selection(settings)
    deps.endpoint_url_policy = policy


__all__ = [
    "DIRECTION",
    "EXPERIMENT_IMAGE",
    "EXPERIMENT_SCRIPT",
    "OUTPUT_NAMES",
    "PROTOCOL",
    "RECORD_POOL",
    "REVIEW_BINDINGS",
    "VARIANT_A",
    "VARIANT_B",
    "OfflineEuropePmc",
    "RelayFixture",
    "attach_session_tools",
    "capability_step",
    "deps_for",
    "plan_reply",
    "pmid_of_prompt",
    "question_reply",
    "review_reply",
    "sandbox_runner",
]
