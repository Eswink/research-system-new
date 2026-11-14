"""GOAL-20261114-113 的**产品面断言集**（收口验证器的另一半）。

与 `tools/verify_goal113_closeout.py`（记录面）分工：本文件判**交付物真的在、且行为
真的对**（重放行为，不只查文件存在）；主文件判 EC 终态与宪章记账。

**本轮的判法**：

* 四行装配（EC-01）：`OrchestrationDependencies` 有 `memory_gate` 字段、
  `runner_wiring` 传参、两个组合根各调用自己的 builder；
* 声明面（EC-02）：真加载 34 份合约 —— `research_manuscript` 带声明
  （tier=PROJECT、confidence=Decimal("0.8")）、`editorial_decision` 不带、
  `experiment`/`report` 排他不受影响；
* 声明不进 gate（EC-03）：`gate.py` 源码**不含** `memory_export`
  （门不因声明放宽；`_CURATOR_TIERS` 逐字）；
* Decimal 不变量（EC-02 偏离的理由面）：canonical 序列化拒绝 float、
  spec 的 confidence 是 Decimal、loader 用 `Decimal(str(...))` 换算；
* condenser（EC-06）：两处构造点都传护栏、参数逐字、无 `max_tokens` / 无
  `max_message_chars`；
* metric（EC-07）：两个名字逐字在词表与采样点；
* 阶梯（EC-09）：「迭代」行带本轮 bar、其余六行不被推广。
"""

from __future__ import annotations

import importlib.util
import sys
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

DELIVERABLES: tuple[str, ...] = (
    "packages/application/run_orchestration/dependencies.py",
    "packages/application/run_orchestration/runner_wiring.py",
    "packages/application/run_orchestration/memory_promotion.py",
    "services/api/memory_gate_support.py",
    "services/api/composition.py",
    "services/api/pg_composition.py",
    "packages/domain/tasks.py",
    "adapters/contracts/tasks_loaders.py",
    "schemas/task-contract.schema.json",
    "examples/contracts/task_contracts.yaml",
    "adapters/openhands/session_builder.py",
    "packages/application/observability/attributes.py",
)

JUDGES: tuple[str, ...] = (
    "tests/application/run_orchestration/test_memory_export_declaration.py",
    "tests/integration/test_ig1_phase_runner.py",
    "tests/adapters/openhands/test_session_guardrail_and_readings.py",
)

VERIFIER = "tools/verify_goal113_closeout.py"
ASSERTIONS = "tools/goal113_closeout_assertions.py"

#: 阶梯锚（本轮推进的是「迭代」格）。
ITERATION_BAR = "记忆的最后一米"
#: 本轮**不动**的六行各自的边界锚（`下一级` 格内；取改写后实测）。
OTHER_LADDER_ANCHORS: tuple[tuple[str, str], ...] = (
    ("| 检索 |", "检索改变下一轮问题"),
    ("| 计划 |", "配对消融下"),
    ("| 复检 |", "评审者与作者分开"),
    ("| 证据 |", "处置闭环成立（策略闭集 + 可判依据）"),
    ("| 报告 |", "叙述质量与事实一致性可判"),
    ("| 实验 |", "三条约束在全部执行面生效"),
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


def _assembly_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01 四行装配：字段、传参、两个组合根的 builder 调用逐处在源码面按压。"""
    deps_src = (root / "packages/application/run_orchestration/dependencies.py").read_text(
        encoding="utf-8"
    )
    wiring_src = (root / "packages/application/run_orchestration/runner_wiring.py").read_text(
        encoding="utf-8"
    )
    sqlite_src = (root / "services/api/composition.py").read_text(encoding="utf-8")
    pg_src = (root / "services/api/pg_composition.py").read_text(encoding="utf-8")
    return [
        toolbox.verdict(
            "dependencies-has-memory-gate-field",
            "memory_gate: Any | None = None" in deps_src,
            "OrchestrationDependencies 必须声明 memory_gate（缺省 None）",
        ),
        toolbox.verdict(
            "runner-wiring-passes-memory-gate",
            "memory_gate=deps.memory_gate" in wiring_src,
            "runner_wiring 必须把 deps.memory_gate 传进 PhaseRunnerDeps",
        ),
        toolbox.verdict(
            "sqlite-root-wires-the-gate",
            "memory_gate=sqlite_memory_gate(faces, ports)" in sqlite_src,
            "SQLite 组合根必须经 sqlite_memory_gate 注入",
        ),
        toolbox.verdict(
            "pg-root-wires-the-gate",
            "memory_gate=pg_memory_gate(c, inputs)" in pg_src,
            "PG 组合根必须经 pg_memory_gate 注入",
        ),
    ]


def _declaration_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02 声明面：真加载 34 份合约，声明只在 research_manuscript。"""
    catalog = _module(root, "services/api/catalog.py", "goal113_catalog")
    assert catalog is not None, "services/api/catalog.py 载入失败"
    contracts = catalog.load_task_contracts("examples/contracts/task_contracts.yaml")
    manuscript = contracts.get("research_manuscript")
    declared = getattr(manuscript, "memory_export", None) if manuscript is not None else None
    editorial = contracts.get("editorial_decision")
    verdicts: list[Any] = [
        toolbox.verdict(
            "contracts-load-thirty-four",
            len(contracts) == 34,
            f"合约总数应 34（既有面逐字不变），实测 {len(contracts)}",
        ),
        toolbox.verdict(
            "manuscript-declares-project-tier",
            declared is not None and str(declared.tier.value) == "PROJECT",
            "research_manuscript 必须声明 memory_export tier=PROJECT",
        ),
        toolbox.verdict(
            "declared-confidence-is-decimal",
            declared is not None
            and isinstance(declared.confidence, Decimal)
            and declared.confidence == Decimal("0.8"),
            "声明 confidence 必须是 Decimal('0.8')（canonical 序列化拒绝 float）",
        ),
        toolbox.verdict(
            "editorial-does-not-declare",
            editorial is not None and editorial.memory_export is None,
            "未声明的合约必须仍是 None（零回归的机械形态）",
        ),
    ]
    tasks_src = (root / "packages/domain/tasks.py").read_text(encoding="utf-8")
    loaders_src = (root / "adapters/contracts/tasks_loaders.py").read_text(encoding="utf-8")
    verdicts.extend([
        toolbox.verdict(
            "spec-confidence-is-decimal-in-source",
            'confidence: Decimal = Decimal("0.8")' in tasks_src,
            "MemoryExportSpec.confidence 源码必须声明为 Decimal",
        ),
        toolbox.verdict(
            "loader-converts-confidence-via-decimal",
            'Decimal(str(raw.get("confidence", "0.8")))' in loaders_src,
            "loader 必须经 Decimal(str(...)) 换算（float 不进 canonical）",
        ),
    ])
    return verdicts


def _gate_untouched_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：`gate.py` 一行不改 —— 声明不进门；curator 档位逐字保留。"""
    gate_src = (root / "packages/application/memory/gate.py").read_text(encoding="utf-8")
    return [
        toolbox.verdict(
            "gate-does-not-know-the-declaration",
            "memory_export" not in gate_src,
            "gate.py 不得读 memory_export（声明是编排层授权来源，不是门参数）",
        ),
        toolbox.verdict(
            "gate-curator-tiers-verbatim",
            "_CURATOR_TIERS = (MemoryTier.PROJECT, MemoryTier.ORGANIZATION)" in gate_src,
            "curator 档位逐字保留（PROJECT/ORGANIZATION 需审批）",
        ),
    ]


def _condenser_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-06/07：两处 kwarg、参数逐字、无 max_tokens / max_message_chars、metric 名逐字。"""
    src = (root / "adapters/openhands/session_builder.py").read_text(encoding="utf-8")
    attrs_src = (root / "packages/application/observability/attributes.py").read_text(
        encoding="utf-8"
    )
    count = src.count("condenser=_context_guardrail(llm)")
    return [
        toolbox.verdict(
            "condenser-kwarg-on-both-sites",
            count == 2,
            f"两处 PolicyEnforcingAgent 构造点都要传护栏，实测 {count} 处",
        ),
        toolbox.verdict(
            "guardrail-parameters-verbatim",
            "LLMSummarizingCondenser(llm=llm, max_size=80, keep_first=4)" in src,
            "护栏参数必须逐字（复用同一 llm + keep_first=4）",
        ),
        toolbox.verdict(
            "no-token-threshold",
            "max_tokens=" not in src,
            "不得设 max_tokens（触发 HARD 路径）",
        ),
        toolbox.verdict(
            "no-max-message-chars",
            "max_message_chars=" not in src,
            "不得把 max_message_chars 设成 kwarg（openhands-sdk==1.42.0 死字段；"
            "护栏 docstring 里点名的文字不算）",
        ),
        toolbox.verdict(
            "read-only-metric-names-in-vocabulary",
            'SESSION_VIEW_EVENTS = "research_os.session.view_events"' in attrs_src
            and 'SESSION_PROMPT_TOKENS_TOTAL = "research_os.session.prompt_tokens_total"'
            in attrs_src,
            "两个只读读数的 metric 名必须逐字在闭集词表",
        ),
    ]


def _ladder_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-09：迭代行带本轮 bar；其余六行既保自己的锚、也不被推广。

    阶梯表是**四列**（域 | 当前级 | 依据 GOAL | 下一级是什么）⇒ 每行 **5 个竖线**；
    按行首前缀直接取行（与 GOAL-112 断言集同一取法）——按列数过滤会把阶梯行全滤掉。
    """
    charter = (root / ".cursor/plans/goals/MAINLINE.md").read_text(encoding="utf-8")
    lines = charter.splitlines()

    def ladder_row(prefix: str) -> str:
        return next((line for line in lines if line.startswith(prefix)), "")

    verdicts = [
        toolbox.verdict(
            "ladder-iteration-row-carries-the-bar",
            ITERATION_BAR in ladder_row("| 迭代 |"),
            "阶梯「迭代」行的 当前级 必须收录本轮推进（记忆的最后一米）",
        )
    ]
    for prefix, anchor in OTHER_LADDER_ANCHORS:
        name = prefix.strip("| ").strip()
        row = ladder_row(prefix)
        verdicts.append(
            toolbox.verdict(
                f"ladder-{name}-keeps-its-anchor",
                anchor in row,
                f"{name} 行的边界锚必须仍在（不得被改写）",
            )
        )
        verdicts.append(
            toolbox.verdict(
                f"ladder-{name}-stays-unpromoted",
                ITERATION_BAR not in row,
                f"{name} 行不得被越级推广（一轮只推进一格）",
            )
        )
    return verdicts


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """产品面断言（主文件逐条并入总判词）。"""
    return [
        *_file_verdicts(root, toolbox),
        *_assembly_verdicts(root, toolbox),
        *_declaration_verdicts(root, toolbox),
        *_gate_untouched_verdicts(root, toolbox),
        *_condenser_verdicts(root, toolbox),
        *_ladder_verdicts(root, toolbox),
    ]
