"""Control Plane API 幂等中间件（Idempotency-Key）。

语义（CONTROL_PLANE_API.md）：mutating 请求必须携带 Idempotency-Key；
同 key + 同请求摘要 → 重放首次响应；同 key + 不同请求摘要 → 422。
中间件在响应完全生成后读取 body 存储，保证重放内容与首次一致。

实现为单进程内存存储（M13 控制面；durable 幂等随 M14 PostgreSQL 演进，
边界在 IdempotencyStore Port 后即替换，不影响路由语义）。
"""

from __future__ import annotations

import json
from typing import cast

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response, StreamingResponse

from services.api.idempotency import StoredResponse, request_digest

_MUTATING_METHODS = frozenset({"POST", "PATCH", "PUT", "DELETE"})
# 分析类 POST 动作（无业务写入，天然幂等，不要求 Idempotency-Key）：
# 校验/编译/preflight/dry-run/test/discover/probe。写类 POST
# （创建资源、启动 run 等）仍强制 Idempotency-Key。
_ANALYSIS_ACTIONS = frozenset({
    "validate",
    "compile",
    "preflight",
    "dry-run",
    "test",
    "discover-models",
    "probe",
})


def _is_analysis_post(path: str) -> bool:
    last_segment = path.rstrip("/").split("/")[-1]
    return last_segment in _ANALYSIS_ACTIONS


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """mutating 请求幂等：replay / conflict / record。"""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _MUTATING_METHODS:
            return await call_next(request)
        if request.method == "POST" and _is_analysis_post(request.url.path):
            return await call_next(request)
        store = request.app.state.deps.idempotency
        body = await request.body()
        key = request.headers.get("Idempotency-Key")
        if not key:
            return _problem(
                422, "Idempotency-Key Required", "mutating requests require Idempotency-Key"
            )
        digest = request_digest(request.method, request.url.path, body)
        stored = store.get(key)
        if stored is not None:
            if stored.request_digest != digest:
                return _problem(
                    422,
                    "Idempotency-Key Reused",
                    "Idempotency-Key was used with a different request payload",
                )
            headers = {"ETag": stored.etag} if stored.etag else {}
            payload = json.loads(stored.body.decode("utf-8"))
            return JSONResponse(status_code=stored.status_code, content=payload, headers=headers)
        response = await call_next(request)
        streaming = cast(StreamingResponse, response)
        raw_chunks = [cast(bytes, chunk) async for chunk in streaming.body_iterator]
        body = b"".join(raw_chunks)
        store.put(
            key,
            StoredResponse(
                request_digest=digest,
                status_code=response.status_code,
                body=body,
                etag=response.headers.get("etag"),
            ),
        )
        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )


def _problem(status_code: int, title: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "type": "about:blank",
            "title": title,
            "status": status_code,
            "detail": detail,
            "instance": "",
        },
    )
