---
id: RECHECK-20260914-046
plan_id: PLAN-20260914-046
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-14
completed_at: 2026-09-14
reviewer: root-agent-gate-evidence
baseline_ref: 8ff2398
checked_head: 837f730
---

# RECHECK-20260914-046 — budget_adjust 走账本 + 预留-消耗预测独立复检

GOAL-20260912-001 cycle 6（EC-04 第一批）派生计划的复检。本 cycle 的关键语义决定是
**调整以 reservation 生命周期表达**（append-only 账本无"原地改数"：release 既有引用 +
reserve 新额度），且**预测只覆盖已预留额度**（不外推未预留开销）。复检以「本地全门命令
输出 + 定向 e2e + CI run 终态」为权威证据，并重点对抗核查三处诚实性：UNKNOWN 不被
解释为 0、跨币种不求和、run 预留归属不得靠作用域猜。

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260914-046-budget-adjust-ledger-and-forecast.md`
  （`parent_goal: GOAL-20260912-001`，EC-04 第一批）。
- 变更范围：应用层 `run_orchestration/budget_adjust.py`；域 `domain/cost_forecast.py`；
  Port `LedgerSnapshot.reservations_by_ref`（Fake/Sqlite/Postgres 三实现）；
  API `routers/budget_forecast.py`、`routers/approvals.py::_budget_adjust`、
  `dto/budget_forecast.py`、`dto/approvals.py`；前端 budget 页四处 + 4 个 client/types；
  docs 3 份；openapi 再生；测试 25 例（api 14 / domain 11）+ stub e2e 2 + live e2e 1。
- 边界：`replace_agent`（运行中语义变更 → Manifest Revision/Fork）保持诚实 501；
  真 pause-resume 协调、实验队列、artifact diff、memory capability policy（G16）
  属后续 cycle；无新表/迁移（唯一 schema 触点是 `budget_reservations` 行的既有列）。

## 检查结果

| AC | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| AC-01（WP-A） | release+reserve 组合；预算面 None 显式错误 | `pytest tests/domain/test_cost_forecast.py tests/api/test_budget_forecast_api.py` = 25 passed；`execute_budget_adjustment(None, …)` → BudgetAdjustmentError→503 用例 | PASS |
| AC-02（WP-B） | 200/422/503/404 分支 + replace_agent 501；诚实语义；openapi 零漂移 | api 14 例含空调整 422、无 ledger 503、未知 run 404、replace_agent 501、UNKNOWN/跨币种用例；`test_openapi_snapshot` 2 passed（425 行 schema 增量） | PASS |
| AC-03（WP-C） | budget 页预测可见 + 调整真实生效；G5/G12 更新；web 门全绿 | stub e2e `budget-adjust.spec.ts` 2/2（UNKNOWN 不显示为 0；调整后 2500/2100 跟随）；`pnpm --dir apps/web lint/typecheck` 绿；pageSupport G5/G12 与 CONSOLE_PAGE_MAP/CONTROL_PLANE_API 同步 | PASS |
| AC-04（WP-D） | 本地全门 + stub/live e2e + m0 + CI 终态 | 全量 pytest 3132 passed/0 failed（另 151 skipped）；live e2e 15/15；m0 23/23 PASS（`uv run` + Postgres 测试容器 + DSN 固化）；CI run #60 见状态历史 | PASS |

## 警告与处置

1. **W-1（WARNING，既有，非本 cycle）** collector-quality 仍是 RECHECK-042/043/044/045
   登记的**同 2 项** timing flake（本次 run #60 日志实测：`test_collector_persists_
   research_os_spans` 文件导出未在超时内落 span、`test_scenario_d_network_partition_
   no_old_authority` 子进程 10s 超时）；其余 5 个 job 全 SUCCESS。按 fix_policy 不放宽
   断言、不 skip、不改 workflow（治理面）。
2. **W-2（WARNING，新增）** budget_adjust 不发布 outbox 领域事件（与既有 pause/resume
   干预同侧）：持久记录为账本 `budget_reservations` 行（新 ref 行 + 旧 ref `released=1`）
   + API 响应摘要，但**不进事件流**，因此不产生通知/审计事件投影。若要"预算调整进
   审计事件"，需先补领域事件类型与投影（后续 cycle 候选）。
3. **W-3（WARNING，新增）** 预留归属依赖**进程内** `_reservation_refs`（冻结 manifest
   登记的 ref + 调整后登记的新 ref）。跨进程重启后 ref 不可解析，端点退化为
   `run:<id>` 作用域匹配（`attribution=RUN_SCOPE`）并如实标注；此时正式 preflight 的
   `phase:<id>` 预留不会被并入，条数计入 `unattributed_reserved` 而非伪装为零。
4. **W-4（INFO）** 夹具修正属本 cycle 的附带缺陷修复：`tests/api/run_fixtures.py`
   此前 preflight Context / 编排 deps / ApiDeps 各持一个 FakeBudgetLedger（生产
   `composition.py` 是**同一实例**），使夹具内预算读链恒空——已改为共享同一实例；
   该修正同时让 live e2e 的新用例具备真实语义（否则为假绿）。
5. **W-5（INFO）** 安全扫描口径：本次 commit/push 时 Mimosa 未返回完整扫描结论
   （`scanner_enobufs`），按既有兼容策略继续且**不宣称项目安全**；完整性审计待
   专门运行（GOAL EC-06 已列）。

## 结论

PLAN-20260914-046 AC-01~AC-04 全部满足；W-1 为既有范围外项，W-2/W-3 为本 cycle
新增的**已知边界**（已在文档与响应字段中如实标注，非伪装实现）。判定
**PASS_WITH_WARNINGS**，计划 DONE。GOAL-20260912-001 EC-04 为**部分交付**：
budget_adjust + 成本预测已落地并验收；真 pause-resume 执行协调、实验队列、
artifact 文件 diff、memory capability policy（G16）四项未交付，随 GOAL 迭代日志
转入 cycle 7 候选。
