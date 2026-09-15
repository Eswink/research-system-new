"""OpsStore Port：告警规则与事故登记的配置存储（G7 / PLAN-20260915-059）。

职责：ops 控制面两写面（静音规则、事故处置）的持久化；与 ProjectStore/LibraryStore
同族（配置面，SQLite 共享连接由 composition root 注入）。
非职责：不派生告警（那是 read-model 投影），不调度/通知。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.ops_control import AlertRule, Incident


@runtime_checkable
class OpsStore(Protocol):
    """告警规则与事故的 CRUD；未找到一律抛 `KeyError`（控制面映射 404）。"""

    def list_rules(self, project_id: str) -> list[AlertRule]: ...

    def get_rule(self, rule_id: str) -> AlertRule: ...

    def save_rule(self, rule: AlertRule) -> None: ...

    def delete_rule(self, rule_id: str) -> None: ...

    def list_incidents(self, project_id: str) -> list[Incident]: ...

    def get_incident(self, incident_id: str) -> Incident: ...

    def save_incident(self, incident: Incident) -> None: ...
