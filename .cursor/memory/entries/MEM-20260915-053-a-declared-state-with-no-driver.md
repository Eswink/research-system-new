---
id: MEM-20260915-053
title: 状态机里"声明了的状态"不等于"会发生的状态"——枚举驱动方才能发现没人走进去
status: ACTIVE
created_at: 2026-09-17
updated_at: 2026-09-17
scope: repository
confidence: 0.92
review_after: 2027-09-17
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-078-retry-policy-becomes-real.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-078-retry-policy-becomes-real.md
supersedes: []
tags:
  - domain
  - state-machine
  - retry
  - dead-letter
  - gated-invariants
---

# 状态机里"声明了的状态"不等于"会发生的状态"

## 做了什么

`TaskContract.retry_policy.max_attempts` 是**必填字段**，Domain 状态机写着
`RETRY_SCHEDULED` / `DEAD_LETTER` 与对应迁移，schema 与 loader 都收这些字段——
但**没有任何生产调用方**：

```text
限定写法扫描生产代码（ResearchTaskState.State.<NAME>）：
  RETRY_SCHEDULED 命中 0     DEAD_LETTER 命中 0
complete() 任何非 SUCCEEDED 的完成一律写 FAILED；
TaskCompletion 只有 outcome —— 没有"失败类别"，重试分类的输入根本不存在。
```

也就是说 AGENTS.md §7 要的"retry classification + dead-letter / manual recovery"
一条也没落地，而**代码里看不出来**：状态机会接受这些状态，只是没人会走进去。

收口：判据下沉为 Domain 纯函数 `TaskContract.decide_failure(attempt, category)` →
`RETRY` / `DEAD_LETTER` / `FAIL`，SQLite 与 PG 两个 adapter 共用；`TaskCompletion` 加
可选 `failure_category`；`RETRY_SCHEDULED` 与 `QUEUED` 同为可 claim 状态；另加**枚举门禁**：
状态机里每个状态要么登记"由谁驱动"，要么登记"为什么没有"，并用文本扫描对账。

**计数器必须与投影同一条更新落账**：attempt 在交付 lease 的那一刻前进，而投影
（`list_tasks`）读的是 `task_json`——只改列不改 JSON 的话，投影永远停在 1，于是重试产生的
用量会一直落进上一次尝试的 entry id（`packages/application/experiments/budget_entries.py`
的 `_attempt_scope` 专门为 retry 追加 `:attempt-N` 后缀，那条声明同样**永远走不到**）。
两条交付路径（claim 与 acquire）都改成"状态 + 交付代次 + attempt + task_json"一条更新，
并用"租约过期 → 回收 → 再交付"这条不依赖 retry_policy 的路径把投影前进钉住。

## 为什么这样做

1. **"声明"会被当成"实现"**：必填字段 + 状态常量 + 迁移表 + loader 校验，四样都在，
   review 时看上去就是"重试已经做了"。只有问"**谁**设置这个状态"才发现是空的。
2. **判据必须在 Domain**：两个 adapter（SQLite/PG）各自 if-else 会漂移；纯函数
   （attempt + category → 动作）只有一份，两个 adapter 只是调用者。
3. **attempt 的语义要与域不变量对齐**：域要求 `attempt > 1` 必须带 `lease_id`，
   所以 attempt 只能在**拿到 lease 的那一刻**递增（= "已开始的尝试次数"）。
   在"排重试"时递增会让该不变量无法满足（重排时任务没有租约）。
4. **门禁要能对着未来报警**：状态 → 驱动方登记表 + 生产代码扫描，新加状态不接线即红
   （[[MEM-20260915-051]] 的同一手法，这次用在状态机上）。

## 怎么做与复现

```bash
python -m pytest tests/adapters/sqlite/test_workflow_retry_policy.py -q   # 8 passed
python -m pytest tests/postgres/test_workflow_retry_policy_pg.py -q       # 2 passed（parity）
python -m pytest tests/domain/test_task_state_drivers.py -q               # 3 passed（枚举门禁）
```

改任务生命周期时的检查清单：① 新状态先写"谁设置它"；② 判据放 Domain 纯函数，
adapter 只调用；③ attempt/计数类字段与域不变量对齐（递增时机决定语义）；④ "可 claim 状态"
表只允许有一份，扫描与写事务内复核共用同一张表，否则任务会在复核那步被判 contended；
⑤ 重放路径（at-least-once）要覆盖新状态——"处置已落账"的状态也必须算 noop；
⑥ 计数器只有落到**投影**里才算数：列与 JSON、投影与列不能各说一套。

## 适用边界（踩过的坑）

- **没有退避**：重排后立即可被 claim，失败很快的任务会在 `max_attempts` 内热循环。
  退避需要策略字段或新列，本轮刻意不做（如实登记）。
- **`failure_policy` 仍是零消费者**：它的键名空间没和 `FailureCategory` 对齐，
  直接消费等于自己发明语义——**不猜**，留给单独一轮。
- **门禁是文本级**：按 `ResearchTaskState.State.<NAME>` 限定写法扫描，别名导入会漏。
- 相关：[[MEM-20260915-047]]（声明了却没人消费的配置是一种谎言）、
  [[MEM-20260915-051]]（把边界枚举出来再门禁）、[[MEM-20260915-049]]（存在性检查不是解析）。

## 来源

- PLAN-20260915-078 / RECHECK-20260915-078（GOAL-20260915-003 cycle 15）。
