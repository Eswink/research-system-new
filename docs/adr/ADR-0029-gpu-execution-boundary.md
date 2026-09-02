# ADR-0029 — GPU Execution Boundary（M17）

Status: Accepted
Date: 2026-09-02
Deciders: Eswink（single owner）
Scope: `packages/domain/workers.py`（WorkerGpuObservation / GPU capability）、
`adapters/execution/`（profiles / docker_backend / gpu_probe / remote_backend）、
`services/api/worker_gateway/`（freshness TTL 门禁）、`services/worker/`
（探测与取消探针）、`docs/roadmap/M17_COMPLETION_RECORD.md`；
关联 ADR-0027（分布式执行平面）、ADR-0028（个人规模 rebaseline）

## Context

M17 经 ADR-0028 收缩为「在真实单卡 GPU Worker 上跑通一条完整 GPU Research
Slice」。落地时出现四个必须显式记录的决策：

1. **capability 观测 vs 调度键的分离**：worker 能观测到丰富的 GPU 事实
   （设备名/驱动/CUDA/显存/framework），但 M16 的任务侧需求是单字符串
   `tasks.required_capability` 精确匹配。为单 worker 个人环境发明第二套
   数值调度匹配系统属于 theater。
2. **freshness 分层**：注册是 upsert + generation+1，但没有任何 capability
   时效概念；GPU 消失/驱动变化后旧观测会误导调度。
3. **readonly rootfs × nvidia hook**：M16 安全基线含 `ReadonlyRootfs=True`；
   nvidia container runtime 的 hook 会向容器 rootfs 注入驱动库缓存，存在
   冲突风险，需要实测决策。
4. **诚实边界**：用户确认物理远程 GPU 服务器当前不可用，M17 在**本机 GPU**
   执行；worker 边界仍是 M16 已验证的跨进程 + 跨网络 untrusted gateway。
   「GPU 主机 ≠ Control Plane 主机」这一物理远程属性无法在本环境验证。

## Decision

### 1. 单 token 调度键 + 观测值对象分离

- 调度键**只有一个 token：`gpu`**（`GPU_CAPABILITY`）。GPU-required 任务
  `required_capability='gpu'`，复用 M16 已验证的 claim SQL（不改）。
- 新增 `WorkerGpuObservation` 有界值对象（`packages/domain/workers.py`）：
  device_name / device_count / driver_version / cuda_runtime_version /
  total_vram_bytes / framework / probed_at / probe_digest，全字段 fail-closed
  构造，纯数据不含 provider SDK 类型。它是**观测事实**，不是硬件清单，
  也不是调度谓词。
- VRAM/CUDA/framework 需求是**执行期契约**（`GpuRequirements`，由
  DockerExecutionBackend 注入 `RESEARCHOS_GPU_ASSERT_*` 环境，容器内强制
  断言），不进调度谓词。
- `resource_profile` 仍是唯一需求载体（Domain 不新增 GPU 类型）；GPU profile
  名集合 `GPU_RESOURCE_PROFILES` 落在 domain 作单一事实源，adapter 限额表
  与 application 证据门禁共同引用（漂移由断言锁定）。

### 2. Freshness 四层

1. **注册即真相**：restart/reconnect 必然重新探测并整体替换 capability 与
   观测（upsert + generation+1）。
2. **TTL 门禁（服务端 fail-closed）**：claim 请求含 `gpu` 时，gateway
   `_require_schedulable` 额外校验**服务端**记录的观测接收时间
   （`gpu_observed_at`，注册时由服务端时钟打点）在 TTL（默认 900s，可配）
   内，超期返回 409。worker 自报的 `probed_at` 永不参与判定（M16 服务端
   时间权威不破）。**不改动已验证的 claim SQL**。
3. **周期性重探 → 重注册**：worker 每 N 次空闲心跳重探；`probe_digest`
   变化或探测失败 → 触发 re-register（新 generation）。claim 被 409 拒绝时
   强制重探+重注册（重探即刷新服务端接收时间，清除 TTL 门禁——否则同
   digest 的陈旧观测会永久 409，活性缺陷）。
4. **执行期再验证**：每次 GPU 执行在容器内强制断言设备（见 §5），最终安全网。

### 3. 探测走真实执行路径

worker 侧 GPU 探测（`adapters/execution/gpu_probe.py`）在**已 pin 的 GPU
sandbox 镜像 + DeviceRequests + 完整安全基线**的容器内真实执行（torch 设备
属性 + 一次确定性 GEMM 校验），不是读 `nvidia-smi` 文本、不缓存、不猜测。
探测失败 → 不声明 `gpu`（退化 CPU-only 注册）。`nvidia-smi` 原文不进
canonical state，只存结构化观测 + digest。

### 4. ReadonlyRootfs 决策：不放开（实测无冲突）

WP0 实测（`M17_GPU_RUNTIME_QUALIFICATION.md` T2/T4）：完整 M16 安全基线
（readonly rootfs + tmpfs noexec + network none + CapDrop ALL +
no-new-privileges + 非 root uid 1000 + pids/mem/cpu 限额）下 CUDA 12.8
初始化与真实 GEMM 全部成功，nvidia hook 与 readonly rootfs **无冲突**。

决策：GPU profile **完整保留** M16 安全基线，与 CPU profile 的 host_config
差异**只有** `DeviceRequests`。该「单维度差异」由安全测试断言
（`test_gpu_security_e2e.py::TestGpuProfileSingleDelta`），防止未来借 GPU
需求放宽其它控制。**不批准放开 readonly rootfs。**

### 5. 无静默 CPU fallback 四层防线

1. 调度层：无 `gpu` capability 的 worker 拿不到 GPU 任务。
2. 容器层：GPU profile 但 DeviceRequests 无法满足 → Docker 创建失败 →
   映射 `GPU_UNAVAILABLE`，不重试为 CPU。
3. 容器内契约层：实验入口强制断言设备 + 只在 `cuda:0` 计算；GPU 实验源码
   禁止 `cuda if available else cpu` 模式（静态检查门禁）。
4. 证据层：`experiment_result.json` 记录真实 `compute_device`；声明 GPU 但
   记录到 CPU/缺失设备的结果在证据准入被拒（run → FAILED，结果 artifact
   不落库）。隐藏 GPU（清空设备可见性 / 无 DeviceRequests）重跑同一实验
   必须 FAIL/UNSCHEDULABLE。

### 6. 失败语义与记账

- `FailureCategory` 新增 `GPU_UNAVAILABLE` / `GPU_OOM`（additive，映射点穷尽）。
- 边界：CUDA OOM → `GPU_OOM`（执行/资源失败）；模型指标未改善 →
  `SCIENTIFIC_NEGATIVE_RESULT`（科学结论）。二者由测试固定不混淆。
- UsageLedger 复用单一 experiment 路径（M16 F-5）：`ResourceType.GPU_TIME`
  条目（首个真实消费方），货币成本 `cost_status=UNKNOWN` + 原因，绝不写 0；
  只记框架级可靠量（`torch.cuda.max_memory_allocated`），WSL2 下不记
  utilization/energy/billing。
- worker 解析的 image_digest 与 GPU 观测沿结果路径回传，使远程路径喂同一条
  用量/复现链（无第二真相）。

### 7. 诚实边界（强制条款）

- `real GPU execution` = **VERIFIED**（真实设备、真实 CUDA、真实计算）。
- `process/network-remote worker boundary` = **VERIFIED**（复用 M16 gateway/
  lease/fencing 平面）。
- `physically-remote GPU host（GPU 主机 ≠ Control Plane 主机）` =
  **NOT VERIFIED / DEFERRED**。
- 任何文档不得把本机 GPU 描述为「远程服务器 GPU」。
- Deferred（ADR-0028 清单 + 本条）：multi-GPU、NCCL、distributed training、
  multi-node、Slurm、PBS、MPI、HPC、RDMA、InfiniBand、GPU autoscaling、
  cluster federation、HPC quota、physically-remote GPU host。

## Consequences

- (+) GPU 能力发现/调度/执行/失败/取消/记账/复现全链在真实单卡 GPU 上闭环，
  且安全基线未被 GPU 需求稀释（单维度差异有测试锁定）。
- (+) 单 token 调度 + 执行期契约避免了为个人规模过度设计数值调度器。
- (−) physically-remote GPU host 未验证：M17 证明的是「跨进程/跨网络 untrusted
  worker 边界 + 真实 GPU」，不是「GPU 在另一台物理机」。SI-1/PA-1 不得据此
  宣称多机 GPU 集群能力。
- (−) WSL2/WDDM 下 NVML per-process 显存/utilization 不可靠 → 相关观测一律
  不记账，诚实标注测量局限。
- 复现契约是「语义结果在实测容差内一致」，不声称 bit-for-bit；GPU 浮点
  非确定性如实记录。
