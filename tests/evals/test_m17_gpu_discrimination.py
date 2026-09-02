"""M17 GPU 证据层判别器单测（PART B W-03）。

`gpu_compute_device`（scorers_m17_gpu.py）的四个判别路径必须显式固定：
1. expected.device_name 匹配 → PASS；
2. expected.device_name 不匹配 → FAIL（该分支此前无任何测试覆盖）；
3. expected={}（m17_gpu_v1.yaml 数据集现状）时仅要求 kind=cuda → PASS；
4. compute_device 缺失 / kind 不为 cuda → FAIL。

设备身份绑定不写进评测数据集（保持硬件无关，见 ADR-0029 诚实边界），
真正的设备身份绑定由 ReproducibilityAudit 的 GPU fingerprint 承担
（tests/adapters/execution/test_gpu_reproduction_e2e.py 已锁定）。
"""

from __future__ import annotations

from packages.application.evaluation.scorer_types import (
    V1,
    ScorerContext,
    ScorerInput,
)
from packages.application.evaluation.scorers import resolve_scorer
from packages.domain.core import Version
from packages.domain.eval_result import EvalFindingStatus, ScorerFinding
from packages.domain.eval_spec import EvalCase, EvalScope

_SCORER_ID = "gpu_compute_device"
_DEVICE_NAME = "NVIDIA GeForce RTX 4060 Laptop GPU"


def _case(case_id: str, expected: object) -> EvalCase:
    return EvalCase(
        id=case_id,
        version=Version("1.0.0"),
        scope=EvalScope.UNIT,
        input_ref=f"input://{case_id}",
        expected=expected,
        scorer_refs=(),
    )


def _run(case: EvalCase, actual: object) -> ScorerFinding:
    fn = resolve_scorer(_SCORER_ID, V1.text)
    return fn(
        ScorerContext(
            case=case,
            input=ScorerInput(actual=actual),
            predicates={},
        )
    )


def _cuda_result(name: str = _DEVICE_NAME) -> dict[str, object]:
    return {
        "status": "SUCCEEDED",
        "metrics": {"baseline_accuracy": 0.999, "candidate_accuracy": 0.999},
        "compute_device": {
            "kind": "cuda",
            "name": name,
            "total_vram_bytes": 8585216000,
            "cuda_runtime_version": "12.8",
        },
    }


def _assert_status(finding: ScorerFinding, expected: EvalFindingStatus) -> None:
    assert finding.status is expected, finding.detail


def test_expected_device_name_matching_passes() -> None:
    case = _case("match", {"device_name": _DEVICE_NAME})
    _assert_status(_run(case, _cuda_result()), EvalFindingStatus.PASS)


def test_expected_device_name_mismatch_fails() -> None:
    """设备名称绑定分支（scorers_m17_gpu.py 的 expected.name != actual.name）：
    声明的 GPU 与注册观测（expected）不一致必须 FAIL——独立复审中该分支
    无任何测试覆盖（数据集 expected={}，case 只走 kind 判别）。"""
    case = _case("mismatch", {"device_name": _DEVICE_NAME})
    finding = _run(case, _cuda_result(name="NVIDIA GeForce RTX 3060"))
    _assert_status(finding, EvalFindingStatus.FAIL)
    assert "!= registered" in finding.detail


def test_empty_expected_requires_only_cuda_kind() -> None:
    """数据集现状（m17_gpu_v1.yaml gpu_compute_device_001 expected: {}）：只做
    kind=cuda 判别，不要求设备名（硬件无关数据集）。"""
    case = _case("empty", {})
    _assert_status(_run(case, _cuda_result()), EvalFindingStatus.PASS)


def test_missing_compute_device_fails() -> None:
    case = _case("missing", {})
    result = _cuda_result()
    del result["compute_device"]
    _assert_status(_run(case, result), EvalFindingStatus.FAIL)


def test_cpu_kind_fails() -> None:
    case = _case("cpu", {})
    result = _cuda_result()
    result["compute_device"] = {"kind": "cpu", "name": "AMD Ryzen"}
    _assert_status(_run(case, result), EvalFindingStatus.FAIL)


def test_unknown_kind_fails_closed() -> None:
    case = _case("unknown", {})
    result = _cuda_result()
    result["compute_device"] = {"kind": "mps", "name": "Apple"}
    _assert_status(_run(case, result), EvalFindingStatus.FAIL)
