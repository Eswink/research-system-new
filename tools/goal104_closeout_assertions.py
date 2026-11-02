"""GOAL-20261103-104 的产品面断言集（收口复检的**本轮特有**部分）。

公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 / 规范页 / 记录自洽）一行都
不重写 —— 由 `tools/closeout_recheck_assertions.standard_verdicts` 给；本文件只判
**本轮七条 EC 的交付**在树上的事实。

**每一组都钉两侧**（本轮反复实测的失败形态）：
- 「实现存在」**与**「接线真的接了」—— 组件在树但没人 import 就成了死代码；
- 「判据存在」**与**「判据咬得住」—— 只写在文档里的要求不会让任何东西变红。

**判词不绑定树的绝对路径**（两树入口会正确地拒绝这种输出）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# ── EC-01：三处悬空样式 + 机械判据 ──────────────────────────────────────────────

#: 三处缺陷的**修复形态**与**缺陷形态**（两侧都判：改对了，且没有留着错的）。
DANGLING_STYLE_FIXES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    # PhaseProgress 的 `.muted` 必须改成**局部**类，且局部模块里真的定义了它。
    "apps/web/src/features/runs/PhaseProgress.tsx": (
        ("phaseStyles.muted",),
        ("styles.muted",),
    ),
    "apps/web/src/features/runs/PhaseProgress.module.css": (
        (".muted {", "var(--fg-muted)"),
        (),
    ),
    "apps/web/src/features/command-center/CommandCenterPage.module.css": (
        ("var(--bg-app)",),
        ("var(--bg)",),
    ),
    "apps/web/src/layout/ConsoleLoading.module.css": (
        ("var(--bg-app)",),
        ("var(--bg)",),
    ),
    "apps/web/src/features/shared/LivePage.module.css": (
        ("var(--fg-faint)",),
        ("var(--text-dim)",),
    ),
}

#: EC-01 的机械判据（token 面 + 类名面 + 反证臂）。
CSS_TOKEN_JUDGE = "apps/web/tests/unit/css-token-references.test.ts"
CSS_TOKEN_MARKERS: tuple[str, ...] = (
    "every var(--token) in a CSS module resolves to a real definition",
    "every styles.<key> resolves to a class in the imported CSS module",
    "the detector actually bites",
    "LOCAL_CASCADE_DIRS",
)

# ── EC-02：设计门禁扩到四组合 + 十一相入基线 ─────────────────────────────────────

DESIGN_SPEC = "apps/web/tests/e2e/design-fidelity.spec.ts"
DESIGN_MARKERS: tuple[str, ...] = (
    # 四组合参数化（对角：每轴各出现两次）。
    "const COMBINATIONS: readonly Prefs[] = [",
    '{ theme: "dark", density: "normal", lang: "zh" }',
    '{ theme: "dark", density: "compact", lang: "en" }',
    '{ theme: "light", density: "normal", lang: "en" }',
    '{ theme: "light", density: "compact", lang: "zh" }',
    # 十一相填充态路由。
    'name: "run-timeline-phases"',
    "#/run/timeline?run=eleven-phases",
    # 元素级像素判据（整页截图看不见折叠线以下的进度条 —— 实测反证）。
    "maxDiffPixels: 0",
    'scale: "css"',
    'getByTestId("phase-track")',
)

#: 结构签名基线：新路由必须含 **≥11 个** `phase-node`（十一相各一）。
OUTLINE_STORE = "apps/web/tests/e2e/design-outlines.json"
OUTLINE_ROUTE = "run-timeline-phases"
OUTLINE_PHASE_IDS: tuple[str, ...] = (
    "question",
    "retrieval",
    "novelty",
    "plan",
    "experiment",
    "review",
    "manuscript",
    "editorial",
    "revision",
    "submission",
    "report",
)
#: 两个平台的基线目录（PNG 由 Playwright 按平台加后缀）。
SNAPSHOT_DIR = "apps/web/tests/e2e/design-fidelity.spec.ts-snapshots"

# ── EC-03：联调补齐（7 条带 UI + 3 条如实登记）──────────────────────────────────

#: 带 UI 的 5 条（reviews / direction / programs 四条中的 4 条）。
WIRED_UI: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "apps/web/src/api/inspectionClient.ts": (
        ("reviews(runId: string): Promise<ReviewFindingDto[]>",),
        (),
    ),
    "apps/web/src/features/runs/ReviewPanelSection.tsx": (
        ("export function ReviewPanelSection(", "reviewer_model", "review-panel"),
        # 前端**不得**调用域聚合函数。射程只判**调用形态**（`aggregate_panel(`）：
        # 注释里解释「为什么不做聚合」时点名它是对的，按子串判会把正确的事判成错。
        ("aggregate_panel(",),
    ),
    "apps/web/src/features/runs/RunPanel.tsx": (
        ("<ReviewPanelSection",),
        (),
    ),
    "apps/web/src/api/projectsClient.ts": (
        ("setDirection(projectId: string",),
        (),
    ),
    "apps/web/src/features/projects/ProjectDirectionEditor.tsx": (
        ("export function ProjectDirectionEditor(", "project-direction-input-"),
        (),
    ),
    "apps/web/src/features/projects/ProjectsPage.tsx": (
        ("<ProjectDirectionEditor", "<ProgramsSection"),
        (),
    ),
    "apps/web/src/api/programsClient.ts": (
        ("export const programsClient", "detail(programId: string)", "advance(programId: string)"),
        (),
    ),
    "apps/web/src/features/projects/ProgramsSection.tsx": (
        ("export function ProgramsSection(", "program-advance-"),
        (),
    ),
}

#: 三条「只加 client + 白名单登记」的方法（**不是**消费者）。
CLIENT_ONLY: tuple[tuple[str, str], ...] = (
    ("apps/web/src/api/libraryClient.ts", "detail(resourceId: string)"),
    ("apps/web/src/api/memoryClient.ts", "validity("),
    ("apps/web/src/api/runClient.ts", "retryTask(taskId: string)"),
)

# ── EC-04：路由覆盖判据 + 登记表 ────────────────────────────────────────────────

ROUTE_JUDGE = "apps/web/tests/unit/backend-route-coverage.test.ts"
REGISTRY_JUDGE = "apps/web/tests/unit/unconsumed-registry.test.ts"
REGISTRY_HELPER = "apps/web/tests/unit/unconsumed-registry.ts"
UNCONSUMED_DOC = "docs/frontend/UNCONSUMED.md"

ROUTE_JUDGE_MARKERS: tuple[str, ...] = (
    "every OpenAPI route has a frontend consumer or a reasoned whitelist entry",
    "readWhitelist",
    "clientShapes",
)

#: 登记表里必须有的三条（本轮新写的 client-only 方法）+ 一条既有无消费者探针。
REGISTERED_ROUTES: tuple[str, ...] = (
    "GET | /health",
    "GET | /library/{resource_id}",
    "GET | /projects/{project_id}/memory/validity",
    "POST | /tasks/{task_id}/retry",
)

# ── EC-05：收口资产 ────────────────────────────────────────────────────────────

VERIFIER = "tools/verify_goal104_closeout.py"
ASSERTIONS = "tools/goal104_closeout_assertions.py"
VERIFIER_REGISTRY = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"

# ── EC-07：两个已修的 workflow 项**不得回退** ───────────────────────────────────

WORKFLOW = ".github/workflows/m0-quality.yml"
#: W-7 / W-5 的检查必须**按 job 定位**：同一文件里 `eval-gate` / `container-quality`
#: 等 job 合法地写着 `runs-on: ubuntu-latest` 与 `timeout-minutes: 20` —— 全文件 grep 会
#: 把它们的合法配置当成「回退」（本轮实测的假红）。射程 = 从 job 名到下一个 job 之间。
WORKFLOW_JOBS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    # W-7：`console-frontend` 必须钉 24.04。26.04 上 Playwright 1.56.1 装不了 chromium
    # ⇒ `Console e2e` 与 `Console live API e2e` 都 skipped ⇒ 像素门禁在 CI 上从未执行。
    "console-frontend": (
        ("runs-on: ubuntu-24.04",),
        ("runs-on: ubuntu-latest",),
    ),
    # W-5：`quality` 的时间预算必须是 30（20 会稳定杀掉 windows leg）。
    "quality": (
        ("timeout-minutes: 30",),
        ("timeout-minutes: 20",),
    ),
}


def _verdict(toolbox: Any, name: str, ok: bool, detail: str = "") -> Any:
    return toolbox.verdict(name, ok, "" if ok else detail)


def _text(root: Path, relative: str) -> str:
    return (root / relative).read_bytes().decode("utf-8")


def _present_and_absent(toolbox: Any, root: Path) -> list[Any]:
    """EC-01 与 EC-03 共用的「在场 + 缺席」判据形态。"""
    verdicts: list[Any] = []
    groups: tuple[tuple[str, dict[str, tuple[tuple[str, ...], tuple[str, ...]]]], ...] = (
        ("style", DANGLING_STYLE_FIXES),
        ("ui", WIRED_UI),
    )
    for label, mapping in groups:
        for relative, (present, absent) in mapping.items():
            path = toolbox.tree(root, relative)
            if not path.is_file():
                verdicts.append(
                    _verdict(toolbox, f"{label}-{Path(relative).name}", False, f"{relative} 不在树")
                )
                continue
            text = _text(root, relative)
            missing = [marker for marker in present if marker not in text]
            lingering = [marker for marker in absent if marker in text]
            verdicts.append(
                _verdict(
                    toolbox,
                    f"{label}-{Path(relative).name}",
                    not missing and not lingering,
                    f"缺 {missing} / 残留 {lingering}",
                )
            )
    return verdicts


def _ec01_verdicts(toolbox: Any, root: Path) -> list[Any]:
    path = toolbox.tree(root, CSS_TOKEN_JUDGE)
    text = _text(root, CSS_TOKEN_JUDGE) if path.is_file() else ""
    missing = [marker for marker in CSS_TOKEN_MARKERS if marker not in text]
    return [
        _verdict(toolbox, "css-token-judge-present", path.is_file(), f"{CSS_TOKEN_JUDGE} 不在树"),
        _verdict(toolbox, "css-token-judge-has-both-faces", not missing, ",".join(missing)),
    ]


def _outline_entry(root: Path, toolbox: Any) -> str:
    """从 `design-outlines.json` 取本路由的签名正文。

    **必须按 JSON 解析**，不能按文本切：文件名 `run-timeline-phases` 是 `run-timeline`
    的子串，文本切分会把整份文件的后半都算进来 ⇒ 「有没有 `phase-progress-unavailable`」
    这类判据会扫到别的路由（本轮实测的假红）。
    """
    import json

    path = toolbox.tree(root, OUTLINE_STORE)
    if not path.is_file():
        return ""
    doc = json.loads(path.read_bytes().decode("utf-8"))
    value = doc.get(OUTLINE_ROUTE, "")
    return value if isinstance(value, str) else ""


def _ec02_verdicts(toolbox: Any, root: Path) -> list[Any]:
    spec = toolbox.tree(root, DESIGN_SPEC)
    text = _text(root, DESIGN_SPEC) if spec.is_file() else ""
    missing = [marker for marker in DESIGN_MARKERS if marker not in text]
    verdicts = [
        _verdict(toolbox, "design-spec-four-combinations", not missing, ",".join(missing)),
    ]
    body = _outline_entry(root, toolbox)
    nodes = [phase for phase in OUTLINE_PHASE_IDS if f"phase-node-{phase}" in body]
    verdicts.append(
        _verdict(
            toolbox,
            "outline-covers-eleven-phases",
            len(nodes) >= 11,
            f"结构签名基线的 {OUTLINE_ROUTE} 只覆盖 {len(nodes)} 个 phase-node",
        )
    )
    verdicts.append(
        _verdict(
            toolbox,
            "outline-phase-route-is-not-the-empty-state",
            "phase-progress-unavailable" not in body,
            "新路由录的是空态 ⇒ 十一相仍是名义覆盖",
        )
    )
    return verdicts


def _snapshot_verdicts(toolbox: Any, root: Path) -> list[Any]:
    """两个平台的 PNG 基线都必须有（**只产 win32** = CI 恒红，本轮的禁止项）。"""
    directory = toolbox.tree(root, SNAPSHOT_DIR)
    if not directory.is_dir():
        return [
            _verdict(toolbox, "design-baselines-two-platforms", False, f"{SNAPSHOT_DIR} 不在树")
        ]
    names = {item.name for item in directory.iterdir() if item.name.endswith(".png")}
    win = {name for name in names if name.endswith("-win32.png")}
    linux = {name for name in names if name.endswith("-linux.png")}
    paired = {name[: -len("-win32.png")] for name in win} == {
        name[: -len("-linux.png")] for name in linux
    }
    return [
        _verdict(
            toolbox,
            "design-baselines-two-platforms",
            bool(win) and len(win) == len(linux) and paired,
            f"win32={len(win)} linux={len(linux)} paired={paired}",
        ),
        _verdict(
            toolbox,
            "design-baselines-include-phase-track",
            any("phase-track-" in name for name in linux),
            "缺 phase-track 的元素级基线（十一相在折叠线以下，整页截图看不见）",
        ),
    ]


def _ec03_verdicts(toolbox: Any, root: Path) -> list[Any]:
    verdicts: list[Any] = []
    for relative, marker in CLIENT_ONLY:
        path = toolbox.tree(root, relative)
        text = _text(root, relative) if path.is_file() else ""
        verdicts.append(
            _verdict(toolbox, f"client-only-{Path(relative).stem}", marker in text, f"缺 {marker}")
        )
    return verdicts


def _ec04_verdicts(toolbox: Any, root: Path) -> list[Any]:
    verdicts: list[Any] = []
    for relative in (ROUTE_JUDGE, REGISTRY_JUDGE, REGISTRY_HELPER, UNCONSUMED_DOC):
        verdicts.append(
            _verdict(
                toolbox,
                f"route-asset-{Path(relative).name}",
                toolbox.tree(root, relative).is_file(),
            )
        )
    judge = toolbox.tree(root, ROUTE_JUDGE)
    text = _text(root, ROUTE_JUDGE) if judge.is_file() else ""
    missing = [marker for marker in ROUTE_JUDGE_MARKERS if marker not in text]
    verdicts.append(_verdict(toolbox, "route-judge-has-both-faces", not missing, ",".join(missing)))
    doc = toolbox.tree(root, UNCONSUMED_DOC)
    doc_text = _text(root, UNCONSUMED_DOC) if doc.is_file() else ""
    for row in REGISTERED_ROUTES:
        verdicts.append(
            _verdict(
                toolbox, f"registered-{row.split('/')[-1]}", row in doc_text, f"缺登记行 {row}"
            )
        )
    return verdicts


def _ec05_verdicts(toolbox: Any, root: Path) -> list[Any]:
    verdicts: list[Any] = []
    for relative in (VERIFIER, ASSERTIONS):
        verdicts.append(
            _verdict(
                toolbox,
                f"closeout-asset-{Path(relative).name}",
                toolbox.tree(root, relative).is_file(),
            )
        )
    registry = toolbox.tree(root, VERIFIER_REGISTRY)
    registry_text = _text(root, VERIFIER_REGISTRY) if registry.is_file() else ""
    verdicts.append(
        _verdict(
            toolbox,
            "verifier-registered-in-verifiers",
            f'"{VERIFIER}"' in registry_text,
            f"{VERIFIER} 未登记进 _VERIFIERS",
        )
    )
    scope = toolbox.tree(root, SCOPE_JUDGE)
    scope_text = _text(root, SCOPE_JUDGE) if scope.is_file() else ""
    verdicts.append(
        _verdict(
            toolbox,
            "verifier-registered-in-in-scope",
            f'"{VERIFIER}"' in scope_text and f'"{ASSERTIONS}"' in scope_text,
            "收口脚本与断言集必须进 IN_SCOPE（否则不过四道门）",
        )
    )
    return verdicts


def _job_block(workflow: str, job: str) -> str:
    """从 job 名那一行切到**下一个同缩进的 job**（`\\n  <name>:\\n`）。

    用缩进定位而不是「找下一个 `runs-on`」：job 体内也有缩进更深的键，只有 `\\n  X:\\n`
    （恰好两个空格）才是新 job 的边界。
    """
    header = f"\n  {job}:\n"
    index = workflow.find(header)
    if index == -1:
        return ""
    tail = workflow[index + len(header) :]
    stop = len(tail)
    for line_start in range(len(tail)):
        if tail.startswith("\n  ", line_start) and line_start + 3 < len(tail):
            rest = tail[line_start + 3 :]
            if rest and not rest.startswith(" ") and ":" in rest.split("\n", 1)[0]:
                stop = line_start
                break
    return tail[:stop]


def _ec07_verdicts(toolbox: Any, root: Path) -> list[Any]:
    """W-7 / W-5 的修复必须仍在（**按 job 定位**，不扫全文件）。"""
    path = toolbox.tree(root, WORKFLOW)
    workflow = _text(root, WORKFLOW) if path.is_file() else ""
    verdicts: list[Any] = []
    for job, (present, absent) in WORKFLOW_JOBS.items():
        block = _job_block(workflow, job)
        if block == "":
            verdicts.append(
                _verdict(toolbox, f"workflow-job-{job}-present", False, f"job {job} 不在 workflow")
            )
            continue
        missing = [marker for marker in present if marker not in block]
        regressed = [marker for marker in absent if marker in block]
        verdicts.append(
            _verdict(
                toolbox,
                f"workflow-{job}-fix-intact",
                not missing and not regressed,
                f"缺 {missing} / 回退形态 {regressed}",
            )
        )
    return verdicts


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 七条 EC 的产品面判据（记录面由 `verify_goal104_closeout.py` 另判）。"""
    verdicts: list[Any] = []
    verdicts.extend(_present_and_absent(toolbox, root))
    verdicts.extend(_ec01_verdicts(toolbox, root))
    verdicts.extend(_ec02_verdicts(toolbox, root))
    verdicts.extend(_snapshot_verdicts(toolbox, root))
    verdicts.extend(_ec03_verdicts(toolbox, root))
    verdicts.extend(_ec04_verdicts(toolbox, root))
    verdicts.extend(_ec05_verdicts(toolbox, root))
    verdicts.extend(_ec07_verdicts(toolbox, root))
    return verdicts
