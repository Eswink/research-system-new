---
id: PLAN-20260902-028
slug: m17-remote-gpu-execution
title: "M17 — Remote GPU Execution / Personal Scale Baseline"
status: IN_PROGRESS
created_at: 2026-09-02
updated_at: 2026-09-02
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "用户 2026-09-02 会话：循环执行 .cursor/plans/m17_remote_gpu_execution_7fa9785b.plan.md 直至完成并同步计划"
subagent_parallel_limit: 3
latest_recheck: null
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

- [ ] AC-01 WP0：GPU runtime qualification 记录 + 实际硬件事实块 +
      UPSTREAM_COMPONENTS.yaml digest pin（readonly-rootfs 决策树结论）。
- [ ] AC-02 WP1：WorkerGpuObservation 有界值对象 + gpu token 调度 +
      worker 真实探测 + migration/DTO + freshness 四层。
- [ ] AC-03 WP1 tests：探测失败不声明 gpu / restart 重建 / probe_digest
      re-register / 过期观测 gateway 拒绝 / 有界 fail-closed。
- [ ] AC-04 WP2：gpu-small / gpu-oom-probe profile +
      derive_required_capability + backend_kind 缺陷修复（真实实验远程
      分发可被 claim 的回归测试）。
- [ ] AC-05 WP2 tests：Fake+SQLite+PG 三实现调度契约（GPU 任务不入
      CPU-only worker / CPU 任务不升级 / 伪造 claim 拒绝 / 无 GPU worker
      → UNSCHEDULABLE 不落 CPU）。
- [ ] AC-06 WP3a：pinned GPU sandbox 镜像构建 + 供应链记录。
- [ ] AC-07 WP3b：DeviceRequests（仅 GPU profile）+ GPU
      compute_usage_summary + Real GPU Smoke 全过。
- [ ] AC-08 WP3c：四层无静默 CPU fallback 防线 + 隐藏 GPU 负向测试
      （CUDA_VISIBLE_DEVICES="" 与无 DeviceRequests 两路必 FAIL）+
      cuda-else-cpu 静态检查。
- [ ] AC-09 WP4a：GPU_UNAVAILABLE / GPU_OOM 分类 + 全部映射点 +
      FAILURE_MODEL.md + GPU_OOM vs SCIENTIFIC_NEGATIVE_RESULT 边界测试。
- [ ] AC-10 WP4b：受控 OOM：进程终止/容器清理/显存释放/worker 仍
      READY/下一 job 成功/canonical state 正确。
- [ ] AC-11 WP4c：取消传播/收敛/清理/lease/终态/usage + stale-fence
      迟到结果被拒。
- [ ] AC-12 WP5a：ExperimentUsage GPU 字段 + GPU_TIME 条目（首个真实
      消费方）+ 成本 UNKNOWN 不写 0 + 只记可靠量。
- [ ] AC-13 WP5b：3 个 GPU MetricName + gpu_device_ref + REMOTE_EXECUTION
      span 补发 + 隐私 canary GPU 路径。
- [ ] AC-14 WP6a：m17_gpu_research_v1 协议 + m17_gpu_v1 评测集 + FP32 vs
      混合精度 + GPU/CPU 对照，clean_run 全链 Objective→Deliverable。
- [ ] AC-15 WP6b：≥2 次重复 + fingerprint/allowed_variance 记录 + 浮点
      非确定性如实记录。
- [ ] AC-16 WP7a：tests/distributed 全套回归 + GPU 长任务 fencing 变体。
- [ ] AC-17 WP7b：GPU 安全测试套件 + 过度宣称 grep 门禁（含
      physically-remote NOT VERIFIED 声明存在性校验）。
- [ ] AC-18 WP8：M17_COMPLETION_RECORD（19 条 Exit Criteria 逐条证据）+
      ADR-0029 + MILESTONES/INDEX/BACKLOG/CHANGELOG/UPSTREAM 同步 +
      全量门禁 + RECHECK-20260902-028。
- [ ] AC-19 完成后停止，交独立复审窗口（PART B）；不自动进入 SI-1。

## 实施清单

- [ ] STEP-01：plan-asset（本文件 + ALL_PLAN 行 IN_PROGRESS）。
- [ ] STEP-02：WP0 环境发现 + GPU runtime qualification（先行门）。
- [ ] STEP-03：WP1 + WP1-tests（capability 值对象/探测/持久化/freshness）。
- [ ] STEP-04：WP2 + WP2-tests（profiles + derive_required_capability +
      三实现契约）。
- [ ] STEP-05：WP3a/b/c（GPU 镜像 + DeviceRequests + Real Smoke +
      无 fallback 防线与负向测试）。
- [ ] STEP-06：WP4a/b/c（失败分类 + OOM + 取消）。
- [ ] STEP-07：WP5a/b（Usage GPU_TIME + Telemetry）。
- [ ] STEP-08：WP6a/b（Research Slice + 可复现性）。
- [ ] STEP-09：WP7a/b（M16 回归 + 安全 + 过度宣称门禁）。
- [ ] STEP-10：WP8（Completion Record + ADR-0029 + 文档同步 + 全量门禁
      + RECHECK）→ 停止。

## 状态历史

- 2026-09-02：计划建立（IN_PROGRESS）；STEP-01 完成。
