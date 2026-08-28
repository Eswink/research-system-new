"""PG evidence_ledger: mirrors sqlite/evidence_ledger.py + evidence_rows.py."""

from __future__ import annotations

from typing import Any

from adapters.postgres.base import PostgresAdapterBase
from adapters.postgres.db import connect as pg_connect
from adapters.postgres.db import dsn_from_env
from adapters.postgres.evidence_rows import (
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
    SourceRecord,
)


class PostgresEvidenceLedger(PostgresAdapterBase):
    def __init__(
        self,
        *,
        dsn: str | None = None,
        connection: Any | None = None,
    ) -> None:
        super().__init__("evidence_ledger")
        self._owns_connection = connection is None
        if connection is not None:
            self._conn: Any = connection
        else:
            resolved = dsn or dsn_from_env()
            if not resolved:
                raise ValueError("PostgresEvidenceLedger requires dsn or connection")
            self._conn = pg_connect(resolved)

    def close(self) -> None:
        if self._owns_connection:
            try:
                self._conn.close()
            except Exception:
                pass
        super().close()

    def register_source(self, source: SourceRecord) -> None:
        self._ensure_open()
        self._record("register_source", source.origin)
        with self._conn.transaction():
            cur = self._conn.execute(
                "INSERT INTO m12_sources (origin, content_digest, trust_label, access_time,"
                " license_terms, authors, parser_version) VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s)"
                " ON CONFLICT (origin) DO NOTHING",
                (
                    source.origin,
                    source.content_digest,
                    source.trust_label.value,
                    source.access_time.value if source.access_time else None,
                    source.license_terms,
                    to_json(source.authors),
                    source.parser_version,
                ),
            )
            if cur.rowcount == 0:
                # Conflict: verify idempotent (same data) or reject (different data).
                existing = self._source_row(source.origin)
                if existing is not None and not same_source(existing, source):
                    raise InvalidInputError(f"conflicting source registration: {source.origin}")

    def register_evidence(self, evidence: Evidence) -> None:
        self._ensure_open()
        self._record("register_evidence", evidence.id)
        with self._conn.transaction():
            cur = self._conn.execute(
                "INSERT INTO m12_evidence (id, source_ref, content_digest, extracted_by,"
                " captured_at, artifact_id, run_id, experiment_run_id, metric_refs,"
                " workspace_snapshot_before, workspace_snapshot_after, image_digest,"
                " environment_digest, tool_refs, skill_refs, model_refs, manifest_digest)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,"
                " %s::jsonb,%s::jsonb,%s::jsonb,%s)"
                " ON CONFLICT (id) DO NOTHING",
                (
                    evidence.id,
                    evidence.source_ref,
                    evidence.content_digest,
                    evidence.extracted_by,
                    evidence.captured_at.value if evidence.captured_at else None,
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
            if cur.rowcount == 0:
                existing = self._evidence_row(evidence.id)
                if existing is not None and not same_evidence(existing, evidence):
                    raise InvalidInputError(f"conflicting evidence registration: {evidence.id}")

    def register_claim(self, claim: Claim) -> None:
        self._ensure_open()
        self._record("register_claim", claim.id)
        with self._conn.transaction():
            # Atomic: verify provenance (FOR SHARE) + insert in same tx.
            if claim.status is ClaimStatus.VERIFIED:
                self._verify_provenance_in_tx(claim)
            cur = self._conn.execute(
                "INSERT INTO m12_claims (id, statement, status, author, evidence_relations)"
                " VALUES (%s,%s,%s,%s,%s::jsonb)"
                " ON CONFLICT (id) DO NOTHING",
                claim_values(claim),
            )
            if cur.rowcount == 0:
                existing = self._claim_row(claim.id)
                if existing is not None and claim_from_row(existing) != claim:
                    raise InvalidInputError(f"conflicting claim registration: {claim.id}")

    def update_claim(self, claim: Claim) -> None:
        self._ensure_open()
        self._record("update_claim", claim.id)
        with self._conn.transaction():
            # Atomic: verify provenance (FOR SHARE) + update in same tx.
            if claim.status is ClaimStatus.VERIFIED:
                self._verify_provenance_in_tx(claim)
            if self._claim_row(claim.id) is None:
                raise InvalidInputError(f"unknown claim id: {claim.id}")
            relations = to_json([
                (evidence_id, relation.value) for evidence_id, relation in claim.evidence_relations
            ])
            cur = self._conn.execute(
                "UPDATE m12_claims SET statement=%s, status=%s, author=%s,"
                " evidence_relations=%s::jsonb WHERE id=%s",
                (claim.statement, claim.status.value, claim.author, relations, claim.id),
            )
            if cur.rowcount == 0:
                raise InvalidInputError(f"unknown claim id: {claim.id}")

    def attach_relation(self, relation: EvidenceRelation) -> None:
        self._ensure_open()
        self._record("attach_relation", f"{relation.claim_id}->{relation.evidence_id}")
        if self._claim_row(relation.claim_id) is None:
            raise InvalidInputError(f"unknown claim id: {relation.claim_id}")
        if self._evidence_row(relation.evidence_id) is None:
            raise InvalidInputError(f"unknown evidence id: {relation.evidence_id}")
        with self._conn.transaction():
            self._conn.execute(
                "INSERT INTO m12_relations (claim_id, evidence_id, relation, strength)"
                " VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
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

        from packages.domain.evidence import EvidenceRelationType

        rows: Any = self._conn.execute(
            "SELECT * FROM m12_relations WHERE claim_id=%s ORDER BY relation", (claim_id,)
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
        rows: Any = self._conn.execute("SELECT * FROM m12_claims ORDER BY id").fetchall()
        return tuple(claim_from_row(row) for row in rows)

    def _source_row(self, origin: str) -> Any:
        return self._conn.execute("SELECT * FROM m12_sources WHERE origin=%s", (origin,)).fetchone()

    def _evidence_row(self, evidence_id: str) -> Any:
        return self._conn.execute(
            "SELECT * FROM m12_evidence WHERE id=%s", (evidence_id,)
        ).fetchone()

    def _claim_row(self, claim_id: str) -> Any:
        return self._conn.execute("SELECT * FROM m12_claims WHERE id=%s", (claim_id,)).fetchone()

    def _verify_provenance_in_tx(self, claim: Claim) -> None:
        """Verify VERIFIED claim provenance within current transaction (FOR SHARE)."""
        for evidence_id, _rel in claim.evidence_relations:
            evidence = self._conn.execute(
                "SELECT * FROM m12_evidence WHERE id = %s FOR SHARE",
                (evidence_id,),
            ).fetchone()
            if evidence is None:
                raise InvalidInputError(
                    f"VERIFIED claim {claim.id} references unknown evidence {evidence_id!r}"
                )
            source = self._conn.execute(
                "SELECT * FROM m12_sources WHERE origin = %s FOR SHARE",
                (evidence["source_ref"],),
            ).fetchone()
            if source is None:
                raise InvalidInputError(
                    f"VERIFIED claim {claim.id} evidence {evidence_id!r}"
                    f" source {evidence['source_ref']!r} is not registered"
                )
