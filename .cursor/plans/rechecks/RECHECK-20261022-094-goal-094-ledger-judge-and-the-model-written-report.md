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

读数口径：`git diff --numstat 2998649d..<收口提交>`（`+` = 新增行 / `−` = 删除行）。
**四个既有文件被改动，其余全是新增**（`numstat` 里没有第四个数）。

| 文件 | numstat | 性质 | 说明 |
| --- | --- | --- | --- |
| `packages/application/deliverable/research_report.py` | **+21 / −14** | 产品 | `report_metadata(inputs, narrative=None)` 新增**可选**参数；缺省时键集**逐字不变**（`test_the_compiled_form_is_byte_identical_without_a_narrator` 钉住） |
| `packages/application/run_orchestration/report_task.py` | **+80 / −25** | 产品 | 新增 `ReportTaskDeps.narrator`（可选）、`ReportAdmission.narrative`（可选）、`_body` / `_admission_blocker`；`_admit` / `_put_report` 多一个参数；`execute_report_task` 的既有两条失败分支**逐字保留**（只是移进 `_admission_blocker`） |
| `services/api/report_support.py` | **+31 / −2** | 产品 | `report_task_runner` 多一个**可选** `narrator=` 参数（缺省 `None` ⇒ 既有行为）；新增 `narrative_runner` |
| `tests/tooling/test_tooling_scripts_meet_product_gates.py` | **+3 / −0** | **判据** | `IN_SCOPE` 追加本轮的验证器 + 断言集两行，并把既有「GOAL-031…」那行的注释沿用（**纯收紧**，与 GOAL-092 `W-7` 同一纪律） |
| `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` | **+1 / −0** | **判据** | 把 `tools/verify_goal094_closeout.py` 加进**验证器清单**（`_VERIFIERS`）。**此前漏登记**：不登记它，「声明 == 实载」与「断言集可执行」两条就看不见本轮的验证器（本轮自审补上） |

**为什么这五处都不算「改判据使其通过」**：四处是**新增可选面**（缺省逐字不变，有两个
`byte-identical` 判据钉住）；两处 `tests/tooling` 的改动都是**纯收紧**（只加受判对象，
不删条目、不改任何断言）。`git diff --numstat` 的删除行全部落在 `report_task.py` /
`research_report.py` / `report_support.py` 的**函数体搬移**（`_admission_blocker` 抽出）与
**签名扩展**上，没有一行删在判据文件里。

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

## 十、两树复检与终局读数（收口时实证）

| 项 | 读数 |
| --- | --- |
| 两树复检 | `TREE current … exit=0 verdicts=77` / `TREE clean … exit=0 verdicts=77` / `COMPARE identical=True` / `TWO-TREE PASS`；两树 `sha256` 逐字相同 （`9bb0a1c98cbcc5661b9e7eefeaf3b471c428d911fcc07717eaa17f85d303012a`）|
| 收口验证器 | `tools/verify_goal094_closeout.py --root . --verdict-only` ⇒ **77 PASS / 0 FAIL** |
| 治理校验 | `Cursor 治理验证通过`（ALL_PLAN / Task Plan / Recheck / Memory 交叉引用一致；GOAL 循环记录结构合规）|
| 凭据审计 | 四面 `offenders=0`（tracked 4614 / records 1022 / config_db 1 / logs 901）|
| 终局见证 | `b07c3398` 的树：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、覆盖 **4584**、`tree changed during the run: False` |
| CI（六个提交，逐条） | `80e844b1` / `38edc9ac` / `b07c3398` / `b11ab450` / `f8c61422` ⇒ M0 **八 job 全 success**；`b911e4a0` ⇒ **2/8 判红**（见证与树失配：记录改在跑门之后，判据正确、未改），由 `b11ab450` 重跑门重封见证处置；`068e16c4` ⇒ attempt 1/2 各 1 `cancelled`（`quality-windows-latest` 撞 **20 分钟作业上限**，实测 20:03 / 20:07；同一 job 在 `b11ab450` 上 19:19 通过）⇒ attempt 3 **八 job 全 success**。**阈值一字未动**。CodeQL 三 job 在上述各提交全 `success` |

## 十一、完成核验判负后的四项补正（逐条，含实跑读数）

第四轮完成核验指出四处**验证强度 / 记录自洽**的缺口（不是产品缺陷）。逐条处置：

| # | 判负 | 补正 | 实跑读数 |
| --- | --- | --- | --- |
| 1 | EC-03 的 `verify` 写「`verify_goal093_closeout.py` ⇒ 全 PASS」，但**没有任何一次它的真实输出** —— 违反「未实跑不得记 PASS」 | 在本树实跑并把读数写进 EC-03 的 `verify` | `uv run --frozen --no-sync python -B tools/verify_goal093_closeout.py --root . --verdict-only` ⇒ **exit 0**、`grep -c '^PASS'` = **68**、`grep -c '^FAIL'` = **0**（`--verdict-only` 略去 `SUMMARY` 行，故以两条 grep 计数取证） |
| 2 | 自指边界段写「`b07c3398` 之后再无提交改动受判面：本轮**到此为止**」，而同表随后有 `b911e4a0`、`b11ab450` —— 段与表**自相矛盾** | 重写该段：**逐条点名** `b911e4a0`（台账补记 + 两树读数）与 `b11ab450`（完成后重跑 m0 并封印见证），并写明「链条的地基是**最后一次跑门的那棵树**，不是表的最后一行」 | 见 GOAL 的「自指边界」段（现在三个只改记录的提交各有一行） |
| 3 | RECHECK 第五节声称「`numstat` 逐条」，却漏了 `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的 **+1**（把本轮验证器加进 `_VERIFIERS`） | 重写该表：改用**实测 `numstat`**（`git diff --numstat 2998649d..`），五处改动逐个列出含该 +1 | 表内读数：`research_report.py` +21/−14、`report_task.py` +80/−25、`report_support.py` +31/−2、`test_tooling_scripts_meet_product_gates.py` +3/−0、`test_closeout_verifiers_run_their_own_assertions.py` **+1/−0** |
| 4 | EC-04 的「接上叙述者 ⇒ `Artifact.created_by` 是 `model:<endpoint>/<returned>`」只由 `inspect.getsource` 的**子串**证明；`llm_narrator` 只测了凭据缺失分支，**正常解析路径未测** | 新增 `tests/application/test_report_task_narrator_behaviour.py`（**8 条**）：真的跑 `execute_report_task` → 从 `FakeArtifactStore` 读回 `created_by`；`llm_narrator` 用假 gateway + 假 resolver 走正常路径 | **8 passed**；两向按压：把 `created_by` 写死 ⇒ **3 条判红**；让 `llm_narrator` 忽略返回名 ⇒ **1 条判红**；均按 raw `sha256` 复原（`044602e3…` / `80606a97…`） |

**为什么第 4 条是真实缺口**：`inspect.getsource(...)` 里的子串判据判的是**代码形态**。
把那一行改成 `narrative.author or "x"`、或干脆写死一个常量，子串判据仍绿而制品上的作者
已经错了 —— 这正是本仓反复出现的「形态判据 ≠ 行为判据」。新的行为判据从 **store 读回**
`Artifact`，因此**只有真的把作者写对**才会绿。

**这三处后来都进了台账**（第十一节写完时它们还只在散文里，第十二节把台账补齐了）：
`b911e4a0` 一行（**如实记 2/8 判红**）、`b11ab450` 一行（八 job 全 success）、
`068e16c4` 一行（attempt 1/2 各 1 `cancelled`＝作业超时、attempt 3 八 job 全 success）。
**当时的判断错在哪**：我按 GOAL-089/091/092/093 的旧手法认为「只改记录的提交不进表」，
但本轮自己定的纪律是「**CI 台账一提交一行**」—— 旧手法是**对自指无解时的退让**，
不是一条比它更强的纪律。**现在的边界**：只改记录的提交**也进表**，唯一例外是
「写它那一行这个动作本身又产生了新提交」的那一条 —— 那种提交在 GOAL 的「自指边界」段
**逐条点名并附 run 读数**（不进表，但**也不匿踪**）。两者都要有出处，区别只在出处放在哪。

## 十二、补正之后又自查到的两处台账缺口（如实登记）

在追 `068e16c4` 的 CI 时逐条比对全部 run，抓到**两处我自己写坏的台账**（都已补齐，判据未改）：

| # | 我原先写的 | 真实读数 | 处置 |
| --- | --- | --- | --- |
| 1 | `b911e4a0` 记成「见下方自指边界」（**没有**给它一行台账） | 它自己的 M0 是 **2/8 判红**（[39835359599](https://github.com/Eswink/research-system-new/actions/runs/39835359599)：`quality-{ubuntu,windows}-latest` 同一判据 `test_the_witness_is_for_the_tree_we_are_looking_at`） | 补成真台账行并点名判红；由 `b11ab450`（对改完的树重跑门）处置 |
| 2 | `b11ab450` / `068e16c4` 只写在自指边界段里，**没进台账表**；`068e16c4` 的 CI 写「待回填」 | `b11ab450` ⇒ 8/8 `success`；`068e16c4` ⇒ attempt 1/2 各 1 **`cancelled`**（`quality-windows-latest` **作业超时**：20:03 / 20:07 vs `timeout-minutes: 20`；同一 job 在 `b11ab450` 上 19:19 通过）⇒ attempt 3 **8/8 `success`**；`f8c61422` ⇒ 8/8 `success` | 三个提交各补一行台账并折进 cycle 行 |

**为什么这值得单列**：这正是本轮那个判据要挡的形态 ——「台账里有、cycle 行里没有」与
「结论只在散文里、台账里没有」是**两种不同的漏记**。第一处是判据能抓的（台账 → cycle），
第二处**它抓不到**（台账里没这个提交，就没东西可对） ⇒ 后者只能靠**逐提交与 GitHub 实际
run 对账**。本轮两处都是这样自查出来的，如实登记。

**`cancelled` 的归因（三条取证）**：① 两次 attempt 都是**恰好 20 分 0x 秒**结束；
② 该 job 的 `timeout-minutes` 字面是 **20**；③ **同一个 job** 在前一个提交上 **19:19**
通过。三条合起来是「撞上限」而不是「并发取消」（后者会看到 `cancel-in-progress` 与同批
在飞 job 一起终止）。**阈值一字未动**。

## 结论

**PASS**。五个 EC 全达成：跨 GOAL 台账判据在树且自动覆盖新 GOAL（8 条判据 + 两向按压 +
逐字节复原）、GOAL-093 的记账退化如数补齐且**判据未因它而改**、报告由模型撰写而数字仍
逐行可溯源（24 条判据 + 反证）、记录面与见证齐备。残余与未覆盖范围逐条登记在 GOAL 的
「残余与未覆盖范围」节（`W-1`…`W-5` + `R-1`…`R-3`）。`R-M1` 未收口 ⇒ 本复检**不**宣称
项目安全；投递语义**不是**「恰好一次」。
