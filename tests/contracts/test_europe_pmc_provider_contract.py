"""EuropePmcProvider 契约套件（离线；`httpx.MockTransport` 走**真解析**）。

GOAL-20260929-027 EC-01 的**新增**判据（既有判据一字未改）。本文件覆盖 Port 语义面：

1. **正向真取证**：MockTransport 返回**真实响应样本**（真 PMID / 真 DOI / 真标题，
   取自 Europe PMC 线上 REST 的实测记录），断言归一化产物里这些字段逐字相等，
   且 `ToolResultRecord.output_digest` == `Digest.of_bytes(原始产物 JSON)`（内容寻址可重算）。
2. **参数防篡改**：`tool-args:{task_id}:{operation_key}` 的内容 digest 必须等于
   `call.argument_digest`，否则判 permanent（与 `ncbi.py::_read_args` 同口径）。
3. **失败分类**：429/5xx ⇒ transient 可重试；响应体非 JSON ⇒ `TOOL_SCHEMA_MISMATCH`；
   JSON 合法但结构不符 ⇒ `VALIDATION_FAILURE`（两者都 permanent）。

URL 策略（触网前判 host）在 `test_europe_pmc_url_policy.py` 里单独判（同一 EC 的另一半）。
共享样本与装配辅助在 `tests/contracts/europe_pmc_support.py`（规模门：单文件 ≤ 450 行）。

口径边界（如实）：Europe PMC 检索**无需凭据** ⇒ 本套件**不**断言任何凭据注入面
（provider 不解析凭据，因此没有 token passthrough 通道可言）。真实网络调用不在本套件内。
"""

from __future__ import annotations

import json

import httpx
import pytest

from adapters.fakes import FakeArtifactStore
from adapters.research_tools.europe_pmc import EuropePmcConfig, EuropePmcProvider
from packages.application.ports.errors import PermanentPortError, TransientPortError
from packages.domain.core import Digest
from packages.domain.enums import EffectClass, FailureCategory, ProviderType, ToolResultStatus
from tests.contracts.europe_pmc_support import (
    CITATION_TOOL,
    GHOST_TOOL,
    OP_KEY,
    PROVIDER,
    QUERY_KEY,
    READ_TOOL,
    REAL_AUTHOR_STRING,
    REAL_DOI,
    REAL_JOURNAL,
    REAL_PMID,
    REAL_TITLE,
    REAL_YEAR,
    SEARCH_TOOL,
    SECOND_DOI,
    SECOND_PMID,
    SECOND_TITLE,
    TASK_ID,
    Transport,
    call_port,
    make_call,
    make_provider,
    put_args,
    read_args,
    real_record,
    run_tool,
    search_args,
    search_payload,
    second_record,
)


class TestRealFieldsAndDigest:
    """正向：真解析 ⇒ 真标识 + 真标题 + 可重算的内容寻址 digest。"""

    def test_search_returns_real_pmid_doi_and_title(self) -> None:
        store = FakeArtifactStore()
        transport = Transport({"EXT_ID": search_payload(real_record())})
        provider = make_provider(transport, store=store)
        result, payload = run_tool(provider, store, SEARCH_TOOL, search_args())

        assert transport.count > 0, "合法 host ⇒ 请求必须真的发出（正控制）"
        articles = payload["articles"]
        assert isinstance(articles, list) and len(articles) == 1
        article = articles[0]
        assert isinstance(article, dict)
        assert article["pmid"] == REAL_PMID
        assert article["doi"] == REAL_DOI
        assert article["title"] == REAL_TITLE
        assert article["journal"] == REAL_JOURNAL
        assert article["year"] == REAL_YEAR
        assert article["author_string"] == REAL_AUTHOR_STRING
        assert payload["count"] == 1
        assert payload["ids"] == [REAL_PMID]
        assert getattr(result, "status") is ToolResultStatus.SUCCEEDED

    def test_output_digest_is_content_addressed_and_recomputable(self) -> None:
        transport = Transport({"EXT_ID": search_payload(real_record())})
        store = FakeArtifactStore()
        provider = make_provider(transport, store=store)
        result, payload = run_tool(provider, store, SEARCH_TOOL, search_args())

        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        assert getattr(result, "output_digest") == Digest.of_bytes(raw), (
            "content-addressed digest 必须可由产物字节重算"
        )

    def test_read_returns_second_real_record(self) -> None:
        transport = Transport({"EXT_ID": search_payload(second_record())})
        store = FakeArtifactStore()
        provider = make_provider(transport, store=store)
        _result, payload = run_tool(provider, store, READ_TOOL, read_args())

        articles = payload["articles"]
        assert isinstance(articles, list) and len(articles) == 1
        article = articles[0]
        assert isinstance(article, dict)
        assert article["pmid"] == SECOND_PMID
        assert article["doi"] == SECOND_DOI
        assert article["title"] == SECOND_TITLE

    def test_search_returns_the_real_metadata_block_not_just_a_dict(self) -> None:
        """产物必须是**结构化真字段**（防止「返回了 dict」式的空断言）。"""
        transport = Transport({"EXT_ID": search_payload(real_record())})
        store = FakeArtifactStore()
        provider = make_provider(transport, store=store)
        _result, payload = run_tool(provider, store, SEARCH_TOOL, search_args())

        assert set(payload) == {"query", "count", "ids", "articles"}
        assert payload[QUERY_KEY] == search_args()[QUERY_KEY]
        articles = payload["articles"]
        assert isinstance(articles, list) and len(articles) == 1
        article = articles[0]
        assert isinstance(article, dict)
        assert set(article) == {"pmid", "doi", "title", "journal", "year", "author_string"}
        assert REAL_DOI.startswith("10."), "DOI 前缀是真实标识的一部分"


class TestArgsAndFailures:
    """参数防篡改与失败分类（与 REST 适配器同口径）。"""

    def test_args_digest_mismatch_is_permanent(self) -> None:
        """被换掉的参数与 `argument_digest` 不符 ⇒ permanent 且**一次请求都不发**。

        篡改内容必须是**语义上完全合法**的另一种参数（换成另一个真 PMID 的检索串）：
        否则判据会被「参数本身非法」那条路径满足而掩盖住 digest 校验的缺失
        —— 按压 P4（删掉 digest 比对）实测过这个陷阱，本条因此额外断言
        **请求计数 == 0**（只有 digest 校验能在触网前拦住它）。
        """
        store = FakeArtifactStore()
        transport = Transport()
        provider = make_provider(transport, store=store)
        call = make_call(SEARCH_TOOL, search_args())
        put_args(store, call, search_args(pmid=SECOND_PMID))  # 合法但是**别的内容**

        with pytest.raises(PermanentPortError) as exc_info:
            call_port(provider, PROVIDER, call)

        assert exc_info.value.failure_category is FailureCategory.VALIDATION_FAILURE
        assert transport.count == 0, "digest 不符必须在触网前拒（不得先发请求）"

    def test_missing_args_artifact_is_permanent(self) -> None:
        store = FakeArtifactStore()
        provider = make_provider(store=store)
        call = make_call(SEARCH_TOOL, search_args())

        with pytest.raises(PermanentPortError):
            call_port(provider, PROVIDER, call)

    def test_unknown_tool_id_is_permanent(self) -> None:
        store = FakeArtifactStore()
        provider = make_provider(store=store)
        call = make_call(GHOST_TOOL, {})
        put_args(store, call, {})

        with pytest.raises(PermanentPortError):
            call_port(provider, PROVIDER, call)

    def test_the_two_declared_tools_are_the_only_ones(self) -> None:
        """声明的工具面就是这两个；`citation.inspect` 属 NCBI，本 provider 没有。"""
        store = FakeArtifactStore()
        provider = make_provider(store=store)
        tools = provider.list_tools(PROVIDER)
        ids = {tool.id for tool in tools}

        assert ids == {SEARCH_TOOL, READ_TOOL}
        assert CITATION_TOOL not in ids
        assert all(tool.provider_kind is ProviderType.REST for tool in tools)
        assert all(tool.effect_class is EffectClass.READ_ONLY for tool in tools)

    def test_empty_query_is_permanent_and_never_touches_network(self) -> None:
        transport = Transport()
        store = FakeArtifactStore()
        provider = make_provider(transport, store=store)
        args: dict[str, object] = {QUERY_KEY: "   "}
        call = make_call(SEARCH_TOOL, args)
        put_args(store, call, args)

        with pytest.raises(PermanentPortError):
            call_port(provider, PROVIDER, call)

        assert transport.count == 0, "入参非法 ⇒ 不得触网"

    def test_empty_ids_is_permanent_and_never_touches_network(self) -> None:
        transport = Transport()
        store = FakeArtifactStore()
        provider = make_provider(transport, store=store)
        args: dict[str, object] = {"ids": []}
        call = make_call(READ_TOOL, args)
        put_args(store, call, args)

        with pytest.raises(PermanentPortError):
            call_port(provider, PROVIDER, call)

        assert transport.count == 0

    def test_non_json_body_is_schema_mismatch(self) -> None:
        """响应体不是 JSON ⇒ `TOOL_SCHEMA_MISMATCH`（与 REST 适配器同口径）。"""

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="<not-json>")

        store = FakeArtifactStore()
        provider = EuropePmcProvider(
            store,
            config=EuropePmcConfig(min_request_interval_seconds=0.0),
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
            spill_threshold_bytes=1,
        )
        call = make_call(SEARCH_TOOL, search_args())
        put_args(store, call, search_args())

        with pytest.raises(PermanentPortError) as exc_info:
            call_port(provider, PROVIDER, call)

        assert exc_info.value.failure_category is FailureCategory.TOOL_SCHEMA_MISMATCH

    def test_malformed_envelope_is_permanent_validation_failure(self) -> None:
        """JSON 合法但结构不符 ⇒ `VALIDATION_FAILURE`（permanent，不可重试）。

        与上一条**不同的类别**是既有的分层：归一化层的结构校验抛
        `InvalidInputError`（`VALIDATION_FAILURE`），而 JSON 解码失败归
        `TOOL_SCHEMA_MISMATCH`。两者都**不可重试** —— 这条断言固定住该区分，
        防止有人把结构缺陷误降级成 transient 重试。
        """
        transport = Transport({"EXT_ID": {"unexpected": True}})
        store = FakeArtifactStore()
        provider = make_provider(transport, store=store)
        call = make_call(SEARCH_TOOL, search_args())
        put_args(store, call, search_args())

        with pytest.raises(PermanentPortError) as exc_info:
            call_port(provider, PROVIDER, call)

        assert exc_info.value.failure_category is FailureCategory.VALIDATION_FAILURE
        assert exc_info.value.retryable is False

    def test_transient_status_maps_to_retryable(self) -> None:
        """429 / 5xx ⇒ 可重试（与 REST 适配器同口径，不静默放行）。"""

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, text="unavailable")

        store = FakeArtifactStore()
        provider = EuropePmcProvider(
            store,
            config=EuropePmcConfig(min_request_interval_seconds=0.0),
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
            spill_threshold_bytes=1,
        )
        call = make_call(SEARCH_TOOL, search_args())
        put_args(store, call, search_args())

        with pytest.raises(TransientPortError) as exc_info:
            call_port(provider, PROVIDER, call)

        assert exc_info.value.retryable is True
        assert exc_info.value.failure_category is FailureCategory.TOOL_UNAVAILABLE

    def test_timeout_maps_to_tool_timeout(self) -> None:
        """超时 ⇒ `TOOL_TIMEOUT`（transient，可重试）。"""

        def handler(_request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectTimeout("injected timeout")

        store = FakeArtifactStore()
        provider = EuropePmcProvider(
            store,
            config=EuropePmcConfig(min_request_interval_seconds=0.0),
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
            spill_threshold_bytes=1,
        )
        call = make_call(SEARCH_TOOL, search_args())
        put_args(store, call, search_args())

        from packages.application.ports.errors import PortTimeoutError

        with pytest.raises(PortTimeoutError) as exc_info:
            call_port(provider, PROVIDER, call)

        assert exc_info.value.failure_category is FailureCategory.TOOL_TIMEOUT
        assert exc_info.value.retryable is True

    def test_operation_key_participates_in_the_args_artifact_id(self) -> None:
        """操作键是参数制品的唯一坐标：另一个 key 读不到本 key 的参数（零请求被拒）。"""
        transport = Transport()
        store = FakeArtifactStore()
        provider = make_provider(transport, store=store)
        other = make_call(SEARCH_TOOL, search_args(), operation_key="op-2")
        put_args(store, other, search_args())
        lookalike = make_call(SEARCH_TOOL, search_args(), operation_key=OP_KEY)

        with pytest.raises(PermanentPortError):
            call_port(provider, PROVIDER, lookalike)

        assert transport.count == 0

    def test_store_scope_is_the_injected_fixture_store(self) -> None:
        """判据断言的是 provider 实际使用的那一个 store（防装配错位）。"""
        store = FakeArtifactStore()
        provider = make_provider(store=store)
        call = make_call(SEARCH_TOOL, search_args())
        put_args(store, call, search_args())
        result = call_port(provider, PROVIDER, call)

        assert getattr(result, "task_id") == TASK_ID
        assert getattr(result, "operation_key") == OP_KEY
