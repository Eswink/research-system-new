"""GOAL-20261117-114 EC-07 的 live 支持件：**k=3 两臂配对消融**的驱动与取证。

**为什么单列**：判据文件贴着规模门（450 行 / 函数 50 行），而「两臂 × k 次 + 观测汇总 +
证据落盘」是可独立读的一段装配。

**与离线判据的分工**：`test_paired_ablation_offline_arms.py` 判**读数管线**（受控输出）；
本模块驱动**真实模型**，判的是「两臂的输出读数分布」。两者不互相顶替。

**四条硬纪律**（每条都对准一个会假绿/假红的形态）：

1. **臂顺序预先声明 P/A 交替**（`ARM_SEQUENCE`）：不许「先跑一臂看结果再决定另一臂跑几次」，
   也不许因为某次失败而补跑到「够 3 对」为止 —— 失败如实登记。
2. **每 run 一个全新的库**：`absent` 臂必须是**零行记忆**（`deactivate` 不被
   `build_prior_knowledge` 认，见 `prior_knowledge.py` 只过滤 `expires_at`）⇒ 换库是唯一
   干净的杠杆。
3. **读面取证**：状态 / 可比键 / 计划正文 / `RETRIEVED` 来源全部经既有 HTTP 读面，
   不读内部对象。
4. **不归一化掉失败**：读数只从 `SUCCEEDED` 的 run 里取；一条失败 ⇒ 该 pair 作废并在
   证据 JSON 里点名（不重试到绿）。
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

PROTOCOL = "ablation_plan_probe_v1.yaml"
#: 立题格的合约（会话输出/受控注入都按它取）。
PLAN_CONTRACT = "research_report_plan"
#: 臂的**预先声明**顺序：present / absent 交替（3 对；任何一次失败不补跑）。
ARM_SEQUENCE: tuple[str, ...] = ("present", "absent", "present", "absent", "present", "absent")
#: 预置的前序知识（PROJECT 档 = 跨 run 才读得到）。
MEMORY_ID = "mem-ablation-live-prior"
MEMORY_PROVENANCE = "run:ablation-prior:claim:result"
MEMORY_CONTENT = (
    "Prior round lesson: duplicate_pairs must be pinned before comparing arms, because "
    "unpinned duplicate generation dominates the measured variance."
)
EVIDENCE = ".cursor/plans/goals/evidence/GOAL-20261117-114-ablation-k3.json"


@dataclass(frozen=True, slots=True)
class ArmRun:
    """一次 run 的读数（**全部经读面**；观测缺席时 `observation` 为 `None`）。"""

    index: int
    arm: str
    run_id: str
    state: str
    comparison_digest: str
    retrieved_sources: int
    seconds: float
    observation: dict[str, Any] | None

    def as_json(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "arm": self.arm,
            "run_id": self.run_id,
            "state": self.state,
            "comparison_digest": self.comparison_digest,
            "retrieved_sources": self.retrieved_sources,
            "seconds": round(self.seconds, 1),
            "observation": self.observation,
        }


def load_report_tool() -> ModuleType:
    """按路径加载 `tools/ablation_report.py`（`tools/` 不是包，静态 import 会撞 mypy）。"""
    import importlib.util
    import sys

    root = Path(__file__).resolve().parents[2]
    module = sys.modules.get("goal114_ablation_report")
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(
        "goal114_ablation_report", root / "tools" / "ablation_report.py"
    )
    assert spec is not None and spec.loader is not None
    loaded = importlib.util.module_from_spec(spec)
    sys.modules["goal114_ablation_report"] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def build_raw_pairs(runs: list[ArmRun]) -> dict[str, Any]:
    """按**声明顺序**把相邻的 present/absent 配成对（失败的一侧不参与配对）。

    配对键的相等由 `tools/ablation_report._load` 自己判（它会对不相等的两臂**点名拒绝**）；
    本函数只负责形状：`{slot, pairs: [{label, present, absent}]}`。
    """
    pairs: list[dict[str, Any]] = []
    pending: ArmRun | None = None
    for run in runs:
        if run.observation is None:
            pending = None
            continue
        if pending is None:
            pending = run
            continue
        if pending.arm == "present" and run.arm == "absent":
            pairs.append({
                "label": f"pair{pending.index}-{run.index}",
                "present": pending.observation,
                "absent": run.observation,
            })
        pending = None
    return {"slot": "prior_knowledge", "pairs": pairs}


def write_evidence(runs: list[ArmRun], *, report: Any, rendered: str, refused: str | None) -> Path:
    """证据 JSON（原始观测 + 门 + 位移 + 每个 run 的可比键与墙钟）。"""
    path = Path(EVIDENCE)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "goal": "GOAL-20261117-114",
        "protocol": PROTOCOL,
        "arm_sequence": list(ARM_SEQUENCE),
        "memory": {"id": MEMORY_ID, "provenance": MEMORY_PROVENANCE, "tier": "PROJECT"},
        "runs": [run.as_json() for run in runs],
        "corpus_gate": {
            "sufficient": bool(report.gate.sufficient),
            "pairs": int(report.gate.pairs),
            "missing": list(report.gate.missing),
        },
        "column_shifts": [
            {
                "field": column.field,
                "present_mean": column.present_mean,
                "absent_mean": column.absent_mean,
                "shift": column.shift,
            }
            for column in report.shifts
        ],
        "shifted_columns": list(report.shifted_columns),
        "rendered_report": rendered,
        "refused": refused,
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "host_pid": os.getpid(),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
