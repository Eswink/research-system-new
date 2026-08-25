"""Control Plane API 共享依赖：deps 注入与 If-Match 校验。"""

from __future__ import annotations

from typing import cast

from fastapi import Request

from services.api.composition import ApiDeps
from services.api.errors import ApiError


def get_deps(request: Request) -> ApiDeps:
    return cast(ApiDeps, request.app.state.deps)


def require_if_match(request: Request, current_version: str) -> None:
    """If-Match 校验：缺失 → 428；不匹配 → 412（浏览器禁用按钮不是并发保证）。"""
    header = request.headers.get("If-Match")
    if header is None:
        raise ApiError(428, "Precondition Required", "If-Match header is required for mutation")
    if header.strip() != "*" and header.strip() != current_version:
        raise ApiError(
            412,
            "Precondition Failed",
            f"resource version mismatch: expected {current_version}",
        )
