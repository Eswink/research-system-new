---
id: PLAN-20260917-086
slug: failure-policy-gets-a-consumer
title: 失败策略有真实消费者：终局失败被容忍还是立刻失败，且"消费了哪条"可见
status: IN_PROGRESS
created_at: 2026-09-17
updated_at: 2026-09-17
parent_goal: GOAL-20260917-004
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260917-004 cycle 3 = EC-03（承接 GOAL-003「终止与收口 · BLOCKED 记录（2026-09-18）」后继入口第 4 项）。授权来源：2026-09-17 用户 goal 模式指令（新建承接 GOAL-004 并自动化循环推进）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260917-086 — 失败策略的消费者（GOAL-004 cycle 3 = EC-03）

## 目标

`TaskContract.failure_policy` 今天**只有解析面**：域里声明
（`packages/domain/tasks.py:102`）、YAML loader 解析
（`adapters/contracts/tasks_loaders.py:54`）、SQLite 往返
（`adapters/sqlite/serialization.py:95`）、示例里声明了两个键
（`examples/contracts/task_contracts.yaml`：`on_validation_failure: DEAD_LETTER`、
`allow_partial_evidence: false`）——**没有任何执行期消费者**。于是"运维在契约里写下的
失败意图"是装饰：写了也不生效，而且没人告诉运维它不生效。

本轮把它变成真消费者，并让"这一次消费了哪条策略"变成事实：

- **run 级**（本轮消费）：`on_task_failure ∈ {FAIL_RUN（缺省）, CONTINUE}`——
  任务终局失败后是"立刻失败 run"（既有行为）还是"记为被容忍的失败、剩余工作照跑"；
- **其余声明键不假装**：`on_validation_failure` / `allow_partial_evidence` 等由策略视图
  登记为"无消费者"，并在文档点名原因（`on_validation_failure` 的消费需要"完成任务行之后
  再写一次"，属后继入口）——写到不生效比默默忽略更诚实。

## 口径

1. **未声明 ⇒ 行为逐字不变**：缺省 `FAIL_RUN` = 今天的隐式 fail-fast（首个终局失败即
   `deps.fail` → run `FAILED`），既有用例就是回归对照。
2. **已知键取值非法 ⇒ 响亮失败**（`ValueError`），不静默回退到缺省——运维写了
   `on_task_failure: MAYBE` 时必须有人知道这是错的。
3. **未知键 ⇒ 登记，不猜**：进 `unhonored`（确定性排序），行为按缺省。
4. **CONTINUE 不让 run 假装成功**：有被容忍的失败 ⇒ 收敛 **`DEGRADED`**（非终态，
   今天无生产者、语义空闲），事件与消息点名"哪几条失败 + 哪条策略允许的"；无失败照常
   `SUCCEEDED`。DEGRADED 只读面可见（`GET /runs/{id}`），不新增 run 行字段。
5. **策略归属进事实**：每条被容忍的失败进 `TaskOutcome.failure_policy`，run 级事实进
   `run.degraded` 事件 payload（既有事件读面，无第二套存储）。

## 验收条件

- [ ] AC-01 **域判定**：`TaskContract.failure_policy_view()` 返回冻结视图
  （`on_task_failure` + `declared` + `unhonored`）；缺省 `FAIL_RUN`；已知键非法取值
  `ValueError`；未知键进 `unhonored` 且不影响取值。
- [ ] AC-02 **run 级消费**：声明 `CONTINUE` 的 run 在任务终局失败后**继续执行**同组后续
  任务与后续 phase，最后收敛 `DEGRADED`；声明 `FAIL_RUN` 或未声明 ⇒ 与基线逐字一致
  （首个失败即 `FAILED`、后续任务不执行）；**反证**：把消费点去掉 ⇒ 新用例失败。
- [ ] AC-03 **可见**：被容忍失败的 `TaskOutcome.failure_policy == "CONTINUE"`；
  `run.degraded` payload 含 `failure_policy` 与被容忍失败清单；成功路径不发该事件。
- [ ] AC-04 **诚实边界**：`on_validation_failure`/`allow_partial_evidence` 在视图里
  `unhonored`，用例钉住"声明了它们也不改变行为"，文档点名原因与后继入口。
- [ ] AC-05 **门禁与记录**：定向（domain/application/e2e/api）+ m0 23 项 + OpenAPI/文档
  同源 + RECHECK-086 + MEM + GOAL-004/ALL_PLAN 记账。

## 实施清单

- [ ] WP-A **域**：`packages/domain/failure_policy.py`（`OnTaskFailure`、`FailurePolicyView`、
  `failure_policy_view(policy)`）+ `TaskContract.failure_policy_view()` + 域用例。
- [ ] WP-B **执行器**：`PhaseStep.tolerated_failure`、`TaskOutcome.failure_policy`、
  三处失败点（任务失败 / 结果畸形 / 验收门拒收）统一走同一个 `failure_step(...)`、
  `execute_phases` 收敛 `DEGRADED` + `EventType.RUN_DEGRADED`（+ `EVENT_MODEL.md` 词表）+
  `service._degrade_run` + 应用/e2e 用例。
- [ ] WP-C **诚实边界与收口**：unhonored 用例 + 文档（`CONTROL_PLANE_API.md` 语义段）+
  定向 + m0 → commit（每 WP 独立）→ push → CI 六 job → RECHECK-086 + MEM + GOAL-004 回写。

## 证据

（执行后填写）

## 状态历史

- 2026-09-17 建档（GOAL-20260917-004 cycle 3 = EC-03）；`status: IN_PROGRESS`。

## 影响报告

- **Domain**：新增 `failure_policy.py`（纯函数视图）；`TaskContract` 新增只读方法
  （字段与既有契约不变）；新增 `EventType.RUN_DEGRADED`。
- **API/schema**：无新端点、无 DTO 变化（DEGRADED 是既有 run 状态）；事件词表文档补一行。
- **持久化**：无迁移；被容忍失败不进 run 行（只进事件与 RunOutcome）。
- **安全/凭据**：无新面。
- **兼容性/迁移风险**：缺省行为不变（fail-fast）；`DEGRADED` 此前无生产者，读面/UI
  对未知状态有兜底（`RunStateBadge` 未命中走 `tone: unknown`）。
- **上游版本影响**：无新依赖。
