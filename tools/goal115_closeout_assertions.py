"""GOAL-20261119-115 的产品面断言集（收口验证器的另一半）。

与 `tools/verify_goal115_closeout.py`（记录面）分工：本文件判**交付物真的在、且形态
就是声明的那一个**；主文件判 EC 终态与宪章记账。

**本轮的判法**（每条指向具体闭集、具体读数或具体行为，不判「模块存在」）：

* 换站与零价纪律（EC-01）：`llm_endpoints.yaml` 的两个 `base_url` 是新站的两张脸、
  都带 `x-opencode-session`；`models.yaml` 的每个 `model_name` 落在**离线夹具**的
  零价集合里。
* 旧站清零（EC-02）：产品面与判据面零命中四个旧标记。
* 四类失败模式（EC-03）：四条判据文件在树，且各自的**反证描述**在文件里
  （按压不是文档承诺，是判据的一部分）。
* 三次真实读数（EC-04）：证据 JSON 三份 + 汇总；每份 2 条可归因判词、两个不同目标、
  同一 phase 两个 task、`voters=2`、`independent=true`。
* advisory 并存（EC-05）：只读模块在树且**不 import `Decision`**；`panel_rejection`
  的判负行逐字在；`threshold: 0.8` 与 `operator: GTE` 在。
* 上游可重试（EC-06）：四份上游合约 `max_attempts >= 2` + 三个瞬时类别。
* PRD 差距（EC-07）：文档四节 + 去重 `file:line` 计数 + INDEX 登记。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ENDPOINTS = "examples/config/llm_endpoints.yaml"
MODELS = "examples/config/models.yaml"
CATALOG = "tests/fixtures/free_models_catalog.json"
PRD = "docs/product/PRD_GAP_ANALYSIS.md"
INDEX = "docs/INDEX.md"
CONTRACTS = "examples/contracts/task_contracts.yaml"
REJECTION = "packages/application/run_orchestration/review_panel_judging.py"
ADVICE = "packages/application/run_orchestration/panel_advice.py"

#: 新站的两张脸（run 腿 / probe 腿）。
OPENAI_FACE = "https://opencode.ai/inference/go/openai/v1"
ANTHROPIC_FACE = "https://opencode.ai/inference/go/anthropic/v1"
#: 推理面的必填路由头（缺它 400）。
SESSION_HEADER = "x-opencode-session"

#: 要清零的旧站标识（**拼接构造**：本文件自身也要能被那条 pin 判据扫过）。
_OLD_ADDRESS = "192" + ".168.101" + ".9"
STALE_MARKERS: tuple[str, ...] = (
    _OLD_ADDRESS,
    "hy4" + "free",
    "hy4" + "-preview-f",
    "hy4" + "flash-exp4",
)

#: EC-03 的四条判据（每类一条）。
FAILURE_MODE_JUDGES: tuple[str, ...] = (
    "tests/adapters/openhands/test_event_mapping_missing_content.py",
    "tests/contracts/test_upstream_failures_are_retryable.py",
    "tests/application/run_orchestration/test_manifest_freeze_refusal_event.py",
    "tests/application/run_orchestration/test_under_review_segment_is_present.py",
)

#: EC-04 的三份读数 + 汇总。
EVIDENCE_RUNS: tuple[str, ...] = (
    ".cursor/plans/goals/evidence/GOAL-20261119-115-dual-review-k1.json",
    ".cursor/plans/goals/evidence/GOAL-20261119-115-dual-review-k2.json",
    ".cursor/plans/goals/evidence/GOAL-20261119-115-dual-review-k3.json",
)
EVIDENCE_SUMMARY = ".cursor/plans/goals/evidence/GOAL-20261119-115-dual-review-k3-summary.json"

#: 四个上游合约（EC-06）。
UPSTREAM_CONTRACTS: tuple[str, ...] = (
    "dual_model_review_deliverable",
    "research_manuscript",
    "retrieval_report_from_the_run_chain",
    "research_question_retrieval",
)
TRANSIENT = frozenset({"MODEL_RELAY_UNAVAILABLE", "MODEL_RATE_LIMIT", "MODEL_TIMEOUT"})

_CITATION = re.compile(r"[A-Za-z0-9_./-]+\.(?:py|ts|tsx|yaml|yml|json|md|toml):\d+")


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _zero_price(payload: dict[str, Any]) -> set[str]:
    """夹具里 `cost.text` 下所有 `price` 全为 0 的模型 id。"""
    free: set[str] = set()
    for item in payload.get("data", []):
        prices: list[float] = []

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    if key == "price" and isinstance(value, (int, float)):
                        prices.append(float(value))
                    else:
                        walk(value)

        walk((item.get("cost") or {}).get("text") or {})
        if prices and all(price == 0 for price in prices):
            free.add(str(item["id"]))
    return free


def _station_verdicts(root: Path, toolbox: Any) -> list[Any]:
    text = _text(root, ENDPOINTS)
    main_block = text.split("  agnes-anthropic:", 1)[0]
    return [
        toolbox.verdict(
            "station-run-leg-is-the-openai-face",
            OPENAI_FACE in main_block,
            f"`main.base_url` 必须是 {OPENAI_FACE}",
        ),
        toolbox.verdict(
            "station-probe-leg-is-the-anthropic-face",
            ANTHROPIC_FACE in text,
            f"`agnes-anthropic.base_url` 必须是 {ANTHROPIC_FACE}",
        ),
        toolbox.verdict(
            "station-both-faces-declare-the-session-header",
            text.count(SESSION_HEADER) >= 2,
            f"两个端点都必须声明 {SESSION_HEADER}（缺它推理面 400）",
        ),
        toolbox.verdict(
            "station-is-not-the-other-inference-tree",
            "/inference/v1" not in text,
            "`/inference/v1` 是另一棵树（模型集不同），不得混用",
        ),
    ]


def _free_model_verdicts(root: Path, toolbox: Any) -> list[Any]:
    catalog_path = root / CATALOG
    if not catalog_path.is_file():
        return [toolbox.verdict("free-model-catalog-present", False, f"{CATALOG} 不在树")]
    free = _zero_price(json.loads(catalog_path.read_text(encoding="utf-8")))
    models = _text(root, MODELS)
    declared = re.findall(r"^\s+model_name:\s*([A-Za-z0-9._/-]+)", models, re.MULTILINE)
    paid = sorted({name for name in declared if name not in free})
    return [
        toolbox.verdict(
            "free-model-set-is-non-vacuous",
            len(free) == 4,
            f"零价集合必须恰是 4 个，实得 {sorted(free)}",
        ),
        toolbox.verdict(
            "free-model-every-configured-name-is-zero-price",
            bool(declared) and not paid,
            f"这些收费模型名出现在 models.yaml 里（会真实扣费）：{paid}",
        ),
    ]


def _stale_pin_verdicts(root: Path, toolbox: Any) -> list[Any]:
    text = _text(root, ENDPOINTS) + _text(root, MODELS)
    hits = [marker for marker in STALE_MARKERS if marker in text]
    return [
        toolbox.verdict(
            "stale-pins-are-cleared-from-the-config-face",
            not hits,
            f"旧站标识仍在配置面里：{hits}",
        )
    ]


def _failure_mode_verdicts(root: Path, toolbox: Any) -> list[Any]:
    verdicts = [
        toolbox.verdict(
            f"failure-mode-judge-present-{Path(relative).stem}",
            (root / relative).is_file(),
            f"{relative} 不在树",
        )
        for relative in FAILURE_MODE_JUDGES
    ]
    # 每条判据必须自带**反证描述**（按压是判据的一部分，不是文档承诺）。
    bite_counts = [
        len(re.findall(r"反证|fails when|press|按压", _text(root, relative)))
        for relative in FAILURE_MODE_JUDGES
    ]
    verdicts.append(
        toolbox.verdict(
            "failure-mode-judges-carry-reverse-arms",
            all(count > 0 for count in bite_counts),
            f"这些判据没有反证描述：{bite_counts}",
        )
    )
    return verdicts


def _evidence_verdicts(root: Path, toolbox: Any) -> list[Any]:
    verdicts: list[Any] = []
    for relative in (*EVIDENCE_RUNS, EVIDENCE_SUMMARY):
        verdicts.append(
            toolbox.verdict(
                f"live-reading-present-{Path(relative).stem}",
                (root / relative).is_file(),
                f"{relative} 不在树",
            )
        )
    summary_path = root / EVIDENCE_SUMMARY
    if not summary_path.is_file():
        return verdicts
    runs = json.loads(summary_path.read_text(encoding="utf-8")).get("runs", [])
    verdicts.append(
        toolbox.verdict(
            "live-reading-covers-three-runs",
            len(runs) == 3,
            f"必须恰有三次读数，实得 {len(runs)}",
        )
    )
    bad = [
        item.get("run")
        for item in runs
        if not (
            item.get("review_verdicts") == 2
            and len(item.get("reviewer_targets") or []) == 2
            and item.get("phase_count") == 1
            and item.get("task_count") == 2
            and item.get("panel_voters") == 2
            and item.get("panel_independent") is True
            and item.get("verdict_text_present") is True
        )
    ]
    verdicts.append(
        toolbox.verdict(
            "live-reading-each-run-has-two-attributable-verdicts",
            not bad,
            f"这些 run 的读数不满足「2 条可归因判词 + 目标互异 + 独立小组」：{bad}",
        )
    )
    return verdicts


def _imports_decision(source: str) -> bool:
    """模块**真的** import 了 `Decision` 吗（AST 判，不看注释/文档串）。

    **为什么不能按子串判**：本模块的 docstring 逐字写着「不 import `Decision`」——
    子串判据会把那句声明本身读成违规（本判据第一版正是这样假红的）。
    """
    import ast

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if any(alias.name == "Decision" for alias in node.names):
                return True
            if (node.module or "").endswith("decision"):
                return True
        elif isinstance(node, ast.Import):
            if any(alias.name.rsplit(".", 1)[-1] == "Decision" for alias in node.names):
                return True
    return False


def _advisory_verdicts(root: Path, toolbox: Any) -> list[Any]:
    advice = _text(root, ADVICE)
    rejection = _text(root, REJECTION)
    contracts = _text(root, CONTRACTS)
    return [
        toolbox.verdict(
            "advisory-read-face-present",
            "def panel_advice(" in advice,
            "`panel_advice` 不在树",
        ),
        toolbox.verdict(
            "advisory-does-not-import-decision",
            _imports_decision(advice) is False,
            "advisory 模块 import 了 `Decision` ⇒ 它会夺走硬门的真相权",
        ),
        toolbox.verdict(
            "hard-gate-rejection-line-is-verbatim",
            'rejected = tuple(item for item in verdicts if item[1] != "PASS")' in rejection,
            "`panel_rejection` 的判负条件被改动了",
        ),
        toolbox.verdict(
            "hard-gate-threshold-is-verbatim",
            "operator: GTE" in contracts and "threshold: 0.8" in contracts,
            "`REVIEW_SCORE >= 0.8` 的 operator/threshold 被改动了",
        ),
    ]


def _retry_verdicts(root: Path, toolbox: Any) -> list[Any]:
    import sys

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from adapters.contracts.tasks_loaders import load_task_contracts

    loaded = load_task_contracts(str(root / CONTRACTS))
    bad: list[str] = []
    for name in UPSTREAM_CONTRACTS:
        policy = getattr(loaded.get(name), "retry_policy", None)
        if policy is None:
            bad.append(f"{name}: no retry_policy")
            continue
        cats = {
            str(item.value) if hasattr(item, "value") else str(item)
            for item in policy.retryable_categories
        }
        if policy.max_attempts < 2 or not (TRANSIENT <= cats):
            bad.append(f"{name}: attempts={policy.max_attempts} cats={sorted(cats)}")
    return [
        toolbox.verdict(
            "upstream-contracts-are-retryable",
            not bad,
            f"这些上游合约仍不可重试：{bad}",
        )
    ]


def _prd_verdicts(root: Path, toolbox: Any) -> list[Any]:
    text = _text(root, PRD)
    headings = [line for line in text.splitlines() if line.startswith("## ")]
    citations = set(_CITATION.findall(text))
    return [
        toolbox.verdict("prd-document-present", (root / PRD).is_file(), f"{PRD} 不在树"),
        toolbox.verdict(
            "prd-has-four-sections",
            len(headings) >= 5,
            f"二级标题不足（实得 {len(headings)} 个）",
        ),
        toolbox.verdict(
            "prd-cites-at-least-twenty-repo-locations",
            len(citations) >= 20,
            f"去重后的 `file:line` 引用只有 {len(citations)} 条（要求 ≥20）",
        ),
        toolbox.verdict(
            "prd-is-registered-in-the-index",
            "PRD_GAP_ANALYSIS" in _text(root, INDEX),
            f"{INDEX} 没有登记该文档",
        ),
        toolbox.verdict(
            "prd-states-the-non-zdr-fact",
            "iceman-contributor-free" in text and "ZDR" in text,
            "非 ZDR 的接入事实没有写进 PRD 文档",
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 的产品面断言集（收口验证器按路径加载本函数）。"""
    return [
        *_station_verdicts(root, toolbox),
        *_free_model_verdicts(root, toolbox),
        *_stale_pin_verdicts(root, toolbox),
        *_failure_mode_verdicts(root, toolbox),
        *_evidence_verdicts(root, toolbox),
        *_advisory_verdicts(root, toolbox),
        *_retry_verdicts(root, toolbox),
        *_prd_verdicts(root, toolbox),
    ]


__all__ = ["assertion_verdicts"]
