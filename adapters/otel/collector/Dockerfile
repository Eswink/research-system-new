# Research OS OTel Collector(M15 证据管线)。
#
# base image 以 sha256 manifest digest 固定(多架构 index):
# otel/opentelemetry-collector-contrib:0.139.0
# digest 见 UPSTREAM_COMPONENTS.yaml 的 DOCKERFILE 组件条目。
FROM otel/opentelemetry-collector-contrib@sha256:faf125d656fa47cea568b2f3b4494efd2525083bc75c1e96038bc23f05cd68fd

COPY collector.yaml /etc/otelcol-contrib/config.yaml
