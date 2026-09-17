---
id: PLAN-20260915-083
slug: durable-resume-entry
title: 重启后的续跑入口：装配来源落 canonical + 按来源重建上下文续跑
status: DONE
created_at: 2026-09-18
updated_at: 2026-09-18
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 20（预算内最后一轮）= cycle 19（PLAN-20260915-082）「下一轮输入」第一项（重启后的续跑入口）。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」+ 2026-09-17 用户拍板恢复条件②（显式变更 budget.max_cycles 10→20 并置回 ACTIVE）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-083-durable-resume-entry.md
memory_entries:
  - MEM-20260915-058
---

# PLAN-20260915-083 — 重启后的续跑入口（GOAL-003 cycle 20）

## 目标

cycle 18 把"重排未到期"的失败变成停车（`PAUSED` + 交回 specs），cycle 19 补上守护线程
按时续跑——但两者都建立在**本进程内存里那份执行上下文**（`RunContext` + 剩余 specs）之上。
derive 探针 `scratch/goal3-cycle20-probe1-restart-loses-the-plan.py` 把重启后的实况量成事实：

```text
1) 停车：run=PAUSED runtime 执行 1 次
2) durable 任务行：[('sort_analysis_execution', 'RETRY_SCHEDULED', 1)]（计划里 2 条 specs）
   事件：manifest.frozen / task.created / task.leased / task.retry_scheduled
   进程内暂存以外，durable 有没有"还剩哪些 specs"的记录：没有
3) 重启后 has_paused_context = False
   resume_paused 抛 InvalidInputError: no paused execution context for run …
4) 重启后守护线程一次 pass：派发 0 个
5) 结论：这条已到期的重排在重启后**没有任何交付入口**
```

所以本轮把"重启后还能不能续跑"从"看进程运气"改成"看 durable 事实"。

## 口径

1. **来源是 run 的 canonical 事实**：`ResearchRun.protocol_source`（路径 xor 草稿修订，
   复用队列已用的 `ProtocolSource` 值对象），`POST /runs` 与队列派发在启动作业时登记；
   来源是唯一的重建入口——没有它**必须拒绝**，不猜协议、不换一份协议。
2. **重建走同一条装配链**：来源解析 → 目录/项目合并 → preflight 上下文 → 编译/预检
   （复用 `execution_inputs`，与 `POST /runs`/队列派发同源），不建第二套"简化版启动"。
3. **冻结语义校验不放宽**：重建的上下文必须过 `assert_semantics_frozen`（plan/catalog/
   契约/定价漂移一律拒绝）+ manifest digest 一致；顺带修掉一个真缺陷——**语义 digest
   此前根本没有过 HTTP 边界**（`RunOutcome` 只带 manifest digest 与定价引用，
   `run_from_execution` 因此从不落语义 digest），所以任何 API 启动的 run 都过不了
   resume 的漂移校验（旧路径走 `resume_paused`，恰好绕开了这项检查）。
4. **剩余工作按稳定身份重算**：`resolve_sessions` 每次解析都生成**新 task id**，只有
   idempotency key（`run:phase:agent`）稳定 ⇒ 新增读面 `task_identities` 把解析结果对齐
   回 canonical 任务（已成功的不重跑，其余换成 canonical task id 才能被 acquire）。
5. **两个入口共用**：`POST /runs/{id}/resume`（重启后人工续跑）与
   `RetryDispatchScheduler`（重启后无人值守续跑）走同一个 `rebuild_and_resume`。
6. **顺序不变**：先迁 canonical（`PAUSED → RUNNING`）并落库，再续跑（cycle 19 的教训：
   协作式暂停谓词读的就是 canonical 状态）。重建被诚实拒绝时：API 面保持"解除暂停、
   不伪造续跑"的既有语义（不动状态，只把原因说清楚），守护线程则把 run 放回停车状态
   （它本来就是在找活干，一个任务都没执行就不该留下 RUNNING）。

## 范围

- Domain：`packages/domain/protocol_source.py`（新增共享值对象）+ `ResearchRun.protocol_source`
  （含 `transition`/`with_manifest` 的逐字段复制、`with_protocol_source`）；
  `experiment_queue.py` 保留 `QueueProtocolSource` 别名（调用点与持久化行零改动）。
- 端口与 adapter：`WorkflowEngine.task_identities`（Fake/SQLite/PG 同判据）；
  run store 编解码（SQLite `run_json` + PG JSONB）落地来源。
- 应用层：`StartRunCommand.protocol_source`；`RunOutcome.manifest_semantic_digest`（回填）；
  `RunOrchestrationService.resume_rebuilt` + `_remaining_specs` + `_assert_resumable`。
- API 面：`services/api/run_resume.py`（`rebuild_and_resume` + `ResumeAttempt`）、
  resume 路由的 `REBUILT` 口径、`run_from_execution` 落语义 digest 与来源、守护线程接线。
- 用例：e2e 4（重启续跑 / 不重跑已完成 / digest 不符拒绝 / 漂移拒绝）、
  API 4（来源落库 / 重建被拒原因 / 无来源 / 服务缺席）、
  SQLite 3（来源往返与迁移保留 / 草稿来源 / 身份读面）、PG 2（同判据 parity）。
- 文档：`docs/api/CONTROL_PLANE_API.md` 的 resume 口径。
- **不改**：run 状态机、schema（无新表：来源与语义 digest 落在既有 run 行 JSON 里）、
  claim 语义、cycle 18/19 的停车/派发机制、未用依赖。

## 验收条件

- [x] AC-01 **来源是 durable 事实**：`POST /runs` 启动的 run 行带上来源（API 用例读回）；
  路径与草稿两种来源都能落库往返，状态迁移不丢；早于登记的旧行显式留空。
- [x] AC-02 **重启后真的能续跑**：e2e（真 SQLite + 注入时钟）——停车 ⇒ 换新 service
  （进程内暂存为空）⇒ 按来源重建 ⇒ `SUCCEEDED`、runtime 执行 2 次、断点任务 `attempt=2`。
- [x] AC-03 **剩余工作重算正确**：已成功完成的任务不重跑（断点落在第二个任务时，
  第一个任务只执行 1 次、第二个走第二次尝试）。
- [x] AC-04 **重建不放宽**：冻结 digest 不符 ⇒ 拒绝；目录漂移（语义 digest 变化）⇒ 拒绝；
  两者都**一次都不执行**、不改 run 状态。
- [x] AC-05 **没有入口就诚实说**：run 没有登记来源 ⇒ 拒绝并点名"no recorded protocol
  source"；编排服务缺席 ⇒ 拒绝"not configured"；两个入口（API/守护线程）口径一致。
- [x] AC-06 **重置语义 digest 的边界缺陷**：`RunOutcome` 带上语义 digest，
  `run_from_execution` 落库（此前 HTTP 边界静默丢弃 ⇒ 任何 API 启动的 run 都过不了
  漂移校验）。
- [x] AC-07 **门禁与记录**：m0 23 项 + 定向套件 + RECHECK-083 + MEM-058 +
  GOAL cycle 20 记账（含收口评估）+ ALL_PLAN 行。

## 实施清单

- [x] WP-A 来源事实：domain + 命令 + 装配 + 两个 run store 编解码 + 用例
- [x] WP-B 重建路径：`task_identities` 读面（3 adapter）+ `resume_rebuilt` + `run_resume`
  + 路由/守护线程接线 + 语义 digest 回填 + 用例
- [x] WP-C 收口：宽口径 + m0 + 记录（含 GOAL 收口评估）→ commit → push → CI

## 证据

```text
探针（scratch/goal3-cycle20-probe1-restart-loses-the-plan.py，真实 SqliteWorkflowEngine）
  收口前（scratch/goal3-cycle20-probe1-before.txt）：重启后 has_paused_context=False、
    resume_paused 抛 InvalidInputError、守护线程派发 0、任务行只有断点那条
  ⇒ 收口后由 e2e 用例承担同一条链（换新 service + 按来源重建 ⇒ SUCCEEDED、执行 2 次）

定向 23 passed：e2e 4（重启续跑 / 不重跑已完成 / digest 不符拒绝 / 目录漂移拒绝）
  + API 5（来源落行 / 成功 run 的语义 digest 过边界 / 重建被拒原因 / 无来源 / 服务缺席）
  + SQLite 3（store 往返与迁移保留 / 草稿来源与旧行 / 身份读面）
  + PG 2（身份读面 parity / 来源 JSONB 往返，实跑非 skip）
  + ops/调度 9（3 条新增：无上下文按来源重建续跑 / 重建被拒放回 PAUSED / 无来源不进入候选）

受影响的广套件 tests/application tests/api：1005 passed / 1 skipped（2:36）
宽口径 tests/application+adapters+domain+e2e+postgres+contracts：收集 2022 项 ⇒
  2015 passed / 7 skipped（4:52；命令原文写在 scratch/goal3-cycle20-wide2.log 头）
mypy：894 source files clean；ruff check 全过、ruff format --check 904 files already formatted
m0：第 1 轮 python/tests 红（3 条**真实**规模门禁 + 13 条环境干扰，见下）⇒ 修后第 2 轮
  **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3759 passed / 10 skipped**，478.71s）

第 1 轮 m0 的两类红（如实分开记）：
  ① **真实**——`tests/tooling/test_python_source_limits.py`：
     `services/api/run_resume.py` 的 `rebuild_and_resume` **57 行**（>50）、
     `services/api/scheduler.py` **462 行**（>450 硬上限）、
     e2e 的 `test_already_finished_work_...` **51 行**（>50）。
     处置：**按门禁要求改代码，不动门禁**——`rebuild_and_resume` 拆出
     `_resume_from_source`；重建续跑的"被拒 ⇒ 异常"翻译与 `RebuildRefused` 挪进
     `run_resume.py`（调度器不再自持一份）；e2e 用例抽出 `_two_task_harness()`。
  ② **环境**——我 kill 掉上一轮 m0 时留下的**孤儿 pytest 进程**仍在跑：docker/GPU
     用例的"无残留容器"断言 8 条（残留 `research-os-exec-*` 是那次 kill 造成的）、
     PG `DeadlockDetected`/跨进程与网络分区时序 5 条。处置：查明 PID（创建时间
     14:04 = 被 kill 的那轮）后终止孤儿进程、确认 `research-os-exec-*` 容器为 0，
     再复跑（复跑前先确认环境干净，不是重试掩盖）。
```

## 影响报告

- **Domain/API/schema**：Domain 多一个字段（`ResearchRun.protocol_source`，可空）与一个共享
  值对象（`ProtocolSource`，队列侧旧名保留别名）；`RunOutcome` 多一个可空字段；
  **没有新表、没有新路由**；`POST /runs/{id}/resume` 多一个 `continuation=REBUILT` 取值
  与更明确的 `note`（既有 `RESUMED`/`NONE` 取值不变）；`WorkflowEngine` 端口多一个只读方法
  （三个 adapter 同步）。
- **安全/凭据**：无变化；重建路径不接触任何凭据字面量（凭据仍从既有 credentials 面解析）。
- **兼容性/迁移风险**：① 旧 run 行没有来源 ⇒ 重建拒绝（诚实，不猜）——这正是 cycle 20
  之前所有 run 的状态；② `run_json`/JSONB 里多一个键（`protocol_source`），旧行读回为
  None；③ 语义 digest 现在会落库 ⇒ 之前被 `snapshot_migration` 判为"legacy 快照"的
  新 run 不再被误判（历史行不受影响）；④ API 启动 run 的 `research_run_json` 体积略增。
- **可观测性**：重建失败一律不静默（API `note` 点名原因、守护线程跳过并留痕）；无新增
  指标。
- **上游版本影响**：无新依赖、无版本 pin 变更。
- **遗留边界（如实登记）**：`RunOutcome` 的 ValueError 收敛分支仍不落语义 digest
  （本轮用 API 用例把这条边界量成事实：该夹具的 m12 run 收敛 `FAILED`，行上有来源与
  manifest digest、没有语义 digest；该 run 已终态，resume/fork 都不可能）；`manifest.frozen`
  事件 payload 仍只带 manifest digest（语义 digest 不在事件里，跨进程只能靠 run 行）；
  重启后的续跑要求来源可解析（协议文件/草稿修订仍在），来源消失即拒绝。
- **下一项任务**：GOAL 收口评估（EC 全 PASS + 预算触顶 ⇒ 用户决定收口或续期），
  未处理长程项：`failure_policy` 零消费者、锁粒度（每线程连接）、「按声明给 adapter 接线」
  （受控出网，需用户/ADR）、读面区分两种 `PAUSED`。

## 状态历史

- 2026-09-18 创建（IN_PROGRESS）：derive 用探针量出重启后没有任何交付入口 + 语义 digest
  从不过 HTTP 边界两个事实，圈定本轮 = 来源落 canonical + 重建装配 + 稳定身份重算。
- 2026-09-18 收口（DONE）：AC-01…AC-07 全达成，RECHECK-083 = PASS_WITH_WARNINGS
  （W-1 失败收敛分支与 W-2 事件 payload 的语义 digest、W-3 来源可解析、W-4 两个入口拒绝
  语义有意不同、W-5 身份读面只回答带 key 的行、W-6 探针口径）。两处实现期的返工如实
  记在 RECHECK 的检验列：① 剩余工作第一版按新解析的 task id 重算 ⇒ 被引擎按
  idempotency key 判重 ⇒ run 收敛 FAILED（e2e `assert 'FAILED' == 'PAUSED'` 抓出），
  改成 `task_identities` 回答 canonical id；② `run_from_execution` 构造 run 实体时漏传
  语义 digest（API 用例 `stored.protocol_source is None` 暴露），补 `RunOutcome` 字段后
  两个字段同时落库。③ m0 首轮红于 3 条**规模门禁**（50 行函数 / 450 行文件），按门禁
  要求拆函数与挪模块（未动门禁），复跑 23/23。
