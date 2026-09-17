---
id: RECHECK-20260915-083
plan_id: PLAN-20260915-083
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-18
completed_at: 2026-09-18
reviewer: root-agent-goal-003-cycle20
baseline_ref: 405d327
checked_head: 405d327+worktree
---

# RECHECK-20260915-083 — 重启后的续跑入口（GOAL-003 cycle 20）

## 检查范围

PLAN-20260915-083 声称的交付面：① 装配来源成为 run 的 canonical 事实
（`ProtocolSource` 值对象 + `ResearchRun.protocol_source` + 两个 run store 编解码 +
`POST /runs` 与队列派发同源登记）；② 重启后按来源**重建**执行上下文并续跑
（`rebuild_and_resume` = 解析来源 → 同一条装配链 → 编译/预检 → `resume_rebuilt`）；
③ 剩余工作按**稳定身份**重算（新读面 `WorkflowEngine.task_identities` + 已成功的不重跑）；
④ 冻结语义校验不放宽（digest 不符 / 目录漂移一律拒绝，一次都不执行）；
⑤ 修掉"语义 digest 从不过 HTTP 边界"的真缺陷；⑥ 两个入口（`POST /runs/{id}/resume`
与 `RetryDispatchScheduler`）共用同一条重建链。

**未覆盖**（见告警）：失败收敛分支与 `manifest.frozen` 事件 payload 仍不带语义 digest；
来源必须可解析（协议文件/草稿修订仍在）；两个入口的拒绝语义有意不同。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 来源是 durable 事实（AC-01） | SQLite 用例 3：store 往返、**逐次状态迁移不丢**、草稿来源往返且旧行留空；PG 用例 1：JSONB 往返同判据；API 用例：`POST /projects/{id}/runs` 后从 `runs_store` 读回 `protocol_source == ProtocolSource(protocol_path=…)` | PASS |
| 重启后真的能续跑（AC-02） | e2e 全回路（真 SQLite + 真 run store + 注入时钟）：停车（`PAUSED`，runtime 执行 1 次）⇒ **换一个新的 service**（进程内暂存为空、`has_paused_context` 为假）⇒ 按来源重建 ⇒ run `SUCCEEDED`、runtime 共 **2 次**、断点任务 `attempt=2` | PASS |
| 剩余工作重算正确（AC-03） | e2e：断点落在第二个任务 ⇒ 第一个任务只执行 **1 次**（已 `SUCCEEDED` 的不重发）、第二个走第二次尝试。**这条是跑出来的**：第一版按 `succeeded_task_keys` 重算 ⇒ 解析出的新 task id 被引擎按 idempotency key 判为"已存在"⇒ run 收敛 `FAILED`（`assert 'FAILED' == 'PAUSED'`）；改为 `task_identities` 回答 canonical id 后通过 | PASS |
| 重建不放宽（AC-04） | e2e 2：冻结 digest 不符 ⇒ 拒绝；目录漂移（语义 digest 变化）⇒ 拒绝——两者都**一次都不执行**、run 状态不变 | PASS |
| 没有入口就诚实说（AC-05） | API 2：无登记来源 ⇒ `continuation=NONE` + note 点名 `no recorded protocol source`；编排服务缺席 ⇒ `not configured`；resume 路由另一例：来源不可解析 ⇒ note 点名缺的是 `frozen manifest digest`（拒绝原因**具体到缺哪条事实**）。守护线程 2：来源缺失的 run 不进入候选（不翻转 canonical 状态）；重建被诚实拒绝 ⇒ run 放回 `PAUSED` | PASS |
| 语义 digest 过 HTTP 边界（AC-06） | API 用例（`console_demo_research_v1.yaml` 跑完的真实链路）：run `SUCCEEDED`、`manifest_semantic_digest` 非空且**不等于** manifest digest（语义 digest 排除冻结时刻）。缺陷本体：`RunOutcome` 此前不带该字段，`run_from_execution` 于是从不落它 | PASS |
| 门禁与记录（AC-07） | 定向 **23 passed**（e2e 4 + API 5 + SQLite 3 + PG 2 + ops/调度 9）；受影响的广套件 `tests/application tests/api` **1005 passed / 1 skipped**（2:36）；宽口径 `tests/application+adapters+domain+e2e+postgres+contracts` 收集 **2022** 项 ⇒ **2015 passed / 7 skipped**（4:52，命令原文写在 `scratch/goal3-cycle20-wide2.log` 头）；mypy **894 source files clean**；ruff check 全过、ruff format --check **904 files** already formatted；m0 = **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3759 passed / 10 skipped**，478.71s）；RECHECK-083 + MEM-058 + GOAL 记账 + ALL_PLAN 行 | PASS |

## 告警

- **W-1（失败收敛分支仍丢语义 digest，已量成事实）**：`run_from_execution` 的
  `ValueError` 分支只恢复 manifest digest 与定价引用（`frozen_manifest_refs_of`），
  语义 digest 不在其中；API 用例里那个收敛到 `FAILED` 的 run 行有来源、有 manifest
  digest、**没有语义 digest**。影响面：终态 `FAILED` 的 run 不可 resume/fork，
  不在本轮的交付路径上；但"run 行完整记录冻结语义"这件事对失败 run 不成立。
- **W-2（`manifest.frozen` payload 不带语义 digest）**：重建路径只读 run 行（不读事件），
  所以不阻塞本轮；代价是"从事件链重放 run 行"补不齐这项——跨进程只有 run 行一处权威。
- **W-3（重建的输入是外部文件）**：来源可解析（协议文件仍在 / 草稿修订仍在）是重建的
  前提，来源消失即拒绝——有意的诚实边界（不猜协议、不换一份协议），但意味着
  "重启后能续跑"依赖那份文件的可获得性，不是纯自足。
- **W-4（两个入口的拒绝语义有意不同）**：API 面保持既有文档口径（解除暂停、不伪造
  续跑、**不动 canonical 状态**），守护线程则把 run **放回 `PAUSED`**（它一个任务都没
  执行，留 `RUNNING` 就不是事实）。差异的成因写在 `scheduler._resume` 的 docstring 里，
  读面仍无法区分"这个停车 run 曾经重建失败过"。
- **W-5（`task_identities` 只回答带 idempotency key 的任务行）**：与 SQL 侧
  `idempotency_key IS NOT NULL` 同义；无 key 的历史任务行会被当成"新任务"重发。
  当前会话任务的 key 只在一个地方生成（`run:phase:agent`），所以只是适用边界。
- **W-6（探针口径）**：收口前的数字来自 `scratch/goal3-cycle20-probe1-restart-loses-the-plan.py`
  （真实 `SqliteWorkflowEngine`，非 mock）与它的 `-before.txt`；脚本写于改造前，只能量
  "现状"，量不了新路径——收口后的数字由 e2e 用例承担（同一条链、真实现）。脚本与日志
  在 `scratch/`（gitignored），输出原文抄进 PLAN 的证据段与本文件。
- **W-7（首轮 m0 红：3 条真实规模门禁 + 13 条环境干扰）**：第 1 轮 m0 的
  `python/tests` 红。真实项是 `test_python_source_size_limits` 命中本轮的三个文件
  （`rebuild_and_resume` 57 行、`scheduler.py` 462 行、e2e 一个用例 51 行）——
  **处置是改代码而不是改门禁**：拆出 `_resume_from_source`、把"被拒 ⇒ 异常"的翻译与
  `RebuildRefused` 挪进 `run_resume.py`、e2e 抽出 `_two_task_harness()`；环境项是
  **我 kill 掉上一轮 m0 留下的孤儿 pytest 进程**导致的（docker/GPU 的"无残留容器"
  断言 8 条、PG 死锁与网络分区时序 5 条），终止孤儿进程后复跑即绿。教训：kill 掉
  后台 m0 不等于停掉它起的子进程，复跑前要先确认环境干净。

## 结论

cycle 18/19 让"重排未到期"把 run 停 `PAUSED` 并由**本进程**的守护线程按时续跑，但两者
都建立在进程内那份 `RunContext` 上——探针量出重启后 `has_paused_context=False`、
`resume_paused` 抛 `InvalidInputError`、守护线程派发 0，已到期的重排**没有任何交付入口**。
本轮把续跑从"看进程运气"变成"看 durable 事实"：装配来源落 canonical、按来源重建上下文、
剩余工作按稳定身份重算、冻结语义校验不放宽、两个入口共用同一条重建链，并顺带修掉
"语义 digest 从不过 HTTP 边界"这个一直存在但从未被触发的缺陷。

结果为 **PASS_WITH_WARNINGS**：W-1/W-2 是同一件事的两处（失败 run 与事件 payload 的
语义 digest），W-3…W-6 是适用范围与口径的如实登记。**未宣称"任何 run 重启后都能续跑"**：
没有登记来源的旧 run、来源已消失的 run 都会被诚实拒绝，且拒绝原因具体到缺哪条事实。
