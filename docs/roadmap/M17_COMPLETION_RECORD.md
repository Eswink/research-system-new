# M17 Completion Record — Remote GPU Execution / Personal Scale Baseline

- Date: 2026-09-02
- Plan: `.cursor/plans/m17_remote_gpu_execution_7fa9785b.plan.md`
- Task record: `.cursor/plans/tasks/PLAN-20260902-028-m17-remote-gpu-execution.md`
- ADR: `docs/adr/ADR-0029-gpu-execution-boundary.md`
- Qualification: `docs/references/upstream/M17_GPU_RUNTIME_QUALIFICATION.md`
- Scope source: `docs/roadmap/MILESTONES.md` M17（经 ADR-0028 RM-P2 收缩为
  真实单卡 GPU Worker 上的完整 GPU Research Slice）

## 实际测试硬件（唯一权威，实测 2026-09-02）

- GPU：NVIDIA GeForce RTX 4060 Laptop GPU（Ada，sm_89），8188 MiB 总显存
- Driver 581.80（WDDM），驱动上报 CUDA 13.0
- Docker Desktop 29.2.1，linux/amd64，WSL2 后端；`nvidia` runtime 已注册
- 容器内：torch 2.9.1+cu128 / CUDA 12.8 / cuDNN 9.10.02
- 基础镜像 pin：`pytorch/pytorch:2.9.1-cuda12.8-cudnn9-runtime`
  @ `sha256:7b324d212a4450795b49edba9949b7cdc72429148a64e974334bfe5774d51385`
- **环境限制（诚实边界）**：GPU 主机 = Control Plane 主机（同一物理机）。
  worker 边界仍是 M16 跨进程 + 跨网络 HTTP gateway untrusted 平面。

## 强制诚实判定

| 能力 | 判定 |
|---|---|
| real GPU execution（真实设备/CUDA/计算） | **VERIFIED** |
| process/network-remote worker boundary | **VERIFIED**（复用 M16 gateway/lease/fencing） |
| physically-remote GPU host（GPU 主机 ≠ Control Plane 主机） | **NOT VERIFIED / DEFERRED** |

任何文档不得把本机 GPU 描述为「远程服务器 GPU」。

## Exit Criteria → Evidence Map（逐条）

| # | Exit Criterion | 证据（代码 / 测试 / 运行） | 结果 |
|---|---|---|---|
| 1 | GPU runtime qualification 先行门 | `M17_GPU_RUNTIME_QUALIFICATION.md`（T1–T4 实测：--gpus 可见 / 完整安全基线兼容 / 负向对照 / DeviceRequests 形式）；`UPSTREAM_COMPONENTS.yaml` `research_os_gpu_base_image` digest pin | PASS |
| 2 | readonly-rootfs × nvidia hook 决策 | 实测无冲突 → 保留全基线，仅增 DeviceRequests；单维度差异由 `test_gpu_security_e2e.py::TestGpuProfileSingleDelta` 锁定；ADR-0029 §4 | PASS |
| 3 | GPU capability 有界观测值对象 | `packages/domain/workers.py` `WorkerGpuObservation`（8 有界字段 fail-closed）+ `gpu_probe_digest`；`tests/domain/test_worker_gpu_observation.py` | PASS |
| 4 | worker 启动期真实探测（失败不声明 gpu） | `adapters/execution/gpu_probe.py`（真实容器 + GEMM 校验）；`tests/worker/test_worker_loop.py`（probe 失败→CPU-only、成功→声明 gpu） | PASS |
| 5 | freshness 四层 | 注册即真相（契约 `test_worker_registry_contract.py` restart 清观测）；TTL 门禁（`test_worker_gpu_gateway.py` 过期 409 / CPU 不受阻）；重探 re-register（loop 测试 digest 变化）；执行期断言（WP3c） | PASS |
| 6 | 调度需求 gpu-small/gpu-oom-probe + derive | `adapters/execution/profiles.py`（GpuRequirements + derive_required_capability）；`test_gpu_dispatch.py` | PASS |
| 7 | backend_kind 缺陷修复（真实远程分发可 claim） | `remote_backend._submit` 改用 derive；回归 `test_gpu_dispatch.py::test_real_experiment_spec_claims_as_docker`；真实 worker claim 修复见 `WorkerClient._capabilities`（slice E2E 实证） | PASS |
| 8 | 三实现调度契约（GPU 不入 CPU-only / 不升级 / 伪造拒 / 无 GPU→UNSCHEDULABLE） | `tests/contracts/test_gpu_claim_contract.py`（Fake/SQLite/PG 18 例）；`test_gpu_dispatch.py::test_gpu_profile_unclaimed_timeout_is_gpu_unavailable` | PASS |
| 9 | pinned GPU sandbox 镜像 | `adapters/execution/sandbox/Dockerfile.gpu`（基座 digest pin，非 root）；构建产物 `research-os-gpu-sandbox:m17-v1` | PASS |
| 10 | DeviceRequests（仅 GPU profile）+ GPU usage 摘要 | `docker_backend._create_container`（唯一 delta）+ `_parse_gpu_facts` 白名单并入 compute_usage_summary；`test_gpu_backend_unit.py` | PASS |
| 11 | Real GPU Smoke（device/CUDA/compute/logs/artifact/timeout/cleanup） | `test_gpu_backend_e2e.py` 4 例（真实 GEMM 精确 checksum + facts + 落盘 + timeout 清理 + network none） | PASS |
| 12 | 无静默 CPU fallback 四层 + 隐藏 GPU 负向 + 静态检查 | L2 容器层映射 GPU_UNAVAILABLE；L3 容器内断言 + `test_gpu_backend_e2e.py::test_hidden_gpu_must_fail_not_fallback`；L4 证据层 `test_gpu_no_fallback_evidence.py`；静态检查 `test_gpu_no_fallback_static.py` | PASS |
| 13 | FailureCategory GPU_UNAVAILABLE/GPU_OOM + 映射 + FAILURE_MODEL | `packages/domain/enums.py`；映射点 docker/remote/classification；`docs/reliability/FAILURE_MODEL.md` 矩阵；边界测试 `test_gpu_failure_semantics.py`（OOM≠NEGATIVE_RESULT） | PASS |
| 14 | 受控可重复 OOM | `test_gpu_oom_e2e.py`（真实 CUDA OOM→GPU_OOM→进程终止/容器清理/显存释放实测回升/下一 job 成功/probe 健康） | PASS |
| 15 | 长 GPU job 取消 + stale-fence | `test_gpu_cancel_scenario.py`（cancel 传播→容器 kill→CANCELLED→lease 释放→显存健康→迟到结果 409）；gateway cancel 路由 lease-holder-only | PASS |
| 16 | UsageLedger GPU_TIME 首个真实消费方 | `budget_entries.experiment_entries` GPU_TIME（KNOWN 量 + UNKNOWN 成本不写 0）；`test_gpu_usage_entries.py`；slice E2E budget_entries≥1 | PASS |
| 17 | Telemetry 3 MetricName + gpu_device_ref + REMOTE_EXECUTION span + 隐私 canary | `attributes.py`（GPU_* + gpu_device_ref digest）；`services/worker/loop.py` 发射点；`test_m17_gpu_vocabulary.py`（原文设备名/框架永不进遥测面） | PASS |
| 18 | 真实 GPU Research Slice 全链 + 可复现性 | `examples/experiments/m17_gpu_research.py`（FP32 vs bf16 + GPU/CPU 对照）+ `m17_gpu_research_v1` 协议 + `m17_gpu_v1` 评测集（含 gpu_compute_device 判别器）；`test_gpu_research_slice.py`（RemoteExecutionBackend over 真实 worker，Objective→Deliverable verdict PASS）；`test_gpu_reproduction_e2e.py`（≥2 次真实重复，语义容差实测，GPU fingerprint 绑定 audit） | PASS |
| 19 | M16 回归 + 安全 + 过度宣称门禁 + 诚实边界 | `tests/distributed` 25 例全绿（含 GPU fencing 变体）；`test_gpu_security_e2e.py` 9 例；`test_overclaiming_gate.py`（推迟词仅在 deferral 语境 + physically-remote NOT VERIFIED 声明存在）；本记录诚实判定表 | PASS |

## 实际执行 workload 清单

- GPU 探测（torch 设备属性 + 64×64 GEMM）
- GPU smoke（128×128 GEMM + facts + 落盘 + timeout + network-none）
- 受控 OOM（256 MiB 分块分配越过 free+512MiB，捕获 OutOfMemoryError）
- 取消（sleep 120 GPU 容器被协作式 kill）
- Research Slice（8000/2000 合成 4 类 MLP，FP32 vs bf16 autocast，GPU/CPU 计时对照）
- 复现（同 seed+image 两次真实重复）

## Deferred（不实现，禁止 Fake/Mock 宣称 supported）

multi-GPU scheduling、multi-GPU training、NCCL、distributed training、
multi-node execution、Slurm、PBS、MPI、HPC scheduler、RDMA、InfiniBand、
heterogeneous accelerator fleet、GPU autoscaling、cluster federation、HPC
quota system；外加 **physically-remote GPU host**（本环境 GPU 与 Control
Plane 同机，NOT VERIFIED）。

## SI-1 Readiness 判定

M17 为 SI-1（Personal Scale Integration Review）提供：真实 GPU 执行 + 跨进程/
跨网络 untrusted worker 边界 + 完整 Artifact/Evidence/Evaluation/Usage 闭环 +
失败/取消/OOM 语义 + 可复现性。**不**提供 physically-remote GPU host 证据
（SI-1 不得据此宣称多机 GPU 集群）。M17 PASS 后进入 SI-1。

## 验证命令与结果（2026-09-02）

见 `RECHECK-20260902-028`（全量门禁实测计数）。
