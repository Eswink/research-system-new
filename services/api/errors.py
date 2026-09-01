"""Control Plane API 错误模型与异常映射。

统一输出 RFC 7807 风格 ProblemDetail；Domain/Port 错误 → 稳定 HTTP 语义：
- KeyError / 资源缺失 → 404
- InvalidInputError / ValueError（域不变量） → 422
- Idempotency-Key 缺失 → 422；同 key 不同 payload → 422
- If-Match 缺失 → 428；不匹配 → 412
- PortError（transient） → 503；其余未分类异常 → 500（detail 脱敏）
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeAlias, cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from packages.application.ports.errors import (
    InvalidInputError,
    PermanentPortError,
    PortError,
    TransientPortError,
)
from packages.domain.redaction import redact_text

ExceptionHandler: TypeAlias = Callable[[Request, Exception], Awaitable[JSONResponse]]


class ApiError(Exception):
    """带稳定 status/title/detail 的 API 层错误。"""

    def __init__(self, status_code: int, title: str, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.title = title
        self.detail = detail


def _problem(status_code: int, title: str, detail: str, instance: str) -> dict[str, str | int]:
    return {
        "type": "about:blank",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": instance,
    }


def _handler(status_code: int, title: str) -> ExceptionHandler:
    """Construct a ProblemDetail handler whose detail is genuinely redacted.

    M16 re-audit F-10: an uncaught adapter error can embed a DSN/secret in its
    message; `redact_text` strips bearer/api-key/URL-credential shapes before
    the text reaches the client, so the docstring guarantee actually holds.
    """

    async def handle(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content=_problem(status_code, title, redact_text(str(exc)), request.url.path),
        )

    return handle


async def _handle_api_error(request: Request, exc: Exception) -> JSONResponse:
    api_error = cast(ApiError, exc)
    return JSONResponse(
        status_code=api_error.status_code,
        content=_problem(
            api_error.status_code, api_error.title, api_error.detail, request.url.path
        ),
    )


def register_error_handlers(app: FastAPI) -> None:
    """注册统一异常处理器（ProblemDetail JSON，绝不含 secret 明文）。"""
    app.add_exception_handler(ApiError, _handle_api_error)
    app.add_exception_handler(KeyError, _handler(404, "Not Found"))
    app.add_exception_handler(InvalidInputError, _handler(422, "Unprocessable Entity"))
    app.add_exception_handler(ValueError, _handler(422, "Unprocessable Entity"))
    app.add_exception_handler(TransientPortError, _handler(503, "Service Unavailable"))
    app.add_exception_handler(PermanentPortError, _handler(400, "Bad Request"))
    app.add_exception_handler(PortError, _handler(400, "Bad Request"))
