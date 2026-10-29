"""GOAL-20261028-099 EC-04 的**离线装配支持件**（八相手稿链走产品入口）。

**为什么单列**：判据文件贴着 450 行硬上限（规模门），而「mock 中转站 + 离线 Europe PMC +
四段执行体缝 + spec 记录器」是可独立读的一段装配 —— 与
`direction_to_report_support` 同一手法。本模块**不含用例**。

**与被复用件的分工**：`question_reply` / `RelayFixture` / `OfflineEuropePmc` /
`attach_session_tools` / `capability_step` / `sandbox_runner` **逐字复用**
`tests.e2e.direction_to_report_support`（那套已被 GOAL-096 的判据验证）。本模块只补三件
本协议**多出来**的东西：

1. 两个新会话格的受控回复（`novelty` 与 `manuscript`）——本协议比 v1 多这两相；
2. 报告缝开 `manuscript=True`（产品装配面的那个开关）；
3. `deps_for_manuscript()`：把上面两件接进产品组合根。

**边界**：与生产路径的差别只有「传输层换 mock」这一处（真解析、真编排、真容器实验）。
`manuscript` 相的回复里**写死** `[1]`（本 run 只取 retmax=2 且离线池只有两条记录 ⇒
去重后 ≤2 条 ⇒ `[1]` 一定在范围内）；这是**受控夹具**，不是产品推导。
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any

import httpx

from adapters.research_tools import EuropePmcConfig, EuropePmcProvider
from tests.e2e.direction_to_report_support import (
    RECORD_POOL,
    capability_step,
    sandbox_runner,
)
from tests.e2e.literature_chain_support import EUROPE_PMC_ID

PROTOCOL = "direction_to_manuscript_v1.yaml"
DIRECTION = "retrieval augmentation for scientific hypothesis generation"
EXPERIMENT_SCRIPT = "examples/experiments/exact_match_index_benchmark.py"
EXPERIMENT_IMAGE = "research-os-sandbox:m9-test"
#: 本协议声明的**十个**相（判据按它核相集与产物）。
PHASES: tuple[str, ...] = (
    "question",
    "retrieval",
    "novelty",
    "plan",
    "experiment",
    "review",
    "manuscript",
    # GOAL-20261029-100 EC-02：投稿决策相（`scientific_editor` 被激活的那一格）。
    "editorial",
    # GOAL-20261029-100 EC-03：逐条应答相（评审点 → 作者回应）。
    "revision",
    "report",
)
#: 本 run 应当落库的会话产物名 + 两个汇编产物。
OUTPUT_NAMES: tuple[str, ...] = (
    "research_question",
    "retrieval_report",
    "novelty_claim",
    "research_plan",
    "review_decision",
    "manuscript_narrative",
    # GOAL-20261029-100 EC-02：编辑决定（四值闭集之一 + 理由 + 逐条要求的改动）。
    "editorial_decision",
    # GOAL-20261029-100 EC-03：作者逐条应答（汇编器据此产出 `response_letter.md`）。
    "author_responses",
    "research_report.md",
    "manuscript.md",
)
VARIANT_A = ("retrieval augmented planning", "39284801", "ENCORE")
VARIANT_B = ("systematic review automation", "40601758", "FAIR biomedical")

#: 手稿正文（**无任何数字**，只有 `[1]` 引用标记 —— 与合约的两条硬规则一致）。
MANUSCRIPT_SECTIONS: dict[str, str] = {
    "title": "Retrieval Grounding For Controlled Planning Studies",
    "abstract": "We ask whether grounding a research plan in the retrieved literature "
    "changes the design a controlled experiment can execute, and we report the measured "
    "comparison in the assembled table rather than in this prose.",
    "introduction": "Planning assistants propose studies that the literature may already "
    "settle; we ask what changes when the material is retrieved before the plan is written.",
    "related_work": "The closest retrieved work builds reproducibility tooling for "
    "computational research and documents the cost of custom pipelines [1]; it leaves open "
    "which planning choices actually move a measured outcome, which is what this study "
    "varies.",
    "methods": "Two arms run the same shipped benchmark script. The treatment arm sets a "
    "larger item count than the control arm, so the comparison isolates the workload under "
    "a fixed procedure.",
    "results": "The treatment arm's comparison count differs from the control arm's; the "
    "per-arm readings and their sources are published in the data table below, by name, so "
    "each value can be checked against this run rather than against this sentence [1].",
    "discussion": "The measured difference is a workload effect and nothing more: the study "
    "varies the item count alone, one script cannot speak for another, and the run carries "
    "a single retrieved record.",
    "conclusion": "Grounded planning yields an executable design here; whether it yields a "
    "better one is not something this run measured, and we do not claim it.",
}


def response_reply(prompt: str) -> str:
    """应答格的受控回复：**逐条**回应提示词里列出的每一个 `P<n>`。

    为什么从提示词里**读编号**（而不是写死 `P1`/`P2`）：本夹具的意义是证明「点表真的
    到了模型眼前」—— 写死编号会让它在点表缺失时**依然通过**（那是假绿）。这里按提示词
    实际给出的 id 生成应答，点表为空就**一条也不回**（那会让汇编器点名漏答 ⇒ 判据红，
    这正是我们要的行为）。
    """
    # `prompt` 是 **JSON 序列化后**的 messages（本文件上游 `json.dumps` 过 ⇒ 换行是
    # 字面 `\n` 两字符），所以行首锚不能用 `^`+MULTILINE —— 直接按 `- P<n> (` 取。
    ids = re.findall(r"- (P\d+) \(([a-z_]+)\): ", prompt)
    block = json.dumps(
        {
            "author_responses": [
                {
                    "point_id": point_id,
                    "response": f"We accept {point_id}: the review is right about this one.",
                    "action_taken": f"revised the section named in {point_id}",
                }
                for point_id, _severity in ids
            ]
        },
        ensure_ascii=False,
    )
    return "Here is our point by point response.\n\n```json\n" + block + "\n```\n"


def editorial_reply() -> str:
    """编辑决定格的受控回复（形状照合约 `editorial_decision` 的规定）。

    取 `minor_revision` 而不是 `accept`：**带改动的决定**才会经过
    「`required_changes` 必须非空」那条判据 —— 用 `accept` 作夹具会让那个分支在
    产品入口上从未被走到（判据侧的单测会绿，产品路径**没有**证据）。
    """
    block = json.dumps(
        {
            "editorial_decision": {
                "decision": "minor_revision",
                "rationale": "the review asks which planning choice moved the measured "
                "outcome, and the Related Work section does not yet say so in its own words",
                "required_changes": [
                    "name the planning choice that differs between the two arms in Related Work",
                ],
            }
        },
        ensure_ascii=False,
    )
    return (
        "The manuscript needs limited edits before it can proceed.\n\n```json\n" + block + "\n```\n"
    )


def manuscript_reply() -> str:
    """手稿格的受控回复（形状照合约 `research_manuscript` 的规定）。"""
    block = json.dumps({"manuscript_narrative": MANUSCRIPT_SECTIONS}, ensure_ascii=False)
    return (
        "The body below states no quantity: every number lives in the assembled data table."
        "\n\n```json\n" + block + "\n```\n"
    )


def novelty_reply(pmid: str) -> str:
    """创新点格的受控回复（`nearest_prior` 用本 run 真取回的标识）。"""
    block = json.dumps(
        {
            "novelty_claim": {
                "claim": "This study ties the planning step to what retrieval returned.",
                "why_novel": "the closest retrieved work builds tooling but does not vary "
                "which planning choices move a measured outcome",
                "nearest_prior": [f"PMID:{pmid}"],
            }
        },
        ensure_ascii=False,
    )
    return (
        "That record leaves the planning choice open, which is what this study varies."
        "\n\n```json\n" + block + "\n```\n"
    )


class ManuscriptRelayHandler(BaseHTTPRequestHandler):
    """按提示词里的**合约指纹**分派回复（六个会话格 + 一个 review 格 ×2 位评审者）。

    指纹用合约 `purpose` 的首句（**逐字**取自 `task_contracts.yaml`），与
    `direction_to_report_support._content_for` 同一手法：不按 phase id 猜，也不按模型名猜。
    """

    requests: list[dict[str, Any]] = []
    query_of_question: str = VARIANT_A[0]
    pmid_of_run: str = VARIANT_A[1]

    def do_GET(self) -> None:  # noqa: N802
        self._respond(json.dumps({"data": [{"id": "relay-model", "object": "model"}]}).encode())

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
        ManuscriptRelayHandler.requests.append(body)
        prompt = json.dumps(body.get("messages", []), ensure_ascii=False)
        response = {
            "id": "chatcmpl-mock-manuscript",
            "object": "chat.completion",
            "created": 1755000000,
            "model": body.get("model", "relay-model"),
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": self._content(prompt)},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15},
        }
        self._respond(json.dumps(response).encode())

    def _content(self, prompt: str) -> str:
        """六个会话格的指纹 → 受控回复（顺序即判据：指纹取自合约 purpose 首句）。"""
        from tests.e2e.direction_to_report_support import (
            plan_reply,
            question_reply,
            review_reply,
        )

        if "turn the operator's stated research direction" in prompt:
            return question_reply(ManuscriptRelayHandler.query_of_question)
        if "write the retrieval report for this study" in prompt:
            return (
                "The search returned the records listed above for the question above."
                "\n\n```json\n"
                + json.dumps({
                    "retrieval_report": {
                        "decision": "the records bear on the question",
                        "rationale": "they cover reproducibility tooling for research",
                        "cited_ids": [ManuscriptRelayHandler.pmid_of_run],
                    }
                })
                + "\n```\n"
            )
        if "state what is new about this study" in prompt:
            return novelty_reply(ManuscriptRelayHandler.pmid_of_run)
        if "write the research plan for this study" in prompt:
            return plan_reply(ManuscriptRelayHandler.pmid_of_run)
        if "独立复核" in prompt:
            return review_reply()
        if "write the body of a submission-shaped research manuscript" in prompt:
            return manuscript_reply()
        if "act as the handling editor" in prompt:
            return editorial_reply()
        if "answer the review of this study, point by point" in prompt:
            return response_reply(prompt)
        return "Done."

    def _respond(self, payload: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return


class ManuscriptRelayFixture:
    """本机 mock 端点（threading HTTP 服务器；不出公网）。"""

    def __init__(self) -> None:
        self._server = HTTPServer(("127.0.0.1", 0), ManuscriptRelayHandler)
        self._thread = Thread(target=self._server.serve_forever, daemon=True)

    def __enter__(self) -> str:
        ManuscriptRelayHandler.requests = []
        self._thread.start()
        return f"http://127.0.0.1:{self._server.server_port}/v1"

    def __exit__(self, *args: Any) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


class OfflineEuropePmc:
    """参数化的离线 Europe PMC 传输（两个变体回**不同的记录集**；与 v1 判据同一手法）。

    `requests` 逐条记录**发给 provider 的检索词** —— 判据用它做「检索词来自问题产出」
    那一侧的取证（本文件不重判那一格，只保留读数）。
    """

    def __init__(self, pmids: tuple[str, ...]) -> None:
        self.requests: list[str] = []
        self._records = tuple(RECORD_POOL[pmid] for pmid in pmids)

    def handler(self, request: httpx.Request) -> httpx.Response:
        from tests.e2e.literature_chain_support import europepmc_record

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


def deps_for(relay_url: str, pmids: tuple[str, ...], query: str, *, manuscript: bool = True) -> Any:
    """产品组合根 + 四段执行体缝 + 上下文/被评对象装配 + spec 记录器（只观察）。

    `manuscript`（本轮的开关）：传给**产品装配面** `report_task_runner` —— 它是
    「报告相要不要**同时**汇出手稿」的**唯一**装配决策点（GOAL-099 EC-04）。
    关掉它 ⇒ 报告相只产 `research_report.md`（既有行为），手稿不落库。
    """
    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.report_support import report_task_runner
    from services.api.retrieval_context_support import retrieval_context_builder
    from services.api.review_material_support import review_material_builder
    from tests.e2e.direction_to_report_support import attach_session_tools
    from tests.e2e.live_run_support import openhands_deps
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
                manuscript=manuscript,
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
    ManuscriptRelayHandler.query_of_question = query
    ManuscriptRelayHandler.pmid_of_run = pmids[0]
    return deps, offline


__all__ = [
    "DIRECTION",
    "EXPERIMENT_IMAGE",
    "EXPERIMENT_SCRIPT",
    "MANUSCRIPT_SECTIONS",
    "OUTPUT_NAMES",
    "PHASES",
    "PROTOCOL",
    "VARIANT_A",
    "VARIANT_B",
    "ManuscriptRelayFixture",
    "ManuscriptRelayHandler",
    "OfflineEuropePmc",
    "deps_for",
    "manuscript_reply",
    "novelty_reply",
]
