"""GOAL-20261117-114 的产品面断言集（收口验证器的另一半）。

与 `tools/verify_goal114_closeout.py`（记录面）分工：本文件判**交付物真的在、且形态就是
声明的那一个**；主文件判 EC 终态与宪章记账。

**本轮的判法**（每条指向具体闭集或具体行为，不判「模块存在」）：

* 可比键（EC-02）：归一化面**显式声明**且只剥一个墙钟键；`EXCLUDED_FIELDS` 仍是那三个；
  真实形状的两份 manifest 可配对，而语义差异仍判不可比（六条反证）。
* 冻结快照（EC-03）：payload 带第三键，且它不是另两个 digest 的别名。
* 观测映射（EC-04）：四列是 `int`、不是 `bool`；闭集外状态点名拒绝。
* 消融台（EC-05）：单相、合约逐字、能力集与来源相集合相等、相 id 是产品瞄准的那个。
* 读数（EC-07）：证据 JSON 六条 run、六条可比键**逐字相同**、语料门给出结论、
  三列位移（`citation_count` 必须真的位移 —— 首轮它是恒 0 的判据缺陷）。
* 阶梯（EC-08）：`下一级` 逐字不动（bar 未升）。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any

#: 四个新件 + 一个改动件（少一件 = 该 EC 没交付）。
DELIVERABLES: tuple[str, ...] = (
    "packages/application/run_orchestration/ablation_observations.py",
    "examples/protocols/ablation_plan_probe_v1.yaml",
    "tests/e2e/test_paired_ablation_offline_arms.py",
    "tests/e2e/test_paired_ablation_on_the_plan_live.py",
    "tests/tooling/test_the_latest_terminal_goal_is_charter_readable.py",
)

#: 判据文件（`verify:` 字段点名的每一个都必须**在树**）。
JUDGES: tuple[str, ...] = (
    "tests/application/run_orchestration/test_comparison_digest.py",
    "tests/application/run_orchestration/test_ablation_observations.py",
    "tests/application/run_orchestration/test_frozen_payload_semantic_digest.py",
    "tests/contracts/test_ablation_plan_probe_protocol.py",
)

#: 本轮收口资产（自指）。
VERIFIER = "tools/verify_goal114_closeout.py"
ASSERTIONS = "tools/goal114_closeout_assertions.py"

#: 真跑读数（EC-07 的产物）。
EVIDENCE = ".cursor/plans/goals/evidence/GOAL-20261117-114-ablation-k3.json"

#: 阶梯「计划」行：`下一级` 的**逐字**锚（bar 未升的机械形态）。
NEXT_LEVEL_MARKERS: tuple[str, ...] = (
    "**配对消融下，X 的存在使输出读数分布发生位移**",
    "不判**「模型采纳了 X」",
    "MIN_CORPUS=3",
)
#: 本轮追加的**描述性**读数锚（`当前级`）。
CURRENT_LEVEL_MARKER = "已按 k=3 两臂实测四列"


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


def _exception(**overrides: object) -> dict[str, object]:
    """一条**真实形状**的例外（键与值都照 `policy_acceptance._allowed_entries` 写）。"""
    entry: dict[str, object] = {
        "capability": "workspace.read",
        "phase_id": "retrieval",
        "provider_id": "openhands_workspace",
        "policy_version": "policy-1",
        "decision": "ALLOW",
        "constraints": {"effect_class": "EXECUTE"},
        "accepted_at": "2026-11-18T04:57:01.000000+00:00",
    }
    entry.update(overrides)
    return entry


def _digest_fixtures() -> tuple[Any, Any, Any, Any]:
    """四份 manifest：基线 / 左 / 右（只差身份+墙钟）/ 漂移（语义不同）。"""
    from packages.domain.core import Version
    from packages.domain.manifest import RunManifest

    def manifest(**kwargs: Any) -> Any:
        return RunManifest(protocol_version=Version(text="1.0.0"), **kwargs)

    base = manifest(run_id="a", project_id="p")
    left = manifest(run_id="a", project_id="p", accepted_policy_exceptions=[_exception()])
    right = manifest(
        run_id="b",
        project_id="p2",
        accepted_policy_exceptions=[_exception(accepted_at="2026-11-11T11:26:07.000000+00:00")],
    )
    drifted = manifest(
        run_id="c",
        project_id="p",
        accepted_policy_exceptions=[_exception(capability="artifact.write")],
    )
    return base, left, right, drifted


def _digest_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：归一化面**显式声明**且只剥一个墙钟键；剔除面未变宽。"""
    module = _load_module(
        root, "packages/application/run_orchestration/comparison_digest.py", "g114_digest"
    )
    if module is None:
        return [
            toolbox.verdict("comparison-digest-importable", False, "comparison_digest 不可加载")
        ]
    base, left, right, drifted = _digest_fixtures()
    return [
        toolbox.verdict(
            "normalization-is-one-declared-nested-key",
            tuple(module.NORMALIZED_NESTED_KEYS)
            == (("accepted_policy_exceptions", "accepted_at"),),
            f"归一化面必须显式声明且只一个键，实得 {module.NORMALIZED_NESTED_KEYS}",
        ),
        toolbox.verdict(
            "excluded-fields-still-exactly-three",
            set(module.EXCLUDED_FIELDS) == {"run_id", "frozen_at", "project_id"},
            f"剔除面必须仍是三个身份字段，实得 {sorted(module.EXCLUDED_FIELDS)}",
        ),
        toolbox.verdict(
            "acceptance-instant-does-not-break-pairing",
            module.comparable(left, right),
            "只差 `accepted_at` 的两份 manifest 必须可配对（真实路径的形状）",
        ),
        toolbox.verdict(
            "semantic-difference-still-breaks-pairing",
            not module.comparable(left, drifted) and not module.comparable(base, drifted),
            "例外表的语义差异必须仍判不可比（归一化没把字段丢掉）",
        ),
    ]


def _payload_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：冻结快照带第三键，且它不是另两个 digest 的别名。"""
    module = _load_module(
        root, "packages/application/run_orchestration/eventing.py", "g114_eventing"
    )
    if module is None:
        return [toolbox.verdict("eventing-importable", False, "eventing 不可加载")]
    from packages.domain.core import ID, Timestamp, Version
    from packages.domain.manifest import RunManifest
    from packages.domain.run import ResearchRun

    run_id = ID.generate()
    run = ResearchRun(id=run_id, project_id="project-1", protocol_id="protocol-1")
    left = module.frozen_payload(
        run,
        RunManifest(run_id=run_id.value, project_id="project-1", protocol_version=Version("0.4.0")),
    )
    right = module.frozen_payload(
        run,
        RunManifest(
            run_id=ID.generate().value,
            project_id="project-1",
            protocol_version=Version("0.4.0"),
            frozen_at=Timestamp(datetime(2026, 11, 18, tzinfo=timezone.utc)),
        ),
    )
    return [
        toolbox.verdict(
            "frozen-payload-carries-comparison-digest",
            str(left.get("comparison_digest") or "").startswith("sha256:"),
            "冻结快照必须带可比键（完整 manifest 不落库 ⇒ 事后无从复算）",
        ),
        toolbox.verdict(
            "comparison-digest-pairs-what-the-others-cannot",
            left["comparison_digest"] == right["comparison_digest"]
            and left["digest"] != right["digest"]
            and left["semantic_digest"] != right["semantic_digest"],
            "身份字段不同 ⇒ 只有可比键相等（它不是另两个 digest 的别名）",
        ),
    ]


def _observation_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四列 `int`（不是 `bool`）、闭集外点名拒绝。"""
    module = _load_module(
        root, "packages/application/run_orchestration/ablation_observations.py", "g114_obs"
    )
    if module is None:
        return [toolbox.verdict("observations-importable", False, "ablation_observations 不可加载")]
    readings_module = _load_module(
        root, "packages/application/run_orchestration/output_readings.py", "g114_readings"
    )
    if readings_module is None:
        return [toolbox.verdict("readings-importable", False, "output_readings 不可加载")]
    content = (
        "plan\n```experiment_design\n"
        '{"experiment_design": {"arms": {"treatment": {"seed": 17}, "control": {"seed": 17}}}}\n'
        "```\nbuilds on mem-x\n"
    )
    observation = module.observation_from(
        readings_module.read_plan_payload({"content": content}, known_memory_ids=("mem-x",)),
        comparison_digest="sha256:aa",
    )
    bogus = readings_module.PlanOutputReadings(
        source_state="something_else",
        design_state="block_absent",
        arms_state="arms_absent",
        arms=(),
        cited_memory_ids=(),
    )
    refused = False
    try:
        module.observation_from(bogus, comparison_digest="sha256:aa")
    except module.AblationObservationError:
        refused = True
    return [
        toolbox.verdict(
            "observation-columns-are-ints-not-bools",
            all(type(observation[key]) is int for key in module.READING_KEYS),
            "四列必须是 `int`（`bool` 是 `int` 的子类，会被消融门拒）",
        ),
        toolbox.verdict(
            "observation-counts-the-cited-memory",
            observation["citation_count"] == 1 and observation["arm_count"] == 2,
            "引用计数必须有分母（首轮真跑曾在缺分母时恒为 0 —— 那条判据不可能判红）",
        ),
        toolbox.verdict(
            "observation-refuses-a-state-outside-the-closed-set",
            refused,
            "闭集外的 `source_state` 必须点名拒绝（不回落成 0）",
        ),
    ]


def _probe_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-05：消融台单相、合约逐字、能力集与来源相集合相等、相 id 是产品瞄准的那个。"""
    import yaml

    probe_path = root / "examples" / "protocols" / "ablation_plan_probe_v1.yaml"
    source_path = root / "examples" / "protocols" / "research_report_chain_v1.yaml"
    if not probe_path.is_file() or not source_path.is_file():
        return [toolbox.verdict("ablation-probe-protocol-present", False, "协议不在树")]
    probe: Any = yaml.safe_load(probe_path.read_text(encoding="utf-8"))
    source: Any = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    phases = {phase["id"]: phase for phase in probe["phases"]}
    source_plan = next(p for p in source["phases"] if p["id"] == "plan")
    shipped_phase = "retrieval"
    ok_phase = set(phases) == {shipped_phase}
    probe_caps = set(phases[shipped_phase].get("required_capabilities") or ())
    source_caps = set(source_plan.get("required_capabilities") or ())
    return [
        toolbox.verdict(
            "ablation-probe-is-one-phase-targeting-the-shipped-phase-id",
            ok_phase,
            f"消融台必须单相且相 id 是出厂检索面瞄准的那个（实得 {sorted(phases)}）",
        ),
        toolbox.verdict(
            "ablation-probe-uses-the-same-contract",
            phases[shipped_phase].get("task_contract") == "research_report_plan",
            "消融台必须原样复用 `research_report_plan`（换合约 ⇒ 读数不是那条链的读数）",
        ),
        toolbox.verdict(
            "ablation-probe-capabilities-match-the-source-phase",
            probe_caps == source_caps and bool(source_caps),
            f"能力集必须与来源相集合相等：探针={sorted(probe_caps)} 来源={sorted(source_caps)}",
        ),
    ]


def _evidence_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-07：六条 run、六条可比键逐字相同、门给出结论、三列位移（含引用数）。"""
    path = root / EVIDENCE
    if not path.is_file():
        return [toolbox.verdict("ablation-evidence-present", False, f"{EVIDENCE} 不在树")]
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    runs = payload.get("runs") or []
    digests = {run.get("comparison_digest") for run in runs}
    gate = payload.get("corpus_gate") or {}
    shifted = payload.get("shifted_columns") or []
    return [
        toolbox.verdict(
            "ablation-evidence-registers-six-runs",
            len(runs) == 6 and [run.get("arm") for run in runs] == ["present", "absent"] * 3,
            f"六条 run 必须按预先声明的 P/A 交替登记，实得 {[r.get('arm') for r in runs]}",
        ),
        toolbox.verdict(
            "ablation-six-runs-share-one-comparison-digest",
            len(digests) == 1 and all(str(d).startswith("sha256:") for d in digests),
            f"六条 run 的可比键必须逐字相同（EC-02 在真实路径上的证据），实得 {len(digests)} 个",
        ),
        toolbox.verdict(
            "ablation-corpus-gate-reaches-a-verdict",
            gate.get("sufficient") is True and gate.get("pairs") == 3,
            f"语料门必须给出结论（k=3），实得 {gate}",
        ),
        toolbox.verdict(
            "ablation-readings-shifted-in-three-columns",
            "citation_count" in shifted and len(shifted) >= 3,
            f"四列至少三列位移且必须含 `citation_count`（首轮缺分母时它恒 0），实得 {shifted}",
        ),
        toolbox.verdict(
            "ablation-evidence-states-its-recompute",
            bool(payload.get("recompute_note")),
            "读数重算必须在证据里点名理由与手段（否则读数与那次真跑的产物关系不可审）",
        ),
    ]


def _ladder_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-08：`下一级` 逐字不动（bar 未升），`当前级` 带描述性读数。"""
    charter = toolbox.text(root, ".cursor/plans/goals/MAINLINE.md")
    row = next((line for line in charter.splitlines() if line.startswith("| 计划 |")), "")
    cells = row.split("|")
    current = cells[2] if len(cells) > 2 else ""
    next_level = cells[4] if len(cells) > 4 else ""
    missing = [marker for marker in NEXT_LEVEL_MARKERS if marker not in next_level]
    return [
        toolbox.verdict(
            "ladder-plan-next-level-unchanged",
            not missing,
            f"『计划』行 `下一级` 缺锚点 {missing} ⇒ bar 被升了（本轮拍板：无位移不升 bar）",
        ),
        toolbox.verdict(
            "ladder-plan-current-level-records-the-reading",
            CURRENT_LEVEL_MARKER in current,
            "『计划』行 `当前级` 必须含本轮的描述性读数",
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 的产品面全量断言（验证器按路径加载并调用它）。"""
    return [
        *_file_verdicts(root, toolbox),
        *_digest_verdicts(root, toolbox),
        *_payload_verdicts(root, toolbox),
        *_observation_verdicts(root, toolbox),
        *_probe_verdicts(root, toolbox),
        *_evidence_verdicts(root, toolbox),
        *_ladder_verdicts(root, toolbox),
    ]
