"""主体（Principal）领域值对象：**谁在调用**。

MVP 口径（GOAL-20260926-019 / 用户判词「甲」）：

- 主体 = **主体 id + 类型** 两要素。**不含**租户 / organization / 角色 /
  权限矩阵字段——多用户、RBAC 与 tenant isolation 属 **M18（DEFERRED）**，
  本模块**明文不表达授权语义**（与 `packages/domain/projects.py` 同口径）。
- 本模块只回答「主体**是什么**」，不回答「他能做什么」。逐路由 / 逐对象的
  授权判定（BOLA / BFLA）**不在**本模块范围，也不因本模块存在而变成已覆盖。
- 与 `docs/security/IDENTITY_AND_ACCESS.md` 的关系：该文档的「预留实体」
  （`Organization` / `User` / `ServicePrincipal` / `ProjectMembership` /
  `AccessGrant`）仍是未来落点；`Principal` 只取其中**最小**的公共内核。

**诚实边界（不得被读作更强的结论）**：控制面今天用**单一共享 token** ⇒
**单一主体**。本模块**不**支持「调用方自报身份」——在无逐调用方凭据时那只能被伪造，
会形成「看起来有归因、其实可冒充」的假象。「每个调用方各自身份」需要
**逐调用方凭据**，属未来工作，**不在**本轮范围。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PrincipalKind(StrEnum):
    """主体类型（`actor` 字符串的前缀）。

    取值沿用树上既有的 actor 字面量前缀（`user:console` / `system:orchestration`
    / `system:m12`），使主体「是什么」在 canonical 里**无需查表**即可读。
    **不含**角色 / 权限等级——那属 M18。
    """

    USER = "user"
    """人类调用方（控制台 / 运维操作者）。"""

    SERVICE = "service"
    """服务身份（控制面自身以服务主体调用时）。"""

    AGENT = "agent"
    """Agent / 会话主体（`docs/security/IDENTITY_AND_ACCESS.md` §3）。"""

    SYSTEM = "system"
    """系统自身动作（工作流引擎、参考实现内部步骤等非「某次请求」的动作）。"""


@dataclass(frozen=True, slots=True)
class Principal:
    """一次调用的主体：`kind` + `id`，`actor` 为其 canonical 字符串形态。

    不变量：`id` 非空、无首尾空白、**不含 `":"`**——`actor` 是 `"<kind>:<id>"`，
    id 里再出现分隔符会让「类型 / 标识」的切分产生歧义（读面只能看见字符串）。
    """

    id: str
    kind: PrincipalKind

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("principal id must not be empty")
        if self.id != self.id.strip():
            raise ValueError("principal id must not have leading/trailing whitespace")
        if ":" in self.id:
            raise ValueError("principal id must not contain ':' (actor separator)")

    @property
    def actor(self) -> str:
        """canonical actor 字符串（`EventEnvelope.actor` 的取值形态）。"""
        return f"{self.kind.value}:{self.id}"

    @classmethod
    def from_actor(cls, actor: str) -> Principal | None:
        """解析 `"<kind>:<id>"`；形态不合法或类型未知 ⇒ None（**不**猜测、不回退）。

        读面 / 用例用它把 canonical 的 actor 还原成主体；返回 None 表示
        「这不是一个本模块能表达的主体」，而不是「主体缺失」——
        调用方必须自己区分这两种情况。
        """
        kind_text, separator, identifier = actor.partition(":")
        if not separator or not identifier or ":" in identifier:
            return None
        try:
            kind = PrincipalKind(kind_text)
        except ValueError:
            return None
        return cls(id=identifier, kind=kind)


__all__ = ["Principal", "PrincipalKind"]
