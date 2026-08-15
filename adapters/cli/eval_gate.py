"""M11 CI 确定性评测门禁 CLI（entry adapter；离线、无 LLM、无网络）。

用法：
    uv run --frozen --no-sync python -B -m adapters.cli.eval_gate

行为：
- 加载 examples/eval/datasets/ 下的 unit/integration 评测集；
- 用确定性 scorer 与冻结输入运行评测（OFFLINE_FAKE 语义）；
- 产出 EvalScore 报告（UTF-8、canonical JSON）到 artifacts/eval/；
- exit code：PASS/PASS_WITH_WARNINGS → 0；REVISE/BLOCK → 1；
- 不启动真实 LLM Reviewer（真实 LLM 显式手动运行，非默认 CI 依赖）。
"""

from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone
from decimal import Decimal
from typing import Mapping

from adapters.contracts.eval_loaders import load_eval_dataset
from adapters.contracts.eval_report_io import write_report
from packages.application.evaluation.runner import (
    RunnerOutcome,
    RunRequest,
    run_evaluation,
)
from packages.domain.core import Version
from packages.domain.enums import QualityGateVerdict
from packages.domain.eval_gate import GateConfig

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_DATASETS = (
    "examples/eval/datasets/unit_v1.yaml",
    "examples/eval/datasets/integration_v1.yaml",
)
_INPUTS: dict[str, dict[str, object]] = {
    "unit": {
        "input://unit/exact_001": {"answer": 42},
        "input://unit/fields_001": {"answer": 42, "meta": {"confidence": "high"}},
        "input://unit/numeric_001": "100",
        "input://unit/schema_001": {"conclusion": "sound"},
        "input://unit/digest_001": "M11-canary-payload",
    },
    "integration": {
        "input://integration/evidence_001": {},
        "input://integration/invariant_001": [3, 2, 1],
    },
}
_EVIDENCE: dict[str, dict[str, dict[str, str]]] = {
    "integration": {
        "input://integration/evidence_001": {
            "s1": "identity-a",
            "s2": "identity-b",
        },
    },
}
_EXIT_OK = {QualityGateVerdict.PASS, QualityGateVerdict.PASS_WITH_WARNINGS}


def _sorted_desc(value: object, params: Mapping[str, object]) -> bool:
    del params
    if not isinstance(value, list) or len(value) < 2:
        return True
    return all(value[index] >= value[index + 1] for index in range(len(value) - 1))


def _system_version() -> str:
    return (_ROOT / "VERSION").read_text(encoding="utf-8").strip()


def _gate_config() -> GateConfig:
    return GateConfig(
        id="m11-ci-gate",
        version=Version("1.0.0"),
        min_pass_ratio=Decimal("0"),
    )


def _run_dataset(relative_path: str, key: str) -> RunnerOutcome:
    dataset = load_eval_dataset(relative_path)
    outcome = run_evaluation(
        RunRequest(
            dataset=dataset,
            config=_gate_config(),
            mode="OFFLINE_FAKE",
            system_version=_system_version(),
            inputs=_INPUTS[key],
            evidence=_EVIDENCE.get(key, {}),
            predicates={"sorted_desc": _sorted_desc},
            report_id=f"eval:{dataset.id}:ci",
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
    )
    return outcome


def _combined_verdict(verdicts: list[QualityGateVerdict]) -> QualityGateVerdict:
    if any(item is QualityGateVerdict.BLOCK for item in verdicts):
        return QualityGateVerdict.BLOCK
    if any(item is QualityGateVerdict.REVISE for item in verdicts):
        return QualityGateVerdict.REVISE
    if any(item is QualityGateVerdict.PASS_WITH_WARNINGS for item in verdicts):
        return QualityGateVerdict.PASS_WITH_WARNINGS
    return QualityGateVerdict.PASS


def main() -> int:
    artifacts = _ROOT / "artifacts" / "eval"
    artifacts.mkdir(parents=True, exist_ok=True)
    verdicts: list[QualityGateVerdict] = []
    for relative_path in _DATASETS:
        key = relative_path.rsplit("/", 1)[-1].removesuffix(".yaml").removesuffix("_v1")
        outcome = _run_dataset(relative_path, key)
        report = outcome.report
        write_report(artifacts / f"{report.frozen_conditions.dataset_id}-report.json", report)
        verdicts.append(report.gate_verdict)
        print(
            f"{relative_path}: verdict={report.gate_verdict.value} "
            f"digest={report.digest()} missing={list(outcome.missing_inputs)}"
        )
    final = _combined_verdict(verdicts)
    (artifacts / "summary.json").write_text(
        json.dumps(
            {
                "datasets": list(_DATASETS),
                "verdicts": [item.value for item in verdicts],
                "final_verdict": final.value,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"M11 CI eval gate: {final.value}")
    return 0 if final in _EXIT_OK else 1


if __name__ == "__main__":
    raise SystemExit(main())
