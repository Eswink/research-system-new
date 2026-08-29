"""MetricSample → OTel instruments 映射(adapters/otel 私有)。

instruments 按 MetricName 惰性创建;label 值必须是 `MetricLabel` 闭集键
(词汇层已强制),映射为 OTel attributes;COUNTER 只接受 int(词汇层已强制)。
"""

from __future__ import annotations

from opentelemetry.metrics import Counter, Histogram, Meter

from packages.application.observability.attributes import MetricKind, MetricName, MetricSample


def _unit_for(name: MetricName) -> str:
    if name.value.endswith("_ms"):
        return "ms"
    if name.value.endswith("_seconds"):
        return "s"
    return ""


class MetricMapper:
    """MetricSample → OTel Counter/Histogram 的一对一映射。"""

    def __init__(self, meter: Meter) -> None:
        self._meter = meter
        self._counters: dict[MetricName, Counter] = {}
        self._histograms: dict[MetricName, Histogram] = {}

    def record(self, sample: MetricSample) -> None:
        attributes = {label: str(value) for label, value in sample.labels.items()}
        if sample.kind is MetricKind.COUNTER:
            self._counter_for(sample).add(int(sample.value), attributes)
            return
        self._histogram_for(sample).record(float(sample.value), attributes)

    def _counter_for(self, sample: MetricSample) -> Counter:
        instrument = self._counters.get(sample.name)
        if instrument is None:
            instrument = self._meter.create_counter(sample.name.value, unit=_unit_for(sample.name))
            self._counters[sample.name] = instrument
        return instrument

    def _histogram_for(self, sample: MetricSample) -> Histogram:
        instrument = self._histograms.get(sample.name)
        if instrument is None:
            instrument = self._meter.create_histogram(
                sample.name.value, unit=_unit_for(sample.name)
            )
            self._histograms[sample.name] = instrument
        return instrument
