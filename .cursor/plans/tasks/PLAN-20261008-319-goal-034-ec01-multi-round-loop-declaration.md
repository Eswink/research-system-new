---
id: PLAN-20261008-319
slug: goal-034-ec01-multi-round-loop-declaration
title: GOAL-034 cycle 1（EC-01/EC-02 声明面）：多轮循环的声明与停止判据 —— 纯逻辑面落地 + 执行接线待续
status: IN_PROGRESS
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261008-034
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-034 的 **EC-01 / EC-02**。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：**不建第二套编排**（轮次挂在既有相位执行链上；
    派生复用既有 `RunChainCall`）；**不改** `PhaseStrategy` 枚举语义（要改须 ADR ⇒ escalation）；
    **不改**协议 schema（声明放装配面，与 `RunChainCall` 同层）；**不得**把「固定轮数加长」
    当推进深度轴（MAINLINE 明文）；**不得**宣称安全（`R-M1`），**不得**宣称投递语义为
    恰好一次（**明确否认**）。
objective: >-
    把多轮循环的**声明面**与**停止判据**从建档勘察的散文读数推进到**有判据的纯函数**：
    ① `RoundLoop`（相序列 + `max_rounds` 护栏 + 结论驱动的 `stop_when` 判据名）与它的
    展开/反查（**每轮 id 必须不同** —— 同 id 会被既有按 key 去重吞掉 ⇒ **静默停**）；
    ② `RoundFact` / `StopDecision` / `evaluate_stop`：停止判定**永远先读结论、再谈护栏**
    （反过来会把「结论已收敛」谎报成「只是上界到了」）；③ 事实读取
    （`ids_from_step_outputs`，与既有派生链的 `content.ids` 形态同源）；④ 执行面的
    **循环控制状态机**（`RoundLoopState`：逐轮记事实、判定、产出可读的停止载荷）。
    本轮**只做**声明面与纯逻辑面（可独立验收的最小增量）；**执行接线**（真跑三轮）为下一步。
exit_criteria:
  - id: AC-1
    criterion: >-
      **声明面**：`RoundLoop` 支持多相序列 + `max_rounds` + 判据名；**展开每轮 id 不同**
      （第 1 轮保持原始 id ⇒ 既有单轮语义逐字不动）；单轮循环 / 未知判据 / 重复 phase
      **构造期点名拒绝**；`find_loop` 能反查**原始 id 与展开 id 两种形态**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/application/run_orchestration/test_round_loop_declaration.py -q` ⇒
      `TestTheDeclarationFace`（5 例）绿。
    status: PASS
  - id: AC-2
    criterion: >-
      **停止判据（含顺序）**：无新标识 ⇒ 停、类别 `CONCLUSION`；有护栏且结论未收敛 ⇒
      停、类别 `MAX_ROUNDS`；**两者同时成立时必须是 `CONCLUSION`**（顺序的判据）；
      同类读数下两臂类别**互斥**。
    verify: >-
      同文件的 `TestTheStopDecision`（5 例）绿。
    status: PASS
  - id: AC-3
    criterion: >-
      **事实读取**：按声明路径取标识（`content.ids`）、去重保序、整轮无标识型产出 ⇒
      空元组（⇒ 判据判「无新标识」）；**「新」是集合差不是计数**（同批标识重来一遍
      不算新）。
    verify: >-
      同文件的 `TestTheFactReader`（4 例）绿。
    status: PASS
  - id: AC-4
    criterion: >-
      **执行面的循环控制状态机**：`RoundLoopState` 逐轮记事实（`seen_before` 由已记录
      事实推出）、`decide()` 走 `evaluate_stop`、`stop_payload()` 输出**可复读**的停止
      载荷（判据名 / 类别 / 本轮新标识 / 累计标识 / 上界）；装配期 `validate_loops`
      对未知 phase **点名拒绝**。
    verify: >-
      `uv run --frozen --no-sync python -B -m mypy
      packages/application/run_orchestration/round_loop_runner.py` ⇒ 绿；
      `RoundLoopState` 的逐轮行为由 **AC-5 的接线** 覆盖（本 PLAN 只到状态机本身）。
    status: PENDING
  - id: AC-5
    criterion: >-
      **执行接线（三轮真的跑起来）**：`RoundLoop` 声明经装配面注入 ⇒ `execute_phases`
      按轮**懒展开**该轮 specs（判「停」就**不再解析**下一轮，否则判据只是装饰）；
      第 N>1 轮的 phase/任务 id 带轮次后缀 ⇒ 派生链读到**上一轮**的产出。
    verify: >-
      待做：`tests/e2e/test_multi_round_research_loop.py`（三轮触发臂 + 派生可追 +
      结论驱动停止臂 + 上界护栏臂 + 反证）。
    status: PENDING
---

# PLAN-20261008-319 — GOAL-034 cycle 1：多轮循环的声明面与停止判据

## 验收条件

见 frontmatter `exit_criteria`。**本 PLAN 是 cycle 1 的第一段**（声明面 + 纯逻辑面），
AC-4/AC-5 是**执行接线**，留待下一步——**不把未做的记成已完成**。

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 声明面（展开 / 反查 / 构造期点名拒绝） | PASS |
| AC-2 | 停止判据 + **顺序**（结论优先于护栏） | PASS |
| AC-3 | 事实读取（集合差 / 空轮语义） | PASS |
| AC-4 | 执行面的循环控制状态机 | PENDING（模块已进树，行为待接线覆盖） |
| AC-5 | 执行接线（三轮真跑） | PENDING |

## 实施清单

- [x] `packages/application/run_orchestration/round_loop.py`：`RoundLoop` 声明 +
      展开/反查 + 判据词表（`CONVERGED_NO_NEW_IDS`）+ 停止类别词表。
- [x] `packages/application/run_orchestration/round_loop_facts.py`：`RoundFact` /
      `StopDecision` / `evaluate_stop`（顺序固定）/ `ids_from_step_outputs`。
- [x] `packages/application/run_orchestration/round_loop_runner.py`：`RoundLoopState`
      （逐轮事实 + 判定 + 停止载荷）+ `validate_loops`。
- [x] `tests/application/run_orchestration/test_round_loop_declaration.py`（14 例）。
- [ ] 执行接线（AC-4 / AC-5）+ e2e 三轮判据。

## 证据

### 勘察（建档已入 GOAL 的「事实层结论」，此处只记本 PLAN 用到的两条）

| # | 事实 | 读数 |
| --- | --- | --- |
| 1 | `ITERATIVE_OPTIMIZER` / `POPULATION_SEARCH` 零消费 | `rg` 只命中枚举定义处；而 `m12_reference_research_v1.yaml` 已在用 `iterative_optimizer` |
| 2 | `stop_conditions` 运行期零消费 | 解析/编译/preflight 三段有；`rg -n "\.stop_conditions" packages/application/run_orchestration/ services/api/ adapters/` = **零命中** |

### 设计取舍（为什么声明在装配面）

`RunChainCall` 就是**装配方声明**的（`OrchestrationDependencies.capabilities`），不过协议
schema。多轮循环控制同理：它是执行装配的形状。改协议 schema 会连带 loader / compiler /
preflight / 前端表单四处同步，而收益只是把同一件事换个地方声明 ⇒ **放装配面**。
副作用：`PhaseStrategy` 枚举语义**不动**（改它须 ADR ⇒ escalation），本 PLAN 零协议改动。

### 实现要点（两处「判据在这一层就必须钉住」的地方）

1. **每轮 id 必须不同**：任务 `idempotency_key` 是 `{run}:{phase}:{agent}` ⇒ 同 id 时
   第二轮的 `submit` 被既有按 key 去重**静默吞掉**。第 1 轮保持原始 id（既有单轮语义
   逐字不动），N>1 加 `@{n}` 后缀（`@` 不在协议 phase id 的命名空间里）。
2. **停止判定的顺序**：**永远**先评估结论判据、护栏只在结论没停时说话。反过来会把
   「刚好跑到上界且结论也收敛」谎报成「只是上界到了」—— 那正是 MAINLINE 禁止的
   「把结论驱动谎报成固定轮数」。

### 判据

```
tests/application/run_orchestration/test_round_loop_declaration.py .............. [100%]  14 passed
tests/application + tests/e2e                                             997 passed, 14 skipped
```

### 门（本 PLAN 触及面）

| 门 | 读数 |
| --- | --- |
| `ruff check` / `ruff format --check`（`packages/application/run_orchestration/`） | 绿（首跑 3 条 import 排序错 ⇒ `--fix`） |
| `mypy`（三个新模块） | 绿 |
| 记录面判据（`tests/architecture/python` + `tests/tooling`） | **首跑 1 failed**：`test_the_cjk_lemma_never_appears_in_product_or_docs` 抓到我在 `round_loop.py` 里写了禁用的中文短语（它在本仓是**计数**语义、产品面必须零命中）⇒ 改写措辞 ⇒ **1619 passed** |

## 影响报告

- **Domain / API / schema 变化**：**无**（零协议/schema/DTO 改动；三个新模块都在
  `packages/application/run_orchestration/`）。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：无（纯新增模块；既有 `execute_phases` 单遍语义**未改**）。
- **观测隐私**：无新增出口（新模块不发日志/遥测）。
- **上游版本影响**：无。
- **下一项任务**：执行接线（AC-4 / AC-5）—— `RoundLoop` 声明经装配面注入，
  `execute_phases` 按轮懒展开，e2e 三轮判据。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | IN_PROGRESS | cycle 1 第一段落地：声明面 + 纯逻辑停止判据（14 例全绿）+ 执行面状态机模块进树。**执行接线未做**（AC-4/AC-5 = PENDING，如实登记）。门抓到我自己的一处措辞违规（产品面禁用中文短语）⇒ 已改。 |
