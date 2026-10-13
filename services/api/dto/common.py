"""Control Plane API 公共 DTO。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StrictRequestDto(BaseModel):
    """**写面请求体**的共享基类：未知字段 ⇒ **422 + 点名该字段**（GOAL-20261013-071）。

    **为什么需要**：此前**实测**写面打错字段名 ⇒ **200 + 无声丢弃**
    （`{"protocol_path": …, "trace_di": "typo"}` ⇒ 200）—— 调用方**以为设了那个字段**
    （与序 36/37/38 的「静默吞掉」同族，落点从读面转到写面）。pydantic 缺省的
    `extra="ignore"` 正是那个静默形态；本基类把它翻成 `"forbid"`。

    **为什么是基类而不是逐路由校验**：EC-01 实测选定 —— 一次声明按类生效（DRY；
    逐路由要改 37 处调用点、且会漏），错误形态与既有 422 同形
    （`{"detail":[{"type":"extra_forbidden","loc":["body","<字段>"],…}]}` ⇒ 字段名在 `loc` 里）。

    **射程（有意边界）**：**只**给**写面请求体**用；**响应**模型**不**继承它
    （响应由我们生成 ⇒ 禁字段没有调用方受益面；且会把我们自己的输出判红）。
    """

    model_config = ConfigDict(extra="forbid")


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
