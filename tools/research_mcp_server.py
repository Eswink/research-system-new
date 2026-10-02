"""Research MCP server：自建、离线、确定性的科研文献 MCP server（GOAL-20260927-027 EC-02）。

**它是什么**：一个 stdio MCP server，暴露两个工具 -- `literature_search` / `literature_read`
-- 服务一份**冻结的真实文献语料**（`CORPUS`）。

**语料 provenance（如实边界）**：全部记录于 **2026-09-30** 经 Europe PMC REST
（`resultType=lite`）实取，逐字保留 `pmid` / `doi` / `title` / `journalTitle` /
`pubYear` / `authorString`（字段名归一化为 `journal` / `year` / `author_string`，
值一字未改；只收标题无 XML 标记的记录，避免把标记当正文）。它们是**真实发表记录**：
真 PMID、真 DOI、真标题、真期刊、真年份 -- 但语料本身是**冻结快照**，不是在线检索。

**为什么冻结（而不是在线转发）**：默认 CI 与默认门必须离线（AGENTS.md §9 默认 deny
外网；EC-02 选 stdio 传输就是为离线优先）。冻结语料让"Run 复现"不依赖对端可用性：
server 侧只读本地常量，无网络、无时钟、无随机 -- 同输入恒同输出。

**活检索模式（GOAL-20261001-028 EC-02）**：同一个 server 另有一条**去真的取**的路
（`tools/research_mcp_live.py`），只在显式开关（`RESEARCHOS_MCP_LIVE_RETRIEVAL=1`，
或装配方直接给 `build_server(live=...)`）下启用；它真打 Europe PMC REST、复用既有
provider 的限速与归一化、遵守**触网前** URL 策略，归一化形状与冻结语料**逐字同形**。
**默认（未开关）仍是冻结语料、逐字节不变**。两条路都**不**构成"第三方 MCP server
可用性"的证明 —— 第三方可 pin 性的勘察结论见
`docs/integration/MCP_TOOL_PROVIDERS.md` §6.4（结论：以本仓现有 pin 规则衡量，
未登记的第三方 server 目前不可 pin）。

**协议面**：由 `mcp` SDK（仓库既有的 `mcp>=1.28,<2` 依赖，零新增）的 FastMCP 承载；
传输仅 stdio。本文件**不 import 仓库内任何模块**（server 是独立进程，经 stdio 契约与
adapter 相接）；模块可被 `python -B tools/research_mcp_server.py` 直接起。

**工具面**（与能力名 `literature.search` / `literature.read` 对齐）：

- `literature_search(query, limit=5)`：整串按空白切成 token，**所有** token
  （大小写不敏感）都出现在记录的检索面（PMID / DOI / 标题 / 期刊 / 年份 / 作者）才算命中；
  结果按语料顺序稳定返回；`hitCount` 是**命中总数**（截断前），`ids` / `articles` 截断到 `limit`。
- `literature_read(ids)`：按 id（PMID）精确取记录；取不到的 id 在 `missing` 里**点名**，
  绝不编造、绝不用别的记录顶替。

空 query / 空 ids / 非法 limit 一律**拒绝**（抛 `ValueError`，FastMCP 会作为工具错误
回给调用方）——不静默返回空结果。
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, cast

from mcp.server.fastmcp import FastMCP

SERVER_NAME = "research-frozen-corpus"

#: 记录的字段名（冻结语料的规范化形态；值 = Europe PMC 实取值）。
Record = dict[str, str]

#: 冻结的真实文献语料（2026-09-30 经 Europe PMC REST 实取；见模块 docstring）。
CORPUS: tuple[Record, ...] = (
    {
        "pmid": "42803750",
        "doi": "10.1002/cns.71179",
        "title": (
            "Explore the Mechanism of Xiaoyaosan for Treatment of Bipolar Disorder "
            "Based on Network Pharmacology, Experimental Validation and Molecular Docking."
        ),
        "journal": "CNS Neurosci Ther",
        "year": "2026",
        "author_string": (
            "Chen M, Ding N, Qiu X, Li L, Guo Y, Wang R, Mo X, Zou T, Yu S, Li X, Chen J."
        ),
    },
    {
        "pmid": "42796516",
        "doi": "10.3390/molecules31183228",
        "title": (
            "Molecular Docking of Natural Products: Critical Appraisal of "
            "Current Methodology and Practical Guidelines."
        ),
        "journal": "Molecules",
        "year": "2026",
        "author_string": "Makhmutova AS, Remetova NS, Kurmantayeva GK.",
    },
    {
        "pmid": "42740546",
        "doi": "10.1080/07391102.2026.2731448",
        "title": (
            "Deciphering the molecular recognition of advantame by calf thymus DNA and "
            "human serum albumin through integrated multispectroscopic and molecular "
            "docking analyses."
        ),
        "journal": "J Biomol Struct Dyn",
        "year": "2026",
        "author_string": "Abbasi Majd S.",
    },
    {
        "pmid": "42772441",
        "doi": "10.1016/j.envpol.2026.129209",
        "title": (
            "Network pharmacology and molecular docking-based investigation on the "
            "mechanism of BPA in depression and experimental verification in offspring mice."
        ),
        "journal": "Environ Pollut",
        "year": "2026",
        "author_string": "Zhou H, Doubra O, Qian M, Li H, Yan D, Gao L.",
    },
    {
        "pmid": "42665486",
        "doi": "10.1016/j.bja.2026.07.034",
        "title": (
            "Carbon footprint of anaesthesia pharmaceuticals and disposable products "
            "during Caesarean delivery: a single-centre prospective observational study."
        ),
        "journal": "Br J Anaesth",
        "year": "2026",
        "author_string": (
            "Kouwenberg LHJA, Demir M, van Bodegraven L, Colenbrander ECA, de Haes FI, "
            "Cohen ES, Hehenkamp WJK, Weiland NHS, Salentijn DA."
        ),
    },
    {
        "pmid": "42613204",
        "doi": "10.1016/j.bja.2026.06.051",
        "title": (
            "Assessing the carbon footprint of inhalation anaesthesia, total intravenous "
            "anaesthesia, and spinal anaesthesia for a single surgical procedure: "
            "a prospective observational study."
        ),
        "journal": "Br J Anaesth",
        "year": "2026",
        "author_string": (
            "Lechani L, Verdonk F, Daigné D, Maire M, Tan D, Cambriel A, Kapandji N, "
            "Pardo E, Taconet C."
        ),
    },
    {
        "pmid": "42775559",
        "doi": "10.1111/anae.70395",
        "title": (
            "A web application for estimating the carbon footprint of individual anaesthetics."
        ),
        "journal": "Anaesthesia",
        "year": "2026",
        "author_string": "Fullick J.",
    },
)

#: `literature_search` 的默认页大小（与语料规模同量级；调用方可显式给 `limit`）。
DEFAULT_LIMIT = 5

_FIELDS = ("pmid", "doi", "title", "journal", "year", "author_string")


def _haystack(record: Mapping[str, str]) -> str:
    """记录的检索面（大小写折叠；字段顺序固定 => 结果与匹配都确定）。"""
    return " ".join(record.get(field, "") for field in _FIELDS).casefold()


def _search_records(query: str, limit: int) -> dict[str, object]:
    """token-AND 检索（见模块 docstring；命中数 = 截断前总数）。"""
    needle = query.strip().casefold()
    if not needle:
        raise ValueError("query must be a non-empty string")
    if limit < 1:
        raise ValueError("limit must be a positive integer")
    tokens = needle.split()
    matched = [record for record in CORPUS if all(token in _haystack(record) for token in tokens)]
    selected = matched[:limit]
    return {
        "query": query,
        "hitCount": len(matched),
        "ids": [record["pmid"] for record in selected],
        "articles": [dict(record) for record in selected],
    }


def _read_records(ids: list[str]) -> dict[str, object]:
    """按 PMID 精确取记录；缺失的 id **点名**（不编造、不顶替）。"""
    if not ids:
        raise ValueError("ids must be a non-empty list of identifiers")
    by_id = {record["pmid"]: record for record in CORPUS}
    seen: set[str] = set()
    found: list[Record] = []
    missing: list[str] = []
    for identifier in ids:
        if identifier in seen:
            continue
        seen.add(identifier)
        record = by_id.get(identifier)
        if record is None:
            missing.append(identifier)
        else:
            found.append(record)
    return {
        "ids": [record["pmid"] for record in found],
        "articles": [dict(record) for record in found],
        "missing": missing,
    }


class _LiveModule(Protocol):
    """活检索模块的**结构面**（`tools/` 不是包 ⇒ 只能按路径加载，故用 Protocol 定形）。"""

    def LiveSettings(self, *, client: object = ...) -> Any: ...  # noqa: N802 - 类名即构造器

    def live_search(self, settings: Any, query: str, limit: int) -> dict[str, object]: ...

    def live_read(self, settings: Any, ids: list[str]) -> dict[str, object]: ...


def _load_live_module() -> _LiveModule | None:
    """按**路径**加载活检索模块（`tools/` 不是包 ⇒ 静态 `tools.` 导入会让同一文件
    有两个模块身份；仓内既有先例用 `spec_from_file_location`，见
    `tools/verify_goal027_closeout.py::load_standard`）。取不到 ⇒ None（缺件，交由调用点点名）。
    """
    import importlib.util
    import sys
    from pathlib import Path

    name = "research_os_mcp_live"
    existing = sys.modules.get(name)
    if existing is not None:
        return cast(_LiveModule, existing)
    target = Path(__file__).resolve().parent / "research_mcp_live.py"
    spec = importlib.util.spec_from_file_location(name, target)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:  # noqa: BLE001 - 加载失败 ⇒ 缺件，如实交由调用点处理
        sys.modules.pop(name, None)
        return None
    return cast(_LiveModule, module)


def _live_settings() -> object | None:
    """活检索模式（GOAL-028 EC-02）：**显式开关**打开时才返回设置，否则 None。

    开关 = 环境变量 `RESEARCHOS_MCP_LIVE_RETRIEVAL=1`（值必须恰为 `"1"`，与仓内
    `live_e2e_switch_enabled` 的口径一致）。**默认（未设置）返回 None ⇒ 全程冻结语料**，
    既有判据的确定性与标签语义因此一字不变。
    """
    import os

    if os.environ.get("RESEARCHOS_MCP_LIVE_RETRIEVAL") != "1":
        return None
    module = _load_live_module()
    if module is None:
        return None
    try:
        import httpx

        client: object | None = httpx.Client(timeout=30.0)
    except Exception:  # noqa: BLE001 - 取不到 client ⇒ 缺件，交由 LiveSettings 点名
        client = None
    settings: object = module.LiveSettings(client=client)
    return settings


def build_server(*, live: object | None = None) -> FastMCP:
    """构建 server 并注册两个工具（工具名 = 能力名的下划线形态）。

    `live`（GOAL-028 EC-02）：非 None ⇒ 检索/读取改走**真实上游**（仍走同一对工具名与
    同一份归一化形状）；None（缺省）⇒ 冻结语料，行为逐字节不变。缺省 None 时**不读**
    任何环境变量（纯函数式入口，判据可确定地构造两种模式）。
    """
    settings = live if live is not None else _live_settings()
    server = FastMCP(SERVER_NAME, json_response=True)

    @server.tool()
    def literature_search(query: str, limit: int = DEFAULT_LIMIT) -> dict[str, object]:
        """Search the frozen real-literature corpus (token AND over record fields)."""
        if settings is not None:
            module = _load_live_module()
            if module is None:
                raise RuntimeError("live retrieval mode requires research_mcp_live.py")
            return module.live_search(settings, query, limit)
        return _search_records(query, limit)

    @server.tool()
    def literature_read(ids: list[str]) -> dict[str, object]:
        """Fetch records by exact PMID from the frozen real-literature corpus."""
        if settings is not None:
            module = _load_live_module()
            if module is None:
                raise RuntimeError("live retrieval mode requires research_mcp_live.py")
            return module.live_read(settings, ids)
        return _read_records(ids)

    return server


def main() -> None:
    build_server().run(transport="stdio")


if __name__ == "__main__":
    main()
