"""Control Plane API 幂等层（Idempotency-Key）。

语义（CONTROL_PLANE_API.md）：mutating 请求必须携带 Idempotency-Key；
同 key + 同请求摘要 → 重放首次响应；同 key + 不同请求摘要 → 422。
实现为单进程内存存储（M13 控制面；durable 幂等随 M14 PostgreSQL 演进，
此边界在 IdempotencyStore Port 后即替换，不影响 router 语义）。
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from services.api.errors import ApiError


@dataclass(frozen=True, slots=True)
class StoredResponse:
    request_digest: str
    status_code: int
    body: bytes
    etag: str | None = None


@runtime_checkable
class IdempotencyStore(Protocol):
    """Idempotency-Key → 存储响应。"""

    def get(self, key: str) -> StoredResponse | None: ...

    def put(self, key: str, value: StoredResponse) -> None: ...


class InMemoryIdempotencyStore:
    """内存实现；单进程 uvicorn 下满足控制面语义。"""

    def __init__(self) -> None:
        self._records: dict[str, StoredResponse] = {}

    def get(self, key: str) -> StoredResponse | None:
        return self._records.get(key)

    def put(self, key: str, value: StoredResponse) -> None:
        self._records[key] = value


def request_digest(method: str, path: str, body: bytes) -> str:
    """请求摘要：method + path + canonical body（body 为 UTF-8 字节）。"""
    payload = hashlib.sha256()
    payload.update(method.upper().encode("utf-8"))
    payload.update(b"\0")
    payload.update(path.encode("utf-8"))
    payload.update(b"\0")
    payload.update(body)
    return payload.hexdigest()


def guard_idempotency(
    *,
    key: str | None,
    method: str,
    path: str,
    body: bytes,
    store: IdempotencyStore,
) -> StoredResponse | None:
    """幂等门禁：返回 StoredResponse 表示应重放；None 表示首次执行。

    - 无 key → 422（mutating 必须显式幂等，浏览器按钮禁用不是并发保证）；
    - 同 key 不同摘要 → 422（禁止用同一 key 提交不同 payload）。
    """
    if not key:
        raise ApiError(422, "Idempotency-Key Required", "mutating requests require Idempotency-Key")
    digest = request_digest(method, path, body)
    stored = store.get(key)
    if stored is None:
        return None
    if stored.request_digest != digest:
        raise ApiError(
            422,
            "Idempotency-Key Reused",
            "Idempotency-Key was used with a different request payload",
        )
    return stored
