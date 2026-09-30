"""GOAL-20260927-027 EC-03 判据的共享支持件（运行链装配 + 离线传输 + 读面快照）。

**为什么单独成模块**：规模门禁对 `tests/**` 同样生效（单文件 ≤ 450 行、函数 ≤ 50 行），
而本 EC 的判据要覆盖两个 provider（Europe PMC 的 REST 链 / MCP 的 stdio 链）与两个
运行链形态（`httpx.MockTransport` 离线 / 真 stdio 子进程）。本模块**不含用例**，
只放常量与装配辅助。

**与既有装配的分工**（不复制、不改写既有件）：
`tests/e2e/live_run_support.py` 的 `retrieval_capabilities` 把 provider 写死成
`ncbi_eutils`（那些判据的取样对象），本模块提供**同一形态但 provider 可选**的装配
（`capabilities_for`）——它走**同一批**产品代码（`CapabilityDeps` /
`execute_run_chain_capabilities` / `RunChainCall`），只是把 spec/provider 换成
本 EC 的两个新能力来源。既有那两份判据**一字未改**。

**离线纪律**：Europe PMC 链走 `httpx.MockTransport`（真解析、不出网）；MCP 链走
真 stdio 子进程（`tools/research_mcp_server.py`，离线、确定性）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from adapters.research_tools import EuropePmcConfig, EuropePmcProvider
from packages.application.run_orchestration.phase_capabilities import (
    CapabilityDeps,
    RunChainCall,
)
from tests.contracts.mcp_research_support import (
    PROVIDER_ID as MCP_PROVIDER_ID,
)
from tests.contracts.mcp_research_support import (
    QUERY_DOCKING,
)
from tests.contracts.mcp_research_support import (
    READ_CAPABILITY as MCP_READ_CAPABILITY,
)
from tests.contracts.mcp_research_support import (
    READ_TOOL as MCP_READ_TOOL,
)
from tests.contracts.mcp_research_support import (
    SEARCH_CAPABILITY as MCP_SEARCH_CAPABILITY,
)
from tests.contracts.mcp_research_support import (
    SEARCH_TOOL as MCP_SEARCH_TOOL,
)

EUROPE_PMC_ID = "europe_pmc"
LITERATURE_SEARCH = "literature.search"
LITERATURE_READ = "literature.read"
EUROPE_PMC_SEARCH_TOOL = "literature_search"
EUROPE_PMC_READ_TOOL = "literature_read"
#: `europe_pmc` 在多处声明里复用的能力名（policy 三处因此零改动）。
EUROPEPMC_CAPABILITIES: tuple[str, ...] = (LITERATURE_SEARCH, LITERATURE_READ)

#: EC-03 协议（新增；run-chain 声明 + 真标识两步链）。
EC03_PROTOCOL = "real_literature_chain_v1.yaml"
#: 声明输入（与既有真实协议同一份 brief —— 不新造输入面）。
DECLARED_BRIEF = "input-brief:real_research_v1"
#: brief 里的检索参数（检索串由**产品函数**构造，见 EC-01 的 `ext_id_query` 口径）。
BRIEF_QUERY = "reproducibility of computational research"

#: 线上实测记录（2026-09-30 经 Europe PMC REST `resultType=lite` 取回，用于离线夹具）。
#: 它们是**真实发表记录**：真 PMID / 真 DOI / 真标题逐字保留。
REAL_PMID_PRIMARY = "39284801"
REAL_DOI_PRIMARY = "10.1038/s41467-024-52446-8"
REAL_TITLE_PRIMARY = (
    "ENCORE: a practical implementation to improve reproducibility and "
    "transparency of computational research."
)
REAL_JOURNAL_PRIMARY = "Nat Commun"
REAL_YEAR_PRIMARY = "2024"
REAL_AUTHOR_PRIMARY = "Hoffmann C, Djerroud S, Khayat S, et al."

REAL_PMID_SECONDARY = "40601758"
REAL_DOI_SECONDARY = "10.1371/journal.pcbi.1013215"
REAL_TITLE_SECONDARY = (
    "Fundamentals of FAIR biomedical data analyses in the cloud using custom pipelines."
)
REAL_JOURNAL_SECONDARY = "PLoS Comput Biol"
REAL_YEAR_SECONDARY = "2025"

RECORDS: tuple[dict[str, str], ...] = (
    {
        "pmid": REAL_PMID_PRIMARY,
        "doi": REAL_DOI_PRIMARY,
        "title": REAL_TITLE_PRIMARY,
        "journal": REAL_JOURNAL_PRIMARY,
        "year": REAL_YEAR_PRIMARY,
        "author_string": REAL_AUTHOR_PRIMARY,
    },
    {
        "pmid": REAL_PMID_SECONDARY,
        "doi": REAL_DOI_SECONDARY,
        "title": REAL_TITLE_SECONDARY,
        "journal": REAL_JOURNAL_SECONDARY,
        "year": REAL_YEAR_SECONDARY,
        "author_string": "Kanitz A, Gürsoy G, et al.",
    },
    {
        "pmid": "40197327",
        "doi": "10.1186/s13059-025-03506-9",
        "title": (
            "Missing cell types in single-cell references impact deconvolution "
            "of bulk data but are detectable."
        ),
        "journal": "Genome Biol",
        "year": "2025",
        "author_string": "Kraven LM, van Kampen AHC, et al.",
    },
)


def europepmc_record(record: dict[str, str]) -> dict[str, object]:
    """一条记录 → Europe PMC `resultList.result[]` 项（字段名与真响应同构）。"""
    return {
        "id": record["pmid"],
        "source": "MED",
        "pmid": record["pmid"],
        "doi": record["doi"],
        "title": record["title"],
        "journalTitle": record["journal"],
        "pubYear": record["year"],
        "authorString": record["author_string"],
    }


def search_envelope(records: tuple[dict[str, str], ...] = RECORDS) -> dict[str, object]:
    """`search` 端点的真响应信封（`hitCount` + `resultList.result[]`）。"""
    return {
        "version": "6.9",
        "hitCount": len(records),
        "request": {"queryString": BRIEF_QUERY, "resultType": "lite"},
        "resultList": {"result": [europepmc_record(record) for record in records]},
    }


def record_by_pmid(pmid: str) -> dict[str, object]:
    """按 PMID 精确取记录的信封（读取步用；取不到返回零条 —— 与真 API 同构）。"""
    matched = tuple(record for record in RECORDS if record["pmid"] == pmid)
    return search_envelope(matched)


@dataclass(slots=True)
class OfflineEuropePmc:
    """离线 Europe PMC 传输：记录每次请求，按 `EXT_ID:<pmid>` 或整串检索作答。"""

    requests: list[str]

    def handler(self, request: httpx.Request) -> httpx.Response:
        term = request.url.params.get("query", "")
        self.requests.append(term)
        if term.startswith("EXT_ID:"):
            return httpx.Response(200, json=record_by_pmid(term.split(":", 1)[1]))
        return httpx.Response(200, json=search_envelope())

    def client(self) -> httpx.Client:
        return httpx.Client(transport=httpx.MockTransport(self.handler))


def europepmc_run_chain_provider(
    deps: Any, offline: OfflineEuropePmc, *, spill_threshold_bytes: int = 1
) -> EuropePmcProvider:
    """运行链用的**真实** Europe PMC provider（传输层换离线 Mock；不出网）。

    `spill_threshold_bytes=1`：运行链证据要求**内容在场**（准入会重算 digest），
    默认 32KiB 阈值会让小响应不落盘 ⇒ 证据准入 fail closed。
    """
    store, _ledger = run_chain_store_ledger(deps)
    return EuropePmcProvider(
        store,
        config=EuropePmcConfig(min_request_interval_seconds=0.0),
        http_client=offline.client(),
        spill_threshold_bytes=spill_threshold_bytes,
    )


def run_chain_store_ledger(deps: Any) -> tuple[Any, Any]:
    """该 run 装配持有的 store / ledger（与编排链同一对实例）。"""
    inner = deps.runs._deps
    return inner.artifacts, inner.ledger


def europepmc_calls() -> tuple[RunChainCall, ...]:
    """两步链：检索（query 来自声明输入）→ 读取（ids 来自上一步结果）。"""
    return (
        RunChainCall(
            provider_id=EUROPE_PMC_ID,
            tool_id=EUROPE_PMC_SEARCH_TOOL,
            capability=LITERATURE_SEARCH,
            arguments_from_input=("retrieval.query",),
            fixed_arguments={"retmax": 3},
        ),
        RunChainCall(
            provider_id=EUROPE_PMC_ID,
            tool_id=EUROPE_PMC_READ_TOOL,
            capability=LITERATURE_READ,
            ids_from_previous="ids",
        ),
    )


def mcp_calls() -> tuple[RunChainCall, ...]:
    """MCP 两步链：结果是一层信封 ⇒ 读取步用**点分路径**取 `structured.ids`。"""
    return (
        RunChainCall(
            provider_id=MCP_PROVIDER_ID,
            tool_id=MCP_SEARCH_TOOL,
            capability=MCP_SEARCH_CAPABILITY,
            fixed_arguments={"query": QUERY_DOCKING, "limit": 3},
        ),
        RunChainCall(
            provider_id=MCP_PROVIDER_ID,
            tool_id=MCP_READ_TOOL,
            capability=MCP_READ_CAPABILITY,
            ids_from_previous="structured.ids",
        ),
    )


def capabilities_for(
    deps: Any,
    *,
    provider_id: str,
    provider: Any,
    calls: tuple[RunChainCall, ...],
) -> CapabilityDeps:
    """把给定 provider 与声明接到运行链能力步上（**同一批产品对象**）。

    spec 取自**目录里那份**（`examples/config/tool_providers.yaml` 经 run-ready 装配
    读入）——不在测试里重写一份，`trust_label` 因此由**登记声明**决定。
    """
    from packages.application.run_orchestration.phase_capabilities import CapabilityDeps
    from services.api.assembly import policy_bindings

    context = deps.preflight_override
    assert context is not None
    spec = context.catalog.tool_providers[provider_id]
    store, ledger = run_chain_store_ledger(deps)
    policy = policy_bindings().get("policy_evaluator")
    assert policy is not None, "policy.yaml must be loadable for the run-chain policy check"
    return CapabilityDeps(
        calls=calls,
        providers={spec.id: provider},
        provider_specs={spec.id: spec},
        policy=policy,
        artifacts=store,
        ledger=ledger,
    )


def with_capabilities(deps: Any, capability_deps: CapabilityDeps) -> None:
    """把运行链能力步接到既有装配上（重建服务、复用同一批 store/ledger 实例）。"""
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService

    deps.runs = RunOrchestrationService(replace(deps.runs._deps, capabilities=capability_deps))


@dataclass(slots=True)
class OutcomeRecorder:
    """记录每次 `start_run` 的 `RunOutcome`（EC-04 要读 HandoffBundle digest 序列）。

    这是**装配方**的包装（与 `with_capabilities` 同一层）：`RunOutcome` 是产品对象，
    但 HTTP 边界不持久化 `handoff_digests` ⇒ 判据若只看读面就取证不到。包装不改产品
    代码：它把同一个 `start_run` 的返回值原样透传，同时留一份引用。
    """

    outcomes: list[Any]

    def install(self, deps: Any) -> None:
        service = deps.runs
        original = service.start_run

        def recorded(*args: Any, **kwargs: Any) -> Any:
            outcome = original(*args, **kwargs)
            self.outcomes.append(outcome)
            return outcome

        service.start_run = recorded

    def handoff_digests(self) -> tuple[str, ...]:
        """最后一次 run 的 HandoffBundle digest 序列（没有记录 ⇒ 空元组）。"""
        if not self.outcomes:
            return ()
        return tuple(str(item) for item in self.outcomes[-1].handoff_digests)


__all__ = [
    "BRIEF_QUERY",
    "DECLARED_BRIEF",
    "EC03_PROTOCOL",
    "EUROPE_PMC_ID",
    "EUROPE_PMC_READ_TOOL",
    "EUROPE_PMC_SEARCH_TOOL",
    "EUROPEPMC_CAPABILITIES",
    "LITERATURE_READ",
    "LITERATURE_SEARCH",
    "MCP_PROVIDER_ID",
    "OfflineEuropePmc",
    "OutcomeRecorder",
    "REAL_DOI_PRIMARY",
    "REAL_DOI_SECONDARY",
    "REAL_PMID_PRIMARY",
    "REAL_PMID_SECONDARY",
    "RECORDS",
    "capabilities_for",
    "europepmc_calls",
    "europepmc_run_chain_provider",
    "mcp_calls",
    "with_capabilities",
]
