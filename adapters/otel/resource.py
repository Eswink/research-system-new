"""OTel Resource 构造(adapters/otel 私有)。

只携带服务身份属性(service.name / service.version);不采集 host 路径、
home 目录、环境变量或任何部署指纹以外的信息。

**不使用 `Resource.create`**:该工厂会无条件合并 `OTEL_RESOURCE_ATTRIBUTES`
与 `OTEL_EXPERIMENTAL_RESOURCE_DETECTORS` 指定的探测器,M15 复审实测可经环境
变量把任意属性(含凭据)注入每一条 span/metric 的 resource,完全绕过闭集词汇。
改为显式 `Resource(...)`:只有本函数枚举的键会被导出。
"""

from __future__ import annotations

from opentelemetry.sdk.resources import Resource

from adapters.otel.config import OtelConfig
from packages.domain.redaction import redact_text

_MAX_RESOURCE_VALUE_LENGTH = 96

# SDK 自描述属性显式声明(原先由 Resource.create 隐式追加;这里保留其可观测价值
# 而不引入环境变量逃逸面)
_SDK_ATTRIBUTES: dict[str, str] = {
    "telemetry.sdk.name": "opentelemetry",
    "telemetry.sdk.language": "python",
}


def build_resource(config: OtelConfig) -> Resource:
    """service 身份 resource;显式属性集,环境变量无法追加键。

    值同样经 `redact_text` + 定长:resource 属性会挂在**每一条** span 与 metric
    上,是遥测面里放大倍数最高的通道,不能假设调用方传进来的一定是干净版本号。
    """
    attributes: dict[str, str] = {
        **_SDK_ATTRIBUTES,
        "service.name": _bounded(config.service_name),
    }
    if config.service_version is not None:
        attributes["service.version"] = _bounded(config.service_version)
    return Resource(attributes)


def _bounded(value: str) -> str:
    return redact_text(value)[:_MAX_RESOURCE_VALUE_LENGTH]
