"""Europe PMC 响应解析与归一化（与 `europe_pmc.py` 拆分，保持模块规模阈值）。

Europe PMC REST 返回 JSON。本模块是**纯函数**：原始 payload → 归一化 dict；
结构非法一律抛 `InvalidInputError`（由 provider 归入 permanent 分类）。

与 NCBI 的差别（实测）：Europe PMC 的 `search` 直接返回 `resultList.result[]`，
每条含 `pmid` / `doi` / `title` 等字段；**无需二次解析 XML**。检索与取记录用的是
同一个 `search` 端点（按 `query=EXT_ID:<pmid>` 精确取），故只有两个归一化函数。
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from packages.application.ports.errors import InvalidInputError

#: 单条记录里可选字段的取法：Europe PMC 对缺失字段**不保证**给空串，
#: 有时整键缺失 ⇒ 一律收敛成空串（与 NCBI 的 `extract_article` 同口径）。
_TEXT_FIELDS: tuple[tuple[str, str], ...] = (
    ("pmid", "pmid"),
    ("doi", "doi"),
    ("title", "title"),
    ("journal", "journalTitle"),
    ("year", "pubYear"),
    ("author_string", "authorString"),
)

#: 按标识精确取记录的**固定**检索模板（Europe PMC 的 REST 检索语法）。
_EXT_ID_TEMPLATE = "EXT_ID:{identifier}"


def _as_text(raw: object) -> str:
    """标量 → 去空白字符串；None / 非标量 ⇒ 空串（不猜、不编造）。"""
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, (int, float)):
        return str(raw)
    return ""


def _as_count(raw: object, default: int) -> int:
    """`hitCount` → int；缺键取默认（= 已收条数），非法一律 fail closed。

    显式逐类型判定而非 `int(raw)`：`int()` 对 `object` 没有可依靠的重载语义，
    且 `True` 会被静默读成 `1`（命中数不是布尔）。
    """
    if raw is None:
        return default
    if isinstance(raw, bool):
        raise InvalidInputError("europe pmc search hitCount must not be a boolean")
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            return int(raw.strip())
        except ValueError as exc:
            raise InvalidInputError("europe pmc search hitCount must be an integer") from exc
    raise InvalidInputError("europe pmc search hitCount must be an integer")


def normalize_record(item: Mapping[str, Any]) -> dict[str, object]:
    """Europe PMC 单条检索结果 → 归一化 article dict（缺失字段空串）。"""
    record: dict[str, object] = {}
    for key, source_key in _TEXT_FIELDS:
        record[key] = _as_text(item.get(source_key))
    return record


def ext_id_query(identifier: str) -> str:
    """按标识精确取记录的 Europe PMC **检索语法**串（唯一入口，便于审计与按压）。

    实现是「固定模板 + 参数化填充」：调用方给的标识只作 `{identifier}` 的**值**，
    没有任何位置能改变模板结构，也没有字符串拼接。
    """
    return _EXT_ID_TEMPLATE.format(identifier=str(identifier))


def normalize_search(payload: Mapping[str, Any], query: str) -> dict[str, object]:
    """Europe PMC `search` JSON → {query, count, ids, articles}。

    结构非法（缺 `resultList` 或 `resultList` 不是对象 / `result` 不是列表）⇒
    `InvalidInputError`（provider 侧归 permanent `TOOL_SCHEMA_MISMATCH`）。

    `ids` 只收**非空**标识（优先 `pmid`，退化到 `doi`）：运行链下一步
    （`ids_from_previous`）要求**非空 id 列表**，空串混进去会让下游按空 id 去取记录
    ⇒ 这里就挡掉（fail closed，不把空标识传下去）。
    """
    result_list = payload.get("resultList")
    if not isinstance(result_list, Mapping):
        raise InvalidInputError("europe pmc search response missing resultList")
    raw_results = result_list.get("result", [])
    if not isinstance(raw_results, list):
        raise InvalidInputError("europe pmc search response result must be a list")

    articles: list[dict[str, object]] = []
    ids: list[str] = []
    for item in raw_results:
        if not isinstance(item, Mapping):
            continue
        article = normalize_record(item)
        articles.append(article)
        identifier = _as_text(article.get("pmid")) or _as_text(article.get("doi"))
        if identifier:
            ids.append(identifier)
    count = _as_count(payload.get("hitCount"), len(articles))
    return {"query": query, "count": count, "ids": ids, "articles": articles}


__all__ = ["ext_id_query", "normalize_record", "normalize_search"]
