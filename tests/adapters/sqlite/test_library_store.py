"""SqliteLibraryStore 单元测试（PLAN-20260914-044 WP-A）。

upsert/list（按 project + kind 过滤）/排序/KeyError 语义 + LibraryResource
有界校验（name 空/超长、kind/status 非法、tags 越界）。
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from adapters.sqlite.library_store import SqliteLibraryStore
from packages.application.ports.errors import PermanentPortError
from packages.domain.core import Timestamp
from packages.domain.library import LibraryResource, ResourceKind, ResourceStatus

_EPOCH = Timestamp(datetime(2020, 1, 1, tzinfo=timezone.utc))


def _resource(
    rid: str,
    *,
    kind: ResourceKind = ResourceKind.PROMPT,
    name: str = "r",
    status: ResourceStatus = ResourceStatus.ACTIVE,
    at: Timestamp | None = None,
) -> LibraryResource:
    now = at or Timestamp.now()
    return LibraryResource(
        id=rid,
        project_id="proj-1",
        kind=kind,
        name=name,
        description="",
        content_ref=None,
        tags=(),
        status=status,
        created_at=now,
        updated_at=now,
    )


class TestStore:
    def test_save_get_roundtrip_preserves_fields(self) -> None:
        store = SqliteLibraryStore(":memory:")
        store.save_resource(replace(_resource("res-1", name="Alpha"), tags=("x", "y")))
        loaded = store.get_resource("res-1")
        assert loaded.name == "Alpha"
        assert loaded.kind is ResourceKind.PROMPT
        assert loaded.tags == ("x", "y")
        assert loaded.status is ResourceStatus.ACTIVE

    def test_list_is_deterministic(self) -> None:
        # 同一 created_at 时排序回退到 resource_id（避免 now() 时序依赖）。
        store = SqliteLibraryStore(":memory:")
        store.save_resource(_resource("b", at=_EPOCH))
        store.save_resource(_resource("a", at=_EPOCH))
        assert [item.id for item in store.list_resources("proj-1")] == ["a", "b"]

    def test_list_filters_by_kind(self) -> None:
        store = SqliteLibraryStore(":memory:")
        store.save_resource(_resource("p1", kind=ResourceKind.PROMPT))
        store.save_resource(_resource("d1", kind=ResourceKind.DATASET))
        store.save_resource(_resource("n1", kind=ResourceKind.NOTEBOOK))
        prompts = store.list_resources("proj-1", ResourceKind.PROMPT)
        assert [item.id for item in prompts] == ["p1"]

    def test_list_scopes_by_project(self) -> None:
        store = SqliteLibraryStore(":memory:")
        store.save_resource(_resource("a"))
        store.save_resource(replace(_resource("b"), project_id="proj-2"))
        assert [item.id for item in store.list_resources("proj-1")] == ["a"]

    def test_save_upserts_only_via_entity(self) -> None:
        store = SqliteLibraryStore(":memory:")
        store.save_resource(_resource("x", name="old"))
        store.save_resource(_resource("x", name="new"))
        assert store.get_resource("x").name == "new"
        assert len(store.list_resources("proj-1")) == 1

    def test_get_unknown_raises_key_error(self) -> None:
        store = SqliteLibraryStore(":memory:")
        with pytest.raises(KeyError):
            store.get_resource("nope")

    def test_close_rejects_calls(self) -> None:
        store = SqliteLibraryStore(":memory:")
        store.close()
        with pytest.raises(PermanentPortError):
            store.list_resources("proj-1")


class TestDomain:
    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValueError, match="name"):
            _resource("p", name="   ")

    def test_overlong_name_rejected(self) -> None:
        with pytest.raises(ValueError, match="name"):
            _resource("p", name="n" * 201)

    def test_invalid_kind_rejected(self) -> None:
        with pytest.raises(ValueError, match="kind"):
            _resource("p", kind="spreadsheet")  # type: ignore[arg-type]

    def test_invalid_status_rejected(self) -> None:
        with pytest.raises(ValueError, match="status"):
            _resource("p", status="DELETED")  # type: ignore[arg-type]

    def test_too_many_tags_rejected(self) -> None:
        with pytest.raises(ValueError, match="tags"):
            replace(_resource("p"), tags=tuple(f"t{i}" for i in range(33)))

    def test_archived_transition_is_idempotent_value(self) -> None:
        resource = _resource("p")
        archived = resource.with_status(ResourceStatus.ARCHIVED, at=_EPOCH)
        assert archived.status is ResourceStatus.ARCHIVED
        assert archived.updated_at == _EPOCH
