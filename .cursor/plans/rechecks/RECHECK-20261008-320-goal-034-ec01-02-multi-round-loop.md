---
id: RECHECK-20261008-320
slug: goal-034-ec01-02-multi-round-loop
title: 独立复检：GOAL-034 cycle 1（EC-01/EC-02）多轮循环的执行接线与三轮实跑
plan_id: PLAN-20261008-319
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-08
completed_at: 2026-10-08
owners:
  - root-agent
---

# RECHECK-20261008-320 — GOAL-034 cycle 1 独立复检

复检对象：`PLAN-20261008-319`（AC-5 = 执行接线 + 三轮 e2e）。**独立重跑**下列判据与按压。

## 检查结果

### 1. 三轮真的跑（独立重跑，读事件链）

| 读数 | 值 |
| --- | --- |
| `rounds_run` | **3** |
| `stopped_by` | **`MAX_ROUNDS`**（每轮都有新标识 ⇒ 只能由上界停） |
| `criterion` | `max_rounds` |
| `ids_seen` | **三轮全部 PMID**（`39500001/2`、`39500011/12`、`39500021/22`）|
| `new_ids_this_round` | 第 3 轮的新标识（非空 ⇒ 不是结论停）|
| 每轮检索 | 离线传输层收到 **3 次** `esearch`，且三个词各出现一次 |

**复检交叉核**：`ids_seen` 含**三轮各一对** PMID ⇒ 三轮**都真的执行了检索**，
不是同一轮跑三遍（同一轮跑三遍时 `ids_seen` 只会有一对）。

### 2. 两臂可区分（独立重跑）

| 臂 | 构造 | `rounds_run` | `stopped_by` |
| --- | --- | --- | --- |
| 护栏臂 | `max_rounds=3`，每轮都有新标识 | 3 | `MAX_ROUNDS` |
| 结论臂 | `max_rounds=9`，第 2 轮零命中 | **2** | **`CONCLUSION`** |

结论臂**同时**是反证：上界（9）远大于实际轮数（2）⇒ 停**不是**上界逼的。

**重合判据**（顺序）：`max_rounds=2` 且第 2 轮零命中 ⇒ 两者同时成立 ⇒ 必须读成
`CONCLUSION`。按压把护栏判断提到结论之前 ⇒ 该条**判红**（1 failed）。

### 3. 判据重跑

```
tests/e2e/test_multi_round_research_loop.py ......... [100%]  9 passed
```

### 4. 按压独立重跑

```
BASELINE_GREEN 9 passed
P1_RED exit=1 1 failed, 8 passed      （结论/护栏顺序颠倒 ⇒ 重合那条判红）
P2_RED exit=1 7 failed, 2 passed      （不换任务身份 ⇒ 三轮塌成一轮/撞 source 登记）
RESTORED True {'round_loop_facts.py': '1a2a611615af->1a2a611615af',
               'round_loop_runner.py': 'f018082c8d3c->f018082c8d3c'}
FINAL_MATCHES_BASELINE True 9 passed
```

两条都**真的判红**，且逐字节复原（sha 归因在日志里）。留档
`scratch/goal034-cycle1b/press-matrix.log`。

### 5. 既有语义未动（回归面）

| 套件 | 读数 |
| --- | --- |
| `tests/application + tests/e2e + tests/integration + tests/architecture/python + tests/tooling` | **2660 passed / 14 skipped / 0 failed** |
| 规模门 | 1141 passed（`phase_capabilities` 的 53 行函数已拆 `_run_planned_calls`，纯搬迁） |
| `ruff` / `format` / `mypy` | 绿 |
| 治理 `validate.py` | 绿 |

## 结论

**result: PASS_WITH_WARNINGS**。AC-5 成立（三轮实跑 + 派生可追 + 两臂可区分 + 反证）；
AC-1…AC-4 在本 PLAN 早前段落已 PASS。**无产品缺陷**（本段改动均为新增面与纯结构性拆分）。

### Warnings

- **W-1（三处真机制缺口，均先量后改）**：① 轮次改 phase id ⇒ 运行链 phase 级过滤查不到
  表 ⇒ 第 2 轮起**静默跳过所有运行链调用**；② 轮次不换任务 id ⇒ 同任务重跑以不同 digest
  重登记同一 `source_ref` ⇒ 撞 `conflicting source registration`（实测第一轮成功、
  第二轮 FAILED）；③ 三轮起 `artifact_from_previous` 的后缀判据匹配多份 ⇒ fail closed。
  三条都不是判据缺陷，而是**两轮语义不适用于多轮**。⇒ 已分别用幂等键后缀、按轮新 id、
  `artifact_from_previous_round` 修掉，并各有判据。
- **W-2（一次判据假信号，轮内已修）**：首版 `_rounds_fact` 取「第一条 `run.completed`」，
  而跑过循环的 run 事件链里有**两条**（带 `rounds` 的循环收尾 + 单遍原样载荷）
  ⇒ 顺序一变就会静默读到错的那条。改为**点名带键的那条**。
- **W-3（`calls_by_round` 的边界）**：轮次差异只支持「按轮给出整批调用声明」这一种形态；
  「按轮只改某一个参数」需要装配方自己拼（夹具即如此）。**如实登记**为未覆盖的便利性需求。
- **W-4（本段未覆盖）**：并行多轮（`parallel_agents` / `map_reduce`）、跨 run 的知识累积
  （MAINLINE 序 5）、预算驱动的停止（`budget_exhausted` 仍未消费）**均未做**。
- **W-5（不得宣称安全 / 不得宣称恰好一次）**：**不得**宣称项目安全（`R-M1` 未收口）；
  **不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once +
  idempotency + deduplication）。
