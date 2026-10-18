"""GOAL-20261018-085 EC-04：归因与聚合**在产品路径上生效**，且单评审逐字不变。

**判两组**：

1. **产品路径**（走 `review_read` 的 canonical 读面 —— 与 `review.read` 能力同一个查询口径）：
   - 一条判词在**落库后**仍带 `reviewer_model`（证明归因没有被落库这一步丢掉）；
   - 同一个任务上有两份可归因判词 ⇒ 读面给出 `panels`（逐票 + advisory + 独立性）；
   - **单评审**⇒ `panels == []`（既有读面形态不变，只多了恒为 `[]` 的键）。
2. **按压**：把第二份判词的目标改成与第一份相同 ⇒ `independent` 翻转（证明结论来自
   落库事实，不是读面编造）。

**如实边界**：本文件不声称「模型真的判出了负」—— 那需要真实模型在两个不同目标上各跑一次
（GOAL-084 的 `W-2` 与 GOAL-085 的 `W-3` 都登记了这条射程边界）。本文件判的是**可归因与
可聚合**这两件事在**产品读面**上成立。
"""

from __future__ import annotations

from typing import Any

from adapters.canonical.review_read import review_read
from packages.application.ports.review_finding_store import ScopedReviewFinding
from packages.domain.evidence import ReviewFinding


class _Store:
    """最小 `ReviewFindingStore`（只实现读面用到的 `for_run`）。"""

    def __init__(self, records: tuple[ScopedReviewFinding, ...]) -> None:
        self._records = records

    def for_run(self, run_id: str) -> tuple[ScopedReviewFinding, ...]:
        return tuple(item for item in self._records if item.run_id == run_id)


class _Scope:
    """一份判词的作用域与作者面（参数对象，守住函数签名 <= 5）。"""

    def __init__(
        self,
        *,
        run_id: str = "run-1",
        task_id: str = "task-1",
        contract_id: str = "contract-1",
        reviewer: str = "reviewer_a",
    ) -> None:
        self.run_id = run_id
        self.task_id = task_id
        self.contract_id = contract_id
        self.reviewer = reviewer


def _scoped(
    finding_id: str,
    *,
    scope: _Scope | None = None,
    verdict: str = "PASS",
    model: str | None = "main/glm-5.3",
) -> ScopedReviewFinding:
    where = scope or _Scope()
    return ScopedReviewFinding(
        finding=ReviewFinding(
            id=finding_id,
            review_type="acceptance_gate",
            verdict=verdict,
            findings=[f"{finding_id} wording"],
            reviewed_by=f"gate:{where.reviewer}",
            reviewer_model=model,
        ),
        run_id=where.run_id,
        task_id=where.task_id,
        contract_id=where.contract_id,
    )


def _payload(store: _Store, run_id: str = "run-1") -> dict[str, Any]:
    """读面载荷（带类型的投影；判据不依赖未类型化的 `object`）。"""
    return review_read(store, {"run_id": run_id})


def _reviews(payload: dict[str, Any]) -> list[dict[str, Any]]:
    value = payload["reviews"]
    assert isinstance(value, list), value
    return [item for item in value if isinstance(item, dict)]


def _panels(payload: dict[str, Any]) -> list[dict[str, Any]]:
    value = payload["panels"]
    assert isinstance(value, list), value
    return [item for item in value if isinstance(item, dict)]


def test_each_verdict_names_its_model_on_the_read_face() -> None:
    payload = _payload(_Store((_scoped("f-1"),)))
    assert [item["reviewer_model"] for item in _reviews(payload)] == ["main/glm-5.3"]


def test_a_single_review_produces_no_panel() -> None:
    """**零回归边界**：单评审 ⇒ `panels == []`（不聚合，既有形态不变）。"""
    payload = _payload(_Store((_scoped("f-1"),)))
    assert payload["count"] == 1
    assert _panels(payload) == []
    assert payload["panel_count"] == 0


def test_two_distinct_models_produce_an_independent_panel() -> None:
    store = _Store((
        _scoped("f-1", model="main/glm-5.3"),
        _scoped("f-2", scope=_Scope(reviewer="reviewer_b"), model="main/kimi-k2.6"),
    ))
    panels = _panels(_payload(store))
    assert len(panels) == 1
    panel = panels[0]
    assert panel["voters"] == 2
    assert panel["advisory"] == "PASS"
    assert panel["independent"] is True
    assert panel["targets"] == ["main/glm-5.3", "main/kimi-k2.6"]


def test_pressing_the_second_model_to_the_first_flips_independence() -> None:
    """**按压**：只改第二份判词的目标 ⇒ `independent` 从 `True` 翻成 `False`。"""
    distinct = _Store((
        _scoped("f-1", model="main/glm-5.3"),
        _scoped("f-2", scope=_Scope(reviewer="reviewer_b"), model="main/kimi-k2.6"),
    ))
    same = _Store((
        _scoped("f-1", model="main/glm-5.3"),
        _scoped("f-2", scope=_Scope(reviewer="reviewer_b"), model="main/glm-5.3"),
    ))
    assert _panels(_payload(distinct))[0]["independent"] is True
    assert _panels(_payload(same))[0]["independent"] is False


def test_panels_never_mix_two_tasks() -> None:
    """**分组边界**：不同任务上的判词**不混**成一票（否则「多数票」失去对象）。"""
    store = _Store((
        _scoped("f-1", model="main/glm-5.3"),
        _scoped(
            "f-2",
            scope=_Scope(task_id="task-2", reviewer="reviewer_b"),
            model="main/kimi-k2.6",
        ),
    ))
    payload = _payload(store)
    assert _panels(payload) == []
    assert payload["panel_count"] == 0


def test_an_unattributed_verdict_is_named_on_the_read_face() -> None:
    """**设施面**：没有模型身份的判词在读面 `reviewer_model` 为 `None`，
    且它**不进票数**（被点名而不是被折算）。"""
    store = _Store((
        _scoped("f-1", model="main/glm-5.3"),
        _scoped("f-2", scope=_Scope(reviewer="reviewer_b"), model=None, verdict="REJECT"),
    ))
    panel = _panels(_payload(store))[0]
    assert panel["voters"] == 1
    assert panel["votes"] == {"PASS": 1}
    assert panel["independent"] is False
    assert any("f-2" in note for note in panel["ineligible"])
