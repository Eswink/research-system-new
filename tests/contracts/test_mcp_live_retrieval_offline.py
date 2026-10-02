"""GOAL-028 EC-02 判据：**活检索**（真实上游模式 + 非预置语料正反两向 + 离线零出站）。

**被测对象**：自建 MCP server 的**第二条路**（`tools/research_mcp_live.py`）——
真打 Europe PMC REST、复用既有 provider 的限速与归一化、遵守**触网前** URL 策略，
且**仍走 MCP 协议往返**（同一对工具名）。默认（冻结）路径由 GOAL-027 的三份判据承担，
本文件**不重复**它们。

**四件事逐条取证**：

1. **非预置语料（正向）**：判据喂入与树内冻结语料**不相交**的上游响应（专属 PMID），
   经真协议栈 + 真解析取回**上游那条**（真标识 + 内容寻址 digest 重算相等）；
2. **非预置语料（反向）**：同一标识在**冻结模式**下取不到（在 `missing` 里点名）——
   两向合起来才证「非预置」，只证正向可能是巧合；
3. **触网前 URL 策略**：host 不在声明域名内 / 非 http(s) / 保留类地址 ⇒ **零请求**；
4. **离线零出站**：默认（未开关）模式**不构造任何 client**、请求计数恒 0；
   本文件所有用例都在 `MockTransport` 上跑（`tests/egress_guard.py` 的默认 deny 不变）。

**为什么用 `httpx.MockTransport` 而不是真出网**：默认门必须离线（AGENTS.md §9）；
MockTransport 让「真协议栈 + 真解析 + 真策略」全程可测，只把**最外层 socket** 换掉。
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import httpx
import pytest

_ROOT = Path(__file__).resolve().parents[2]
_LIVE_PATH = _ROOT / "tools" / "research_mcp_live.py"
_SERVER_PATH = _ROOT / "tools" / "research_mcp_server.py"

#: **与树内冻结语料不相交**的专属标识（判据断言两件事都要成立：
#: 正向取得到它 / 反向取不到它）。取一个冻结语料里不存在的 PMID。
_LIVE_ONLY_PMID = "99000001"
_LIVE_ONLY_DOI = "10.9999/goal028.live.1"
_LIVE_ONLY_TITLE = "Live-upstream-only record for GOAL-028 EC-02"
#: 冻结语料里**确实存在**的标识（反向臂的第二面：活模式下取得到、冻结模式下也取得到，
#: 证明两模式**同形**而不是另一条路完全不可用）。
_CORPUS_PMID = "42796516"


def _load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def live_module() -> Any:
    return _load(_LIVE_PATH, "goal028_live_under_test")


def _upstream_payload(pmid: str, doi: str, title: str) -> dict[str, object]:
    """上游响应的**真形状**（Europe PMC `resultList.result[]`；字段名逐字对齐官方文档）。"""
    return {
        "version": "6.9",
        "hitCount": 1,
        "resultList": {
            "result": [
                {
                    "pmid": pmid,
                    "doi": doi,
                    "title": title,
                    "journalTitle": "Journal of Live Retrieval",
                    "pubYear": "2026",
                    "authorString": "Doe J, Roe R.",
                }
            ]
        },
    }


def _settings(
    live_module: Any, payload: dict[str, object], *, domains: tuple[str, ...] | None = None
) -> Any:
    """活检索设置 + MockTransport（记录请求，供零请求反证读取计数）。"""
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = live_module.LiveSettings(client=client, declared_domains=domains)
    settings.requests = requests  # 判据侧记录句柄（LiveSettings 不关心它）
    return settings


class TestTheLivePathReturnsUpstreamCorpus:
    """正向：喂入**与树内语料不相交**的上游响应 ⇒ 取回上游那条（真标识 + digest）。"""

    def test_search_returns_the_upstream_record_not_a_local_one(self, live_module: Any) -> None:
        settings = _settings(
            live_module, _upstream_payload(_LIVE_ONLY_PMID, _LIVE_ONLY_DOI, _LIVE_ONLY_TITLE)
        )
        out = live_module.live_search(settings, "live upstream only", 5)

        assert out["ids"] == [_LIVE_ONLY_PMID], out
        record = out["articles"][0]
        assert record["doi"] == _LIVE_ONLY_DOI, record
        assert record["title"] == _LIVE_ONLY_TITLE, record
        assert record["journal"] == "Journal of Live Retrieval", record
        assert record["year"] == "2026", record

    def test_the_record_digest_is_content_addressed(self, live_module: Any) -> None:
        """内容寻址：digest **重算**必须相等（不是搬运一个声明值）。"""
        settings = _settings(
            live_module, _upstream_payload(_LIVE_ONLY_PMID, _LIVE_ONLY_DOI, _LIVE_ONLY_TITLE)
        )
        out = live_module.live_search(settings, "live upstream only", 5)
        record = out["articles"][0]

        from packages.domain.core import Digest

        recomputed = str(
            Digest.of_bytes(
                json.dumps(dict(record), ensure_ascii=False, sort_keys=True).encode("utf-8")
            )
        )
        assert live_module.record_digest(record) == recomputed, record
        assert recomputed.startswith("sha256:"), recomputed

    def test_read_returns_the_upstream_record_by_id(self, live_module: Any) -> None:
        settings = _settings(
            live_module, _upstream_payload(_LIVE_ONLY_PMID, _LIVE_ONLY_DOI, _LIVE_ONLY_TITLE)
        )
        out = live_module.live_read(settings, [_LIVE_ONLY_PMID])

        assert out["ids"] == [_LIVE_ONLY_PMID], out
        assert out["missing"] == [], out
        assert out["articles"][0]["doi"] == _LIVE_ONLY_DOI, out


class TestTheCorpusIsNotPreloaded:
    """反向：同一标识在**冻结模式**下取不到 —— 两向合起来才证「语料非预置」。"""

    def test_the_live_only_id_is_absent_from_the_frozen_corpus(self) -> None:
        """前提事实：专属标识**不在**树内冻结语料里（否则正向臂证明不了任何事）。"""
        server = _load(_SERVER_PATH, "goal028_server_for_corpus")
        pmids = {record["pmid"] for record in server.CORPUS}
        assert _LIVE_ONLY_PMID not in pmids, sorted(pmids)
        assert _CORPUS_PMID in pmids, sorted(pmids)

    def test_the_frozen_mode_cannot_return_the_live_only_id(self) -> None:
        """冻结模式下同一个 id 在 `missing` 里被**点名**（不编造、不顶替）。"""
        server = _load(_SERVER_PATH, "goal028_server_frozen_mode")
        out = server._read_records([_LIVE_ONLY_PMID])
        assert out["ids"] == [], out
        assert out["missing"] == [_LIVE_ONLY_PMID], out

    def test_both_modes_are_shape_compatible(self, live_module: Any) -> None:
        """两模式**同形**：从上游取的记录，字段集与冻结语料**逐字相同**。

        判据喂的上游响应**逐字取自**冻结语料里那条真记录（title/doi/journal/... 全部照抄），
        于是断言的是「活模式解析出的形状与冻结模式**一致**」——同一条记录经两条路，
        产出必须相等。若活模式少了键 / 改了字段名 / 换了大小写，这里即红。
        """
        server = _load(_SERVER_PATH, "goal028_server_shape")
        frozen = dict(server._read_records([_CORPUS_PMID])["articles"][0])
        settings = _settings(
            live_module,
            _upstream_payload(_CORPUS_PMID, str(frozen["doi"]), str(frozen["title"])),
            domains=("www.ebi.ac.uk",),
        )
        out = live_module.live_read(settings, [_CORPUS_PMID])
        upstream = dict(out["articles"][0])
        assert set(upstream) == set(frozen), (sorted(upstream), sorted(frozen))
        # 上游响应里逐字照抄的字段必须原样回来（journal/year 由 payload 固定，故单独对齐）。
        for field in ("pmid", "doi", "title"):
            assert upstream[field] == frozen[field], (field, upstream, frozen)


class TestTheUrlPolicyRunsBeforeAnyRequest:
    """触网前策略：三类拒绝各自**零请求**（不是「请求后被拒」）。"""

    @pytest.mark.parametrize(
        ("domains", "reason"),
        [
            ((), "empty declaration"),
            (("example.invalid",), "host outside declaration"),
        ],
    )
    def test_a_host_outside_the_declaration_is_refused_with_zero_requests(
        self, live_module: Any, domains: tuple[str, ...], reason: str
    ) -> None:
        settings = _settings(live_module, _upstream_payload("1", "d", "t"), domains=domains)
        with pytest.raises(Exception) as caught:
            live_module.live_search(settings, "q", 1)
        assert settings.requests == [], (reason, "拒绝必须发生在触网之前")
        assert "declared network_domains" in str(caught.value), (reason, str(caught.value))

    def test_the_declared_domain_is_allowed_and_reaches_the_transport(
        self, live_module: Any
    ) -> None:
        """正控制：合法 host ⇒ 请求**真的发出**（否则上面的零请求断言可能是空真）。"""
        settings = _settings(
            live_module,
            _upstream_payload(_LIVE_ONLY_PMID, _LIVE_ONLY_DOI, _LIVE_ONLY_TITLE),
            domains=("www.ebi.ac.uk",),
        )
        out = live_module.live_search(settings, "q", 1)
        assert len(settings.requests) == 1, settings.requests
        assert settings.requests[0].url.host == "www.ebi.ac.uk", settings.requests[0].url
        assert out["ids"] == [_LIVE_ONLY_PMID], out


class TestTheDefaultModeStaysOffline:
    """默认（未开关）模式：不构造 client、零请求、行为逐字节等于冻结语料。"""

    def test_without_the_switch_there_is_no_live_settings(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("RESEARCHOS_MCP_LIVE_RETRIEVAL", raising=False)
        server = _load(_SERVER_PATH, "goal028_server_default_mode")
        assert server._live_settings() is None

    def test_a_non_unit_switch_value_does_not_enable_live(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """开关值必须恰为 `"1"`（与仓内既有 live 开关口径一致；`true`/`yes` 不算）。"""
        server = _load(_SERVER_PATH, "goal028_server_switch_values")
        for value in ("true", "yes", "0", ""):
            monkeypatch.setenv("RESEARCHOS_MCP_LIVE_RETRIEVAL", value)
            assert server._live_settings() is None, value

    def test_the_frozen_default_still_serves_the_corpus(self) -> None:
        server = _load(_SERVER_PATH, "goal028_server_still_frozen")
        out = server._search_records("molecular docking", 5)
        assert _CORPUS_PMID in out["ids"], out
        assert _LIVE_ONLY_PMID not in out["ids"], out


class TestTheLivePathGoesThroughTheMcpProtocol:
    """活检索**仍走 MCP 协议往返**（不是绕开协议直接调函数）。

    做法：起一个**活模式**的 server（`build_server(live=...)`，client 是 MockTransport），
    用 SDK 的 in-memory 会话（`create_connected_server_and_client_session`）真握手、
    真 `call_tool` —— 客户端看到的就只有两个**工具名**与一份 JSON 结果，
    与冻结模式经 stdio 时的界面完全一致。这就是「同一个 server、同一对工具名」的取证。
    """

    def test_call_tool_returns_the_upstream_record_over_the_protocol(
        self, live_module: Any
    ) -> None:
        import asyncio

        from mcp.shared.memory import create_connected_server_and_client_session

        server = _load(_SERVER_PATH, "goal028_server_live_protocol")
        settings = _settings(
            live_module,
            _upstream_payload(_LIVE_ONLY_PMID, _LIVE_ONLY_DOI, _LIVE_ONLY_TITLE),
            domains=("www.ebi.ac.uk",),
        )
        built = server.build_server(live=settings)

        async def _round_trip() -> tuple[list[str], dict[str, object]]:
            async with create_connected_server_and_client_session(
                built._mcp_server
            ) as session:
                await session.initialize()
                listing = await session.list_tools()
                result = await session.call_tool(
                    "literature_search", {"query": "live upstream only", "limit": 5}
                )
                return [tool.name for tool in listing.tools], json.loads(result.content[0].text)

        names, payload = asyncio.run(_round_trip())
        assert names == ["literature_search", "literature_read"], names
        assert payload["ids"] == [_LIVE_ONLY_PMID], payload
        assert payload["articles"][0]["doi"] == _LIVE_ONLY_DOI, payload

    def test_the_frozen_server_keeps_the_same_tool_surface(
        self, live_module: Any
    ) -> None:
        """对照：**冻结**模式（缺省）的工具面与活模式**逐字相同** —— 只是数据来源不同。"""
        import asyncio

        from mcp.shared.memory import create_connected_server_and_client_session

        server = _load(_SERVER_PATH, "goal028_server_frozen_protocol")
        built = server.build_server()

        async def _tools() -> list[str]:
            async with create_connected_server_and_client_session(
                built._mcp_server
            ) as session:
                await session.initialize()
                listing = await session.list_tools()
                return [tool.name for tool in listing.tools]

        assert asyncio.run(_tools()) == ["literature_search", "literature_read"]
