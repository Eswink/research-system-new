---
id: MEM-20261014-219
title: "「每轮必须更近目标」是一条可机械强制的判据：给长跑战役的活跃面加一列能力域 + 一张阶梯表，用「最新一轮必须被阶梯收录」把它钉住"
status: ACTIVE
created_at: 2026-10-14
updated_at: 2026-10-14
scope: repository
confidence: 0.95
review_after: 2027-04-14
source_plans:
  - .cursor/plans/tasks/PLAN-20261014-464-goal-077-research-report-assembler-and-arc.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261014-465-goal-077-research-report-and-the-end-to-end-research-arc.md
supersedes: []
tags: [mainline, drift-prevention, judged-convention, campaign, charter]
---

## 做了什么

长跑的战役宪章（`MAINLINE.md`）会**漂移**：程序表一直在前进，但「离目标还有多远」
**没有任何读数**。实测证据：序 35…44 **十个** GOAL 都是「查询参数纪律」（API 卫生），
与项目的科研能力**无直接关系** —— 程序表看起来忙，阶梯十轮没动。

本轮加三件东西把它钉住：

1. **新小节 `## 科研能力阶梯`**：一张闭集表 `| 域 | 当前级 | 依据 GOAL | 下一级是什么 |`，
   域集合 = {检索, 证据, 计划, 实验, 复检, 报告, 迭代}。
2. **两张表各加一列 `能力域`**：程序表（追加在末尾）+ 进展记录（**插在 `RECHECK` 之前**
   —— `RECHECK` 必须留在末格，因为既有判据 `_bad_recheck_links` 取 `row[-1]`）。
   `—` = 非科研（API 卫生类）。
3. **新判据 `tests/tooling/test_mainline_research_ladder_advances.py`**，核心不变式：
   **最新收口的一轮的能力域不得是 `—`，且必须被阶梯的某个 `依据 GOAL` 收录**。

## 为什么这样做

**为什么必须是判据而不是散文**：命令式的要求（「每轮都要更近目标」）写在提示词里，
**下一次触发就失效**——没有人读它。写成判据才**每轮自动执行**：一个 GOAL 收口了却没推进
任何科研域（或其推进没记进阶梯）⇒ 门判红 ⇒ 循环被迫面对它。

**为什么域要闭集**：否则可以不断切细域来凑「前进一格」。闭集 + 改域要改判据（有意的摩擦）。

**为什么允许依据面混列进行中的 GOAL，但**必须至少一个终态**：
一个域常常「已由某轮奠定 + 当前又有一轮在进行」（报告域正是：`035` 已收口、`077` 在进行）。
只允许终态 ⇒ 读者看不见「正在做」；只列进行中 ⇒ 「当前级」是**承诺**而非**事实**。
「至少一个终态」把两者分开。

**为什么 `能力域` 列要两张表都加**：阶梯是**读数**，程序表/进展记录是**归因**。
只加阶梯 ⇒ 读者不知道哪一轮贡献了哪一格；只加列 ⇒ 没有「离目标多远」的总览。

## 怎么做与复现

```bash
# 三条宪章判据（结构 / 归档连续性 / 阶梯不变式）
uv run --frozen --no-sync python -B -m pytest \
  tests/tooling/test_mainline_research_ladder_advances.py \
  tests/tooling/test_mainline_program_is_intact.py \
  tests/tooling/test_mainline_archive_is_continuous.py -q

# 两条按压（P1 最新轮改成非科研 ⇒ 判红；P2 依据指向不存在的 id ⇒ 判红）+ 逐字节复原
uv run --frozen --no-sync python -B scratch/mainline_ladder_press.py
```

实测：P1 判词「**这一轮迭代没有把科研能力推向前**」；P2 判词「依据 … 在树里找不到对应文件」；
`FINAL_MATCHES_BASELINE True`。

## 适用边界

- **判据挡静默漂移，不挡夸大**：「最新一轮被记进阶梯」不等于「那一格真的升级了」——
  后者由各 GOAL 自己的 EC + RECHECK 承担。
- **祖父条款**：判据落地**之前**已收口的轮次不回填（`_CUTOFF_SEQ`）。故落地当轮及以后
  才受判；早于此的如实跳过（在失败消息里说明读到哪个序，不静默）。
- **`PAUSED` 是状态词表成员**：宪章里**不得**出现它（状态只在 GOAL frontmatter）。
  写「暂停」的中文表述即可 —— 这是本次踩到的一处（修订记录里写了 `PAUSED` 被既有判据抓到）。
- **改动既有判据的列契约**要**逐条申报**（`_PROGRAM_COLUMNS` / `_PROGRESS_COLUMNS` +
  它们的合成夹具）—— 谓词**未放宽**，只是列数契约更新。
- 本记忆**不**作任何安全结论（`R-M1` 未收口）。

## 来源

- `PLAN-20261014-464` / `RECHECK-20261014-465`；
- 判据：`tests/tooling/test_mainline_research_ladder_advances.py`（6 例）；
- 宪章：`.cursor/plans/goals/MAINLINE.md` 的 `## 科研能力阶梯`。
