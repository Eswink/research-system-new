"""GOAL-20261023-095 EC-04：**跨记录**语义矛盾聚合（阶梯「证据」域的 `下一级`）。

**它补哪一格**：写入时的 `gate._content_conflict_check` 只判「新提案 vs 现行记录」。
两条**早已并存**的记录说法相反时，没有任何判据看得到 —— 读面逐条报 `USE`，一份
自相矛盾的库与一份一致的库在处置面上**不可区分**。

**判据分五组**：

1. **聚合出存量矛盾**（正向）：两条并存且相反 ⇒ 报一对，判词带形态与共享核；
2. **三条边界**（与门链逐条对应）：同 scope 才比 / `active=False` 不参与 / 已声明不重复；
3. **只读 + 确定性**：同一批记录跑两次输出**逐字相同**；函数**不写** store；
4. **缺省载荷逐字不变**：不请求 `sweep_conflicts` 时，`memory.read` 的键集与改动前**相同**
   —— 这一条是「新增面不得改变既有读者看到的东西」；
5. **成本评估**（`W-1` 的取证）：实测全库扫描的耗时随规模如何增长，并把结论写进 GOAL。
"""

from __future__ import annotations

import ast
import time
from dataclasses import dataclass
from pathlib import Path

from adapters.canonical.memory_read import memory_read
from adapters.fakes import FakeMemoryStore
from packages.application.memory.conflict_sweep import (
    conflict_rows,
    conflict_summary,
    conflict_sweep,
    conflicts_among,
)
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal

_ROOT = Path(__file__).resolve().parents[3]
_SWEEP = "packages/application/memory/conflict_sweep.py"
_MOMENT = "2026-10-23T00:00:00+00:00"


@dataclass(frozen=True)
class _Record:
    """最小记录形状（扫描只读 `id` / `content` / `scope` / `active` / `contradictions`）。"""

    id: str
    content: str
    scope: str = "project"
    active: bool = True
    contradictions: tuple[str, ...] = ()


def _ids(conflicts: tuple[object, ...]) -> list[tuple[str, str]]:
    return [(str(getattr(item, "first_id")), str(getattr(item, "second_id"))) for item in conflicts]


def test_two_coexisting_opposed_records_are_aggregated() -> None:
    """正向：两条并存且相反 ⇒ 报一对（判词带形态与共享核；两端 id 排序）。"""
    records = (
        _Record("m-b", "the drug supports the hypothesis"),
        _Record("m-a", "the drug does not support the hypothesis"),
    )
    found = conflicts_among(records)
    assert _ids(found) == [("m-a", "m-b")], found
    assert found[0].form == "NEGATION_POLARITY"
    assert found[0].shared, "共享断言核为空 ⇒ 读者看不出凭什么判它们相反"


def test_conflicting_records_are_ordered_so_the_output_is_stable() -> None:
    """确定性：输入顺序翻转 ⇒ 输出**逐字相同**（两端 id 排序，不依赖遍历序）。"""
    left = (_Record("m-1", "the count increases"), _Record("m-2", "the count decreases"))
    right = tuple(reversed(left))
    assert conflict_rows(conflicts_among(left)) == conflict_rows(conflicts_among(right))


def test_different_scopes_are_not_compared() -> None:
    """边界一（与门链同源）：**跨 scope 不比** —— 选择面不是同一知识面。"""
    records = (
        _Record("m-run", "the metric increases", scope="run"),
        _Record("m-proj", "the metric decreases", scope="project"),
    )
    assert conflicts_among(records) == ()


def test_inactive_and_declared_pairs_are_skipped() -> None:
    """边界二 / 三：`active=False` 不参与；已声明的对子不重复报（声明优先）。"""
    inactive = (
        _Record("m-1", "x supports y"),
        _Record("m-2", "x does not support y", active=False),
    )
    assert conflicts_among(inactive) == ()
    declared = (
        _Record("m-1", "x supports y", contradictions=("m-2",)),
        _Record("m-2", "x does not support y"),
    )
    assert conflicts_among(declared) == (), "已声明的对子又被报一次 ⇒ 与门链口径不一致"


def test_consistent_or_unrelated_records_produce_nothing() -> None:
    """误报防线：一致 / 无关 / 正文相同 ⇒ 空集（正向与误报同等重要）。"""
    assert conflicts_among((_Record("m-1", "same text"), _Record("m-2", "same text"))) == ()
    assert conflicts_among((_Record("m-1", "alpha"), _Record("m-2", "beta gamma"))) == ()
    unrelated = (_Record("m-1", "pipeline 3 minutes"), _Record("m-2", "coverage 40 runs"))
    assert conflicts_among(unrelated) == ()


def test_the_sweep_is_read_only_and_the_summary_counts_by_form() -> None:
    """只读 + 摘要：扫描后 store 的记录数不变；摘要按形态计数且总量一致。"""
    store = FakeMemoryStore(allowed_sources=("test:goal095",))
    for index, text in enumerate(("the count increases", "the count decreases")):
        store.commit(_proposal(f"m-{index}", text))
    before = len(store.query())
    payload = conflict_sweep(store)
    assert len(store.query()) == before, "扫描写了 store ⇒ 它就不是读面"
    summary = payload["summary"]
    assert isinstance(summary, dict)
    assert summary["total"] == 1, summary
    assert summary["by_form"] == {"ANTONYM_PREDICATE": 1}, summary
    assert conflict_summary(conflicts_among(())) == {"total": 0, "by_form": {}}


def test_memory_read_payload_is_unchanged_unless_the_sweep_is_requested() -> None:
    """缺省载荷**逐字不变**：不请求 `sweep_conflicts` ⇒ 没有 `conflicts` 键。"""
    store = FakeMemoryStore(allowed_sources=("test:goal095",))
    store.commit(_proposal("m-1", "the count increases"))
    store.commit(_proposal("m-2", "the count decreases"))
    plain = memory_read(store, {"now": _MOMENT})
    assert "conflicts" not in plain, sorted(plain)
    asked = memory_read(store, {"now": _MOMENT, "sweep_conflicts": "1"})
    assert "conflicts" in asked, sorted(asked)
    # 请求了也不改既有键的取值（新增键只加不改）。
    assert {key: value for key, value in asked.items() if key != "conflicts"} == plain


def test_the_sweep_module_has_no_io_and_no_clock() -> None:
    """确定性构造判据：模块**不 import** 时间 / 随机 / 网络 / 模型（源码级钉住）。"""
    tree = ast.parse((_ROOT / _SWEEP).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    forbidden = {"time", "random", "socket", "http", "requests", "httpx", "litellm", "datetime"}
    assert imported & forbidden == set(), sorted(imported & forbidden)


def test_the_sweep_cost_grows_quadratically_so_it_stays_opt_in() -> None:
    """**成本评估**（`W-1` 取证）：全库扫描是两两比较 ⇒ 耗时随规模平方增长。

    这一条**不是**性能门（不设阈值 —— 机器不同）；它钉住的是**形态**：把规模翻四倍，
    耗时明显超过翻倍。结论写进 GOAL：扫描必须**显式请求**，不摊进每次读。
    """

    def elapsed(count: int) -> float:
        records = tuple(
            _Record(f"m-{index:04d}", f"the count increases in sample {index} items")
            if index % 2 == 0
            else _Record(f"m-{index:04d}", f"the count decreases in sample {index} items")
            for index in range(count)
        )
        start = time.perf_counter()
        conflicts_among(records)
        return time.perf_counter() - start

    small = max(elapsed(60), 1e-6)
    large = elapsed(240)
    assert large > small * 2, (
        f"4x records should cost clearly more than 2x ({small:.6f}s -> {large:.6f}s); "
        "if it does not, the sweep is not quadratic and this note can be revisited"
    )


def _proposal(memory_id: str, content: str) -> MemoryWriteProposal:
    return MemoryWriteProposal(
        id=memory_id,
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content=content,
        provenance="test:goal095",
        confidence=0.9,
        scope="project",
    )
