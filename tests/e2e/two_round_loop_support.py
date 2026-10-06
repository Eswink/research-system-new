"""GOAL-20261006-031 EC-03 判据的**共享支持件**（两轮运行链装配 + 读面辅助）。

**为什么单独成模块**：规模门禁对 `tests/**` 同样生效（单文件 ≤ 450 行），而本 EC 的判据要
覆盖两条臂（触发 / 不触发）、两轮派生链、四条能力的调用与消费、两向反证。本模块**不含
用例**，只放常量与装配辅助 —— 与 `tests/e2e/granted_reads_support.py` /
`tests/e2e/literature_chain_support.py` 的拆分同一手法。

**它装配什么**（一条真正的**派生链**，跨两个 phase）：

  * `round1`：`evidence.read`（读本 run 的证据投影，`run_id_argument`）→
    `literature.search`（`query` 来自声明输入的 `retrieval.query`）；
  * `round2`：`evidence.read`（**再读一次**投影——此时里面已有 round1 的工具证据）→
    `artifact.read`（**读 round1 检索结果的制品内容**；哪个制品由
    `artifact_from_previous="literature_search"` 声明式选中）→
    `literature.read`（`ids` 来自**刚读到的内容**的 `content.ids`，
    `requires_previous_ids=False` ⇒ 第一轮没返回标识时**带理由跳过**）。

**为什么 round2 的标识必须经「读面 → 制品内容」两跳**：EC-03(c) 明文要求
「第二轮能读到第一轮的结论（**读面**证据，不是内存传递）」。`previous` 在**同一个 phase
内部**是内存传递；跨 phase 没有内存通道（`CompiledPhase.inputs` 只是声明的输入制品 id）。
因此 round2 的派生走**读面**：`evidence.read` 拿投影 → 按声明的后缀选中 round1 的产出
制品 → `artifact.read` 读它的**内容** → 从内容里取 `ids`。这条链上的每一跳都是**产品
代码**（`CanonicalReadProvider` 的真实现），不是支持件拼的。

**装配的三条实测结构事实**（支持件按它们设计，不是绕过它们）：

1. **两个 phase 必须都能跑**：`capability_execution: run_chain` 把 provider 从会话工具面
   拿掉（`run_chain_tool_ids` 按 phase 的 tool_requirements 算），否则会话创建会因
   provider→SDK 工具映射缺失而**点名失败**（生产装配里 `register_tools` 是空操作）。
2. **`m12_artifact` 与 `ncbi_eutils` 都要接进链**：`CanonicalReadProvider` 提供三条读
   （`evidence.read` / `artifact.read`），`NcbiEutilsProvider` 提供两条检索。两个实例、
   两张 spec —— 与生产目录同源（`examples/config/tool_providers.yaml`）。
3. **跳过臂的构造方式**：把 round1 的检索响应换成**零命中**（`esearchresult.idlist == []`）
   ⇒ round2 的读取步**声明式跳过**。这是**同一套装配 + 同一份协议**，只换 mock 响应 ——
   两条臂因此在**同一判据**下可区分（不是两套代码各证一半）。
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any, cast

from adapters.canonical import CanonicalReadProvider
from adapters.research_tools import NcbiEutilsConfig, NcbiEutilsProvider
from packages.application.ports.tool_provider import ToolProvider
from packages.application.run_orchestration.phase_capabilities import (
    CapabilityDeps,
    RunChainCall,
)

PROTOCOL = "two_round_research_loop_v1.yaml"
ROUND1_PHASE = "round1"
ROUND2_PHASE = "round2"

#: provider id（与 `examples/config/tool_providers.yaml` 逐字一致）。
CANONICAL_ID = "m12_artifact"
NCBI_ID = "ncbi_eutils"

#: 能力 → provider 侧 tool id（`RunChainCall.tool_id` 用这一侧的名字）。
TOOL_IDS = {
    "evidence.read": "evidence_read",
    "artifact.read": "artifact_read",
    "literature.search": "literature_search",
    "literature.read": "literature_read",
}

#: 检索与读取的能力名（逐字写死，不 import 产品常量当预言机）。
SEARCH = "literature.search"
READ = "literature.read"

#: 离线检索响应的标识（**夹具值**；真实 run 里它们是响应本身返回的 PMID）。
MOCK_PMIDS: tuple[str, ...] = ("39000001", "39000002")
#: `artifact_from_previous` 的声明后缀（round1 检索制品的 tool id 尾段）。
SEARCH_ARTIFACT_SUFFIX = "literature_search"
#: round2 从 round1 内容里取标识的**声明路径**（`artifact.read` 返回的 `content.ids`）。
IDS_PATH = "content.ids"


def _esearch_json(pmids: tuple[str, ...]) -> dict[str, object]:
    return {"esearchresult": {"count": str(len(pmids)), "idlist": list(pmids)}}


def _efetch_xml(pmid: str) -> bytes:
    return (
        b'<?xml version="1.0" encoding="UTF-8"?><PubmedArticleSet><PubmedArticle>'
        b"<MedlineCitation><PMID>" + pmid.encode("ascii") + b"</PMID><Article>"
        b"<ArticleTitle>Derived follow-up on a first-round hit</ArticleTitle>"
        b"<Journal><Title>J Derived Res</Title></Journal></Article>"
        b"</MedlineCitation></PubmedArticle></PubmedArticleSet>"
    )


class OfflineNcbi:
    """离线 NCBI 传输（`httpx.MockTransport`，不出网）：记录每次请求、按请求作答。

    `pmids` 为空元组 ⇒ esearch 返回**零命中**（**不触发臂**的输入；同一条装配、
    同一份协议，只有这一个响应不同）。
    """

    def __init__(self, pmids: tuple[str, ...] = MOCK_PMIDS) -> None:
        self.pmids = pmids
        self.requests: list[tuple[str, str]] = []

    def client(self) -> Any:
        import httpx

        def handler(request: httpx.Request) -> httpx.Response:
            endpoint = request.url.path.rsplit("/", 1)[-1]
            self.requests.append((endpoint, str(request.url.query)))
            if endpoint == "esearch.fcgi":
                return httpx.Response(200, json=_esearch_json(self.pmids))
            if endpoint == "efetch.fcgi":
                pmid = request.url.params.get("id", "") or self.pmids[0]
                return httpx.Response(200, content=_efetch_xml(pmid.split(",")[0]))
            return httpx.Response(404, text="not found")

        return httpx.Client(transport=httpx.MockTransport(handler))

    def endpoints(self) -> list[str]:
        return [endpoint for endpoint, _query in self.requests]


def _canonical_calls() -> tuple[RunChainCall, ...]:
    """`round1` 的两条调用：读证据投影 → 检索（`query` 来自声明输入）。"""
    return (
        RunChainCall(
            provider_id=CANONICAL_ID,
            tool_id=TOOL_IDS["evidence.read"],
            capability="evidence.read",
            run_id_argument=True,
            phase_id=ROUND1_PHASE,
        ),
        RunChainCall(
            provider_id=NCBI_ID,
            tool_id=TOOL_IDS[SEARCH],
            capability=SEARCH,
            arguments_from_input=("retrieval.query",),
            fixed_arguments={"retmax": 3},
            phase_id=ROUND1_PHASE,
        ),
    )


def derived_calls() -> tuple[RunChainCall, ...]:
    """`round2` 的三条调用 —— **派生链的本体**（每一步的取值来源都是声明）：

    1. `evidence.read`（读面）：拿本 run 的投影（此刻已含 round1 的工具证据与产出）；
    2. `artifact.read`：`artifact_from_previous=literature_search` ⇒ 从**上一步的读面
       结果**里按声明后缀选中 round1 的检索制品，读它的**内容**；
    3. `literature.read`：`ids_from_previous=content.ids` ⇒ 从**刚读到的内容**里取标识，
       `requires_previous_ids=False` ⇒ 内容里**没有**非空 ids 时**带理由跳过**。
    """
    return (
        RunChainCall(
            provider_id=CANONICAL_ID,
            tool_id=TOOL_IDS["evidence.read"],
            capability="evidence.read",
            run_id_argument=True,
            phase_id=ROUND2_PHASE,
        ),
        RunChainCall(
            provider_id=CANONICAL_ID,
            tool_id=TOOL_IDS["artifact.read"],
            capability="artifact.read",
            artifact_from_previous=SEARCH_ARTIFACT_SUFFIX,
            phase_id=ROUND2_PHASE,
        ),
        RunChainCall(
            provider_id=NCBI_ID,
            tool_id=TOOL_IDS[READ],
            capability=READ,
            ids_from_previous=IDS_PATH,
            requires_previous_ids=False,
            phase_id=ROUND2_PHASE,
        ),
    )


def all_calls() -> tuple[RunChainCall, ...]:
    """两个 phase 的全部调用（同一份装配里的声明顺序）。"""
    return (*_canonical_calls(), *derived_calls())


def assembled_deps(mock_relay_url: str, *, offline: OfflineNcbi) -> Any:
    """run-ready 装配 + 两轮派生链的装配面（**同一批产品对象**）。

    两个真 provider（canonical 读面 + NCBI 检索），两条 spec 取自**目录里那两份**
    （`examples/config/tool_providers.yaml` 经 run-ready 装配读入）—— 不在测试里重写，
    `trust_label` 与 URL 策略因此由**登记声明**决定。
    """
    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.assembly import policy_bindings
    from tests.e2e.live_run_support import openhands_deps as _openhands_deps

    deps = _openhands_deps(mock_relay_url, map_tools=False)
    store, ledger = store_ledger(deps)
    context = deps.preflight_override
    assert context is not None
    canonical_spec = context.catalog.tool_providers[CANONICAL_ID]
    ncbi_spec = context.catalog.tool_providers[NCBI_ID]
    policy = policy_bindings().get("policy_evaluator")
    assert policy is not None, "policy.yaml must be loadable for the run-chain policy check"
    capabilities = CapabilityDeps(
        calls=all_calls(),
        providers={
            CANONICAL_ID: cast(
                "ToolProvider",
                CanonicalReadProvider(store, ledger, spill_threshold_bytes=1),
            ),
            NCBI_ID: cast(
                "ToolProvider",
                NcbiEutilsProvider(
                    store,
                    credentials=deps.credentials,
                    config=NcbiEutilsConfig(min_request_interval_seconds=0.0),
                    http_client=offline.client(),
                    spill_threshold_bytes=1,
                ),
            ),
        },
        provider_specs={CANONICAL_ID: canonical_spec, NCBI_ID: ncbi_spec},
        policy=policy,
        artifacts=store,
        ledger=ledger,
    )
    old = deps.runs
    assert old is not None
    deps.runs = RunOrchestrationService(replace(old._deps, capabilities=capabilities))
    return deps


def store_ledger(deps: Any) -> tuple[Any, Any]:
    """该 run 装配持有的 store / ledger（与编排链同一对实例）。"""
    inner = deps.runs._deps
    return inner.artifacts, inner.ledger


def rewire_calls(deps: Any, calls: tuple[RunChainCall, ...]) -> Any:
    """**反证臂**入口：换掉运行链的调用声明（同一批 provider/policy/store，只改声明）。

    与 `test_release_expansion_is_read_only.py` 的内存内目录裁剪同一手法：产品文件
    零改动，改的是**本次 run 看到的声明**。「派生规则改坏 ⇒ 判红」由此可构造。
    """
    from packages.application.run_orchestration.service import RunOrchestrationService

    old = deps.runs
    assert old is not None
    capabilities = old._deps.capabilities
    assert capabilities is not None, "两轮链必须先装配再改声明"
    deps.runs = RunOrchestrationService(
        replace(old._deps, capabilities=replace(capabilities, calls=calls))
    )
    return deps


def with_read_step(
    ids_path: str, *, suffix: str = SEARCH_ARTIFACT_SUFFIX
) -> tuple[RunChainCall, ...]:
    """把派生链的声明换成给定路径/后缀（反证臂用；其余声明逐字不变）。"""
    return tuple(
        replace(call, ids_from_previous=ids_path)
        if call.tool_id == TOOL_IDS[READ]
        else replace(call, artifact_from_previous=suffix)
        if call.tool_id == TOOL_IDS["artifact.read"]
        else call
        for call in all_calls()
    )


def read_face(deps: Any) -> CanonicalReadProvider:
    """判据侧另建一个同源读面（读同一份 store / ledger；**只读**，不参与运行链）。"""
    store, ledger = store_ledger(deps)
    return CanonicalReadProvider(store, ledger, spill_threshold_bytes=1)


def phase_of_task(reads: Any) -> dict[str, str]:
    """`task_id` → phase id（由**该任务的交付物制品名**判，不靠调用顺序猜）。"""
    mapping: dict[str, str] = {}
    for artifact_id in artifact_ids(reads):
        head, _, tail = artifact_id.rpartition(":")
        if tail == "round_one_findings":
            mapping[head] = ROUND1_PHASE
        elif tail == "round_two_followup":
            mapping[head] = ROUND2_PHASE
    return mapping


def tool_evidence(reads: Any, *, phase: str | None = None) -> dict[tuple[str, str], dict[str, Any]]:
    """`tool_refs` 非空的证据，按 `(provider_id, tool_id)` 建索引（读面口径）。

    `phase` 非空时只取该 phase 任务的证据 —— 两个 phase 都会调 `evidence_read`
    ⇒ 单键索引会**后写覆盖前写**（GOAL-030 EC-01 实测过这个掩蔽形态）。
    """
    by_task = phase_of_task(reads)
    by_tool: dict[tuple[str, str], dict[str, Any]] = {}
    for item in reads.evidence:
        refs = item.get("tool_refs") or []
        if len(refs) != 2:
            continue
        if phase is not None and by_task.get(task_of_evidence(item)) != phase:
            continue
        by_tool[(str(refs[0]), str(refs[1]))] = item
    return by_tool


def task_of_evidence(item: dict[str, Any]) -> str:
    """证据所属任务的标识（工具证据的 `artifact_id` 带 `tool-result:{task_id}:…`）。"""
    parts = str(item.get("artifact_id") or "").split(":")
    return parts[1] if len(parts) > 2 else ""


def content_of(client: Any, artifact_id: str) -> dict[str, Any]:
    """按 artifact id 取**内容**并解析成 JSON 对象（经既有读面，不经内部对象）。"""
    response = client.get(f"/artifacts/{artifact_id}/content")
    assert response.status_code == 200, (artifact_id, response.status_code, response.text[:200])
    parsed = json.loads(response.content.decode("utf-8"))
    assert isinstance(parsed, dict), ("工具结果内容必须是 JSON 对象", artifact_id, type(parsed))
    return parsed


def artifact_ids(reads: Any) -> list[str]:
    payload = reads.artifacts
    entries = payload["artifacts"] if isinstance(payload, dict) else payload
    return [str(item.get("id") or "") for item in entries]


def skip_facts(client: Any, run_id: str) -> list[dict[str, Any]]:
    """`run.completed` 的 `skipped` 载荷（**声明式跳过**的读面形态；无 ⇒ 空列表）。"""
    events = client.get(f"/runs/{run_id}/events").json()
    for event in events:
        if event["type"] != "run.completed":
            continue
        raw = event.get("payload", {}).get("skipped")
        if isinstance(raw, list):
            return [dict(item) for item in raw if isinstance(item, dict)]
    return []


def app(deps: Any) -> Any:
    from services.api.app import create_app

    return create_app(deps)


__all__ = [
    "CANONICAL_ID",
    "IDS_PATH",
    "MOCK_PMIDS",
    "NCBI_ID",
    "OfflineNcbi",
    "PROTOCOL",
    "READ",
    "ROUND1_PHASE",
    "ROUND2_PHASE",
    "SEARCH",
    "SEARCH_ARTIFACT_SUFFIX",
    "TOOL_IDS",
    "all_calls",
    "app",
    "artifact_ids",
    "assembled_deps",
    "content_of",
    "derived_calls",
    "phase_of_task",
    "read_face",
    "rewire_calls",
    "skip_facts",
    "store_ledger",
    "task_of_evidence",
    "tool_evidence",
    "with_read_step",
]
