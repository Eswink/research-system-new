---
id: MEM-20261009-211
title: "append-only 事实的自然键里放「挂钟」⇒ 同一刻度内的多条事实被静默顶掉（需要单调 tie-breaker）"
status: ACTIVE
created_at: 2026-10-09
updated_at: 2026-10-09
scope: repository
confidence: 0.95
review_after: 2027-04-09
source_plans:
  - .cursor/plans/tasks/PLAN-20261009-361-goal-041-ec02-04-bounded-retry-on-the-crash-window.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261009-362-goal-041-ec02-04-bounded-retry-on-the-crash-window.md
supersedes: []
tags: [canonical-state, append-only, timestamp, natural-key, sqlite, postgres, goal-041]
---

## 做了什么

`record_decision` 的实现（SQLite `INSERT OR IGNORE` / PG `ON CONFLICT DO NOTHING`）以
`(program_id, after_index, decided_at)` 为自然键。实测发现：**同一时钟刻度**内写入的多条
决策会**互相顶掉**且**完全静默**（无异常、无返回差异）。修法：驱动侧把 `decided_at` 归一为
**该程序内严格递增**（取已落决策的最大时点；`now <= latest` 时只推进 1 微秒），
于是自然键不再碰撞、每次推进都留下可读事实。

## 为什么这样做

**先量后改（读数）**：紧循环连录 **10** 条同 `(program_id, after_index)` 的决策 ⇒
`decisions_of` 只返回 **1** 条；连录 50 条 ⇒ 只留存 **2** 条。间隔 20ms / 1ms 写入 ⇒
10 条全留（说明不是「键设计错」而是**分辨率撞车**）。

**根因**：`Timestamp.now()` 取 `datetime.now(timezone.utc)`，其分辨率与运行平台的实际
时钟刻度绑定 —— 在 Windows 上实测**连续 5 次调用返回逐字相同**的微秒值。
而 `INSERT OR IGNORE` / `ON CONFLICT DO NOTHING` 对冲突的处理是**幂等空操作**（这是
Port 契约里写明的「重复写同一时刻 = 幂等空操作」）⇒ 语义上「同一时刻的同一事实不该有两条」
成立，但**「两次推进不会在同一时刻」这个前提不成立**。

**为什么危险**：决策面是读面回答「为何继续 / 为何停」的**唯一**事实源。被静默顶掉意味着
**读面少条**而**没有任何红**：判据若从决策面计数（本轮 EC-02 正是如此），计数会**偏低**
⇒ 声明的上界被绕过，而机器看不出来。这是「append-only」这一措辞的**反面**：
append-only 说的是「不覆盖已有事实」，但自然键冲突会让新事实**根本进不去**。

## 现象

```
# 紧循环（同一刻度）
连续录 10 条同 (program_id, after_index) 的 DEDUP 决策 ⇒ decisions_of 返回 1 条
连续录 50 条 ⇒ 返回 2 条

# 有间隔（真实请求节奏）
间隔 20ms / 1ms 各录 10 条 ⇒ 各返回 10 条

# 端到端形态（失败重试面）
allowed=3 + 反复「认领即崩」⇒ 判定序列 card 停在 DEDUP_FAILED_RUN 不动（永不收口）
```

## 根因

| 层 | 事实 |
| --- | --- |
| 域 | `Timestamp.now() = cls(datetime.now(timezone.utc))` —— 无单调保证 |
| 平台 | Windows 时钟刻度实测产出**逐字相同**的微秒值（连续 5 次） |
| 存储 | SQLite `PRIMARY KEY (program_id, after_index, decided_at)` + `INSERT OR IGNORE`；PG 同构 + `ON CONFLICT DO NOTHING` ⇒ 冲突**静默** |
| 驱动 | 每次推进自造一条带 `Timestamp.now()` 的决策 ⇒ 紧循环下彼此撞车 |

## 怎么做与复现

**复现（最小）**：

```python
store = SqliteProgramStore()          # 或 PostgresProgramStore
for i in range(10):
    store.record_decision(ProgramDecision(program_id="p", after_index=1,
        kind=ProgramDecisionKind.DEDUP, reason=f"r{i}", cited_facts=()))
assert len(store.decisions_of("p")) == 10   # 实测失败：只有 1
```

**修法（本轮采用：驱动侧单调 tie-breaker）**：

```python
latest = max((d.decided_at.value for d in programs.decisions_of(program_id)), default=None)
now = decision.decided_at.value
if latest is not None and now <= latest:
    now = latest + timedelta(microseconds=1)
programs.record_decision(replace(decision, decided_at=Timestamp(now)))
```

不引入新依赖、不改存储 schema、不改 Port 契约（「同一时刻重复写 = 幂等空操作」逐字保持）
—— 只是**保证**驱动不会产生「同一时刻」这一形态。**逻辑时钟**的语义（决策各自带时间、
读面顺序 = 写入顺序）也一并成立。

**替代方向（未采用，登记）**：给决策表加代理主键（sequence / rowid）并把
`decided_at` 降为普通列 —— 那是**迁移**（PG 需要 ALTER + 回填），本轮不做；
判定依据是「驱动侧归一即可让契约成立，且不动 canonical schema」。

**判据（新判据必须钉住这一形态）**：
`test_every_advance_leaves_a_decision_even_in_the_same_clock_tick`（驱动）
与 `test_the_program_read_face_keeps_every_advance_as_a_decision`（e2e）——
后者的断言是「推进次数 == 决策数」且时点**单调且互不相同**。

## 适用边界

- 适用于：本仓一切以**时间戳参与自然键**的 append-only 面。实测同类面：
  `program_decisions`（本轮修）；**待核查**：其余带 `decided_at` / `created_at` 参与主键
  或唯一约束的表（本条目**不**声称它们已修）。
- **不**适用于：时间戳只作记录字段（不参与唯一性）的表 —— 那里的撞车只是读数相同，
  不丢事实。
- **不声称**：本修法保证的是**驱动**不再产生撞车；**直接调用 store 的第三方**
  仍可撞车（契约里那一条「幂等空操作」保持不变）。要让**存储层**自身免疫，
  需要代理主键（见「替代方向」）。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20261009-361-goal-041-ec02-04-bounded-retry-on-the-crash-window.md` | WP-4：发现的形态 + 修法 + 门链读数 |
| recheck | `.cursor/plans/rechecks/RECHECK-20261009-362-goal-041-ec02-04-bounded-retry-on-the-crash-window.md` | 独立复检：按压 R-3（不归一 ⇒ 必红）+ 静默丢弃的独立复现 |
| repository | `packages/domain/core.py::Timestamp.now` | 无单调保证（`datetime.now(timezone.utc)`） |
| repository | `adapters/sqlite/program_store.py` / `adapters/postgres/program_store.py` | 自然键 + `INSERT OR IGNORE` / `ON CONFLICT DO NOTHING`（静默） |
| repository | `packages/application/ports/program_store.py` | 契约原文：「重复推进产生的是**多条**决策（各自带时间）」—— 撞车即违反 |
