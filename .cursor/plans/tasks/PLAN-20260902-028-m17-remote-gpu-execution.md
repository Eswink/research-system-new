---
id: PLAN-20260902-028
slug: m17-remote-gpu-execution
title: "M17 — Remote GPU Execution / Personal Scale Baseline"
status: DONE
created_at: 2026-09-02
updated_at: 2026-09-02
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "用户 2026-09-02 会话：循环执行 .cursor/plans/m17_remote_gpu_execution_7fa9785b.plan.md 直至完成并同步计划"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260902-028-m17-remote-gpu-execution.md
memory_entries: []
---

# PLAN-20260902-028 — M17 Remote GPU Execution

## 目标

让 M16 分布式执行平面在真实 NVIDIA GPU 上跑通一条完整的 GPU Research
Slice：真实 capability 发现、GPU-required 调度门禁、真实 CUDA 容器执行、
无静默 CPU fallback、OOM/取消/故障语义、真实 Artifact/Evidence/Evaluation/
Usage 闭环，并诚实标注「GPU 主机与 Control Plane 同一物理机」这一环境限制。

权威任务书：`.cursor/plans/m17_remote_gpu_execution_7fa9785b.plan.md`
（用户批准；含环境事实、诚实条款、执行顺序、Deferred 清单）。

## 范围

- 包含：WP0 GPU runtime qualification → WP1 capability/freshness →
  WP2 调度需求 → WP3 真实 GPU runtime + 无 fallback 防线 →
  WP4 失败语义/OOM/取消 → WP5 Usage/Telemetry → WP6 Research Slice +
  可复现性 → WP7 回归/安全/过度宣称门禁 → WP8 Completion Record +
  ADR-0029 + RECHECK。
- 不包含：multi-GPU / NCCL / distributed training / multi-node / Slurm /
  PBS / MPI / HPC / RDMA / InfiniBand / GPU autoscaling / cluster federation
  （ADR-0028 Deferred 清单）；physically-remote GPU host（本机 GPU，
  NOT VERIFIED 如实标注）；任何 Fake/Mock 宣称 supported。

## 验收条件

对应任务书 WP8 的 19 条 Exit Criteria；逐条证据见
`docs/roadmap/M17_COMPLETION_RECORD.md`（WP8 产出后回填索引）。

- [x] AC-01 WP0：GPU runtime qualification 记录 + 实际硬件事实块 +
      UPSTREAM_COMPONENTS.yaml digest pin（readonly-rootfs 决策树结论）。
- [x] AC-02 WP1：WorkerGpuObservation 有界值对象 + gpu token 调度 +
      worker 真实探测 + migration/DTO + freshness 四层。
- [x] AC-03 WP1 tests：探测失败不声明 gpu / restart 重建 / probe_digest
      re-register / 过期观测 gateway 拒绝 / 有界 fail-closed。
- [x] AC-04 WP2：gpu-small / gpu-oom-probe profile +
      derive_required_capability + backend_kind 缺陷修复（真实实验远程
      分发可被 claim 的回归测试）。
- [x] AC-05 WP2 tests：Fake+SQLite+PG 三实现调度契约（GPU 任务不入
      CPU-only worker / CPU 任务不升级 / 伪造 claim 拒绝 / 无 GPU worker
      → UNSCHEDULABLE 不落 CPU）。
- [x] AC-06 WP3a：pinned GPU sandbox 镜像构建 + 供应链记录。
- [x] AC-07 WP3b：DeviceRequests（仅 GPU profile）+ GPU
      compute_usage_summary + Real GPU Smoke 全过。
- [x] AC-08 WP3c：四层无静默 CPU fallback 防线 + 隐藏 GPU 负向测试
      （CUDA_VISIBLE_DEVICES="" 与无 DeviceRequests 两路必 FAIL）+
      cuda-else-cpu 静态检查。
- [x] AC-09 WP4a：GPU_UNAVAILABLE / GPU_OOM 分类 + 全部映射点 +
      FAILURE_MODEL.md + GPU_OOM vs SCIENTIFIC_NEGATIVE_RESULT 边界测试。
- [x] AC-10 WP4b：受控 OOM：进程终止/容器清理/显存释放/worker 仍
      READY/下一 job 成功/canonical state 正确。
- [x] AC-11 WP4c：取消传播/收敛/清理/lease/终态/usage + stale-fence
      迟到结果被拒。
- [x] AC-12 WP5a：ExperimentUsage GPU 字段 + GPU_TIME 条目（首个真实
      消费方）+ 成本 UNKNOWN 不写 0 + 只记可靠量。
- [x] AC-13 WP5b：3 个 GPU MetricName + gpu_device_ref + REMOTE_EXECUTION
      span 补发 + 隐私 canary GPU 路径。
- [x] AC-14 WP6a：m17_gpu_research_v1 协议 + m17_gpu_v1 评测集 + FP32 vs
      混合精度 + GPU/CPU 对照，clean_run 全链 Objective→Deliverable。
- [x] AC-15 WP6b：≥2 次重复 + fingerprint/allowed_variance 记录 + 浮点
      非确定性如实记录。
- [x] AC-16 WP7a：tests/distributed 全套回归 + GPU 长任务 fencing 变体。
- [x] AC-17 WP7b：GPU 安全测试套件 + 过度宣称 grep 门禁（含
      physically-remote NOT VERIFIED 声明存在性校验）。
- [x] AC-18 WP8：M17_COMPLETION_RECORD（19 条 Exit Criteria 逐条证据）+
      ADR-0029 + MILESTONES/INDEX/BACKLOG/CHANGELOG/UPSTREAM 同步 +
      全量门禁 + RECHECK-20260902-028。
- [x] AC-19 完成后停止，交独立复审窗口（PART B）；不自动进入 SI-1。

## 实施清单

- [x] STEP-01：plan-asset（本文件 + ALL_PLAN 行 IN_PROGRESS）。
- [x] STEP-02：WP0 环境发现 + GPU runtime qualification（先行门）。
- [x] STEP-03：WP1 + WP1-tests（capability 值对象/探测/持久化/freshness）。
- [x] STEP-04：WP2 + WP2-tests（profiles + derive_required_capability +
      三实现契约）。
- [x] STEP-05：WP3a/b/c（GPU 镜像 + DeviceRequests + Real Smoke +
      无 fallback 防线与负向测试）。
- [x] STEP-06：WP4a/b/c（失败分类 + OOM + 取消）。
- [x] STEP-07：WP5a/b（Usage GPU_TIME + Telemetry）。
- [x] STEP-08：WP6a/b（Research Slice + 可复现性）。
- [x] STEP-09：WP7a/b（M16 回归 + 安全 + 过度宣称门禁）。
- [x] STEP-10：WP8（Completion Record + ADR-0029 + 文档同步 + 全量门禁
      + RECHECK）→ 停止。

## 状态历史

- 2026-09-02：计划建立（IN_PROGRESS）；STEP-01 完成。
- 2026-09-02：WP0–WP8 全部完成，RECHECK-20260902-028 = PASS_WITH_WARNINGS → DONE。

工程记忆：无可复用事实——M17 的 GPU 观测/调度/freshness/无-fallback/取消/OOM/记账/复现设计决策已由 ADR-0029 + M17_COMPLETION_RECORD + 资格记录权威承载；跨会话可复用的工程教训（backend_kind 缺陷、falsy-zero ExitCode、claim 能力回写、CANCELLED 规范化漂移）均已内化为代码 + 回归测试，无需单独记忆条目。

## 证据

- 代码：`packages/domain/workers.py`（WorkerGpuObservation/GPU_CAPABILITY/
  GPU_RESOURCE_PROFILES）、`adapters/execution/{profiles,docker_backend,
  gpu_probe,remote_backend}.py`、`services/worker/{loop,__main__}.py`、
  `services/api/worker_gateway/{jobs,dto,settings,app}.py`、
  `adapters/postgres/migrations/009_worker_gpu.sql`、
  `packages/application/experiments/{budget_entries,classification,execute,
  metric_extraction}.py`、`packages/application/observability/attributes.py`、
  `packages/application/evaluation/scorers_m17_gpu.py`、
  `examples/{experiments/protocols/eval}` M17 资产。
- 测试：`tests/domain/test_worker_gpu_observation.py`、
  `tests/contracts/{test_worker_registry_contract,test_gpu_claim_contract}.py`、
  `tests/api/test_worker_gpu_gateway.py`、`tests/worker/test_worker_loop.py`、
  `tests/adapters/execution/{test_gpu_dispatch,test_gpu_backend_unit,
  test_gpu_backend_e2e,test_gpu_oom_e2e,test_gpu_security_e2e,
  test_gpu_reproduction_e2e}.py`、`tests/application/experiments/
  {test_gpu_no_fallback_evidence,test_gpu_failure_semantics,test_gpu_usage_entries}.py`、
  `tests/distributed/{test_gpu_cancel_scenario,test_gpu_research_slice}.py`、
  `tests/observability/test_m17_gpu_vocabulary.py`、`tests/architecture/
  {test_gpu_no_fallback_static,test_overclaiming_gate}.py`。
- 运行：Real GPU Smoke 4/4、受控 OOM、取消、Slice 全链 verdict PASS、复现 ≥2 次
  真实重复（RTX 4060 Laptop / CUDA 12.8 / torch 2.9.1，2026-09-02）。
- 文档：`docs/references/upstream/M17_GPU_RUNTIME_QUALIFICATION.md`、
  `docs/adr/ADR-0029-gpu-execution-boundary.md`、
  `docs/roadmap/M17_COMPLETION_RECORD.md`、`UPSTREAM_COMPONENTS.yaml`。

## 影响报告

- Domain/API/schema：`FailureCategory` +GPU_UNAVAILABLE/GPU_OOM；
  `WorkerRegistration` +gpu_observation/gpu_observed_at（additive）；
  `ExperimentRunResult` +gpu 字段；`ReproducibilityAudit` +gpu_fingerprint/
  allowed_variance；`ExecutionJobQueue` Port +claimed_by/image_digest/gpu 观测；
  migration 009 additive；worker gateway +cancel 路由 +gpu_observation DTO。
- 安全/凭据：GPU profile 仅增 DeviceRequests（单维度差异锁定）；探测走真实执行
  路径；无静默 CPU fallback 四层；secret 面不变。
- 兼容性/迁移：全部 additive；旧 worker 无 gpu_observation 正常注册；
  CANCELLED 规范化修正（PG 与 Fake 对齐）。
- 上游：新增 pinned GPU 基础镜像（digest）；无新 Python 依赖。
- 诚实边界：physically-remote GPU host = NOT VERIFIED/DEFERRED。
