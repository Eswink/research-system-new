"""Shared run-scoped evidence projection for read-only control-plane routers.

`evidence_of_run` walks persisted claims → relations → evidence and keeps only
evidence whose `run_id` matches. Multiple routers (inspection, lineage) need the
same projection; keeping one implementation avoids divergence in run isolation.
"""

from __future__ import annotations

from packages.application.ports import EvidenceLedger
from packages.domain.evidence import Evidence


def evidence_of_run(ledger: EvidenceLedger, run_id: str) -> tuple[Evidence, ...]:
    """从 ledger 查询 run 的 evidence（经 relations_for_claim 投影）。"""
    found: list[Evidence] = []
    seen: set[str] = set()
    for claim in ledger.claims():
        for relation in ledger.relations_for_claim(claim.id):
            evidence_id = relation.evidence_id
            if evidence_id in seen:
                continue
            seen.add(evidence_id)
            try:
                evidence = ledger.get_evidence(evidence_id)
            except Exception:  # noqa: BLE001 - 引用可能已删除（视觉态：missing evidence）
                continue
            if evidence.run_id == run_id:
                found.append(evidence)
    return tuple(found)
