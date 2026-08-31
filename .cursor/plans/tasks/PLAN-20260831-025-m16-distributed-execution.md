---
id: PLAN-20260831-025
slug: m16-distributed-execution
title: M16 Distributed Execution + Remote Sandbox/Worker
status: VERIFYING
created_at: 2026-08-31
updated_at: 2026-08-31
cursor_plan_uri: .cursor/plans/m16_分布式执行_1657b1d6.plan.md
owners:
  - root-agent
authorization:
  source: cursor-plan
  ref: "用户已批准 M16 计划(m16_分布式执行_1657b1d6.plan.md)并要求循环执行至完成"
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260831-025 — M16 Distributed Execution + Remote Sandbox/Worker

## 目标

在 M14 已验证的 PostgreSQL 队列/lease/fencing 内核之上，增量建立 Research OS 正式
Distributed Execution Plane：Worker 生命周期与认证、能力/分区调度、远程 Sandbox
ExecutionBackend、真实多进程网络故障取证，以及 SWE-ReX 等价上游 qualification 裁决。
M16 不建第二队列/租约/Artifact 真相；PostgreSQL 仍是唯一 canonical；Worker 是
untrusted 执行方，授权独占于 Control Plane。权威范围：`docs/roadmap/MILESTONES.md`
M16 节。Non-goals：GPU 调度（M17）、多租户配额（M18）、自动扩缩容、公有云多地域。

## Current Local Execution Contract（基线固化，实测）

- 队列/租约内核：`WorkflowEngine` Port（submit / acquire_lease(task_id) / heartbeat /
  complete / cancel / cancel_run / recover_expired_leases），全同步，无 claim-next；
  PG 实现 `leases` 每 task 一行，`lease_id` 轮换即 fencing，`recover_expired_leases`
  是全仓唯一 `FOR UPDATE SKIP LOCKED`。
- 驱动模型是 push：`RunOrchestrationService → execute_phases → execute_task` 同进程
  for 循环内联执行；无 worker 守护进程；API 进程内三个守护线程（lease recovery /
  outbox relay / retention）。
- 时钟不统一：租约到期比较用注入应用时钟 `now_iso(now)`；`outbox_events.created_at`
  用 PG `now()`。`leases` 不记录 worker 身份。
- 执行边界：`ExecutionBackend.execute(spec, timeout_seconds) -> ExecutionRun` 同步、
  无 cancel；唯一真实实现 `DockerExecutionBackend`（本机 docker.from_env + bind-mount
  宿主路径 + NetworkMode=none/CapDrop ALL/readonly rootfs）。
- 传输缺口：`WorkspaceSnapshot` 只带 digest，无 export/import；`ArtifactStore`
  content-addressed 服务端验 digest（现成完整性边界）。
- 认证缺口：Control Plane API 完全无认证（M18/M19 债务）；M16 只补 worker 面。
- 遥测：闭集词表 OperationScope(12)/MetricName(15)/AttributeKey(27)/MetricLabel(7)，
  无内容通道，fail-open 三层。

## Distributed Responsibility Boundary

- Canonical 真相 + 授权：PostgreSQL（tasks/leases/artifacts/域表）。唯一权威。
- 队列 + 租约 + fencing：现有 PG 内核，不新建第二套。
- 调度决策（能力/分区/健康匹配）：Control Plane Application。
- Worker 注册表 / 心跳 / drain / LOST 判定：Control Plane，服务端时间为准。
- 作业输入输出内容：ArtifactStore（content-addressed，服务端复验 digest）。
- 远端命令执行：Worker 进程 + 其本地 DockerExecutionBackend。
- Worker 本地磁盘 / 容器状态 / RPC 消息 / 遥测：都不是业务真值。
- Console：只经 Control Plane 只读 API 观察，绝不直连 Worker。

## 范围

- 包含：
  - WP1：`packages/domain/workers.py`（WorkerState 状态机 + WorkerRegistration）、
    `TaskKind`；`WorkerRegistry` Port + Fake + PG + 契约套件；迁移 `008_worker_plane.sql`；
    `services/api/worker_gateway/` 独立 ASGI app + enrollment/session token 认证 +
    TLS fail-closed；`WorkerReaperScheduler` + 数据库侧时间源抽象。
  - WP2：`WorkflowEngine.claim_next`（kind=EXECUTION + 能力/分区过滤 + SKIP LOCKED）、
    `TaskLease.worker_id/fence`、`tasks.fence_seq`、fence 覆盖 completion/result/
    artifact/final status/retry、分区 sha256(run_id) mod 16 + 饥饿兜底、多 Scheduler
    并发 claim / 重叠分区单一所有权测试。
  - WP3：`adapters/execution/remote_backend.py`（RemoteExecutionBackend）、
    `WorkspaceBackend.export_bundle/import_bundle`（digest 双校验 + 符号链接/路径穿越
    拒绝）、`ExecutionBackend.execute` 可选 `cancelled` 回调、`services/worker` 进程 +
    `adapters/worker` HTTP 客户端、作业级最小凭据 scope、SWE-ReX qualification
    （M16_REMOTE_EXECUTION_QUALIFICATION.md + UPSTREAM_COMPONENTS.yaml 同步）。
  - WP4：`tests/distributed/`（distributed marker + WorkerHarness + net_proxy，场景
    A–J）、分布式安全攻击套件、遥测/词表增量 + 隐私 canary + BudgetLedger 远程记账、
    `GET /cluster/workers` + `GET /runs/{run_id}/placement` + Console useCluster、
    架构回归（.importlinter.worker / otel 登记）、文档同步、M16_COMPLETION_RECORD +
    RECHECK + 三 reviewer 独立复审。
- 不包含：
  - M17 GPU/HPC 调度、M18 多租户配额、自动扩缩容、Kubernetes、多地域、集群联邦、
    成本优化引擎。
  - run 内 phase/session 顺序执行模型的改动（phase 内并行分发为 M17 非阻塞债务）。
  - Console 全面认证（M18/M19）；Temporal 采用（除非 M16 重评条件被真实证据触发）。
  - 第二套 Experiment Domain / DistributedExperimentRun；第二 usage counter。

## 验收条件

- [ ] AC-01 Worker 生命周期状态机（REGISTERING/READY/BUSY/DRAINING/OFFLINE/LOST）有契约测试与转移表穷尽检查
- [ ] AC-02 Worker 认证：enrollment secret 常量时间比较、session token 仅存 sha256、generation 作废旧 token、反冒充 401、非 loopback 无 TLS 拒绝启动
- [ ] AC-03 协议握手 fail closed：protocol/capability/backend_kinds 不兼容即注册拒绝并计数，不「连上就算兼容」
- [ ] AC-04 心跳与时钟权威：服务端 PG now() 判 LOST；租约到期比较改数据库侧时间源；worker 自报时间不参与 expiry/fence/ordering（时钟偏移 +3600s 测试）
- [ ] AC-05 claim_next 跨进程合法分配：多进程并发 claim 无 split-brain；重叠分区仍单一所有权（partition 非权威）
- [ ] AC-06 fencing 覆盖 completion/result/artifact/final status/retry；stale result 被拒并计数（BLOCKER 级场景 C）
- [ ] AC-07 RemoteExecutionBackend 过 ExecutionBackend 契约；Application 零 local/remote 分支；超时下发 cancel
- [ ] AC-08 Workspace/Artifact 传输完整性：bundle digest + 工作区树 digest 双校验；符号链接/路径穿越/错 digest/截断/跨 task artifact 全部拒绝且有测试
- [ ] AC-09 崩溃 failover：worker 执行中硬崩溃 → 心跳/租约检测 → requeue → 接管完成 → 无 stuck/孤儿/重复 authoritative completion
- [ ] AC-10 网络分区后旧权威不复活：session 被拒必须重新注册新 generation；迟到结果被 fence 拒绝
- [ ] AC-11 重复物理执行不产生重复业务事实（幂等键 + idempotency_records + content-addressed artifact）
- [ ] AC-12 Scheduler 重启不丢 authoritative state（状态全在 PG）
- [ ] AC-13 Cancellation 语义：cancel 传播、worker ack、迟到结果不污染 canonical
- [ ] AC-14 drain：DRAINING 不再分配、既有作业正常收尾、安全 OFFLINE
- [ ] AC-15 远程路径下安全默认不变：host shell 拒绝、Docker host_config 默认拒绝、NetworkMode=none、secret 枚举面为零、凭据不入 payload/artifact/遥测
- [ ] AC-16 上游 qualification：SWE-ReX 逐项评估 + 原生 HTTP worker 与 Docker-over-TCP 基线对照 + Temporal M16 重评条件复检 + ADOPT/REJECT/DEFER 裁决 + UPSTREAM_COMPONENTS.yaml 同步（PLANNED 不声称 resolution）
- [ ] AC-17 PostgreSQL 仍唯一 canonical；迁移集仍单队列表 + 单租约表；Domain/Application 无 worker/RPC/上游类型（import-linter）
- [ ] AC-18 遥测闭集增量过基数与隐私审计；canary 扩展 worker token 与 bundle 标记；telemetry 故障不破坏正确性
- [ ] AC-19 Usage/Budget：远程执行经现有 BudgetLedger 记账（usage:{task}:remote-exec 命名空间），无第二 counter
- [ ] AC-20 Console 只读面：GET /cluster/workers + /runs/{run_id}/placement + useCluster 面板；不直连 Worker
- [ ] AC-21 M0–M15 关键回归 + m0 profile 全绿；CI 接入 tests/distributed；450/300/50 行门槛
- [ ] AC-22 独立复审 PASS（architecture / security-governance / verification 三 reviewer 并行 + 根代理交叉裁决）

## 实施清单

- [x] STEP-01 WP0 基线固化：本任务文件 + ALL_PLAN 索引 + ADR-0027 + Current Local Execution Contract / Distributed Responsibility Boundary 记录
- [x] STEP-02 WP1 domain/workers.py + TaskKind + WorkerRegistry Port + Fake + 契约套件注册
- [x] STEP-03 WP1 迁移 008_worker_plane.sql + PG WorkerRegistry
- [x] STEP-04 WP1 worker_gateway ASGI app + 认证（enrollment/session token/generation/TLS fail-closed/大小上限）
- [x] STEP-05 WP1 WorkerReaperScheduler + 数据库侧时间源抽象 + 心跳幂等/乱序规则 + LOST 并入 recover_expired_leases
- [x] STEP-06 WP2 claim_next（Fake/SQLite/PG 三实现）+ TaskLease.worker_id/fence + fence_seq 递增
- [x] STEP-07 WP2 分区键 + 饥饿兜底 + fence 校验覆盖全部 authoritative 写 + 并发/重叠分区测试
- [x] STEP-08 WP3 WorkspaceBackend export/import_bundle（File+Fake）+ 双 digest 校验 + 穿越/符号链接拒绝
- [x] STEP-09 WP3 RemoteExecutionBackend + ExecutionBackend.cancelled 回调 + DockerExecutionBackend 轮询
- [x] STEP-10 WP3 services/worker 进程 + adapters/worker HTTP 客户端 + 最小凭据 scope 下发
- [x] STEP-11 WP3 SWE-ReX qualification 文档 + UPSTREAM_COMPONENTS.yaml + Temporal 重评条件复检
- [x] STEP-12 WP4 tests/distributed 基础设施（marker/conftest/WorkerHarness/net_proxy）
- [x] STEP-13 WP4 场景 A–J + 时钟偏移测试
- [x] STEP-14 WP4 分布式安全攻击套件
- [x] STEP-15 WP4 遥测词表增量 + canary + BudgetLedger 远程记账 + 基数/隐私审计
- [x] STEP-16 WP4 operations 只读路由 + DTO/mapper + Console useCluster
- [x] STEP-17 WP4 架构回归（.importlinter.worker + otel 登记）+ CI 接入 + m0 覆盖断言
- [x] STEP-18 WP4 文档同步（PORTS/WORKFLOW_RELIABILITY/WORKSPACE_RUNTIME/OBSERVABILITY/DEPLOYMENT_PROFILES/THREAT_MODEL/IDENTITY_AND_ACCESS/SECRET_MANAGEMENT/DATABASE_SCHEMA/CONTROL_PLANE_API/OPERATIONS_RUNBOOK/INDEX/CHANGELOG/BACKLOG/MILESTONES）
- [ ] STEP-19 M16_COMPLETION_RECORD + RECHECK + 三 reviewer 独立复审 + 停在阶段边界

## 子代理使用

Subagent 默认不启用。需要并行时，每个 wave 最多 3 个；多 wave 必须在前一波完成并整合后才可开始。复审阶段固定三个 reviewer 并行。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| — | 未使用（实施阶段） | 0 | — | — |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | AC-01/02/03 | check | `pytest tests/api/test_worker_gateway.py tests/domain/test_workers_domain.py` → 15+43 pass；契约 `test_worker_registry_contract.py`（Fake+PG） | PASS |
| EV-02 | AC-04 | check | `pytest tests/api/test_worker_heartbeat_reaper.py` → 6 pass（LOST 租约并入 recover_expired_leases PG 实证） | PASS |
| EV-03 | AC-05/06 | check | `pytest tests/contracts/test_claim_fencing_contract.py tests/postgres/test_claim_concurrency_pg.py` → 24+3 pass（并发 disjoint/重叠分区/fence reclaim） | PASS |
| EV-04 | AC-07/08 | check | `pytest tests/adapters/execution/test_remote_backend.py tests/adapters/workspace/test_file_backend.py tests/contracts/test_workspace_bundle_contract.py` → 全绿 | PASS |
| EV-05 | AC-09..14 | check | `pytest tests/distributed -q` → 19 passed（场景 A–J + 时钟偏移，真实 subprocess + PG） | PASS |
| EV-06 | AC-15 | check | `pytest tests/distributed/test_security_distributed.py` → 10 pass（攻击套件） | PASS |
| EV-07 | AC-16 | file | `docs/references/upstream/M16_REMOTE_EXECUTION_QUALIFICATION.md`（SWE-ReX REJECT；实测 pin）+ UPSTREAM_COMPONENTS.yaml | PASS |
| EV-08 | AC-17 | check | `pytest tests/architecture`（test_worker_boundaries：单 tasks/单 leases、worker plane 隔离）+ lint-imports .importlinter.worker KEPT | PASS |
| EV-09 | AC-18/19 | check | `pytest tests/observability/test_m16_vocabulary.py` → 16 pass（canary + 基数） | PASS |
| EV-10 | AC-20 | check | `pytest tests/api/test_operations_api.py` → 10 pass；web tsc clean + 27 pass；OpenAPI 再生 | PASS |
| EV-11 | AC-21 | check | m0 profile（ruff/format/mypy/pytest/framework/docs 全绿修复后）+ CI m0-quality 接入 tests/distributed | PASS |
| EV-12 | AC-22 | file | 三 reviewer（architecture/security-governance/verification）独立复审 + RECHECK-20260831-025 | 见 recheck |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-31 | 用户批准 M16 Cursor Plan 并要求循环执行至完成、同步计划状态 | 计划模式调查已实测队列/租约/执行/认证/遥测现状 | 本计划执行范围 |
| 2026-08-31 | Worker transport 采用 HTTP/JSON worker gateway（复用已 pin 的 fastapi/uvicorn/httpx） | Worker 直连 PG 交出整库权威（拒绝）；gRPC/Redis/NATS 引入新上游与第二队列风险（M16 拒绝） | ADR-0027 |
| 2026-08-31 | 执行作业复用 tasks 表（kind='EXECUTION'）+ execution_jobs payload 投影，不新建队列 | 保持单队列/单租约权威；与 experiment_plans 同型 | 迁移 008 全部 additive |
| 2026-08-31 | 分区仅为 claim 过滤条件，所有权权威仍是 leases 行 | 结构上排除双重所有权；rebalance 不触碰在飞租约 | 重叠分区单一 claim 成功测试 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-31 | — | DRAFT | 建立任务计划 | Cursor Plan 批准 |
| 2026-08-31 | DRAFT | IN_PROGRESS | 用户批准并要求循环执行 | `m16_分布式执行_1657b1d6.plan.md` |
| 2026-08-31 | IN_PROGRESS | VERIFYING | WP1–WP4 实施完成；m0 门禁修复后全绿；三 reviewer 复审启动 | EV-01..EV-11 |

## 影响报告

- Domain/API/schema：待实施后填写（预期：`workers.py`、`TaskKind`、`WorkerRegistry` Port、`claim_next`、`TaskLease.worker_id/fence`、`export/import_bundle`、`cancelled` 关键字、迁移 008、2 个只读 API 端点、遥测词表增量）。
- 安全/凭据：新增 WORKER 凭据域（enrollment secret + session token sha256）；非 loopback 无 TLS 拒绝启动；作业级最小凭据 scope。
- 兼容性/迁移：全部 additive；`TaskKind` 默认 `AGENT_SESSION` 向后兼容；现有 agent-session 任务永不被远程 worker claim。
- 上游版本：预期零新直接依赖（复用 fastapi/uvicorn/httpx）；SWE-ReX qualification 若 DEFER/REJECT 则不 pin。
- 下一项任务：按 STEP-02 起顺序实施 WP1。
