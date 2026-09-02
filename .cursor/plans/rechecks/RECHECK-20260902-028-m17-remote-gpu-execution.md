---
id: RECHECK-20260902-028
plan_id: PLAN-20260902-028
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-02
completed_at: 2026-09-02
reviewer: root-agent-independent-pass
baseline_ref: 359e9ba
checked_head: working-tree（M17 实施，基线 359e9ba RM-P2 rebaseline 之后）
---

# RECHECK-20260902-028 — M17 Remote GPU Execution 复检

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260902-028-m17-remote-gpu-execution.md`
- 权威任务书：`.cursor/plans/m17_remote_gpu_execution_7fa9785b.plan.md`
- 验收条件：AC-01..AC-19（对应 19 条 Exit Criteria）
- 变更范围：`packages/domain/{workers,enums,experiments}.py`、
  `packages/application/{experiments,observability,evaluation,m12_reference}/`、
  `adapters/{execution,postgres,fakes,worker,sqlite}/`、`services/{worker,api/worker_gateway}/`、
  `examples/{experiments,protocols,eval}` M17 资产、`schemas/task-contract.schema.json`、
  `UPSTREAM_COMPONENTS.yaml`、`docs/{adr,references,roadmap,reliability}/` M17 文档、
  `tests/` M17 套件、本计划与复检记录
- 基线：`359e9ba`（RM-P2 rebaseline 之后）

## 检查结果

| Gate | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| G-01 | WP0 先行门（GPU runtime qualification） | `M17_GPU_RUNTIME_QUALIFICATION.md` T1–T4 实测（RTX 4060 / sm_89 / CUDA 12.8 / torch 2.9.1 / 真实 GEMM checksum=64³ 精确）；readonly-rootfs×nvidia-hook 无冲突 → 保留全基线仅增 DeviceRequests；`UPSTREAM_COMPONENTS.yaml` `research_os_gpu_base_image` digest pin `sha256:7b324d21…` | PASS |
| G-02 | WP1 capability + freshness 四层 | `WorkerGpuObservation` 有界值对象；`gpu_probe.py` 真实容器探测；migration 009 additive；gateway 握手 gpu⇔observation + TTL 门禁（服务端时钟）；loop 重探 re-register + 409 自愈强制重注册（活性缺陷修复）；`tests/domain/test_worker_gpu_observation.py`、`tests/api/test_worker_gpu_gateway.py`、`tests/worker/test_worker_loop.py`、契约 restart 清观测 | PASS |
| G-03 | WP2 调度 + backend_kind 缺陷 | `derive_required_capability`；`test_gpu_claim_contract.py`（Fake/SQLite/PG 18 例：GPU 不入 CPU-only / 不升级 / 伪造拒 / 无 GPU→GPU_UNAVAILABLE）；`test_gpu_dispatch.py::test_real_experiment_spec_claims_as_docker` 回归锁定缺陷修复 | PASS |
| G-04 | WP3 真实 GPU runtime + 无 fallback 四层 | `DockerExecutionBackend` DeviceRequests（单维度差异 `test_gpu_security_e2e.py::TestGpuProfileSingleDelta`）；Real GPU Smoke 4/4（`test_gpu_backend_e2e.py`，真实 GEMM + 隐藏 GPU 必 FAIL/GPU_UNAVAILABLE + timeout 清理 + network none）；L4 证据层 `test_gpu_no_fallback_evidence.py`；静态检查 `test_gpu_no_fallback_static.py` | PASS |
| G-05 | WP4 失败/OOM/取消 | `FailureCategory` +GPU_UNAVAILABLE/GPU_OOM（映射点穷尽 + FAILURE_MODEL 矩阵 + schema enum 同步）；OOM≠NEGATIVE_RESULT 边界 `test_gpu_failure_semantics.py`；受控 OOM `test_gpu_oom_e2e.py`（真实 OutOfMemoryError→GPU_OOM→显存释放→下一 job 成功）；取消 `test_gpu_cancel_scenario.py`（cancel→kill→CANCELLED→lease 释放→stale-fence 409）+ 离线场景 H | PASS |
| G-06 | WP5 Usage/Telemetry | `GPU_TIME` 首个真实消费方（成本 UNKNOWN 不写 0）`test_gpu_usage_entries.py`；3 GPU MetricName + `gpu_device_ref` digest + REMOTE_EXECUTION span 补发 + 隐私 canary `test_m17_gpu_vocabulary.py`（原文设备名/框架永不进遥测面） | PASS |
| G-07 | WP6 Research Slice + 复现 | `m17_gpu_research.py`（FP32 vs bf16 + GPU/CPU 对照）+ 协议 + 评测集（gpu_compute_device 判别器）；`test_gpu_research_slice.py` 全链 verdict PASS（RemoteExecutionBackend over 真实 worker）；`test_gpu_reproduction_e2e.py` ≥2 次真实重复 + GPU fingerprint 绑定 audit + 实测 allowed_variance | PASS |
| G-08 | WP7 回归/安全/过度宣称 | `tests/distributed` 25 例全绿（含 GPU fencing 变体）；`test_gpu_security_e2e.py` 9 例；`test_overclaiming_gate.py`（推迟词仅 deferral 语境 + physically-remote NOT VERIFIED 声明存在 + 禁"远程服务器 GPU"表述） | PASS |
| G-09 | 全量门禁 | `ruff check`/`format --check` 全绿；`mypy` 684 files 无错；`test_python_source_limits` 694 passed（450/300/50 门槛，7 个超长函数已拆分）；`validate_bundle.py` 验证通过；`governance-check/validate.py` 通过；离线 pytest 2695+ passed；GPU E2E（smoke/oom/security/reproduction/cancel/slice）全绿 | PASS |
| G-10 | 诚实边界 | `M17_COMPLETION_RECORD.md` 强制判定表：real GPU execution + process/network-remote worker boundary = VERIFIED；physically-remote GPU host = NOT VERIFIED/DEFERRED；Deferred 清单（multi-GPU/NCCL/Slurm/… + physically-remote）不实现、不 Fake/Mock 宣称 | PASS |

## 警告（WARNING，不阻断）

- W-01：`physically-remote GPU host` 在本环境无法验证（GPU 与 Control Plane 同机）；
  已在 ADR-0029 / Completion Record / MILESTONES / 过度宣称门禁四处一致标注
  NOT VERIFIED/DEFERRED，SI-1 不得据此宣称多机 GPU 集群。
- W-02：WSL2/WDDM 下 NVML per-process 显存/utilization 不可靠 → 相关量一律不记账，
  只记框架级可靠量（`torch.cuda.max_memory_allocated`）；诚实标注测量局限。
- W-03：M17 密封深度扫描已重跑完成（scanId `scan-2026-09-02T06-14-50.920Z-01730a5138ce`，
  seal `sha256:538e5cea…`，38 findings；其中 27 条 medium 均为静态 advisory、
  带「需人工确认真实数据流和可利用性」proof-gap）——**M17 代码面零命中**，全部落在
  `scratch/`/`tools/probes/`/`tools/upstream-spikes/`/M12 示例/M8 解析器（BACKLOG
  既有非 M16/M17 债务，与 M16 attempt-2 同形：surface clean，coverage partial）。
  证据边界 static_only；完整密封审计在独立复审窗口（PART B）复核。

## 结论

M17 WP0–WP8 全部完成，19 条 Exit Criteria 逐条有真实证据（真实 GPU 运行，非
Fake/Mock）。判定 **PASS_WITH_WARNINGS**（警告均为环境局限与审计待重跑，非缺陷）。
完成后停止，交独立复审窗口（PART B）；不自动进入 SI-1。
