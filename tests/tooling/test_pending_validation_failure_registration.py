"""待拍板决策的同源登记：`on_validation_failure`（GOAL-20260918-006 cycle 2 = EC-02）。

`on_validation_failure` 至今**没有执行期消费者**：验收门跑在任务行 durable `SUCCEEDED`
之后，按声明处置就得改写一条终态行 ⇒ canonical 状态机改动。本仓库对这件事的处置是
"如实登记、等人工拍板"，而不是偷偷实现一半。

本文件把那份登记的**形状**钉成判据（读真实文件，不是断言注释文案）：

1. 决策记录在树：`docs/adr/ADR-0030-validation-failure-consumption.md`，且 `Status: Proposed`
   （草案，不是 Accepted —— 它还没被拍板）；
2. 权威登记在索引：`docs/INDEX.md` 里有它的条目（含 Proposed）；
3. 声明面**同源**：`packages/domain/failure_policy.py`、`docs/architecture/TASK_HANDOFF.md`、
   `examples/contracts/task_contracts.yaml` 三处各自同时出现 `on_validation_failure` 与
   ADR 文件名 ⇒ 读者从任一处都能走到同一份决策；
4. "未消费"仍是**声明**：用户契约里写 `on_validation_failure` 只会被 `unhonored` 点名、
   不改变任何判定（行为判据，不是文案判据）。

反证：把任一处声明面的 ADR 指针删掉 ⇒ 第 3 条红；把 ADR 的 `Status` 改成 `Accepted`
⇒ 第 1 条红（它没被拍板，不许冒充）。
"""

from __future__ import annotations

from pathlib import Path

from packages.domain.failure_policy import OnTaskFailure, failure_policy_view

_ROOT = Path(__file__).resolve().parents[2]
_ADR_NAME = "ADR-0030-validation-failure-consumption.md"
_ADR = _ROOT / "docs" / "adr" / _ADR_NAME
_INDEX = _ROOT / "docs" / "INDEX.md"
# 三处声明面：本模块 docstring、交接契约文档、示例契约注释。
_SURFACES = (
    _ROOT / "packages" / "domain" / "failure_policy.py",
    _ROOT / "docs" / "architecture" / "TASK_HANDOFF.md",
    _ROOT / "examples" / "contracts" / "task_contracts.yaml",
)
_KEY = "on_validation_failure"


def test_the_decision_record_is_a_proposal_not_a_decision() -> None:
    text = _ADR.read_text(encoding="utf-8")
    assert "Status: Proposed" in text, "草案必须是 Proposed：它还没被人工拍板"


def test_the_index_registers_the_pending_decision() -> None:
    text = _INDEX.read_text(encoding="utf-8")
    assert _ADR_NAME in text, "待拍板的决策要有唯一入口（docs/INDEX.md 登记）"
    entry = next(line for line in text.splitlines() if _ADR_NAME in line)
    assert "Proposed" in entry, "索引条目必须写明它是 Proposed，不冒充已接受"


def test_every_declaration_surface_points_at_the_same_record() -> None:
    for surface in _SURFACES:
        text = surface.read_text(encoding="utf-8")
        assert _KEY in text, f"{surface.name} 必须提到这条声明"
        assert _ADR_NAME in text, f"{surface.name} 必须指向同一份决策记录（同源收敛）"


def test_the_key_is_still_declared_but_not_consumed() -> None:
    view = failure_policy_view({"on_validation_failure": "DEAD_LETTER"})
    assert view.unhonored == (_KEY,), "声明的意图被点名，而不是被悄悄忽略"
    assert view.on_task_failure == OnTaskFailure.FAIL_RUN, "行为按缺省：不改变任何判定"
    assert view.tolerated is False
