"""`ReviewFindingStore` Port 的 SQLite 实现契约（GOAL-20261008-035 EC-01）。

与 `tests/postgres/test_review_finding_store_pg.py` 同一份语义（两个实现同一口径）：
判词逐字回读、同 id 重复写是幂等空操作、run 级隔离、**跨 reopen 持久化**（读面在
重启后仍读得到结论 —— 这正是「落库」与「内存里算一下」的分界）。
"""

from __future__ import annotations

import uuid
from pathlib import Path

from adapters.sqlite.review_finding_store import SqliteReviewFindingStore
from packages.application.ports.review_finding_store import ScopedReviewFinding
from packages.domain.core import Timestamp
from packages.domain.evidence import ReviewFinding

_LINES = [
    "ARTIFACT_EXISTS: artifact analysis_report exists",
    "EVIDENCE_COVERAGE: 3 >= 1 sources; 2 >= 1 retrieved",
]


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


def test_roundtrip_survives_reopen_with_verdict_words_verbatim(tmp_path: Path) -> None:
    db_path = tmp_path / "reviews.db"
    run_id = uuid.uuid4().hex
    store = SqliteReviewFindingStore(db_path)
    store.put(_scoped(run_id, _LINES))
    store.close()

    reopened = SqliteReviewFindingStore(db_path)
    stored = reopened.for_run(run_id)
    assert len(stored) == 1
    assert stored[0].finding.findings == _LINES
    assert stored[0].finding.verdict == "PASS"
    assert stored[0].run_id == run_id
    assert stored[0].contract_id == "real_retrieval_deliverable"
    assert stored[0].finding.reviewed_by == "gate:domain_a"
    assert stored[0].finding.reviewed_at is not None
    reopened.close()


def test_second_put_of_the_same_finding_is_a_noop(tmp_path: Path) -> None:
    store = SqliteReviewFindingStore(tmp_path / "reviews.db")
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


def test_for_run_is_scoped_by_run(tmp_path: Path) -> None:
    store = SqliteReviewFindingStore(tmp_path / "reviews.db")
    mine, other = uuid.uuid4().hex, uuid.uuid4().hex
    store.put(_scoped(mine, ["EVIDENCE_COVERAGE: 1 >= 1 sources"]))
    store.put(_scoped(other, ["EVIDENCE_COVERAGE: 2 >= 1 sources"]))
    assert len(store.for_run(mine)) == 1
    assert store.for_run(other)[0].run_id == other
    assert store.for_run(uuid.uuid4().hex) == ()
    store.close()
