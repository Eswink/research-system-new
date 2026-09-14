---
id: RECHECK-20260915-048
plan_id: PLAN-20260914-048
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-15
completed_at: 2026-09-15
reviewer: root-agent-gate-evidence
baseline_ref: 10dc459
checked_head: working-tree (pre-commit)
---

# RECHECK-20260915-048 — pause/resume 派发协调独立复检

GOAL-20260912-001 cycle 8（EC-04 第三批）派生计划的复检。本 cycle 的关键语义决定是
**暂停事实只存一份**：`runs` 行的 canonical state 就是暂停信号，派发面（`claim_next`）
与执行器谓词都读它，不引入第二个标志位（避免状态漂移）。复检以「三层可证伪断言 +
本地全门 + CI 终态」为权威证据，重点对抗核查三处诚实性：暂停不撤销在途租约、
"恢复"不伪装成"续跑"、夹具不产生"绿而不真"的派发断言。

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260914-048-pause-resume-dispatch-coordination.md`
  （`parent_goal: GOAL-20260912-001`，EC-04 第三批）。
- 变更范围：Port `workflow_engine.py`（`run_state` + claim 文档语义）；三实现
  `adapters/{sqlite,postgres,fakes}` 的 claim 过滤与 `run_state`；
  `adapters/sqlite/db.py`（`RUNS_SCHEMA_SQL` 单一来源）与 `run_store.py` 复用；
  `phase_runner.py`（`pause_requested` + 边界暂停）；`service.py`（谓词/暂存/续跑）；
  `services/api/routers/approvals.py`（pause/resume/interventions）；夹具
  `tests/api/run_fixtures.py`（补 `runs_store`）；前端 `RunActionButtonRow.tsx` /
  `navigation/pageSupport.ts`；docs 三处；openapi 再生；新增测试 19。
- 边界：不做抢占式中断（不撤销租约）、不做跨进程暂停上下文持久化、不新发 outbox
  事件类型；实验队列与 memory capability policy（G16）属后续 cycle。

## 检查结果

| AC | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| AC-01（WP-A） | 三实现 `claim_next` 跳过 PAUSED run；解除后恢复；在途租约不受影响；未知 run → None | `pytest -q tests/contracts/test_pause_dispatch_contract.py` = 9 passed（3 用例 × Fake/SQLite/PG，PG 实连测试容器） | PASS |
| AC-02（WP-B） | 暂停信号为真时零任务执行、返回 PAUSED、剩余 specs 交回、不发 RUN_COMPLETED | `pytest -q tests/application/test_pause_coordination.py` = 5 passed（含"信号恒假仍正常完成"的对照与"第一组后翻转"的边界语义） | PASS |
| AC-03（WP-C） | 409/404 守卫；暂停后 claim 为 None、恢复后可认领；`continuation=NONE` 诚实；interventions 同实现；web 门全绿 | `pytest -q tests/api/test_pause_resume_api.py` = 5 passed；`pnpm --dir apps/web lint`（--max-warnings 0）+ `typecheck` + unit(73) 绿；stub e2e 34/34；live e2e 17/17 | PASS |
| AC-04（WP-D） | 本地全门 + m0 + CI 终态 | 全量 pytest 3319 passed/6 skipped/0 failed（DSN 固化）；m0 23/23 PASS；ruff check/format + mypy 绿；CI run 见状态历史 | PASS |

## 警告与处置

1. **W-1（WARNING，既有，非本 cycle）** collector-quality 仍是 RECHECK-042/043/044/045/046/047
   登记的**同 2 项** timing flake；其余 job 终态见 GOAL 迭代日志。按 fix_policy 不放宽
   断言、不 skip、不改 workflow（治理面）。
2. **W-2（WARNING，新增）** 进程内 run 是**同步执行**（`POST /runs` 阻塞式跑完整条链，
   单事件循环内无法并发插入 pause）。因此本 cycle 的"执行器观测"只在以下两种情况真实
   发生：暂停在边界前已被控制面持久化（如 run 处于 QUEUED/租约态被暂停后再被本进程
   接手），或测试装配直接驱动。**进程内运行中途 pause 不会被抢占**——这一点写进了
   响应 note、tooltip 与两处文档，不冒充"物理暂停"。
3. **W-3（WARNING，新增）** 暂停不发布新的 outbox 领域事件（与 budget_adjust 同侧）：
   状态迁移与派发效果可观测（run 状态 + claim 行为），但事件流/通知里没有
   `run.paused`。若要"暂停进审计事件"，需先补事件类型与投影（后续 cycle 候选）。
4. **W-4（INFO）** 夹具补 `runs_store`（`tests/api/run_fixtures.py`）是本 cycle 的
   必要条件：没有它，派发面在夹具里读不到 run 行，"暂停后不可认领"会是空断言。
   该修正让夹具与生产 `composition.py` 同侧（两者都用共享连接的 `SqliteRunStore`）。
5. **W-5（WARNING，既有 flake 类）** 全量 pytest 三次运行中曾出现 1 次未复现失败
   （随后 3319 passed/0 failed，另一次后台运行 exit 0）；与既有记录一致
   （`tests/observability` OTLP receiver teardown race 类）。本轮不针对它改动断言。
6. **W-6（INFO）** 安全扫描口径：本次 commit/push 时 Mimosa 未返回完整扫描结论
   （`scanner_enobufs`），按既有兼容策略继续且**不宣称项目安全**；完整性审计待专门
   运行（GOAL EC-06 已列）。

## 结论

PLAN-20260914-048 AC-01~AC-04 全部满足；W-1/W-5 为既有范围外项，W-2/W-3 为本 cycle
**已知边界**且已在响应字段、tooltip 与文档中如实标注（非伪装实现）。判定
**PASS_WITH_WARNINGS**，计划 DONE。GOAL-20260912-001 EC-04 仍为**部分交付**
（本批交付 pause/resume 派发协调；实验队列与 memory capability policy G16 未交付），
转入 cycle 9。
