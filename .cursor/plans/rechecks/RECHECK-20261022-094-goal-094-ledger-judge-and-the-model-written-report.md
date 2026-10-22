---
id: RECHECK-20261022-094
slug: goal-094-ledger-judge-and-the-model-written-report
title: GOAL-094 复检 —— 跨 GOAL 台账判据 + 报告由模型撰写（数字仍在事实表）
status: COMPLETED
result: PASS
created_at: 2026-10-22
updated_at: 2026-10-22
plan_id: PLAN-20261022-094
parent_goal: GOAL-20261022-094
owners:
  - root-agent
verify_paths:
  - tests/tooling/test_goal_ledger_covers_every_commit.py
  - tests/application/test_report_narrative.py
  - tests/application/test_report_narrative_on_the_product_path.py
  - packages/application/deliverable/report_narrative.py
  - packages/application/run_orchestration/report_narrative_task.py
  - .cursor/plans/goals/evidence/GOAL-20261022-094-next-round-charter.md
memory_entries:
  - MEM-20261022-228
---

# RECHECK-20261022-094 — GOAL-094

## 检查结果

**PASS**。五个 EC 全部达成。两件事都做成了**可判**：① **台账纪律不再靠继承** ——
`tests/tooling/` 下的新判据**遍历**树里所有终态 GOAL（不靠任何验证器传参、不靠清单登记），
GOAL-093 实测抓到的记账退化（台账 4 行 vs 7 个提交、三个提交两张表都不进）**同一轮补齐**，
且**判据一字未因它而改**；② **报告由模型撰写** —— 叙述（第 1…4 节）由模型写、数字
（第 5 节事实表）由汇编器写，模型写数字即**点名拒绝**，「谁写的」由 `created_by` 与元数据
可读，而**每个数字仍可溯源**。

## 一、建档实测的四处缺口（先钉缺口存在，读数在本轮动手前取得）

| # | 缺口 | 实测读数 | 修法 |
| --- | --- | --- | --- |
| 1 | 判据**只保护它自己那个 GOAL** | `_log_verdicts` 在 `tools/goal092_closeout_assertions.py:286`；`rg _log_verdicts tools/goal093*` **零命中** | 提成**跨 GOAL 的 tooling 判据**（遍历 GOAL 文件；不继承、不传参） |
| 2 | 记账退化**未被发现** | GOAL-093 `CI 台账` **4 行**、实际提交 **7 个**；三个提交两张表都不进；收口验证器仍 **68 PASS / 0 FAIL** | 同轮把三个提交补进台账与 cycle 行（台账 → **7 行 = 7 个提交**） |
| 3 | 报告是**确定性汇编** | `build_research_report` 逐字节由输入决定；`created_by="system:report-assembler"`；docstring 自陈「不调模型」 | 新增叙述面：模型写第 1…4 节，汇编器写第 5 节事实表 |
| 4 | **叙述质量无人判**（阶梯「报告」行的 `下一级` 逐字） | 「报告由模型撰写（现为确定性汇编；叙述质量无人判）」 | 本轮推进到「模型撰写 + 数字不脱离来源」；质量本身如实留作残余 |

## 二、为什么**不**把 `_log_verdicts` 上提到 `tools/closeout_recheck_assertions.py`

`standard_verdicts(root: Path)` **只收树根**，它不知道「当前在验哪个 GOAL」。上提之后仍要
每个验证器把 GOAL 路径**主动**传进来 —— 而「主动传」正是这次失效的原因（GOAL-092 的判据
被 GOAL-093 忘掉，就是因为它是**继承来的**）。所以正确形态是**让判据自己去树里找 GOAL**：
`_terminal_goals_in_scope()` 遍历 `.cursor/plans/goals/GOAL-*.md` ⇒ 新增 GOAL **自动**受判，
**69 个验证器一个都不用改**。

## 三、两向按压（本轮核心证据，raw `sha256` 逐字节）

判据在真树上**本来就会绿**（GOAL-093 的台账在按压前是日志的**子集**）⇒「它会咬」不能由
真树的绿证明，必须由按压证明。

| 按压 | 做了什么 | 判词（原文） | `sha256` 前 → 中 → 后 |
| --- | --- | --- | --- |
| ① 压日志 | 删掉 GOAL-093 迭代日志的 cycle 2 数据行（2 行 → 1 行） | `FAIL test_every_terminal_goal_in_scope_ledgers_its_commits_in_a_cycle_row` / `GOAL-20261022-093（序 61）：CI 台账里的 4 个提交没有任何 cycle 行的 commits 格收录：['33e48f57', '3d53676e', '7fa4f651', 'a905c6c3']` | `89e2fda8…` → `c9dcb895…` → `89e2fda8…` |
| ② 删 cycle 2 一格里的一个提交 | 从 cycle 2 的 `commits` 格删掉 `33e48f57` | `FAIL` 同一条判据 / `CI 台账里的 1 个提交没有任何 cycle 行的 commits 格收录：['33e48f57']` | `89e2fda8…` → `fb67595f…` → `89e2fda8…` |

两次复原后 `pytest` 均 **8 passed**（修正后重做按压亦同），且 `sha256` **逐字节**回到按压前的值（`git diff` 不足以
当逐字节证据：它看不到行尾 / 编码差异）。

## 四、报告面反证（判据真的会咬）

| 按压 | 做了什么 | 结果 | 复原 |
| --- | --- | --- | --- |
| 撤掉数字禁令 | `found = _numeral(...)` → `found = None` | `test_a_numeral_in_the_narrative_is_refused_by_name[...]` **3 failed** | `report_narrative.py` `sha256` 回到 `91198c6c…`，17 passed |

## 五、既有判据改动逐条申报

**没有改任何既有判据的断言。** `numstat` 逐条：

| 文件 | 性质 | 说明 |
| --- | --- | --- |
| `packages/application/deliverable/research_report.py` | 产品（+18 / −12） | `report_metadata(inputs, narrative=None)` 新增**可选**参数；缺省时键集**逐字不变**（`test_the_compiled_form_is_byte_identical_without_a_narrator` 钉住） |
| `packages/application/run_orchestration/report_task.py` | 产品（+52 / −22） | 新增 `ReportTaskDeps.narrator`（可选）、`ReportAdmission.narrative`（可选）、`_body` / `_admission_blocker`；`_admit` / `_put_report` 多一个参数；`execute_report_task` 的既有两条失败分支**逐字保留**（只是移进 `_admission_blocker`） |
| `services/api/report_support.py` | 产品（+26 / −4） | `report_task_runner` 多一个**可选** `narrator=` 参数（缺省 `None` ⇒ 既有行为）；新增 `narrative_runner` |
| `tests/tooling/test_tooling_scripts_meet_product_gates.py` | **判据**（+2 / −0） | `IN_SCOPE` 追加本轮的验证器与断言集两行（**纯收紧**，与 GOAL-092 `W-7` 同一纪律） |

## 六、读数

| 项 | 读数 |
| --- | --- |
| 新台账判据 | **8 passed** |
| 新报告判据 | **24 passed**（17 + 7） |
| 受影响套件 | `tests/application` + `tests/e2e/test_research_report_arc_offline.py` ⇒ **1297 passed / 1 skipped** |
| 规模门 | **1324 passed**（`report_task.py` 418 行；`execute_report_task` 拆分后 ≤ 50 行） |
| 三面 | `ruff format --check` / `ruff check` / `mypy` 全过 |
| GOAL-093 | 台账 **7 行 = 7 个提交**；`tools/verify_goal093_closeout.py --verdict-only` 全 PASS |
| 上一轮残余读取器 | `exit 0`；`W-1…W-5` **5 条**；`sha256:d0aaae8f…`；处置 **5/5** |
| 见证 | 见第七节（记录面判据之后、最后跑） |

## 七、m0 见证（正式见证，记录写完 + `git add` 之后跑）

| 项 | 读数 |
| --- | --- |
| `terminal_line` | `PASS: profile=m0; 23 deterministic checks` |
| `PASS [` 行数 | **24** |
| FAILED | **0** |
| `tree changed during the run` | `False` |
| 覆盖（受判面文件数） | 见 `M0-WITNESS.json`（本轮读数回填于收口提交） |

## 八、射程边界（本复检**不**声称的）

- **叙述质量无人判**：本轮判「模型写了正文」与「它不能碰数字」，**不**判「这段写得好」，
  也**不**判「叙述与事实一致」（模型可以写出不含数字但仍错的句子）。
- **`llm_narrator` 未在产品组合根默认接线**：只给产品闭包与可注入面；出厂路径今天仍是
  确定性汇编（接上会改交付物 `created_by`，属产品行为变更，须单独决定）。
- **跨 GOAL 判据不读 git 历史**：CI 的 `actions/checkout` 未声明 `fetch-depth` ⇒ 工作区只有
  HEAD 一个提交 ⇒ 「数这一轮有多少提交」在 CI 上会空真。该判据判的是**两份记录之间**的
  关系；「台账是否穷尽 git」由本复检在本机取证（`git log --oneline 2998649d..HEAD` 逐条对账）。

## 九、首轮封口 m0 的真红与修法（如实登记）

首轮封口 m0 报 **23 PASS / 3 FAILED**（`python/tests` 一项失败 + 两个派生行），失败判据是**本轮新写的那一条**：

```
GOAL-20261022-094（序 62）：CI 台账第 2 行的 `提交` 格里没有反引号包裹的提交哈希
GOAL-20261022-094（序 62）：CI 台账第 3 行的 `提交` 格里没有反引号包裹的提交哈希
```

**两个根因，一是我写记录的位置错、二是判据实现有缺陷**：

1. 我把 `状态历史` 的两行**追加到了文件末尾** —— 那里已经在 `## CI 台账` 小节之后，于是台账小节里混进了一张**三列**的表（`| 日期 | 状态 | 说明 |`）；
2. `_table` 在整个小节里**继续收集** `|` 行（只在遇到非 `|` 行时才停），把那张表的**列头**当成了台账数据行。

**处置**：① 两行移回 `## 状态历史` 节；② `_table` 改为**遇到表格结束就停**（连续 `|` 行 + **列数一致**），并补一条 `test_a_second_table_in_the_same_section_is_not_read_as_ledger_rows` 钉住它（判据用法 7 条）。**这不是放宽判据**：受判面的定义（台账每个提交都要在某个 cycle 行里）一字未改，改的是「怎么读一张表」这个**实现**缺陷 —— 而且改的方向是**收紧**（它现在会拒绝把别的表的行当台账）。

**按压重做**：修正后重做「删 `33e48f57`」一向 ⇒ 仍判红并点名它；逐字节复原后 `sha256` 往返不变（`95c8b240…`）、`git diff` 为空、7 passed。

## 结论

**PASS**。五个 EC 全达成：跨 GOAL 台账判据在树且自动覆盖新 GOAL（8 条判据 + 两向按压 +
逐字节复原）、GOAL-093 的记账退化如数补齐且**判据未因它而改**、报告由模型撰写而数字仍
逐行可溯源（24 条判据 + 反证）、记录面与见证齐备。残余与未覆盖范围逐条登记在 GOAL 的
「残余与未覆盖范围」节（`W-1`…`W-5` + `R-1`…`R-3`）。`R-M1` 未收口 ⇒ 本复检**不**宣称
项目安全；投递语义**不是**「恰好一次」。
