"""OpenTelemetry adapter 配置(adapters/otel 私有)。

仅 adapter 层可见;Domain/Application 只依赖 TelemetrySink Port(ADR-0026)。
telemetry off(默认)→ provider 直接组装 Null,零网络依赖;构造失败由
provider 捕获并回退 Null(fail-open,telemetry 故障不得阻断业务路径)。
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

_MIN_SAMPLE_RATIO = 0.0
_MAX_SAMPLE_RATIO = 1.0


@dataclass(frozen=True, slots=True)
class OtelConfig:
    """OTel 导出配置。

    endpoint 为 OTLP/HTTP base URL(在 provider 推导 `/v1/traces`、`/v1/metrics`);
    header_credential_refs 为 (header 名, credential ref) 对,凭据经
    CredentialResolver 在 provider 构造时解析,永不落盘、永不进入 span/metric。
    """

    enabled: bool = False
    endpoint: str = "http://localhost:4318"
    timeout_seconds: float = 5.0
    sample_ratio: float = 1.0
    queue_size: int = 2048
    export_interval_millis: int = 5000
    service_name: str = "research-os"
    service_version: str | None = None
    header_credential_refs: tuple[tuple[str, str], ...] = ()
    # "gzip" | "none";canary/证据扫描需要 none(明文 wire bytes)
    compression: str = "gzip"

    def __post_init__(self) -> None:
        parsed = urlsplit(self.endpoint)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("endpoint must be an absolute http(s) URL")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if not 0.0 <= self.sample_ratio <= _MAX_SAMPLE_RATIO:
            raise ValueError(
                f"sample_ratio must be within [{_MIN_SAMPLE_RATIO}, {_MAX_SAMPLE_RATIO}]"
            )
        if self.queue_size <= 0:
            raise ValueError("queue_size must be positive")
        if self.export_interval_millis <= 0:
            raise ValueError("export_interval_millis must be positive")
        if not self.service_name:
            raise ValueError("service_name must not be empty")
        for header_name, credential_ref in self.header_credential_refs:
            if not header_name or not credential_ref:
                raise ValueError("header credential refs must be non-empty pairs")
        if self.compression not in ("gzip", "none"):
            raise ValueError("compression must be 'gzip' or 'none'")

    def traces_endpoint(self) -> str:
        return _join_path(self.endpoint, "/v1/traces")

    def metrics_endpoint(self) -> str:
        return _join_path(self.endpoint, "/v1/metrics")


def _join_path(base: str, path: str) -> str:
    return base.rstrip("/") + path
