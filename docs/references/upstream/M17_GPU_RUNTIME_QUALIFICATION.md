# M17 GPU Runtime Qualification Report

状态：**ADOPTED（单卡，个人规模）** · Qualification date：2026-09-02 ·
Owner：root-agent · 计划：PLAN-20260902-028（M17 Remote GPU Execution）

M5R 形状资格记录：实测版本/digest/许可证/边界/拒绝理由/重评条件。
本记录是 WP0 先行门：以下全部实测通过后，M17 业务代码才允许落地。
所有事实来自 2026-09-02 真实容器探测（命令与输出摘录见 §4），
无任何推测值。

## 1. 实际测试硬件事实块（唯一权威）

后续所有 M17 文档（Completion Record / ADR-0029 / MILESTONES）以本块为
准；**不得把型号硬编码进业务逻辑**——业务逻辑只消费运行时探测值。

| 事实 | 实测值（2026-09-02） |
| --- | --- |
| GPU | NVIDIA GeForce RTX 4060 Laptop GPU（Ada, compute capability sm_89） |
| 显存 | 8188 MiB（nvidia-smi total）；桌面会话占用约 2010–2122 MiB，空闲约 5956 MiB |
| 驱动 | 581.80（WDDM 模型，Windows 主机 + WSL2 后端） |
| 驱动支持 CUDA | 13.0 |
| Docker | Server 29.2.1，linux/amd64，WSL2 后端（Ubuntu-24.04 + docker-desktop） |
| nvidia runtime | `nvidia-container-runtime` 已注册（NVIDIA Container Toolkit 在位，无需安装） |
| 容器内 CUDA runtime | 12.8（torch 2.9.1+cu128） |
| 容器内 cuDNN | 9.10.02（91002） |
| 容器内 torch | 2.9.1+cu128 |
| 环境限制（诚实边界） | **GPU 主机 = Control Plane 主机（同一物理机）**。worker 边界仍是 M16 已验证的跨进程 + 跨网络（HTTP worker gateway）untrusted 边界；`physically-remote GPU host` = NOT VERIFIED / DEFERRED |

## 2. 上游组件：pinned GPU 基础镜像

- 镜像：`pytorch/pytorch:2.9.1-cuda12.8-cudnn9-runtime`
- **OCI index digest（pin）**：`sha256:7b324d212a4450795b49edba9949b7cdc72429148a64e974334bfe5774d51385`
- 获取方式：`docker pull`（2026-09-02），`docker image inspect` RepoDigests
  与 pull Digest 一致（上面同一 sha256）
- 选择理由（备选对比）：
  - `pytorch/pytorch:*`（**选定**）：torch+CUDA+cuDNN 预装，单一供应链
    入口；构建期零联网安装；CUDA 12.8 原生支持 sm_89；执行期保持
    `NetworkMode=none`
  - `nvidia/cuda:12.x-runtime` + 构建期 pin 安装 torch：多一个供应链环节
    （pip 拉取 torch wheel），构建不可复现风险更大；未选用
  - CUDA 13.x 镜像：驱动支持（581.80 ≥ 580），但 torch 2.9.1 稳定线以
    cu128 wheel 生态更成熟；未选用
- 许可证（镜像内容物多层）：
  - PyTorch：BSD-3-Clause（https://github.com/pytorch/pytorch/blob/main/LICENSE）
  - CUDA Toolkit / cuDNN runtime 库：NVIDIA 专有运行时再分发条款
    （CUDA Toolkit EULA：https://docs.nvidia.com/cuda/eula/ ）
  - 镜像基座：Ubuntu userland（pytorch 官方 Dockerfile，Ubuntu 22.04）
- 记录位置：`UPSTREAM_COMPONENTS.yaml` `research_os_gpu_base_image` 条目
  （ADOPTED / digest pin / upgrade gate）
- sm_89 支持验证：容器内 `get_device_properties(0)` 返回 `sm_89`，且真实
  GEMM kernel 成功执行（§4 T1）——wheel 必须包含 sm_89 kernel 才能跑通，
  实测排除「架构不支持但 import 成功」的假阳性

## 3. 决策树：ReadonlyRootfs × nvidia hook（WP0 关键风险）

风险假设：nvidia container runtime 的 CDI/legacy hook 会在容器 rootfs
内执行 `ldconfig` 注入驱动库缓存；`ReadonlyRootfs=True` 可能使该写入
失败，导致 CUDA 初始化失败。

实测（T2，§4）：**在完整 M16 安全基线（readonly rootfs + tmpfs /tmp
noexec + network none + CapDrop ALL + no-new-privileges + 非 root
uid 1000 + pids/mem/cpu 限额）下，CUDA 12.8 初始化与真实 GEMM 全部
成功。**

决策树结论：**走「不放开」分支**：

1. GPU profile 完整保留 M16 安全基线（readonly rootfs / network none /
   CapDrop ALL / no-new-privileges / 非 root / tmpfs / pids-mem-cpu 限额 /
   仅 workspace bind mount）；
2. GPU 与 CPU profile 的**唯一** host_config 差异 =
   `DeviceRequests`（nvidia，Count=1，`[["gpu","compute","utility"]]`）；
3. 该「单维度差异」由安全测试套件断言（WP7b：
   `test_gpu_profile_differs_only_in_device_requests`），防止未来有人
   借 GPU 需求放宽其它安全控制；
4. ADR-0029 记录本决策；不批准放开 readonly rootfs。

补充实测：`--user 1000:1000` 下 conda 发行版（/opt/conda）全部
world-readable，非 root 执行 python/CUDA 无障碍——GPU sandbox 镜像
无需 root。

## 4. 实测证据（命令 + 结果摘录）

| # | 实验 | 命令要点 | 结果 |
| --- | --- | --- | --- |
| T1 | GPU 可见性 + 真实计算 | `docker run --rm --gpus all <pin> python gpu_probe.py`（探针含 64×64 FP32 GEMM + synchronize + checksum） | PASS：`cuda_available=true`，`device_count=1`，`sm_89`，`torch 2.9.1+cu128`，`cudnn 91002`，`total_vram_bytes=8585216000`；GEMM checksum=262144.0（=64³，期望值精确） |
| T2 | 完整安全基线 × GPU | T1 + `--read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m,mode=1777 --network none --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --pids-limit 512 --memory 8g --cpus 4` | PASS：与 T1 完全一致的事实输出 → readonly-rootfs 无冲突 |
| T3 | 负向对照（无 GPU） | T2 去掉 `--gpus all` | PASS：`cuda_available=False, device_count=0` → 无 DeviceRequests 时 CUDA 结构性不可见，无静默 GPU |
| T4 | DeviceRequests host_config 形式 | docker-py `create_container(host_config={...全基线..., "DeviceRequests":[{Driver:nvidia,Count:1,Capabilities:[["gpu","compute","utility"]]}]})` | PASS：exit 0，`device_request_cuda=True`，设备名正确 → `DockerExecutionBackend` 使用的形式可用 |

（T3 同时是 WP3c「无静默 CPU fallback」第 2 层防线的环境级证据。）

## 5. 边界（本记录不宣称的事）

- 单机单卡：multi-GPU、NCCL、distributed training、Slurm/PBS/MPI/HPC、
  RDMA/InfiniBand、GPU autoscaling 均 **Deferred**（ADR-0028 清单 +
  M17 计划「明确不实现」节）；本资格记录不支撑任何上述宣称。
- WSL2 限制：NVML 的 per-process 显存与 utilization 读数经 WDDM 中转
  不可靠 → M17 不记录 utilization/energy（WP5 只记框架级可靠量
  `torch.cuda.max_memory_allocated()`）。
- `physically-remote GPU host`：本机 GPU，NOT VERIFIED（诚实条款）。
- 桌面共用显存：同一 GPU 供 Windows 桌面会话使用，空闲显存动态波动；
  实验代码的 VRAM 契约断言按「运行时实测 free 显存」执行，不假设 8 GiB
  全量可用。

## 6. 重评条件（trigger-based）

- Docker Desktop / WSL2 大版本升级后：重跑 T1–T4
- 更换基础镜像 digest（torch/CUDA 版本变化）：重跑 T1–T4 + sm_89 检查
  + WP7b 安全套件
- nvidia-container-toolkit 升级：重跑 T2（readonly-rootfs 冲突回归）
- 驱动升级（尤其跨 CUDA 主版本）：重跑 T1 + T3
- 出现物理远程 GPU 主机时：physically-remote 边界重评（SI-1/PA-1 输入）

## 7. 结论

WP0 先行门 **PASS**：真实 GPU 容器执行在完整安全基线下可用、镜像已按
digest pin、许可证据在位、负向对照成立。允许进入 WP1 业务代码实现。
