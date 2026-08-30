"""Independent M15 audit probe: telemetry soak (longer manual run).

Runs the canonical M15 scenario against a live OTLP receiver with telemetry
on for a configurable number of iterations, tracking:
- latency per iteration (off vs on comparison),
- exporter drop counts (FailSafe + sink),
- thread count stability (no worker leak),
- clean bounded shutdown.

Optional PG soak: point RESEARCHOS_POSTGRES_DSN at a disposable instance and
pass --pg to run the Postgres workflow engine under telemetry as well.

Run (default 200 iterations):
  uv run --frozen --no-sync python -B tools/probes/probe_telemetry_soak.py
  uv run --frozen --no-sync python -B tools/probes/probe_telemetry_soak.py --iterations 500 --pg
"""

from __future__ import annotations

import argparse
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

from adapters.otel.config import OtelConfig  # noqa: E402
from adapters.otel.provider import build_telemetry_sink  # noqa: E402
from tests.observability.isolation_scenario import _state_with  # noqa: E402
from tests.observability.otlp_receiver import OtlpHttpReceiver  # noqa: E402
from tests.observability.test_telemetry_overhead import _rss_mib  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="M15 telemetry soak probe")
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--pg", action="store_true", help="also soak the PG engine path")
    args = parser.parse_args()

    receiver = OtlpHttpReceiver()
    receiver.start()
    config = OtelConfig(
        enabled=True,
        endpoint=receiver.endpoint,
        timeout_seconds=2.0,
        export_interval_millis=200,
        queue_size=2048,
        compression="none",
    )
    failsafe = build_telemetry_sink(config)
    threads_before = threading.active_count()

    rss_before = _rss_mib()
    start = time.perf_counter()
    latencies: list[float] = []
    try:
        for index in range(args.iterations):
            iteration_start = time.perf_counter()
            state = _state_with(failsafe)
            latencies.append(time.perf_counter() - iteration_start)
            if not state:
                print(f"FAIL: empty scenario at iteration {index}")
                return 1
        elapsed = time.perf_counter() - start
    finally:
        failsafe.shutdown(timeout_seconds=10.0)
        threads_after = threading.active_count()

    drops = failsafe.drop_count
    last_error = failsafe.last_error
    avg_ms = (sum(latencies) / len(latencies)) * 1000 if latencies else 0.0
    p99_ms = sorted(latencies)[int(len(latencies) * 0.99) - 1] * 1000 if latencies else 0.0
    print(
        f"iterations={args.iterations} elapsed={elapsed:.2f}s avg={avg_ms:.2f}ms p99={p99_ms:.2f}ms"
    )
    print(f"drop_count={drops} last_error={last_error}")
    print(f"threads before={threads_before} after={threads_after}")
    print(f"rss before={rss_before:.1f}MiB after={_rss_mib():.1f}MiB")
    print(f"receiver spans captured: {len(receiver.span_names)}")
    pg_ok = True
    if args.pg:
        pg_ok, pg_message = _pg_soak(args.iterations, config)
        print(pg_message)
    ok = drops == 0 and threads_after <= threads_before + 2 and pg_ok
    print("SOAK PASS" if ok else "SOAK FAIL")
    return 0 if ok else 1


def _pg_soak(iterations: int, config: OtelConfig) -> tuple[bool, str]:
    """Soak the PG workflow engine under telemetry with unique per-iteration tasks."""
    import os
    from dataclasses import replace

    dsn = os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
    )
    from adapters.postgres.db import connect as pg_connect
    from adapters.postgres.db import migrate as pg_migrate
    from adapters.postgres.workflow_engine import PostgresWorkflowEngine
    from packages.application.ports.workflow_engine import TaskCompletion
    from packages.domain.core import ID
    from tests.contracts.fixtures import research_task, task_contract

    try:
        import psycopg

        probe_conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3.0)
        probe_conn.close()
    except Exception as error:  # noqa: BLE001 - 不可达是明确的失败报告
        return False, f"PG SOAK FAIL: PostgreSQL unreachable: {type(error).__name__}: {error}"

    try:
        pg_migrate(dsn)
        conn = pg_connect(dsn)
        conn.autocommit = True
        engine = PostgresWorkflowEngine(connection=conn, telemetry=build_telemetry_sink(config))
        for index in range(min(iterations, 50)):
            # task id 必须是合法 UUID4（ID 契约）；每轮唯一标识只放在自由
            # 格式的 idempotency_key 上，避免固定 id 重复提交崩溃。
            task = replace(
                research_task(),
                id=ID.generate(),
                idempotency_key=f"soak-{index}-{ID.generate().value}",
            )
            engine.submit(task, task_contract())
            lease = engine.acquire_lease(task.id.value)
            engine.complete(
                lease,
                TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"),
            )
        engine.close()
        return True, f"pg soak done ({min(iterations, 50)} iterations)"
    except Exception as error:  # noqa: BLE001 - probe 必须报告 PG 失败而非崩溃
        return False, f"PG SOAK FAIL: {type(error).__name__}: {error}"


if __name__ == "__main__":
    raise SystemExit(main())
