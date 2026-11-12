"""证据矛盾的**仲裁决策面**（GOAL-20261111-110 EC-01）：谁、依据什么消解。

**闭环缺的哪一环**：检测（`content_conflict` / `conflict_sweep`）与记账
（`resolve_memory_conflict` 落 `ConflictResolution`）都已齐备；缺的是**推断**——
两条矛盾的记忆留谁删谁、依据什么。本模块给**确定性纯函数**的三值闭集：

| 结果 | 可判依据 |
| --- | --- |
| `NEWER_WINS` | 两边的 `valid_from` **都在场**且可比较（新者留；平手判不了） |
| `SOURCE_TRUST_WINS` | 两边的 `TrustLabel` **都在**声明的信任序里且**不等**（高者留） |
| `REQUIRE_HUMAN` | **缺省**；或任何依据缺席 / 平手 / 置信度低于声明阈值 |

**缺省 = `REQUIRE_HUMAN`**（与 AGENTS.md §9 默认 deny 同姿态）：不显式声明策略的调用
得到「必须人来裁决」，**绝不**悄悄挑一边。自动策略只经由**显式声明**的
`DeclaredPolicy`（strategy + min_confidence + 可选信任序覆盖）启用。

**判「序」不改「枚举」**：`TRUST_RANKING` 是**本模块的读序**（对既有 `TrustLabel`
五个成员的排序），`TrustLabel` 枚举本身一字不动——那是 `escalation_triggers`。

**不宣称的事**：本模块**不写库**（消解的落账仍由 `lifecycle.resolve_memory_conflict` 做，
调用方拿 verdict 去调它）；`REQUIRE_HUMAN` 不产出 winner。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Mapping

from packages.application.ports.errors import InvalidInputError

if TYPE_CHECKING:  # pragma: no cover - 仅类型
    from packages.domain.memory import MemoryRecord

#: 三值闭集（结果与「显式声明」共用同一词表；`REQUIRE_HUMAN` 兼作缺省）。
NEWER_WINS = "NEWER_WINS"
SOURCE_TRUST_WINS = "SOURCE_TRUST_WINS"
REQUIRE_HUMAN = "REQUIRE_HUMAN"
OUTCOMES: frozenset[str] = frozenset({NEWER_WINS, SOURCE_TRUST_WINS, REQUIRE_HUMAN})

#: 自动策略（`REQUIRE_HUMAN` 不是策略——它是**没有策略**时的缺省结果）。
AUTO_STRATEGIES: frozenset[str] = frozenset({NEWER_WINS, SOURCE_TRUST_WINS})

#: `TrustLabel` 的**仲裁读序**（值大者可信度高；只排序，不改枚举成员）。
#: **键集必须与 `TrustLabel` 成员集同源**（判据钉住）——新增枚举成员而不给读序 ⇒ 红。
TRUST_RANKING: Mapping[str, int] = {
    "VERIFIED_SOURCE": 5,
    "TRUSTED_INTERNAL": 4,
    "RETRIEVED": 3,
    "USER_PROVIDED": 2,
    "GENERATED": 1,
    "UNTRUSTED_EXTERNAL": 0,
}


@dataclass(frozen=True, slots=True)
class DeclaredPolicy:
    """一次**显式声明**的自动策略（缺省路径完全不经这个类）。

    `min_confidence` 必填：声明自动策略却不开阈值 = 给「谁对谁错」开了无凭据的口子。
    `trust_ranking` 只在 `SOURCE_TRUST_WINS` 下被读；给了就**整体替换**缺省读序
    （不合并），让声明的序就是生效的序。
    """

    strategy: str
    min_confidence: float
    trust_ranking: Mapping[str, int] | None = None

    def __post_init__(self) -> None:
        if self.strategy not in AUTO_STRATEGIES:
            raise InvalidInputError(
                f"declared strategy must be one of {sorted(AUTO_STRATEGIES)}, "
                f"got {self.strategy!r} (REQUIRE_HUMAN is the default, not a strategy)"
            )
        if not 0.0 <= self.min_confidence <= 1.0:
            raise InvalidInputError(
                f"min_confidence must be in [0, 1], got {self.min_confidence!r}"
            )


@dataclass(frozen=True, slots=True)
class ArbitrationVerdict:
    """一次仲裁的**可判依据**：结果 + 胜者（或 `None`）+ 机器可读的依据句。"""

    outcome: str
    winner_id: str | None
    basis: str
    missing: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.outcome not in OUTCOMES:
            raise InvalidInputError(f"arbitration outcome must be one of {sorted(OUTCOMES)}")
        if self.outcome == REQUIRE_HUMAN and self.winner_id is not None:
            raise InvalidInputError("REQUIRE_HUMAN must not name a winner")


def arbitrate(
    left: "MemoryRecord",
    right: "MemoryRecord",
    *,
    policy: DeclaredPolicy | None = None,
    trust_labels: Mapping[str, str] | None = None,
) -> ArbitrationVerdict:
    """两条矛盾记忆 → 仲裁结果（确定性；零出网；**不写库**）。

    `policy=None`（**缺省**）⇒ `REQUIRE_HUMAN`——点名「没有声明策略」。
    `trust_labels` 只在 `SOURCE_TRUST_WINS` 下被读：id → `TrustLabel` 名
    （由调用方从证据面取；本模块**不**从 record 猜）。
    """
    if left.id == right.id:
        raise InvalidInputError(f"arbitration pair must be two distinct records, got {left.id!r}")
    if policy is None:
        return ArbitrationVerdict(
            outcome=REQUIRE_HUMAN,
            winner_id=None,
            basis="no arbitration policy declared; default refuses automated resolution",
            missing=("policy",),
        )
    low = _below_threshold(left, right, policy.min_confidence)
    if low is not None:
        return _human("confidence below declared threshold", (low,))
    if policy.strategy == NEWER_WINS:
        return _by_newer(left, right)
    return _by_trust(left, right, policy.trust_ranking or TRUST_RANKING, trust_labels or {})


def _below_threshold(left: "MemoryRecord", right: "MemoryRecord", threshold: float) -> str | None:
    """任一边置信度低于声明阈值 ⇒ 返回点名理由（否则 `None`）。"""
    for record in (left, right):
        if record.confidence < threshold:
            return f"confidence {record.confidence} of {record.id!r} < {threshold}"
    return None


def _human(basis: str, missing: tuple[str, ...]) -> ArbitrationVerdict:
    return ArbitrationVerdict(outcome=REQUIRE_HUMAN, winner_id=None, basis=basis, missing=missing)


def _by_newer(left: "MemoryRecord", right: "MemoryRecord") -> ArbitrationVerdict:
    """`NEWER_WINS`：`valid_from` 都在场才可比（缺一个、或平手 ⇒ 交给人）。

    比较的是 `Timestamp.value`（datetime）：`Timestamp` 本身不是可序对象，
    直接 `max` 会 TypeError（实测）。
    """
    stamps: dict[str, str] = {}
    values: dict[str, Any] = {}
    for record in (left, right):
        if record.valid_from is None:
            return _human("valid_from undeclared", (f"valid_from: {record.id!r}",))
        stamps[record.id] = str(record.valid_from.value.isoformat())
        values[record.id] = record.valid_from.value
    if values[left.id] == values[right.id]:
        return _human("valid_from tie", (f"tie at {stamps[left.id]}",))
    winner = max((left, right), key=lambda record: values[record.id])
    other = right if winner.id == left.id else left
    return ArbitrationVerdict(
        outcome=NEWER_WINS,
        winner_id=winner.id,
        basis=(
            f"newer valid_from: {winner.id!r}@{stamps[winner.id]} > {other.id!r}@{stamps[other.id]}"
        ),
    )


def _by_trust(
    left: "MemoryRecord",
    right: "MemoryRecord",
    ranking: Mapping[str, int],
    trust_labels: Mapping[str, str],
) -> ArbitrationVerdict:
    """`SOURCE_TRUST_WINS`：两边的标签都在序里且**不等**才可比。"""
    labels: dict[str, str] = {}
    for record in (left, right):
        label = trust_labels.get(record.id)
        if label is None:
            return _human("trust label missing", (f"trust_label: {record.id!r}",))
        if label not in ranking:
            return _human(
                "trust label outside the declared ranking",
                (f"trust_label: {record.id!r}={label!r}",),
            )
        labels[record.id] = label
    if labels[left.id] == labels[right.id]:
        return _human("trust label tie", (f"tie at {labels[left.id]!r}",))
    winner = max((left, right), key=lambda record: ranking[labels[record.id]])
    other = right if winner.id == left.id else left
    return ArbitrationVerdict(
        outcome=SOURCE_TRUST_WINS,
        winner_id=winner.id,
        basis=(
            f"higher trust: {winner.id!r}={labels[winner.id]!r} > {other.id!r}={labels[other.id]!r}"
        ),
    )


__all__ = [
    "AUTO_STRATEGIES",
    "NEWER_WINS",
    "OUTCOMES",
    "REQUIRE_HUMAN",
    "SOURCE_TRUST_WINS",
    "ArbitrationVerdict",
    "DeclaredPolicy",
    "TRUST_RANKING",
    "arbitrate",
]
