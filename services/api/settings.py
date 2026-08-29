"""Control Plane API settings。"""

from __future__ import annotations

import os
from dataclasses import dataclass

_DEFAULT_DB_PATH = "data/research-os-control.db"
_DEFAULT_OTEL_ENDPOINT = "http://localhost:4318"


@dataclass(frozen=True, slots=True)
class OtelSettings:
    """M15 观测配置面;enabled 默认 off(telemetry fail-open,ADR-0026)。"""

    enabled: bool = False
    endpoint: str = _DEFAULT_OTEL_ENDPOINT
    timeout_seconds: float = 5.0
    sample_ratio: float = 1.0
    header_credential_ref: str | None = None

    @classmethod
    def from_env(cls) -> OtelSettings:
        enabled = os.environ.get("RESEARCHOS_OTEL_ENABLED", "0").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        ref = os.environ.get("RESEARCHOS_OTEL_HEADER_CREDENTIAL_REF", "").strip()
        return cls(
            enabled=enabled,
            endpoint=os.environ.get("RESEARCHOS_OTEL_ENDPOINT", _DEFAULT_OTEL_ENDPOINT),
            timeout_seconds=float(os.environ.get("RESEARCHOS_OTEL_TIMEOUT", "5")),
            sample_ratio=float(os.environ.get("RESEARCHOS_OTEL_SAMPLE_RATIO", "1")),
            header_credential_ref=ref or None,
        )


class ApiSettings:
    """控制面配置；来自显式构造或环境变量。

    allow_localhost_endpoints：显式开发开关（RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS=1
    放行 localhost/private/link-local 端点探测）；默认关闭保持 fail-closed
    （endpoint_policy.py 默认拒绝，生产不暴露 loopback SSRF 面）。
    """

    def __init__(
        self,
        *,
        db_path: str = _DEFAULT_DB_PATH,
        endpoint_timeout_seconds: float = 120.0,
        allow_localhost_endpoints: bool = False,
        database_url: str | None = None,
        otel: OtelSettings | None = None,
    ) -> None:
        if not db_path:
            raise ValueError("db_path must not be empty")
        self.db_path = db_path
        self.endpoint_timeout_seconds = endpoint_timeout_seconds
        self.allow_localhost_endpoints = allow_localhost_endpoints
        # M14: PostgreSQL DSN (optional) — explicit construct or env
        self.database_url = database_url
        if self.database_url is not None and not self.database_url.strip():
            raise ValueError("database_url must not be empty string")
        # M15: telemetry（默认 off；配置错误在装配时回退 Null，不阻断启动）
        self.otel = otel if otel is not None else OtelSettings()

    @property
    def is_postgres(self) -> bool:
        """Whether this settings points at PostgreSQL (vs SQLite file)."""
        effective = self.effective_database_url()
        return effective is not None and effective.startswith("postgresql")

    def effective_database_url(self) -> str | None:
        """Resolved DSN: explicit database_url > env DATABASE_URL > None (use SQLite)."""
        if self.database_url is not None:
            return self.database_url
        for key in ("DATABASE_URL", "RESEARCHOS_DATABASE_URL", "POSTGRES_DSN"):
            val = os.environ.get(key)
            if val and val.strip():
                return val.strip()
        return None

    @classmethod
    def from_env(cls) -> ApiSettings:
        database_url: str | None = None
        for key in ("DATABASE_URL", "RESEARCHOS_DATABASE_URL", "POSTGRES_DSN"):
            val = os.environ.get(key)
            if val and val.strip():
                database_url = val.strip()
                break
        return cls(
            db_path=os.environ.get("RESEARCHOS_DB_PATH", _DEFAULT_DB_PATH),
            endpoint_timeout_seconds=float(os.environ.get("RESEARCHOS_ENDPOINT_TIMEOUT", "120")),
            allow_localhost_endpoints=(
                os.environ.get("RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS", "0").strip().lower()
                in ("1", "true", "yes", "on")
            ),
            database_url=database_url,
            otel=OtelSettings.from_env(),
        )
