"""GOAL-20261009-042 EC-02 判据：**`memory.read` 的时效判定与处置**（三态互不混用）。

靶子：读面按**调用方给的时点**（`now`）给每条记忆的 `validity` 与 `disposition`：

- `EXPIRED`（`expires_at <= now`）⇒ `SKIP`（**不**参与后续行为）；
- `REVIEW_DUE`（`review_after <= now`，且未过期）⇒ `ANNOTATE`；
- `None`（未声明时效 **或** 都未到）⇒ `USE`（**不猜** —— §8 口径：未声明不得当成已到期）。

**三条硬约束的判据**（逐条）：

1. **不读挂钟**：同一条记录 + **同一个** `now` ⇒ 判定必相同；且换 `now` 会让判定**翻转**
   （两向都可判：两侧时点分别落 `USE` 与 `SKIP`）；
2. **未声明不猜**：没声明时效的记录在任何时点都是 `USE`（构造性反证）；
3. **点名**：缺 `MemoryStore` / 缺 `now` / `now` 非法（含 naive）⇒ **点名拒绝**
   （**不**返回空列表冒充「没有记忆」）。

**边界**（如实登记）：本文件只判**读面**的判定与处置；「研究循环按处置改变行为」是
EC-03 的事（另有判据）。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from adapters.canonical.memory_read import (
    DISPOSITION_ANNOTATE,
    DISPOSITION_SKIP,
    DISPOSITION_SUPERSEDED,
    DISPOSITION_USE,
    memory_read,
)
from adapters.fakes import FakeMemoryStore
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

_EPOCH = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)


def _moment(offset_days: int) -> str:
    """时点（相对 `_EPOCH` 偏移若干天；**RFC3339**，UTC）。"""
    return (_EPOCH + timedelta(days=offset_days)).isoformat()


def _record(
    memory_id: str,
    *,
    expires_at: datetime | None = None,
    review_after: datetime | None = None,
    scope: str = "project",
    supersedes: list[str] | None = None,
) -> MemoryWriteProposal:
    """一条**待提交**的记忆（经既有 §8 写入门链落到 store ⇒ 与产品路径同一形态）。"""
    return MemoryWriteProposal(
        id=memory_id,
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content=f"内容 {memory_id}",
        provenance="test:goal042",
        confidence=0.9,
        scope=scope,
        supersedes=list(supersedes or ()),
        expires_at=Timestamp(expires_at) if expires_at is not None else None,
        review_after=Timestamp(review_after) if review_after is not None else None,
    )


def _first(payload: dict[str, object]) -> dict[str, object]:
    """读面载荷里的第一条记忆（类型化取值：读面契约里 `memories` 是对象数组）。"""
    rows = payload["memories"]
    assert isinstance(rows, list) and rows, rows
    first = rows[0]
    assert isinstance(first, dict), first
    return first


def _rows_by_id(payload: dict[str, object]) -> dict[str, dict[str, object]]:
    """载荷里 `memory_id → 那一行`（类型化取值：`memories` 是对象数组）。"""
    rows = payload["memories"]
    assert isinstance(rows, list), rows
    out: dict[str, dict[str, object]] = {}
    for item in rows:
        assert isinstance(item, dict), item
        out[str(item["memory_id"])] = item
    return out


def _counts(payload: dict[str, object]) -> dict[str, int]:
    """载荷里的处置计数摘要（类型化取值：`dispositions` 是 `str -> int` 的对象）。"""
    raw = payload["dispositions"]
    assert isinstance(raw, dict), raw
    return {str(k): int(v) for k, v in raw.items()}


def _store(*records: MemoryWriteProposal) -> FakeMemoryStore:
    """把记录**真的提交**进 store（deny-by-default 的来源先登记 —— 与产品路径同一形态）。"""
    store = FakeMemoryStore(allowed_sources=("test:goal042",))
    for record in records:
        store.commit(record)
    return store


class TestTheThreeDispositionsDoNotMix:
    """三态 → 处置：**互不混用**（读面按 `disposition` 即可分派，不靠措辞）。"""

    def test_an_expired_record_is_skipped(self) -> None:
        record = _record("m-expired", expires_at=_EPOCH - timedelta(days=1))
        payload = memory_read(_store(record), {"now": _moment(0)})
        row = _first(payload)
        assert row["validity"] == "EXPIRED", row
        assert row["disposition"] == DISPOSITION_SKIP, row
        assert "已过" in str(row["reason"]), row
        assert str(row["reason"]).startswith("expires_at="), ("理由点名被引的声明值", row)

    def test_a_review_due_record_is_annotated_not_skipped(self) -> None:
        record = _record("m-due", review_after=_EPOCH - timedelta(days=1))
        payload = memory_read(_store(record), {"now": _moment(0)})
        row = _first(payload)
        assert row["validity"] == "REVIEW_DUE", row
        assert row["disposition"] == DISPOSITION_ANNOTATE, row
        assert row["disposition"] != DISPOSITION_SKIP, ("待复核不是过期：处置必须可分", row)
        assert str(row["reason"]).startswith("review_after="), row

    def test_an_expiry_dominates_a_due_review(self) -> None:
        """过期是更强的状态：两条声明都到了 ⇒ `EXPIRED`（不是 `REVIEW_DUE`）。"""
        record = _record(
            "m-both",
            expires_at=_EPOCH - timedelta(days=1),
            review_after=_EPOCH - timedelta(days=2),
        )
        payload = memory_read(_store(record), {"now": _moment(0)})
        assert _first(payload)["validity"] == "EXPIRED", payload["memories"]

    def test_a_record_without_declared_validity_is_used(self) -> None:
        """**未声明不猜**（§8 口径）：没声明时效 ⇒ `USE`，理由明写「不得被当成已到期」。"""
        record = _record("m-plain")
        payload = memory_read(_store(record), {"now": _moment(0)})
        row = _first(payload)
        assert row["validity"] is None, row
        assert row["disposition"] == DISPOSITION_USE, row
        assert "不得被当成已到期" in str(row["reason"]), row

    def test_dispositions_are_counted_for_consumers_that_do_not_parse_the_array(self) -> None:
        store = _store(
            _record("m-a", expires_at=_EPOCH - timedelta(days=1)),
            _record("m-b", review_after=_EPOCH - timedelta(days=1)),
            _record("m-c"),
        )
        payload = memory_read(store, {"now": _moment(0)})
        # GOAL-20261010-050 EC-03：契约的处置枚举**多了一个成员**（`SUPERSEDED`）⇒
        # 本条的期望值**同轮跟上**。**谓词形态一字未改**（仍是 `==` 精确相等 —— 既不放宽也
        # 不改成子集判定）；本条**没有**收窄受判面（原有的三个键仍然逐个被要求）。
        assert payload["dispositions"] == {
            DISPOSITION_USE: 1,
            DISPOSITION_ANNOTATE: 1,
            DISPOSITION_SKIP: 1,
            DISPOSITION_SUPERSEDED: 0,
        }, payload["dispositions"]
        assert payload["memory_count"] == 3


class TestTheDecisionIsReproducible:
    """**不读挂钟**：同一记录 + 同一时点 ⇒ 判定相同；换时点 ⇒ 判定翻转（两向）。"""

    def test_the_same_moment_yields_the_same_decision(self) -> None:
        record = _record("m-1", expires_at=_EPOCH)
        store = _store(record)
        first = memory_read(store, {"now": _moment(0)})
        second = memory_read(store, {"now": _moment(0)})
        assert first["memories"] == second["memories"], "同一时点必须给出同一判定"

    def test_the_decision_flips_across_the_declared_boundary(self) -> None:
        """两向反证：`expires_at` **之前** ⇒ `USE`；**之后** ⇒ `SKIP`（同一份记录）。"""
        record = _record("m-2", expires_at=_EPOCH)
        store = _store(record)
        before = memory_read(store, {"now": _moment(-1)})
        after = memory_read(store, {"now": _moment(0)})
        assert _first(before)["disposition"] == DISPOSITION_USE, before["memories"]
        assert _first(after)["disposition"] == DISPOSITION_SKIP, after["memories"]

    def test_the_moment_is_echoed_so_a_reader_can_recheck(self) -> None:
        payload = memory_read(_store(_record("m-3")), {"now": _moment(0)})
        assert payload["now"] == _moment(0), payload


class TestMissingDependenciesAreNamed:
    """**点名而非静默降级**：缺依赖 / 缺时点 / 时点非法 ⇒ 点名拒绝。"""

    def test_a_missing_store_is_named(self) -> None:
        with pytest.raises(InvalidInputError, match="MemoryStore"):
            memory_read(None, {"now": _moment(0)})

    def test_a_missing_moment_is_named(self) -> None:
        with pytest.raises(InvalidInputError, match="explicit 'now'"):
            memory_read(_store(), {})

    def test_a_blank_moment_is_named(self) -> None:
        with pytest.raises(InvalidInputError, match="explicit 'now'"):
            memory_read(_store(), {"now": "   "})

    def test_a_naive_moment_is_named(self) -> None:
        """naive 时间戳 ⇒ 点名（挂钟语义会随机器时区漂 ⇒ 不接受）。"""
        with pytest.raises(InvalidInputError, match="timezone-aware"):
            memory_read(_store(), {"now": "2026-10-01T12:00:00"})

    def test_an_unparsable_moment_is_named(self) -> None:
        with pytest.raises(InvalidInputError, match="not a valid timestamp"):
            memory_read(_store(), {"now": "not-a-timestamp"})

    def test_an_unknown_tier_is_named(self) -> None:
        with pytest.raises(InvalidInputError, match="not a known tier"):
            memory_read(_store(), {"now": _moment(0), "tier": "GALAXY"})


class TestTheReadFaceIsScopeAware:
    """tier 过滤走既有口径（`MemoryStore.query(tier=...)`），未知 tier **点名**。"""

    def test_a_tier_filter_is_passed_through(self) -> None:
        store = FakeMemoryStore()
        payload = memory_read(store, {"now": _moment(0), "tier": "PROJECT"})
        assert payload["tier"] == "PROJECT", payload
        assert payload["memory_count"] == 0, payload


# --- GOAL-20261010-045 EC-03/EC-04：冲突与生效起点**在读面上**（点名，不凭空） ----------


def _declaring(
    memory_id: str, *, conflicts: list[str], valid_from: str | None = None
) -> MemoryWriteProposal:
    """一条**声明了**冲突（与可选生效起点）的提案。"""
    from datetime import datetime

    from packages.domain.core import Timestamp
    from packages.domain.enums import MemoryTier, MemoryType

    extra: dict[str, object] = {"contradictions": conflicts}
    if valid_from is not None:
        extra["valid_from"] = Timestamp(datetime.fromisoformat(valid_from))
    return MemoryWriteProposal(
        id=memory_id,
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content=f"内容 {memory_id}",
        provenance="test:goal042",
        confidence=0.9,
        **extra,  # type: ignore[arg-type]
    )


def test_a_declared_conflict_is_disclosed_and_named_in_the_reason() -> None:
    """**EC-03 的靶子**：声明了冲突 ⇒ 读面**逐条披露**且理由**点名**它（不自动消解）。"""
    store = _store(_declaring("m-c", conflicts=["memory:earlier-claim"]))
    row = _first(memory_read(store, {"now": _moment(0)}))
    assert row["contradictions"] == ["memory:earlier-claim"], row
    assert "memory:earlier-claim" in str(row["reason"]), ("冲突必须**点名**", row["reason"])
    assert "冲突" in str(row["reason"]), row["reason"]


def test_a_declared_valid_from_is_disclosed_as_a_moment() -> None:
    """**生效起点**逐条披露（ISO 串，可复核）。"""
    store = _store(_declaring("m-v", conflicts=[], valid_from="2026-10-01T00:00:00+00:00"))
    row = _first(memory_read(store, {"now": _moment(0)}))
    assert row["valid_from"] == "2026-10-01T00:00:00+00:00", row


def test_an_undeclared_memory_reports_no_conflict_at_all() -> None:
    """**反证臂（不该红时不红）**：未声明 ⇒ `[]` **且**理由里**不得**出现「冲突」。"""
    store = _store(_record("m-plain"))
    row = _first(memory_read(store, {"now": _moment(0)}))
    assert row["contradictions"] == [], row
    assert row["valid_from"] is None, ("`None` = 不适用/未声明，**不猜**成时点", row)
    assert "冲突" not in str(row["reason"]), row["reason"]


class TestTheDeclaredScopeBecomesSelectable:
    """GOAL-20261010-049 EC-03：**适用范围成为可选的一维**（缺省逐字不变）。

    `scope` 早在域里声明、读面也逐条披露，但**查询面此前只认 `tier`** ⇒「看得见、选不着」。
    本类钉住四件事：① 传了 `scope` ⇒ **真的筛**；② **缺省不筛**（载荷与改动前**逐字相同**）；
    ③ **未知范围点名**（「你要的范围不存在」≠「该范围没有记录」）；④ 与 `tier` **可并存**。
    """

    def test_the_default_payload_carries_no_scope_keys(self) -> None:
        """**缺省逐字不变**：不传 `scope` ⇒ 载荷里**没有** `scope` / `filtered_out` 两键。"""
        payload = memory_read(_store(_record("m-a")), {"now": _moment(0)})
        assert payload["memory_count"] == 1
        assert "scope" not in payload, ("缺省不得凭空多出键", sorted(payload))
        assert "filtered_out" not in payload, sorted(payload)

    def test_the_scope_selects_and_counts_what_it_filtered_out(self) -> None:
        """传 `scope` ⇒ 只留该范围，且**点名筛掉了多少条**（不静默丢）。"""
        kept = _record("m-keep")
        other = _record("m-other", scope="team")
        payload = memory_read(_store(kept, other), {"now": _moment(0), "scope": "project"})
        assert payload["memory_count"] == 1, payload
        assert payload["scope"] == "project"
        assert payload["filtered_out"] == 1, ("必须点名筛掉几条", payload)
        assert _first(payload)["memory_id"] == "m-keep"

    def test_an_unknown_scope_is_named_not_read_as_empty(self) -> None:
        """**未知范围 ⇒ 点名**（不静默返回空集 —— 那是「拼错了」被读成「没有记录」）。"""
        with pytest.raises(InvalidInputError, match="not a known scope"):
            memory_read(_store(_record("m-a")), {"now": _moment(0), "scope": "nope"})

    def test_the_scope_and_tier_dimensions_coexist(self) -> None:
        """两维**可并存**：`tier` 与 `scope` 都传 ⇒ 两者**同时**生效（不是互相顶替）。"""
        a = _record("m-a")
        b = _record("m-b", scope="team")
        payload = memory_read(_store(a, b), {"now": _moment(0), "tier": "PROJECT", "scope": "team"})
        assert payload["memory_count"] == 1, payload
        assert _first(payload)["memory_id"] == "m-b"


class TestASupersededRecordIsNoLongerUsed:
    """GOAL-20261010-050 EC-02/EC-03：**被取代**是第四种可判定的不适用理由。

    **靶子**：`supersedes` 早已声明且有**写者**（`lifecycle.supersede_memory` 会把旧记录
    `deactivate`），但读面**从不披露该链接**、且 `disposition_of` **只看时效** ⇒
    被取代的记录经读面出来仍报 `USE`（「照用」）⇒ 被替代的知识**照样进下一步**。

    本类钉住四件事：① **处置**不再是 `USE`；② 两个**方向**的链接都披露；
    ③ 与「已过期」**可区分**（且两者都有时**都点名**）；④ **无取代关系 ⇒ 逐字不变**。
    """

    def test_a_superseded_record_is_no_longer_used(self) -> None:
        """被取代 ⇒ `SUPERSEDED`（**不是** `USE`），理由**点名取代它的那条 id**。"""
        old = _record("m-old")
        new = _record("m-new", supersedes=["m-old"])
        payload = memory_read(_store(old, new), {"now": _moment(0)})
        rows = _rows_by_id(payload)
        assert rows["m-old"]["disposition"] == DISPOSITION_SUPERSEDED, rows["m-old"]
        assert rows["m-old"]["disposition"] != DISPOSITION_USE, "被取代不得被照用"
        assert "m-new" in str(rows["m-old"]["reason"]), ("必须点名取代它的那条", rows["m-old"])

    def test_both_link_directions_are_disclosed(self) -> None:
        """两个方向都披露：新记录给 `supersedes`，旧记录给 `superseded_by`（**不调换**）。"""
        old = _record("m-old")
        new = _record("m-new", supersedes=["m-old"])
        payload = memory_read(_store(old, new), {"now": _moment(0)})
        rows = _rows_by_id(payload)
        assert rows["m-new"]["supersedes"] == ["m-old"], rows["m-new"]
        assert rows["m-new"]["superseded_by"] == [], ("正向记录不得凭空有反向链接", rows["m-new"])
        assert rows["m-old"]["supersedes"] == [], rows["m-old"]
        assert rows["m-old"]["superseded_by"] == ["m-new"], rows["m-old"]

    def test_no_relation_keeps_the_previous_answer_verbatim(self) -> None:
        """**反证臂**：无取代关系 ⇒ 处置仍是 `USE`、理由**逐字**与改动前相同。"""
        payload = memory_read(_store(_record("m-a")), {"now": _moment(0)})
        row = _first(payload)
        assert row["disposition"] == DISPOSITION_USE, row
        assert row["reason"] == "未声明时效或未到 ⇒ 照用（未声明不得被当成已到期）", row
        assert row["supersedes"] == [] and row["superseded_by"] == [], (
            "无关系 ⇒ 空列表（声明性的值，不是缺字段）",
            row,
        )

    def test_superseded_and_expired_are_distinguishable(self) -> None:
        """**两者可区分**：一条既过期又被取代 ⇒ 理由**同时点名两者**（不共用一句）。"""
        old = _record("m-old", expires_at=_EPOCH - timedelta(days=1))
        new = _record("m-new", supersedes=["m-old"])
        payload = memory_read(_store(old, new), {"now": _moment(0)})
        rows = _rows_by_id(payload)
        reason = str(rows["m-old"]["reason"])
        assert "取代" in reason, ("被取代要点名", reason)
        assert "已过" in reason, ("既然也过期了，也要点名时效面", reason)
        assert rows["m-old"]["disposition"] == DISPOSITION_SUPERSEDED, (
            "优先级固定：已取代先于时效",
            rows["m-old"],
        )

    def test_the_count_summary_separates_the_two_reasons(self) -> None:
        """计数摘要**分开**报（不合并成一格）—— 消费者不解析数组也知道各有几条。"""
        store = _store(
            _record("m-expired", expires_at=_EPOCH - timedelta(days=1)),
            _record("m-old"),
            _record("m-new", supersedes=["m-old"]),
        )
        payload = memory_read(store, {"now": _moment(0)})
        counts = _counts(payload)
        assert counts[DISPOSITION_SUPERSEDED] == 1, counts
        assert counts[DISPOSITION_SKIP] == 1, (
            "「已取代」不得被并进「已过期」那一格",
            counts,
        )
