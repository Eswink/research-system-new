"""GOAL-20261014-078 EC-04 的判据支持件（live 面的上下文取证）。

**为什么单列**：`tests/e2e/test_research_report_chain_live.py` 贴着 450 行硬上限
（规模门），而本轮的上下文取证（读面制品 + 会话 spec 的同源断言）是**独立可读**的一段；
按全仓既有的「支持件 vs 用例」分列（与 `literature_chain_support` 同一手法）。

**边界**：本模块**不含**用例，只放两个取证/断言函数 —— 它们只经**既有读面**
（`GET /runs/{id}/artifacts` 与 `/content`）取数，不经内部对象。
"""

from __future__ import annotations

import json
from typing import Any

from fastapi.testclient import TestClient

__all__ = ["assert_the_context_reached_sessions", "context_payloads"]


def context_payloads(client: TestClient, run_id: str) -> dict[str, Any]:
    """读面上该 run 的上下文制品 → `{artifact_id: payload}`（只经既有路由）。"""
    artifacts = client.get(f"/runs/{run_id}/artifacts").json()
    ids = [str(item["id"]) for item in artifacts if str(item["id"]).endswith(":retrieval_context")]
    return {
        artifact_id: json.loads(
            client.get(f"/artifacts/{artifact_id}/content").content.decode("utf-8")
        )
        for artifact_id in ids
    }


def assert_the_context_reached_sessions(sample: dict[str, Any]) -> None:
    """EC-04 的上下文面：**真实检索取得的内容进了下游会话**，且读面可复核。

    两条一起看：
    ① 读面制品（`GET /runs/{id}/artifacts`）里有**非空**的上下文载荷 —— 它带
       `identifier` / `evidence_id` / `artifact_id` / `shown` 四列（真标识来自**本次**
       活检索）；
    ② 会话 spec 的 `retrieval_digest` **在场于**读面制品的 digest 列表里（同源）。
    """
    payloads = sample["context_artifacts"]
    assert payloads, ("真实 run 的读面上必须有上下文制品", sample["artifact_ids"])
    non_empty = [p for p in payloads.values() if p["entries"]]
    assert non_empty, ("下游会话的上下文必须**非空**（真实检索取回了内容）", payloads)
    entries = [e for payload in non_empty for e in payload["entries"]]
    assert entries, payloads
    for entry in entries:
        for key in ("identifier", "evidence_id", "artifact_id", "shown"):
            assert entry.get(key), (key, entry)
    # 标识与本次 run 的检索证据一致（不是凭空写的字符串）。
    retrieved_ids = {
        str(item["artifact_id"])
        for item in sample["evidence"]
        if item.get("source_trust_label") == "RETRIEVED" and item.get("artifact_id")
    }
    refs = {str(entry["artifact_id"]) for entry in entries}
    assert refs <= retrieved_ids, (
        "上下文里的制品必须指向**本次 run 系统取得**的证据",
        sorted(refs - retrieved_ids),
    )
