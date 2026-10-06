"""Canonical 读面的 **run 投影**（GOAL-031 EC-03 从 `read_provider.py` 拆出）。

**为什么单列**：`read_provider.py` 有 450 行硬上限（规模门），EC-03 给证据条目加了
`artifact_id` 一列（派生链要按它选中上一轮的产出）⇒ 越界。拆分的切法沿用本文件族既有的
「声明面 vs 执行面」（`read_surface.py`）：本模块放**投影**（canonical 事实 → 读面
JSON 形状），`read_provider.py` 放执行分派。**形状逐字不变**（除 EC-03 增的那一列）。
"""

from __future__ import annotations

from packages.application.ports.evidence_ledger import EvidenceLedger


def project_run(ledger: EvidenceLedger, run_id: str) -> dict[str, object]:
    """把 ledger 里属于 `run_id` 的 claim/evidence 投影出来（按 relation 走）。

    **run 归属判定在 evidence 一侧**：`Claim` 域类型没有 `run_id` 字段（claim 是全局
    命题，run 是证据的采集上下文）⇒ 本投影按 `Evidence.run_id == run_id` 筛选，
    只保留**引用到本 run 证据**的 claim。只 register 不 attach_relation 的证据
    **不会**出现在这里（GOAL-010 EC-02 的口径）。
    """
    claims: list[dict[str, object]] = []
    evidence: list[dict[str, object]] = []
    seen: set[str] = set()
    for claim in ledger.claims():
        matched: list[str] = []
        for relation in ledger.relations_for_claim(claim.id):
            try:
                item = ledger.get_evidence(relation.evidence_id)
            except Exception:  # noqa: BLE001 - 引用可能已删除（视觉态：missing evidence）
                continue
            if item.run_id != run_id:
                continue
            matched.append(relation.evidence_id)
            if relation.evidence_id in seen:
                continue
            seen.add(relation.evidence_id)
            evidence.append({
                "id": item.id,
                "source_ref": item.source_ref,
                # GOAL-20261006-031 EC-03：`artifact_id` 与 HTTP 读面
                # （`GET /runs/{id}/evidence` 的 DTO）**同源同列**——工具读面此前少了
                # 这一列，而运行链的「第二轮读第一轮的产出」需要它来**按声明后缀选中**
                # 上一轮的制品（`phase_capability_triggers.select_artifact_id`）。
                # 纯增列：既有键不动。
                "artifact_id": item.artifact_id,
                "content_digest": item.content_digest,
                "relation": str(relation.relation),
            })
        if matched:
            claims.append({
                "id": claim.id,
                "status": str(claim.status),
                "evidence_ids": sorted(matched),
            })
    return {
        "run_id": run_id,
        "claims": sorted(claims, key=lambda item: str(item["id"])),
        "evidence": sorted(evidence, key=lambda item: str(item["id"])),
    }


__all__ = ["project_run"]
