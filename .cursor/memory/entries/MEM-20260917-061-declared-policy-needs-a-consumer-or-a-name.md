---
id: MEM-20260917-061
title: "自由 dict 的声明要么有消费者、要么被点名；容忍失败要有'不假装成功'的落点"
status: ACTIVE
created_at: 2026-09-17
updated_at: 2026-09-17
scope: repository
confidence: 0.9
review_after: 2027-09-17
source_plans:
  - .cursor/plans/tasks/PLAN-20260917-086-failure-policy-gets-a-consumer.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260917-086-failure-policy-gets-a-consumer.md
supersedes: []
tags:
  - contract
  - failure-policy
  - run-state
  - honest-boundary
  - event-vocabulary
  - source-limits
---

# 自由 dict 的声明要么有消费者、要么被点名

## 做了什么

`TaskContract.failure_policy` 是自由 dict：域里声明、loader 解析、SQLite 往返，
**没有任何执行期消费者**——写了不生效，也没人告诉运维。本轮把它变成可消费 + 可点名：

```text
视图：  TaskContract.failure_policy_view() -> FailurePolicyView
        on_task_failure: FAIL_RUN(缺省) | CONTINUE ；declared / unhonored（点名）
消费：  phase_runner.failure_step —— 三处失败点（任务失败/结果畸形/验收门拒收）唯一分叉
        缺省 = 既有隐式 fail-fast（run FAILED、后续不跑）
        CONTINUE = 失败记账（task.failed + TaskOutcome.failure_policy）+ 剩余照跑
落点：  跑完收敛 DEGRADED（非终态）并发 run.degraded（payload：策略 + 被容忍失败清单）
```

## 为什么这样做

1. **自由声明的代价必须显式**：`failure_policy` 这种"资源键值 dict"最容易变成装饰——
   解析器接受一切，运行时没人读。要么给它消费者，要么**点名**"这条键本运行时不管"。
   `unhonored` 就是这个点名（示例里 `on_validation_failure`/`allow_partial_evidence` 就在里面）。
2. **非法取值要响亮**：`on_task_failure: MAYBE` 不能静默回退到缺省——那等于把运维的意图
   悄悄丢掉。取值域是白名单，越界直接 `ValueError`（错在配置面，别等运行期猜）。
3. **容忍失败不能冒充成功**：`SUCCEEDED` 会掩盖失败，`FAILED` 是终态（回头不了，正是
   `CONTINUE` 要避免的）。`DEGRADED` 恰好是空的语义位——"活干完了，但有几条被容忍的失败"。
4. **策略归属要落在事实里**：`TaskOutcome.failure_policy` + `task.failed` + `run.degraded`
   三处可见；run 行只体现状态（不新增字段），要追问细节读事件链。

## 怎么做与复现

```bash
python -m pytest tests/domain/test_failure_policy_view.py -q                       # 视图/点名/响亮失败
python -m pytest tests/application/run_orchestration/test_failure_policy_consumer.py -q  # 尝试次数差异
python -m pytest tests/e2e/test_failure_policy_degraded_run.py -q                  # 端到端 + 事件链
python -m pytest tests/domain/test_m5_domain_increments.py -q                      # 事件词表门禁
```

## 适用边界（踩过的坑）

- **事件词表有门禁**：`TestEventTypeInventory` 同时钉"集合相等"与"数量"（34→36 时必红）。
  加事件类型是**词表扩展**：补 `EVENT_MODEL.md` 与清单，断言本身不动。
- **450 行/50 行硬上限会连续拦人**：本轮 `phase_runner.py`（456 行 + `_execute_phase_group`
  61 行）与 `service.py`（483 行）同时红。处置是**搬**：结果值对象进 `outcomes.py`、两条
  终态发布进 `run_terminals.py`、参数用 `_GroupFrame` 收敛、记账函数进 helpers。
  `service.py` 搬完正好 450——再动它必须先搬。
- **"组合跑"的顺序会造红**：手工按 `application→e2e→…→api` 拼接会把 PG 用例排到
  `test_pg_crash_restart.py` 之后（该用例重启 PG、临时存储清空）⇒ 假红。按字母序/整目录跑
  就不会；判据是隔离复跑 + m0 全量。
- 相关：[[MEM-20260915-047]]（声明了却没消费者的配置等于谎言）、
  [[MEM-20260917-060]]（停车语义成为读面事实）、[[MEM-20260917-059]]（冻结被解析的字节）。

## 来源

- PLAN-20260917-086 / RECHECK-20260917-086（GOAL-20260917-004 cycle 3 = EC-03）。
