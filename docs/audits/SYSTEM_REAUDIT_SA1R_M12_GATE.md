# SA-1R — Independent Full-System Re-audit（M12 Entry Gate）

- 日期：2026-08-21
- 范围：对 SA-1（SYSTEM_AUDIT_M0_M11.md）的独立复核；非重新执行 SA-1、非新 Milestone
- 事实优先级：当前代码 / Git diff / Port 契约 / deterministic validation / Fault Injection / 重跑结果 > SA-1 记录与开发窗口判断
- 审计方法：根代理独立复核 + 3 个并行只读子代理（架构/契约、安全、Research Truth/测试可信度）+ 独立 Fault Injection reproduction + 全量质量门重跑

## 1. SA-1 Finding Revalidation Matrix

| SA-1 ID | severity | 独立验证方式 | 结论 |
| --- | --- | --- | --- |
| SA-1-B001 cancel() 覆盖终止态 | BLOCKER | 代码核对 + 独立 reproduction（submit→acquire→complete→cancel） | **FIXED（验证关闭）**：`cancel()` 终止态 guard 在，reproduction 不再成功，回归测试有判别力 |
| SA-1-M001 complete() 非幂等 | MAJOR | 代码核对 + `test_complete_is_idempotent_after_success` 重跑 | **FIXED**：terminated dedup noop 成立 |
| SA-1-M002 EXPIRE_LEASE 状态机 | MAJOR | `task_state.py` + `test_state_machines.py` 重跑 | **FIXED**：LEASED→EXPIRE_LEASE→QUEUED 显式转换存在 |
| SA-1-M005 workspace symlink | MAJOR | `file_backend.py` 代码核对 + 测试（Windows 环境条件 skip，CI Linux 执行） | **FIXED（环境限制）**：snapshot 拒绝 symlink、digest 跳过；本机 Windows 无 symlink 特权按条件 skip，CI ubuntu 真实执行 |
| SA-1-M003/M004/M006/M007/M008/M009 延期 | MAJOR | 代码核对 | 保持延期，均有明确清偿里程碑（M12/M14），不改变 M12 Entry 判定 |
| SA-1-N001..N011 | MINOR | 抽样 | 保持记录；其中 N003（evidence run_id 未填充）为类型化溯源缺口，维持 MINOR |

**SA-1 判定复核结论**：SA-1 的 BLOCKER 直接修复本身正确（B001 guard 在 task_id 调用面上有效），但**覆盖不完整**——发现了 SA-1 遗漏的两个同根因状态机缺口（见 §2），说明 SA-1 的"取消语义"审计仅覆盖了 adapter 单方法，未验证 service 层调用面与 lease 重放面。

## 2. 新发现 BLOCKER（已修复）

### SA-1R-B001 — `cancel_run(run_id)` 对生产路径完全无效

- subsystem: `packages/application/run_orchestration/service.py` + `adapters/sqlite/workflow_engine.py`
- evidence: `service.cancel_run` 把 `command.run_id`（run 标识）直接传入 `workflow.cancel(task_id)`；SQLite 的 `cancel()` 按 `task_id` 查询。run_id 与 task_id 不相同（fixture: run=`a1b2c3d4-…`, task=`6f8f56a0-…`），取消永远查不到任务
- reproduction（独立脚本）: submit→acquire→`service.cancel_run(CancelRunCommand(run_id=task.run_id))` → 修复前任务保持 LEASED、lease 仍在、cancelled=0
- root cause: Port 契约只有 `cancel(task_id)`，service 层用 run_id 调用而实现按 task_id 匹配；语义错配被测试掩盖——既有测试 `test_cancel_after_submit_marks_task_cancelled`/`test_double_cancel_is_idempotent`/F-10 全部用 `CancelRunCommand(run_id=task.id)`（task.id 冒充 run_id）通过
- 影响: 用户取消 run 实际无效，任务继续运行（协作式取消信号丢失），且存在"运行中任务无法终止"的运行时风险
- fix: Port 新增 `cancel_run(run_id) -> int`；SQLite 实现按 run_id 扫描任务取消（跳过终止态，状态+事件同事务）；Fake 同步；service 改调 `cancel_run`；既有 5 处测试改用真实 run_id
- regression coverage: `tests/adapters/sqlite/test_workflow_cancel_run.py`（全部取消/跳过终止态/幂等/未知 run）；contract suite 双实现参数化 `test_workflow_cancel_run_reaches_all_tasks`
- final status: FIXED

### SA-1R-B002 — 终止态任务可被重新租约复活（cancelled-but-completed / completed-but-retried）

- subsystem: `adapters/sqlite/workflow_engine.py` / `adapters/fakes/workflow_engine.py` 的 `acquire_lease`
- evidence: `acquire_lease` 不检查任务状态；`cancel()` 删除 lease 后，重复投递（at-least-once 重放）可再次 acquire → 状态从 CANCELLED 回写 LEASED → 再 complete(SUCCEEDED) → 最终 `status=SUCCEEDED, cancelled=1`，outbox 同时含 TASK_CANCELLED 与 TASK_COMPLETED——与 SA-1-B001 同类的 canonical-state 矛盾，SA-1 修复未覆盖 lease 重放面
- reproduction（独立脚本）: submit→acquire→cancel→acquire→complete → 修复前 SUCCEEDED+cancelled=1 矛盾状态
- root cause: lease 获取路径缺少终止态守卫，domain 状态机（terminal 无出边）未被 adapter 执行
- fix: `acquire_lease` 前置检查 `status in terminal()` → `InvalidInputError`；Fake 同步对齐（cancelled/completed 拒绝）
- regression coverage: `test_acquire_after_cancel_raises` / `test_acquire_after_complete_raises` / `test_acquire_after_fail_raises`；contract suite `test_workflow_acquire_after_cancel_is_rejected` / `test_workflow_acquire_after_complete_is_rejected`
- final status: FIXED

## 3. Architecture Re-audit（子代理 A + 根代理复核）

- 依赖方向：`packages/domain` 0 外部 import；`packages/application` 0 个 `import adapters`、无 SDK 类型；adapter→application→domain 方向合规（.importlinter 生效，CI 强制）
- 核心契约链唯一性：Protocol→Preflight→Manifest→Run、Role→Skill→Capability→Tool、Experiment→Execution→Run→Metric→Artifact、Source→Evidence→Claim→Memory、Eval 链均无 duplicate model / shadow repository / parallel service
- Port 契约：WorkflowEngine 双实现（Fake/SQLite）语义差异点已收敛（本审计新增 cancel_run 与终止态 lease 拒绝为双实现一致行为）
- 结构约束：全仓 0 文件超 300 行（SA-1R 修复后 `workflow_engine.py` 292 行）
- 结论：无 SA-1 修复引入的架构破坏

## 4. Reliability / Recovery Re-audit（子代理 A + Fault Injection）

| 注入 | 结果 |
| --- | --- |
| cancel 后重放 acquire（SA-1R-B002） | 修复后拒绝，无复活 |
| run 级取消（SA-1R-B001） | 修复后到达全部任务 |
| cancel/complete 竞态（B001 原场景） | terminal_noop 保持 |
| 过期 lease 恢复 | LEASED→QUEUED 显式转换，事件照常 |
| outbox 事务性 | 与任务状态同事务（既有测试保持） |
| restart recovery | 跨实例恢复通过 |
| 3 轮 soak | 3×75 passed，无 flake |

- 已知延期债（不阻塞）：M003 服务层事件非事务（M14）、M004 预算预留进程内（M14）、M006 OpenHands 真实对话零 CI 覆盖（M12）、M007 并发 lease 测试缺失（M14）、M008 usage UNKNOWN（M12）、M009 镜像可变 tag（M12）

## 5. Security Re-audit（子代理 S）

- Capability 双门禁：exposure-time fail-closed；execution-time 门禁存在但生产接线缺失（S-FIND-01/03/04）——当前生产唯一 direct-tool 通道是 OpenHands Policy Wrapper，`execute_tool_call`/`require_frozen_tool_set` 仅测试调用。**归类为 MAJOR 延期债（M0 上线前必须接线），当前无实际绕过**（无生产调用点，非 BLOCKER）
- S-FIND-02（tool 名当 capability 求值）、S-FIND-05（provider collision）、S-FIND-07（CredentialScope 声明式）、S-FIND-08（redaction 正则缺口）：MAJOR 记录，均无当前可执行绕过（无 production bypass 证据）
- Workspace/Execution：路径防护、symlink 拒绝、容器 host_config（network none/非特权/cap-drop/readonly/tmpfs 限额）全部成立；restore/merge 不重查 symlink 与 TOCTOU 为 MINOR（S-FIND-09）
- Secret：全仓无硬编码凭据、无意外 secret 文件；LLM↔Tool 凭据域分离为声明式但实现侧分离（不同 resolver 域）
- 结论：无实际 authority bypass；S-FIND-01/03/04 构成 M0 接线前的 enforcement 缺口（MAJOR 延期）

## 6. Research Truth / Provenance Re-audit（子代理 R）

- ToolResult≠Evidence、Agent Output≠Verified Claim、Reviewer≠Truth、Derived Index≠Canonical：边界成立（唯一 VERIFIED 赋值点 `verification.py:59`，前置 evidence 解析检查）
- Memory gate：pipeline 无 bypass；**policy 未注入默认 ALLOW（fail-open）**（R-FIND-3）——生产 composition root 未构造 MemoryGateDeps；归类 MAJOR 延期债（M12 composition root 落地时强制注入，与 SA-1-N002 一致）
- Negative result：NEGATIVE_RESULT 为科学终态、可入证据链、可 REFUTES Claim；**Scientific Negative Result != System Failure 成立**
- EvalGate fail-closed：compute_verdict 任一 FAIL→BLOCK；CI gate `min_pass_ratio=0` + 无 rules 为弱化配置（潜在 always-PASS 通道）——当前 datasets 每个 case 有 scorer_ref 使 FAIL 仍被检出；归类 MAJOR（M11 CI gate 需配置真实阈值与 rules）
- N005（delete 后 index ghost）维持开放 MINOR

## 7. Test Trustworthiness（子代理 R）

- skip/xfail：0 xfail；7 处 skip 均为环境能力（docker daemon/symlink 权限），非掩盖
- SA-1 新增回归判别力：B001 测试有判别力（旧实现下断言必失败）；`test_cancel_before_complete_cancels` 中 `result_summary is None` 断言无判别力（对照组，真正判别在 complete 抛错）
- 生产路径覆盖缺口（维持延期）：无真实 EvidenceLedger/MemoryStore/PolicyEvaluator 实现（仅 Fake）；IG-1 offline 链使用 Fake 存储；真实 docker 链测试不进 VERIFIED 升级路径
- **测试纪律问题（SA-1 期间引入）**：既有 5 处取消测试用 `run_id=task.id` 掩盖语义错配（本审计已全部修正为真实 run_id）

## 8. Supply-chain / Repository

- openhands-sdk==1.42.0（uv.lock 一致，.venv 实测 1.42.0，UPSTREAM_COMPONENTS.yaml digest 一致）；docker==7.2.0/httpx==0.28.1/tenacity==9.1.4 精确 pin；mcp 范围约束有锁文件 pin 与文档解释；`uv lock --check` 通过
- CI：quality/eval-gate/container-quality 三 job，actions commit-hash pin，ubuntu+windows 矩阵
- 文档一致性：validate_bundle / governance-check / docs_consistency_check 全 PASS；MILESTONES / COMPLETION_MATRIX / Completion Records / SA-1 记录与代码一致；未改写任何历史记录

## 9. Quality Gate（SA-1R 重跑）

| 门禁 | 结果 |
| --- | --- |
| run_all_checks.py --profile m0（19 项） | 18 PASS；python/tests=1 项失败为**本机无 docker daemon**（17 项 docker e2e ERROR/FAILED，CI ubuntu container-quality job 执行；SA-1 记录在 Linux 环境 11 passed） |
| mypy strict | Success: no issues found（371 files） |
| ruff check / format | All checks passed / 376 files formatted |
| 非 docker 全量 pytest（-m "not requires_docker and not requires_live_llm"） | 1076 passed |
| IG-1 专项（tests/integration + tests/e2e 非 docker） | 91 passed |
| soak | 3×75 passed |
| validate_bundle.py / validate.py / docs_consistency_check | PASS |

**docker e2e 在本环境标记 NOT VERIFIED（环境原因），不视为 PASS；CI Linux 门禁覆盖。**

## 10. 判定

- SA-1 全部 BLOCKER：独立验证关闭（B001）
- 新发现 BLOCKER：2（SA-1R-B001/B002）→ 已修复并锁定回归
- 高风险 MAJOR：SA-1 延期 6 项保持（有清偿里程碑）；本审计新增 MAJOR（execution-time 门禁接线、Memory gate fail-open 默认、CI eval gate 弱化配置）均为**无当前可执行绕过的接线/配置缺口**，不改变 M12 Entry 判定，列为 M0 接线与 M12 清偿项
- Security / Reliability / Research Truth 边界：成立（无实际 bypass）
- 核心 production integration chain：非 docker 全链真实执行通过（SqliteWorkflowEngine 真实存储 + gate 真实逻辑）
- 测试判别力：SA-1 回归测试有判别力；既有取消测试的语义掩盖已修正

**SA-1R 最终状态：PASS（条件通过——docker e2e 依赖 CI Linux 环境，本机 NOT VERIFIED）**

**M12 Entry：READY**

- 阻塞项清零；SA-1R 修复项均有回归测试与 contract suite 锁定；M12 启动仍须按仓库契约从 Plan Mode 立项并经用户显式授权。