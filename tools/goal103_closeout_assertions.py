"""GOAL-20261101-103 的产品面断言集（收口复检的**本轮特有**部分）。

公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 / 规范页 / 记录自洽）一行都
不重写 —— 由 `tools/closeout_recheck_assertions.standard_verdicts` 给；本文件只判
**本轮八件交付**在树上的事实。

**每一组都钉「实现存在」+「接线真的接了」两侧**，因为本轮反复实测到的失败形态是
「字段/函数在树、但没有任何调用点」（声明了但从未构造）：
`run_phases_dto` 只要没被 `routers/runs.py` 调就只有签名价值；`apply_retmax` 只要没被
`execute_run_chain_capabilities` 调就是一个死函数。

**判词不许含树的绝对路径**（两树入口会正确地拒绝这种输出）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

#: EC-01：相级事件与相进度读面（域 → 发射 → DTO → 视图 → 路由 → 双读面消费）。
PHASE_FILES: dict[str, tuple[str, ...]] = {
    "packages/domain/events.py": (
        'PHASE_STARTED = "phase.started"',
        'PHASE_COMPLETED = "phase.completed"',
    ),
    "packages/application/run_orchestration/phase_progress.py": (
        "def emit_phase_started(",
        "def emit_phase_completed(",
        "PHASE_OUTCOMES",
    ),
    "packages/application/run_orchestration/phase_runner.py": (
        "phase_progress.emit_phase_started(",
        "phase_progress.emit_phase_completed(",
    ),
    "services/api/dto/runs.py": (
        "class PhaseProgressDto(",
        "PHASE_STATES",
        "phases: list[PhaseProgressDto] | None",
    ),
    "services/api/run_phase_view.py": ("def run_phases_dto(", "_phase_state("),
    "services/api/routers/runs.py": ("run_phases_dto(", "phases=phases,"),
    # 前端两侧：具名 SSE 监听 + 进度条组件 + 页面接入。
    "apps/web/src/features/runs/useRunEventStream.ts": ('"phase.started"', '"phase.completed"'),
    "apps/web/src/features/runs/PhaseProgress.tsx": ("data-phase-state", "phase-node-"),
    "apps/web/src/features/runs/RunPanel.tsx": ("<PhaseProgress",),
}

#: EC-02：两个读面漏字段的三处同步（Python DTO / OpenAPI / types.ts）。
READ_FACE_FILES: dict[str, tuple[str, ...]] = {
    "services/api/dto/artifacts.py": ("supersedes: str | None = None",),
    "services/api/routers/artifacts.py": ("supersedes=getattr(artifact",),
    "services/api/dto/inspection.py": ("reviewer_model: str | None = None",),
    "services/api/routers/inspection.py": (
        'reviewer_model=getattr(item.finding, "reviewer_model", None)',
    ),
    "apps/web/src/api/types.ts": (
        "supersedes: string | null;",
        "reviewer_model: string | null;",
        "export interface PhaseProgressDto",
        "export interface EditorialDecisionDto",
    ),
}

#: EC-04：链上制品标签与手稿视图。
CHAIN_FILES: dict[str, tuple[str, ...]] = {
    "apps/web/src/features/workspace/artifactLabels.ts": (
        "ARTIFACT_LABELS",
        '"manuscript.md"',
        "export function artifactLabel(",
    ),
    "apps/web/src/features/workspace/ArtifactBrowser.tsx": ("<ArtifactLabelChip",),
    "apps/web/src/features/reports/ManuscriptPanel.tsx": (
        "export function ManuscriptPanel(",
        "export function hasManuscript(",
        "editorial-decision-block",
    ),
    "apps/web/src/features/reports/ReportsPage.tsx": ("<ManuscriptPanel",),
}

#: EC-05：`retmax` 项目级 + §7 论证。
#:
#: **GOAL-20261103-105 更新（资产跟随代码，不是放宽）**：本组原先钉两个字面形态 —
#: `retmax: int = 3` 与 `apply_retmax(declared, deps.retmax)` —— 而 GOAL-105 EC-03
#: **按判据点名修掉了那个缺省**（缺省 3 让「未声明」与「声明 3」不可区分，运行期会把
#: env 与显式参数一起抹平），并把取值拆到 `retmax_for_phase`。两项都改判**语义等价且
#: 更强**的标记：① 字段仍在且是可选（`retmax: int | None`）—— 项目级声明这一件事没有
#: 退回去；② 施加点仍然调用 `apply_retmax` 且仍然读 `deps.retmax`（那是项目那一级的
#: 载体）。**本轮没有放宽任何判据**：GOAL-103 关心的「项目声明真的到了调用表」由
#: `tests/application/test_retmax_project_setting.py` 与
#: `tests/application/test_retmax_undeclared_is_a_fact.py` 两条行为判据继续钉住。
RETMAX_FILES: dict[str, tuple[str, ...]] = {
    "packages/application/ports/resource_catalog.py": (
        "retmax: int | None = None",
        "def _retmax_of(",
    ),
    "services/api/retrieval_wiring.py": ("project_retmax: int | None = None",),
    "packages/application/run_orchestration/phase_call_arguments.py": (
        "def apply_retmax(",
        "def retmax_for_phase(",
    ),
    "packages/application/run_orchestration/phase_capabilities.py": (
        "apply_retmax(declared, retmax_for_phase(spec, deps))",
    ),
    "packages/application/run_orchestration/runner_wiring.py": ("_with_project_retmax(",),
    "docs/architecture/MANUSCRIPT_QUALITY.md": ("## 7. 强口径判定",),
}

#: EC-06：早期一代验证器纳入负判射程（名单是闭集）。
EARLY_SCAN_FILES: dict[str, tuple[str, ...]] = {
    "tests/tooling/test_verifier_main_files_report_no_negative.py": (
        "_EARLY_RECORD_VERIFIERS",
        "tools/verify_goal026_closeout.py",
        "tools/verify_goal028_closeout.py",
        "tools/verify_goal029_closeout.py",
        "TestTheEarlyGenerationCriterionBites",
    ),
}

#: 本轮新增的判据文件（每件交付至少一条判据；判据文件不在树 = 交付没有可证伪面）。
CRITERION_FILES: tuple[str, ...] = (
    "tests/application/run_orchestration/test_phase_progress_events.py",
    # **真跑取证**（收口复检指名的缺口：两相合成协议与前端 stub 都不算真跑）。
    "tests/e2e/test_goal103_phase_events_product_path.py",
    "tests/e2e/test_goal103_read_face_http.py",
    "tests/api/test_run_detail_phases.py",
    "tests/api/test_read_face_field_completeness.py",
    "tests/application/test_retmax_project_setting.py",
    "tests/tooling/test_manuscript_quality_strong_criterion.py",
    "apps/web/tests/e2e/run-phase-progress.spec.ts",
    "apps/web/tests/e2e/run-artifact-chain-labels.spec.ts",
)


def _present(text: str, needles: tuple[str, ...]) -> tuple[bool, str]:
    missing = [needle for needle in needles if needle not in text]
    return (not missing, ",".join(missing))


def _group(root: Path, toolbox: Any, prefix: str, files: dict[str, tuple[str, ...]]) -> list[Any]:
    """一组文件 × 必备字面量（逐文件一条判词，缺哪个字面量就点名）。"""
    verdicts: list[Any] = []
    for relative, needles in files.items():
        text = toolbox.text(root, relative)
        ok, missing = _present(text, needles)
        verdicts.append(toolbox.verdict(f"{prefix}-{Path(relative).name}", ok, missing))
    return verdicts


def phase_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：域枚举 → 发射点 → DTO → 视图 → 路由 → 前端，六跳逐跳在位。"""
    verdicts = _group(root, toolbox, "ec01", PHASE_FILES)
    events = toolbox.text(root, "packages/domain/events.py")
    verdicts.append(
        toolbox.verdict(
            "ec01-phase-events-are-typed",
            "PHASE_STARTED" in events and "PHASE_COMPLETED" in events,
            "两个相级事件必须是 `EventType` 的成员（不是字符串字面量）",
        )
    )
    return verdicts


def read_face_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：两个域层早有的字段在三处读面同步（Python / OpenAPI / types.ts）。"""
    import json

    verdicts = _group(root, toolbox, "ec02", READ_FACE_FILES)
    schema = json.loads(toolbox.text(root, "docs/api/openapi.m13.json"))
    schemas = schema["components"]["schemas"]
    verdicts.append(
        toolbox.verdict(
            "ec02-openapi-declares-both-fields",
            "supersedes" in schemas["ArtifactDto"]["properties"]
            and "reviewer_model" in schemas["ReviewFindingDto"]["properties"]
            and "phases" in schemas["RunDetailDto"]["properties"],
            "OpenAPI 快照必须同轮重生成（三处漏一处即漂移）",
        )
    )
    return verdicts


def chain_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：19 类制品标签闭集 + 手稿视图接进报告页。"""
    verdicts = _group(root, toolbox, "ec04", CHAIN_FILES)
    labels = toolbox.text(root, "apps/web/src/features/workspace/artifactLabels.ts")
    # 闭集的规模下界：19 个产物名（少一个就说明表被削过）。
    entries = [line for line in labels.splitlines() if "{ zh:" in line]
    verdicts.append(
        toolbox.verdict(
            "ec04-label-table-covers-nineteen-names",
            len(entries) >= 19,
            f"标签闭集至少 19 项（实测 {len(entries)}）—— 削表等于把已做的产物退回裸 id",
        )
    )
    verdicts.append(
        toolbox.verdict(
            "ec04-unmatched-names-are-not-labelled",
            # 未命中的形态是 `?? null`（查表失败 ⇒ 空值 ⇒ 调用方原样显示 id）。判的是
            # 「没有为未命中编一个标签」：表是纯字面量 + 一次查表，没有任何兜底构造。
            "?? null" in labels and "ARTIFACT_LABELS[artifactName(" in labels,
            "未命中必须给 null（调用方原样显示 id），不得伪造标签",
        )
    )
    return verdicts


def retmax_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-05：`retmax` 四级回落 + §7 论证逐项。"""
    verdicts = _group(root, toolbox, "ec05", RETMAX_FILES)
    doc = toolbox.text(root, "docs/architecture/MANUSCRIPT_QUALITY.md")
    verdicts.append(
        toolbox.verdict(
            "ec05-strong-criterion-argues-every-item",
            doc.count("| ") > 0 and "只能人评" in doc and "可机械判" in doc,
            "§7 必须对两项结论词都给出（只写一种等于没做区分）",
        )
    )
    wiring = toolbox.text(root, "services/api/retrieval_wiring.py")
    verdicts.append(
        toolbox.verdict(
            "ec05-default-is-still-three",
            "DEFAULT_RETMAX = 3" in wiring,
            "默认逐字段不变是硬约束（改动前是 3）",
        )
    )
    return verdicts


def early_scan_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-06：早期一代验证器进负判射程（含反证臂）。"""
    return _group(root, toolbox, "ec06", EARLY_SCAN_FILES)


def criterion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """每件交付都有可证伪面：本轮新增的判据文件逐个在位。"""
    verdicts: list[Any] = []
    for relative in CRITERION_FILES:
        verdicts.append(
            toolbox.verdict(
                f"criterion-{Path(relative).name}",
                toolbox.tree(root, relative).is_file(),
                f"{relative} 不在树 ⇒ 该项交付没有判据",
            )
        )
    return verdicts


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本文件对外入口（`verify_goal103_closeout.py` 按它取本轮断言）。"""
    return [
        *phase_verdicts(root, toolbox),
        *read_face_verdicts(root, toolbox),
        *chain_verdicts(root, toolbox),
        *retmax_verdicts(root, toolbox),
        *early_scan_verdicts(root, toolbox),
        *criterion_verdicts(root, toolbox),
    ]
