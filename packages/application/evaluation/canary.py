"""M11 Canary：从冻结 dataset 选择高价值小规模子集。

约束：canary 是同一 dataset 内 tags 含 canary 的 case 子集（独立冻结
集合、独立 digest），可快速运行但不可替代完整 regression suite。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.domain.eval_spec import CanaryTag, EvalCase, EvalDataset


@dataclass(frozen=True, slots=True)
class CanarySelection:
    dataset: EvalDataset | None
    excluded_case_ids: tuple[str, ...]

    @property
    def is_proper_subset(self) -> bool:
        """canary 子集不得等于全集（否则失去快速门语义）。"""

        return bool(self.excluded_case_ids)


def select_canary(dataset: EvalDataset) -> CanarySelection:
    """按 CanaryTag 筛选 case；无 canary case → dataset=None（fail-closed）。"""

    canary_cases: list[EvalCase] = []
    excluded: list[str] = []
    for case in dataset.cases:
        if CanaryTag in case.tags:
            canary_cases.append(case)
        else:
            excluded.append(case.id)
    if not canary_cases:
        return CanarySelection(dataset=None, excluded_case_ids=tuple(sorted(excluded)))
    sub = EvalDataset(
        id=f"{dataset.id}-canary",
        version=dataset.version,
        cases=tuple(canary_cases),
        description=f"canary subset of {dataset.id}",
    )
    return CanarySelection(dataset=sub, excluded_case_ids=tuple(sorted(excluded)))
