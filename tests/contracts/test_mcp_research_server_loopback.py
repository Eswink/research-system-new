"""GOAL-20260927-027 EC-02 判据 A：**真回环** —— 生产 adapter 真连自建 MCP server。

被测对象是**生产那条链**，不是夹具：`McpToolProvider`（`adapters/mcp/provider.py`）
以 stdio 真起子进程（`sys.executable -B tools/research_mcp_server.py`）、真调工具、
真取结果。判据只经 Port 面（`list_tools` / `execute` / `check_health`），不 import
server 内部函数来"造"结果——server 是独立进程，与 adapter 之间只有 stdio 契约
（唯一例外：两条用例把冻结语料读回来**对照**断言，方向是判据 → 语料，不是反过来）。

**净增量**（本文件相对既有 `tests/contracts/test_tool_provider_contract.py` 多测的东西；
既有套件逐字节未改、也不重复它已覆盖的 mock 工具面）：

1. **工具名与 `literature.search` / `literature.read` 对齐**（EC-02 ③ 第一句）；
2. **结果含真标识**：真 PMID / 真 DOI / 真标题（逐字常量 + 与冻结语料逐条互证）；
3. **内容寻址 digest**：spill 字节重算 == `output_digest`（连同 `text[]` 与
   `structured` 信封一致性）；
4. **参数真的到达 server**：两个不同 query ⇒ 两组不同结果（空参数缺陷的反证面）；
   同 query 两次 ⇒ digest 逐字节相同（server 无时钟、无随机 ⇒ 确定性）；
5. **读取步往返**：读的是检索结果里出现的 id；不存在的 id 被**点名**在 `missing`
   （绝不编造、绝不用别的记录顶替）；两条路径取回的同一条记录逐字段相等。
"""

from __future__ import annotations

from packages.domain.enums import ProviderType, ToolResultStatus
from tests.contracts.mcp_research_support import (
    DOCKING_IDS,
    MISSING_PMID,
    OP_ALT,
    OP_READ,
    OP_SEARCH,
    PROVIDER,
    QUERY_CARBON,
    QUERY_DOCKING,
    READ_CAPABILITY,
    READ_TOOL,
    REAL_DOI,
    REAL_PMID,
    REAL_TITLE,
    SEARCH_DOI,
    SEARCH_PMID,
    SEARCH_TOOL,
    ToolInvocation,
    article_list,
    call_port,
    id_list,
    int_field,
    make_call,
    make_provider,
    put_args,
    result_content,
    result_of,
    run_tool,
    structured_payload,
    text_field,
)

#: `QUERY_CARBON` 应在冻结语料里命中的三条真记录（Br J Anaesth ×2 + Anaesthesia）。
CARBON_IDS = ("42665486", "42613204", "42775559")


class TestToolSurface:
    """list_tools / check_health：声明面是真 server 给的，不是本地常量。"""

    def test_tool_names_align_with_the_literature_capabilities(self) -> None:
        provider, _store = make_provider()
        tools = provider.list_tools(PROVIDER)
        assert {tool.id for tool in tools} == {SEARCH_TOOL, READ_TOOL}
        for tool in tools:
            assert tool.provider_kind is ProviderType.MCP
            assert tool.effect_class is PROVIDER.effect_class
            assert set(tool.capabilities) == set(PROVIDER.capabilities)

    def test_health_probe_reports_healthy_with_a_stable_schema_digest(self) -> None:
        provider, _store = make_provider()
        first = provider.check_health(PROVIDER)
        second = provider.check_health(PROVIDER)
        assert str(first.status) == "HEALTHY", first.detail
        assert first.observed_schema_digest is not None
        assert str(first.observed_schema_digest) == str(second.observed_schema_digest), (
            "确定性 server 两次探测的 schema 指纹必须相同"
        )

    def test_unknown_tool_is_named_by_the_server_side_not_stubbed_locally(self) -> None:
        """不存在的工具由 server 回绝（消息来自子进程）⇒ 证明真调了真进程。"""
        provider, store = make_provider()
        call = make_call("ghost_tool", {}, "op-ghost")
        put_args(store, call, {})
        result = result_of(call_port(provider, PROVIDER, call))
        assert result.status is ToolResultStatus.FAILED
        message = str(result.error_message_redacted)
        assert "Unknown tool" in message and "ghost_tool" in message, message


class TestSearchResults:
    """检索：真标识 + 内容寻址 + 与冻结语料逐条互证。"""

    def test_search_returns_the_real_records(self) -> None:
        provider, store = make_provider()
        payload = run_tool(
            provider, store, ToolInvocation(SEARCH_TOOL, {"query": QUERY_DOCKING}, OP_SEARCH)
        )
        assert text_field(payload, "query") == QUERY_DOCKING
        assert int_field(payload, "hitCount") == len(DOCKING_IDS)
        assert id_list(payload) == DOCKING_IDS
        first = article_list(payload)[0]
        assert first["pmid"] == SEARCH_PMID
        assert first["doi"] == SEARCH_DOI

    def test_the_declared_literals_match_the_frozen_corpus(self) -> None:
        """本文件逐字断言的 REAL_* 常量必须与 server 语料里的那条记录一致。"""
        from tools.research_mcp_server import CORPUS

        by_id = {record["pmid"]: record for record in CORPUS}
        record = by_id[REAL_PMID]
        assert record["doi"] == REAL_DOI
        assert record["title"] == REAL_TITLE

    def test_search_result_matches_the_corpus_record_for_record(self) -> None:
        """工具面搬回来的记录 == 语料声明的那几条（逐条、逐字段，按声明顺序）。"""
        from tools.research_mcp_server import CORPUS

        provider, store = make_provider()
        payload = run_tool(
            provider, store, ToolInvocation(SEARCH_TOOL, {"query": QUERY_DOCKING}, OP_SEARCH)
        )
        expected = [record for record in CORPUS if record["pmid"] in DOCKING_IDS]
        assert [dict(item) for item in article_list(payload)] == expected
        assert REAL_PMID in id_list(payload)


class TestArgumentRoundTrip:
    """参数真的到达 server（空参数缺陷的反证面）+ 同一输入确定性。"""

    def test_two_queries_yield_two_different_result_sets(self) -> None:
        provider, store = make_provider()
        docking = run_tool(
            provider, store, ToolInvocation(SEARCH_TOOL, {"query": QUERY_DOCKING}, OP_SEARCH)
        )
        carbon = run_tool(
            provider, store, ToolInvocation(SEARCH_TOOL, {"query": QUERY_CARBON}, OP_ALT)
        )
        assert id_list(docking) != id_list(carbon), (
            "不同 query 必须取回不同结果（空参数会让两者相同）"
        )
        assert int_field(carbon, "hitCount") == len(CARBON_IDS)
        assert set(id_list(carbon)) == set(CARBON_IDS)

    def test_identical_inputs_produce_identical_bytes(self) -> None:
        """同 query 两次调用 ⇒ spill 字节逐字节相同（确定性 server，无时钟无随机）。"""
        provider, store = make_provider()
        args: dict[str, object] = {"query": QUERY_DOCKING}
        first = make_call(SEARCH_TOOL, args, OP_SEARCH)
        put_args(store, first, args)
        result_a = result_of(call_port(provider, PROVIDER, first))
        second = make_call(SEARCH_TOOL, args, OP_ALT)
        put_args(store, second, args)
        result_b = result_of(call_port(provider, PROVIDER, second))
        assert result_content(store, OP_SEARCH, SEARCH_TOOL) == result_content(
            store, OP_ALT, SEARCH_TOOL
        )
        assert str(result_a.output_digest) == str(result_b.output_digest)


class TestReadRoundTrip:
    """读取步：用检索结果里的 id 取回同一条记录；缺失 id 点名。"""

    def test_read_uses_the_searched_identifier_and_names_the_missing_one(self) -> None:
        provider, store = make_provider()
        searched = run_tool(
            provider, store, ToolInvocation(SEARCH_TOOL, {"query": QUERY_DOCKING}, OP_SEARCH)
        )
        identifier = id_list(searched)[0]
        read = run_tool(
            provider,
            store,
            ToolInvocation(
                READ_TOOL, {"ids": [identifier, MISSING_PMID]}, OP_READ, READ_CAPABILITY
            ),
        )
        assert id_list(read) == (identifier,)
        assert id_list(read, "missing") == (MISSING_PMID,)
        assert article_list(read) == article_list(searched)[:1], (
            "两条路径取回的同一条记录必须逐字段相等"
        )

    def test_read_result_is_content_addressed(self) -> None:
        provider, store = make_provider()
        payload = run_tool(
            provider,
            store,
            ToolInvocation(READ_TOOL, {"ids": [REAL_PMID]}, OP_READ, READ_CAPABILITY),
        )
        assert id_list(payload) == (REAL_PMID,)
        assert id_list(payload, "missing") == ()
        content = result_content(store, OP_READ, READ_TOOL)
        assert structured_payload(content) == payload

    def test_empty_arguments_are_rejected_not_silently_answered_empty(self) -> None:
        """空 ids / 空 query 由 server 回绝（工具错误），**不是**静默返回空结果。"""
        provider, store = make_provider()
        cases: tuple[tuple[str, dict[str, object]], ...] = (
            (READ_TOOL, {"ids": []}),
            (SEARCH_TOOL, {"query": ""}),
        )
        for tool_id, args in cases:
            call = make_call(tool_id, args, "op-empty")
            put_args(store, call, args)
            result = result_of(call_port(provider, PROVIDER, call))
            assert result.status is ToolResultStatus.FAILED, (tool_id, args)
