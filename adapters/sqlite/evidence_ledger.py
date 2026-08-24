"""SqliteEvidenceLedger：EvidenceLedger Port 的 SQLite 持久化实现（M12-R1 WP9）。

契约与 FakeEvidenceLedger 完全一致（contract suite 注册表驱动双实现验证）：
- 同键重登内容不一致失败（防静默漂移）；未知 id 查询抛 InvalidInputError；
- attach_relation 强制引用完整性（claim + evidence 必须已登记）；
- VERIFIED Claim 的 provenance 不变量在登记面强制（每个 relation 的
  evidence 与其 source 必须已登记）——防止绕过 promote_claim_to_verified
  的直写路径（M10 复审强化，contract suite 强制）；
- 持久化：source/evidence/claim/relation 四表 + canonical JSON 序列化，
  跨进程重启可恢复（M12 生产链证据不可丢）。

SQLite 是本轮生产持久化边界（M14 前不引入 PostgreSQL）。
行映射在 evidence_rows.py（模块规模阈值拆分）。
"""

from __future__ import annotations

import sqlite3

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.evidence_rows import (
    EVIDENCE_COLS,
    SCHEMA,
    SOURCE_COLS,
    claim_from_row,
    claim_values,
    evidence_from_row,
    same_evidence,
    same_source,
    source_from_row,
    to_json,
)
from packages.application.ports.errors import InvalidInputError
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)


class SqliteEvidenceLedger(SqliteAdapterBase):
    """SQLite 持久化 EvidenceLedger；共享连接可参与外部事务边界。"""

    def __init__(self, connection: sqlite3.Connection | str = ":memory:") -> None:
        super().__init__("evidence_ledger")
        if isinstance(connection, str):
            self._connection = sqlite3.connect(connection)
        else:
            self._connection = connection
        self._connection.row_factory = sqlite3.Row
        self._connection.executescript(SCHEMA)
        self._connection.commit()

    # --- Port 实现 ---

    def register_source(self, source: SourceRecord) -> None:
        self._ensure_open()
        self._record("register_source", source.origin)
        existing = self._source_row(source.origin)
        if existing is not None and not same_source(existing, source):
            raise InvalidInputError(f"conflicting source registration: {source.origin}")
        if existing is not None:
            return
        with self._connection:
            self._connection.execute(
                f"INSERT INTO m12_sources ({SOURCE_COLS}) VALUES (?,?,?,?,?,?,?)",
                (
                    source.origin,
                    source.content_digest,
                    source.trust_label.value,
                    source.access_time.value.isoformat() if source.access_time else None,
                    source.license_terms,
                    to_json(source.authors),
                    source.parser_version,
                ),
            )

    def register_evidence(self, evidence: Evidence) -> None:
        self._ensure_open()
        self._record("register_evidence", evidence.id)
        existing = self._evidence_row(evidence.id)
        if existing is not None and not same_evidence(existing, evidence):
            raise InvalidInputError(f"conflicting evidence registration: {evidence.id}")
        if existing is not None:
            return
        with self._connection:
            self._connection.execute(
                f"INSERT INTO m12_evidence ({EVIDENCE_COLS}) VALUES "
                "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    evidence.id,
                    evidence.source_ref,
                    evidence.content_digest,
                    evidence.extracted_by,
                    evidence.captured_at.value.isoformat() if evidence.captured_at else None,
                    evidence.artifact_id,
                    evidence.run_id,
                    evidence.experiment_run_id,
                    to_json(list(evidence.metric_refs)),
                    evidence.workspace_snapshot_before,
                    evidence.workspace_snapshot_after,
                    evidence.image_digest,
                    evidence.environment_digest,
                    to_json(list(evidence.tool_refs)),
                    to_json(list(evidence.skill_refs)),
                    to_json(list(evidence.model_refs)),
                    evidence.manifest_digest,
                ),
            )

    def register_claim(self, claim: Claim) -> None:
        self._ensure_open()
        self._record("register_claim", claim.id)
        self._require_verifiable(claim)
        existing = self._claim_row(claim.id)
        if existing is not None and claim_from_row(existing) != claim:
            raise InvalidInputError(f"conflicting claim registration: {claim.id}")
        if existing is not None:
            return
        with self._connection:
            self._connection.execute(
                "INSERT INTO m12_claims (id, statement, status, author, evidence_relations) "
                "VALUES (?,?,?,?,?)",
                claim_values(claim),
            )

    def update_claim(self, claim: Claim) -> None:
        self._ensure_open()
        self._record("update_claim", claim.id)
        self._require_verifiable(claim)
        if self._claim_row(claim.id) is None:
            raise InvalidInputError(f"unknown claim id: {claim.id}")
        relations = to_json([
            (evidence_id, relation.value) for evidence_id, relation in claim.evidence_relations
        ])
        with self._connection:
            self._connection.execute(
                "UPDATE m12_claims SET statement=?, status=?, author=?, "
                "evidence_relations=? WHERE id=?",
                (claim.statement, claim.status.value, claim.author, relations, claim.id),
            )

    def attach_relation(self, relation: EvidenceRelation) -> None:
        self._ensure_open()
        self._record("attach_relation", f"{relation.claim_id}->{relation.evidence_id}")
        if self._claim_row(relation.claim_id) is None:
            raise InvalidInputError(f"unknown claim id: {relation.claim_id}")
        if self._evidence_row(relation.evidence_id) is None:
            raise InvalidInputError(f"unknown evidence id: {relation.evidence_id}")
        with self._connection:
            self._connection.execute(
                "INSERT OR IGNORE INTO m12_relations VALUES (?,?,?,?)",
                (
                    relation.claim_id,
                    relation.evidence_id,
                    relation.relation.value,
                    relation.strength,
                ),
            )

    def get_source(self, origin: str) -> SourceRecord:
        self._ensure_open()
        self._record("get_source", origin)
        row = self._source_row(origin)
        if row is None:
            raise InvalidInputError(f"unknown source origin: {origin}")
        return source_from_row(row)

    def get_evidence(self, evidence_id: str) -> Evidence:
        self._ensure_open()
        self._record("get_evidence", evidence_id)
        row = self._evidence_row(evidence_id)
        if row is None:
            raise InvalidInputError(f"unknown evidence id: {evidence_id}")
        return evidence_from_row(row)

    def get_claim(self, claim_id: str) -> Claim:
        self._ensure_open()
        self._record("get_claim", claim_id)
        row = self._claim_row(claim_id)
        if row is None:
            raise InvalidInputError(f"unknown claim id: {claim_id}")
        return claim_from_row(row)

    def relations_for_claim(self, claim_id: str) -> tuple[EvidenceRelation, ...]:
        self._ensure_open()
        self._record("relations_for_claim", claim_id)
        if self._claim_row(claim_id) is None:
            raise InvalidInputError(f"unknown claim id: {claim_id}")
        rows = self._connection.execute(
            "SELECT * FROM m12_relations WHERE claim_id=? ORDER BY relation", (claim_id,)
        ).fetchall()
        return tuple(
            EvidenceRelation(
                claim_id=row["claim_id"],
                evidence_id=row["evidence_id"],
                relation=EvidenceRelationType(row["relation"]),
                strength=row["strength"],
            )
            for row in rows
        )

    def has_source(self, origin: str) -> bool:
        self._ensure_open()
        self._record("has_source", origin)
        return self._source_row(origin) is not None

    def claims(self) -> tuple[Claim, ...]:
        self._ensure_open()
        self._record("claims", "*")
        rows = self._connection.execute("SELECT * FROM m12_claims ORDER BY id").fetchall()
        return tuple(claim_from_row(row) for row in rows)

    def close(self) -> None:
        if not self._closed:
            self._connection.close()
        super().close()

    # --- 内部 ---

    def _source_row(self, origin: str) -> sqlite3.Row | None:
        row = self._connection.execute(
            "SELECT * FROM m12_sources WHERE origin=?", (origin,)
        ).fetchone()
        if row is None:
            return None
        assert isinstance(row, sqlite3.Row)
        return row

    def _evidence_row(self, evidence_id: str) -> sqlite3.Row | None:
        row = self._connection.execute(
            "SELECT * FROM m12_evidence WHERE id=?", (evidence_id,)
        ).fetchone()
        if row is None:
            return None
        assert isinstance(row, sqlite3.Row)
        return row

    def _claim_row(self, claim_id: str) -> sqlite3.Row | None:
        row = self._connection.execute(
            "SELECT * FROM m12_claims WHERE id=?", (claim_id,)
        ).fetchone()
        if row is None:
            return None
        assert isinstance(row, sqlite3.Row)
        return row

    def _require_verifiable(self, claim: Claim) -> None:
        """VERIFIED Claim 的 provenance 不变量（contract suite 强制）。"""
        if claim.status is not ClaimStatus.VERIFIED:
            return
        for evidence_id, _relation in claim.evidence_relations:
            evidence = self._evidence_row(evidence_id)
            if evidence is None:
                raise InvalidInputError(
                    f"VERIFIED claim {claim.id} references unknown evidence {evidence_id!r}"
                )
            if self._source_row(evidence["source_ref"]) is None:
                raise InvalidInputError(
                    f"VERIFIED claim {claim.id} evidence {evidence_id!r} "
                    f"source {evidence['source_ref']!r} is not registered"
                )


__all__ = ["SqliteEvidenceLedger"]
