"""SqliteProjectStore 单元测试（PLAN-041 WP-A）。

upsert/list 排序/KeyError 语义 + ProjectDefinition 有界校验（name 空/超长、
status 非法拒绝）。"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from adapters.sqlite.project_store import SqliteProjectStore
from packages.domain.core import Timestamp
from packages.domain.projects import ProjectDefinition, ProjectStatus

_EPOCH = Timestamp(datetime(2020, 1, 1, tzinfo=timezone.utc))


def _project(
    pid: str,
    name: str = "p",
    status: ProjectStatus = ProjectStatus.ACTIVE,
    at: Timestamp | None = None,
) -> ProjectDefinition:
    now = at or Timestamp.now()
    return ProjectDefinition(id=pid, name=name, status=status, created_at=now, updated_at=now)


class TestStore:
    def test_save_get_roundtrip(self) -> None:
        store = SqliteProjectStore(":memory:")
        project = _project("proj-1", "Alpha")
        store.save_project(project)
        loaded = store.get_project("proj-1")
        assert loaded.name == "Alpha"
        assert loaded.status is ProjectStatus.ACTIVE

    def test_list_is_deterministic(self) -> None:
        # 同一 created_at 时排序回退到 project_id（避免 now() 时序依赖）。
        store = SqliteProjectStore(":memory:")
        store.save_project(_project("b", at=_EPOCH))
        store.save_project(_project("a", at=_EPOCH))
        assert [item.id for item in store.list_projects()] == ["a", "b"]

    def test_save_upserts_and_advances_only_via_entity(self) -> None:
        store = SqliteProjectStore(":memory:")
        store.save_project(_project("x", "old"))
        store.save_project(_project("x", "new"))
        assert store.get_project("x").name == "new"
        assert len(store.list_projects()) == 1

    def test_get_unknown_raises_key_error(self) -> None:
        store = SqliteProjectStore(":memory:")
        with pytest.raises(KeyError):
            store.get_project("nope")


class TestDomain:
    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValueError, match="name"):
            _project("p", "   ")

    def test_overlong_name_rejected(self) -> None:
        with pytest.raises(ValueError, match="name"):
            _project("p", "n" * 201)

    def test_invalid_status_rejected(self) -> None:
        with pytest.raises(ValueError, match="status"):
            _project("p", "ok", status="DELETED")  # type: ignore[arg-type]
