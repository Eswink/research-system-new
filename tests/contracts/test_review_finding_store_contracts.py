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


def test_the_reviewed_object_survives_reopen(tmp_path: Path) -> None:
    """`phase_id`（GOAL-20261018-086 EC-02）**逐字往返**且缺省 `None` 也往返。

    为什么这条必须在**契约层**判：读面按它分组（同一 phase 的评审者收成一份小组），
    落库时丢掉这一格会让小组在生产上**重新消失** —— 而单元层的分组判据仍会绿。
    """
    db_path = tmp_path / "reviews.db"
    run_id = uuid.uuid4().hex
    with_phase = ScopedReviewFinding(
        finding=ReviewFinding(
            id="finding:task-a:gate",
            review_type="acceptance_gate",
            verdict="PASS",
            findings=["ARTIFACT_EXISTS: ok"],
        ),
        run_id=run_id,
        task_id="task-a",
        contract_id="review_scored_deliverable",
        phase_id="review",
    )
    without_phase = ScopedReviewFinding(
        finding=ReviewFinding(
            id="finding:task-b:gate",
            review_type="acceptance_gate",
            verdict="PASS",
            findings=["ARTIFACT_EXISTS: ok"],
        ),
        run_id=run_id,
        task_id="task-b",
        contract_id="review_scored_deliverable",
    )
    store = SqliteReviewFindingStore(db_path)
    store.put(with_phase)
    store.put(without_phase)
    store.close()

    reopened = SqliteReviewFindingStore(db_path)
    by_task = {item.task_id: item for item in reopened.for_run(run_id)}
    assert by_task["task-a"].phase_id == "review"
    assert by_task["task-b"].phase_id is None
    reopened.close()


def test_an_existing_database_gains_the_phase_column(tmp_path: Path) -> None:
    """既有库（表已存在、**无** `phase_id` 列）⇒ 打开时补列，旧行保持 `None`。

    `CREATE TABLE IF NOT EXISTS` **不**给已存在的表加列 —— 只写建表语句会让**升级**后的
    开发库在读面崩掉（`no such column: phase_id`），而新建库的判据照绿。
    """
    import sqlite3

    db_path = tmp_path / "legacy.db"
    legacy = sqlite3.connect(str(db_path))
    legacy.executescript(
        "CREATE TABLE review_findings ("
        " finding_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, task_id TEXT NOT NULL,"
        " contract_id TEXT NOT NULL, review_type TEXT NOT NULL, verdict TEXT NOT NULL,"
        " reviewed_by TEXT, reviewed_at TEXT, findings_json TEXT NOT NULL,"
        " recorded_at TEXT NOT NULL, reviewer_model TEXT);"
    )
    legacy.execute(
        "INSERT INTO review_findings VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            "finding:old:gate",
            "run-old",
            "task-old",
            "c",
            "acceptance_gate",
            "PASS",
            None,
            None,
            "[]",
            "2026-10-18T00:00:00+00:00",
            None,
        ),
    )
    legacy.commit()
    legacy.close()

    store = SqliteReviewFindingStore(db_path)
    stored = store.for_run("run-old")
    assert len(stored) == 1
    assert stored[0].phase_id is None
    store.close()
