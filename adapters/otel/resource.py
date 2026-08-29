"""OTel Resource 构造(adapters/otel 私有)。

只携带服务身份属性(service.name / service.version);不采集 host 路径、
home 目录、环境变量或任何部署指纹以外的信息。
"""

from __future__ import annotations

from opentelemetry.sdk.resources import Resource

from adapters.otel.config import OtelConfig


def build_resource(config: OtelConfig) -> Resource:
    """service 身份 resource;`Resource.create` 追加 telemetry.sdk 自描述属性。"""
    attributes: dict[str, str] = {"service.name": config.service_name}
    if config.service_version is not None:
        attributes["service.version"] = config.service_version
    return Resource.create(attributes)
