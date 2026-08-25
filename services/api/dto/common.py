"""Control Plane API 公共 DTO。"""

from __future__ import annotations

from pydantic import BaseModel


class ProblemDto(BaseModel):
    """RFC 7807 风格错误体（统一错误契约）。"""

    type: str
    title: str
    status: int
    detail: str
    instance: str


class IdempotencyHeaderDto(BaseModel):
    """Idempotency-Key 约定说明（OpenAPI 文档用）。"""

    key: str
