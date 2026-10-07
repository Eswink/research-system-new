---
id: MEM-20261008-194
title: "一个被多重门掩蔽的断言无法被单变量证伪：`dispatched == 0` 改状态过滤后仍是 0（判据假绿）"
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
scope: repository
confidence: 0.95
review_after: 2027-04-08
source_plans:
  - .cursor/plans/tasks/PLAN-20261008-313-goal-033-ec02-dead-letter-run-coordination.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261008-314-goal-033-ec02-dead-letter-run-coordination.md
supersedes: []
tags: [judge-masking, false-green, single-variable-refutation, spy, goal-033, plan-313]
---

## 做了什么

GOAL-033 cycle 2 要判「`RetryDispatchScheduler` 不会碰一条死信 run」。首版断言写成：

```python
scheduler.run_once() == 0   # "它不派发这条 run"
```

按压（把派发方的 `run.state != PAUSED` 过滤放开，让它也扫 `FAILED`）**没判红** —— 仍然是
0。原因是那条 run 要走到「被派发」要过**三道独立门**：

1. 状态过滤（`run.state == PAUSED`）；
2. 重建能力（`_can_rebuild`：本进程有 `rebuild` **且** run 记了装配来源）；
3. 到期重排（`due_retry_task_ids(run_id)` 非空）。

首版判据里 run **根本不在 store 里** ⇒ 第 2 道门先把它挡掉 ⇒ 改第 1 道门读数不变
⇒ 断言在缩小的受判面上恒真（与 `MEM-20260922-160` / `MEM-20261005-187` 同族：
受判面被写窄）。

## 为什么这样做

**改法**：把「它不派发」换成「它**根本不考虑**这条 run」，观测点是**派发方对
`due_retry_task_ids` 的询问** —— 那次询问发生在两道门**之后**，所以「被问到 ⟺ 真的进了
能力圈」。实现是转调真实引擎的 spy：

```python
class _WorkflowSpy:              # 转调真实引擎，但记录被问过的 run_id
    def due_retry_task_ids(self, run_id): self.due_calls.append(run_id); ...
    def __getattr__(self, name):     return getattr(self._engine, name)
```

**必备的正向对照**（否则空集可能是空真）：把**同一条 run** 改成 `PAUSED`
（其余不动）⇒ 它**必须**被问到。改完后同一次按压 `1 failed`。

**推广**：一条「什么都没发生」式的断言（0 计数 / 空列表 / 未调用），若其否定面有多条
独立来源，就必须回答「**哪一道门**是我在判的、另外几道是否已置为放行态」。做不到就换个
观测点 —— 观测**最靠近被判机制**的那一步（这里是「考虑」而不是「结果」）。

## 关联

- 同族掩蔽：`MEM-20260922-160`（并集掩蔽）、`MEM-20261005-187`（交集掩蔽）。
- 本条是**第三类**：既不是并集也不是交集，而是**多重门串联**下的读数饱和。
- 按压脚本另一条教训（字节面）：文本模式读写把 LF 签出的文件写成 CRLF ⇒
  `RESTORED False`；见 `MEM-20260928-152`。本轮的按压脚本已改 **`read_bytes`/`write_bytes`**。

## 怎么做与复现

```bash
# 基线
uv run --frozen --no-sync python -B -m pytest   tests/e2e/test_dead_letter_run_coordination_matrix.py -q      # 6 passed
# 按压（放开派发方的状态过滤）：
#   首版断言 dispatched == 0 ⇒ 仍 0 ⇒ 不判红（受判面被三重门掩蔽）
#   改 spy 读数后 ⇒ 1 failed
uv run --frozen --no-sync python -B scratch/goal033-cycle2-press.py
# 期望：P1_RED exit=1 1 failed, 5 passed / RESTORED True / FINAL_MATCHES_BASELINE True
```

写新断言时先问：**这条「没发生」的否定面有几条独立来源？** 逐条列出并确认除被判那条外
其余都已置为放行态；做不到就换观测点（spy 到最靠近被判机制的那一步）。

## 适用边界

- 适用于任何「计数为 0 / 集合为空 / 未被调用」形态的弱断言；不适用于直接断言**结果值**
  的断言（那种断言天然可被单变量证伪）。
- 正向对照（同一条输入改一个字段 ⇒ 必须变为「被观测到」）是本条的**载荷**，
  不是可选装饰：没有它，空集无法与空真区分。
- 边界：spy 记录的是**询问**而非**结果**；若被测机制在询问之前就该拦下（例如更早的
  权限门），spy 的位置要选在被判门的**下游**。

## 来源

- `.cursor/plans/tasks/PLAN-20261008-313-goal-033-ec02-dead-letter-run-coordination.md`（实施 + 返工记录）
- `.cursor/plans/rechecks/RECHECK-20261008-314-goal-033-ec02-dead-letter-run-coordination.md`（W-1）
- 留档：`scratch/goal033-cycle2/press-matrix.log`
