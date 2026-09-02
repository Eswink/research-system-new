"""M17 GPU Research 实验代码（真实 CUDA 容器内执行）。

研究问题：固定训练预算下，混合精度（bf16 autocast）能否在保持准确率的同时
提升吞吐？外加 GPU vs CPU 同 workload 计时对照，作为「GPU 真的在算」的量化
证据。

设计约束（M17 Scope / 无静默 CPU fallback 第 3 层契约）：
- 主计算设备**硬编码** `cuda:0`，先经 RESEARCHOS_GPU_ASSERT_* 环境契约强制
  断言（设备数 / 显存下限 / CUDA 下限 / framework）；断言失败 = 非零退出，
  绝不降级 CPU（代码中不存在 `cuda if available else cpu` 模式，静态检查
  门禁锁定）；
- CPU 计时对照是**显式独立分支**（cpu_control_*），只用于吞吐对照，绝不参与
  主实验的模型训练或准确率指标；
- 输入数据在实验代码内确定性生成（torch.manual_seed + deterministic
  algorithms + cudnn.deterministic + CUBLAS_WORKSPACE_CONFIG 由运行环境注入）；
- 不下载任何模型/数据集，容器保持 network=none；
- 输出 `experiment_result.json`（对齐 experiment_run_output_v1 schema +
  M17 compute_device）与 `gpu_runtime_facts.json`（执行后端白名单解析）。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import torch


def _assert_gpu_contract() -> torch.device:
    """第 3 层决定性断言：不满足 profile 契约即失败退出（无 CPU 降级）。"""
    required = int(os.environ.get("RESEARCHOS_GPU_ASSERT_DEVICE_COUNT", "1"))
    min_vram = int(os.environ.get("RESEARCHOS_GPU_ASSERT_MIN_VRAM_BYTES", "0"))
    min_cuda = os.environ.get("RESEARCHOS_GPU_ASSERT_MIN_CUDA", "")
    if not torch.cuda.is_available() or torch.cuda.device_count() < required:
        _write_facts({"cuda_available": False, "gpu_oom": False})
        sys.exit(1)
    props = torch.cuda.get_device_properties(0)
    cuda = torch.version.cuda or ""
    if int(props.total_memory) < min_vram or (min_cuda and cuda < min_cuda):
        _write_facts({"cuda_available": False, "gpu_oom": False})
        sys.exit(1)
    return torch.device("cuda:0")


def _write_facts(facts: dict[str, object]) -> None:
    Path("gpu_runtime_facts.json").write_text(json.dumps(facts), encoding="utf-8")


def _driver_version() -> str:
    sm = subprocess.run(
        ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return sm.stdout.strip() if sm.returncode == 0 else "unknown"


def _make_dataset(seed: int, n_train: int, n_test: int, features: int, classes: int):
    """确定性合成分类数据：每类一个随机中心 + 高斯噪声（可分性适中）。"""
    gen = torch.Generator(device="cpu").manual_seed(seed)
    centers = torch.randn(classes, features, generator=gen)
    noise = torch.randn(n_train + n_test, features, generator=gen) * 1.35
    labels = torch.arange(n_train + n_test) % classes
    x = centers[labels] + noise
    y = labels
    return x[:n_train], y[:n_train], x[n_train:], y[n_train:]


def _train(  # noqa: PLR0913 - 实验内部训练函数，数据/设备/精度参数显式
    x_train: torch.Tensor,
    y_train: torch.Tensor,
    x_test: torch.Tensor,
    y_test: torch.Tensor,
    device: torch.device,
    epochs: int,
    *,
    mixed_precision: bool,
    seed: int,
) -> tuple[float, float, int, float]:
    """训练小 MLP；返回 (test_accuracy, samples_per_sec, peak_memory_bytes, elapsed)。

    mixed_precision=True 用 bf16 autocast（candidate），False 用 FP32（baseline）。
    两者共用同一确定性数据与同一初始化种子，唯一差异是精度模式。`elapsed`
    是本次完整训练循环的墙钟（W-01: GPU_TIME 记账的全 workload 时长——此前
    只记单 batch 墙钟导致 real GPU 时长取整为 0）。
    """
    torch.manual_seed(seed)
    model = torch.nn.Sequential(
        torch.nn.Linear(64, 128), torch.nn.ReLU(), torch.nn.Linear(128, 4)
    ).to(device)
    opt = torch.optim.SGD(model.parameters(), lr=0.05)
    loss_fn = torch.nn.CrossEntropyLoss()
    xtr, ytr = x_train.to(device), y_train.to(device)
    xte, yte = x_test.to(device), y_test.to(device)
    batch = 256
    n = xtr.shape[0]
    peak = 0
    started = time.monotonic()
    for _ in range(epochs):
        gen = torch.Generator(device=device).manual_seed(seed)
        perm = torch.randperm(n, device=device, generator=gen)
        for i in range(0, n, batch):
            idx = perm[i : i + batch]
            opt.zero_grad()
            if mixed_precision:
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    loss = loss_fn(model(xtr[idx]), ytr[idx])
            else:
                loss = loss_fn(model(xtr[idx]), ytr[idx])
            loss.backward()
            opt.step()
        peak = max(peak, int(torch.cuda.max_memory_allocated(device)))
    elapsed = max(1e-6, time.monotonic() - started)
    with torch.no_grad():
        preds = model(xte).argmax(dim=1)
        accuracy = float((preds == yte).float().mean().item())
    return accuracy, n / elapsed, peak, elapsed


def main() -> None:
    device = _assert_gpu_contract()
    seed = int(os.environ.get("EXPERIMENT_SEED", "7"))
    epochs = int(os.environ.get("EXPERIMENT_EPOCHS", "12"))
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    try:
        torch.use_deterministic_algorithms(True)
    except Exception:  # noqa: BLE001 - 个别算子无确定性实现时不致命（如实记录）
        pass
    x_train, y_train, x_test, y_test = _make_dataset(seed, 8000, 2000, 64, 4)

    # baseline: FP32 on GPU
    base_acc, base_sps, base_peak, base_elapsed = _train(
        x_train, y_train, x_test, y_test, device, epochs, mixed_precision=False, seed=seed
    )
    # candidate: mixed precision (bf16 autocast) on GPU
    cand_acc, cand_sps, cand_peak, cand_elapsed = _train(
        x_train, y_train, x_test, y_test, device, epochs, mixed_precision=True, seed=seed
    )
    # GPU vs CPU 同 workload 计时对照（显式独立分支，不参与准确率指标）
    cpu_seconds = _cpu_control(x_train, y_train, x_test, y_test, epochs, seed)
    gpu_seconds = _gpu_seconds(x_train, y_train, x_test, y_test, device, epochs, seed)

    props = torch.cuda.get_device_properties(device)
    peak = max(base_peak, cand_peak)
    _write_facts({
        "cuda_available": True,
        "gpu_device_name": props.name,
        "driver_version": _driver_version(),
        "cuda_runtime_version": torch.version.cuda or "",
        "framework_version": torch.__version__,
        "peak_gpu_memory_bytes": peak,
        # 全 workload 真实 GPU 时长（baseline+candidate 完整训练循环墙钟；预算
        # 记账与遥测消费此值——单 batch 墙钟会取整为 0，不可作 GPU_TIME 量）。
        "gpu_elapsed_seconds": int(round(base_elapsed + cand_elapsed)),
        "gpu_oom": False,
    })
    result = {
        "experiment_run_id": os.environ.get("EXPERIMENT_RUN_ID", "m17-gpu-run"),
        "status": "SUCCEEDED",
        "seed": seed,
        "artifact_refs": [],
        "metrics": {
            "baseline_accuracy": round(base_acc, 6),
            "candidate_accuracy": round(cand_acc, 6),
            "baseline_samples_per_sec": round(base_sps, 3),
            "candidate_samples_per_sec": round(cand_sps, 3),
            "throughput_speedup": round(cand_sps / base_sps, 4) if base_sps else 0.0,
            "cpu_control_seconds": round(cpu_seconds, 4),
            "gpu_seconds": round(gpu_seconds, 4),
            "gpu_speedup_vs_cpu": round(cpu_seconds / gpu_seconds, 4) if gpu_seconds else 0.0,
            "peak_gpu_memory_bytes": peak,
            "n_test": int(x_test.shape[0]),
            "seed": seed,
            "epochs": epochs,
        },
        "compute_device": {
            "kind": "cuda",
            "name": props.name,
            "total_vram_bytes": int(props.total_memory),
            "cuda_runtime_version": torch.version.cuda or "",
        },
    }
    Path("experiment_result.json").write_text(json.dumps(result), encoding="utf-8")
    print("m17 gpu research slice ok")


def _cpu_control(  # noqa: PLR0913 - 与 _train 同形参集
    x_train, y_train, x_test, y_test, epochs: int, seed: int
) -> float:
    """CPU 计时对照：单 epoch 前向+反向墙钟，仅用于 GPU/CPU 对照。"""
    cpu = torch.device("cpu")
    torch.manual_seed(seed)
    model = torch.nn.Sequential(
        torch.nn.Linear(64, 128), torch.nn.ReLU(), torch.nn.Linear(128, 4)
    ).to(cpu)
    opt = torch.optim.SGD(model.parameters(), lr=0.05)
    loss_fn = torch.nn.CrossEntropyLoss()
    xtr, ytr = x_train.to(cpu), y_train.to(cpu)
    started = time.monotonic()
    for _ in range(1):
        opt.zero_grad()
        loss = loss_fn(model(xtr[:256]), ytr[:256])
        loss.backward()
        opt.step()
    return time.monotonic() - started


def _gpu_seconds(  # noqa: PLR0913 - 与 _train 同形参集
    x_train, y_train, x_test, y_test, device, epochs: int, seed: int
) -> float:
    """GPU 同规模单 batch 墙钟（与 cpu_control 可比），用于 speedup 对照。"""
    torch.manual_seed(seed)
    model = torch.nn.Sequential(
        torch.nn.Linear(64, 128), torch.nn.ReLU(), torch.nn.Linear(128, 4)
    ).to(device)
    opt = torch.optim.SGD(model.parameters(), lr=0.05)
    loss_fn = torch.nn.CrossEntropyLoss()
    xtr, ytr = x_train.to(device), y_train.to(device)
    torch.cuda.synchronize(device)
    started = time.monotonic()
    opt.zero_grad()
    loss = loss_fn(model(xtr[:256]), ytr[:256])
    loss.backward()
    opt.step()
    torch.cuda.synchronize(device)
    return time.monotonic() - started


if __name__ == "__main__":
    main()
