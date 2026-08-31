# M16 Completion Record — Distributed Execution + Remote Sandbox/Worker

- Date: 2026-08-31
- Plan: `.cursor/plans/m16_分布式执行_1657b1d6.plan.md`
- Task record: `.cursor/plans/tasks/PLAN-20260831-025-m16-distributed-execution.md`
- ADR: `docs/adr/ADR-0027-distributed-execution-plane.md`
- Scope source: `docs/roadmap/MILESTONES.md` M16（多 worker 注册/心跳/下线、
  分区调度、远程 sandbox adapter、worker 故障转移、SWE-ReX 或等价 qualification）

## Deliverables → Evidence Map（DoD 逐条）

| # | DoD | 证据（代码 / 测试 / 运行） | 结果 |
|---|---|---|---|
| 1 | Worker 生命周期 | `packages/domain/workers.py` WorkerState 转移表（穷尽检查）；`tests/domain/test_workers_domain.py`；契约 `tests/contracts/test_worker_registry_contract.py`（Fake+PG） | PASS |
| 2 | Worker 认证与握手 | `services/api/worker_gateway/`（auth.py 常量时间比较、token 仅存 sha256、generation 作废、反冒充 401、非 loopback 无 TLS 拒启）；`tests/api/test_worker_gateway.py` 15 例 | PASS |
| 3 | 协议不兼容 fail closed | 注册握手 protocol/backend_kinds 检查（409）；场景 J（`tests/distributed/test_scenarios.py`） | PASS |
| 4 | 心跳与时钟权威 | `WorkerReaperScheduler`（PG now() 判 LOST）；`db_time_expr/server_now` 时间源抽象；心跳幂等 greatest() 不回拨；`tests/api/test_worker_heartbeat_reaper.py`（含 LOST 租约并入单一恢复权威的 PG 实证）；时钟偏移 +3600s 场景 | PASS |
| 5 | claim_next 跨进程合法分配 | `adapters/postgres/workflow_claim.py`（静态 SQL + SKIP LOCKED）；`tests/postgres/test_claim_concurrency_pg.py`（并发 disjoint + 重叠分区单一所有权 + fence reclaim） | PASS |
| 6 | fencing 覆盖 + stale 拒绝（BLOCKER） | complete/record_result 校验 `(task_id, lease_id, fence)`；场景 C（`test_scenarios.py`）；契约 `test_claim_fencing_contract.py`（Fake/SQLite/PG） | PASS |
| 7 | RemoteExecutionBackend 过契约 | `adapters/execution/remote_backend.py`；`tests/adapters/execution/test_remote_backend.py`（超时下发 cancel、输出 digest 复验、物化回写）；`cancelled` 回调（Docker 轮询） | PASS |
| 8 | Workspace/Artifact 传输完整性 | `adapters/workspace/bundle.py`（canonical 编码 + 双重 digest）+ File/Fake `export/import_bundle`；穿越/符号链接/截断/错 digest 拒绝（`test_file_backend.py`、契约 `test_workspace_bundle_contract.py`） | PASS |
| 9 | 崩溃 failover | 场景 B：硬 kill → 租约过期 → requeue → 接管 → 无 stuck/孤儿/重复完成 | PASS |
| 10 | 分区后旧权威不复活 | 场景 D：分区 → 过期 → 恢复 → 迟到结果 InvalidInputError；重连需新 generation | PASS |
| 11 | 重复物理执行不重复业务事实 | 幂等键 enqueue（Fake/PG dedup）；场景 E；ArtifactStore 内容寻址 | PASS |
| 12 | Scheduler 重启不丢状态 | 场景 F（状态全在 PostgreSQL，重启后 poll/claim 一致） | PASS |
| 13 | Cancellation 语义 | `cancelled` 回调 + `request_cancel`；`test_remote_backend.py`（TIMED_OUT/CANCELLED 均下发 cancel） | PASS |
| 14 | drain | 场景 G + heartbeat drain_requested 传播（worker loop 退出） | PASS |
| 15 | 远程安全默认不变 | 攻击套件 `tests/distributed/test_security_distributed.py` 10 例（伪造注册/被盗 token/重放/错 fence/冒充/秘密枚举面零/超大 413/畸形 422/bundle 穿越/host shell 拒绝/Docker host_config 默认不变） | PASS |
| 16 | 上游 qualification | `docs/references/upstream/M16_REMOTE_EXECUTION_QUALIFICATION.md`（16Q：SWE-ReX REJECT；实测 pin v1.4.0/sdist sha256/MIT；对照原生 worker + Docker-over-TCP；Temporal 重评条件未触发）；`UPSTREAM_COMPONENTS.yaml` 同步（PLANNED/REJECTED，不声称 resolution） | PASS |
| 17 | PostgreSQL 唯一 canonical / 迁移 additive / 边界 | `tests/architecture/python/test_worker_boundaries.py`（迁移集恰一 tasks 一 leases；worker plane 不触业务真相；domain/application 无 worker 类型）；`.importlinter.worker` KEPT；`.importlinter.otel` 覆盖 adapters.worker | PASS |
| 18 | 遥测闭集增量 + 隐私 | `tests/observability/test_m16_vocabulary.py` 16 例（worker_ref digest、token/bundle canary、partition 有界、rejection_reason 闭集） | PASS |
| 19 | Usage/Budget 无第二真相 | `remote_execution_entries`（WALL_CLOCK [+CPU_TIME]，`usage:{run_id}:remote-exec:{task_id}`，UNKNOWN 不伪造 0）；`test_m16_vocabulary.py` | PASS |
| 20 | Console 只读面 | `GET /cluster/workers` + `GET /runs/{id}/placement`（worker_ref 短 digest；registry 缺失 503）；`apps/web` useCluster + ClusterPanel；api 10 例 + web 27 例 + tsc 全绿；OpenAPI 快照再生 | PASS |
| 21 | M0–M15 回归 + CI + 行数门槛 | `tests/distributed` 19 例全绿（真实子进程 + 真实 PG）；CI collector job 接入（`RESEARCHOS_REQUIRE_POSTGRES=1`）；`test_m0_ci_coverage` 更新；450/300/50 行门槛全过；m0 profile 全量见下 | PASS |

## 验证命令与结果（2026-08-31）

```text
uv run --frozen --no-sync python -B -m pytest tests/distributed -q
  → 19 passed（场景 A–J + 时钟偏移 + 安全攻击套件，真实 subprocess + PG）
uv run --frozen --no-sync python -B -m pytest tests/contracts tests/architecture -q
  → PASS（claim/fencing、worker registry、job queue、bundle、worker boundaries）
uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
  → m0 profile deterministic checks 全绿（见 recheck 记录的实测计数）
uv run --frozen --no-sync python -B .cursor/skills/system-spec-check/scripts/validate_bundle.py
  → 验证通过
uv run --frozen --no-sync python -B .cursor/skills/governance-check/scripts/validate.py
  → 治理验证通过
```

## 不变式复核

- PostgreSQL 仍是唯一 canonical：worker/gateway/遥测/本地文件均不回读为业务真相（架构测试断言）。
- 单队列/单租约：`tasks.kind='EXECUTION'` + `execution_jobs` 投影，非第二队列（迁移集断言）。
- M12 参考工作流关键路径：agent-session 任务默认 kind，永不被远程 worker claim（契约测试）。
- 零新直接上游依赖（复用 fastapi/uvicorn/httpx pin）；SWE-ReX 未引入。

## 独立复审

三 reviewer（architecture / security-governance / verification）独立复审：
arch PASS（1 major）、security FAIL（1 blocker + 2 major）、verification PASS
（1 major）。全部修复（ALL_PLAN 投影一致性、worker 自报 status 闭集校验、
结果写路径绑定认证身份）并以回归测试固化；全门禁重跑全绿。逐项记录见
`.cursor/plans/rechecks/RECHECK-20260831-025-m16.md`。最终裁决 M16 = PASS，
停在阶段边界，不自动进入 M17/M18。
