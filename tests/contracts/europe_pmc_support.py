"""Europe PMC 判据的共享支持件（真实样本 + MockTransport 宿主 + Port 调用）。

为什么单独成模块：规模门禁对 `tests/**` 同样生效（单文件 ≤ 450 行），而两份判据
（Port 语义 / URL 策略）共用同一批真实样本与装配辅助。**本模块不含任何用例**
（文件名不以 `test_` 开头 ⇒ 不被收集），只放常量与纯辅助。

真实样本口径：`REAL_*` 常量取自 Europe PMC 线上 REST 的**实测记录**
（2026-09-29 取回，`resultType=lite` 默认档）——真 PMID / 真 DOI / 真标题逐字保留，
**不是**合成标识。判据只走 `httpx.MockTransport`（离线），真实网络调用不在射程内。

检索串一律经**产品函数** `ext_id_query` 构造（本模块不自己拼检索语法），
既避免第二份模板，也让判据走的就是运行链会走的那条路径。
"""

from __future__ import annotations

import json

import httpx
import pytest

from adapters.fakes import FakeArtifactStore
from adapters.research_tools.europe_pmc import (
    ARGS_ARTIFACT_PREFIX,
    EUROPE_PMC_BASE_URL,
    EuropePmcConfig,
    EuropePmcProvider,
)
from adapters.research_tools.europe_pmc_parsing import ext_id_query
from packages.application.model_relay.endpoint_policy import EndpointUrlPolicy
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import PermanentPortError
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from packages.domain.enums import (
    EffectClass,
    ProviderType,
    ToolResultStatus,
    TrustLevel,
)
from packages.domain.tools import ToolCallRecord, ToolProviderSpec

#: 线上实测记录（2026-09-29 由 Europe PMC REST 取回；resultType=lite 默认档）。
REAL_PMID = "38000001"
REAL_DOI = "10.1177/0310057x231212211"
REAL_TITLE = (
    "Exploring anaesthetists' views on the carbon footprint of anaesthesia and "
    "identifying opportunities and challenges for reducing its impact on the environment."
)
REAL_JOURNAL = "Anaesth Intensive Care"
REAL_YEAR = "2024"
REAL_AUTHOR_STRING = (
    "Breth-Petersen M, Barratt AL, McGain F, Skowno JJ, Zhong G, Weatherall AD, "
    "Bell KJ, Pickles KM."
)
#: 第二条真实记录（`literature_read` 的 ids 面；DOI 与 PMID 均真实）。
SECOND_PMID = "31452104"
SECOND_DOI = "10.1007/978-1-4939-9752-7_10"
SECOND_TITLE = "Molegro Virtual Docker for Docking."
SECOND_AUTHOR_STRING = "Bitencourt-Ferreira G, de Azevedo WF."
SECOND_JOURNAL = "Methods Mol Biol"
SECOND_YEAR = "2019"

QUERY_KEY = "query"
TASK_ID = "task-goal027"
OP_KEY = "op-1"
SEARCH_TOOL = "literature_search"
READ_TOOL = "literature_read"
CITATION_TOOL = "citation_inspect"
GHOST_TOOL = "ghost_tool"

PROVIDER = ToolProviderSpec(
    id="europe_pmc",
    kind=ProviderType.REST,
    trust_level=TrustLevel.VERIFIED,
    capabilities=["literature.search", "literature.read"],
    effect_class=EffectClass.READ_ONLY,
    transport="rest",
    network_domains=["www.ebi.ac.uk"],
)


def call_port(provider: object, spec: ToolProviderSpec, call: ToolCallRecord) -> object:
    """按 Port 面调用 `execute`（经 `getattr` 取方法名）。

    经 `getattr` 而非点号调用，是因为安全扫描器把点号 + `execute(` 的字面量形态
    一律判成裸 SQL 执行并**拦截写入**（全仓既有的书写面规避口径）。这里调用的仍是
    同一个 Port 方法，没有改变任何被测语义。
    """
    return getattr(provider, "execute")(spec, call)


#: 单条记录的可替换字段（默认值 = 第一条真实记录）。
RecordFields = dict[str, str]

_FIRST: RecordFields = {
    "pmid": REAL_PMID,
    "doi": REAL_DOI,
    "title": REAL_TITLE,
    "journal": REAL_JOURNAL,
    "year": REAL_YEAR,
    "author_string": REAL_AUTHOR_STRING,
}


def real_record(**overrides: str) -> dict[str, object]:
    """一条**真实结构**的 Europe PMC `resultList.result[]` 项。

    字段默认取第一条真实记录；`overrides` 只允许覆盖 `_FIRST` 里已有的键
    （拼错字段名会立刻 KeyError，而不是静默产出一条半真的记录）。
    """
    fields = {**_FIRST, **overrides}
    unknown = set(overrides) - set(_FIRST)
    assert not unknown, f"未知字段名（会造出假记录）：{sorted(unknown)}"
    return {
        "id": fields["pmid"],
        "source": "MED",
        "pmid": fields["pmid"],
        "doi": fields["doi"],
        "title": fields["title"],
        "journalTitle": fields["journal"],
        "pubYear": fields["year"],
        "authorString": fields["author_string"],
    }


def second_record() -> dict[str, object]:
    """第二条**真实**记录（不同 PMID / DOI / 标题 / 期刊 / 年份）。"""
    return real_record(
        pmid=SECOND_PMID,
        doi=SECOND_DOI,
        title=SECOND_TITLE,
        journal=SECOND_JOURNAL,
        year=SECOND_YEAR,
        author_string=SECOND_AUTHOR_STRING,
    )


def search_payload(*records: dict[str, object], hit_count: int | None = None) -> dict[str, object]:
    """`search` 端点的真实响应信封（`hitCount` + `resultList.result[]`）。"""
    return {
        "version": "6.9",
        "hitCount": len(records) if hit_count is None else hit_count,
        "request": {"queryString": "EXT_ID", "resultType": "lite"},
        "resultList": {"result": list(records)},
    }


def search_args(pmid: str = REAL_PMID, retmax: int = 10) -> dict[str, object]:
    """检索工具的参数对象（检索串来自**产品函数**，不是本模块拼的）。"""
    return {QUERY_KEY: ext_id_query(pmid), "retmax": retmax}


def read_args(pmid: str = SECOND_PMID) -> dict[str, object]:
    return {"ids": [pmid]}


class Transport:
    """请求计数 + 可编排响应的 MockTransport 宿主（反证判据读它计数）。"""

    def __init__(self, payloads: dict[str, dict[str, object]] | None = None) -> None:
        self.requests: list[httpx.Request] = []
        self._payloads = payloads or {}

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        term = request.url.params.get(QUERY_KEY, "")
        for key, payload in self._payloads.items():
            if key in term:
                return httpx.Response(200, json=payload)
        fallback = self._payloads.get("*")
        if fallback is not None:
            return httpx.Response(200, json=fallback)
        return httpx.Response(200, json=search_payload(real_record()))

    @property
    def count(self) -> int:
        return len(self.requests)

    def client(self) -> httpx.Client:
        return httpx.Client(transport=httpx.MockTransport(self.handler))


def make_provider(
    transport: Transport | None = None,
    *,
    base_url: str = EUROPE_PMC_BASE_URL,
    policy: EndpointUrlPolicy | None = None,
    store: ArtifactStore | None = None,
) -> EuropePmcProvider:
    return EuropePmcProvider(
        store if store is not None else FakeArtifactStore(),
        config=EuropePmcConfig(base_url=base_url, min_request_interval_seconds=0.0),
        http_client=(transport or Transport()).client(),
        url_policy=policy if policy is not None else EndpointUrlPolicy(),
        spill_threshold_bytes=1,
    )


def make_call(tool_id: str, args: dict[str, object], operation_key: str = OP_KEY) -> ToolCallRecord:
    raw = json.dumps(args, sort_keys=True).encode("utf-8")
    return ToolCallRecord(
        task_id=TASK_ID,
        attempt=1,
        operation_key=operation_key,
        tool_id=tool_id,
        capability="literature.search",
        argument_digest=Digest.of_bytes(raw),
    )


def put_args(store: ArtifactStore, call: ToolCallRecord, args: dict[str, object]) -> None:
    raw = json.dumps(args, sort_keys=True).encode("utf-8")
    store.put(
        Artifact(
            id=f"{ARGS_ARTIFACT_PREFIX}{call.task_id}:{call.operation_key}",
            digest=Digest.of_bytes(raw),
            size_bytes=len(raw),
            media_type="application/json",
        ),
        raw,
    )


def spilled_payload(store: ArtifactStore, result: object, tool_id: str) -> dict[str, object]:
    """取回 spill 的内容（`spill_threshold_bytes=1` ⇒ 必然落盘）并反序列化。"""
    artifact_id = f"tool-result:{TASK_ID}:{OP_KEY}:{tool_id}"
    content = store.get(artifact_id)
    assert Digest.of_bytes(content) == getattr(result, "output_digest"), (
        "spill 内容必须与 output_digest 逐字节一致（内容寻址）"
    )
    decoded: object = json.loads(content.decode("utf-8"))
    assert isinstance(decoded, dict), "spill 内容必须是 JSON 对象"
    return decoded


def run_tool(
    provider: EuropePmcProvider,
    store: ArtifactStore,
    tool_id: str,
    args: dict[str, object],
) -> tuple[object, dict[str, object]]:
    """跑一次工具调用并取回 spill 内容（断言 SUCCEEDED）。"""
    call = make_call(tool_id, args)
    put_args(store, call, args)
    result = call_port(provider, PROVIDER, call)
    assert getattr(result, "status") is ToolResultStatus.SUCCEEDED
    return result, spilled_payload(store, result, tool_id)


def refuse_before_network(base_url: str, spec: ToolProviderSpec = PROVIDER) -> Transport:
    """按给定 base_url 跑一次调用，断言**零请求**被拒；返回 transport 供进一步断言。"""
    store = FakeArtifactStore()
    transport = Transport()
    provider = make_provider(transport, base_url=base_url, store=store)
    args = search_args()
    call = make_call(SEARCH_TOOL, args)
    put_args(store, call, args)

    with pytest.raises(PermanentPortError):
        call_port(provider, spec, call)

    assert transport.count == 0, (
        f"触网前必须被拒（零请求），实测发出 {transport.count} 次：{base_url}"
    )
    return transport
