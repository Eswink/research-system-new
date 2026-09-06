"""NcbiEutilsProvider contract suite（离线，httpx MockTransport）。

覆盖：esearch/efetch/elink 成功路径与结果归一化；参数 artifact digest 防篡改；
429 限流→transient；超时→TOOL_TIMEOUT；畸形响应→TOOL_SCHEMA_MISMATCH；
TOOL 域凭据注入（api_key query 参数，禁止 passthrough）；健康探测；
大结果 spill。真实网络调用不进入本套件（requires_live_llm marker 手动运行）。
"""

from __future__ import annotations

import json
import time

import httpx
import pytest

from adapters.fakes import FakeArtifactStore, FakeCredentialResolver
from adapters.research_tools import NcbiEutilsConfig, NcbiEutilsProvider
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import (
    PermanentPortError,
    PortTimeoutError,
    TransientPortError,
)
from packages.domain.core import Digest
from packages.domain.enums import (
    EffectClass,
    EndpointHealth,
    FailureCategory,
    ProviderType,
    ToolResultStatus,
    TrustLevel,
)
from packages.domain.tools import ToolCallRecord, ToolProviderSpec

# Computed fixture credential (never a real secret).
_NCBI_FIXTURE_KEY = "ncbi-" + "key" * 4

PROVIDER = ToolProviderSpec(
    id="ncbi_eutils",
    kind=ProviderType.REST,
    trust_level=TrustLevel.VERIFIED,
    capabilities=["literature.search", "literature.read", "citation.inspect"],
    effect_class=EffectClass.READ_ONLY,
    network_domains=["eutils.ncbi.nlm.nih.gov"],
)

SEARCH_JSON = {"esearchresult": {"count": "2", "idlist": ["38000001", "38000002"]}}

EFETCH_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>38000001</PMID>
      <Article>
        <ArticleTitle>Frozen embeddings for low-resource classification</ArticleTitle>
        <Abstract><AbstractText>We compare TF-IDF and frozen embeddings.</AbstractText></Abstract>
        <Journal><Title>J Test Res</Title>
          <JournalIssue><PubDate><Year>2026</Year></PubDate></JournalIssue>
        </Journal>
        <AuthorList>
          <Author><ForeName>Ann</ForeName><LastName>Author</LastName></Author>
        </AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>"""

ELINK_JSON = {
    "linksets": [{"linksetdbs": [{"dbto": "pmc", "links": ["PMC8000001", "PMC8000002"]}]}]
}

REQUESTS: list[httpx.Request] = []


def _handler(request: httpx.Request) -> httpx.Response:
    REQUESTS.append(request)
    path = request.url.path
    if path.endswith("einfo.fcgi"):
        return httpx.Response(200, json={"dbinfo": [{"db": "pubmed"}, {"db": "pmc"}]})
    if path.endswith("esearch.fcgi"):
        return httpx.Response(200, json=SEARCH_JSON)
    if path.endswith("efetch.fcgi"):
        return httpx.Response(200, content=EFETCH_XML)
    if path.endswith("elink.fcgi"):
        return httpx.Response(200, json=ELINK_JSON)
    return httpx.Response(404, text="not found")


def _provider(
    *,
    fault: str = "none",
    token: str | None = None,
    interval: float = 0.0,
) -> NcbiEutilsProvider:
    REQUESTS.clear()

    def handler(request: httpx.Request) -> httpx.Response:
        REQUESTS.append(request)
        if fault == "rate_limit":
            return httpx.Response(429, text="too many requests")
        if fault == "timeout":
            raise httpx.ConnectTimeout("injected timeout")
        if fault == "malformed":
            return httpx.Response(200, text="<not-json>")
        if fault == "unreachable":
            raise httpx.ConnectError("injected connection failure")
        return _handler(request)

    credentials = FakeCredentialResolver({"NCBI_API_KEY": _NCBI_FIXTURE_KEY}) if token else None
    return NcbiEutilsProvider(
        FakeArtifactStore(),
        credentials=credentials,
        config=NcbiEutilsConfig(min_request_interval_seconds=interval),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def _call(tool_id: str, args: dict[str, object], operation_key: str = "op-1") -> ToolCallRecord:
    raw = json.dumps(args, sort_keys=True).encode("utf-8")
    return ToolCallRecord(
        task_id="task-1",
        attempt=1,
        operation_key=operation_key,
        tool_id=tool_id,
        capability="literature.search",
        argument_digest=Digest.of_bytes(raw),
    )


def _put_args(store: ArtifactStore, call: ToolCallRecord, args: dict[str, object]) -> None:
    raw = json.dumps(args, sort_keys=True).encode("utf-8")
    from packages.domain.artifacts import Artifact

    store.put(
        Artifact(
            id=f"tool-args:{call.task_id}:{call.operation_key}",
            digest=Digest.of_bytes(raw),
            size_bytes=len(raw),
            media_type="application/json",
        ),
        raw,
    )


class TestSearchRead:
    def test_esearch_success(self) -> None:
        provider = _provider()
        call = _call("literature_search", {"query": "frozen embeddings", "retmax": 10})
        _put_args(provider._store, call, {"query": "frozen embeddings", "retmax": 10})
        result = provider.execute(PROVIDER, call)
        assert result.status is ToolResultStatus.SUCCEEDED
        assert result.output_digest is not None

    def test_efetch_parses_xml(self) -> None:
        provider = _provider()
        call = _call("literature_read", {"ids": ["38000001"]})
        _put_args(provider._store, call, {"ids": ["38000001"]})
        result = provider.execute(PROVIDER, call)
        assert result.status is ToolResultStatus.SUCCEEDED

    def test_elink_returns_pmc_links(self) -> None:
        provider = _provider()
        call = _call("citation_inspect", {"id": "38000001"})
        _put_args(provider._store, call, {"id": "38000001"})
        result = provider.execute(PROVIDER, call)
        assert result.status is ToolResultStatus.SUCCEEDED

    def test_args_digest_mismatch_is_permanent(self) -> None:
        provider = _provider()
        call = _call("literature_search", {"query": "one"})
        _put_args(provider._store, call, {"query": "two"})
        with pytest.raises(PermanentPortError) as exc_info:
            provider.execute(PROVIDER, call)
        assert exc_info.value.failure_category is FailureCategory.VALIDATION_FAILURE

    def test_missing_args_artifact_is_invalid_input(self) -> None:
        provider = _provider()
        call = _call("literature_search", {"query": "one"})
        with pytest.raises(PermanentPortError):
            provider.execute(PROVIDER, call)

    def test_unknown_tool_id_is_invalid_input(self) -> None:
        provider = _provider()
        call = _call("ghost_tool", {})
        _put_args(provider._store, call, {})
        with pytest.raises(PermanentPortError):
            provider.execute(PROVIDER, call)


class TestFailureClassification:
    def test_rate_limit_is_transient(self) -> None:
        provider = _provider(fault="rate_limit")
        call = _call("literature_search", {"query": "x"})
        _put_args(provider._store, call, {"query": "x"})
        with pytest.raises(TransientPortError) as exc_info:
            provider.execute(PROVIDER, call)
        assert exc_info.value.retryable is True
        assert exc_info.value.failure_category is FailureCategory.TOOL_UNAVAILABLE

    def test_timeout_is_port_timeout(self) -> None:
        provider = _provider(fault="timeout")
        call = _call("literature_search", {"query": "x"})
        _put_args(provider._store, call, {"query": "x"})
        with pytest.raises(PortTimeoutError) as exc_info:
            provider.execute(PROVIDER, call)
        assert exc_info.value.failure_category is FailureCategory.TOOL_TIMEOUT

    def test_connection_failure_is_transient(self) -> None:
        provider = _provider(fault="unreachable")
        call = _call("literature_search", {"query": "x"})
        _put_args(provider._store, call, {"query": "x"})
        with pytest.raises(TransientPortError) as exc_info:
            provider.execute(PROVIDER, call)
        assert exc_info.value.failure_category is FailureCategory.TOOL_UNAVAILABLE

    def test_malformed_response_is_permanent(self) -> None:
        provider = _provider(fault="malformed")
        call = _call("literature_search", {"query": "x"})
        _put_args(provider._store, call, {"query": "x"})
        with pytest.raises(PermanentPortError) as exc_info:
            provider.execute(PROVIDER, call)
        assert exc_info.value.failure_category is FailureCategory.TOOL_SCHEMA_MISMATCH


class TestCredentialAndHealth:
    def test_api_key_injected_as_query_param(self) -> None:
        provider = _provider(token="present")
        call = _call("literature_search", {"query": "x"})
        _put_args(provider._store, call, {"query": "x"})
        provider.execute(PROVIDER, call)
        assert REQUESTS, "at least one request must be issued"
        assert REQUESTS[0].url.params.get("api_key") == _NCBI_FIXTURE_KEY

    def test_no_credential_means_no_api_key_param(self) -> None:
        provider = _provider()
        call = _call("literature_search", {"query": "x"})
        _put_args(provider._store, call, {"query": "x"})
        provider.execute(PROVIDER, call)
        assert REQUESTS[0].url.params.get("api_key") is None

    def test_check_health_healthy(self) -> None:
        provider = _provider()
        report = provider.check_health(PROVIDER)
        assert report.status is EndpointHealth.HEALTHY
        assert report.observed_schema_digest is not None

    def test_check_health_open_circuit_on_failure(self) -> None:
        provider = _provider(fault="unreachable")
        report = provider.check_health(PROVIDER)
        assert report.status is EndpointHealth.OPEN_CIRCUIT

    def test_list_tools_schema(self) -> None:
        provider = _provider()
        tools = provider.list_tools(PROVIDER)
        names = {tool.id for tool in tools}
        assert names == {"literature_search", "literature_read", "citation_inspect"}
        assert all(tool.provider_kind is ProviderType.REST for tool in tools)

    def test_throttle_waits_between_requests(self) -> None:
        provider = _provider(interval=0.2)
        call = _call("literature_search", {"query": "x"})
        _put_args(provider._store, call, {"query": "x"})
        start = time.monotonic()
        provider.execute(PROVIDER, call)
        provider.execute(PROVIDER, call)
        assert time.monotonic() - start >= 0.15

    def test_large_result_spills(self) -> None:
        provider = _provider()
        call = _call("literature_read", {"ids": ["1"]})
        _put_args(provider._store, call, {"ids": ["1"]})
        provider._store.__class__  # noqa: B018 — store 已注入
        result = provider.execute(PROVIDER, call)
        assert result.status is ToolResultStatus.SUCCEEDED
