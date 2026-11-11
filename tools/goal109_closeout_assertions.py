"""GOAL-20261111-109 的**产品面断言集**（收口验证器的另一半）。

与 `tools/verify_goal109_closeout.py`（记录面）分工：本文件判**交付物真的在、且形态就是
声明的那一个**；主文件判 EC 终态与宪章记账。

**本轮的判法**（每条指向具体闭集或具体行为，不判「模块存在」）：

* 可比键（EC-01）：剔除面恰是三个身份字段；`semantic_digest` 在同装配对上不等
  （「不能用」的机械事实钉在断言集里）。
* 两臂（EC-02）：`only_slot_differs` 对六段各成立；**别的段漂移 ⇒ 证明判假**（反证）。
* 读数（EC-03）：两种「空」点名字段可辨；引用计数有分母。
* 报告与门（EC-04/05）：`MIN_CORPUS=3` 与产品侧常量同值；k=2 判「不足」并点名；
  措辞闭集非空、出口守卫在渲染函数体内。
* 阶梯（EC-06）：「计划」行带新 bar、其余三格**不含**消融句（试点射程）。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

#: 四个新件（少一件 = 该 EC 没交付）。
DELIVERABLES: tuple[str, ...] = (
    "packages/application/run_orchestration/comparison_digest.py",
    "packages/application/run_orchestration/ablation.py",
    "packages/application/run_orchestration/output_readings.py",
    "tools/ablation_report.py",
)

#: 判据文件（`verify:` 字段点名的每一个都必须**在树**——GOAL-108 的教训）。
JUDGES: tuple[str, ...] = (
    "tests/application/run_orchestration/test_comparison_digest.py",
    "tests/application/run_orchestration/test_ablation_pair.py",
    "tests/application/run_orchestration/test_output_readings.py",
    "tests/tooling/test_ablation_report_gate.py",
    "tests/tooling/test_ablation_report_wording.py",
    "tests/tooling/test_goal109_ladder_pilot_scope.py",
)

#: 本轮收口资产（自指）。
VERIFIER = "tools/verify_goal109_closeout.py"
ASSERTIONS = "tools/goal109_closeout_assertions.py"

#: 「计划」行新 bar 的锚（与 `test_goal109_ladder_pilot_scope.py` 同源；两处断言互为备份）。
PLAN_NEW_MARKER = "配对消融下"
PLAN_OLD_MARKER = "计划改变下一轮问题"
#: 其余三格不得被推广。
UNCHANGED_PREFIXES: tuple[str, ...] = ("| 检索 |", "| 复检 |", "| 迭代 |")


def _load_tool_source(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _load_module(root: Path, relative: str, name: str) -> ModuleType | None:
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
    verdicts: list[Any] = []
    for relative in (*DELIVERABLES, *JUDGES, VERIFIER, ASSERTIONS):
        verdicts.append(
            toolbox.verdict(
                f"delivered-{Path(relative).name}",
                (root / relative).is_file(),
                f"{relative} 不在树",
            )
        )
    return verdicts


def _comparison_digest_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：用**真 manifest** 在断言集里重放键的两条性质（不等依赖任何判据文件）。"""
    module = _load_module(
        root, "packages/application/run_orchestration/comparison_digest.py", "g109_comparison"
    )
    if module is None:
        return [toolbox.verdict("comparison-key-importable", False, "comparison_digest 不可加载")]
    from packages.domain.core import Version
    from packages.domain.manifest import RunManifest

    left = RunManifest(run_id="run-a", project_id="p", protocol_version=Version(text="1.0.0"))
    right = RunManifest(run_id="run-b", project_id="p", protocol_version=Version(text="1.0.0"))
    return [
        toolbox.verdict(
            "comparison-key-ignores-identity-fields",
            module.comparable(left, right),
            "仅 run_id 不同的两份 manifest 必须可配对",
        ),
        toolbox.verdict(
            "comparison-key-excludes-exactly-three",
            set(module.EXCLUDED_FIELDS) == {"run_id", "frozen_at", "project_id"},
            f"剔除面必须恰是三个身份字段，实得 {sorted(module.EXCLUDED_FIELDS)}",
        ),
        toolbox.verdict(
            "semantic-digest-cannot-pair-runs",
            left.semantic_digest() != right.semantic_digest(),
            "semantic_digest 含 run_id ⇒ 不能当配对键（EC-01 点名的那句话）",
        ),
    ]


def _ablation_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：六段各消融一次 + 反证（别的段漂移 ⇒ 证明判假）。"""
    module = _load_module(
        root, "packages/application/run_orchestration/ablation.py", "g109_ablation"
    )
    if module is None:
        return [toolbox.verdict("ablation-importable", False, "ablation 不可加载")]
    from packages.domain.core import Version
    from packages.domain.manifest import RunManifest

    slots: dict[str, str] = {name: f"PAYLOAD::{name}" for name in module.SLOT_ORDER}
    manifest = RunManifest(run_id="run-a", project_id="p", protocol_version=Version(text="1.0.0"))
    all_slots_hold = all(
        module.build_pair(manifest, slots, slot).only_slot_differs() for slot in module.SLOT_ORDER
    )
    drifted = {**slots, "direction": slots["direction"] + "X", "retrieval": None}
    counter = module.AblationPair(
        slot="retrieval",
        present=module.PromptArm(manifest=manifest, slots=slots),
        absent=module.PromptArm(manifest=manifest, slots=drifted),
    )
    return [
        toolbox.verdict(
            "ablation-pair-holds-for-every-slot",
            all_slots_hold,
            "六段各消融一次都必须成立（机制不挑段）",
        ),
        toolbox.verdict(
            "ablation-proof-rejects-extra-drift",
            counter.only_slot_differs() is False and "direction" in counter.differing_sections(),
            "别的段漂移 ⇒ 机械证明必须判假（它真在逐段比）",
        ),
    ]


def _readings_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：两种「空」点名字段可辨 + 引用计数有分母。"""
    module = _load_module(
        root, "packages/application/run_orchestration/output_readings.py", "g109_readings"
    )
    if module is None:
        return [toolbox.verdict("readings-importable", False, "output_readings 不可加载")]
    unreadable = module.read_plan_payload(None)
    no_block = module.read_plan_payload({"content": "a plan without a design block"})
    cited = module.read_plan_payload(
        {"content": "builds on mem-20261101-235"},
        known_memory_ids=("mem-20261101-235",),
    )
    stray = module.read_plan_payload(
        {"content": "mentions mem-999999-999"},
        known_memory_ids=("mem-20261101-235",),
    )
    return [
        toolbox.verdict(
            "readings-name-two-kinds-of-empty",
            unreadable.source_state == "payload_absent"
            and no_block.source_state == "payload_present"
            and no_block.design_state == "block_absent",
            "两种「空」必须点名字段可辨（payload_absent ≠ block_absent）",
        ),
        toolbox.verdict(
            "citation-counting-has-a-denominator",
            cited.cited_memory_ids == ("mem-20261101-235",) and stray.cited_memory_ids == (),
            "引用计数只在已知分母里找（不在分母的 id 形 token 不算）",
        ),
    ]


def _report_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04/05：门常量同值、k=2 拒绝点名、措辞闭集非空、出口守卫在渲染函数体内。"""
    module = _load_module(root, "tools/ablation_report.py", "g109_report")
    if module is None:
        return [toolbox.verdict("report-importable", False, "ablation_report 不可加载")]
    from packages.application.deliverable.citation_distribution import MIN_CORPUS as PRODUCT

    def obs() -> dict[str, object]:
        return {
            "comparison_digest": "sha256:a",
            "design_block": 1,
            "arm_count": 2,
            "parameter_count": 3,
            "citation_count": 1,
        }

    def pairs(count: int) -> dict[str, object]:
        return {
            "slot": "retrieval",
            "pairs": [
                {"label": f"k{i}", "present": obs(), "absent": obs()} for i in range(1, count + 1)
            ],
        }

    gate_two = module.build_report(pairs(2)).gate
    source = _load_tool_source(root, "tools/ablation_report.py")
    render_body = source.split("def render_report", 1)[1].split("\ndef ", 1)[0]
    return [
        toolbox.verdict(
            "report-min-corpus-matches-product",
            module.MIN_CORPUS == 3 == PRODUCT,
            "MIN_CORPUS=3 必须与产品侧 citation_distribution 同值",
        ),
        toolbox.verdict(
            "report-gate-refuses-two-pairs-by-name",
            gate_two.sufficient is False and "2 of 3 required" in gate_two.missing[0],
            "k=2 必须判「不足」并点名",
        ),
        toolbox.verdict(
            "report-wording-closed-set-non-empty",
            len(module.forbidden_words()) >= 4 and "采纳" in module.forbidden_words(),
            "措辞闭集必须非空且含「采纳」",
        ),
        toolbox.verdict(
            "report-exit-guard-lives-in-render",
            "forbidden wording" in render_body,
            "出口守卫必须在渲染函数体内（fail-closed 在出口）",
        ),
    ]


def _ladder_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-06：计划行带新 bar；其余三格不含消融句（试点射程）。"""
    charter = toolbox.text(root, ".cursor/plans/goals/MAINLINE.md")
    plan_row = next((line for line in charter.splitlines() if line.startswith("| 计划 |")), "")
    return [
        toolbox.verdict(
            "ladder-plan-row-carries-the-new-bar",
            PLAN_NEW_MARKER in plan_row and PLAN_OLD_MARKER not in plan_row,
            "「计划」行的 下一级 必须是消融 bar（替换，不是追加）",
        ),
        *(
            toolbox.verdict(
                f"ladder-{prefix.strip('| ').strip()}-not-promoted",
                ABLATION_PROMOTION_MARKER
                not in next((line for line in charter.splitlines() if line.startswith(prefix)), ""),
                f"{prefix.strip('| ')} 行不得被越级推广",
            )
            for prefix in UNCHANGED_PREFIXES
        ),
    ]


ABLATION_PROMOTION_MARKER = "配对消融"


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 的产品面全量断言（验证器按路径加载并调用它）。"""
    return [
        *_file_verdicts(root, toolbox),
        *_comparison_digest_verdicts(root, toolbox),
        *_ablation_verdicts(root, toolbox),
        *_readings_verdicts(root, toolbox),
        *_report_verdicts(root, toolbox),
        *_ladder_verdicts(root, toolbox),
    ]
