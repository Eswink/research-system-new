"""GOAL-20261019-089 EC-01 的**运行期**判据：方向 → 问题 → 检索在一次 run 里成链。

**判什么**（一次真实编排，受控执行体）：

1. 方向进会话：`question` 格拿到的提示词里**有** `PROJECT DIRECTION` 段与那句话
   （从受控执行体处取证：它收到的 spec 的 `direction_prompt`）；
2. 问题的产出**成为**检索词：`retrieval` 格的 run-chain 检索**真的**用了上游产物里的
   `query`（从 provider 收到的请求参数取证）；
3. 两格都落库：`research_question` 与 `retrieval_report` 是**不同的任务**产出的；
   检索证据带 `RETRIEVED`（性质维），run 收敛 `SUCCEEDED`。

**为什么这不算重复判据**：`test_run_chain_reads_cross_phase_material.py` 判的是
「材料怎么进参数」（单元 + provider 传输层）；本文件判的是「**编排**真的把两格按
声明串起来了」（phase 分组、任务身份解析、跨相证据登记、验收门）。两者任一绿另一红
都说明链没通。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, cast

import httpx
from fastapi.testclient import TestClient

from adapters.research_tools import NcbiEutilsConfig, NcbiEutilsProvider
from packages.application.run_orchestration.phase_capabilities import (
    CapabilityDeps,
    RunChainCall,
)
from services.api.app import create_app
from tests.api.run_fixtures import make_run_ready_deps
from tests.e2e.scenario import StructuredOutputAgentRuntime

_PROTOCOL = "direction_to_question_v1.yaml"
_DIRECTION = "how retrieval augments scientific planning"
_QUESTION_CONTRACT = "research_question_proposal"
_RETRIEVAL_CONTRACT = "research_question_retrieval"
_MODEL_QUERY = "retrieval augmented scientific planning"
_SPEC_IDS = ["39000101", "39000102"]
_SEARCH_JSON = {"esearchresult": {"count": str(len(_SPEC_IDS)), "idlist": list(_SPEC_IDS)}}
_EFETCH_XML = (
    b'<?xml version="1.0" encoding="UTF-8"?><PubmedArticleSet><PubmedArticle>'
    b"<MedlineCitation><PMID>39000101</PMID><Article><ArticleTitle>t</ArticleTitle>"
    b"<Journal><Title>J</Title></Journal></Article></MedlineCitation>"
    b"</PubmedArticle></PubmedArticleSet>"
)


class _RecordingRuntime(StructuredOutputAgentRuntime):
    """受控执行体：按合约给交付物，并**记下**每格拿到的方向那一段。"""

    def __init__(self) -> None:
        super().__init__(
            outputs_by_contract={
                _QUESTION_CONTRACT: {
                    "research_question": {
                        "query": _MODEL_QUERY,
                        "rationale": "the direction implies this question",
                    }
                },
                _RETRIEVAL_CONTRACT: {"retrieval_report": {"summary": "retrieved"}},
            }
        )
        self.directions: dict[str, str | None] = {}

    def create_session(self, spec: Any) -> Any:
        handle = super().create_session(spec)
        self.directions[spec.task_contract.id] = spec.direction_prompt
        return handle


def _deps(
    runtime: _RecordingRuntime, queries: list[str], *, direction: str | None = _DIRECTION
) -> Any:
    deps = make_run_ready_deps()
    assert deps.runs is not None
    inner = deps.runs._deps
    ledger = inner.ledger
    artifacts = inner.artifacts
    assert ledger is not None and artifacts is not None
    provider = _provider(artifacts, queries)
    context = deps.preflight_override
    assert context is not None
    spec = context.catalog.tool_providers["ncbi_eutils"]
    deps.tool_providers = {"ncbi_eutils": cast("Any", provider)}
    from packages.application.run_orchestration.service import RunOrchestrationService

    deps.runs = RunOrchestrationService(
        replace(
            inner,
            runtime=runtime,
            # 方向解析器由组合根注入（本判据用受控值替代 `project_direction_builder`）。
            project_direction=lambda project_id: direction,
            capabilities=_capabilities(provider, spec, context, artifacts, ledger),
        )
    )
    return deps


def _provider(artifacts: Any, queries: list[str]) -> Any:
    """真 provider + MockTransport（记下真正发出的 query；不出网）。"""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("esearch.fcgi"):
            queries.append(request.url.params.get("term", ""))
            return httpx.Response(200, json=_SEARCH_JSON)
        return httpx.Response(200, content=_EFETCH_XML)

    return NcbiEutilsProvider(
        artifacts,
        config=NcbiEutilsConfig(min_request_interval_seconds=0.0),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        spill_threshold_bytes=1,
    )


def _capabilities(provider: Any, spec: Any, context: Any, artifacts: Any, ledger: Any) -> Any:
    """运行链两步：检索词来自**上游问题产物**，读取步的标识来自检索结果。"""
    return CapabilityDeps(
        calls=(
            RunChainCall(
                provider_id="ncbi_eutils",
                tool_id="literature_search",
                capability="literature.search",
                arguments_from_input=("research_question.query",),
                fixed_arguments={"retmax": 2},
                phase_id="retrieval",
            ),
            RunChainCall(
                provider_id="ncbi_eutils",
                tool_id="literature_read",
                capability="literature.read",
                ids_from_previous="ids",
                phase_id="retrieval",
            ),
        ),
        providers={"ncbi_eutils": cast("Any", provider)},
        provider_specs={"ncbi_eutils": spec},
        policy=context.policy_evaluator,
        artifacts=artifacts,
        ledger=ledger,
    )


def test_the_direction_reaches_the_question_phase_and_its_query_drives_the_search() -> None:
    runtime = _RecordingRuntime()
    queries: list[str] = []
    deps = _deps(runtime, queries)

    with TestClient(create_app(deps)) as client:
        created = client.post(
            "/projects/example-project/runs",
            json={"protocol_path": _PROTOCOL},
            headers={"Idempotency-Key": "goal089-ec01-run"},
        )
        assert created.status_code == 200, created.text
        run_id = str(created.json()["id"])
        run = client.get(f"/runs/{run_id}").json()
        evidence = client.get(f"/runs/{run_id}/evidence").json()
        artifacts = client.get(f"/runs/{run_id}/artifacts").json()

    # (1) 方向进了**立题**格的提示词（逐字），而检索格不需要它。
    question_prompt = runtime.directions.get(_QUESTION_CONTRACT)
    assert question_prompt is not None, runtime.directions
    assert _DIRECTION in question_prompt, question_prompt
    assert "PROJECT DIRECTION" in question_prompt

    # (2) 检索词**就是**模型在问题里写下的那句话。
    assert queries == [_MODEL_QUERY], queries

    # (3) 两件产物分属两个任务；run 成功；检索证据带 RETRIEVED。
    ids = {item["id"] for item in artifacts}
    question_ids = [item for item in ids if item.endswith(":research_question")]
    report_ids = [item for item in ids if item.endswith(":retrieval_report")]
    assert len(question_ids) == 1, ids
    assert len(report_ids) == 1, ids
    assert question_ids[0].split(":")[0] != report_ids[0].split(":")[0], ids
    assert run["state"] == "SUCCEEDED", (run["state"], run.get("message"))
    labels = {item["source_trust_label"] for item in evidence if item["tool_refs"]}
    assert "RETRIEVED" in labels, labels


def test_without_a_direction_the_question_phase_gets_no_direction_section() -> None:
    """**零回归**：没有方向 ⇒ 提示词里**没有**那一段（不是空标题）。"""
    runtime = _RecordingRuntime()
    deps = _deps(runtime, [], direction=None)

    with TestClient(create_app(deps)) as client:
        created = client.post(
            "/projects/example-project/runs",
            json={"protocol_path": _PROTOCOL},
            headers={"Idempotency-Key": "goal089-ec01-run-nodirection"},
        )
        assert created.status_code == 200, created.text

    assert runtime.directions.get(_QUESTION_CONTRACT) is None, runtime.directions
