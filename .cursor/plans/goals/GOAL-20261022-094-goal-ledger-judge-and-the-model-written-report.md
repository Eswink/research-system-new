---
id: GOAL-20261022-094
slug: goal-ledger-judge-and-the-model-written-report
title: 台账纪律不再靠继承（跨 GOAL 判据）+ 报告由模型撰写而数字仍可溯源
status: ACHIEVED
created_at: 2026-10-22
updated_at: 2026-10-22
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    用户 2026-10-22 的 goal-mode 指令逐字：「本轮先补一个**元缺陷**（它刚被实测抓到），
    再做一格功能」「正确形态 = 跨 GOAL 的 tooling 测试，落 `tests/tooling/`（在 m0 的
    `python/tests` 收集面内 ⇒ 自动覆盖每个 GOAL，不需继承，不改那 69 个验证器）」
    「同轮必须做的：让 GOAL-093 在**新判据下通过**」「第二个靶子（若 cycle 有余）：
    报告域「报告由模型撰写」…判据要能区分「模型写的」与「汇编器生成的」，且**不得**
    因为模型写的就让数字脱离来源」。授权要点：(a) 全部决策权下放，只有「改产品边界 /
    放宽任何判据 / 动冻结面 / 新增或改 TrustLabel 取值」才停下登记 BLOCKED；
    (b) 每一步必须有**机械判据**；(c) 每轮必须让科研能力阶梯前进；(d) push-to-main-for-CI
    （只推 `main`、不 force、不重写历史）；(e) `max_cycles` 给 **14**。
objective: >
  两件事，都做成**可判**：① **台账纪律不再靠继承** —— 把「CI 台账里的每个提交都要落在某条
  cycle 行的 `commits` 格里」从 `tools/goal092_closeout_assertions.py` 里的**单 GOAL 断言**
  提成**跨 GOAL 的 tooling 判据**（遍历树里所有终态 GOAL，带祖父条款），使 GOAL-093 实测
  抓到的记账退化（台账 4 行 vs 实际 7 个提交、三个提交两张表都不进）**从第一天起**就被
  判据覆盖，并把那三个提交如数补上；② **报告由模型撰写** —— 叙述（第 1…4 节）由模型写、
  数字（第 5 节事实表）由汇编器写，两条面**互不越界**（模型写数字即点名拒绝），
  「谁写的」在制品上可读（`created_by` + 元数据），而**每个数字仍可溯源**。
exit_criteria:
  - id: EC-01
    criterion: >-
      **跨 GOAL 的台账判据在树且自动覆盖新 GOAL**：`tests/tooling/` 下有一条判据**遍历**
      `.cursor/plans/goals/GOAL-*.md`（不靠任何验证器传参、不靠清单登记），对**每个**终态且
      在受判面内的 GOAL 判「`CI 台账` 的 `提交` 列里每个哈希都出现在某条 cycle 行的
      `commits` 格里」；**只认 `commits` 列**（同一行别格出现不算）；台账为空 / 台账行没写
      提交 / 日志无数据行 / 缺小节**分别**点名。判据：`tests/tooling/test_goal_ledger_covers_every_commit.py`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_goal_ledger_covers_every_commit.py -q` ⇒ 8 passed；
      `test_every_terminal_goal_in_scope_ledgers_its_commits_in_a_cycle_row`（核心）+
      `test_the_predicate_bites_both_ways_on_synthetic_records`（同一谓词两向）+
      `test_a_commit_written_outside_the_commits_column_does_not_count`（散文掩蔽）+
      `test_an_empty_ledger_or_an_unattributed_row_is_not_evidence`（三态空真）。
    status: PASS
  - id: EC-02
    criterion: >-
      **祖父条款两向 + 两向按压 + 逐字节复原**：只有序 ≥ 61（或 `created_at >=
      2026-10-22`）的 GOAL 进受判面；序 60（GOAL-092）**被如实跳过**且理由写明「不回填历史
      = 不改写历史记录」。按压①把 GOAL-093 的迭代日志压成 1 行 ⇒ 判红并**逐条点名**缺席的
      4 个提交；按压②从 cycle 2 的 `commits` 格里删掉 `33e48f57` ⇒ 判红并点名它；两次都按
      raw `sha256` **逐字节复原**并复绿。
    verify: >-
      同上命令 + `test_the_scope_reaches_this_generation_and_skips_the_grandfathered_ones`；
      按压记录见 RECHECK-20261022-094 第三节（含按压前后 `sha256` 与判词原文）。
    status: PASS
  - id: EC-03
    criterion: >-
      **GOAL-093 在新判据下通过**（空真的绿不算收口）：`ff7546d7` / `c626aced` /
      `2998649d` 三个提交**逐条**补进它的 `CI 台账`（一提交一行；零 run 的写 `covered_by`）
      并折进 cycle 2 的 `commits` 格 ⇒ 台账 **7 行 = 本轮实际 7 个提交**。**补记录不是放宽
      判据**：判据一字未因它而改。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal093_closeout.py --root . --verdict-only`
      ⇒ **实跑读数：exit 0、68 `PASS` / 0 `FAIL`**（2026-10-23 在本树跑，原始输出 68 行 PASS；`SUMMARY` 行被 `--verdict-only` 略去，故以 `grep -c '^PASS'` = 68、`grep -c '^FAIL'` = 0 取证）；`tests/tooling/test_goal_ledger_covers_every_commit.py` ⇒ 8 passed；
      `rg -c '^\| \`[0-9a-f]{7,8}\` \|'` 在 GOAL-093 的 CI 台账节 ⇒ **7**。
    status: PASS
  - id: EC-04
    criterion: >-
      **报告由模型撰写，而数字不脱离来源**：叙述四节由模型写、事实表由汇编器写；
      ①**模型写数字即点名拒绝**（`NarrativeError` 点名键与字符，不静默抽掉）；
      ②**事实表逐行带来源列**且与 `ReportInputs` 逐条对得上，叙述区里**一个指标值都没有**；
      ③**谁写的可读**：接上叙述者 ⇒ `Artifact.created_by` 是 `model:<endpoint>/<returned>`、
      元数据有 `narrative` 块；没接 ⇒ **逐字节**回到既有确定性汇编、`created_by` 仍是
      `system:report-assembler`、元数据键集不变；④模型任务书**不发数值与标识符**（它无从复述）。
      判据：`tests/application/test_report_narrative.py` +
      `tests/application/test_report_narrative_on_the_product_path.py` +
      `tests/application/test_report_task_narrator_behaviour.py`（**行为面**：真的跑一次
      `execute_report_task` 再从 `FakeArtifactStore` 读回 `Artifact.created_by`；
      `llm_narrator` 的**正常解析路径**用假 gateway + 假 resolver 取证）。
    verify: >-
      三个文件 ⇒ **32 passed**；`test_the_artifact_created_by_is_the_model_when_a_narrator_is_wired` /
      `test_the_created_by_follows_a_different_narrator` /
      `test_without_a_narrator_the_artifact_is_the_compiled_report_byte_for_byte` /
      `test_llm_narrator_on_the_happy_path_attributes_the_returned_model`。
      反证臂（不改判据）：① 撤掉数字禁令 ⇒ 3 条判红；② 把 `created_by` 写死成
      `system:report-assembler` ⇒ **3 条判红**；③ 让 `llm_narrator` 忽略返回名 ⇒ **1 条判红**；
      三处都按 raw `sha256` 逐字节复原（`report_task.py` `044602e3…`、
      `report_narrative_task.py` `80606a97…`）。
    status: PASS
  - id: EC-05
    criterion: >-
      **收口**：记录写完（GOAL / PLAN / RECHECK / MEM / 阶梯「报告」行升级 / 程序表序 62 /
      进展记录 + 两表归档）→ `git add` **全部受判文件（含新增的未跟踪文件）** → 记录面判据 →
      **最后**跑 `tools/run_m0_with_witness.py` → 之后**不再**改受判文件 → 提交推送 → CI 到
      终态（逐提交一行台账）+ 凭据审计四面 `offenders=0` + 残余与未覆盖范围逐条。
    verify: >-
      见证 `terminal_line` = `PASS: profile=m0; 23 deterministic checks`、0 FAILED、
      `tree changed during the run: False`；`tools/credential_audit.py` 四面 `offenders=0`；
      治理校验器通过；`tools/verify_goal094_closeout.py --root . --verdict-only` 全 PASS。
    status: PASS
budget:
  max_cycles: 14
  per_cycle_minutes: 90
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator / 门禁 / 快照 / 测试断言使其通过
    - 放宽任何既有判据的断言、词表、扫描面或阈值
    - 把受判面写成交集、并集掩蔽或写法清单
    - 收窄既有受判面而不逐条申报（逐条枚举 + `numstat` 删除行读数 + 谓词比对）
    - >-
      **为了让 GOAL-093 过而改判据**：补记录是允许的（那正是本轮要做的），
      改判据让它不咬是禁止的
    - >-
      **把模型写的叙述与汇编器写的事实混成一块**：第 1…4 节（模型）与第 5 节（汇编器）
      必须各自可指认；把数字搬进叙述或把叙述搬进事实表 = 改契约
    - >-
      **静默抽取模型写的数字**：叙述含数字必须**点名拒绝**；悄悄删掉那个数字会让
      「这段是谁说的」不可判
    - >-
      **让数字脱离来源**：事实表每行必须有来源列，且值逐字来自持久事实（不重算、不编造）
    - >-
      把真实凭据（`sk-…` 等）写进**任何 tracked 文件**；
      判据自证 = `tools/credential_audit.py` 四面 `offenders=0`
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 新增任何依赖
    - 自行再扩 `max_goals`
    - 宣称项目安全（`R-M1` 未收口）；宣称投递语义为「恰好一次」（**明确否认**）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 `fix_policy` 上限
  - >-
    **真实凭据出现在 tracked 文件里**（含记录）—— **立即 BLOCKED** 并清理
  - >-
    需要**再**扩 `max_goals` / 改战役预算 —— 停下登记（用户决定）
  - >-
    只靠改判据就能让「报告由模型撰写」看起来成立 —— 停下登记（那是假绿）
child_plans:
  - .cursor/plans/tasks/PLAN-20261022-094-goal-094-ledger-judge-and-the-model-written-report.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261022-094-goal-094-ledger-judge-and-the-model-written-report.md
memory_entries:
  - MEM-20261022-228
---

## 目标与退出标准

**一句话**：让「台账纪律」**不再靠每个 GOAL 自己继承**（那正是它退化的原因），
并让**报告的叙述部分由模型写**、而**数字仍然只在可溯源的事实表里**。

**建档实测（缺口形态，逐条带读数）**：

1. **判据只保护它自己那个 GOAL**：`_log_verdicts` 在
   `tools/goal092_closeout_assertions.py:286`；`rg _log_verdicts tools/goal093*` **零命中**。
   这条判据属于**某一个 GOAL 的收口断言集** ⇒ 下一个 GOAL 天然没有它。
2. **后果（实测）**：GOAL-093 的 `CI 台账` **4 行**、实际提交 **7 个**；
   `ff7546d7` / `c626aced` / `2998649d` **既不进台账、也不进任何 cycle 行**，
   而它的收口验证器仍报 **68 PASS / 0 FAIL**。
3. **报告是确定性汇编**：`build_research_report` 的每个字节都由输入决定，
   `created_by="system:report-assembler"`；`research_report.py` 自己的 docstring 逐字写着
   「**不调模型**…模型的叙述性撰写是**另一件事**（阶梯上「报告」域的再下一级）」。
4. **「叙述质量」无判据**：阶梯「报告」行的 `下一级` 逐字是「**报告由模型撰写**
   （现为确定性汇编；叙述质量无人判）」。

**本 GOAL 的射程边界（先写清楚，避免越判）**：

- **只新增**：`tests/tooling/test_goal_ledger_covers_every_commit.py`、
  `packages/application/deliverable/report_narrative.py`、
  `packages/application/run_orchestration/report_narrative_task.py`、两条报告判据、
  `services/api/report_support.narrative_runner`、`ReportTaskDeps.narrator` 与
  `ReportAdmission.narrative` 两处**可选**字段、本 GOAL 的记录；
- **不改**：`TrustLabel`、`Decision`、`aggregate_panel`、`SECTION_HEADINGS`、m0 条数、
  `PRODUCT_ROOTS`、任何既有判据的断言；
- **如实登记**：本轮**不**判「叙述的科学质量好不好」—— 那需要人评或更强判据。
  本轮判的是「**谁写的**」与「**数字在哪**」两件结构事实。

## 为什么这一轮更近科研（以及哪一面没被推进）

**推进的那一面（阶梯「报告」域的 `下一级`，逐字）**：「**报告由模型撰写**（现为确定性
汇编；叙述质量无人判）」。上一轮把报告做成了**经产品路径产出的可读制品**（四节 + 每数字
可溯源），本轮把**叙述**交给模型，同时**没有**让数字脱离来源：数字被**移出**叙述面，
只存在于汇编器写的第五节点事实表里。没有这一步，「报告」在科研循环里就永远只是一张
**读数表**，而不是一篇能被评审读的东西。

**同轮推进的第二面（元缺陷，不是科研域）**：台账纪律从「单 GOAL 断言」变成「跨 GOAL
判据」。它不推进任何科研域，但它是**记账可信度**的前提 —— 上一轮的记账退化（台账 4 行 vs
7 个提交）说明「靠继承的判据」会以「另一个 GOAL」的面貌消失。

**没推进的那一面（如实登记）**：**叙述质量仍无人判**。本轮给出的是「模型确实写了正文」
与「它不能碰数字」这两件结构事实；「这段叙述好不好」不在射程（与 GOAL-082 EC-04 同类
诚实边界：内容的**好坏**不可由结构判据判定）。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的 7 步判定续点（以「文件 + 工作树 + 远端实况」为准，
**禁止凭记忆假设**）。每步完成后立即回写本文件。

## 单 cycle SOP

沿用宪章与既有 GOAL 的既定纪律（记录 → `git add` → 记录面判据 → 全量 m0 → 治理 →
显式路径提交 → 推送 → CI 到终态 → 纠错 → 回写）。**本 GOAL 特有**：

- **判据先跑在真实缺陷上**：新判据第一次运行就在 GOAL-093 上**通过**（因为它在按压前
  台账 ⊆ 日志），因此「它会咬」必须由**按压**证明，不能由真树的绿证明 ——
  两向各判红一次并逐字节复原（RECHECK 第三节留 `sha256`）。
- **补记录与改判据分开申报**：补 GOAL-093 的三行台账**不改判据**；改判据只为修我自己
  写错的东西，且每次都要能说清「改的是实现，不是受判面」。
- **模型面与事实面互不越界**：任何让数字出现在叙述里、或让模型的任务书带上数值/标识符
  的改动都是**改契约**。

## CI 失败分类与纠错

沿用既有四类（lint/typecheck / 产品测试失败 / flake-env / 基础设施）。基础设施红须三条取证；
时序型 flake 按既有纪律 `rerun-failed-jobs`，**不改阈值**，首轮红如实登记。
**零 run ≠ cancelled**，如实登记 + `covered_by`。

**本轮已知的判红形态（逐条记，免重犯）**：`ff7546d7` 的 2/8 判红是**见证与树失配**
（补记台账改了 GOAL 正文，而见证是在改之前跑的）—— 这不是判据缺陷，正确处置是
**记录写完 → add → 跑门 → 不再改受判文件**（本 GOAL 的顺序纪律逐字如此）。

## 终止与收口

- **ACHIEVED**：EC-01…EC-05 全 PASS + 独立 RECHECK + 本文件收口（`latest_recheck` 为
  **仓库相对路径**）+ CI 台账到终态 + 残余与未覆盖范围逐条 + **阶梯记账成立** + 正式见证的
  `terminal_line` 全绿。
- **BLOCKED**：命中任一 `escalation_triggers` / 同一失败签名超过 `fix_policy` 上限 /
  `max_cycles` 触顶 / 连续 `no_progress_stop_cycles` 轮未推进任何 EC。
- **ABORTED**：用户撤销。

## 迭代日志

（**逐 cycle 一行**，不把多次修复压成散文。每一行的「修复」是该 cycle **真的修掉**的东西，
「剩余差距」是该 cycle 结束时**仍未达成**的东西 —— 两者都按当时的读数写。）

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261022-094 | （未提交） | 新判据 **8 passed**（真树）；两向按压各判红并逐字节复原（`89e2fda8…` → `c9dcb895…`/`fb67595f…` → `89e2fda8…`）；GOAL-093 台账补至 **7 行 = 7 个提交**后仍 8 passed；报告面新判据 **24 passed**（两文件）；受影响套件 `tests/application` + 报告离线 e2e ⇒ **1297 passed / 1 skipped**；规模门 **1324 passed**；`ruff format` / `ruff check` / `mypy` 三面清零 | 无（未推送） | **3**：① 首版 `execute_report_task` 因新增分支涨到 **52 行**（上限 50）⇒ 把两处声明面缺件提出 `_admission_blocker`；② 首版模型任务书把**来源标识**（`39000001`）发给模型，而叙述被禁止含数字 ⇒ 判据自己抓出「请它违规」的形态，任务书改为只给**类别计数 + 指标名**；③ 测试替身用 `type("_D", (), {"narrator": f})` ⇒ 函数变绑定方法，`TypeError: takes 1 positional argument but 2 were given` ⇒ 改 dataclass | EC-05 收口；记录面 / 治理 / m0 / 两树 / CI 全未跑 | 写 GOAL/PLAN/RECHECK/MEM + 阶梯「报告」行 + 进展记录 + 归档 |
| 2 | （同上） | `80e844b1` | 记录写完（GOAL / PLAN / RECHECK / MEM / 宪章序 62 + 阶梯「报告」行 + 进展记录 + 两表归档）→ `git add` **全部受判文件**（23 个：11 新增 + 12 修改）→ 记录面判据（治理校验通过 + **55 passed**）→ **最后**跑 m0 两遍（第一遍用管道跑，输出被 `tail` 截断 ⇒ 为取证 `PASS [` 行数重跑一遍并**直接写文件**）：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、覆盖 **4584**、`tree changed during the run: False`；凭据审计四面 `offenders=0` | [M0 39811518364](https://github.com/Eswink/research-system-new/actions/runs/39811518364) **八 job 全 success** + [Push 39811517931](https://github.com/Eswink/research-system-new/actions/runs/39811517931) success | **2**：① 收口验证器自己抓出两处**判据缺陷**：用例下界写高（`def test_` 实为 12 而非 15）、把 `packages/` 与 `tests/` 的文件也要求进 `IN_SCOPE`（范畴错误 —— 它们本就在 `PRODUCT_ROOTS` 里）⇒ 逐条修正；② 宪章判据抓出我在程序表里写了 `68 PASS / 0 FAIL`（状态枚举词）⇒ 改为「68 条判词全过 / 0 条不过」| **无**（五个 EC 全 PASS、CI 到终态） | 收口 |
| 3 | （同上） |`38edc9ac` → `b07c3398` → `b911e4a0` → `b11ab450`| 判据修正（表格边界 + 标题只认行首）+ 两条新判据（8 条用例）+ 记录修正；见证：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、覆盖 **4584**、`tree changed during the run: False` | [M0 39823432168](https://github.com/Eswink/research-system-new/actions/runs/39823432168) **八 job 全 success** + [Push 39823434219](https://github.com/Eswink/research-system-new/actions/runs/39823434219) success | **2**：① 首轮封口 m0 **真红**（`23 PASS / 3 FAILED`）：判据把 `## CI 台账` 里混进的**另一张三列表的列头**当数据行 ⇒ `_table` 改为「连续 `｜` 行 + 列数一致」；② 同一判据的 `_section` 用朴素 `find`，被 cycle 行**正文里引用**的 `` `## CI 台账` `` 骗过而提前截断 ⇒ 标题只认**行首**。两条各配一条判据（8 条） | **无**（五个 EC 全 PASS、CI 到终态；判据修正只收紧实现，受判面定义未变） | 收口 |
| 4 | （同上） | `068e16c4` | 四项补正：EC-03 回填 `verify_goal093_closeout.py` 的**实跑读数**（exit 0 / 68 PASS / 0 FAIL）；自指边界段重写（逐条点名 `b911e4a0` / `b11ab450`）；RECHECK 第五节 `numstat` 按实测重写（补 `test_closeout_verifiers_run_their_own_assertions.py` 的 +1）；新增 **8 条行为判据**（`test_report_task_narrator_behaviour.py`：真跑 `execute_report_task` 后从 store 读回 `created_by`；`llm_narrator` 正常路径）。台账判据 8 passed；报告面三文件 **32 passed**；收口验证器 **78 PASS** | [M0 39848248670](https://github.com/Eswink/research-system-new/actions/runs/39848248670) attempt 3 **八 job 全 success**（attempt 1/2 各 1 `cancelled`＝作业超时）+ [Push 39848246985](https://github.com/Eswink/research-system-new/actions/runs/39848246985) success | **4**（全是**验证强度 / 记录自洽**缺口，非产品缺陷）：① EC-03 的 `verify` 用「⇒ 全 PASS」代替真实输出 ⇒ 实跑取证；② 自指边界段与表自相矛盾 ⇒ 重写并点名两个提交；③ `numstat` 表漏一处 +1 ⇒ 按实测重写；④ `created_by` 只由 `inspect.getsource` 子串证明、`llm_narrator` 正常路径未测 ⇒ 补 8 条行为判据。**没有改任何受判面的定义**（两向按压：写死 `created_by` ⇒ 3 判红；忽略返回名 ⇒ 1 判红） | **无**（五个 EC 仍全 PASS；补正只增强取证强度） | 收口 |

## 上一轮残余的处置（5/5，逐条）

**这一节是「读取器自举」的物证**：`W-1`…`W-5` 是读取器从 GOAL-093 正文里**读出来的**
（产物 `evidence/GOAL-20261022-094-next-round-charter.md`，
`sha256:d0aaae8fffb82cef8798f2950c20fd84214f5ead458e74ba8e797b5604de9321`），不是手抄。

| 上一轮 | 残余（读取器的判词） | 本轮的处置 | 证据 / 理由 |
| --- | --- | --- | --- |
| `W-1` | 判词 → 指令的改写未做；「评审驱动修订」的含义是判词送达，不是修订一定发生 | **不做**（如实保留） | 与 GOAL-082 EC-04 同源：内容采纳不可判，改判会假绿；解除条件属产品结构改动，需拍板 |
| `W-2` | 模型是否真的据判词改了无判据 | **不做**（边界保留） | 同上一条；本轮的模型面判的是「谁写的 / 数字在哪」，不是「采纳了什么」 |
| `W-3` | 只有一个被评对象、一个协议 | **不做**（射程保留） | 多评审链不在本轮射程；本轮的第二个靶子选的是报告域，不是复检域 |
| `W-4` | 只取序号最大的那个前序 run；不跨空轮回溯 | **不做**（有意保留） | 跨过空轮取旧判词会让「上一轮」失真 —— 既有设计判断，未变 |
| `W-5` | `RECHECK` 只覆盖本地树；CI 覆盖推送后的树 | **承接（本轮即适用）** | 本轮 RECHECK 的读数全部是**本地树**；CI 结论逐提交记台账，两棵树的对象不同照旧如实分开 |

## 残余与未覆盖范围（逐条）

**未覆盖（`W-1`…`W-5`）**：

- **`W-1`**：**叙述的科学质量无人判**。本轮证明「模型写了正文」与「它不能碰数字」，
  不证明「这段正文好」。要判它需要人评或更强的判据（引用逐条对齐 / 事实断言可验证），
  两者都不在本轮射程。
- **`W-2`**：**模型数字禁令只在「有没有数字」这一维**。模型可以写出**不含数字但仍然错**
  的句子（例如把「没有找到来源」说成「来源充分」）。本轮**不**判叙述与事实的一致性 ——
  那需要把叙述拆成可核对的断言，属下一级。
- **`W-3`**：**`llm_narrator` 没有在产品组合根上默认接线**。它只提供**产品闭包**
  （`services/api/report_support.narrative_runner`）与可注入面；装配方（测试 / 运维）显式
  选择接上。出厂路径今天仍是确定性汇编 —— 这是如实的现状，不是遗漏（接上会改交付物的
  `created_by`，那是产品行为变更，须单独决定）。
- **`W-4`**：**跨 GOAL 判据不读 git 历史**。CI 的 `actions/checkout` 未声明 `fetch-depth`
  （实测 `m0-quality.yml` 六处均无）⇒ 工作区只有 HEAD 一个提交 ⇒ 任何「数这一轮有多少提交」
  的判据在 CI 上会**空真**。因此该判据判的是**两份记录之间**的关系；「台账是否穷尽 git」
  由收口复检在本机取证。
- **`W-5`**：**报告仍只覆盖本 run**。跨 run 的报告聚合不在射程（既有边界，逐轮登记）。

**残余风险（`R-1`…`R-3`）**：

- **`R-1`**：`R-M1` 未收口 —— 本 GOAL **不**宣称项目安全。
- **`R-2`**：投递语义**不是**「恰好一次」（at-least-once + 幂等 + 去重）。
- **`R-3`**：模型叙述进的是**报告正文**，不是判定面。事实表仍由汇编器写、值逐字来自
  持久事实 ⇒ 判定面的可复算性未被这一轮改变。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-22 | **ACTIVE** | **建档**：承用户 goal-mode 指令（先补元缺陷、再做一格功能）。建档**实测**四处缺口：① `_log_verdicts` 只在 `goal092_closeout_assertions.py`，`rg` 在 `tools/goal093*` 零命中；② GOAL-093 台账 4 行 vs 实际 7 个提交、三个提交两张表都不进；③ 报告 `created_by="system:report-assembler"` 且 docstring 自陈不调模型；④ 阶梯「报告」行 `下一级` 逐字是「报告由模型撰写」。`max_cycles: 14`。 |
| 2026-10-22 | **ACTIVE** | **收口面落地**：五个 EC 全 PASS（EC-01…04 判据面 6 + 24 例；EC-05 记录面）；GOAL-093 台账补至 **7 行 = 7 个提交**；两向按压各判红并逐字节复原；收口验证器 **77/77**；读取器自举（GOAL-093 → 本 GOAL charter，`W-1…W-5` 5/5 有处置）。CI 台账待推送后回填。 |
| 2026-10-22 | **ACHIEVED** | 五个 EC 全达成。**CI 到终态**：`80e844b1` 八 job 全 `success` + CodeQL 三 job `success`。**本地 m0**：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24**、0 FAILED、覆盖 **4584**、`tree changed during the run: False`。**凭据审计**四面 `offenders=0`。**阶梯前进**：「报告」行升级为「叙述由模型撰写、数字仍在事实表」。残余如实留（`W-1`…`W-5` / `R-1`…`R-3`）。 |
| 2026-10-23 | **ACHIEVED**（补正） | **完成核验判负后的四项补正**：EC-03 回填实跑读数（`verify_goal093_closeout.py` ⇒ exit 0 / **68 PASS / 0 FAIL**）；自指边界段重写（点名 `b911e4a0` / `b11ab450`，并写明「链条的地基是最后一次跑门的那棵树」）；`numstat` 表按 `git diff --numstat 2998649d..` 重写（补上 `test_closeout_verifiers_run_their_own_assertions.py` 的 +1）；新增 **8 条行为判据**（从 `ArtifactStore` 读回 `created_by`，替代 `getsource` 子串；`llm_narrator` 正常路径用假 gateway 取证）。两向按压：写死 `created_by` ⇒ **3 判红**、忽略返回名 ⇒ **1 判红**，均按 raw `sha256` 逐字节复原。收口验证器 **78 PASS / 0 FAIL**。 |

## CI 台账

（**逐提交逐 job**，一个提交一行。**零 run ≠ cancelled**：`cancel-in-progress` 造成的
`cancelled` 与「同批推送被 GitHub 合并成一个 run」的 `无 run` 是**两种不同**的形态，
分别登记；后者用 `covered_by` 指名它被哪一条 run 覆盖。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| `80e844b1` | [M0 39811518364](https://github.com/Eswink/research-system-new/actions/runs/39811518364) / [Push 39811517931](https://github.com/Eswink/research-system-new/actions/runs/39811517931) | **八 job 全 `success`**；CodeQL 三 job 全 `success` | 本轮全部交付面（跨 GOAL 台账判据 + GOAL-093 补记 + 叙述面 + 24 条报告判据 + 记录 + 收口验证器）。本地 m0 已先绿：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、覆盖 **4584** 个受判面文件、`tree changed during the run: False`。凭据审计四面 `offenders=0` |
| `38edc9ac` | [M0 39823432168](https://github.com/Eswink/research-system-new/actions/runs/39823432168) / [Push 39823434219](https://github.com/Eswink/research-system-new/actions/runs/39823434219) | **八 job 全 `success`**；CodeQL 三 job 全 `success` | **判据修正**（表格边界 + 标题只认行首）+ 两条新判据（8 条用例）+ 记录修正。本地见证：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、覆盖 **4584**、`tree changed during the run: False` |
| `b07c3398` | [M0 39831150946](https://github.com/Eswink/research-system-new/actions/runs/39831150946) / [Push 39831148629](https://github.com/Eswink/research-system-new/actions/runs/39831148629) | **八 job 全 `success`**；CodeQL 三 job 全 `success` | 只改见证（对封印后的树重跑全量 m0：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、覆盖 **4584**、`tree changed during the run: False`）⇒ **最终树** |
| `b911e4a0` | [M0 39835359599](https://github.com/Eswink/research-system-new/actions/runs/39835359599) / [Push 39835358355](https://github.com/Eswink/research-system-new/actions/runs/39835358355) | **2/8 判红**（`quality-{ubuntu,windows}-latest`，同一判据 `test_the_witness_is_for_the_tree_we_are_looking_at`）；Push success | **判红 #3（顺序问题，判据正确）**：本提交只改记录（台账补 `b07c3398` + 两树读数），而见证是在改之前跑的 ⇒ 见证覆盖的不是提交后的树。**判据未改**；处置见 `b11ab450`（对改完的树重跑门并重封见证）|
| `b11ab450` | [M0 39839726441](https://github.com/Eswink/research-system-new/actions/runs/39839726441) / [Push 39839725914](https://github.com/Eswink/research-system-new/actions/runs/39839725914) | **八 job 全 `success`**；CodeQL 三 job 全 `success` | 对**改完的记录树**重跑全量 m0 并重封见证（`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、覆盖 **4584**、`tree changed during the run: False`）⇒ 处置了 `b911e4a0` 的判红 #3 |
| `068e16c4` | [M0 39848248670](https://github.com/Eswink/research-system-new/actions/runs/39848248670) / [Push 39848246985](https://github.com/Eswink/research-system-new/actions/runs/39848246985) | attempt 1 **7 success / 1 `cancelled`**（`quality-windows-latest`，实测 **20:03**，`timeout-minutes: 20`）⇒ attempt 2 **同样 `cancelled`**（**20:07**）⇒ attempt 3 **八 job 全 `success`**；Push success | **`cancelled` ≠ 判红**，分开登记（同批其余 7 job 两轮全 `success`）。**已归因**：同一 job 在 `b11ab450` 上 **19:19** 通过、在本提交上 **20:03 / 20:07** ⇒ 撞 **20 分钟作业上限**，**不是**产品缺陷、**不是** `cancel-in-progress`。**阈值一字未动**。本提交 = 四项补正（EC-03 实跑读数 / 自指边界重写 / `numstat` 实测重写 / 8 条行为判据）|

**自指边界（如实登记，不假装闭合）**。先说**已经进表**的三条（它们一度只在散文里，
第十二节补进表了）：`b911e4a0`（**2/8 判红**，见证与树失配）、`b11ab450`（八 job 全 success，
处置上一条）、`068e16c4`（attempt 1/2 各 1 `cancelled`＝作业超时、attempt 3 八 job 全 success）。
**台账表在 `068e16c4` 那一行结束**。

其后的两条**只改记录**，因此**不进表** —— 但**必须在此点名，附 run 读数**，否则就是匿踪：

- `f8c61422` —— 台账补 `b911e4a0` / `b11ab450` / `068e16c4` 三行并折进 cycle 行；
  [M0 39863901569](https://github.com/Eswink/research-system-new/actions/runs/39863901569) **八 job 全 `success`**；
- `2c913d1f` —— RECHECK 第十二节（两处台账缺口的归因 + `cancelled` 的三条取证）；
  [M0 39869801382](https://github.com/Eswink/research-system-new/actions/runs/39869801382) **八 job 全 `success`**。

**为什么它们不能进表**：写它们那一行本身又是一个只改记录的提交 ⇒ 新提交自己的结论
又要一行 ⇒ 无终止。**所以本段就是它们的台账**（两者都有 sha、run id、逐 job 结论）。
**这条规则是终点，不是新的开环**：本段所在的补正提交（修正第十一节末段 + 写本段）同样只改记录，
它的 run 读数在**收口报告**里给出；此后凡只改记录的提交一律按本条处理 ——
**不要求再改本文件**（改本文件会再产生一个提交，那就是上面那个无终止）。

**链条的地基是「最后一次跑门的那棵树」，不是「表的最后一行」**：
`b07c3398` 的见证覆盖 **4584** 个受判面文件、`tree changed during the run: False`；
而上述五个提交**只改记录面与判据面**（`git diff --name-only` 逐条可核：`.cursor/plans/`
下的 GOAL / RECHECK / PLAN 与 `tests/application/` 下的一条新判据），**没有任何产品代码**。
