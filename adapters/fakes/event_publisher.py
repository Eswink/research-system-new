"""FakeEventPublisher：event_id 幂等发布 + 顺序保留。"""

from __future__ import annotations

from adapters.fakes.base import FakeBase
from packages.application.ports.errors import InvalidInputError
from packages.domain.events import EventEnvelope


class FakeEventPublisher(FakeBase):
    """publish 按 event_id 去重（幂等）；published 保留发布顺序。"""

    def __init__(self) -> None:
        super().__init__("event_publisher")
        self._published: dict[str, EventEnvelope] = {}
        self._order: list[str] = []

    @property
    def published(self) -> tuple[EventEnvelope, ...]:
        return tuple(self._published[event_id] for event_id in self._order)

    def publish(self, envelope: EventEnvelope) -> None:
        self._enter("publish", envelope.event_id)
        if not envelope.event_id:
            self._record("publish", "", error="InvalidInputError")
            raise InvalidInputError("event_id must not be empty")
        first_time = envelope.event_id not in self._published
        if first_time:
            # 幂等契约：重复 event_id 返回首次结果；首次 envelope 不被覆盖，
            # 防止调用方用同 id 发布篡改后的 payload。
            self._published[envelope.event_id] = envelope
            self._order.append(envelope.event_id)
        self._record("publish", envelope.event_id, result="published" if first_time else "deduped")
