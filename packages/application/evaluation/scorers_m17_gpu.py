"""M17 GPU 证据层 scorer（确定性、纯函数、无副作用）。

`gpu_compute_device`：实验结果必须自报 `compute_device.kind == "cuda"`，
且（若 expected 提供 device_name）设备身份与 worker 注册观测一致。这是无静默
CPU fallback 的第 4 层（证据/评测面）判别器——声明 GPU 实验却记录 CPU/缺失
设备即 FAIL，复用 M11 对抗测试形状。
"""

from __future__ import annotations

from typing import Mapping

from packages.application.evaluation.scorer_types import (
    ScorerContext,
    ScorerFn,
    make_finding,
)
from packages.domain.eval_result import EvalFindingStatus, ScorerFinding

_SCORER_ID = "gpu_compute_device"


def _actual_device(ctx: ScorerContext) -> Mapping[str, object] | None:
    actual = ctx.input.actual
    if not isinstance(actual, Mapping):
        return None
    device = actual.get("compute_device")
    return device if isinstance(device, Mapping) else None


def _gpu_compute_device(ctx: ScorerContext) -> ScorerFinding:
    device = _actual_device(ctx)
    if device is None:
        return make_finding(
            _SCORER_ID,
            ctx,
            EvalFindingStatus.FAIL,
            "experiment result missing compute_device (no-silent-CPU-fallback)",
        )
    kind = device.get("kind")
    if kind != "cuda":
        return make_finding(
            _SCORER_ID,
            ctx,
            EvalFindingStatus.FAIL,
            f"compute_device.kind={kind!r} is not 'cuda' (no-silent-CPU-fallback)",
        )
    expected = ctx.case.expected
    if isinstance(expected, Mapping):
        want_name = expected.get("device_name")
        if isinstance(want_name, str) and device.get("name") != want_name:
            return make_finding(
                _SCORER_ID,
                ctx,
                EvalFindingStatus.FAIL,
                f"compute_device.name={device.get('name')!r} != registered {want_name!r}",
            )
    return make_finding(
        _SCORER_ID,
        ctx,
        EvalFindingStatus.PASS,
        f"compute_device verified on cuda: {device.get('name')!r}",
        value=str(device.get("name")),
    )


def gpu_compute_device_scorer() -> ScorerFn:
    """工厂绑定（与 m12 truth scorer 同形状）。"""
    return _gpu_compute_device
