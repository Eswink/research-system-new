"""OpenTelemetry adapter(adapters/otel)。

OTel SDK 只允许出现在本包内(架构边界,WP4 `.importlinter.otel` 强制);
Domain/Application 只依赖 TelemetrySink Port 与 observability 词汇。
"""

from adapters.otel.config import OtelConfig
from adapters.otel.failsafe import FailSafeTelemetrySink
from adapters.otel.provider import build_telemetry_sink
from adapters.otel.sink import OtelTelemetrySink

__all__ = [
    "FailSafeTelemetrySink",
    "OtelConfig",
    "OtelTelemetrySink",
    "build_telemetry_sink",
]
