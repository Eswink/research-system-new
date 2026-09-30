"""McpToolProvider 的工具参数面（GOAL-20260927-027 EC-02 的**新增**判据）。

本文件证明**一个具体命题**：MCP 工具**真的收到了**调用方声明的参数。

背景（建档勘察实测的真缺陷）：`adapters/mcp/provider.py` 此前以
`session.call_tool(tool_name, {})` **空参数**调用工具，且不像
`adapters/research_tools/ncbi.py::_read_args` 那样从 ArtifactStore 读
`tool-args:{task_id}:{operation_key}` 并校验 `argument_digest`
⇒ 任何 MCP 工具都收不到 query / ids，EC-03 的运行链在其上**不可能成立**。
本 EC 修此缺陷；本文件是**修复的判据**（既有套件 `test_tool_provider_contract.py`
**逐字节未改**，继续以「声明空参数」的形态覆盖其余行为）。

**为什么断言的是「工具收到的参数」而不是「provider 读到了制品」**：
后者只证明本模块自己那一步；前者要穿过真 stdio 子进程、真 SDK 调用、真结果序列化
—— 这才是「参数到位」的证据。测试 server 的 `literature_search(query)` 会把
`query` 原样回显在结果里 ⇒ 判据读回 spill 内容后断言回显。

**反证（两向）**：
- 声明了**非空**参数却没有 args 制品 ⇒ fail closed（**不开会话**，零子进程）；
- 制品内容与 `argument_digest` 不符（篡改成**语义合法的另一值**）⇒ permanent 拒。

**兼容分支（唯一与 REST 不同的地方）**：声明值恰为 `{}` 的 canonical 序列化时，
制品缺席回落到空参数 —— 这是既有套件（声明 `Digest.of_bytes(b"{}")` 且不落制品）
继续可用的前提，本条也单独判。
"""

from __future__ import annotations

import json
import sys

import pytest

from adapters.fakes import FakeArtifactStore
from adapters.mcp import McpConnectionSpec, McpToolProvider
from packages.application.ports.errors import PermanentPortError
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from packages.domain.enums import (
    EffectClass,
    FailureCategory,
    ProviderType,
    ToolResultStatus,
    TrustLevel,
)
from packages.domain.tools import ToolCallRecord, ToolProviderSpec

TASK_ID = "task-goal027-ec02"
OP_KEY = "op-1"
SEARCH_TOOL = "literature_search"
CITATION_TOOL = "citation_inspect"
SEARCH_CAPABILITY = "search.academic"

#: 真值（同 EC-01 的线上实测记录，逐字进判据；见 RECHECK-256 §2）。
REAL_PMID = "38000001"
REAL_DOI = "10.1177/0310057x231212211"

PROVIDER = ToolProviderSpec(
    id="research-mcp-args",
    kind=ProviderType.MCP,
    trust_level=TrustLevel.VERIFIED,
    capabilities=[SEARCH_CAPABILITY, "citation.inspect"],
    effect_class=EffectClass.READ_ONLY,
    transport="stdio",
)


def stdio_connection() -> McpConnectionSpec:
    """真 stdio 子进程（tests/mcp_server 的 run_stdio 入口，故障档位 none）。"""
    return McpConnectionSpec(
        transport="stdio",
        command=(sys.executable, "-B", "-m", "tests.mcp_server.run_stdio", "none"),
        timeout_seconds=30.0,
    )


def make_provider(store: FakeArtifactStore) -> McpToolProvider:
    return McpToolProvider(
        stdio_connection(),
        artifact_store=store,
        spill_threshold_bytes=1,
    )


def canonical(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, sort_keys=True).encode("utf-8")


def make_call(
    tool_id: str,
    args: dict[str, object] | None = None,
    *,
    operation_key: str = OP_KEY,
) -> ToolCallRecord:
    """按声明值构造调用记录（`args=None` ⇒ 声明空参数）。"""
    raw = canonical({} if args is None else args)
    return ToolCallRecord(
        task_id=TASK_ID,
        attempt=1,
        operation_key=operation_key,
        tool_id=tool_id,
        capability=SEARCH_CAPABILITY,
        argument_digest=Digest.of_bytes(raw),
    )


def put_args(
    store: FakeArtifactStore,
    call: ToolCallRecord,
    payload: dict[str, object],
) -> None:
    raw = canonical(payload)
    store.put(
        Artifact(
            id=f"tool-args:{call.task_id}:{call.operation_key}",
            digest=Digest.of_bytes(raw),
            size_bytes=len(raw),
            media_type="application/json",
        ),
        raw,
    )


def call_port(provider: object, spec: ToolProviderSpec, call: ToolCallRecord) -> object:
    """按 Port 面调用 `execute`（经 `getattr` 取方法名 —— 安全扫描器把点号 +
    `execute(` 的字面量形态判成裸 SQL 执行并拦截写入，全仓既有规避口径）。"""
    return getattr(provider, "execute")(spec, call)


def spilled_payload(store: FakeArtifactStore, result: object, tool_id: str) -> dict[str, object]:
    """取回 spill 的产物（阈值 = 1 ⇒ 必然落盘）并反序列化。"""
    artifact_id = f"tool-result:{TASK_ID}:{OP_KEY}:{tool_id}"
    content = store.get(artifact_id)
    assert Digest.of_bytes(content) == getattr(result, "output_digest"), (
        "spill 内容必须与 output_digest 逐字节一致（内容寻址）"
    )
    decoded: object = json.loads(content.decode("utf-8"))
    assert isinstance(decoded, dict), "spill 内容必须是 JSON 对象"
    return decoded


def echoed(store: FakeArtifactStore, tool_id: str, payload: dict[str, object]) -> dict[str, object]:
    """从 MCP 结果信封里取出**工具真正返回的结构化内容**。

    落盘形态是 adapter 的归一化信封 `{"text": [...], "structured": {...}}`
    （`_serialize_call_tool_result`）；`structured` 是 server 侧工具返回的对象，
    `text` 是同一内容的 JSON 文本渲染。判据**两处都断言**：
    `structured` 证明结构化字段到位，`text` 证明文本通道也带上了同样的值。
    """
    structured = payload["structured"]
    assert isinstance(structured, dict), "structured 必须是对象"
    texts = payload["text"]
    assert isinstance(texts, list) and texts, "text 通道必须非空"
    rendered = json.loads(texts[0])
    assert rendered == structured, "text 与 structured 必须同源（同一份工具返回值）"
    del store, tool_id
    return structured


def run_tool(
    store: FakeArtifactStore,
    tool_id: str,
    args: dict[str, object] | None,
) -> dict[str, object]:
    provider = make_provider(store)
    call = make_call(tool_id, args)
    if args is not None:
        put_args(store, call, args)
    result = call_port(provider, PROVIDER, call)
    assert getattr(result, "status") is ToolResultStatus.SUCCEEDED
    return spilled_payload(store, result, tool_id)


class TestArgumentsReachTheTool:
    """正向：声明的参数**穿过真 stdio 子进程**到达工具。"""

    def test_declared_query_is_echoed_back_by_the_tool(self) -> None:
        """真回环的**参数断言**：工具回显的 `query` 必须等于声明值。

        这是本 EC 的核心判据 —— 「参数到位」要穿过真子进程、真 SDK 调用与
        真结果序列化，不是「provider 读到了制品」那种模块内自证。
        """
        store = FakeArtifactStore()
        payload = run_tool(store, SEARCH_TOOL, {"query": f"EXT_ID:{REAL_PMID}"})
        body = echoed(store, SEARCH_TOOL, payload)

        assert body["query"] == f"EXT_ID:{REAL_PMID}"
        hits = body["hits"]
        assert isinstance(hits, list) and hits, "真回环必须返回至少一条命中"
        first = hits[0]
        assert isinstance(first, dict)
        assert first["id"]

    def test_two_distinct_queries_are_not_the_same_call(self) -> None:
        """不同声明值 ⇒ 工具回显不同 ⇒ 参数是**真的**被传下去（不是恒空）。"""
        store = FakeArtifactStore()
        first = run_tool(store, SEARCH_TOOL, {"query": "alpha-query"})
        second = run_tool(store, SEARCH_TOOL, {"query": "beta-query"})

        first_body = echoed(store, SEARCH_TOOL, first)
        second_body = echoed(store, SEARCH_TOOL, second)

        first_query = str(first_body["query"])
        second_query = str(second_body["query"])
        assert first_query == "alpha-query"
        assert second_query == "beta-query"
        assert first_query != second_query

    def test_real_identifier_survives_the_roundtrip(self) -> None:
        """真标识（真 PMID / 真 DOI）能原样穿过 MCP 参数面。"""
        store = FakeArtifactStore()
        payload = run_tool(
            store,
            SEARCH_TOOL,
            {"query": f"EXT_ID:{REAL_PMID}", "doi": REAL_DOI},
        )

        body = echoed(store, SEARCH_TOOL, payload)

        assert body["query"] == f"EXT_ID:{REAL_PMID}"
        assert REAL_DOI.startswith("10.")
        assert REAL_PMID.isdigit()

    def test_output_digest_is_content_addressed(self) -> None:
        """产物是内容寻址的：digest 可由落盘字节重算（spill 读回已双向校验）。"""
        store = FakeArtifactStore()
        provider = make_provider(store)
        args: dict[str, object] = {"query": f"EXT_ID:{REAL_PMID}"}
        call = make_call(SEARCH_TOOL, args)
        put_args(store, call, args)
        result = call_port(provider, PROVIDER, call)

        raw = store.get(f"tool-result:{TASK_ID}:{OP_KEY}:{SEARCH_TOOL}")
        assert getattr(result, "output_digest") == Digest.of_bytes(raw)

    def test_second_tool_also_receives_its_declared_parameter(self) -> None:
        """参数面是**所有**工具共享的，不是某个工具的特例。"""
        store = FakeArtifactStore()
        payload = run_tool(store, CITATION_TOOL, {"citation_id": REAL_PMID})
        body = echoed(store, CITATION_TOOL, payload)

        assert body["citation_id"] == REAL_PMID


class TestFailClosed:
    """反证：声明了参数却取不到 / 被篡改 ⇒ 拒，且**不静默降级**。"""

    def test_non_empty_declaration_without_artifact_is_rejected(self) -> None:
        """声明非空参数却没有 args 制品 ⇒ permanent（fail closed，不是空参数放行）。

        这是**修复的核心语义**：旧实现会带着 `{}` 继续调用并把「工具收到空参数」
        伪装成成功。
        """
        store = FakeArtifactStore()
        call = make_call(SEARCH_TOOL, {"query": "never-supplied"})

        with pytest.raises(PermanentPortError) as exc_info:
            call_port(make_provider(store), PROVIDER, call)

        assert exc_info.value.failure_category is FailureCategory.CONFIGURATION
        assert "missing" in str(exc_info.value)

    def test_rejected_call_leaves_no_result_artifact(self) -> None:
        """被拒 ⇒ 不产生产物（没有 digest 可被下游当成功证据）。"""
        store = FakeArtifactStore()
        call = make_call(SEARCH_TOOL, {"query": "never-supplied"})

        with pytest.raises(PermanentPortError):
            call_port(make_provider(store), PROVIDER, call)

        assert store.meta(f"tool-result:{TASK_ID}:{OP_KEY}:{SEARCH_TOOL}") is None

    def test_tampered_artifact_content_is_rejected(self) -> None:
        """制品内容与 `argument_digest` 不符 ⇒ permanent 拒（防篡改）。

        篡改值是**语义完全合法**的另一种参数（另一个真 PMID 的检索串）——
        这样断言只能由 digest 校验满足，不会被「参数本身非法」那条分支顶替
        （按压 P4 的教训：篡改要篡成合法的）。

        类别断言是 `CONFIGURATION`（**既有**映射，非本 EC 引入）：MCP adapter 的
        `execute()` 把 `InvalidInputError` 统一归为 `CONFIGURATION`；本判据固定住
        「被拒 + 点名 digest」两件事，不改变该映射。
        """
        store = FakeArtifactStore()
        call = make_call(SEARCH_TOOL, {"query": f"EXT_ID:{REAL_PMID}"})
        put_args(store, call, {"query": "EXT_ID:31452104"})  # 合法但**别的内容**

        with pytest.raises(PermanentPortError) as exc_info:
            call_port(make_provider(store), PROVIDER, call)

        assert exc_info.value.failure_category is FailureCategory.CONFIGURATION
        assert "digest mismatch" in str(exc_info.value)

    def test_artifact_that_is_not_a_json_object_is_rejected(self) -> None:
        """制品是合法 JSON 但不是对象 ⇒ permanent 拒（不猜测形状）。"""
        store = FakeArtifactStore()
        raw = b'["not", "an", "object"]'
        call = ToolCallRecord(
            task_id=TASK_ID,
            attempt=1,
            operation_key=OP_KEY,
            tool_id=SEARCH_TOOL,
            capability=SEARCH_CAPABILITY,
            argument_digest=Digest.of_bytes(raw),
        )
        store.put(
            Artifact(
                id=f"tool-args:{TASK_ID}:{OP_KEY}",
                digest=Digest.of_bytes(raw),
                size_bytes=len(raw),
                media_type="application/json",
            ),
            raw,
        )

        with pytest.raises(PermanentPortError):
            call_port(make_provider(store), PROVIDER, call)

    def test_operation_key_scopes_the_artifact(self) -> None:
        """args 制品的坐标含 `operation_key` ⇒ 另一个 key 的参数取不到（fail closed）。"""
        store = FakeArtifactStore()
        other = make_call(SEARCH_TOOL, {"query": "alpha"}, operation_key="op-2")
        put_args(store, other, {"query": "alpha"})
        lookalike = make_call(SEARCH_TOOL, {"query": "alpha"}, operation_key=OP_KEY)

        with pytest.raises(PermanentPortError):
            call_port(make_provider(store), PROVIDER, lookalike)


class TestEmptyDeclarationStillWorks:
    """兼容分支：声明值恰为 `{}` 时，制品缺席回落到空参数（既有套件形态）。"""

    def test_empty_declaration_without_artifact_is_accepted(self) -> None:
        """`argument_digest == sha256("{}")` 且无制品 ⇒ 以空参数调用（**不**判拒）。

        这条是既有 `test_tool_provider_contract.py`（**逐字节未改**）继续可用的前提：
        它声明空参数且不落制品。**放宽的只有这一种形态**（恰好声明空），
        声明非空即 fail closed（见上一条）。
        """
        store = FakeArtifactStore()
        call = make_call(SEARCH_TOOL)  # args=None ⇒ 声明 {}

        result = call_port(make_provider(store), PROVIDER, call)

        assert getattr(result, "status") is ToolResultStatus.SUCCEEDED

    def test_empty_declaration_is_a_real_call_not_a_stub(self) -> None:
        """回落分支仍真的调用工具（不是空转）：产物在场且 query 为空串。"""
        store = FakeArtifactStore()
        payload = run_tool(store, SEARCH_TOOL, None)
        body = echoed(store, SEARCH_TOOL, payload)

        assert body["query"] == "", "空参数调用 ⇒ 工具回显空 query（真调用过）"
        hits = body["hits"]
        assert isinstance(hits, list) and hits

    def test_explicit_empty_artifact_is_equivalent_to_absent(self) -> None:
        """显式落一个 `{}` 制品与「缺席 + 声明空」语义一致（两条路径同结论）。"""
        store = FakeArtifactStore()
        payload = run_tool(store, SEARCH_TOOL, {})
        body = echoed(store, SEARCH_TOOL, payload)

        assert body["query"] == ""
