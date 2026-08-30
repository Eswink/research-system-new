"""PricingSnapshotStore Port:按 (version, digest) 可寻址的定价快照存储。

BLOCKER-6 定价冻结方案的存储面:RunManifest / ResearchRun 冻结
`pricing_version` + `pricing_digest` 引用,成本投影按引用寻址**当期冻结时
落库的历史价表**,而不是读时传入的当期表——价格后续变更产生新版本
(新 (version, digest) 对),已冻结 run 的历史投影不可被改写。

不变量:
- append-only:`put` 只新增 (version, digest) 条目;同一 (version, digest)
  重复 put 幂等(digest 是内容摘要,同键必同内容),不覆盖不同内容;
- 同一 version 允许多个 digest(改价产生新快照,历史快照保留);
- 寻址未命中返回 None(调用方必须显式降级,绝不回落当期表)。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.application.cost.pricing import PricingTable


@runtime_checkable
class PricingSnapshotStore(Protocol):
    """定价快照存储;(version, digest) 二元组是唯一寻址键。"""

    def put(self, table: PricingTable) -> None: ...

    def get(self, version: str, digest: str) -> PricingTable | None: ...
