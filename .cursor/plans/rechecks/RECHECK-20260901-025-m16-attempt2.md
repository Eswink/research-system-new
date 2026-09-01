---
id: RECHECK-20260901-025
plan_id: PLAN-20260831-025
attempt: 2
status: COMPLETED
result: PASS
created_at: 2026-09-01
completed_at: 2026-09-01
owners:
  - root-agent
reviewers:
  - independent-adversarial-review
---

# RECHECK-20260901-025 — M16 Distributed Execution（独立对抗复审 attempt 2 + 整改轮）

- Date: 2026-09-01
- Scope: `PLAN-20260831-025`（M16）。对 attempt-1 复审结论做独立对抗重判，
  以当前代码 / PostgreSQL canonical state / 真实 OS 子进程 / 真实网络传输 /
  实际远程执行 / ArtifactStore / 故障注入 / M15 遥测 / 确定性回归为事实来源，
  不采信开发窗口的任何 PASS 声明。
- Method: 根代理 + 两个只读探查代理（架构边界 / 凭据泄漏）交叉核对；
  4 个独立对抗探针（真实子进程并发 owner、真实 Docker 远程往返、drain claim、
  未注册能力 claim）+ 第 5 个跨任务替换探针复验；逐项 Reproduce→Root Cause→
  Minimal Fix→Regression→Distributed Re-run→Full Gate。

## 发现矩阵（attempt 2）

| ID | 级别 | 发现 | 处置 |
| --- | --- | --- | --- |
| F-1 | MAJOR | claim 不强制 worker 状态与已注册能力；drain 纯协作 | 已修复 + 回归 |
| F-2 | MAJOR | harness 向 worker 子进程注入 `RESEARCHOS_POSTGRES_DSN`；attempt-1 记录谎称"已移除" | 已修复 + 记录更正 |
| F-3 | MAJOR | 分布式面无生产 composition（gateway 无入口、reaper 不在 lifespan、RemoteBackend 无组装点） | 已修复 + 测试 |
| F-4 | MAJOR | 跨任务 artifact 替换不拒绝不测试（AC-08 过度声明）；内容寻址 id 碰撞 | 已修复 + 回归 |
| F-5 | MAJOR | remote-exec usage 记账为死代码（AC-19 证据不实） | 已修复（删死码 + 实测 elapsed） |
| F-6 | MINOR | 6 个分布式场景弱证/空转（A/C/D/F/J/skew + 并发 claim 顺序化） | 已修复为真实断言 |
| F-7 | MINOR | 执行期无租约续期：长任务被误 failover | 已修复（renew_lease + worker 线程） |
| F-8 | MINOR | remote 未跑正式共享 ExecutionBackend 契约套件 | 已补镜像套件 |
| F-9 | MINOR | bundle canary 死码；M16 通道无端到端 exporter 字节扫描 | 已修复 |
| F-10 | MINOR | download_bundle 无 per-lease ACL；通用错误处理器 `str(exc)` 未脱敏 | 已修复 |

## 整改记录（逐项）

1. **F-1 claim 服务端强制**：`worker_gateway/jobs.py::claim_job` 在认证身份后新增
   `_require_schedulable`——`identity.state ∈ WorkerState.schedulable()`（恰为 READY）
   否则 409；`payload.capabilities ⊆ identity.capabilities` 且
   `payload.partitions ⊆ identity.partition_slots` 否则 409（fail closed，不钳制）。
   `WorkerState.schedulable()` 自此有调用者。回归：gateway 单测 4 例 + 攻击套件
   drain/能力 2 例 + 场景 G 强化 + 探针 3/4（409）。
2. **F-2 harness DSN + 记录不实**：`worker_harness.py` 抽出 `worker_child_env()`，
   显式 pop `RESEARCHOS_POSTGRES_DSN`/`DATABASE_URL`；新增单测断言 worker 子进程
   env 零 DB 凭据。attempt-1 记录加更正行指向本文件（不改写历史正文）。
3. **F-3 生产 composition**：新增 `worker_gateway/composition.py`
   （`build_worker_gateway_deps` 每适配器独立 PG 连接 + `build_gateway_from_env`）
   与 `worker_gateway/__main__.py`（`python -m services.api.worker_gateway`，
   TLS fail-closed 由 `create_worker_app` 强制）；`app.py` lifespan 新增
   `_start_worker_reaper`（gate 在 `deps.worker_registry`，逆序 stop 抽
   `_stop_schedulers`）。诚实边界：Control Plane 实验编排当前仍走 FakeAgentRuntime，
   远程分发选择属 M17（DEPLOYMENT_PROFILES 注记）。回归：composition 单测 5 例。
4. **F-4 artifact provenance + ACL + 碰撞**：`ArtifactStore` Port 新增
   `meta(artifact_id)`（Fake/PG/SQLite）；`ExecutionJobQueue` Port 新增
   `assert_active_lease`（PG 提取 `_require_active_lease` 共享 + Fake 同语义）。
   `transfer.upload_bundle` 要求 `X-Task-Id/X-Lease-Id/X-Fence`，服务端校验活跃
   租约后存 `created_by=worker:{worker_id}:{task_id}`；artifact id 纳入 task
   （`bundle-{digest[:32]}-{task_id}`）修复内容寻址跨任务碰撞；`submit_result` 经
   `_require_output_provenance` 断言 ref 由本 worker 为本任务上传；`download_bundle`
   仅放行本租约任务 input 或本 worker 自有上传。worker client/loop 携带租约上下文。
   回归：契约 meta/assert_active_lease 用例 + 攻击套件 3 例 + 探针 5（409）。
5. **F-5 usage 诚实化**：`remote_backend._normalize` 写入服务端实测
   `elapsed_seconds`；删除死代码 `remote_execution_entries`（无生产调用点，且与
   experiment 路径重复计 WALL_CLOCK）；usage 单一真相走 experiment 路径。
   完成记录 AC-19 表述更正。
6. **F-6 证据完整性**：skew 死旋钮删除，改为 schema 断言（worker→gateway 全部
   DTO 无客户端时间戳字段 + reaper 用 `_time_expr`/`last_heartbeat <`）；场景 A
   断言 `owners == {a-w1,a-w2}`；场景 C 真实网关注册+会话走 409；场景 D 真实
   worker 经 NetProxy 断网（修复 `_pipe` 双向泵送短路 bug）；场景 F 在途 kill
   worker + 停/启 scheduler；场景 J 用正确 enrollment 触达协议 409；
   `test_claim_concurrency_pg` 改真并发（线程+barrier，每线程独立 engine）。
7. **F-7 执行期续租**：`WorkflowEngine` Port 新增 `renew_lease`（PG/SQLite/Fake，
   延长 expires_at 不轮换 lease_id/fence）；网关 `POST /tasks/{id}/renew`
   （gate 三元组 + 刷新 worker 心跳）；worker loop `_process` 期间守护线程续租。
   回归：契约 renew 用例 + gateway 2 例 + 场景 B/F/D 依赖其确定性。
8. **F-8 remote 契约对齐**：新增 `test_execution_backend_contract_remote.py`，
   按 docker 手工镜像先例跑正式 3 测（happy/timeout/cancelled 终态不变式）。
9. **F-9 遥测 canary**：`_BUNDLE_MARK` 接入闭集键丢弃 + metric 值域折叠断言；
   `canary_support.emit_canary_signals` 扩展 WORKER_SESSION/WORKER_DISPATCH/
   REMOTE_EXECUTION span + worker/remote metric，经端到端 OTLP 字节扫描。
10. **F-10 脱敏 + ACL**：`errors.py::_handler` 对 `str(exc)` 过 `redact_text`；
    download ACL 并入 F-4。

## 复验命令与结果（2026-09-01，整改后）

```text
RESEARCHOS_REQUIRE_POSTGRES=1 pytest tests/distributed -q
  → 24 passed（场景 A–J 真实断言 + 时钟免疫 schema + 攻击套件含 drain/能力/
    跨任务替换/零 DSN env，真实 subprocess + PG）
RESEARCHOS_REQUIRE_POSTGRES=1 pytest tests/distributed tests/contracts tests/architecture
  tests/api tests/worker tests/observability tests/tooling -q
  → 1318 passed, 2 skipped（Windows symlink 权限）
m0 profile --keep-going → PASS: profile=m0; 23 deterministic checks 全绿
ruff check / ruff format --check / mypy（apps services packages adapters tests）→ 干净
system-spec-check / governance-check / framework / docs-consistency → PASS
对抗探针（scratch/m16_reaudit_probes.py）→ 5/5 PASS：
  probe1 并发 owner（4 进程各自持任务）· probe2 真实 Docker 远程往返
  probe3 drain claim 409 · probe4 未注册能力 409 · probe5 跨任务替换 409
```

## 不变式复核（attempt 2）

- PostgreSQL 仍唯一 canonical；单队列/单租约不变；迁移 008 仍 additive。
- Worker 子进程 env 零 DB 凭据（探针 + 单测双重证据）。
- 授权独占 Control Plane：claim/renew/upload/result 全部服务端按
  `(task_id, lease_id, fence)` + 认证身份 + 注册事实强制。
- 遥测不参与调度权威；worker_ref 为 digest；bundle 内容经端到端字节扫描证明不外泄。
- Usage 单一真相：远程执行经 experiment 路径记真实测得时长，无第二 counter。

## 检查结果（AC 重判矩阵）

AC-01..AC-22 经 attempt-2 重判：attempt-1 曾据以判 PASS 的 AC-02/03/08/14/19/21
存在证据不足或声明过度，整改后全部以真实代码 + 回归测试 + 对抗探针重判 **PASS**；
其余 AC 维持 PASS。逐项证据映射见
`docs/roadmap/M16_COMPLETION_RECORD.md`「attempt-2 更正」节与本文件「整改记录」。

## 结论

- F-1..F-10 全部关闭（5 MAJOR + 5 MINOR），attempt-1 不实声明已更正。
- **M16 = PASS**（以真实代码 / PG canonical / OS 子进程 / 真实网络 / 实际远程执行 /
  故障注入 / 遥测 / 确定性回归为证据）。
- 停在阶段边界：不自动进入 M17/M18。剩余债务见 BACKLOG（M17：BUSY/max_concurrency
  接线、phase 内并行分发、远程分发 composition 选择；非 M16 扫描 high 另立计划）。

## 密封深度扫描（attempt-2 收尾，2026-09-01）

- scanId `scan-2026-09-01T10-27-41.877Z-9e050066064d`，seal
  `sha256:399b1c6a7f595f93f0282e281bd452f152df190a573611a39b2ded96ae182549`。
- 38 findings（6 high / 27 medium / 5 low）；依赖扫描完成（180 包，1 advisory）。
- **6 个 high 全部落在非 M16 代码**：`scratch/audit_*`（本地审计脚本）、
  `tools/upstream-spikes/S2_llm_construction.py`、`examples/experiments/m12_reference_classification.py`、
  `adapters/research_tools/parsing.py`（M8 解析器）。M16 整改面零 high；上一轮
  `adapters/sqlite/db.py` PRAGMA high 已清。
- **覆盖仍 partial / runStatus inconclusive**（threatModel 0 entry points、
  findingDiscovery businessLogicCandidates 0）——扫描器未解析出本应用以工厂函数
  （`create_app`/`create_worker_app`）装配的 FastAPI 入口，属扫描器能力边界，
  非本轮可闭合。**不得据此宣称项目安全**；完整覆盖基线待扫描器入口解析改进后重建。
- 非 M16 的 6 个 high 已登记 BACKLOG，另立计划处置。
