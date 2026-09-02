"""M17 WP3c 静态检查门禁：GPU 实验代码禁止 cuda-else-cpu 降级模式。

无静默 CPU fallback 第 3 层的源码面防线：扫描 GPU 实验脚本，禁止出现
「设备可用就用 cuda 否则用 cpu」的条件选择模式（含 `.to("cpu")` 作为主
计算设备的回退）。CPU 计时对照必须是显式独立分支（cpu_control_*），不得
与主计算设备选择混用同一条件表达式。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_GPU_EXPERIMENTS = tuple((_REPO_ROOT / "examples" / "experiments").glob("m17_*gpu*.py"))

# 禁止模式：主计算设备由「cuda 可用否则 cpu」条件表达式决定。
_FORBIDDEN_PATTERNS = (
    re.compile(r"=\s*torch\.device\(\s*[\"']cuda[\"'].*\bif\b.*\belse\b.*[\"']cpu[\"']"),
    re.compile(r"=\s*[\"']cuda[\"']\s+if\s+.*\s+else\s+[\"']cpu[\"']"),
    re.compile(r"\.to\(\s*[\"']cuda[\"']\s+if\b.*\belse\b.*[\"']cpu[\"']\s*\)"),
    re.compile(r"device\s*=\s*.*is_available\(\).*else.*cpu", re.DOTALL),
)


def test_gpu_experiment_scripts_exist() -> None:
    """门禁不得空转：至少有一个 GPU 实验脚本被扫描。"""
    assert _GPU_EXPERIMENTS, "expected at least one examples/experiments/m17_*gpu*.py"


@pytest.mark.parametrize("script", _GPU_EXPERIMENTS, ids=lambda p: p.name)
def test_no_cuda_else_cpu_fallback_pattern(script: Path) -> None:
    source = script.read_text(encoding="utf-8")
    for pattern in _FORBIDDEN_PATTERNS:
        assert pattern.search(source) is None, (
            f"{script.name} contains a forbidden cuda-else-cpu fallback "
            f"pattern: {pattern.pattern!r}"
        )


@pytest.mark.parametrize("script", _GPU_EXPERIMENTS, ids=lambda p: p.name)
def test_gpu_experiment_asserts_device_before_compute(script: Path) -> None:
    """主计算设备必须经契约断言获得（_assert_gpu_contract），非裸 is_available。"""
    source = script.read_text(encoding="utf-8")
    assert "_assert_gpu_contract" in source
    assert 'device="cuda:0"' in source or 'torch.device("cuda:0")' in source
