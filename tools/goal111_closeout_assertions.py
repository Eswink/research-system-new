"""GOAL-20261111-111 的**产品面断言集**（收口验证器的另一半）。

与 `tools/verify_goal111_closeout.py`（记录面）分工：本文件判**交付物真的在、且形态就是
声明的那一个**；主文件判 EC 终态与宪章记账。

**本轮的判法**（每条指向具体行为，不判「文件存在」）：

* 引用面（EC-01）：句子编号确定性、`S<n>` 越界判负、真实子串判正、空 rationale 独立一类；
* 降级（EC-02）：`REFUTED` + 无效引用 ⇒ `AMBIGUOUS` + 标记；`SUPPORTED` / 设施失败**原样**；
* 四条判据（EC-03）：① 正例 ② 越界反证 ③ 空反证 ④ advisory（源码面不触 `Decision`）；
* `NOT_JUDGED`（EC-04）：**五项原文逐字比对** + `len == 5`；
* 阶梯（EC-04）：报告行带新 bar、其余六行不被推广。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

DELIVERABLES: tuple[str, ...] = (
    "packages/application/deliverable/panel_grounding.py",
    "packages/application/deliverable/manuscript_panel.py",
    "packages/application/deliverable/manuscript_quality.py",
    "docs/architecture/MANUSCRIPT_QUALITY.md",
)

JUDGES: tuple[str, ...] = (
    "tests/application/deliverable/test_panel_grounding.py",
    "tests/application/test_manuscript_quality.py",
    "tests/application/test_manuscript_panel.py",
    "tests/tooling/test_goal111_ladder_report_scope.py",
)

VERIFIER = "tools/verify_goal111_closeout.py"
ASSERTIONS = "tools/goal111_closeout_assertions.py"

#: `NOT_JUDGED` 的**五项原文**（逐字比对；改一个字即红）。
NOT_JUDGED_EXPECTED: tuple[str, ...] = (
    "whether a citation supports the sentence it is attached to (only: not unrelated)",
    "whether the argument holds (premises sufficient / inference valid / conclusion supported)",
    "whether the method is appropriate for the question",
    "whether the citation set is sufficient for each claim",
    "writing style, readability, grammar",
)

#: 阶梯锚。
REPORT_BAR = "面板判词本身可被反驳"
OTHER_LADDER_PREFIXES: tuple[str, ...] = (
    "| 检索 |",
    "| 计划 |",
    "| 复检 |",
    "| 证据 |",
    "| 实验 |",
    "| 迭代 |",
)

_MANUSCRIPT = (
    "The proposed method combines retrieval with a reranking stage. "
    "Results show a twenty percent gain over the baseline. "
    "We conclude that the hypothesis holds for the tested cohort."
)


def _module(root: Path, relative: str, name: str) -> ModuleType | None:
    path = root / relative
    if not path.is_file():
        return None
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _file_verdicts(root: Path, toolbox: Any) -> list[Any]:
    return [
        toolbox.verdict(
            f"delivered-{Path(relative).name}",
            (root / relative).is_file(),
            f"{relative} 不在树",
        )
        for relative in (*DELIVERABLES, *JUDGES, VERIFIER, ASSERTIONS)
    ]


def _grounding_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01/02：在断言集里**重放**四条（不只查判据文件在树）。"""
    module = _module(root, "packages/application/deliverable/panel_grounding.py", "g111_grounding")
    if module is None:
        return [toolbox.verdict("grounding-importable", False, "panel_grounding 不可加载")]
    panel = _module(root, "packages/application/deliverable/manuscript_panel.py", "g111_panel")
    sentences = module.number_sentences(_MANUSCRIPT)
    positive = module.grounded_in("S2 overstates the gain.", _MANUSCRIPT)
    out_of_range = module.grounded_in("S99 contradicts the abstract.", _MANUSCRIPT)
    empty = module.grounded_in("", _MANUSCRIPT)
    verdicts = [
        toolbox.verdict(
            "sentences-are-numbered-deterministically",
            [item.marker for item in sentences] == ["S1", "S2", "S3"],
            f"切句应为 S1..S3，实得 {[item.marker for item in sentences]}",
        ),
        toolbox.verdict(
            "a_named_sentence_in_range_is_grounded",
            positive.outcome == "GROUNDED" and positive.sentences == (2,),
            f"正例应为 GROUNDED(2)，实得 {positive.outcome}/{positive.sentences}",
        ),
        toolbox.verdict(
            "an_out_of_range_sentence_is_not_grounded",
            out_of_range.outcome == "NOT_GROUNDED"
            and any("S99" in item for item in out_of_range.missing),
            f"越界应为 NOT_GROUNDED 并点名，实得 {out_of_range.outcome}",
        ),
        toolbox.verdict(
            "an_empty_rationale_is_its_own_outcome",
            empty.outcome == "EMPTY_RATIONALE" and empty.outcome != out_of_range.outcome,
            f"空 rationale 应为独立一类，实得 {empty.outcome}",
        ),
    ]
    if panel is not None:
        verdicts.extend(_degradation_verdicts(panel, toolbox))
    return verdicts


def _degradation_verdicts(panel: ModuleType, toolbox: Any) -> list[Any]:
    """EC-02：降级的三条（无效 ⇒ 降级；有效 ⇒ 保持；`SUPPORTED` ⇒ 不受约束）。"""

    def refuted(rationale: str) -> Any:
        return panel.PanelVerdict(
            rubric_id="argument_holds",
            verdict="REFUTED",
            rationale=rationale,
            reviewer_model="main/hy4free",
        )

    degraded = panel.ground_verdict(refuted("S99 contradicts the abstract."), _MANUSCRIPT)
    kept = panel.ground_verdict(refuted("S3 generalises beyond the cohort."), _MANUSCRIPT)
    supported = panel.PanelVerdict(
        rubric_id="method_appropriate",
        verdict="SUPPORTED",
        rationale="",
        reviewer_model="main/hy4free",
    )
    return [
        toolbox.verdict(
            "an_ungrounded_refutation_is_degraded",
            degraded.verdict == "AMBIGUOUS"
            and degraded.rationale.startswith(panel.UNGROUNDED_MARK),
            f"无效引用应降级 AMBIGUOUS+标记，实得 {degraded.verdict}",
        ),
        toolbox.verdict(
            "a_grounded_refutation_survives",
            kept.verdict == "REFUTED",
            f"有效引用应保持 REFUTED，实得 {kept.verdict}",
        ),
        toolbox.verdict(
            "supported_is_not_constrained",
            panel.ground_verdict(supported, _MANUSCRIPT) is supported,
            "SUPPORTED 不指句子 ⇒ 不得被引用核验降级",
        ),
    ]


def _not_judged_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：五项**逐字**未动 + `len == 5`。"""
    module = _module(root, "packages/application/deliverable/manuscript_quality.py", "g111_quality")
    if module is None:
        return [toolbox.verdict("quality-importable", False, "manuscript_quality 不可加载")]
    actual = tuple(module.NOT_JUDGED)
    return [
        toolbox.verdict(
            "not-judged-is-five-items",
            len(actual) == 5,
            f"NOT_JUDGED 必须仍是五项，实得 {len(actual)}",
        ),
        toolbox.verdict(
            "not-judged-items-are-byte-identical",
            actual == NOT_JUDGED_EXPECTED,
            "NOT_JUDGED 五项必须逐字未动",
        ),
    ]


def _advisory_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03 判据 ④：面板与引用面都不触 `Decision`。"""
    grounding = (root / "packages/application/deliverable/panel_grounding.py").read_text(
        encoding="utf-8"
    )
    panel = (root / "packages/application/deliverable/manuscript_panel.py").read_text(
        encoding="utf-8"
    )
    return [
        toolbox.verdict(
            "grounding-never-touches-decisions",
            "Decision" not in grounding and "acceptance_gate" not in grounding,
            "引用核验面不得触及 Decision / 验收门",
        ),
        toolbox.verdict(
            "panel-constructs-no-decision",
            "Decision(" not in panel,
            "面板仍只构造 ReviewFinding，不构造 Decision",
        ),
    ]


def _ladder_verdicts(root: Path, toolbox: Any) -> list[Any]:
    charter = toolbox.text(root, ".cursor/plans/goals/MAINLINE.md")
    report = next((line for line in charter.splitlines() if line.startswith("| 报告 |")), "")
    verdicts = [
        toolbox.verdict(
            "ladder-report-row-carries-the-new-bar",
            REPORT_BAR in report,
            "「报告」行的 下一级 必须含面板判词可反驳的 bar",
        ),
        toolbox.verdict(
            "ladder-report-row-keeps-its-own-scope",
            "这段写得好不好" in report,
            "旧射程声明必须仍在（本轮不宣称它消失了）",
        ),
    ]
    for prefix in OTHER_LADDER_PREFIXES:
        row = next((line for line in charter.splitlines() if line.startswith(prefix)), "")
        verdicts.append(
            toolbox.verdict(
                f"ladder-{prefix.strip('| ').strip()}-stays-unpromoted",
                REPORT_BAR not in row,
                f"{prefix.strip('| ')} 行不得被越级推广",
            )
        )
    return verdicts


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 的产品面全量断言（验证器按路径加载并调用它）。"""
    return [
        *_file_verdicts(root, toolbox),
        *_grounding_verdicts(root, toolbox),
        *_not_judged_verdicts(root, toolbox),
        *_advisory_verdicts(root, toolbox),
        *_ladder_verdicts(root, toolbox),
    ]
