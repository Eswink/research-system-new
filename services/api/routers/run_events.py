"""Run Timeline 事件投影：SSE 流与 JSON replay（双模式）。

Timeline 是 Canonical/Event State 的 projection（outbox 事件），
不建第二套 Timeline DB；SSE 支持 cursor/resume（Last-Event-ID /
?cursor=）与客户端按 event_id 去重。
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from packages.application.ports import RunProjection
from packages.domain.events import EventEnvelope
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.errors import ApiError
from services.api.run_access import get_run_or_error

router = APIRouter(prefix="/runs", tags=["runs"])

_POLL_SECONDS = 1.0


def events_of(projection: RunProjection, run_id: str) -> tuple[EventEnvelope, ...]:
    """outbox 中 run_id 匹配的事件（按 event_id 排序，天然去重）。"""
    return projection.events(run_id)


def envelope_payload(envelope: EventEnvelope) -> str:
    """事件 payload 序列化（secret 永不进入事件；大 payload 转 artifact ref）。"""
    return json.dumps(
        {
            "event_id": envelope.event_id,
            "type": envelope.event_type.value,
            "schema_version": envelope.schema_version,
            "occurred_at": envelope.occurred_at.value.isoformat(),
            "actor": envelope.actor,
            "scope": envelope.scope,
            "run_id": envelope.run_id,
            "task_id": envelope.task_id,
            "trace_id": envelope.trace_id,
            "payload": dict(envelope.payload),
        },
        ensure_ascii=False,
        sort_keys=True,
    )


async def event_stream(
    projection: RunProjection, run_id: str, cursor: str | None, poll: bool
) -> AsyncIterator[str]:
    """SSE 生成器：按 event_id 升序推送 run 事件；cursor 续传。

    poll=True：轮询 outbox（长连接）；poll=False：发送当前快照后关闭
    （测试与短连接客户端；诚实声明：增量订阅走 poll 模式）。
    """
    seen_last = cursor or ""
    while True:
        for envelope in events_of(projection, run_id):
            if envelope.event_id <= seen_last:
                continue
            seen_last = envelope.event_id
            payload = envelope_payload(envelope)
            frame = (
                f"id: {envelope.event_id}\nevent: {envelope.event_type.value}\ndata: {payload}\n\n"
            )
            yield frame
        if not poll:
            return
        await asyncio.sleep(_POLL_SECONDS)


@router.get("/{run_id}/events", response_model=None)
async def run_events(run_id: str, request: Request) -> StreamingResponse | list[dict[str, object]]:
    """Run Timeline 端点（双模式）：

    - `Accept: application/json`（默认 replay）：一次性返回全量事件
      （初始加载 / 刷新恢复，来自 outbox 持久事件投影）；
    - `Accept: text/event-stream`（SSE）：Last-Event-ID / ?cursor= 续传
      增量事件，客户端按 event_id 去重（重连安全）。
    """
    deps: ApiDeps = get_deps(request)
    if deps.projection is None:
        raise ApiError(503, "Projection Unavailable", "run projection not configured")
    get_run_or_error(deps, run_id)
    events = events_of(deps.projection, run_id)
    cursor = request.headers.get("Last-Event-ID") or request.query_params.get("cursor")
    if request.headers.get("accept", "").startswith("text/event-stream"):
        poll = request.query_params.get("poll", "1") != "0"
        return StreamingResponse(
            event_stream(deps.projection, run_id, cursor, poll),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    selected = [envelope for envelope in events if not cursor or envelope.event_id > cursor]
    return [json.loads(envelope_payload(envelope)) for envelope in selected]
