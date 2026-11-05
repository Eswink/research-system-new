"""GOAL-20261104-106 的产品面断言集（收口复检的**本轮特有**部分）。

公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 / 规范页 / 记录自洽）一行都
不重写 —— 由 `tools/closeout_recheck_assertions.standard_verdicts` 给；本文件只判
**本轮七条 EC 的交付**在树上的事实。

**本轮最重要的一条**（EC-06 逐字要求「必须断言真实 run 的读数文件在树，不是散文说跑过」）：
`real-run-readings-are-in-tree` 读
`.cursor/plans/goals/evidence/GOAL-20261104-106-manuscript-chain-live.json`，并判
`state == "SUCCEEDED"`、十一相全 `SUCCEEDED`、`missing_artifacts == []`。散文里写
「跑过」不算 —— 读数文件里的**机器可读事实**才算。

**每一组都钉两侧**（本轮的三件交付各有「实现存在」与「不冒充」两面）：
- 判据在场 **与** 它的读数文件真的含 SUCCEEDED（判据在场 ≠ 跑过）；
- 失败形态台账在场 **与** 台账条目数 ≥ 读数文件记录的失败形态数（不许漏条）；
- 文档写了「首次真实成立」**与** §7 判定表逐字未动（不得为了这句而改口径）。

**判词不绑定树的绝对路径**（两树入口会正确地拒绝这种输出）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# ── EC-01 / EC-02：live 判据 + 真实 run 读数 ─────────────────────────────────────

LIVE_JUDGE = "tests/e2e/test_the_manuscript_chain_runs_live.py"
#: 判据的装配与取数支持件（规模门把判据文件推到 450 行以内 ⇒ 装配面单列在它旁边）。
#: 「产品组合根 / 先写盘再断言」这两条标记因此落在**支持件**里 —— 判据文件仍 import 它，
#: 所以判的是同一件事，不是放宽。（第一版把这两条写在判据文件里，文件拆分后判据假红。）
LIVE_SUPPORT = "tests/e2e/manuscript_chain_live_support.py"
LIVE_JUDGE_MARKERS: tuple[str, ...] = (
    "def test_the_eleven_phase_chain_runs_live(",
    "def test_the_goal105_readings_hold_on_the_real_manuscript(",
    "from tests.e2e.manuscript_chain_live_support import (",
    "pytest.mark.requires_live_llm",
)
#: 支持件必须带的机制标记：产品组合根 / 先写盘再断言。
LIVE_SUPPORT_MARKERS: tuple[str, ...] = (
    "from services.api.composition import assemble",
    "def write_readings(",
    "EVIDENCE.write_text(",
)
#: **不补缝**：live 判据不得出现这几条（它们是「测试侧手工接执行体」的形态）。
#:
#: 判的是 **AST 里的真实语句**，不是文本：本文件的 docstring 就该逐字讨论这几条禁令，
#: 文本搜索会把**禁令本身**读成命中的失败（实测：本断言第一版对 live 判据报红，
#: 命中的是它自己那段「不 `deps.tool_providers = {...}`」的说明）。与 GOAL-105 `W-4`
#: 同一条教训 —— 字符串标记会被提到它的散文骗过。
NO_SEAM_ATTRIBUTES: tuple[str, ...] = ("tool_providers",)
NO_SEAM_CALLS: tuple[str, ...] = ("_attach_capabilities", "_attach_runtime")

#: 真实 run 的读数文件（EC-06 逐字要求：验证器断言它在树，且内容是真跑读数）。
READINGS_EVIDENCE = ".cursor/plans/goals/evidence/GOAL-20261104-106-manuscript-chain-live.json"
#: 本 GOAL 的记录路径（EC 状态如实性判据要读它）。
GOAL_PATH = ".cursor/plans/goals/GOAL-20261104-106-the-manuscript-chain-runs-live.md"
#: 十一相（读数文件里的 `phase_states` 必须恰好是这些键且全 SUCCEEDED）。
PHASES: tuple[str, ...] = (
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
#: 十一件产物（读数文件里的 `present:*` 与 `length:*` 逐件判）。
OUTPUT_NAMES: tuple[str, ...] = (
    "research_question",
    "retrieval_report",
    "novelty_claim",
    "research_plan",
    "review_decision",
    "manuscript_narrative",
    "editorial_decision",
    "author_responses",
    "submission_package",
    "research_report.md",
    "manuscript.md",
    "cover_letter.md",
    "author_contributions.md",
    "conflicts_of_interest.md",
    "data_availability.md",
    "supplementary.md",
    "manuscript_v2.md",
    "response_letter.md",
)

# ── EC-03：GOAL-105 两件机制在真实手稿上的读数 ──────────────────────────────────
#: 读数文件里那三个键必须存在且为真（不是散文断言）。
CITATION_READING_KEYS: tuple[str, ...] = (
    "citation_readings",
    "readings_match_body",
    "action_overlap",
)

# ── EC-04：失败形态台账 ────────────────────────────────────────────────────────
RECHECK = ".cursor/plans/rechecks/RECHECK-20261104-107-manuscript-chain-live.md"
LEDGER_HEADING = "## 真实 run 的失败形态台账"
#: 台账每条必须含的五列（现象 / 读面证据 / 归类 / 修法 / 是否修好）。
LEDGER_COLUMNS: tuple[str, ...] = ("现象", "读面证据", "归类", "修法", "是否修好")

# ── EC-05：文档同步（§7 表逐字不动）────────────────────────────────────────────
QUALITY_DOC = "docs/architecture/MANUSCRIPT_QUALITY.md"
QUALITY_DOC_MARKER = "首次真实"
#: §7 判定表的 5 条判据仍须在场且 `NOT_JUDGED` 仍 5 项（文档同步不得改口径）。
QUALITY_CRITERION_JUDGE = "tests/tooling/test_manuscript_quality_strong_criterion.py"

# ── EC-07：宪章记账 ────────────────────────────────────────────────────────────
PROGRAM_SEQ = 74
PROGRESS_GOAL = "GOAL-20261104-106"
ARCHIVE_PROGRESS = ".cursor/plans/goals/archive/MAINLINE-2026-11-04-progress-103-only.md"
ARCHIVE_REVISIONS = ".cursor/plans/goals/archive/MAINLINE-2026-11-04-revisions-71-only.md"


def _verdict(toolbox: Any, name: str, ok: bool, detail: str = "") -> Any:
    return toolbox.verdict(name, ok, "" if ok else detail)


def _text(root: Path, relative: str) -> str:
    path = root / relative
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _readings(root: Path) -> dict[str, Any] | None:
    """读数文件 → dict（缺失 / 不可解析 ⇒ `None`，由判词点名）。"""
    path = root / READINGS_EVIDENCE
    if not path.is_file():
        return None
    try:
        parsed: Any = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _goal_ec_status(root: Path, ec_id: str) -> str:
    """从 GOAL 正文取某 EC 的 `status:`（按 EC 块定位，不靠全局搜索）。

    与 `verify_goal106_closeout.ec_status` 同一个口径；这里单列一份是因为断言集与验证器
    由**路径**分别加载（`tools/` 不是包），只在同一模块内复用不成立。
    """
    goal = _text(root, GOAL_PATH)
    marker = f"  - id: {ec_id}\n"
    index = goal.find(marker)
    if index == -1:
        return "MISSING"
    tail = goal[index:]
    stop = tail.find("\n  - id: ")
    block = tail[: stop if stop != -1 else len(tail)]
    for line in block.splitlines():
        if line.strip().startswith("status:"):
            return line.split(":", 1)[1].strip()
    return "MISSING"


def _seam_patches(source: str) -> list[str]:
    """源码里**真的**手工补缝的语句（AST 级；空 = 没有补缝）。

    三种形态各自判：
    - `x.tool_providers = ...`（属性赋值）；
    - `replace(<...>._deps, ...)`（给编排依赖做 `replace`）；
    - `_attach_capabilities(...)` / `_attach_runtime(...)`（测试侧的接线函数）。

    **不判文本**：docstring 与注释里逐字讨论这些禁令是判据自身的纪律，文本搜索会把
    禁令读成命中（GOAL-105 `W-4`：字符串标记式判据会被提到它的散文骗过）。
    """
    import ast

    found: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:  # 语法错由别的判据负责
        return found
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
            if node.attr in NO_SEAM_ATTRIBUTES:
                found.append(f"line {node.lineno}: .{node.attr} 被赋值（手工补缝）")
        elif isinstance(node, ast.Call):
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None) or ""
            if name in NO_SEAM_CALLS:
                found.append(f"line {node.lineno}: 调用了 {name}()（测试侧接线）")
            elif name == "replace" and node.args:
                first = node.args[0]
                if "_deps" in ast.dump(first):
                    found.append(f"line {node.lineno}: replace(... _deps ...)（手工补缝）")
    return found


def _judge_verdicts(toolbox: Any, root: Path) -> list[Any]:
    """EC-01：live 判据在场、带两条用例、**不补缝**、先写盘再断言。

    「不补缝」按 **AST** 判**两个文件**（判据 + 它的装配支持件）：缝只可能补在装配面，
    而装配面在文件拆分的哪一边都不该出现。
    """
    source = _text(root, LIVE_JUDGE)
    support = _text(root, LIVE_SUPPORT)
    missing = [marker for marker in LIVE_JUDGE_MARKERS if marker not in source]
    unsupported = [marker for marker in LIVE_SUPPORT_MARKERS if marker not in support]
    patched = _seam_patches(source) + _seam_patches(support)
    return [
        _verdict(
            toolbox,
            "live-judge-carries-its-markers",
            bool(source) and not missing,
            f"{LIVE_JUDGE} 缺失标记：{','.join(missing)}" if source else f"{LIVE_JUDGE} 不在树",
        ),
        _verdict(
            toolbox,
            "live-support-carries-the-mechanism",
            bool(support) and not unsupported,
            f"{LIVE_SUPPORT} 缺失标记：{','.join(unsupported)}"
            if support
            else f"{LIVE_SUPPORT} 不在树",
        ),
        _verdict(
            toolbox,
            "live-judge-patches-no-seam",
            bool(source) and bool(support) and not patched,
            f"live 判据不得手工补缝（命中：{patched}）",
        ),
    ]


def _artifact_verdicts(toolbox: Any, readings: dict[str, Any]) -> list[Any]:
    """产物面：十一件全在场、字节可读、`missing_artifacts` 为空（单列以守住函数长度门）。"""
    present = {name: readings.get(f"present:{name}") for name in OUTPUT_NAMES}
    lengths = {name: readings.get(f"length:{name}") for name in OUTPUT_NAMES}
    return [
        _verdict(
            toolbox,
            "real-run-artifacts-all-present",
            readings.get("missing_artifacts") == [] and all(present.values()),
            f"缺失产物：{readings.get('missing_artifacts')}；present={present}",
        ),
        _verdict(
            toolbox,
            "real-run-artifacts-carry-bytes",
            all(isinstance(v, int) and v > 0 for v in lengths.values()),
            f"有产物读不回字节：{lengths}",
        ),
    ]


def _real_run_verdicts(toolbox: Any, root: Path) -> list[Any]:
    """EC-02 / EC-06：**真实 run 的读数文件在树**，且它**如实**记录了这次 run 的终态。

    这是本轮最重要的一组：散文说「跑过」不算，读数文件里的机器可读事实才算。

    **两种合法形态，都必须被如实读出**（照 `goal076_closeout_assertions._status_verdicts`
    的既有形态：判**如实性**，不判「是否成功」）：

    - `SUCCEEDED` ⇒ 十一相全 `SUCCEEDED`、产物全在场、字节全可读；
    - **未达成** ⇒ 读数文件的终态**必须**与 GOAL 的 `EC-02` 状态一致（都是「未完成」），
      且台账里有对应的失败条目。**这才是判据该判的东西** —— 一条「必须成功否则判红」的
      断言会让验证器在等待上游窗口期间持续红，而**红的原因不是资产坏了**；反过来，把
      断言放宽成「有个文件就行」则会让「没跑过」冒充「跑过了」。两头都是伪造验证证据。
    """
    readings = _readings(root)
    if readings is None:
        return [
            _verdict(
                toolbox,
                "real-run-readings-are-in-tree",
                False,
                f"{READINGS_EVIDENCE} 缺失或不可解析 ⇒ 无法证明真跑过",
            )
        ]
    return _truthfulness_verdicts(toolbox, root, readings)


def _truthfulness_verdicts(toolbox: Any, root: Path, readings: dict[str, Any]) -> list[Any]:
    """如实性四条（单列以守住函数长度门；语义见 `_real_run_verdicts` 的 docstring）。"""
    terminal = readings.get("state")
    ec02 = _goal_ec_status(root, "EC-02")
    return [
        _verdict(toolbox, "real-run-readings-are-in-tree", True, ""),
        _verdict(
            toolbox,
            "real-run-names-a-run-id",
            bool(readings.get("run_id")),
            "读数文件必须记下真实 run id（否则不可复述是哪一个 run）",
        ),
        _verdict(
            toolbox,
            "real-run-terminal-state-is-read-honestly",
            terminal in {"SUCCEEDED", "FAILED"},
            f"读数文件的终态 {terminal!r} 不是一次 run 的合法终态",
        ),
        # 如实性：GOAL 的 EC-02 说达成了 ⇔ 读数文件说 SUCCEEDED。两者必须同向。
        _verdict(
            toolbox,
            "goal-ec02-agrees-with-the-readings",
            (ec02 == "PASS") == (terminal == "SUCCEEDED"),
            f"GOAL 的 EC-02={ec02!r} 但读数文件终态={terminal!r} —— 两者必须同向"
            "（一边说完成、一边说没完成就是伪造）",
        ),
    ]


def _success_verdicts(toolbox: Any, root: Path) -> list[Any]:
    """**仅当**读数文件真的 `SUCCEEDED` 时才要求全套：十一相、产物、字节。

    未达成时这一组**不产出**判词 —— 判它「没成功」是重复 `goal-ec02-agrees-with-the-readings`
    已经判过的事，而**假装它成功**才是要防的（由上面那条同向判据挡）。
    """
    readings = _readings(root)
    if readings is None or readings.get("state") != "SUCCEEDED":
        return []
    states = readings.get("phase_states") or {}
    if not isinstance(states, dict):
        states = {}
    return [
        _verdict(
            toolbox,
            "real-run-carries-eleven-phases",
            sorted(states) == sorted(PHASES) and all(v == "SUCCEEDED" for v in states.values()),
            f"相级状态不符：{states}",
        ),
        *_artifact_verdicts(toolbox, readings),
    ]


def _ledger_body(root: Path) -> str | None:
    """台账小节的正文（标题不在 ⇒ `None`）。标题**只认行首**，见下面那条注释。"""
    source = _text(root, RECHECK)
    # **按行首匹配标题**，不是 `in source` 也不是裸 `split`：本轮实测，RECHECK 的逐条读数
    # 表里有一格**引用了这个标题名**（`| EC-04 | 失败形态台账 | PASS | 本文件 \`## …\` |`）
    # ⇒ 用 `source.split(HEADING)` 会切在**那一格**上，随后「下一个 `## `」把它截成空串，
    # 于是「五列齐备 / 有条目」两条同时假红。标题只认**行首**（与 GOAL-094 的教训同族）。
    marker = f"\n{LEDGER_HEADING}"
    if marker not in source:
        return None
    section = source.split(marker, 1)[1]
    stop = section.find("\n## ")
    return section[: stop if stop != -1 else len(section)]


def _ledger_verdicts(toolbox: Any, root: Path) -> list[Any]:
    """EC-04：失败形态台账在场、五列齐备、条目数不为零。

    **两条实测出来的取数纪律**（都曾让本条判据假红）：

    1. **台账是文件里的小节，可能不是最后一节**，也可能**是**最后一节 —— 只按
       「下一个 `## `」截断会把「最后一节」读成空串（第一版就栽在这里：表头明明在，
       判词却说「五列缺失」）。
    2. **数据行以 `| F-` 开头**（`F-1`…`F-N` 是台账自己的编号），**不是** `| \\``
       —— 编号不是代码片段。第一版按 `| \\`` 数行，永远是 0 条。
    """
    body = _ledger_body(root)
    if body is None:
        return [
            _verdict(
                toolbox,
                "failure-form-ledger-is-in-the-recheck",
                False,
                f"{RECHECK} 缺 `{LEDGER_HEADING}` 一节",
            )
        ]
    missing = [column for column in LEDGER_COLUMNS if column not in body]
    rows = [line for line in body.splitlines() if line.startswith("| F-")]
    return [
        _verdict(toolbox, "failure-form-ledger-is-in-the-recheck", True, ""),
        _verdict(
            toolbox,
            "failure-form-ledger-has-five-columns",
            not missing,
            f"台账每条必须含五列，缺：{missing}",
        ),
        _verdict(
            toolbox,
            "failure-form-ledger-has-entries",
            bool(rows),
            "台账必须至少有一条（零条 = 没有归因过任何失败形态，那是空真）",
        ),
    ]


def _record_verdicts(toolbox: Any, root: Path) -> list[Any]:
    """记录面（EC-05 文档同步 + EC-07 宪章记账）→ 单列在 `goal106_record_assertions.py`。

    **为什么按面拆**：`tools/` 脚本也受 450 行 / 50 行函数双门约束。产品面（live 判据 /
    真实 run 读数 / GOAL-105 读数 / 失败形态台账）与记录面（文档 + 宪章）是两类事实，
    按面切分即满足规模门，又**不把任何判据挪出射程**（同一个验证器仍调用它）。
    """
    import importlib.util
    import sys

    path = Path(__file__).resolve().parent / "goal106_record_assertions.py"
    spec = importlib.util.spec_from_file_location("goal106_record_assertions", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal106_record_assertions"] = module
    spec.loader.exec_module(module)
    verdicts = getattr(module, "record_verdicts")
    return list(verdicts(toolbox, root))


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 特有断言的全集（收口验证器把它们与标准面拼起来）。"""
    return [
        *_judge_verdicts(toolbox, root),
        *_real_run_verdicts(toolbox, root),
        *_success_verdicts(toolbox, root),
        *_ledger_verdicts(toolbox, root),
        *_record_verdicts(toolbox, root),
    ]


__all__ = ["assertion_verdicts"]
