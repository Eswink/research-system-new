"""SqliteAgentStore：AgentSpec 配置的 SQLite 持久化（M13-R1）。

与 SqliteModelStore 同构（JSON-blob-per-row + 显式枚举映射），
延续 M13 控制面配置存储模式；M14 PostgreSQL canonical state 落地后
走同一 AgentStore Port。
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect, now_iso
from packages.domain.enums import BackendKind, ModelBindingMode, WorkspacePolicy
from packages.domain.roles import AgentBinding, AgentContextConfig, AgentSpec

_SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
    agent_id TEXT PRIMARY KEY,
    agent_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class SqliteAgentStore(SqliteAdapterBase):
    """SQLite 持久化 AgentStore；list/get/save/delete + close 语义。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("agent_store")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def list_agents(self) -> list[AgentSpec]:
        self._ensure_open()
        rows = self._conn.execute(
            "SELECT agent_json FROM agents ORDER BY created_at, agent_id"
        ).fetchall()
        agents = [_decode(json.loads(row["agent_json"])) for row in rows]
        self._record("list_agents", "", result=str(len(agents)))
        return agents

    def get_agent(self, agent_id: str) -> AgentSpec:
        self._ensure_open()
        row = self._conn.execute(
            "SELECT agent_json FROM agents WHERE agent_id = ?", (agent_id,)
        ).fetchone()
        if row is None:
            self._record("get_agent", agent_id, error="KeyError")
            raise KeyError(f"agent not found: {agent_id!r}")
        self._record("get_agent", agent_id, result=agent_id)
        return _decode(json.loads(row["agent_json"]))

    def save_agent(self, agent: AgentSpec) -> None:
        self._ensure_open()
        payload = _encode(agent)
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO agents (agent_id, agent_json, created_at) VALUES (?, ?, ?)",
                (agent.id, json.dumps(payload, ensure_ascii=False, sort_keys=True), now_iso(None)),
            )
        self._record("save_agent", agent.id)

    def delete_agent(self, agent_id: str) -> None:
        self._ensure_open()
        with self._conn:
            cursor = self._conn.execute("DELETE FROM agents WHERE agent_id = ?", (agent_id,))
        if cursor.rowcount == 0:
            self._record("delete_agent", agent_id, error="KeyError")
            raise KeyError(f"agent not found: {agent_id!r}")
        self._record("delete_agent", agent_id)


def _encode(agent: AgentSpec) -> dict[str, Any]:
    return {
        "id": agent.id,
        "role": agent.role,
        "model_binding": {
            "mode": agent.model_binding.mode.value,
            "value": agent.model_binding.value,
        },
        "workspace_policy": agent.workspace_policy.value if agent.workspace_policy else None,
        "skill_refs": list(agent.skill_refs),
        "capability_refs": list(agent.capability_refs),
        "context": {
            "max_context_tokens": agent.context.max_context_tokens,
            "max_iterations": agent.context.max_iterations,
        }
        if agent.context is not None
        else None,
        "runtime_kind": agent.runtime_kind.value if agent.runtime_kind else None,
        "budget_policy_ref": agent.budget_policy_ref,
    }


def _decode(record: dict[str, Any]) -> AgentSpec:
    binding = record.get("model_binding") or {}
    context = record.get("context") or {}
    runtime = record.get("runtime_kind")
    binding_value = binding.get("value")
    return AgentSpec(
        id=record["id"],
        role=record["role"],
        model_binding=AgentBinding(
            mode=ModelBindingMode(binding.get("mode", "INHERIT")),
            value=binding_value,
        ),
        workspace_policy=(
            WorkspacePolicy(record["workspace_policy"]) if record.get("workspace_policy") else None
        ),
        skill_refs=list(record.get("skill_refs", [])),
        capability_refs=list(record.get("capability_refs", [])),
        context=AgentContextConfig(
            max_context_tokens=context.get("max_context_tokens"),
            max_iterations=context.get("max_iterations"),
        ),
        runtime_kind=BackendKind(runtime) if runtime else None,
        budget_policy_ref=record.get("budget_policy_ref"),
    )
