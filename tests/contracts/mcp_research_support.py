"""GOAL-20260927-027 EC-02 判据的共享支持件（真回环 / 注册面 / 三反证的共同底座）。

**为什么要单独成模块**：规模门禁对 `tests/**` 同样生效（单文件 ≤ 450 行、函数 ≤ 50 行），
而真回环与注册面两份判据共用同一批常量（真实标识、连接规格、参数装卸）与装配辅助。
本模块**不含任何用例**（文件名不以 `test_` 开头 ⇒ 不被收集），只放常量与纯辅助。

**真实标识口径**（承 EC-01 的同一纪律）：`REAL_*` 常量取自 `tools/research_mcp_server.py`
的冻结语料——那是 **2026-09-30 经 Europe PMC REST 实取**的真实发表记录（真 PMID、真 DOI、
真标题逐字保留）。判据断言的是语料**里**这些真标识能被工具面原样搬运，不是在线可达性。

**参数装卸与 EC-01 同形**：调用方写 `tool-args:{task_id}:{operation_key}`（JSON），
provider 读回并重算 digest 与 `call.argument_digest` 比对（内容寻址防篡改）。
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from adapters.fakes import FakeArtifactStore
from adapters.mcp import McpConnectionSpec, McpToolProvider
from packages.application.ports.artifact_store import ArtifactStore
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from packages.domain.enums import (
    EffectClass,
    ProviderType,
    ToolResultStatus,
    TrustLevel,
)
from packages.domain.tools import ToolCallRecord, ToolProviderSpec, ToolResultRecord

ROOT = Path(__file__).resolve().parents[2]
SERVER_PATH = ROOT / "tools" / "research_mcp_server.py"
SHAPELESS_FIXTURE = ROOT / "tests" / "mcp_server" / "raw_shapeless_tools.py"
ARGS_ARTIFACT_PREFIX = "tool-args:"

PROVIDER_ID = "research_mcp_tools"
SEARCH_TOOL = "literature_search"
READ_TOOL = "literature_read"
SEARCH_CAPABILITY = "literature.search"
READ_CAPABILITY = "literature.read"

TASK_ID = "task-goal027-ec02"
OP_SEARCH = "op-search"
OP_READ = "op-read"
OP_ALT = "op-alt"

#: 查询串：与冻结语料里的真实标题匹配（判据只断言**存在性**，不重实现检索算法）。
QUERY_DOCKING = "molecular docking"
QUERY_CARBON = "carbon footprint"
#: `QUERY_DOCKING` 的命中 id（语料顺序；与 EC-01 的检索口径同一夹具纪律）。
DOCKING_IDS = ("42803750", "42796516", "42740546", "42772441")
#: `QUERY_CARBON` 的命中 id（三条 Br J Anaesth / Anaesthesia 真记录）。
CARBON_IDS = ("42665486", "42613204", "42775559")

#: 真实标识（逐字取自冻结语料里的真实记录）。
REAL_PMID = "42796516"
REAL_DOI = "10.3390/molecules31183228"
REAL_TITLE = (
    "Molecular Docking of Natural Products: Critical Appraisal of "
    "Current Methodology and Practical Guidelines."
)
SEARCH_PMID = "42803750"
SEARCH_DOI = "10.1002/cns.71179"
#: 语料**不含**这个 id：读取必须点名缺失，绝不编造、绝不用别的记录顶替。
MISSING_PMID = "99999999"

#: 目录内该 provider 的规格（kind=MCP + stdio；离线路径不声明网络域与凭据）。
PROVIDER = ToolProviderSpec(
    id=PROVIDER_ID,
    kind=ProviderType.MCP,
    trust_level=TrustLevel.USER_APPROVED,
    capabilities=[SEARCH_CAPABILITY, READ_CAPABILITY],
    effect_class=EffectClass.READ_ONLY,
    transport="stdio",
)


def stdio_connection(script: Path = SERVER_PATH) -> McpConnectionSpec:
    """stdio 连接规格：`sys.executable -B <script>`（真子进程；离线）。"""
    return McpConnectionSpec(
        transport="stdio",
        command=(sys.executable, "-B", str(script)),
        timeout_seconds=60.0,
    )


def make_provider(
    script: Path = SERVER_PATH,
    *,
    store: ArtifactStore | None = None,
    spill_threshold_bytes: int = 1,
) -> tuple[McpToolProvider, ArtifactStore]:
    """构造 `McpToolProvider` 并返回它持有的 store（调用方要读回 spill 内容）。

    `spill_threshold_bytes=1`：任何非空结果都落 ArtifactStore ⇒ 判据能对 spill 内容
    重算 digest（默认 32KiB 阈值会让小响应只留内存 digest，读不到字节）。
    """
    artifacts = store if store is not None else FakeArtifactStore()
    provider = McpToolProvider(
        stdio_connection(script),
        artifact_store=artifacts,
        spill_threshold_bytes=spill_threshold_bytes,
    )
    return provider, artifacts


def make_call(
    tool_id: str, args: dict[str, object], operation_key: str, capability: str = SEARCH_CAPABILITY
) -> ToolCallRecord:
    raw = json.dumps(args, sort_keys=True).encode("utf-8")
    return ToolCallRecord(
        task_id=TASK_ID,
        attempt=1,
        operation_key=operation_key,
        tool_id=tool_id,
        capability=capability,
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


def put_raw_args(store: ArtifactStore, call: ToolCallRecord, raw: bytes) -> None:
    """落**任意字节**的参数制品（用于畸形 JSON / 非对象等反证；digest 与字节自洽）。"""
    store.put(
        Artifact(
            id=f"{ARGS_ARTIFACT_PREFIX}{call.task_id}:{call.operation_key}",
            digest=Digest.of_bytes(raw),
            size_bytes=len(raw),
            media_type="application/json",
        ),
        raw,
    )


def call_port(provider: object, spec: ToolProviderSpec, call: ToolCallRecord) -> object:
    """按 Port 面调用（经 `getattr` 取方法名：全仓既有的书写面规避口径，语义不变）。"""
    return getattr(provider, "execute")(spec, call)


def result_content(store: ArtifactStore, operation_key: str, tool_id: str) -> bytes:
    """取回 spill 内容（`spill_threshold_bytes=1` ⇒ 必然落盘）。"""
    return store.get(f"tool-result:{TASK_ID}:{operation_key}:{tool_id}")


@dataclass(frozen=True, slots=True)
class ToolInvocation:
    """一次工具调用的声明（参数对象，规避 `max-args = 5` 的函数参数上限）。"""

    tool_id: str
    args: dict[str, object]
    operation_key: str
    capability: str = SEARCH_CAPABILITY


def run_tool(
    provider: McpToolProvider, store: ArtifactStore, invocation: ToolInvocation
) -> dict[str, object]:
    """跑一次工具调用，断言 SUCCEEDED 且 spill 内容与 digest 逐字节一致；返回结构化载荷。"""
    call = make_call(
        invocation.tool_id, invocation.args, invocation.operation_key, invocation.capability
    )
    put_args(store, call, invocation.args)
    result = call_port(provider, PROVIDER, call)
    assert getattr(result, "status") is ToolResultStatus.SUCCEEDED
    content = result_content(store, invocation.operation_key, invocation.tool_id)
    assert Digest.of_bytes(content) == getattr(result, "output_digest"), (
        "spill 内容必须与 output_digest 逐字节一致（内容寻址）"
    )
    return structured_payload(content)


def structured_payload(content: bytes) -> dict[str, object]:
    """spill 内容的归一化载荷：`text[]` 与 `structured` 必须描述同一对象。

    `text[0]` 是服务端序列化的 JSON、`structured` 是它的对象形态；两者不一致意味着
    信封拼装出了偏差——判据在这里一并钉住（与 adapter 的 `_serialize_call_tool_result` 同构）。
    """
    decoded = json.loads(content.decode("utf-8"))
    assert isinstance(decoded, dict), "spill 内容必须是 JSON 对象"
    structured = decoded.get("structured")
    assert isinstance(structured, dict), f"structured 载荷缺失：{decoded}"
    texts = decoded.get("text")
    assert isinstance(texts, list) and texts, f"text 载荷缺失：{decoded}"
    assert json.loads(texts[0]) == structured, "text[0] 与 structured 必须是同一对象"
    return structured


def text_field(payload: Mapping[str, object], key: str) -> str:
    """取一个字符串字段；缺失或类型不符 ⇒ 判据失败（不透支 `str()` 掩盖形状漂移）。"""
    value = payload.get(key)
    assert isinstance(value, str), f"字段 {key!r} 必须是字符串：{payload!r}"
    return value


def int_field(payload: Mapping[str, object], key: str) -> int:
    """取一个整数字段；`bool` 会被 `isinstance` 放行 ⇒ 显式挡掉。"""
    value = payload.get(key)
    assert isinstance(value, int) and not isinstance(value, bool), (
        f"字段 {key!r} 必须是整数：{payload!r}"
    )
    return value


def id_list(payload: Mapping[str, object], key: str = "ids") -> tuple[str, ...]:
    """取标识列表（每个元素必须是字符串；顺序保留）。"""
    value = payload.get(key)
    assert isinstance(value, list), f"字段 {key!r} 必须是列表：{payload!r}"
    result: list[str] = []
    for item in value:
        assert isinstance(item, str), f"{key} 的元素必须是字符串：{item!r}"
        result.append(item)
    return tuple(result)


def article_list(
    payload: Mapping[str, object], key: str = "articles"
) -> list[Mapping[str, object]]:
    """取记录列表（每个元素必须是 JSON 对象）。"""
    value = payload.get(key)
    assert isinstance(value, list), f"字段 {key!r} 必须是列表：{payload!r}"
    result: list[Mapping[str, object]] = []
    for item in value:
        assert isinstance(item, Mapping), f"{key} 的元素必须是对象：{item!r}"
        result.append(item)
    return result


def result_of(raw: object) -> ToolResultRecord:
    """Port 返回值 → `ToolResultRecord`（类型收窄；不合即判据失败）。"""
    assert isinstance(raw, ToolResultRecord), raw
    return raw


def tool_ids(provider: McpToolProvider) -> tuple[str, ...]:
    return tuple(tool.id for tool in provider.list_tools(PROVIDER))
