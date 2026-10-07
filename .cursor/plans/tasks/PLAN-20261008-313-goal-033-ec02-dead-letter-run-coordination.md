---
id: PLAN-20261008-313
slug: goal-033-ec02-dead-letter-run-coordination
title: GOAL-033 cycle 2（EC-02）：死信恢复 ↔ run 续跑 —— 三面实测 + 按实测登记边界（含一次判据自证伪的返工）
status: DONE
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-314-goal-033-ec02-dead-letter-run-coordination.md
memory_entries:
  - a-masked-claim-cannot-be-falsified-by-one-variable
parent_goal: GOAL-20261008-033
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-033 的 **EC-02**（死信恢复 ↔ run 续跑的协同）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：**不做半个实现**（A/B 必居其一，按实测决定）；
    **不改** run 级状态机（`FAILED` 是终态是既有设计决定 ⇒ 若需改语义必须 ADR，本轮不触发）；
    **不改既有判据断言**（本 PLAN **只新增**一个 e2e 文件）；**不得**宣称安全（`R-M1`），
    **不得**宣称投递语义为恰好一次（**明确否认**）。
objective: >-
    把 GOAL-032 登记的「死信恢复与 run 续跑的自动协同不存在」从**散文**推进到**逐面实测
    判据**，并按实测在 A/B 之间做**有依据的选择**：① 实测三个面 —— run 状态面（默认契约 /
    容忍契约两条组合）、派发方面（`RetryDispatchScheduler` 到底**考虑不考虑**这条 run）、
    任务面（恢复后**谁**交付它：worker 面 vs 编排面）；② 机制边界（run `FAILED --RESUME-->`
    是否合法）；③ 按实测登记结论并写明**为什么不是另一个路径**；④ 判据自身必须能被**单变量
    反证**（首版判据因受多重门掩蔽而无法被单变量证伪 ⇒ 本 PLAN 的返工记录）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **run 状态面两条组合**：① 默认契约（`max_attempts=1`）⇒ 死信与 run **`FAILED`** 同现；
      ② 容忍契约（`on_task_failure: CONTINUE`）⇒ 死信与 run **`DEGRADED`**（非终态）同现。
      两条都断言 ⇒ 「死信 ⇒ run 终态」不是普遍规律。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/e2e/test_dead_letter_run_coordination_matrix.py -q` ⇒ ①②两例绿。
    status: PASS
  - id: AC-2
    criterion: >-
      **派发方面可被单变量证伪**：量的是「派发方**考虑过**这条 run 吗」（spy 记录
      `due_retry_task_ids` 的询问），不是 `dispatched` 计数 —— 后者被第三道门
      （「没有到期重排就跳过」）掩蔽。**正向对照**：同一条 run 改成 `PAUSED` ⇒ 必须被问到
      （否则空集是空真）。
    verify: >-
      该文件的 `test_the_retry_dispatcher_never_even_considers_a_dead_letter_run` ⇒ 绿；
      按压 `scratch/goal033-cycle2-press.py` ⇒ `P1_RED exit=1 1 failed`。
    status: PASS
  - id: AC-3
    criterion: >-
      **任务面逐面**：① worker 面（`kind=EXECUTION`）恢复后 `claim_next` **直接取到** ⇒
      该面上协同**已存在**（无需实现）；② 编排面（`kind=AGENT_SESSION`）worker 面够不着，
      但会话面取得回来 ⇒「能力在，只缺谁来驱动 run」。
    verify: >-
      同文件的 `test_on_the_worker_face_recovery_is_followed_by_automatic_redelivery` 与
      `test_on_the_orchestration_face_the_worker_claim_cannot_reach_the_dead_task` ⇒ 绿。
    status: PASS
  - id: AC-4
    criterion: >-
      **机制边界 + A/B 决策**：`FAILED --RESUME-->` **非法**（`InvalidTransitionError`），
      而 `DEGRADED --RESUME--> RUNNING` **合法** ⇒ run 级自动继续要么改 run 级状态机、
      要么新增扫非 `PAUSED` run 的派发面，**两条都是新机制** ⇒ 按 EC-02 (b) 的 **B 路径**
      如实登记（并写明「为什么不是 A」的机械依据）。
    verify: >-
      同文件的 `test_the_run_state_machine_has_no_edge_from_failed_back_to_running` ⇒ 绿；
      结论写在该文件 docstring 与 GOAL 的「本轮新增残余」。
    status: PASS
  - id: AC-5
    criterion: >-
      **判据自身可被单变量证伪**（本 PLAN 的返工项）：首版 ③ 用 `dispatched == 0` 断言，
      按压「放开状态过滤」**没判红** ⇒ 受判面被另外两道门掩蔽 ⇒ 改为 spy 读数后
      **同一次按压判红**（`P1_RED exit=1 1 failed`）。按压脚本改用**二进制安全读写**
      （首版文本模式读写把 LF 签出的文件写成 CRLF ⇒ `RESTORED False` 且不可归因）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal033-cycle2-press.py` ⇒
      `P1_RED exit=1 1 failed, 5 passed` / `RESTORED True`（带 sha 归因）/
      `FINAL_MATCHES_BASELINE True`；留档 `scratch/goal033-cycle2/press-matrix.log`（CR=0）。
    status: PASS
  - id: AC-6
    criterion: >-
      **既有判据零改动**：本 PLAN **只新增**一个 e2e 文件；`git diff --numstat` 对
      `tests/**` 既有文件零条目（本轮 EC-02 不碰任何既有判据）。
    verify: >-
      `git status --short` 逐条读数；`services/api/scheduler.py` 两次按压后**逐字节复原**
      （sha 相同，见 AC-5 的日志）。
    status: PASS
---

# PLAN-20261008-313 — GOAL-033 cycle 2（EC-02）：死信恢复 ↔ run 续跑的协同

## 验收条件

见 frontmatter `exit_criteria`（AC-1…AC-6）。

## 实施清单

- [x] `tests/e2e/test_dead_letter_run_coordination_matrix.py`（新增 6 例）：三面实测 +
      机制边界 + spy 读数 + 正向对照。
- [x] 按压脚本 `scratch/goal033-cycle2-press.py`（单变量 + 二进制安全 + sha 归因）+ 留档。
- [x] 返工：首版 ③ 的掩蔽缺陷（见 AC-5）已修，并沉淀记忆
      `a-masked-claim-cannot-be-falsified-by-one-variable`。

## 证据

### 三面实测（探针 → 判据）

| 面 | 情形 | 实测读数 |
| --- | --- | --- |
| run 状态 | 默认契约 `max_attempts=1` | run = **`FAILED`**（终态）；任务面 = `['DEAD_LETTER']` |
| run 状态 | 容忍契约 `on_task_failure: CONTINUE` | run = **`DEGRADED`**（非终态）；任务面 = `['DEAD_LETTER', 'SUCCEEDED']` |
| 派发方 | `RetryDispatchScheduler.run_once()` | **恢复前后都不考虑**这条 run（spy 未被询问）；同一条 run 改 `PAUSED` ⇒ **被询问** |
| 任务面（worker） | `kind=EXECUTION` 死信 → `requeue` | `claim_next` **直接取到**该任务 ⇒ 自动再交付**已存在** |
| 任务面（编排） | 编排死信（`kind=AGENT_SESSION`）→ `requeue` | `claim_next` = `None`（claim 只扫 `EXECUTION`）；`acquire_lease` 取得回来 |
| 机制边界 | `FAILED --RESUME-->` | **`InvalidTransitionError`**；对照 `DEGRADED --RESUME--> RUNNING` 合法 |

### A/B 决策（按实测，B 路径）

- **路径 A 的前置条件**（「实测表明恢复后无任何自动交付方」）被实测**证伪了一半**：
  worker 面上自动交付方**本来就在**（`claim_next` 按状态过滤，恢复后立刻可取）⇒
  **那个面上没有东西需要实现**。
- **编排面上**自动继续确实缺席，但实现它需要：改 run 级状态机（`FAILED` 是终态 —— 改语义，
  须 ADR 且超出本 GOAL 的同步集），**或**新增一个扫非 `PAUSED` run 的派发面（新机制）。
  ⇒ 按 **B 路径如实登记**：把确切边界与复现命令写进判据，并列为下一轮输入。
- **为什么不是 A**：A 的成立条件是「无任何自动交付方」；实测给出了**有**的那一半（worker 面），
  而剩下的那一半（编排面）的实现面**不是「扩展既有调度器」而是「改终态语义或新增调度面」**
  —— 那正是 EC-02 (b) 明文划给 B 的情形。

### 按压（单变量，各独立）

```
BASELINE_GREEN 6 passed in 4.11s
P1_RED exit=1 1 failed, 5 passed in 4.71s
RESTORED True scheduler.py 90562a9d9c3d->90562a9d9c3d
FINAL_MATCHES_BASELINE True 6 passed in 4.06s
```

- **P1**（放开派发方的状态过滤，即"顺手实现路径 A"的最朴素形态）⇒ **1 failed**
  （③ 的 spy 读数：死信 run 被纳入考虑）。
- **首版按压没判红** —— 那是**真缺陷**（我的判据被掩蔽，无法被单变量证伪）；
  返工后同一次按压判红。这条已沉淀记忆。

### 返工记录（两条，都是**我自己的**缺陷）

1. **判据被掩蔽**：`dispatched == 0` 有三个独立来源（状态过滤、重建能力、无到期重排）
   ⇒ 改其中一个读数不变 ⇒ **假绿**。改为 spy 记录「是否被考虑」+ 正向对照（改 `PAUSED`
   必须被问到）。
2. **按压脚本破坏字节**：首版用 `read_text` + `write_text`，把 LF 签出的 `scheduler.py`
   写成 CRLF ⇒ `RESTORED False`。改为 `read_bytes`/`write_bytes`（二进制安全），
   `RESTORED True` 且 sha 可归因。
3. **规模门抓到用例过长**：worker 面那条用例 **52 行**（> 50 行硬上限）⇒ 把「造一条
   worker 面死信」提为 `_worker_face_dead_letter` 助手（**只搬动构造代码，断言一条未改**）；
   `test_the_retry_dispatcher_never_even_considers_a_dead_letter_run` 48 行，未超限。

## 影响报告

- **Domain / API / schema 变化**：**无**（本 PLAN 零产品改动）。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：无。
- **观测隐私**：无新增出口。
- **上游版本影响**：无。
- **下一项任务**：cycle 3 = EC-03（续跑覆盖矩阵机械化：受判面 = 声明集穷尽枚举）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | DONE | cycle 2 落地：三面实测（run 状态两条组合 / 派发方 spy / 任务面两路）+ 机制边界；按实测走 **B 路径**（如实登记：run 级自动继续需改状态机或新增调度面）；**返工一次**（首版 ③ 被三重掩蔽、无法单变量证伪 ⇒ 改 spy 读数后按压判红；按压脚本改二进制安全读写）。`latest_recheck` = `RECHECK-20261008-314`（PASS_WITH_WARNINGS）。 |
