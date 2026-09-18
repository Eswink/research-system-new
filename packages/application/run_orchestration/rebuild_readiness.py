"""重建能力读面：这份 run 记录够不够重建，缺哪条事实（GOAL-005 cycle 6 = EC-06）。

历史行缺口的两条形态（旧 run 无冻结正文、旧 `manifest.frozen` 事件无
`semantic_digest`）此前只有一个 `None` 可读，读面分不清"功能前历史行"与"还没冻结"，
"缺的是哪条事实"也只留在**拒绝文案**里（要真调一次 `/resume` 才看得到，且文案分散在
`run_resume` 与 `convergence`）。

本模块把这件事做成一等事实：纯函数读 run 行上的四个事实
（`manifest_digest` / `manifest_semantic_digest` / `protocol_body` / `protocol_source`），
回答"重建能力"与**确定性排序**的 `missing`。读面（`RunDetailDto.rebuild`）与 `/resume`
的拒绝文案都从这里取——"缺什么"只有这一处枚举，读面与控制面不会各说各话。

三条边界（写进读面注释与 `CONTROL_PLANE_API.md`）：

- `status` 只描述**记录够不够重建**，不描述"该不该重建"（状态机、策略、预算不在本读面）；
- `missing` 是**行上的字段名**，与 canonical `ResearchRun` 的字段一一对应；
- 分类器不判"重建一定成功"：漂移校验、preflight 仍在 `/resume` 真跑时判
  （本读面回答"输入齐不齐"，不是"重建必过"）。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.domain.run import ResearchRun

__all__ = [
    "REBUILD_REFUSED",
    "REBUILD_SELF_CONTAINED",
    "REBUILD_SOURCE_DEPENDENT",
    "RebuildReadiness",
    "rebuild_readiness",
]

#: 冻结正文 + 两个 digest：重建只用行上的字节，不碰外部来源。
REBUILD_SELF_CONTAINED = "SELF_CONTAINED"
#: 两个 digest 齐、无冻结正文：重建依赖来源仍可解析（路径/草稿修订还在）。
REBUILD_SOURCE_DEPENDENT = "SOURCE_DEPENDENT"
#: 缺阻塞事实（`missing` 点名）：重建会被拒绝，出路是 fork run 或 revision。
REBUILD_REFUSED = "REFUSED"

#: `missing` 的确定性顺序（与 run 行字段声明顺序一致；与写入顺序无关）。
_MISSING_ORDER = ("manifest_digest", "manifest_semantic_digest", "protocol_body", "protocol_source")

#: `/resume` 的既有早退文案（逐字不变；条件与 `rebuild_and_resume` 的两条早退对齐）。
_NO_SOURCE_OR_BODY = "run has no recorded protocol source (predates source recording)"
_NO_FROZEN_DIGEST = "run has no frozen manifest digest; cannot verify rebuild"
#: 正文缺席时异常拒绝的前缀（"缺的第二条事实"由异常自己点名，如来源不可解析）。
_SOURCE_DEPENDENT_PREFIX = "run has no frozen protocol body; "


@dataclass(frozen=True, slots=True)
class RebuildReadiness:
    """重建能力读面值对象：status + 按字段名点名的缺失事实 + "正文是否已冻结"。

    `body_frozen` 单独带出来是因为 `/resume` 的**异常前缀**问的正是这一件事
    （没有冻结正文时要如实说明"重建依赖外部来源"）：同一个事实只判定一次。
    """

    status: str
    missing: tuple[str, ...] = ()
    body_frozen: bool = False

    def __post_init__(self) -> None:
        if self.status == REBUILD_REFUSED and not self.missing:
            raise ValueError("REFUSED requires at least one missing fact")
        if self.status != REBUILD_REFUSED and self.missing:
            raise ValueError("missing facts imply REFUSED")
        if self.body_frozen and "protocol_body" in self.missing:
            raise ValueError("a frozen body cannot be listed as missing")

    def early_refusal(self) -> str | None:
        """`/resume` 的两条**早退**拒绝文案（条件与顺序与既有实现逐字一致）。

        只覆盖"连重建都不必尝试"的两种记录形态：装配输入全缺（旧 run）、没有冻结
        digest。语义 digest 缺席不在这里——那一条由 `convergence` 守卫在重建后拒。
        """
        if "protocol_source" in self.missing:
            return _NO_SOURCE_OR_BODY
        if "manifest_digest" in self.missing:
            return _NO_FROZEN_DIGEST
        return None

    def dependency_prefix(self) -> str:
        """异常拒绝时的诚实前缀：没有冻结正文 ⇒ 点名"重建依赖外部来源"这条事实。

        `body_frozen` 就是分类器对"行上有没有冻结正文"的判定（与 `missing` 同源），
        不再各写一遍 `body is None`。
        """
        return "" if self.body_frozen else _SOURCE_DEPENDENT_PREFIX


def rebuild_readiness(run: ResearchRun) -> RebuildReadiness:
    """这份 run 记录的重建能力（纯函数；判据与 `rebuild_and_resume` 的拒绝条件对齐）。

    逐条对应（条件不变、文案不变，只是**同源**）：

    - `manifest_digest is None` ⇒ `/resume` 直接拒（"cannot verify rebuild"）；
    - `manifest_semantic_digest is None` ⇒ `convergence.assert_semantics_frozen` 拒
      （旧 `manifest.frozen` 事件没有这项 ⇒ 这是**历史事件形态**的判据）；
    - `protocol_body` 与 `protocol_source` 都缺 ⇒ 没有任何装配输入可重建（旧 run 形态）。

    最后一条是**合取**：只有正文（正文自足）或只有来源（来源可解析）都仍可重建——
    与今天的拒绝条件逐字一致，不新增也不放宽任何判定。
    """
    missing: list[str] = []
    if run.manifest_digest is None:
        missing.append("manifest_digest")
    if run.manifest_semantic_digest is None:
        missing.append("manifest_semantic_digest")
    if run.protocol_body is None and run.protocol_source is None:
        missing.append("protocol_body")
        missing.append("protocol_source")
    ordered = tuple(fact for fact in _MISSING_ORDER if fact in missing)
    frozen = run.protocol_body is not None
    if ordered:
        return RebuildReadiness(status=REBUILD_REFUSED, missing=ordered, body_frozen=frozen)
    if frozen:
        return RebuildReadiness(status=REBUILD_SELF_CONTAINED, body_frozen=True)
    return RebuildReadiness(status=REBUILD_SOURCE_DEPENDENT)
