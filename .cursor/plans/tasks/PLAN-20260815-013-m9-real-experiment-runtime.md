---
id: PLAN-20260815-013
slug: m9-real-experiment-runtime
title: M9 Real Experiment Runtime
status: DONE
created_at: 2026-08-15
updated_at: 2026-08-15
cursor_plan_uri: c:\Users\googl\.cursor\plans\m9_真实实验运行时_a884c681.plan.md
owners:
  - root-agent
authorization:
  source: cursor-plan
  ref: "m9_真实实验运行时（用户批准：M9 范围/DoD 以 MILESTONES.md 为唯一权威，三 work packages，批准后自主持续执行至阶段边界）"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260815-013-m9-real-experiment-runtime.md
memory_entries: []
---

# PLAN-20260815-013 — M9 Real Experiment Runtime

## 目标

把实验执行骨架升级为真实、隔离、可复现的容器实验运行时：
- 真实容器版 ExecutionBackend 通过现有 contract suite；
- 打通 `ExperimentPlan → ExperimentRun → Metric → Artifact` 执行链；
- 建立 ReproducibilityAudit 与 Artifact retention/export bundle；
- 清偿 BACKLOG 两条 M9 目标 P1 债。

## 范围

- 包含：`adapters/execution/`（DockerExecutionBackend + sandbox
  Dockerfile + profiles）；`adapters/workspace/FileWorkspaceBackend`；
  `packages/domain/experiments.py`/`experiment_state.py`/
  `reproducibility.py`；`packages/application/experiments/`（执行、
  解析、分类、审计 use case）；`packages/application/artifacts/`
  （retention、export bundle）；契约资产与文档同步（PORTS.md、
  LICENSE_MATRIX、UPSTREAM_COMPONENTS、新 schema×2、INDEX、
  M9_DOCKER_QUALIFICATION、M9_COMPLETION_RECORD）。
- 不包含：远程多 Worker（M16）、GPU/HPC（M17）、Temporal（M14）、
  Research Console（M13）、系统级强化沙盒、重写 run_orchestration
  Agent 会话路径、宿主 Shell/Docker socket/任意 host mount/Secret
  枚举/开放网络。

## 架构与数据流

```text
ExperimentPlan(PREREGISTERED)
  → ExperimentExecutor（application use case）
    → WorkspaceBackend.acquire_lease（无 Lease 不执行）
    → ExecutionSpec → ExecutionBackend（DockerExecutionBackend 一次性容器，
      默认 deny host_config，仅 bind-mount 租约工作区）
    → ExecutionRun（stdout/stderr digest + image_digest + 资源摘要）
    → ArtifactStore.put（内容寻址，不拥有 Evidence truth）
    → experiment_result.json 解析 → MetricValue（Decimal，可进 digest）
    → 状态分类（NEGATIVE_RESULT ≠ 执行失败）
    → post-snapshot → ExperimentRun 终态
  → ReproducibilityAudit（input/code/env/seed/resource/image/snapshot/output
    digest 全绑定，audit_digest 确定性封存）
  → retention（显式触发）/ export bundle（内容寻址，digest 复核）
```

职责边界保持：WorkspaceBackend 管 Workspace/Lease 不执行命令；
ExecutionBackend 执行不记账；ArtifactStore 持久化不拥有 truth。

## 验收条件

- [x] AC-01：ExecutionBackend contract suite 以真实容器实现通过（Fake+Docker 双实现）
- [x] AC-02：DockerWorkspace 创建/挂载/执行/清理全量验证（容器 E2E）
- [x] AC-03：容器 timeout/崩溃故障注入测试（TIMED_OUT+kill、非零退出、OOM、pids、镜像缺失、网络禁用）
- [x] AC-04：ExperimentRun 可复现（同 input+seed+image 同 digest；变 seed 变化）
- [x] AC-05：镜像 pin 与供应链登记（UPSTREAM_COMPONENTS + LICENSE_MATRIX + 校验器回归）
- [x] AC-06：ReproducibilityAudit 绑定全部锚点，篡改检测有效
- [x] AC-07：Artifact retention（typed policy）/ export bundle（digest 复核往返）
- [x] AC-08：NEGATIVE_RESULT ≠ 执行失败（exit 0 声明负结论；非零退出不采信声明）
- [x] AC-09：m0 profile 全绿 + validate_bundle + governance validate PASS
- [x] AC-10：独立 recheck PASS（本任务计划）

## 实施清单

- [x] STEP-01：WP1 容器执行（DockerExecutionBackend、profiles、sandbox Dockerfile、docker-py pin、qualification 文档）
- [x] STEP-02：WP1 测试（单元 + 容器 E2E + 故障注入 + 容器 contract + CI container job）
- [x] STEP-03：WP2 Domain（ExperimentPlan/Run/Metric/MetricValue + 状态机 + FileWorkspaceBackend）
- [x] STEP-04：WP2 use case（ExperimentExecutor + metric_extraction + classification + artifact_ingest）
- [x] STEP-05：WP3 审计与保留（ReproducibilityAudit + retention + blob 共享删除修复 + QUARANTINED 删除迁移）
- [x] STEP-06：WP3 export bundle + schema 登记 + 校验器 DOCKERFILE 来源支持
- [x] STEP-07：全量回归 + 完成记录 + BACKLOG/MILESTONES/INDEX 同步

## 子代理使用

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| 1 | Plan Mode 调查：执行链与容器缺口 / 实验生命周期 / Artifact 与复现性 / 验证与 CI | 4 | 完成 | 四份调查报告（Plan Mode 上下文） |

> Wave 1 为 Plan Mode 只读调查（4 个 explore 子代理并行，符合当时
> Plan Mode 上下文与并行调查价值）；实施阶段未再委派子代理。

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | STEP-01 | test | `tests/adapters/execution/test_docker_backend_unit.py` | 17 passed |
| EV-02 | STEP-02 | test | `tests/adapters/execution/test_docker_backend_e2e.py`（requires_docker，本机 Docker 29.2.1） | 10 passed |
| EV-03 | STEP-02 | test | `tests/contracts/test_execution_backend_docker.py` | 6 passed |
| EV-04 | STEP-03 | test | `tests/domain/test_experiments.py` + `tests/adapters/workspace/test_file_backend.py` | 39 passed |
| EV-05 | STEP-04 | test | `tests/application/experiments/`（含容器 E2E 6 tests） | 离线 20 + 容器 6 passed |
| EV-06 | STEP-05/06 | test | `tests/application/artifacts/` + `test_repro_audit.py` + `test_validate_bundle_dockerfile.py` | passed |
| EV-07 | STEP-07 | check | m0 profile（run_all_checks.py --profile m0 --keep-going） | PASS 18/18 |
| EV-08 | STEP-07 | check | validate_bundle + governance validate | 验证通过 |
| EV-09 | STEP-07 | doc | `docs/roadmap/M9_COMPLETION_RECORD.md` | DoD 逐项证据 |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-15 | 初始化 | 用户批准的 Cursor Plan（M9 三 work packages） | 无 |
| 2026-08-15 | 执行路径改为 `adapters/execution/` docker-py 自建，不复用 OpenHands DockerWorkspace | agent-server 运行模型与 ExecutionBackend 命令执行语义不兼容；openhands-workspace 未 pin | M6 映射代码保持 mapping-only，docstring 修正；决策记录入 M9_DOCKER_QUALIFICATION |
| 2026-08-15 | ExecutionSpec 增 3 个可选字段（workspace_path/environment/workdir） | 容器执行需要挂载路径与白名单 env；向后兼容 | PORTS.md 同步 |
| 2026-08-15 | MILESTONES M9 Inputs 所称 Experiment 实体在代码中不存在（调查实证） | 文档乐观声明与代码不符 | M9 在 Domain 新建实体（属 M9 范围，不构成第二套模型）；记录于完成记录 |
| 2026-08-15 | validate_bundle 校验器增加 DOCKERFILE 来源形态 | 镜像不是 PyPI 包，需等价供应链校验 | 新增 `_check_dockerfile_adopted` + 6 个回归测试 |
| 2026-08-15 | ArtifactState 增 QUARANTINED→DELETED_TOMBSTONE 迁移 | retention 需清理过期隔离物 | Fake/Sqlite 同步，PORTS.md 记录 |
| 2026-08-15 | execute.py 拆分为 types/classification/artifact_ingest | 300 行/50 行函数硬约束 | 模块职责更清晰 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-15 | — | IN_PROGRESS | Cursor Plan 批准后开工 | Cursor Plan |
| 2026-08-15 | IN_PROGRESS | VERIFYING | AC-01..09 全部有证据，进入复检 | m0 PASS + 完成记录 |
| 2026-08-15 | VERIFYING | DONE | RECHECK-20260815-013 PASS | recheck 报告 |

## 影响报告

- Domain/API/schema：ExecutionSpec +3 可选字段；compute_usage_summary
  +3 键；Artifact.retention_policy 类型化；新增 Experiment 实体/状态机/
  ReproducibilityAudit；新 schema ×2（已登记 validate_bundle）。
- 安全/凭据：无新凭据域；容器默认 deny 全链（network none、cap drop、
  no-new-privileges、readonly rootfs、限额）；env 白名单由用例构造。
- 兼容性/迁移：contract suite 全部既有用例不变（Fake 实现未改签名）；
  SqliteArtifactStore retention_policy 序列化兼容旧字符串形式解析。
- 上游版本：新增 docker-py 7.2.0（Apache-2.0，pin）；OpenHands SDK
  1.42.0 未变更。
- 下一项任务：并行组 1 剩余 M10/M11；IG-1（M12 entry）待 M8+M9+M10+M11
  复审齐。