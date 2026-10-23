"""**跨记录**的语义矛盾聚合（GOAL-20261023-095 EC-04；阶梯「证据」域的 `下一级`）。

**它补哪一格**：`memory/gate._content_conflict_check` 只在**写入时**判「新提案 vs 现行
记录」—— 那一刻之后没有任何判据看整个记忆库是否自相矛盾。两条**早已并存**的记录说法
相反时，读面照旧逐条报 `USE`（照用）：一份自相矛盾的库与一份一致的库在处置面上
**不可区分**。写入时的判定不能替代存量扫描（存量从未经过那个门）。

**为什么是纯函数、不落在 gate 链上**：判定必须**确定性**（零出网 / 零模型 / 零时钟 /
零随机），且**只读**。写入门链负责「拦住新的」，本模块负责「看清已有的」—— 两者的
射程不同，混在一起会让门链带上全库成本。

**射程（逐条明写，与写入时判定同一套形态）**：复用
`content_conflict.detect_content_conflict` 的三种可机械判形态（否定极性 / 数值方向 /
反义谓词）。需要世界知识的矛盾**不判** —— 本模块不引入第二种语义判定，否则「写入时
判得出的」与「存量里判得出的」会变成两套口径，读者无从知道差异来自哪。

**同 scope 才比**（与门链同一条边界）：跨 scope 是**选择面**而不是同一知识面 ——
一条 `run` 档的临时记录与一条 `organization` 档的结论不是「同一断言的正反」。

**不重复已声明的**：提案方已在 `contradictions` 里写下的对子不再报（声明优先 ——
与门链逐字同一口径）。**`active=False` 不参与**（被取代 / 已删除的知识不构成现行分歧）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from packages.application.memory.content_conflict import detect_content_conflict


@dataclass(frozen=True, slots=True)
class MemoryConflict:
    """一条**跨记录**矛盾（两端的 id + 判词形态 + 共享的断言核）。"""

    #: 两端按 id 排序（**方向无关**：同一对只报一次，且判词可逐字复算）。
    first_id: str
    second_id: str
    #: `detect_content_conflict` 的形态标签（`NEGATION_POLARITY` / `NUMERIC_DIRECTION` /
    #: `ANTONYM_PREDICATE`）—— 读者据此知道「凭什么说它们相反」。
    form: str
    #: 两条共享的断言核（形态级，不做语义推断）。
    shared: str
    #: 两端各自的 scope（同一对必然同 scope —— 这是扫描的边界条件）。
    scope: str


def _active(record: Any) -> bool:
    return getattr(record, "active", True) is not False


def _declared(record: Any) -> set[str]:
    """该记录**声明**的冲突对象（`contradictions`；缺字段 ⇒ 空集，不猜）。"""
    return {str(item) for item in (getattr(record, "contradictions", ()) or ())}


def _pair_declared(left: Any, right: Any) -> bool:
    """两端**任一方**声明了对方 ⇒ 这一对不报（声明优先，与门链同一口径）。"""
    left_id, right_id = str(getattr(left, "id", "")), str(getattr(right, "id", ""))
    return right_id in _declared(left) or left_id in _declared(right)


def conflicts_among(records: tuple[Any, ...]) -> tuple[MemoryConflict, ...]:
    """同一批记录里的**全部**跨记录矛盾（确定性；按 `(scope, first_id, second_id)` 排序）。

    **只比同 `scope`**、**跳过 `active=False`**、**跳过已声明的对子**（三条边界与
    `gate._content_conflict_check` 逐条对应）。同一对只报一次（`i < j` 遍历，
    两端 id 排序后进判词）⇒ 输出与输入顺序无关。
    """
    usable = [record for record in records if _active(record) and str(getattr(record, "id", ""))]
    found: list[MemoryConflict] = []
    for index, left in enumerate(usable):
        for right in usable[index + 1 :]:
            left_scope, right_scope = (
                str(getattr(left, "scope", "")),
                str(getattr(right, "scope", "")),
            )
            if left_scope != right_scope or _pair_declared(left, right):
                continue
            verdict = detect_content_conflict(
                str(getattr(left, "content", "")), str(getattr(right, "content", ""))
            )
            if verdict is None:
                continue
            first, second = sorted((str(getattr(left, "id", "")), str(getattr(right, "id", ""))))
            found.append(
                MemoryConflict(
                    first_id=first,
                    second_id=second,
                    form=verdict.form,
                    shared=verdict.shared,
                    scope=left_scope,
                )
            )
    return tuple(sorted(found, key=lambda item: (item.scope, item.first_id, item.second_id)))


def conflict_summary(conflicts: tuple[MemoryConflict, ...]) -> dict[str, object]:
    """扫描结果的**计数摘要**（形态各几条 + 总量）—— 调用方不解析数组就能看出规模。"""
    by_form: dict[str, int] = {}
    for conflict in conflicts:
        by_form[conflict.form] = by_form.get(conflict.form, 0) + 1
    return {"total": len(conflicts), "by_form": dict(sorted(by_form.items()))}


def conflict_rows(conflicts: tuple[MemoryConflict, ...]) -> list[dict[str, object]]:
    """逐条判词（读面载荷形态；键名与既有一致：`first_id` / `second_id` / `form` / …）。"""
    return [
        {
            "first_id": conflict.first_id,
            "second_id": conflict.second_id,
            "form": conflict.form,
            "shared": conflict.shared,
            "scope": conflict.scope,
        }
        for conflict in conflicts
    ]


def conflict_sweep(memory_store: Any) -> dict[str, object]:
    """全库的**跨记录**矛盾聚合（只读；确定性；与写入时判定同一套形态）。

    读面/调用方的**唯一入口**：它回答「这份库里有没有互相矛盾的现行记录」，
    **不判**「要不要处置」—— 处置仍由调用方的门决定（本模块只读、从不写）。
    """
    found = conflicts_among(tuple(memory_store.query()))
    return {"summary": conflict_summary(found), "pairs": conflict_rows(found)}


__all__ = [
    "MemoryConflict",
    "conflict_rows",
    "conflict_summary",
    "conflict_sweep",
    "conflicts_among",
]
