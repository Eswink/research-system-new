"""FakeScheduleStore：内存版 ScheduleStore（错误注入 + 调用记录）。"""

from __future__ import annotations

from adapters.fakes.base import FakeBase
from packages.application.ports.errors import InvalidInputError
from packages.domain.schedules import ScheduleDefinition


class FakeScheduleStore(FakeBase):
    """按 name 索引的内存定义表；语义与 SQLite 实现一致（存在即替换）。"""

    def __init__(self) -> None:
        super().__init__("schedule_store")
        self._definitions: dict[str, ScheduleDefinition] = {}

    def list_definitions(self) -> list[ScheduleDefinition]:
        self._enter("list_definitions", "*")
        definitions = sorted(self._definitions.values(), key=lambda item: item.name)
        self._record("list_definitions", "*", result=f"{len(definitions)} rows")
        return definitions

    def get_definition(self, name: str) -> ScheduleDefinition | None:
        self._enter("get_definition", name)
        found = self._definitions.get(name)
        self._record("get_definition", name, result="hit" if found is not None else "miss")
        return found

    def save_definition(self, definition: ScheduleDefinition) -> None:
        self._enter("save_definition", definition.name)
        self._definitions[definition.name] = definition
        self._record("save_definition", definition.name, result="stored")

    def delete_definition(self, name: str) -> None:
        self._enter("delete_definition", name)
        if name not in self._definitions:
            self._record("delete_definition", name, error="InvalidInputError")
            raise InvalidInputError(f"schedule not found: {name}")
        del self._definitions[name]
        self._record("delete_definition", name, result="deleted")
