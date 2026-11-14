"""记忆晋升 gate 的**装配面**（GOAL-20261114-113 EC-01；产品路径）。

把**既有** gate 全链（`packages/application/memory/gate.py` 的
schema → provenance → contradiction → policy → curator → sanitize → commit）的
`MemoryGateDeps` 包成组合根能用的**一行闭包**，与
`prior_knowledge_support.prior_knowledge_builder` / `retrieval_context_support`
**同形同层**。

**为什么需要这一层**：`MemoryGateDeps` 要（store / policy / ledger / events）四件 Port，
而编排依赖里只有 Port 聚合 —— 把「用哪个 store、哪份 policy」这个装配决策收在一处
（两个组合根只差实例）。store 是组合根持有的**同一实例**（与 `memory.read` 的读面同源
⇒ 下一轮的 `prior_knowledge` 读到的是刚落库的记忆）。

**既有语义逐字不变**：不晋升时（合约缺 `memory_export` 声明）本面构造了也不写入；
gate 本体（`_CURATOR_TIERS` 与 curator 判定）逐字未动 —— 声明只是授权来源，不是绕过。
"""

from __future__ import annotations

from typing import Any

from packages.application.memory.gate import MemoryGateDeps


def sqlite_memory_gate(faces: Any, ports: Any) -> MemoryGateDeps:
    """SQLite 组合根的 `memory_gate`（与读写面同一 store 实例；policy 可为 None）。"""
    return MemoryGateDeps(
        store=ports.memory_store,
        policy=faces.policy_evaluator,
        ledger=ports.ledger,
        publisher=ports.events,
    )


def pg_memory_gate(c: dict[str, Any], inputs: Any) -> MemoryGateDeps:
    """PG 组合根的 `memory_gate`（与 SQLite 根同侧，只差 Port 实例）。"""
    return MemoryGateDeps(
        store=c["memory"],
        policy=inputs.policy_bindings.get("policy_evaluator"),
        ledger=c["ledger"],
        publisher=c["events"],
    )


__all__ = ["pg_memory_gate", "sqlite_memory_gate"]
