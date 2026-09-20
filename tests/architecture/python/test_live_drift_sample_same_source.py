"""live 漂移样本的同源判据（GOAL-009 EC-03 / PLAN-20260920-123）。

**判据判同源，不判文笔。** runbook §6 记了第一次 live 采样的漂移观测：
声明值与 probe 返回的模型标识，以及这两者代入判定函数得到的结论。本判据把那段记录
**重新算一遍**——如果谁把「返回标识」或「判定」改错（哪怕只改一个字符），
重算结果就与文档写的不一致，判据当即变红。

它同时钉住两件容易被悄悄改掉的事：

1. **读面的 drift 必须由同一个域函数产生**（`assess_model_drift`），
   不允许在读面另写一遍 `==` 比较——两条路径各判各的，正是漂移可见性最容易腐坏的地方；
2. **`UNKNOWN` 不是漂移**（AGENTS.md §4：未知 ≠ 无漂移），且三态字面量与域枚举一致。

**本判据不发起任何真实调用**：它读的是 cycle 1 那次 live probe 留下的记录。
"""

from __future__ import annotations

import re
from pathlib import Path

from packages.domain.enums import ModelDriftState
from packages.domain.model_drift import assess_model_drift

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNBOOK = REPO_ROOT / "docs/integration/LIVE_MODEL_RUNBOOK.md"
RECORD_RECHECK = (
    REPO_ROOT / ".cursor/plans/rechecks/RECHECK-20260920-121-first-live-sampling-run.md"
)
MODELS_ROUTER = REPO_ROOT / "services/api/routers/models.py"
MODELS_DTO = REPO_ROOT / "services/api/dto/models.py"

#: 样本行在 runbook §6 的**固定标签**（解析只认标签，不猜格式）。
_LABELS = {
    "run_id": "run id",
    "returned": "返回 model 名",
    "declared": "声明 model 名",
    "state": "漂移判定",
}
_BACKTICK = re.compile(r"`([^`]+)`")


def _runbook_text() -> str:
    return RUNBOOK.read_text(encoding="utf-8")


def _cell(label: str) -> str:
    """按固定标签取表格行的第二个单元格。

    解析失败时**点名缺哪个标签**——不返回空串、不用宽松正则去猜，
    否则「判据没在看」会伪装成「判据通过」。
    """
    prefix = f"| {label} |"
    for line in _runbook_text().splitlines():
        if line.startswith(prefix):
            parts = line.split("|")
            assert len(parts) >= 3, f"the sample row for {label!r} is not a 2-column table row"
            return parts[2]
    raise AssertionError(f"the runbook sample no longer has a row labelled {label!r}")


def _token(label: str) -> str:
    """取该单元格里**第一个**反引号 token（样本值一律以行内代码给出）。"""
    cell = _cell(label)
    match = _BACKTICK.search(cell)
    assert match is not None, f"the sample row {label!r} carries no inline-code token: {cell!r}"
    return match.group(1).strip()


class TestTheLiveSampleIsReproducible:
    """样本必须能**重算**：文档写的判定 == 两个值代入判定函数的结果。"""

    def test_declared_and_returned_are_recorded(self) -> None:
        assert _token(_LABELS["declared"]), "declared model name is missing"
        assert _token(_LABELS["returned"]), "returned model identifier is missing"

    def test_documented_state_matches_a_fresh_assessment(self) -> None:
        declared = _token(_LABELS["declared"])
        returned = _token(_LABELS["returned"])
        documented = _token(_LABELS["state"])
        fresh = assess_model_drift(declared, returned).state.value
        assert documented == fresh, (
            f"the runbook says {documented!r} but re-deriving from "
            f"declared={declared!r} / returned={returned!r} gives {fresh!r}"
        )

    def test_the_sample_is_traceable_to_a_run_id(self) -> None:
        run_id = _token(_LABELS["run_id"])
        assert len(run_id) >= 8, run_id
        recheck = RECORD_RECHECK.read_text(encoding="utf-8")
        assert run_id in recheck, (
            f"the runbook sample cites run {run_id!r}, but the cycle-1 recheck does not"
        )


class TestTheReadFaceUsesTheSameAssessment:
    """读面的 drift 必须来自同一个域函数——不允许并行的 `==` 比较。"""

    def test_models_router_assesses_drift_with_the_domain_function(self) -> None:
        text = MODELS_ROUTER.read_text(encoding="utf-8")
        assert "assess_model_drift(" in text, (
            "the models router no longer derives drift via assess_model_drift"
        )
        assert "from packages.domain.model_drift import assess_model_drift" in text, (
            "the router must import the shared assessment, not re-implement the comparison"
        )

    def test_read_face_state_literal_covers_the_domain_states(self) -> None:
        text = MODELS_DTO.read_text(encoding="utf-8")
        for state in ModelDriftState:
            assert f'"{state.value}"' in text, (
                f"the read-face literal is missing {state.value!r} — the DTO and the domain enum "
                "must not drift apart"
            )

    def test_unknown_is_not_treated_as_drift(self) -> None:
        """AGENTS.md §4：**未知 ≠ 无漂移**，也 **≠** 漂移。"""
        unknown = assess_model_drift("declared-model", None)
        assert unknown.state is ModelDriftState.UNKNOWN
        assert unknown.is_drift is False, "UNKNOWN must not be reported as drift"
        drifted = assess_model_drift("declared-model", "other-model")
        assert drifted.is_drift is True


class TestTheSampleStatesItsForce:
    """单次样本的证明力边界与「未持久化」必须写在样本旁边（只判在场，不判文笔）。"""

    def test_the_single_sample_limit_is_stated(self) -> None:
        text = _runbook_text()
        assert "只代表" in text and "永不漂移" in text, (
            "the runbook must state that one agreement is not a no-drift guarantee"
        )

    def test_the_not_persisted_boundary_is_stated(self) -> None:
        text = _runbook_text()
        assert "不持久化" in text, (
            "the runbook must state that the drift verdict is not persisted, so the read face "
            "only shows it in the process that probed"
        )
