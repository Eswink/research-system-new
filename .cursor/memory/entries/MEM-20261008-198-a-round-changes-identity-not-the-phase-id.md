---
id: MEM-20261008-198
title: "多轮循环里「轮次」必须改**任务身份**（幂等键 + id），但**不能**改 phase id —— 两处静默失败都是实测出来的"
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
scope: repository
confidence: 0.95
review_after: 2027-04-08
source_plans:
  - .cursor/plans/tasks/PLAN-20261008-319-goal-034-ec01-multi-round-loop-declaration.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261008-320-goal-034-ec01-02-multi-round-loop.md
supersedes: []
tags: [multi-round, round-identity, phase-id, source-registration, goal-034]
---

## 做了什么

把「同一组 phase 重复执行到停」做成真的多轮时，**轮次加在哪个标识上**决定成败。
三个方向各实测一次（都是先写判据、看它怎么红）：

| 轮次加在哪 | 结果 |
| --- | --- |
| **phase id** 加 `@N` 后缀 | **静默跳过**：运行链的 phase 级过滤（`planned_in_this_phase`）拿 spec 的 phase id 去**编译计划表**里查，带后缀查不到 ⇒ 第 2 轮起**所有运行链调用都不执行**（不报错） |
| **任务 id / 幂等键**都不动 | 两种坏法：① 幂等键同 ⇒ 第二轮 submit 被既有按 key 去重**静默吞掉**；② 同一任务上重复跑运行链 ⇒ 以**不同 digest** 重登记同一 `source_ref`（origin = `tool:{tool}:{task_id}:{op}`）⇒ `conflicting source registration`（实测：第一轮 SUCCEEDED、第二轮 FAILED） |
| **幂等键 + 任务 id** 都按轮区分 | 正确：每轮是不同的任务（可数、可续），phase id 不变（过滤仍有效） |

## 为什么这样做

- **phase id 是「查表键」而不是「身份」**：链式过滤、工具需求、gate 都按它查编译计划。
  任何「换个名字让每轮不同」的想法都会把那些查表静默打空。
- **任务身份才是「这一次执行」的载体**：幂等键决定「重复提交会不会被吞」，id 决定
  「同一条任务上重复登记会不会冲突」。两者**必须一起换**。
  - 只换键不换 id ⇒ 撞 source 登记（上面第 2 行的 ②）；
  - 只换 id 不换键 ⇒ 被按 key 去重吞掉（①）。
- **第 1 轮保持原样**：既有单轮语义与「续跑按幂等键对齐」（`_remaining_specs`）逐字不动；
  只有 N>1 加后缀/换新 id。

## 怎么做与复现

```bash
uv run --frozen --no-sync python -B -m pytest tests/e2e/test_multi_round_research_loop.py -q  # 9 passed
uv run --frozen --no-sync python -B scratch/goal034-cycle1b-press.py
# 期望：P1_RED 1 failed（结论/护栏顺序颠倒）
#       P2_RED 7 failed（不换任务身份 ⇒ 三轮塌成一轮）
#       RESTORED True（sha 归因）/ FINAL_MATCHES_BASELINE True
```

**附带发现（第三个缺口）**：三轮起，`artifact_from_previous`（按后缀选上一轮的产出）
会匹配到**多份**（前几轮的产出都还在证据投影里）⇒ 既有「恰好一条」判据 fail closed。
⇒ 需要一个**执行期才知道**的收窄条件（上一轮的任务 id）——与 `run_id_argument` 同层：
声明的是**取值的来源**，不是值。两轮时并不需要它 ⇒ 「两轮能跑」**不代表**「多轮能跑」。

## 适用边界

- 适用于任何「同一段流程重复执行」的编排扩展（多轮研究、重试轮次、迭代优化）。
- **不**适用于 phase id 本身就是业务语义的场合（那里应新增 phase，而不是循环）。
- 判据纪律：这类「静默跳过 / 静默吞掉」不会报错 ⇒ 判据必须断言**副作用条数**
  （每轮各自的检索证据、`ids_seen` 含各轮标识），只看终态 `SUCCEEDED` 会全绿。

## 来源

- `.cursor/plans/tasks/PLAN-20261008-319-goal-034-ec01-multi-round-loop-declaration.md`
- `.cursor/plans/rechecks/RECHECK-20261008-320-goal-034-ec01-02-multi-round-loop.md`（`W-1`）
- 留档：`scratch/goal034-cycle1b/press-matrix.log`
