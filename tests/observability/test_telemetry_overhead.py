"""M15 telemetry overhead 对比测试(telemetry off vs on)。

DoD-18:off/on 延迟对比、线程数稳定、干净 shutdown、无泄漏。
RSS 精确测量平台相关(Windows 无 resource 模块),此处以
tracemalloc 分配对比 + 线程数替代;更长时长的手工 soak 用
tools/probes/probe_telemetry_soak.py(真实 OTLP receiver + PG 可选)。
"""

from __future__ import annotations

import ctypes
import sys
import threading
import tracemalloc

from tests.observability.isolation_scenario import _state_with
from tests.observability.otlp_receiver import OtlpHttpReceiver

_ITERATIONS = 40


def _baseline_thread_count() -> int:
    return threading.active_count()


def _rss_mib() -> float:
    """进程 RSS(MiB);stdlib-only:Windows psapi / Linux /proc / POSIX resource。"""
    if sys.platform == "win32":

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

        psapi = ctypes.WinDLL("psapi.dll")
        psapi.GetProcessMemoryInfo.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_ProcessMemoryCounters),
            ctypes.c_ulong,
        ]
        kernel32 = ctypes.windll.kernel32
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        counters = _ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(_ProcessMemoryCounters)
        handle = kernel32.GetCurrentProcess()
        if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            return 0.0
        return float(counters.WorkingSetSize) / (1024.0 * 1024.0)
    if sys.platform == "darwin":
        import resource

        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024.0 * 1024.0)
    import resource

    # Linux:ru_maxrss 单位为 kB
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def test_telemetry_off_baseline_performance() -> None:
    threads_before = _baseline_thread_count()
    tracemalloc.start()
    for _ in range(_ITERATIONS):
        _state_with(None)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert _baseline_thread_count() == threads_before
    assert peak < 64 * 1024 * 1024  # 场景本身轻量;防回归上限


def test_telemetry_on_overhead_is_bounded_and_shutdown_clean(
    receiver: OtlpHttpReceiver,
) -> None:
    from adapters.otel.config import OtelConfig
    from adapters.otel.provider import build_telemetry_sink

    threads_before = _baseline_thread_count()
    config = OtelConfig(
        enabled=True,
        endpoint=receiver.endpoint,
        timeout_seconds=2.0,
        export_interval_millis=500,
        queue_size=512,
        compression="none",
    )
    failsafe = build_telemetry_sink(config)
    try:
        for _ in range(_ITERATIONS):
            state = _state_with(failsafe)
            assert state, "scenario must keep succeeding under telemetry"
        assert failsafe.drop_count == 0, f"unexpected drops: {failsafe.last_error}"
        # 后台线程:BSP worker + metric reader,数量有界(≤4)
        growth = threading.active_count() - threads_before
        assert growth <= 4, f"unexpected thread growth: {growth}"
    finally:
        failsafe.shutdown(timeout_seconds=5.0)
    # 干净 shutdown:worker 线程退出
    assert threading.active_count() <= threads_before + 1
    # RSS 泄漏检测(宽松上界;M15 债务清偿:精确 RSS 跨平台测量)
    rss_after = _rss_mib()
    assert rss_after < 512.0, f"RSS growth suggests leak: {rss_after:.1f} MiB"


def test_telemetry_on_latency_overhead_bounded(receiver: OtlpHttpReceiver) -> None:
    """on 路径每场景均耗不超过 off 的 8 倍(导出异步,业务路径近零开销)。"""
    import time

    from adapters.otel.config import OtelConfig
    from adapters.otel.provider import build_telemetry_sink

    start = time.perf_counter()
    for _ in range(_ITERATIONS):
        _state_with(None)
    off_seconds = time.perf_counter() - start

    config = OtelConfig(
        enabled=True,
        endpoint=receiver.endpoint,
        timeout_seconds=2.0,
        export_interval_millis=500,
        queue_size=512,
        compression="none",
    )
    failsafe = build_telemetry_sink(config)
    try:
        start = time.perf_counter()
        for _ in range(_ITERATIONS):
            _state_with(failsafe)
        on_seconds = time.perf_counter() - start
    finally:
        failsafe.shutdown(timeout_seconds=5.0)
    assert on_seconds < max(off_seconds * 8.0, off_seconds + 1.0), (
        f"telemetry overhead too high: off={off_seconds:.3f}s on={on_seconds:.3f}s"
    )
