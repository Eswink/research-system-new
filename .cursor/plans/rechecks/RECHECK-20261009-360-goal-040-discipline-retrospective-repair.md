---
id: RECHECK-20261009-360
slug: goal-040-discipline-retrospective-repair
title: 独立复检：GOAL-040 纪律回溯修复（三处既有 e2e 判据的谓词越界 + 显式形态恢复 + 结论面覆盖回补）
plan_id: PLAN-20261009-359
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-09
completed_at: 2026-10-09
owners:
  - root-agent
---

# RECHECK-20261009-360 — GOAL-040 纪律回溯修复 独立复检

复检对象：`PLAN-20261009-359`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 两树实跑复核（AC-1，独立重跑读数）

同一探针（`scratch/goal041_probe_final.py`，同装配、同场景）在两棵树上各跑一次：

| 场景 | `49b2c7d`（干净 checkout） | HEAD |
| --- | --- | --- |
| consumption/normal | `[1,2]` S,S · `CONTINUE` · started | `[1,2]` S,S · `CONTINUE` · started |
| consumption/mismatch | `[1,2]` S,**F** · `CONTINUE` · started | `[1,2]` S,**F** · `CONTINUE` · started |
| consumption/missing-path | `[1,2]` **F,F** · `CONTINUE` · started | **`[1]` F** · **`STOP_RUN_FAILED`** · not started |
| knowledge/missing-provider | `[1,2]` **F,F** · `CONTINUE` · started | **`[1]` F** · **`STOP_RUN_FAILED`** · not started |
| advance/reject | `[1]` **F** · **`STOP_RULE`** (+ `verdict REJECT`) | `[1]` F · **`STOP_RUN_FAILED`** |
| conclusion-face（cross / program） | `[1]` **S** · `STOP_RULE` `verdict PASS` | `[1]` S · `STOP_RULE` `verdict PASS` |

三个 e2e 文件在**两棵树上各自全绿**（各 16 例，独立重跑）。

**读数修正了一条立题描述**：失败轮**不是**「没有任何落库结论」——那一轮仍有 `produce` phase
落库的 `verdict PASS`；失真形态是**旧代码把「这一轮跑失败了」读成「结论判续」**
⇒ 第 2 轮真的被起出来。**以实跑为准**。

### 2. 越界判定与谓词逐条比对（AC-2）

`git diff --numstat 49b2c7d HEAD -- tests/e2e/` 删除行读数：

| 文件 | 新增 | 删除 |
| --- | --- | --- |
| `tests/e2e/test_cross_run_consumption_is_decidable.py` | 15 | **5** |
| `tests/e2e/test_cross_run_knowledge_on_the_run_path.py` | 13 | **5** |
| `tests/e2e/test_program_advance_on_the_run_path.py` | 14 | **5** |
| `tests/e2e/program_advance_support.py` | 2 | 0 |
| `tests/e2e/test_program_stop_reasons_are_decidable.py`（新增文件） | 125 | 0 |

**三行被替换的谓词（原文，逐条）**：

1. `test_cross_run_consumption_is_decidable.py`
   - 删：`assert [row["program_index"] for row in runs] == [1, 2], runs`
   - 增：`assert runs and runs[0]["program_index"] == 1, runs` +
     `second = str(runs[1]["run_id"]) if len(runs) > 1 else first`
   - **谓词不等同**：`== [1, 2]`（恰好两轮 + 第 2 轮存在）→ `runs[0] == 1`（至少一轮）；
     且 `second` 在只有一轮时**回退到第 1 轮** ⇒ 调用方拿到哪一轮**取决于被测行为**。
   - **越界判定**：属 `fix_policy` 同轮同步集**之外**（谓词被改，不是「一字未改」的加法 / 搬迁）。
2. `test_cross_run_knowledge_on_the_run_path.py`
   - 删：`second = advance(client, program_id)` + `assert second["started_run_id"], second` +
     `run_id = str(second["started_run_id"])`（三条，取第 2 轮）
   - 增：`first = advance(...)` + `run_id = str(first["started_run_id"])`（取第 1 轮）
   - **谓词不等同**：受判轮次 **2 → 1**（观测宽度收窄；旧树两轮 `run.failed` 正文逐字相同）。
   - **越界判定**：同属同步集**之外**（改的是受判形态 / 观测轮次）。
3. `test_program_advance_on_the_run_path.py`
   - 删：`def test_a_rejected_verdict_stops_the_program_by_conclusion()` +
     `assert second["decision"]["kind"] == _STOP_RULE, second` +
     `assert "verdict REJECT" in second["decision"]["cited_facts"]`
   - 增：`test_a_rejected_verdict_stops_the_program_on_the_failure_face()` +
     `== _STOP_RUN_FAILED` + `"state=FAILED" in cited_facts`
   - **谓词不等同**：断言对象从**结论面**换成**失败面**；且**结论面在 e2e 上失去覆盖**
     （新增文件零条 `STOP_RULE` 用例；其 docstring 的「由……覆盖」一句**与事实不符**）。
   - **越界判定**：同属同步集**之外**；这一处还额外构成**覆盖缺口**（见本节第 4 段）。

**结论（如实登记，不淡化）**：`GOAL-20261008-040` 的 `fix_policy` 同步集清单**只有通用条款、
无任何条目** ⇒ 三处改动**均未逐条枚举**，属该 GOAL `escalation_triggers` 的
「需要改**同轮同步集以外**的既有判据断言」形态。改动记录里「三处的断言强度未降」
这一句对第 1 处**不成立**（容错回退把「恰好两轮」降为「至少一轮」）。

### 3. 恢复受判强度（AC-3，独立重跑）

- `tests/e2e/` 四文件 **21 passed**（`--no-randomly` 独立重跑）；
- `test_program_advance_on_the_run_path.py` 用例数 **6 → 7**（回补结论面用例）；
- 三个改动文件 `grep -c "^def test_"`：消费 4 / 知识 6 / 推进 7，**无一减少**；
- 三个文件 `CR=0`（逐字节扫 `\r`）；
- 四道门（`ruff format --check` / `ruff check` / `mypy` strict）对三个文件**全绿**。

**回补的形态是实测的**（不是照抄旧用例）：一轮 `SUCCEEDED` + `continue_on=["ACCEPT"]`
⇒ `STOP_RULE` + `cited_facts == ["verdict PASS"]` + `run_count == 1` + 终态 `SUCCEEDED`；
**两件事一起断言**（种类 + 终态）⇒ 它不是靠失败面蒙对的。

### 4. 两向反证（AC-4，独立重跑）

五条按压（P-1…P-5）**全部判红**，复原后 raw `sha256` **逐字节相同**：

| 按压 | 目标 | 结果 |
| --- | --- | --- |
| P-1 | 结论面用例的规则声明 `["ACCEPT"]` → `["PASS"]` | RED（实测那时落 `CONTINUE`） |
| P-2 | 消费面失败形态断言 `[1]` → `[1, 2]` | RED |
| P-3 | 消费面成功形态断言 `[1, 2]` → `[1]` | RED |
| P-4 | 知识面失败形态断言 `[1]` → `[1, 2]` | RED |
| P-5 | 知识面成功形态断言 `[1, 2]` → `[1]` | RED |

归档进树：`.cursor/plans/goals/evidence/GOAL-20261008-040-repair-press-two-way.txt`（613 B / `CR=0`）。

### 5. 记录面与治理（AC-5 / AC-6）

MEM-20261009-210 在树 + `INDEX.md` 有行；MAINLINE 修订记录一行；本 PLAN / 本 RECHECK 在位；
治理 `validate.py` 绿；`tests/tooling/test_mainline_program_is_intact.py` 绿。

### 6. 独立复检中新发现的两个同族缺陷（如实登记，不在本轮修复面内）

- **F-1（`verify_goal040_closeout.py` 加载错了断言集）**：该文件声明
  `ASSERTIONS = "tools/goal040_closeout_assertions.py"`（并因此进入
  `test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`），但 `_load_assertions()`
  实际加载的是 **`goal037_closeout_assertions.py`**。实测：跑 `verify_goal040_closeout.py`
  产出的 73 条判词里 **0 条**来自 `goal040_closeout_assertions.py`（`ec02-three-new-kinds`
  等 20 条断言名**一条都不出现**）⇒ **GOAL-040 收口时其自有的 20 条断言从未运行**。
- **F-2（同族：`verify_goal038/039_closeout.py` 同样加载 037 的那份）**：三处（038/039/040）
  形态相同。**实测补充**：把三份真正的断言集直接在当前树上跑，**各自 0 FAIL**
  （038: 21 条 / 039: 21 条 / 040: 20 条）⇒ 后果是**覆盖面丢失**而非**假绿**
  （被加载的那份恰好也都绿）。**F-1/F-2 不在本轮修复面内**（本轮只做纪律回溯修复），
  登记为序 9 的输入。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-6 逐条独立成立：三处越界**已如实登记**
（`numstat` 删除行读数 + 三行被替换谓词原文）；受判强度**已按显式声明形态恢复**
（成功面恰好两轮 / 失败面恰好一轮 / 结论面覆盖回补）；两向反证打满。

### Warnings

- **W-1（越界事实不淡化）**：`GOAL-20261008-040` 对三个既有 e2e 判据的改动属其
  `fix_policy` 同步集**之外**，且清单**未逐条枚举**；改动记录里「断言强度未降」一句
  对 `_two_rounds` 的容错回退**不成立**。本修复 cycle 是对该事实的处置，**不**追溯改写
  GOAL-040 的终态（只追加迭代日志行 + 本 RECHECK 登记）。
- **W-2（两处受判面收窄，如实申报）**：消费面 `missing-path` 与知识面 `missing-provider`
  的**受判轮次 2 → 1**（观测宽度收窄）。**理由**：旧树两轮判词 / 失败正文**逐字相同**
  ⇒ 谓词等价、观测宽度不同；新形态**额外断言**「恰好一轮 + 失败面判停」（旧形态没有这条）。
  **不得**称「强度不变」。
- **W-3（F-1 / F-2 未修）**：`verify_goal038/039/040_closeout.py` 加载错断言集
  （三处同族）；本轮回溯修复**不含**它们，登记为序 9 输入。
- **W-4（承继残余原样保持）**：GOAL-040 的 `R-1`…`R-3`、GOAL-039 的 `Q-1`…`Q-3`、
  GOAL-038 的 `P-1`…`P-3`、GOAL-037 的 `O-1`…`O-5`、`R26-*` 终态、未覆盖范围逐条保持；
  **不得**据此宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
