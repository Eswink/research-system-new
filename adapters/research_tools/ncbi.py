"""NcbiEutilsProvider：NCBI E-utilities 真实学术检索 ToolProvider（REST）。

来源：https://www.ncbi.nlm.nih.gov/books/NBK25501/（NCBI E-utilities 官方文档）
与 https://www.ncbi.nlm.nih.gov/books/NBK25497/（使用条款：无 key 3 req/s，
有 key 10 req/s；本 provider 以 min_request_interval_seconds 强制间隔）。

边界（AGENTS.md §1 Tools / M8 ToolProvider Port）：
- 工具参数经 ArtifactStore 传递：调用方写入
  `tool-args:{task_id}:{operation_key}` artifact（JSON），provider 读取并校验
  内容 digest == call.argument_digest（内容寻址防篡改）；结果经
  spill_large_result 落 ArtifactStore，ToolResultRecord 只留 digest。
- 凭据只经 CredentialResolver 按 TOOL 域引用解析（默认 NCBI_API_KEY，
  以 api_key query 参数传给 E-utilities，不注入 Authorization），禁止
  token passthrough；错误消息统一 redaction。
- 错误映射：超时→PortTimeoutError(TOOL_TIMEOUT)；429/5xx/连接失败→
  TransientPortError(TOOL_UNAVAILABLE)（可重试）；4xx/解析失败→
  PermanentPortError(TOOL_SCHEMA_MISMATCH)。
- E-utilities 响应中的命中列表只是检索结果，不直接成为可信 Evidence
  （ToolResult 永不直升 Evidence，见 M10 治理链）。
"""

from __future__ import annotations

import json
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Mapping

import httpx

from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.credential_resolver import CredentialResolver
from packages.application.ports.errors import (
    InvalidInputError,
    PermanentPortError,
    PortTimeoutError,
    TransientPortError,
)
from packages.application.tool_plane.results import spill_large_result
from packages.domain.core import Digest
from packages.domain.enums import EndpointHealth, FailureCategory, ProviderType
from packages.domain.redaction import redact_exception_message
from packages.domain.serialization import digest_of
from packages.domain.tools import (
    ToolCallRecord,
    ToolHealthReport,
    ToolProviderSpec,
    ToolResultRecord,
    ToolSpec,
)

EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ARGS_ARTIFACT_PREFIX = "tool-args:"
SEARCH_RETMAX = 10


@dataclass(frozen=True, slots=True)
class NcbiEutilsConfig:
    """E-utilities 连接配置（与 McpConnectionSpec 同角色）。"""

    base_url: str = EUTILS_BASE_URL
    timeout_seconds: float = 30.0
    min_request_interval_seconds: float = 0.34
    credential_ref: str = "NCBI_API_KEY"


class NcbiEutilsProvider:
    """NCBI E-utilities 学术检索：literature.search / literature.read / citation.inspect。"""

    def __init__(
        self,
        artifact_store: ArtifactStore,
        *,
        credentials: CredentialResolver | None = None,
        config: NcbiEutilsConfig | None = None,
        http_client: httpx.Client | None = None,
        spill_threshold_bytes: int = 32 * 1024,
    ) -> None:
        self._store = artifact_store
        self._credentials = credentials
        self._config = config or NcbiEutilsConfig()
        self._client = http_client or httpx.Client(timeout=self._config.timeout_seconds)
        self._last_request_at = 0.0
        self._spill_threshold = spill_threshold_bytes

    def execute(self, provider: ToolProviderSpec, call: ToolCallRecord) -> ToolResultRecord:
        try:
            args = self._read_args(call)
            handler = {
                "literature_search": self._esearch,
                "literature_read": self._efetch,
                "citation_inspect": self._elink,
            }.get(call.tool_id)
            if handler is None:
                raise InvalidInputError(f"unknown tool id: {call.tool_id}")
            payload = handler(args)
            return self._to_record(call, payload)
        except (PortTimeoutError, TransientPortError, PermanentPortError):
            raise
        except (TimeoutError, httpx.TimeoutException) as exc:
            raise PortTimeoutError(
                "ncbi eutils request timed out",
                failure_category=FailureCategory.TOOL_TIMEOUT,
            ) from exc
        except (httpx.HTTPError, ConnectionError, OSError) as exc:
            raise TransientPortError(
                f"ncbi eutils connection failure: {redact_exception_message(str(exc))}",
                failure_category=FailureCategory.TOOL_UNAVAILABLE,
            ) from exc
        except (KeyError, TypeError, ValueError, json.JSONDecodeError, ET.ParseError) as exc:
            raise PermanentPortError(
                f"ncbi eutils malformed response: {redact_exception_message(str(exc))}",
                failure_category=FailureCategory.TOOL_SCHEMA_MISMATCH,
            ) from exc

    def list_tools(self, provider: ToolProviderSpec) -> tuple[ToolSpec, ...]:
        return tuple(
            ToolSpec(
                id=tool_id,
                name=tool_id,
                effect_class=provider.effect_class,
                provider_kind=ProviderType.REST,
                capabilities=list(provider.capabilities),
                description=description,
            )
            for tool_id, description in _TOOL_DESCRIPTIONS.items()
        )

    def check_health(self, provider: ToolProviderSpec) -> ToolHealthReport:
        try:
            payload = self._get("einfo.fcgi", {"retmode": "json"})
            dbinfo = payload.get("dbinfo", [])
            if not isinstance(dbinfo, list):
                raise InvalidInputError("einfo response dbinfo must be a list")
            db_count = len(dbinfo)
        except Exception:  # noqa: BLE001 — 健康探测失败统一归为 open circuit
            return ToolHealthReport(
                provider_id=provider.id,
                status=EndpointHealth.OPEN_CIRCUIT,
                detail="ncbi einfo probe failed",
            )
        schema_digest = digest_of({"tools": sorted(_TOOL_DESCRIPTIONS), "dbs": db_count})
        return ToolHealthReport(
            provider_id=provider.id,
            status=EndpointHealth.HEALTHY,
            observed_schema_digest=schema_digest,
            detail=f"{len(_TOOL_DESCRIPTIONS)} tools, {db_count} dbs",
        )

    def close(self) -> None:
        self._client.close()

    def _read_args(self, call: ToolCallRecord) -> dict[str, object]:
        artifact_id = f"{ARGS_ARTIFACT_PREFIX}{call.task_id}:{call.operation_key}"
        content = self._store.get(artifact_id)
        if Digest.of_bytes(content) != call.argument_digest:
            raise InvalidInputError("tool args digest mismatch")
        parsed = json.loads(content.decode("utf-8"))
        if not isinstance(parsed, dict):
            raise InvalidInputError("tool args must be a JSON object")
        return parsed

    def _get(self, endpoint: str, params: Mapping[str, object]) -> dict[str, object]:
        self._throttle()
        api_key = self._api_key()
        query = {key: str(value) for key, value in params.items()}
        if api_key is not None:
            query["api_key"] = api_key
        response = self._client.get(f"{self._config.base_url}/{endpoint}", params=query)
        self._last_request_at = time.monotonic()
        if response.status_code == 429:
            raise TransientPortError(
                "ncbi eutils rate limited",
                failure_category=FailureCategory.TOOL_UNAVAILABLE,
            )
        if response.status_code == 403:
            raise PermanentPortError(
                "ncbi eutils authentication failed",
                failure_category=FailureCategory.TOOL_UNAVAILABLE,
            )
        response.raise_for_status()
        if endpoint == "efetch.fcgi":
            return self._parse_efetch_xml(response.content)
        parsed: object = response.json()
        if not isinstance(parsed, dict):
            raise InvalidInputError(f"{endpoint} response must be a JSON object")
        return parsed

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        remaining = self._config.min_request_interval_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def _api_key(self) -> str | None:
        if self._credentials is None:
            return None
        try:
            return self._credentials.resolve(self._config.credential_ref).value
        except InvalidInputError:
            return None

    def _esearch(self, args: dict[str, object]) -> dict[str, object]:
        term = str(args.get("query", "")).strip()
        if not term:
            raise InvalidInputError("literature_search requires a non-empty query")
        retmax_raw = args.get("retmax", SEARCH_RETMAX)
        if not isinstance(retmax_raw, int):
            raise InvalidInputError("retmax must be an integer")
        retmax = retmax_raw
        payload = self._get(
            "esearch.fcgi",
            {"db": "pubmed", "term": term, "retmode": "json", "retmax": retmax},
        )
        result = payload.get("esearchresult")
        if not isinstance(result, dict):
            raise InvalidInputError("esearch response missing esearchresult")
        count_raw = result.get("count", 0)
        idlist = result.get("idlist", [])
        if not isinstance(idlist, list):
            raise InvalidInputError("esearch response idlist must be a list")
        try:
            count = int(count_raw)
        except (TypeError, ValueError) as exc:
            raise InvalidInputError("esearch response count must be an integer") from exc
        return {
            "count": count,
            "ids": [str(item) for item in idlist],
            "query": term,
        }

    def _efetch(self, args: dict[str, object]) -> dict[str, object]:
        ids = args.get("ids")
        if not isinstance(ids, list) or not ids:
            raise InvalidInputError("literature_read requires a non-empty ids list")
        id_list = ",".join(str(item) for item in ids[:50])
        payload = self._get("efetch.fcgi", {"db": "pubmed", "id": id_list, "retmode": "xml"})
        articles = payload.get("articles", [])
        if not isinstance(articles, list):
            raise InvalidInputError("efetch response articles must be a list")
        return {"articles": articles}

    def _elink(self, args: dict[str, object]) -> dict[str, object]:
        pmid = args.get("id")
        if pmid is None:
            raise InvalidInputError("citation_inspect requires an id")
        payload = self._get(
            "elink.fcgi",
            {"dbfrom": "pubmed", "db": "pmc", "id": str(pmid), "retmode": "json"},
        )
        links: list[str] = []
        linksets = payload.get("linksets", [])
        if not isinstance(linksets, list):
            raise InvalidInputError("elink response linksets must be a list")
        for linkset in linksets:
            if not isinstance(linkset, dict):
                continue
            for linkdb in linkset.get("linksetdbs", []):
                if not isinstance(linkdb, dict):
                    continue
                raw_links = linkdb.get("links", [])
                if isinstance(raw_links, list):
                    links.extend(str(item) for item in raw_links)
        return {"pmid": str(pmid), "pmc_links": links}

    def _parse_efetch_xml(self, content: bytes) -> dict[str, object]:
        root = ET.fromstring(content)
        articles = []
        for citation in root.findall(".//PubmedArticle"):
            medline = citation.find("MedlineCitation")
            if medline is None:
                continue
            articles.append(_extract_article(medline))
        return {"articles": articles}

    def _to_record(self, call: ToolCallRecord, payload: dict[str, object]) -> ToolResultRecord:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        spill = spill_large_result(
            self._store,
            call,
            raw,
            threshold_bytes=self._spill_threshold,
        )
        return spill.record


_TOOL_DESCRIPTIONS = {
    "literature_search": "Search PubMed via E-utilities esearch.",
    "literature_read": "Fetch PubMed records via E-utilities efetch.",
    "citation_inspect": "List PMC links for a PubMed id via E-utilities elink.",
}


def _extract_article(medline: ET.Element) -> dict[str, object]:
    pmid = medline.findtext("PMID") or ""
    article = medline.find("Article")
    title = ""
    abstract = ""
    journal = ""
    year = ""
    authors: list[str] = []
    if article is not None:
        title = "".join(article.findtext("ArticleTitle") or "").strip()
        abstract = " ".join(
            item.strip() for item in (article.findtext("Abstract/AbstractText") or "").split()
        )
        journal = article.findtext("Journal/Title") or ""
        year = article.findtext("Journal/JournalIssue/PubDate/Year") or ""
        author_list = article.find("AuthorList")
        if author_list is not None:
            for author in author_list.findall("Author"):
                last = author.findtext("LastName")
                fore = author.findtext("ForeName")
                collective = author.findtext("CollectiveName") or ""
                name = f"{fore or ''} {last or ''}".strip() or collective
                if name:
                    authors.append(name)
    return {
        "pmid": pmid,
        "title": title,
        "abstract": abstract,
        "journal": journal,
        "year": year,
        "authors": authors,
    }
