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
from dataclasses import dataclass
from typing import Any, Mapping

import httpx

from adapters.research_tools.parsing import (
    normalize_elink,
    normalize_esearch,
    parse_efetch_xml,
    validate_citation_support,
)
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
            handler = self._handlers().get(call.tool_id)
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
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise PermanentPortError(
                f"ncbi eutils malformed response: {redact_exception_message(str(exc))}",
                failure_category=FailureCategory.TOOL_SCHEMA_MISMATCH,
            ) from exc

    def list_tools(self, provider: ToolProviderSpec) -> tuple[ToolSpec, ...]:
        descriptions = self._tool_descriptions()
        return tuple(
            ToolSpec(
                id=tool_id,
                name=tool_id,
                effect_class=provider.effect_class,
                provider_kind=ProviderType.REST,
                capabilities=list(provider.capabilities),
                description=description,
            )
            for tool_id, description in descriptions.items()
        )

    def check_health(self, provider: ToolProviderSpec) -> ToolHealthReport:
        descriptions = self._tool_descriptions()
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
        schema_digest = digest_of({"tools": sorted(descriptions), "dbs": db_count})
        return ToolHealthReport(
            provider_id=provider.id,
            status=EndpointHealth.HEALTHY,
            observed_schema_digest=schema_digest,
            detail=f"{len(descriptions)} tools, {db_count} dbs",
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
            return parse_efetch_xml(response.content)
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
        return normalize_esearch(payload, term)

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
        return normalize_elink(self._fetch_elink_payload(pmid), str(pmid))

    def _fetch_elink_payload(self, pmid: object) -> dict[str, object]:
        """取 elink 的**原始** JSON（全仓唯一一处 elink 取数）。

        `citation.inspect` 与 `citation.validate` 都从这里取数 ⇒ 两个能力的**取数面是同一
        个 HTTP 调用与同一条端点参数**（GOAL-20261006-031 EC-02(b) 的「不得新造第二套取数」
        在实现上落成这一点：新增一条 elink 请求只有改本方法一途）。
        """
        return self._get(
            "elink.fcgi",
            {"dbfrom": "pubmed", "db": "pmc", "id": str(pmid), "retmode": "json"},
        )

    def _handlers(self) -> dict[str, Any]:
        """tool id → 处理函数（子类**扩展**这张表，不改 `execute` 的分派逻辑）。"""
        return {
            "literature_search": self._esearch,
            "literature_read": self._efetch,
            "citation_inspect": self._elink,
        }

    def _tool_descriptions(self) -> dict[str, str]:
        """tool id → 描述（子类覆盖它即换工具面，`list_tools` 本体不动）。"""
        return _TOOL_DESCRIPTIONS

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

#: `citation.validate` 的工具面（与 `citation.inspect` **不同**的一条工具 id）。
_CITATION_VALIDATE_DESCRIPTION = (
    "Decide whether a PubMed citation is supported by its PMC link data "
    "(three-state: SUPPORTED / UNSUPPORTED / UNDETERMINED)."
)


class NcbiCitationValidationProvider(NcbiEutilsProvider):
    """`citation.validate` 的真实承接：**复用** `NcbiEutilsProvider` 的取数。

    为什么是子类而不是第二个 provider 实现（GOAL-20261006-031 EC-02(b)）：
    - **取数只有一套**：`_fetch_elink_payload` 是唯一 elink 取数点，`citation.inspect`
      （父类 `_elink`）与本类 `citation_validate` 都调它 —— 「不新造第二套取数」在
      **实现上**成立，而不是靠散文声明；
    - **错误映射 / 凭据解析 / 限速 / 健康探测逐字继承**（父类的四个面都未覆盖）。

    判定层用 `parsing.validate_citation_support`（三态）—— 判定语义是**显式常量**
    （`CITATION_SUPPORTED` / `CITATION_UNSUPPORTED` / `CITATION_UNDETERMINED`），
    不是布尔收窄，也不是「非空即真」。
    """

    def _handlers(self) -> dict[str, Any]:
        return {
            "citation_validate": self._citation_validate,
        }

    def _tool_descriptions(self) -> dict[str, str]:
        return {"citation_validate": _CITATION_VALIDATE_DESCRIPTION}

    def _citation_validate(self, args: dict[str, object]) -> dict[str, object]:
        pmid = args.get("id")
        if pmid is None:
            raise InvalidInputError("citation_validate requires an id")
        payload = self._fetch_elink_payload(pmid)
        return validate_citation_support(payload, str(pmid))
