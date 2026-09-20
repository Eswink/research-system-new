"""漂移三态判定的域判据（GOAL-20260920-008 EC-05 / PLAN-20260920-117 AC-01）。

判据分两半：

1. **三态各自可判**：相同 ⇒ `MATCH`、异名 ⇒ `DRIFT`、未探到 ⇒ `UNKNOWN`；
2. **边界的「决定」被钉住**：`UNKNOWN` 不得退化成 `MATCH`（否则「没探到」会被读成
   「一致」）、大小写差异**算** `DRIFT`（不做折叠——折叠等于替 provider 打包票）、
   空白只做首尾裁剪、空声明值直接拒绝构造。
"""

from __future__ import annotations

import pytest

from packages.domain.enums import ModelDriftState
from packages.domain.model_drift import assess_model_drift


def test_same_name_is_match() -> None:
    verdict = assess_model_drift("agnes-2.5-flash", "agnes-2.5-flash")
    assert verdict.state is ModelDriftState.MATCH
    assert verdict.is_drift is False
    assert verdict.returned_model_name == "agnes-2.5-flash"


def test_surrounding_whitespace_is_not_a_difference() -> None:
    assert assess_model_drift(" model-a ", "model-a").state is ModelDriftState.MATCH
    assert assess_model_drift("model-a", "\tmodel-a\n").state is ModelDriftState.MATCH


@pytest.mark.parametrize(
    "returned",
    [
        None,
        "",
        "   ",
    ],
)
def test_missing_returned_name_is_unknown(returned: str | None) -> None:
    """**未探到 ≠ 一致**：这是本判据的核心反义（AGENTS.md §4）。"""
    verdict = assess_model_drift("model-a", returned)
    assert verdict.state is ModelDriftState.UNKNOWN
    assert verdict.state is not ModelDriftState.MATCH
    assert verdict.is_drift is False
    assert verdict.returned_model_name is None
    assert "unknown is not the same as no drift" in verdict.detail


def test_different_name_is_drift_and_names_both_values() -> None:
    verdict = assess_model_drift("model-a", "model-b")
    assert verdict.state is ModelDriftState.DRIFT
    assert verdict.is_drift is True
    assert "model-a" in verdict.detail
    assert "model-b" in verdict.detail


def test_case_only_difference_counts_as_drift() -> None:
    """决定：只差大小写也记 `DRIFT`。

    折叠大小写会让「provider 把 `model-a` 回报成 `MODEL-A`」静默通过——本仓**无法证明**
    两者是同一个底层模型，所以如实点名两个原值，由人判断。
    """
    verdict = assess_model_drift("model-a", "MODEL-A")
    assert verdict.state is ModelDriftState.DRIFT
    assert "model-a" in verdict.detail
    assert "MODEL-A" in verdict.detail


def test_alias_like_suffix_is_drift() -> None:
    """带日期后缀的快照名同样是 `DRIFT`（不是「同一模型的别名」）——本仓不解释别名。"""
    verdict = assess_model_drift("model-a", "model-a-2026-09-20")
    assert verdict.state is ModelDriftState.DRIFT


def test_blank_declared_name_is_rejected() -> None:
    with pytest.raises(ValueError):
        assess_model_drift("   ", "model-a")
