# SA-1 — Pre-M12 Full System Audit & Hardening（M0–M11）

- 日期：2026-08-20
- 范围：M0–M11 + DOC-R1 + IG-1 之上的全系统审计与加固；非新 Milestone、非重新开发、非重复 IG-1
- 事实优先级：当前代码 / Contract / Git evidence / deterministic validation > 文档与历史结论
- 审计方法：4 个并行只读子代理覆盖 8 个 Audit Tracks + 根代理代码级复核 + 主动 Fault Injection + 全量回归
- 判定条件：BLOCKER 全部关闭、核心质量门全绿、M0–M11 Contracts 与 IG-1 保持成立 → PASS

## 1. Audit Coverage Matrix

| Track | 范围 | BLOCKER | MAJOR（SA-1 内修复） | MAJOR（延期） | MINOR | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| T1 Architecture & Contract Integrity | domain 依赖方向 / Protocol→Manifest / Role→Skill→Capability→Tool / Evidence / Memory / Evaluation | 0 | 0 | 0 | 1 | 依赖方向、双门禁、EvalGate fail-closed 均 OK；仅 1 处 inline import（受控循环，已注释） |
| T2 State / Reliability / Recovery | 状态机合法性 / idempotency / outbox / lease / cancel / crash / 孤儿资源 | 1 | 2 | 2 | 1 | cancel 可覆盖终止态（BLOCKER）；complete 非幂等；LEASE 状态机绕过；服务层事件非事务；预算预留进程内缓存；容器孤儿无自愈 |
| T3 Security / Isolation / Credentials | secret / LLM↔Tool 凭据隔离 / exposure+execution 双检查 / workspace 路径与 symlink / 容器边界 / policy bypass | 0 | 1 | 0 | 1 | workspace symlink 遍历（MAJOR 已修）；FakePolicyEvaluator 默认 ALLOW（测试纪律风险） |
| T4 Research Truth / Provenance | ToolResult≠Evidence / Claim 门禁 / 矛盾检测 / negative result / derived index / delete-rebuild | 0 | 0 | 0 | 3 | Evidence.experiment_run_id 未填充；Artifact.source_refs 弱引用；RetrievalIndex Optional 注入 |
| T5 Test Trustworthiness | Fake-only 捷径 / 弱断言 / skip-xfail / 直接构造终态 / always-PASS / 生产路径覆盖 | 0 | 0 | 2 | 1 | OpenHands 真实对话路径零 CI 覆盖；并发 lease 冲突测试缺失；IG-1 offline 测试全 Fake 存储 |
| T6 Dependency / Supply Chain | pin / lockfile / license / revision / adapter 隔离 | 0 | 0 | 0 | 1 | mcp 为范围约束（锁文件实际 pin，有文档解释） |
| T7 Repository / Documentation | 死代码 / 重复实现 / 过期配置 / 生成文件 / 断链 / Roadmap 一致性 | 0 | 0 | 0 | 1 | `.gitignore` 无 `*.sqlite` 通配；N006 断链报告经核实为误报（`docs/PRODUCT.md` 存在） |
| T8 Runtime / Operational Hardening | 资源泄漏 / 清理 / soak / 超时层级 / 错误分类 / usage-budget / 生命周期 | 0 | 0 | 2 | 2 | 用量归账 UNKNOWN（budget 事实无效）；生产镜像可变 tag；引擎非 context manager；SIGKILL 容器残留（语言限制） |
| **合计** | | **1** | **3** | **6** | **10** | |

## 2. Findings

### 2.1 BLOCKER（已关闭）

#### SA-1-B001 — `cancel()` 可覆盖终止态任务（Canonical State 破坏）

- severity: BLOCKER
- subsystem: `adapters/sqlite/workflow_engine.py` / Task 状态机（T2）
- evidence: `cancel()` 只检查 `cancelled` flag，不检查 `status`；`packages/domain/task_state.py` 中 SUCCEEDED/FAILED/DEAD_LETTER/CANCELLED 均为无出边终止态
- reproduction（Fault Injection）: submit → acquire_lease → complete(SUCCEEDED) → cancel()；修复前任务被改写为 CANCELLED 且发出 TASK_CANCELLED 事件，与已发布的 TASK_COMPLETED 矛盾
- root cause: adapter 层绕过 domain 状态机合法性约束，未在写入前检查终止态
- fix: `cancel()` SELECT 增加 `status` 字段；`if row["status"] in ResearchTaskState.terminal(): return`（terminal_noop），不写库、不发事件
- regression coverage: `tests/adapters/sqlite/test_workflow_engine.py` 新增 `test_cancel_after_complete_is_terminal_noop` / `test_cancel_after_fail_is_terminal_noop` / `test_cancel_before_complete_cancels`（竞态对照）
- final status: FIXED（已验证回归）

### 2.2 MAJOR（SA-1 内已修复）

#### SA-1-M001 — `complete()` 非幂等，违反 at-least-once 合约

- severity: MAJOR
- subsystem: `adapters/sqlite/workflow_engine.py`（T2）
- evidence: 首次 complete 删除 lease；第二次调用因 lease 不存在抛 `InvalidInputError`；与 PORTS.md at-least-once + idempotency 语义冲突
- reproduction: submit → acquire_lease → complete(SUCCEEDED) → complete(FAILED) 第二次调用抛异常
- root cause: complete 无终止态幂等前置检查
- fix: `complete()` 先查 `tasks.status`；已为 SUCCEEDED/FAILED 时 dedup noop 返回
- regression coverage: `test_complete_is_idempotent_after_success`（原 `test_complete_requires_matching_lease` 更新为幂等语义）；`test_complete_after_cancel_raises` 保留 cancel 胜出后的显式失败语义
- final status: FIXED

#### SA-1-M002 — `recover_expired_leases()` 绕过 domain 状态机

- severity: MAJOR
- subsystem: `adapters/sqlite/workflow_engine.py` + `packages/domain/task_state.py`（T2）
- evidence: SQL 直接 `SET status = QUEUED`；`task_state.py` 原 LEASED 只有 START→RUNNING、CANCEL→CANCELLED 两条出边
- reproduction: acquire_lease 后使 lease 过期 → recover_expired_leases() → LEASED 状态被裸写为 QUEUED
- root cause: 状态机未声明 LEASED 的过期回退转换，adapter 与 domain 语义分裂
- fix: `task_state.py` 新增 `(State.LEASED, Transition.EXPIRE_LEASE): State.QUEUED`；`docs/reliability/RUN_STATE_MACHINE.md` 迁移表同步；adapter 注释声明对应关系
- regression coverage: `test_state_machines.py::test_task_lease_expiry_returns_to_queued`（合法转换 + RUNNING 上 EXPIRE_LEASE 非法）
- final status: FIXED

#### SA-1-M005 — Workspace symlink 遍历（宿主文件泄露）

- severity: MAJOR
- subsystem: `adapters/workspace/file_backend.py`（T3）
- evidence: `snapshot()` 用 `shutil.copytree`、`workspace_tree_digest()` 用 `path.is_file()`，均跟随 symlink；攻击者在 workspace 放置指向工作区外文件的 symlink 可被 snapshot 复制/摘要
- reproduction（Fault Injection）: workspace 内创建指向 `tmp/outside-secret.txt` 的 symlink → snapshot() 会把目标内容复制进 snapshot store / 计入 digest
- root cause: snapshot/digest 路径无 symlink 检测
- fix: `workspace_tree_digest()` 跳过 symlink；`snapshot()` 新增 `_reject_symlinks()`，发现 symlink 抛 `PermanentPortError(POLICY_DENIED)` 且不产生快照
- regression coverage: `test_file_backend.py::TestSymlinkRejection`（`test_snapshot_rejects_symlink`、`test_tree_digest_ignores_symlink`；Windows 无特权时按环境条件 skip，CI Linux 实际执行）
- final status: FIXED

### 2.3 MAJOR（延期技术债）

| ID | 问题 | 证据 | 延期目标 | 理由 |
| --- | --- | --- | --- | --- |
| SA-1-M003 | 服务层事件（MANIFEST_FROZEN / RUN_FAILED）经 `service._publish()` 在事务外发布，crash 后丢失 | `packages/application/run_orchestration/service.py::_publish` vs `adapters/sqlite/outbox.py` | M14 | 事件为信息性、不参与状态恢复；单进程边界；M14 PostgreSQL + durable workflow 时全面 outbox 化 |
| SA-1-M004 | `_reservation_refs` 进程内 dict，crash 后预算预留泄漏 | `service.py::__init__` 注释 + `_release_reservation` | M14 | 代码注释已声明跨进程恢复依赖 BudgetLedger 持久化；budget enforcement 本身为已知 P1（M12 清偿） |
| SA-1-M006 | OpenHands 真实对话路径零 deterministic 覆盖：e2e/IG-1 全用 FakeAgentRuntime | `tests/e2e`、`tests/integration` 使用 Fake；`tests/adapters/openhands/test_spike_e2e.py` 为手动 spike | M12 | M12 真实工作流强制走真实 AgentRuntime，届时自然建立 CI 覆盖；付费 LLM 不得成为默认 CI 依赖（AGENTS.md §11） |
| SA-1-M007 | SQLiteWorkflowEngine 无并发 lease 冲突测试（多进程 at-least-once 未验证） | `tests/adapters/sqlite/test_workflow_engine.py` 全串行 | M14 | SQLite 单进程语义（db.py 注释）；M14 PostgreSQL 需要完整并发测试 |
| SA-1-M008 | 用量记录恒为 `LedgerCostStatus.UNKNOWN`，budget enforcement 事实无效 | `run_orchestration/usage_recording.py:21` | M12 | BACKLOG 已登记 P1/M12（usage 归账闭环为 M12 硬 DoD） |
| SA-1-M009 | 生产镜像 `DEFAULT_IMAGE = "research-os-sandbox:m9-sandbox-v1"` 为可变 tag | `adapters/execution/docker_backend.py:57` | M12 | 代码注释已要求生产注入 `name@sha256:<digest>`；M12 composition root 落地时强制；每次 execute 已记录实际 image digest 供 ReproducibilityAudit |

### 2.4 MINOR（记录，可延期）

| ID | 问题 | 位置 | 备注 |
| --- | --- | --- | --- |
| SA-1-N001 | `EvalReport.digest()` 方法体内 inline import（受控循环依赖，已注释） | `packages/domain/eval_result.py:197` | 与 no-inline-imports 规则冲突；循环依赖结构性原因 |
| SA-1-N002 | Memory gate `_evaluate_policy` 在 policy 未注入时默认 ALLOW | `packages/application/memory/gate.py` | 测试环境可接受；生产 composition root 必须注入 |
| SA-1-N003 | `_evidence_from_artifact()` 未填充 `run_id` / `experiment_run_id` | `packages/application/run_orchestration/result_handler.py` | Evidence→ExperimentRun 类型化溯源链断裂（source_ref+artifact_id 提供间接溯源） |
| SA-1-N004 | `Artifact.source_refs: list[str]` 弱引用 | `packages/domain/artifacts.py` | 编译期无法保证 Artifact→ExperimentRun 绑定 |
| SA-1-N005 | `MemoryLifecycleDeps.index: RetrievalIndex \| None` Optional 注入 | `packages/application/memory/lifecycle.py` | 未注入时 delete/deactivate 不同步 index（ghost retrieval 风险） |
| SA-1-N007 | `FakePolicyEvaluator` 默认 ALLOW | `adapters/fakes/` | 测试纪律风险；negative case 依赖显式 set_decision(DENY) |
| SA-1-N008 | IG-1 offline 回归测试使用 Fake 存储（FakeWorkflowEngine/FakeEvidenceLedger） | `tests/integration/test_ig1_phase_runner.py` 等 | 状态机转换真实、存储层 fake；SQLite 序列化/事务由 adapter 测试另行覆盖 |
| SA-1-N009 | `pyproject.toml` 中 `mcp>=1.28,<2` 非精确 pin | `pyproject.toml` | uv.lock 实际 pin 1.29.0+sha256；与 openhands-sdk 兼容性约束有关（文档已解释） |
| SA-1-N010 | `.gitignore` 仅逐文件排除 `.importlinter.sqlite`，无 `*.sqlite` 通配 | `.gitignore` | 遗漏风险低（当前无其他 sqlite 产物入仓） |
| SA-1-N011 | `SqliteWorkflowEngine` 无 context manager 协议（`close()` 需调用方显式 finally） | `adapters/sqlite/workflow_engine.py` | 测试均正确 close；调用方纪律风险 |

### 2.5 调查后无问题（False Positive 记录）

- **SA-1-N006（撤销）**：子代理报告 `docs/INDEX.md` 中 `PRODUCT.md` 链接断链；根代理核实 `docs/PRODUCT.md` 实际存在（106 行 Product Definition），链接有效。INDEX.md 已回滚至原状，不构成 finding。教训：子代理输出必须经根代理以仓库事实复核后才可进入代码变更。

## 3. Fault Injection Evidence

| 注入 | 场景 | 结果 |
| --- | --- | --- |
| cancel/complete race | complete(SUCCEEDED) 后到达 cancel | 修复前：状态被覆盖为 CANCELLED + TASK_CANCELLED 事件（BLOCKER）；修复后：terminal_noop，状态保持 SUCCEEDED，无事件（`test_cancel_after_complete_is_terminal_noop`） |
| complete retry（重复投递） | complete(SUCCEEDED) 后重放 complete(FAILED) | 修复前：抛 InvalidInputError；修复后：dedup noop，状态保持 SUCCEEDED |
| 过期 lease（worker 崩溃） | lease 过期 → recover_expired_leases | 修复后：LEASED→QUEUED 为显式 EXPIRE_LEASE 合法转换，TASK_RETRY_SCHEDULED 事件照常（既有测试保持） |
| symlink 注入 | workspace 内指向工作区外文件的 symlink | 修复后：snapshot 抛 PermanentPortError(POLICY_DENIED)，无快照产生 |
| 孤儿容器（实测环境） | 测试中断残留容器 `research-os-exec-04ccb0945e7d`（Up 36min） | 证实 SA-1-M003 容器孤儿场景真实存在：无自愈机制，需手动 `docker rm -f` 清理后测试恢复 |
| repeated-run soak | 关键可靠性测试（workflow_engine/restart/idempotency/cancel_resume）连跑 3 轮 | 3×38 passed，无 flake |
| DB 事务一致性 | outbox 事件与任务状态同一事务 | 既有 `test_events_are_written_transactionally` 保持通过 |
| restart recovery | 跨 engine 实例 lease 恢复 | 既有 `test_recovery_across_engine_instances` 保持通过 |

## 4. 已修复问题

1. SA-1-B001：`cancel()` 终止态 guard（BLOCKER）
2. SA-1-M001：`complete()` 幂等（MAJOR）
3. SA-1-M002：`EXPIRE_LEASE` 状态机转换 + 文档同步（MAJOR）
4. SA-1-M005：workspace symlink 拒绝（MAJOR，安全）

## 5. 延期技术债

见 §2.3（6 项 MAJOR）与 §2.4（10 项 MINOR）。全部延期项有明确目标里程碑与理由，不阻塞 SA-1 判定。

## 6. 全量回归结果（2026-08-20）

| 门禁 | 结果 |
| --- | --- |
| `validate_bundle.py`（system-spec-check） | PASS（Role/Agent/Model/Team/Task/Protocol 引用一致，MVP Runtime/Security/Governance 边界存在） |
| `validate.py`（governance-check） | PASS（VERSION 单一来源、ALL_PLAN 交叉引用一致、未发现凭据） |
| `run_all_checks.py --profile m0` | PASS：19 deterministic checks（含 python/tests 1665 passed、架构测试、contracts、format、lint、mypy、docs-check、framework/learning evals、release-assets-immutable） |
| IG-1 专项回归（tests/integration + tests/e2e，not requires_live_llm） | 93 passed |
| docker e2e（requires_docker） | 11 passed（清理环境孤儿容器后） |
| 新增/更新回归 | workflow_engine 20 tests、state_machines 全量、file_backend 22 tests 全部通过；symlink 测试在 Windows 无特权环境条件 skip（CI Linux 执行） |
| repeated-run soak | 3×38 passed |
| ruff（修改文件） | All checks passed |
| mypy strict（修改文件） | Success: no issues found |
| 源码规模约束 | `workflow_engine.py` 300 行 ≤ 300（压缩后），其余文件合规 |

## 7. 结论

### Architecture / Security / Reliability / Research Integrity

- **Architecture**：依赖方向（adapter→application→domain）无违规；Protocol→Manifest 双重门禁（compile/preflight FAIL 阻断 + ManifestFreezeError）不可绕过；Role→Skill→Capability→Tool 在 exposure 与 execution 双时机执行 Policy；EvalGate fail-closed 无 always-PASS 路径。核心问题集中在 adapter 层对 domain 状态机的绕过（已修复）。
- **Security**：无硬编码凭据；LLM 与 Tool 凭据域分离（CredentialScope + 禁 token passthrough）；容器 host_config 安全（network none / 非特权 / cap-drop / readonly rootfs / 限额）；workspace symlink 攻击面已封堵；默认 deny 清单保持。
- **Reliability**：at-least-once + idempotency + dedup 在 cancel/complete 竞态下修复后成立；lease 过期收敛为合法状态机转换；outbox 任务级事件事务一致；服务层事件与预算预留的 crash 恢复缺口为已知技术债（M14）。
- **Research Integrity**：ToolResult→Evidence→PROPOSED Claim→VERIFIED 无捷径；Memory 五阶段 gate 无 bypass；矛盾检测将 VERIFIED 降级 DISPUTED 且不提升为 Memory；negative result 有专门类型；derived index 可重建、非 Canonical。provenance 类型化缺口（N003/N004）为 MINOR。

### Test Trustworthiness

- 无全局 skip/xfail；无弱断言主导；无直接构造终态绕过状态机（版本漂移测试为数据构造）；无 always-PASS evaluator；IG-1 回归覆盖矛盾/幂等/版本漂移/phase runner 真实逻辑。
- 已知缺口（均延期）：OpenHands 真实对话路径零 CI 覆盖（M12 清偿）、并发 lease 测试缺失（M14 清偿）、IG-1 offline 测试底层存储为 Fake（由 adapter 层测试互补）。

### Dependency / Supply-chain

- 运行时依赖全部精确 pin（openhands-sdk==1.42.0 + sha256、httpx==0.28.1、tenacity==9.1.4、docker==7.2.0）；mcp 范围约束有锁文件 pin 与文档解释；uv.lock 一致性由 CI `uv lock --check` 强制；CI actions commit-hash pin；全部许可证 SPDX 声明（MIT/BSD/Apache，无 GPL/AGPL）；OpenHands revision lock 与 PyPI digest 可追溯；adapter 隔离无 SDK 类型泄漏。

### Repository / Documentation

- 无死代码/重复实现；markers 与配置一致；`docs/PRODUCT.md` 断链报告为误报（已撤销）；ALL_PLAN/BACKLOG/MILESTONES/Completion Matrix 交叉一致；`.gitignore` 有 `*.sqlite` 通配缺口（MINOR，已记录）。

## 8. 判定

- **BLOCKER：1（SA-1-B001）→ 已关闭**
- 核心质量门（m0 profile 19 项 + IG-1 93 项 + docker 11 项 + soak 3×38）全绿
- M0–M11 Contracts 与 IG-1 保持成立（无语义回退、无测试删除、无权限扩大、无 Fake 替代生产路径、无 canonical truth 迁移）

**SA-1 最终状态：PASS**

**M12 Readiness：READY**

- 阻塞项已清零；修复项均有回归测试锁定；6 项 MAJOR 延期债全部有明确清偿里程碑（M12：M006/M008/M009；M14：M003/M004/M007），不改变 M12 Entry 条件。

> SA-1 停止于此。不自动开始 M12；M12 启动须经用户显式授权并按仓库契约从 Plan Mode 立项。