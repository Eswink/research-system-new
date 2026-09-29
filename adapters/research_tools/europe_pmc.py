"""EuropePmcProvider：Europe PMC 真实学术检索 ToolProvider（REST）。

来源：https://europepmc.org/RestfulWebService（Europe PMC RESTful API 官方文档；
检索与按 id 取记录共用 `search` 端点）。许可：Europe PMC 内容按各记录的原始许可
分发，元数据（标题 / 作者 / 期刊 / 年 / DOI / PMID）可自由检索引用；本 provider 只读
元数据、不批量抓取全文，故 pin 记 `license: SEE-ARTICLE`（逐条看原始许可）。

边界（对齐 AGENTS.md §1 Tools / M8 ToolProvider Port，与 `ncbi.py` 同形）：

- **工具参数**经 ArtifactStore 传递：调用方写 `tool-args:{task_id}:{operation_key}`（JSON），
  provider 读回并校验内容 digest == `call.argument_digest`（内容寻址防篡改）。
- **结果**经 `spill_large_result` 落 ArtifactStore，`ToolResultRecord` 只留 digest。
- **凭据**：Europe PMC 检索**无需凭据** ⇒ 本 provider **不解析任何凭据**
  （不声明 `credential_ref`，也就无从把别的域的令牌转发出去）。
- **URL 策略在触网之前**（本 provider 的净增量，GOAL-027 EC-01 ④）：实测既有仓内
  没有任何调用方校验「tool provider 的出站 host 是否落在它自己声明的 `network_domains`
  内」（`endpoint_url_refusal` 只服务 LLM 端点与探针）⇒ 本 provider 在**发请求前**判三件事：
  ① scheme 仅 http/https；② 复用 `endpoint_url_refusal` 作**唯一**保留类判据
  （拒绝 localhost / 环回 / 私有 / 链路本地 / 保留地址，**不新造第二个 host 谓词**）；
  ③ host 必须落在**声明的** `network_domains` 白名单内（声明来自
  `ToolProviderSpec.network_domains` —— 即 provider 的登记声明本身，**不是**另一个副本）。
  任一条不过 ⇒ 抛错、**零请求**。
- **远程检索串与请求参数**一律由 `europe_pmc_runtime` 以**常量分段 / 结构化字段**构造，
  本模块不做任何字符串化拼装。
- **错误映射**：超时 → `PortTimeoutError(TOOL_TIMEOUT)`；429/5xx/连接失败 →
  `TransientPortError(TOOL_UNAVAILABLE)`（可重试）；其余 4xx / 解析失败 →
  `PermanentPortError`（不可重试）。
- 检索结果只是**来源材料**，不直接成为可信 Evidence（ToolResult 永不直升 Evidence）。
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass

import httpx

from adapters.research_tools.europe_pmc_parsing import ext_id_query, normalize_search
from adapters.research_tools.europe_pmc_runtime import (
    HEALTH_PROBE_TERM,
    assert_url_allowed,
    describe_tools,
    request_document,
    search_endpoint,
    search_params,
    tool_ids,
)
from packages.application.model_relay.endpoint_policy import EndpointUrlPolicy
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import (
    InvalidInputError,
    PermanentPortError,
    PortTimeoutError,
    TransientPortError,
)
from packages.application.tool_plane.results import spill_large_result
from packages.domain.core import Digest
from packages.domain.enums import EndpointHealth, FailureCategory
from packages.domain.redaction import redact_exception_message
from packages.domain.serialization import digest_of
from packages.domain.tools import (
    ToolCallRecord,
    ToolHealthReport,
    ToolProviderSpec,
    ToolResultRecord,
    ToolSpec,
)

EUROPE_PMC_BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"
ARGS_ARTIFACT_PREFIX = "tool-args:"
SEARCH_PAGE_SIZE = 10


@dataclass(frozen=True, slots=True)
class EuropePmcConfig:
    """Europe PMC 连接配置（与 `NcbiEutilsConfig` / `McpConnectionSpec` 同角色）。"""

    base_url: str = EUROPE_PMC_BASE_URL
    timeout_seconds: float = 30.0
    #: Europe PMC 对匿名调用者的礼貌间隔（官方未硬性限速；取值与 NCBI 无 key 档同量级）。
    min_request_interval_seconds: float = 0.34


class EuropePmcProvider:
    """Europe PMC 学术检索：literature.search / literature.read。"""

    def __init__(
        self,
        artifact_store: ArtifactStore,
        *,
        config: EuropePmcConfig | None = None,
        http_client: httpx.Client | None = None,
        url_policy: EndpointUrlPolicy | None = None,
        spill_threshold_bytes: int = 32 * 1024,
    ) -> None:
        self._store = artifact_store
        self._config = config or EuropePmcConfig()
        self._client = http_client or httpx.Client(timeout=self._config.timeout_seconds)
        self._url_policy = url_policy or EndpointUrlPolicy()
        self._last_request_at = 0.0
        self._spill_threshold = spill_threshold_bytes

    def _call_tool(self, provider: ToolProviderSpec, call: ToolCallRecord) -> ToolResultRecord:
        """读参（防篡改）→ 分派 → 内容寻址落盘；异常按 transient/permanent 归类。"""
        try:
            args = self._read_args(call)
            handler: Callable[[dict[str, object]], dict[str, object]] | None = {
                "literature_search": lambda args: self._search(provider, args),
                "literature_read": lambda args: self._read(provider, args),
            }.get(call.tool_id)
            if handler is None:
                raise InvalidInputError(f"unknown tool id: {call.tool_id}")
            return self._to_record(call, handler(args))
        except (PortTimeoutError, TransientPortError, PermanentPortError):
            raise
        except (TimeoutError, httpx.TimeoutException) as exc:
            raise PortTimeoutError(
                "europe pmc request timed out",
                failure_category=FailureCategory.TOOL_TIMEOUT,
            ) from exc
        except (httpx.HTTPError, ConnectionError, OSError) as exc:
            raise TransientPortError(
                f"europe pmc connection failure: {redact_exception_message(str(exc))}",
                failure_category=FailureCategory.TOOL_UNAVAILABLE,
            ) from exc
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise PermanentPortError(
                f"europe pmc malformed response: {redact_exception_message(str(exc))}",
                failure_category=FailureCategory.TOOL_SCHEMA_MISMATCH,
            ) from exc

    # ToolProvider Port 的语句入口：单次工具调用（本类不持有策略真值）。
    execute = _call_tool

    def list_tools(self, provider: ToolProviderSpec) -> tuple[ToolSpec, ...]:
        return describe_tools(provider)

    def check_health(self, provider: ToolProviderSpec) -> ToolHealthReport:
        try:
            payload = self._get(provider, HEALTH_PROBE_TERM, {"format": "json", "pageSize": 1})
            hit_count = payload.get("hitCount")
            if not isinstance(hit_count, (int, str)):
                raise InvalidInputError("europe pmc probe hitCount must be a scalar")
        except Exception:  # noqa: BLE001 — 健康探测失败统一归为 open circuit
            return ToolHealthReport(
                provider_id=provider.id,
                status=EndpointHealth.OPEN_CIRCUIT,
                detail="europe pmc probe failed",
            )
        schema_digest = digest_of({"tools": tool_ids(), "hit_count": str(hit_count)})
        return ToolHealthReport(
            provider_id=provider.id,
            status=EndpointHealth.HEALTHY,
            observed_schema_digest=schema_digest,
            detail=f"{len(tool_ids())} tools, hitCount={hit_count}",
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

    def _get(
        self,
        provider: ToolProviderSpec,
        term: str,
        extra: dict[str, str | int],
    ) -> dict[str, object]:
        """先判 URL 策略（**触网之前**），再节流，再发请求。"""
        url = search_endpoint(self._config.base_url)
        assert_url_allowed(url, self._url_policy, tuple(provider.network_domains))
        self._throttle()
        params = {**search_params(term), **extra}
        document = request_document(self._client, url, params)
        self._last_request_at = time.monotonic()
        return document

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        remaining = self._config.min_request_interval_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def _search(self, provider: ToolProviderSpec, args: dict[str, object]) -> dict[str, object]:
        term = str(args.get("query", "")).strip()
        if not term:
            raise InvalidInputError("literature_search requires a non-empty query")
        page_size_raw = args.get("retmax", args.get("pageSize", SEARCH_PAGE_SIZE))
        if not isinstance(page_size_raw, int) or isinstance(page_size_raw, bool):
            raise InvalidInputError("retmax must be an integer")
        payload = self._get(provider, term, {"pageSize": page_size_raw})
        return normalize_search(payload, term)

    def _read(self, provider: ToolProviderSpec, args: dict[str, object]) -> dict[str, object]:
        ids = args.get("ids")
        if not isinstance(ids, list) or not ids:
            raise InvalidInputError("literature_read requires a non-empty ids list")
        articles: list[dict[str, object]] = []
        for identifier in [str(item) for item in ids[:50]]:
            record_query = ext_id_query(identifier)
            payload = self._get(provider, record_query, {"pageSize": 1})
            normalized = normalize_search(payload, record_query)
            found = normalized.get("articles", [])
            if isinstance(found, list):
                articles.extend(item for item in found if isinstance(item, dict))
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


__all__ = [
    "ARGS_ARTIFACT_PREFIX",
    "EUROPE_PMC_BASE_URL",
    "EuropePmcConfig",
    "EuropePmcProvider",
]
