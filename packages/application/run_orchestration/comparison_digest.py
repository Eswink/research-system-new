"""run 级可比键（GOAL-20261111-109 EC-01）：**配对消融的配对依据**。

**为什么必须有它**：两臂「同一份装配、只差一个 slot」这件事，需要一个**不把 run 身份
算进比较**的键。既有 `RunManifest.semantic_digest()` 覆盖除 `frozen_at` 外的全部字段，
**含 `run_id` 与 `project_id`** ⇒ 两次 run（哪怕装配逐字节相同）的语义 digest **永不相等**
——用它配对会把「只差一个 slot」错判成「两份完全不同的东西」。

**剔除哪三个、为什么**（与 `eval_result.comparison_digest` 的「比较键不含被评输入」同一
设计姿态）：

| 剔除字段 | 理由 |
| --- | --- |
| `run_id` | run 的身份，不是装配的内容；配对的意义就是「不同 run、可比装配」 |
| `frozen_at` | 冻结时刻的元数据（`semantic_digest` 也剔除它） |
| `project_id` | 项目归属；试点要在同一项目内比，但键本身不应被它绑死 |

其余**全部声明字段**都进 digest：模型、角色、agent、工具、合约、策略、预算、镜像、
skill 版本、pricing、已接受的策略例外——任何一处漂移 ⇒ 键不等 ⇒ 拒绝配对（fail-closed）。

**不宣称的事**：键相等只证明「装配可比」，**不**证明「两次 run 的输出可比」——输出侧
的判读在 `output_readings.py`（EC-03）与 `tools/ablation_report.py`（EC-04）。
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - 仅类型
    from packages.domain.manifest import RunManifest

from packages.domain.serialization import digest_of

#: 被**剔除**的三个字段（键不比较它们；其余声明字段全部参与）。
EXCLUDED_FIELDS: tuple[str, ...] = ("run_id", "frozen_at", "project_id")


@dataclass(frozen=True, slots=True)
class ComparisonKey:
    """一次 run 的**可比身份**：digest + 参与比较的字段数（受判面非空的证据）。"""

    digest: str
    compared_fields: int

    def __str__(self) -> str:  # pragma: no cover - 仅为读面便利
        return self.digest


def comparison_fields() -> tuple[str, ...]:
    """参与比较的字段名（按 dataclass 声明序；剔除 `EXCLUDED_FIELDS`）。

    公开它有两个用途：① 判据可以断言「剔除的恰是那三个、其余全在」；② 新增 manifest
    字段时这里**自动**纳入（与 `semantic_digest` 的「digest 自动覆盖」同一条哲学）。
    """
    from packages.domain.manifest import RunManifest

    return tuple(field.name for field in fields(RunManifest) if field.name not in EXCLUDED_FIELDS)


def comparison_digest(manifest: "RunManifest") -> ComparisonKey:
    """`RunManifest` → run 级可比键（确定性；零出网；不物化凭据）。"""
    payload: dict[str, Any] = {name: getattr(manifest, name) for name in comparison_fields()}
    return ComparisonKey(
        digest=str(digest_of(payload)),
        compared_fields=len(payload),
    )


def comparable(left: "RunManifest", right: "RunManifest") -> bool:
    """两份 manifest 是否**可配对**（键相等；其余任何声明字段漂移都判不可比）。"""
    return comparison_digest(left).digest == comparison_digest(right).digest


__all__ = [
    "EXCLUDED_FIELDS",
    "ComparisonKey",
    "comparable",
    "comparison_digest",
    "comparison_fields",
]
