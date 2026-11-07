"""GOAL-20261107-107 的**产品面断言集**（收口验证器的另一半）。

与 `tools/verify_goal107_closeout.py`（记录面）分工：本文件判**交付物真的在、且不只是
壳子**；主文件判 EC 终态与宪章记账。

**本轮的判法**：四靶各有自己的可证伪事实，因此每个 EC 一条断言，且每条都**指向具体
字节或具体闭集**（不判「模块存在」，判「模块的闭集/守卫在」）：

* 靶子 C：并排 diff 用的是既有路由（不是第二份 diff 算法）；程序页三件各有 testid。
* 靶子 B：分布模块的三个纯函数在、`MIN_CORPUS` 仍是 3、阈值仍全 `None`。
* 靶子 A：三条 rubric 闭集、`PANEL_UNAVAILABLE` 独立一类、模块不接触 `Decision`。
* 靶子 D：`AUTHORED` 出厂关闭、执行边界真的读约束面。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

#: 四靶各自的关键文件（少一件就等于该靶子没交付）。
MANUSCRIPT_PANEL = "packages/application/deliverable/manuscript_panel.py"
CITATION_DISTRIBUTION = "packages/application/deliverable/citation_distribution.py"
SCRIPT_AUTHORITY = "packages/application/experiments/script_authority.py"
GOVERNED = "packages/application/experiments/governed.py"
CORPUS_TOOL = "tools/citation_corpus_report.py"
MANUSCRIPT_PANEL_UI = "apps/web/src/features/reports/ManuscriptPanel.tsx"
PROGRAMS_UI = "apps/web/src/features/projects/ProgramsSection.tsx"
DIFF_PANEL = "apps/web/src/features/workspace/ArtifactDiffPanel.tsx"
QUALITY_DOC = "docs/architecture/MANUSCRIPT_QUALITY.md"

#: 靶子 C 的 e2e 判据（两条，各带反证臂）。
UI_SPECS: tuple[str, ...] = (
    "apps/web/tests/e2e/revision-diff.spec.ts",
    "apps/web/tests/e2e/programs-completion.spec.ts",
)


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _file_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """四靶的关键文件在位（缺一件 = 该靶子没交付）。"""
    verdicts: list[Any] = []
    for relative in (
        MANUSCRIPT_PANEL,
        CITATION_DISTRIBUTION,
        SCRIPT_AUTHORITY,
        GOVERNED,
        CORPUS_TOOL,
        MANUSCRIPT_PANEL_UI,
        PROGRAMS_UI,
        DIFF_PANEL,
    ):
        verdicts.append(
            toolbox.verdict(
                f"delivered-{Path(relative).name}",
                (root / relative).is_file(),
                f"{relative} 不在树",
            )
        )
    for relative in UI_SPECS:
        verdicts.append(
            toolbox.verdict(
                f"delivered-{Path(relative).name}",
                (root / relative).is_file(),
                f"{relative} 不在树（靶子 C 的判据缺席）",
            )
        )
    return verdicts


def _target_c_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """靶子 C：并排 diff 复用既有路由；程序页三件各有 testid。"""
    manuscript = _text(root, MANUSCRIPT_PANEL_UI)
    programs = _text(root, PROGRAMS_UI)
    diff_panel = _text(root, DIFF_PANEL)
    return [
        toolbox.verdict(
            "revision-diff-reuses-the-existing-route",
            "api.artifactDiff(" in manuscript,
            "改稿并排必须走既有 GET /artifacts/{l}/diff/{r}，不另写 diff 算法",
        ),
        toolbox.verdict(
            "revision-diff-reuses-the-existing-renderer",
            "export function DiffBody" in diff_panel and "DiffBody" in manuscript,
            "行渲染必须复用 ArtifactDiffPanel（导出 DiffBody），不复制三态语义",
        ),
        toolbox.verdict(
            "revision-diff-has-its-testid",
            'data-testid="revision-diff"' in manuscript,
            "并排面板缺 testid ⇒ 判据无法定位",
        ),
        toolbox.verdict(
            "programs-page-renders-the-three-pieces",
            all(
                marker in programs
                for marker in (
                    'data-testid="program-create-form"',
                    "DecisionTimeline",
                    "cited_facts",
                )
            ),
            "程序页缺「建程序 / 决定时间线 / cited_facts 展开」之一",
        ),
        toolbox.verdict(
            "programs-page-shows-an-empty-state-not-a-fake-row",
            "program-timeline-empty-" in programs,
            "没有决定时必须明确空态（伪造一行会被这条抓住）",
        ),
    ]


def _target_b_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """靶子 B：三个纯函数在、门在 3、阈值仍全 `None`。"""
    distribution = _text(root, CITATION_DISTRIBUTION)
    thresholds = _text(root, "packages/application/deliverable/citation_sufficiency.py")
    return [
        toolbox.verdict(
            "citation-distribution-has-the-three-functions",
            all(
                f"def {name}(" in distribution
                for name in ("collect_readings", "summarize", "calibration_gate")
            ),
            "分布模块缺三个纯函数之一",
        ),
        toolbox.verdict(
            "citation-distribution-gate-is-three",
            "MIN_CORPUS = 3" in distribution,
            "标定门必须是 §7 写下的 3 份",
        ),
        toolbox.verdict(
            "citation-thresholds-are-still-unset",
            all(
                f"{name}: int | None = None" in thresholds
                for name in (
                    "MIN_MARKS_PER_SENTENCE",
                    "MIN_CITATIONS_PER_REFERENCE",
                    "MIN_SUPPORT_PER_SECTION",
                )
            ),
            "语料不足时不得拍阈值：三个常量必须仍是 None",
        ),
        toolbox.verdict(
            "corpus-tool-reads-run-databases-not-globs",
            ":manuscript.md" in _text(root, CORPUS_TOOL)
            and "artifact-blobs" in _text(root, CORPUS_TOOL),
            "语料入口必须按 artifact id 后缀 + digest 取字节（glob manuscript*.md 实测 0 命中）",
        ),
    ]


def _target_a_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """靶子 A：三条 rubric 闭集、设施失败独立、不接触 `Decision`。"""
    panel = _text(root, MANUSCRIPT_PANEL)
    return [
        toolbox.verdict(
            "panel-has-three-rubrics",
            panel.count('        "citation_supports_sentence",') == 1
            and panel.count('        "argument_holds",') == 1
            and panel.count('        "method_appropriate",') == 1,
            "面板必须是三条 rubric 的闭集",
        ),
        toolbox.verdict(
            "panel-keeps-facility-failure-separate",
            'PANEL_UNAVAILABLE = "PANEL_UNAVAILABLE"' in panel and "is_facility_failure" in panel,
            "设施失败必须独立成一类（不得折算成任何一态）",
        ),
        toolbox.verdict(
            "panel-never-produces-a-decision",
            "from packages.domain.evidence import Decision" not in panel
            and "Decision(" not in panel,
            "面板不得 import/构造 Decision（advisory 边界）",
        ),
        toolbox.verdict(
            "panel-records-who-judged",
            "reviewer_model" in panel and "returned_model_name" in panel,
            "归因必须取**返回**的模型名（同名漂移可见）",
        ),
        toolbox.verdict(
            "quality-doc-names-the-panel",
            "manuscript_panel.py" in _text(root, QUALITY_DOC),
            "§7 必须写明第 1/2/3 项已委派给面板",
        ),
        toolbox.verdict(
            "not-judged-still-has-five-items",
            _text(root, "packages/application/deliverable/manuscript_quality.py").count(
                '    "whether '
            )
            + _text(root, "packages/application/deliverable/manuscript_quality.py").count(
                '    "writing style'
            )
            == 5,
            "`NOT_JUDGED` 必须仍是五项（实现面板不等于确定性模块会判它）",
        ),
    ]


def _target_d_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """靶子 D：`AUTHORED` 出厂关闭；执行边界真的读约束面。"""
    authority = _text(root, SCRIPT_AUTHORITY)
    governed = _text(root, GOVERNED)
    return [
        toolbox.verdict(
            "authored-is-off-by-default",
            "AUTHORED_ALLOWED_BY_DEFAULT = False" in authority,
            "`AUTHORED` 出厂必须关闭（打开是安全姿态决定）",
        ),
        toolbox.verdict(
            "authority-closed-set-is-two-valued",
            'SHIPPED = "SHIPPED"' in authority and 'AUTHORED = "AUTHORED"' in authority,
            "权威面必须是 SHIPPED / AUTHORED 两值闭集",
        ),
        toolbox.verdict(
            "authority-pins-the-shipped-digest",
            "carries no digest" in authority,
            "白名单命中但无摘要 ⇒ 必须拒（没有 pin 就没有被审过的字节）",
        ),
        toolbox.verdict(
            "execution-boundary-reads-the-constraints",
            "evaluation.constraints" in governed and "_enforce_constraints(" in governed,
            "约束面必须在执行边界被读（此前只被返回、零消费方）",
        ),
        toolbox.verdict(
            "authority-enforces-all-three-constraints",
            all(key in authority for key in ("SANDBOX_KEY", "PATH_PREFIX_KEY", "MAX_SECONDS_KEY")),
            "三条约束各要有判定分支",
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 的全部产品面断言（四靶各一组 + 文件在位）。"""
    verdicts: list[Any] = []
    verdicts.extend(_file_verdicts(root, toolbox))
    verdicts.extend(_target_c_verdicts(root, toolbox))
    verdicts.extend(_target_b_verdicts(root, toolbox))
    verdicts.extend(_target_a_verdicts(root, toolbox))
    verdicts.extend(_target_d_verdicts(root, toolbox))
    return verdicts


__all__ = ["assertion_verdicts"]
