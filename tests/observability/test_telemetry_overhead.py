"""M15 telemetry overhead 对比测试(telemetry off vs on)。

DoD-18:off/on 延迟对比、线程数稳定、干净 shutdown、无泄漏。

复审后的强度修正:
- `drop_count == 0` 曾是**结构性恒真**断言(外壳只数 inner 抛错,而 OTel sink
  自吞一切)。现在 `drop_count` 聚合 inner 计数,该断言真的可能失败——
  非空性由 `test_lifecycle_bounds.py::test_exporter_failure_is_visible_in_drop_count`
  独立证明(全量导出失败时它必须 > 0)。
- 内存与线程上界从"几百倍余量"收紧到有证据的量级,并改测**增量**而非绝对值
  (绝对 512 MiB 对一个基线约 50 MiB 的进程没有判别力)。
- off 路径的线程断言原先恒真(off 不起线程);改为同时断言 off 不引入线程、
  且 on 的线程增长在有界范围内并在 shutdown 后归还。
"""

from __future__ import annotations

import ctypes
import sys
import threading
import time
import tracemalloc

import pytest

from adapters.otel.config import OtelConfig
from adapters.otel.provider import build_telemetry_sink
from tests.observability.isolation_scenario import _state_with
from tests.observability.otlp_receiver import OtlpHttpReceiver

_ITERATIONS = 40
# 实测峰值约 0.22 MiB;16 MiB 留约 70 倍余量防平台抖动,同时保留判别力
_PEAK_ALLOC_LIMIT_BYTES = 16 * 1024 * 1024
# 后台线程:BatchSpanProcessor worker + PeriodicExportingMetricReader
_MAX_TELEMETRY_THREADS = 4
_MAX_RSS_GROWTH_MIB = 128.0


def _baseline_thread_count() -> int:
    return threading.active_count()


class _ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def _rss_mib() -> float:
    """进程 RSS(MiB);stdlib-only:Windows psapi / Linux /proc / POSIX resource。"""
    if sys.platform == "win32":
        return _rss_mib_windows()
    import resource  # noqa: PLC0415 - POSIX-only 模块,Windows 上 import 会失败

    divisor = 1024.0 * 1024.0 if sys.platform == "darwin" else 1024.0
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / divisor


def _rss_mib_windows() -> float:
    # Windows-only 路径（仅 sys.platform == "win32" 时调用）。typeshed 在非
    # Windows 平台不提供 WinDLL/windll 成员，故用 getattr 取属性：既让 Linux
    # CI 的 mypy 通过，也避免在 Windows 上产生 unused-ignore 报错。
    win_dll = getattr(ctypes, "WinDLL")
    psapi = win_dll("psapi.dll")
    psapi.GetProcessMemoryInfo.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(_ProcessMemoryCounters),
        ctypes.c_ulong,
    ]
    windll = getattr(ctypes, "windll")
    kernel32 = windll.kernel32
    kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    counters = _ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(_ProcessMemoryCounters)
    handle = kernel32.GetCurrentProcess()
    if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
        return 0.0
    return float(counters.WorkingSetSize) / (1024.0 * 1024.0)


def _config(endpoint: str) -> OtelConfig:
    return OtelConfig(
        enabled=True,
        endpoint=endpoint,
        timeout_seconds=2.0,
        export_interval_millis=500,
        queue_size=512,
        compression="none",
    )


@pytest.mark.timing_sensitive
def test_telemetry_off_baseline_performance() -> None:
    """telemetry off:不起后台线程,分配峰值在有证据的量级内。

    PART B W-04: 线程断言从「相等」改为「不增长」——同进程内前一个 on 路径
    exporter 线程回收晚于本测试取基线时会出现 after < before（实测 17→14，
    文件内 line ~126 注释已承认该 teardown 噪声）；off 路径的判别语义是
    「不新增线程」，增长判据不会削弱它。
    """
    threads_before = _baseline_thread_count()
    tracemalloc.start()
    for _ in range(_ITERATIONS):
        _state_with(None)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    after = _baseline_thread_count()
    assert after <= threads_before, (
        f"off path must not spawn threads: before={threads_before} after={after}"
    )
    assert peak < _PEAK_ALLOC_LIMIT_BYTES, f"off-path peak allocation regressed: {peak} bytes"


def test_telemetry_on_overhead_is_bounded_and_shutdown_clean(
    receiver: OtlpHttpReceiver,
) -> None:
    """on 路径:业务场景照常成功、无 drop、线程有界且 shutdown 后归还。"""
    threads_before = _baseline_thread_count()
    rss_before = _rss_mib()
    failsafe = build_telemetry_sink(_config(receiver.endpoint))
    try:
        for _ in range(_ITERATIONS):
            state = _state_with(failsafe)
            assert state, "scenario must keep succeeding under telemetry"
        # 非恒真:drop_count 现在聚合 inner 计数,导出失败会让它 > 0
        # (证明见 test_lifecycle_bounds.py::test_exporter_failure_is_visible_in_drop_count)
        assert failsafe.drop_count == 0, f"unexpected drops: {failsafe.last_error}"
        growth = threading.active_count() - threads_before
        assert growth <= _MAX_TELEMETRY_THREADS, f"unexpected thread growth: {growth}"
    finally:
        failsafe.flush(timeout_seconds=5.0)
        failsafe.shutdown(timeout_seconds=5.0)
    # 非空性用"真的导出了字节"来证明,而不是线程增量:同进程内前一个测试的
    # exporter 线程尚未回收会抬高 baseline,实测出现过 growth == -1。
    assert receiver.payloads, (
        "telemetry-on must actually export OTLP bytes; an empty receiver means the sink "
        "silently fell back to Null and this test proves nothing"
    )
    assert threading.active_count() <= threads_before + 1, "exporter threads must be released"
    rss_growth = _rss_mib() - rss_before
    assert rss_growth < _MAX_RSS_GROWTH_MIB, f"RSS grew {rss_growth:.1f} MiB (leak suspected)"


@pytest.mark.timing_sensitive
def test_telemetry_on_latency_overhead_bounded(receiver: OtlpHttpReceiver) -> None:
    """on 路径每场景均耗不超过 off 的 8 倍(导出异步,业务路径近零开销)。

    PART B W-04: off/on 各测 3 轮取中位数——单轮在并发负载下会放大比例
    噪声(负载偏高时 off_seconds 本身膨胀)，中位数保留判别比不引入恒真。
    """

    def _measure(enabled: bool) -> float:
        sink = build_telemetry_sink(_config(receiver.endpoint)) if enabled else None
        start = time.perf_counter()
        try:
            for _ in range(_ITERATIONS):
                _state_with(sink)
            return time.perf_counter() - start
        finally:
            if sink is not None:
                sink.shutdown(timeout_seconds=5.0)

    def _median(values: list[float]) -> float:
        ordered = sorted(values)
        mid = len(ordered) // 2
        if len(ordered) % 2 == 1:
            return ordered[mid]
        return (ordered[mid - 1] + ordered[mid]) / 2.0

    off_seconds = _median([_measure(False) for _ in range(3)])
    on_seconds = _median([_measure(True) for _ in range(3)])
    assert on_seconds < max(off_seconds * 8.0, off_seconds + 1.0), (
        f"telemetry overhead too high: off={off_seconds:.3f}s on={on_seconds:.3f}s"
    )
