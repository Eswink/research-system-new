"""PG 评审结论存储（GOAL-20261008-035 EC-01）：往返、幂等、run 隔离。

跑在 live PG 上（`postgres` 标记）；语义与 `SqliteReviewFindingStore` 同一份口径
（两边都实现 `ReviewFindingStore`）。
"""

from __future__ import annotations

import uuid

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.review_finding_store import PostgresReviewFindingStore
from packages.application.ports.review_finding_store import ScopedReviewFinding
from packages.domain.core import Timestamp
from packages.domain.evidence import ReviewFinding

pytestmark = pytest.mark.postgres


def _dsn() -> str:
    import os

    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
    )


def _clean() -> None:
    import psycopg

    migrate(_dsn())
    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute("TRUNCATE review_findings CASCADE")
    conn.commit()
    conn.close()


def _scoped(run_id: str, findings: list[str], *, verdict: str = "PASS") -> ScopedReviewFinding:
    task_id = uuid.uuid4().hex
    return ScopedReviewFinding(
        finding=ReviewFinding(
            id=f"finding:{task_id}:gate",
            review_type="acceptance_gate",
            verdict=verdict,
            findings=findings,
            reviewed_by="gate:domain_a",
            reviewed_at=Timestamp.now(),
        ),
        run_id=run_id,
        task_id=task_id,
        contract_id="real_retrieval_deliverable",
    )


def test_roundtrip_keeps_the_verdict_words_verbatim() -> None:
    """判词逐字回读（读面读原文，不重排、不截断）。"""
    _clean()
    store = PostgresReviewFindingStore(dsn=_dsn())
    run_id = uuid.uuid4().hex
    lines = [
        "ARTIFACT_EXISTS: artifact analysis_report exists",
        "EVIDENCE_COVERAGE: 3 >= 1 sources; 2 >= 1 retrieved",
    ]
    store.put(_scoped(run_id, lines))
    stored = store.for_run(run_id)
    assert len(stored) == 1
    assert stored[0].finding.findings == lines
    assert stored[0].finding.verdict == "PASS"
    assert stored[0].run_id == run_id
    assert stored[0].contract_id == "real_retrieval_deliverable"
    assert stored[0].finding.reviewed_by == "gate:domain_a"
    store.close()


def test_second_put_of_the_same_finding_is_a_noop() -> None:
    """同一 finding id 重复写是幂等空操作（append-only，首写不改）。"""
    _clean()
    store = PostgresReviewFindingStore(dsn=_dsn())
    run_id = uuid.uuid4().hex
    first = _scoped(run_id, ["EVIDENCE_COVERAGE: 1 >= 1 sources"], verdict="PASS")
    store.put(first)
    store.put(
        ScopedReviewFinding(
            finding=ReviewFinding(
                id=first.finding.id,
                review_type="acceptance_gate",
                verdict="REJECT",
                findings=["EVIDENCE_COVERAGE: 0 < 1 sources"],
            ),
            run_id=run_id,
            task_id=first.task_id,
            contract_id=first.contract_id,
        )
    )
    stored = store.for_run(run_id)
    assert len(stored) == 1, stored
    assert stored[0].finding.verdict == "PASS", stored[0]
    store.close()


def test_for_run_is_scoped_by_run() -> None:
    """run 级隔离：别的 run 的结论不出现。"""
    _clean()
    store = PostgresReviewFindingStore(dsn=_dsn())
    mine, other = uuid.uuid4().hex, uuid.uuid4().hex
    store.put(_scoped(mine, ["EVIDENCE_COVERAGE: 1 >= 1 sources"]))
    store.put(_scoped(other, ["EVIDENCE_COVERAGE: 2 >= 1 sources"]))
    assert len(store.for_run(mine)) == 1
    assert store.for_run(other)[0].run_id == other
    assert store.for_run(uuid.uuid4().hex) == ()
    store.close()
