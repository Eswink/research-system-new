"""Control Plane API 中间件：幂等（Idempotency-Key）+ **写面认证**。

幂等语义（CONTROL_PLANE_API.md）：mutating 请求必须携带 Idempotency-Key；
同 key + 同请求摘要 → 重放首次响应；同 key + 不同请求摘要 → 422。
中间件在响应完全生成后读取 body 存储，保证重放内容与首次一致。

实现为单进程内存存储（M13 控制面；durable 幂等随 M14 PostgreSQL 演进，
边界在 IdempotencyStore Port 后即替换，不影响路由语义）。

写面认证（GOAL-20260926-019 EC-02）：只对 `_MUTATING_METHODS` 要求
`Authorization: Bearer <token>`；token 从环境变量读取、常数时间比较、
不落盘；留空 ⇒ **认证关闭**（并在启动时打印显式警告）。**读面（GET/HEAD）
一律放行**——保护范围**只有写面**。
"""

from __future__ import annotations

import hmac
import json
import os
from dataclasses import dataclass
from typing import Any, cast

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response, StreamingResponse

from packages.application.principal_context import (
    reset_current_principal,
    set_current_principal,
)
from packages.domain.principal import Principal, PrincipalKind
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


# --- 写面认证（GOAL-20260926-019 EC-02）------------------------------------------
#
# 保护范围 = **只保护写面**：复用上面的 `_MUTATING_METHODS`，**不新造第二套分类**。
# 读面（GET/HEAD）放行；`/health` 是 GET ⇒ 自动豁免（**不设路径白名单**，少一处可漂移的
# 特例）。也**不**把 `_ANALYSIS_ACTIONS` 当成认证面例外——那是**幂等**面的例外。
#
# 诚实边界：单一共享 token ⇒ **单一主体**（服务主体）。本中间件**不**接受调用方自报
# 身份：无逐调用方凭据时那只可被伪造，会形成「看起来有归因、其实可冒充」的假象。
# 逐调用方身份属未来工作（M18 面）。

CONTROL_PLANE_TOKEN_ENV = "RESEARCHOS_CONTROL_PLANE_TOKEN"
CONTROL_PLANE_PRINCIPAL_ID_ENV = "RESEARCHOS_CONTROL_PLANE_PRINCIPAL_ID"
_DEFAULT_PRINCIPAL_ID = "control-plane"
_BEARER_SCHEME = "bearer"


@dataclass(frozen=True, slots=True)
class ControlPlaneAuth:
    """控制面写面认证配置。

    `token` 为 None / 空 ⇒ **认证关闭**（本地开发姿态；启动时打印显式警告）。
    `principal_id` 是认证通过后落 canonical 的主体标识——它**来自配置**，
    不由请求自报（见上面的诚实边界）。
    """

    token: str | None = None
    principal_id: str = _DEFAULT_PRINCIPAL_ID

    @property
    def enabled(self) -> bool:
        return bool(self.token)

    @property
    def principal(self) -> Principal:
        """共享 token 认证出的主体（服务类型：token 无法证明调用者是自然人）。"""
        return Principal(id=self.principal_id, kind=PrincipalKind.SERVICE)


def control_plane_auth_from_env() -> ControlPlaneAuth:
    """从环境变量解析认证配置（**只登记变量名，值不落盘、不进日志**）。

    构造期快照：解析一次，之后不随进程内环境变化（与 worker 网关的凭据姿态一致）。
    """
    token = os.environ.get(CONTROL_PLANE_TOKEN_ENV, "").strip()
    principal_id = (
        os.environ.get(CONTROL_PLANE_PRINCIPAL_ID_ENV, "").strip() or _DEFAULT_PRINCIPAL_ID
    )
    return ControlPlaneAuth(token=token or None, principal_id=principal_id)


def auth_disabled_warning() -> str:
    """认证关闭时的启动警告：**必须**明确说「无认证」。

    不得写成「认证已配置」「受保护」之类会让读者误以为已认证的措辞；也**不得**被读成
    安全结论（`R-M1` 未收口 ⇒ 不得宣称项目安全）。
    """
    return (
        "CONTROL PLANE AUTH IS DISABLED: no control-plane token is configured "
        f"({CONTROL_PLANE_TOKEN_ENV} is unset or empty), so ANY caller that can reach this "
        "process can perform mutating writes (create projects, start runs, change "
        "configuration, decide approvals). This is a local-development posture only: set "
        f"{CONTROL_PLANE_TOKEN_ENV} to require a token on mutating requests. "
        "Boundaries: read endpoints (GET/HEAD) are never authenticated, multi-tenancy and "
        "RBAC are not implemented, and object-level authorization (BOLA/BFLA) is not "
        "covered — this is NOT a statement that the project is secure."
    )


def verify_control_plane_token(provided: str | None, expected: str | None) -> bool:
    """常数时间 token 比较；**空值永不匹配**（不把「未配置」当成「匹配」）。

    与 `services/api/worker_gateway/auth.py::verify_enrollment` **同纪律**（该模块属
    worker 信任域，其包 `__init__` 会拉起整个 worker 应用 ⇒ 这里**不**导入它，只沿用
    同一原语与同一条不变量）。禁用 `==` 直接比较。
    """
    if not provided or not expected:
        return False
    return hmac.compare_digest(provided, expected)


def _bearer_token(authorization: str | None) -> str | None:
    """取 `Authorization: Bearer <t>` 的 token；形态不符 ⇒ None。

    与 worker 网关的 `extract_bearer` **同形态**（此处为该格式在本进程的唯一定义点）。
    """
    if not authorization:
        return None
    scheme, separator, value = authorization.partition(" ")
    if not separator or scheme.lower() != _BEARER_SCHEME:
        return None
    token = value.strip()
    return token or None


class PrincipalAuthMiddleware(BaseHTTPMiddleware):
    """写面认证：只拦 `_MUTATING_METHODS`；通过后把主体放进请求上下文。

    未通过 ⇒ **401 + 点名**（响应体说明缺什么 / 哪里不匹配），**不**进下游、
    **不**触达幂等存储（本中间件注册在 `IdempotencyMiddleware` **之外**）。
    """

    def __init__(self, app: Any, *, config: ControlPlaneAuth | None = None) -> None:
        super().__init__(app)
        self._config = config if config is not None else control_plane_auth_from_env()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self._config.enabled:
            return await call_next(request)
        if request.method not in _MUTATING_METHODS:
            return await call_next(request)
        provided = _bearer_token(request.headers.get("Authorization"))
        if provided is None:
            return _problem(
                401,
                "Authentication Required",
                "mutating requests require an 'Authorization: Bearer <token>' header",
            )
        if not verify_control_plane_token(provided, self._config.token):
            return _problem(
                401,
                "Authentication Required",
                "the provided bearer token does not match the configured control-plane token",
            )
        token = set_current_principal(self._config.principal)
        try:
            return await call_next(request)
        finally:
            reset_current_principal(token)
