---
id: RECHECK-20261009-362
slug: goal-041-ec02-04-bounded-retry-on-the-crash-window
title: 独立复检：GOAL-20261009-041 cycle 1（失败重试面的崩溃窗口去重 + 计数口径 + 静默丢弃缺陷）
plan_id: PLAN-20261009-361
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-09
completed_at: 2026-10-09
owners:
  - root-agent
---

# RECHECK-20261009-362 — GOAL-20261009-041 cycle 1 独立复检

复检对象：`PLAN-20261009-361`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 立题复核（修前 / 修后读数，独立重跑）

**修前**（`scratch/goal042_probe_unbounded_retry.py`，在**未改**的驱动上）：
`allowed=2` ⇒ 判定序列 `RETRY_FAILED_RUN × 5`、`cited_facts` 全为 `attempts=1/2`、
`bounded=false`、`unbounded_retry=true`。

**修后**（同一探针）：`decision_kinds = ["RETRY_FAILED_RUN", "STOP_RUN_FAILED"]`、
`attempts=1/2 → 2/2`、`bounded=true`、`unbounded_retry=false`、落库 run 始终 `[[1,"FAILED"]]`。

**四组上界**（`scratch/goal042_probe_retry_faces.py`，独立重跑）：

| allowed | 判定序列 | converged | steps_within_bound | no_second_run | attempts_ceiling |
| --- | --- | --- | --- | --- | --- |
| 1 | `STOP_RUN_FAILED` | ✅ | ✅ (1) | ✅ | 1 |
| 2 | `RETRY_FAILED_RUN` → `STOP_RUN_FAILED` | ✅ | ✅ (2) | ✅ | 2 |
| 3 | `RETRY_FAILED_RUN` → `DEDUP_FAILED_RUN` → `STOP_RUN_FAILED` | ✅ | ✅ (3) | ✅ | 3 |
| 4 | `RETRY_FAILED_RUN` → `DEDUP_FAILED_RUN` ×2 → `STOP_RUN_FAILED` | ✅ | ✅ (4) | ✅ | 4 |

**对照臂（正常落库的重试）**：`allowed=1/2/3` ⇒ `started = 0/1/2`、序列
`…RETRY_FAILED_RUN × (allowed-1)` → `STOP_RUN_FAILED`（**逐字保持** GOAL-040 行为）。

### 2. 三形态互不混用（AC-2 / AC-3，独立重跑）

- `DEDUP_FAILED_RUN` 分支**不调用启动面**（实测 `h.started == []`）且 `started_run_id is None`；
- 判词点名 `claimed run <id>` 与已用数（实测 e2e：`attempts=2/3` + `claimed run ghost-single`）；
- **结论面的 `DEDUP` 未被混用**：`CONTINUE` 认领下一序号未落库 ⇒ 仍落 `DEDUP`
  （`test_the_conclusion_face_dedup_is_unchanged`，独立重跑绿）；
- **排序是判据的一部分**：按压 R-1（交换「用尽 / 去重」两分支）⇒ 三例判红（下节）。

### 3. 两向反证（AC-5，独立重跑）

| 按压 | 改坏什么 | 结果（独立重跑） |
| --- | --- | --- |
| `R-1` | 交换「用尽」与「去重」两分支的顺序 | RED（3 例：驱动收敛例 + e2e 两例） |
| `R-2` | 「未落库的认领」不计入尝试数 | RED（3 例：去重例 + 收敛例 + e2e 计数例） |
| `R-3` | `decided_at` 不归一（直接用挂钟） | RED（2 例：驱动收敛例 + 同刻度留痕例） |

复原后 raw `sha256` **逐字节相同**（三条按压后均为 `c93a3f67953c…`）；
判词归档进树 `.cursor/plans/goals/evidence/GOAL-20261009-041-press-two-way.txt`（199 B / `CR=0`）。

### 4. 本轮新发现的第二个缺陷（**独立复现**，本条属"复检发现"）

**形态**：决策自然键 `(program_id, after_index, decided_at)` + 静默冲突处理
（SQLite `INSERT OR IGNORE` / PG `ON CONFLICT DO NOTHING`）⇒ **同一时钟刻度**内的多条决策
**互相顶掉**。独立复现读数：

```
紧循环连录 10 条同 (program_id, after_index) 的 DEDUP 决策 ⇒ decisions_of 返回 1 条
紧循环连录 50 条 ⇒ 返回 2 条
间隔 20ms / 1ms 各录 10 条 ⇒ 各返回 10 条（⇒ 是分辨率撞车，不是键设计错）
连续 5 次 Timestamp.now() ⇒ 5 个**逐字相同**的微秒值
```

**危害**：决策面是读面「为何停」的唯一事实源；静默少条 ⇒ 从决策面计数时**偏低** ⇒
声明的上界被绕过而**没有任何红**（本轮 EC-02 的计数正依赖它）。
**处置**：驱动侧把 `decided_at` 归一为**该程序内严格递增**（`_record`），
不引入新依赖、不改 schema、不改 Port 契约。**已沉淀 `MEM-20261009-211`。**

### 5. 改既有判据的申报（承 `MEM-20261009-210`）

本 cycle 对**既有**判据文件只动**一处**：

| 文件 | 谓词形态 | `numstat`（相对 `89e0d85`） | 判定 |
| --- | --- | --- | --- |
| `tests/domain/test_research_program.py` | **未改**（仍是 `kinds == {…}` 集合相等） | `+4 / -0` | **纯加法登记**（新增枚举值进集合，否则该例必红） |

**消费面 / 知识面 / 推进面三个 e2e 文件未触碰**（`git diff --numstat` 零输出）；
**既有断言的删除行数 = 0**。

### 6. 门链与记录面（AC-6）

`ruff format --check`（`tests/` + `packages/` **864 文件**全绿）/ `ruff check` /
`mypy` strict / **规模门**（`program_runner.py` 423 行 ≤ 450；函数全部 ≤ 50 行 ——
`_failed_round` 曾 **60 行**，已拆 `_bounded_stop` / `_returning_claim_stop`）
对全部改动文件全绿；`tests/e2e` **319 passed, 13 skipped**；
治理 `validate.py` 绿；主判据例数只增不减（驱动 13 → **18**；e2e 新增 **6**）。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-6 逐条独立成立：修前失真复现、修后四组上界全部
**有界且收敛**、三形态互不混用、两向反证打满、**并额外定位并修复了同轴的第二个缺陷**
（决策静默顶掉）。

### Warnings

- **W-1（计数口径的变化面，如实申报）**：已用尝试数从「同序号落库行数」改为
  「落库行数 + 未落库的认领数 + 被阻塞的推进数」。**正常落库路径读数不变**（对照臂实测
  `started=0/1/2` 与 `attempts=N/N` 逐条保持）；变化**只**发生在崩溃窗口形态。
  这类口径变更属**受判面扩展**（不是收窄），但仍是**语义变更**，故如实登记。
- **W-2（第二个缺陷的修法是驱动侧，不是存储侧）**：存储层的自然键与静默冲突处理
  **未变**（Port 契约「同一时刻重复写 = 幂等空操作」逐字保持）⇒ **直接调用 store 的
  第三方**仍可撞车并静默丢事实。要让存储层免疫需**代理主键 + 迁移**（本轮不做，登记）。
- **W-3（`DEDUP_FAILED_RUN` 是本轮**新增**的判定种类）**：旧读者把它读作未知字符串
  （读面本就逐条透出 `kind` 原文）。**未**在 DTO / OpenAPI / 前端登记枚举
  （实测三方零引用）—— 若有下游按枚举白名单分派，需要时另行登记。
- **W-4（承继残余原样保持）**：GOAL-041 的 `S-1`（退避未做）/ `S-2`（跨序号 / 跨程序
  认领去重未做）/ `S-3`（未落库 run 的**归因**未做）；GOAL-040 的 `R-1`…`R-3`；
  GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；
  `R26-*` 终态；未覆盖范围逐条保持。**不得**据此宣称项目安全（`R-M1`）；
  **不得**宣称投递语义为那四个字（**明确否认**）。
