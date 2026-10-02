"""活检索模式：`tools/research_mcp_server.py` 的**真实上游**分支（GOAL-028 EC-02）。

**它解决什么**：冻结语料能证明「MCP 回环成立」，但**证不了**「这个 server 真会去取」——
语料是 2026-09-30 的快照。本模块给同一个 server 加一条**去真的取**的路：查询打到
Europe PMC REST，响应经**真解析**归一化成与冻结语料**同形**的记录（`_FIELDS` 一致），
于是上层（`literature_search` / `literature_read`）不需要知道自己在哪一模式。

**为什么复用既有 provider 的零件而不是另写一套 HTTP**：限速、429⇒transient、
4xx⇒permanent、字段归一化、URL 策略（仅 http/https + 保留类拒绝 + host ∈ 声明的
`network_domains`）在 `adapters/research_tools/europe_pmc_*` 里已经**只有一份**；
活检索直接调它们，语义与 REST provider 同源（AGENTS.md §12 的「dependency > adapter >
… > fork」——不做第二份实现）。

**边界**：

- **默认不用它**：只有 `RESEARCHOS_MCP_LIVE_RETRIEVAL=1`（或调用方显式注入 client）时
  才走本模块；默认门永远不碰它 ⇒ 既有 MCP 判据的确定性/标签语义一字不变。
- **触网前判策略**：先 `assert_url_allowed`（**唯一**的保留类判据 + 声明式白名单），
  过了才发请求 ⇒ 非法 host 时**零请求**。
- **不引凭据**：Europe PMC 检索无需凭据 ⇒ 本模块不解析任何凭据（也就不可能把别的域的
  令牌转发出去）。
- 本文件**不 import SDK / 产品装配**（server 是独立进程）：只依赖 `adapters.research_tools.*`
  的纯函数与 `packages.*` 的域类型，与 `tools/research_mcp_server.py` 同样的自持口径。
"""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from typing import Any

from adapters.research_tools.europe_pmc import EUROPE_PMC_BASE_URL
from adapters.research_tools.europe_pmc_parsing import ext_id_query, normalize_search
from adapters.research_tools.europe_pmc_runtime import (
    assert_url_allowed,
    request_document,
    search_endpoint,
    search_params,
)
from packages.application.model_relay.endpoint_policy import EndpointUrlPolicy

#: 活检索声明的上游域名（与 `toolpack_europe_pmc.yaml` / `tool_providers.yaml` 的
#: `europe_pmc` 条目同集合）。host 不在其中 ⇒ **触网前**拒绝。
NETWORK_DOMAINS: tuple[str, ...] = ("www.ebi.ac.uk",)
#: 上游检索端点（常量分段拼接，无调用方输入参与）。
BASE_URL = EUROPE_PMC_BASE_URL
#: 匿名调用者的礼貌间隔（与 `EuropePmcConfig` 的无 key 档同量级）。
MIN_REQUEST_INTERVAL_SECONDS = 0.34
#: 命中的记录里取哪些字段（**与冻结语料的 `_FIELDS` 逐字相同** ⇒ 两种模式同形）。
_LIVE_FIELDS = ("pmid", "doi", "title", "journal", "year", "author_string")


class LiveSettings:
    """活检索的调用期状态（限速用；每个 server 进程一份）。"""

    def __init__(
        self, *, client: Any = None, declared_domains: tuple[str, ...] | None = None
    ) -> None:
        self.client = client
        self.declared_domains = NETWORK_DOMAINS if declared_domains is None else declared_domains
        self.last_request_at = 0.0
        self.request_count = 0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self.last_request_at
        remaining = MIN_REQUEST_INTERVAL_SECONDS - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def get(self, params: Mapping[str, Any]) -> dict[str, Any]:
        """发一次检索请求：**先判策略、再节流、最后触网**（三条顺序不可换）。"""
        url = search_endpoint(BASE_URL)
        assert_url_allowed(url, EndpointUrlPolicy(), self.declared_domains)
        self._throttle()
        if self.client is None:
            raise RuntimeError("live retrieval requires an injected http client in this assembly")
        document = request_document(self.client, url, {**search_params(""), **params})
        self.last_request_at = time.monotonic()
        self.request_count += 1
        return document


def live_search(settings: LiveSettings, query: str, limit: int) -> dict[str, object]:
    """真实上游检索：响应经 `normalize_search` 归一化，形状与冻结模式**逐字一致**。"""
    document = settings.get({"query": query, "pageSize": limit})
    normalized = normalize_search(document, query)
    articles = [_record(item) for item in _articles(normalized)]
    count = normalized.get("count")
    return {
        "query": query,
        "hitCount": count if isinstance(count, int) else len(articles),
        "ids": [str(record["pmid"]) for record in articles],
        "articles": articles,
    }


def live_read(settings: LiveSettings, ids: list[str]) -> dict[str, object]:
    """按 id 从真实上游取记录；取不到的 id 在 `missing` 里**点名**（不编造、不顶替）。"""
    found: list[dict[str, object]] = []
    missing: list[str] = []
    seen: set[str] = set()
    for identifier in ids:
        if identifier in seen:
            continue
        seen.add(identifier)
        document = settings.get({"query": ext_id_query(identifier), "pageSize": 1})
        articles = [_record(item) for item in _articles(normalize_search(document, identifier))]
        matched = next((item for item in articles if str(item["pmid"]) == str(identifier)), None)
        if matched is None:
            missing.append(identifier)
        else:
            found.append(matched)
    return {
        "ids": [str(record["pmid"]) for record in found],
        "articles": found,
        "missing": missing,
    }


def _articles(normalized: Mapping[str, object]) -> list[Mapping[str, Any]]:
    raw = normalized.get("articles")
    if not isinstance(raw, list):
        raise RuntimeError("upstream response carries no article list")
    return [item for item in raw if isinstance(item, Mapping)]


def _record(item: Mapping[str, Any]) -> dict[str, object]:
    """归一化记录 → 与冻结语料同形的字段集（缺字段补空串，不省略键）。"""
    return {field: item.get(field) or "" for field in _LIVE_FIELDS}


def record_digest(record: Mapping[str, object]) -> str:
    """内容寻址 digest（canonical JSON；与冻结语料的取证口径同形）。"""
    payload = json.dumps(dict(record), ensure_ascii=False, sort_keys=True).encode("utf-8")
    from packages.domain.core import Digest

    return str(Digest.of_bytes(payload))


__all__ = [
    "BASE_URL",
    "MIN_REQUEST_INTERVAL_SECONDS",
    "NETWORK_DOMAINS",
    "LiveSettings",
    "live_read",
    "live_search",
    "record_digest",
]
