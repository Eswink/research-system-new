---
id: PLAN-20260925-184
slug: goal-017-closeout-recheck
title: GOAL-017 收口复检（EC-04）：两树复检 + m0 支持终态行 + 13 项 D-NN 终态表 + CI 台账到终态
status: DONE
created_at: 2026-09-25
updated_at: 2026-09-25
parent_goal: GOAL-20260925-017
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260925-017 的 **EC-04**（收口复检 + 残余登记）。授权沿用 GOAL 的
    `child_plans` / `push-to-main-for-CI`：**只推 main、不 force、不重写历史、不推旁支**；
    授权面仅 D-10(a) / D-11(a) / D-13(a)+(b) 三条，**不扩面**。EC-04 自身**不改产品代码**：
    交付物 = 独立复检脚本（两树同结论 + 非恒真）+ m0 终态行 + 13 项 `D-NN` 终态表
    + CI 台账到终态 + 承继残余逐条在位。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260925-185-goal-017-closeout-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260925-140-gate-input-face-needs-an-authority-and-a-pair.md
  - .cursor/memory/entries/MEM-20260925-141-one-switch-one-reader-and-one-job-per-threshold.md
---

# PLAN-20260925-184 — GOAL-017 收口复检（EC-04）

## 目标

把 GOAL-017 的三条实施（EC-01 D-10 / EC-02 D-11 / EC-03 D-13）**换一个观察者**复检一遍：
复检脚本**不复用 GOAL 的叙述**，自己重读树做结构断言，并把每个 EC 的判据文件在**被测树**里
以子进程实跑；同一脚本在**工作树**与**干净 checkout**（`git worktree`）给出**同一结论**且
**非恒真**（按压必须判红）。再补交 EC-04 的四件交付物：m0 终态行、13 项 `D-NN` 终态表、
CI 台账到终态、承继残余逐条在位。**本 PLAN 不改任何产品代码 / 判据 / 阈值。**

## 验收条件

- **AC-1**：复检脚本两路同时成立——①「脚本自己重读树」的结构断言；② 该 EC 的判据文件
  在**被测树**里子进程实跑。两路都过 ⇒ 该 EC 复检成立。
- **AC-2**：**非恒真**——按压 `dnn-table` / `switch-name` / `job-structure` / `threshold` /
  `git-face` 五处（**只改内存，不写仓库文件**）⇒ 结构半**必须判红**且点名是哪一条。
- **AC-3**：**两棵树同结论**——工作树与干净 `git worktree`（detached HEAD = cycle 2 推送 tip
  `505f2ab`）跑同一脚本：**判词列 19/19（14 结构 + 5 判据）逐行相同**；翻 EC-04 状态后整份输出
  差异**恰一行**且只在**明细文字**（EC 状态字典多一个键），**无一条判据在两树间结论不同**。
- **AC-4**：**m0 可支持的终态行**——`R-3` 修好后 as-is 本机 m0 **23/23**（不再需要代管跑法），
  终态行 + 日志 + `size` / `sha256` 复核留档。
- **AC-5**：**13 项 `D-NN` 终态表**在位（13 行），三条本轮授权项（D-10 / D-11 / D-13）
  从「需授权未实施」→「已实施」，未授权项（D-04 / D-05 / D-06 与 (a) 面）**逐条写明**。
- **AC-6**：**治理面绿**——`validate.py` = 通过、`DOCS-CHECK PASS`。
- **AC-7**：**CI 台账到终态**——本 GOAL 四行（建档 / cycle 1 / cycle 2 / cycle 3）逐行给出
  run id + 链接 + 逐 job 结论 + CodeQL 3/3 + `run_attempt`。
- **AC-8**：**承继残余逐条在位**——`R-F1` / `R-F2` / `R-F3` / `R-M1` / `R-D1` / `R-B1` /
  `R-N1` / `W-1…W-7` 原样保留，**未**被本 GOAL 收口也**未**被掩盖。

## 实施清单

- **WP1 复检脚本**：`scratch/goal017-ec04-closeout-recheck.py`（295 行，**不提交**）——
  `--root` / `--only structural|criterion|all` / `--press <面>`；结构半 14 条断言（EC-01 三条 /
  EC-02 四条 / EC-03 四条 / 收口两条），判据半 5 个目标（`3 / 14 / 18 / 3 / 5 passed`）。
- **WP2 非恒真按压**：五处按压各判红一次，日志 `scratch/goal017-ec04-press.log`；
  按压**只改内存**（跑完 `git status` 里除本 GOAL 的记录面与**别人**的在制品外无改动）。
- **WP3 两树复检**：工作树 + `D:\rs-ec04-clean`（`505f2ab`，detached）两路跑 `--only all`，
  输出 `scratch/goal017-ec04-worktree.out` / `scratch/goal017-ec04-clean.out`；
  **判词列逐行相同**（只比判词列的 `diff` = 0 字节），整份输出的唯一差异是 EC 状态那行的
  **明细文字**（干净树的 GOAL 里 EC-04 还没翻成 PASS）——`scratch/goal017-ec04-twotree.diff`。
- **WP4 m0 终态行**：`make validate-all` 的等价展开命令（本机 Git Bash **无 `make`**，
  按 `Makefile` 的展开命令用仓库 `.venv` + `--keep-going` 独占跑）⇒ 终态行 + 日志 + 复核。
- **WP5 记录面**：本 PLAN + `RECHECK-20260925-185` + GOAL-017 的 EC-04 状态 / 迭代表第 3 行 /
  状态历史 / `child_plans` / `latest_recheck` + `ALL_PLAN` 投影（同提交）。
- **WP6 治理面**：`validate.py` + `DOCS-CHECK`；然后 commit（**逐路径**）→ `pull --ff-only`
  → push main → 轮询 CI 到终态。

## 证据（本地）

| 项 | 证据 |
| --- | --- |
| 结构半 14 条 | `scratch/goal017-ec04-worktree.out`：14 条 `PASS`（EC-01 输入面由 git 决定 / 不可用时点名硬失败 / 判据在位；EC-02 一个声明点 / 一个读取点 / runbook 逐字同源 / 放行面未拓宽；EC-03 阈值与语义未动 / 判据跑在专用作业里 / 共享进程已排除 / 传播无豁免；收口 EC-01…EC-03 = PASS + 13 项终态表在位） |
| 判据半 5 个目标 | 同文件尾行：`3 passed` / `14 passed` / `18 passed` / `3 passed` / `5 passed`；末行 `EC04-RECHECK: PASS` |
| 非恒真按压 | `scratch/goal017-ec04-press.log`：`5/5 PRESS-RED-OK`——`dnn-table` ⇒ 红在「13 项终态表在位」；`switch-name` ⇒ 红在「常量一个声明点」；`job-structure` ⇒ 红在「判据跑在专用作业里」；`threshold` ⇒ 红在「阈值与语义未动」；`git-face` ⇒ 红在「不可用时点名硬失败」 |
| 两树同结论 | `scratch/goal017-ec04-clean.out`（`--root D:/rs-ec04-clean`）与工作树输出的**判词列 19/19 相同**（只比判词列的 `diff` = `scratch/goal017-ec04-twotree-verdicts.diff` = **0 字节**）；整份输出的差异**恰一行**且只在**明细文字**（工作树的 EC 状态多列 `'EC-04': 'PASS'`，干净树停在 `505f2ab`、EC-04 还没翻成 PASS）⇒ `scratch/goal017-ec04-twotree.diff` = **243 字节 / 一行**，**没有一条判据在两树间结论不同** |
| m0 终态行 | **`PASS: profile=m0; 23 deterministic checks`**（`M0_EXIT=0`；`RUN [` = 23 / `PASS [` = **24**，其中 `release-assets-immutable` 在 23 项计数之外；`FAIL` 零行）。日志 `scratch/goal017-c3-m0-as-is.log`，**size `97141`** / **sha256 `748ece31349a61e1aa8818821c38c1098c153a1a100f790f74452c8bc20c82d7`**（跑前跑后同一文件、跑门期间未改工作树）。**`R-3` 已消除** ⇒ 不再需要 GOAL-015/016 那种代管分行标注 |
| 治理面 | 治理 `validate.py` = `Cursor 治理验证通过`（exit 0）；`DOCS-CHECK PASS: 6 deterministic checks`（`scratch/goal017-c3-docs-check.log`）；两者在**本 PLAN / RECHECK 落盘后**重跑通过 |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-25 | IN_PROGRESS | derive：从 GOAL-017 的 EC-04 圈定收口范围，本文件 + `ALL_PLAN` 投影 + `parent_goal` 同提交。 |
| 2026-09-25 | IN_PROGRESS | WP1–WP3：复检脚本落盘并跑到结构 `PASS`；三处调试（读取点判据两次收窄 + `git-face` 按压绑到声明行）后 **5/5 按压 RED-OK**；两树输出一致。 |
| 2026-09-25 | IN_PROGRESS | WP4：m0 **独占**跑（机时**未**与任何写记录动作重叠；`env -u PYTEST_ADDOPTS` 保证 as-is 语义）⇒ 终态行 `PASS: profile=m0; 23 deterministic checks`。 |
| 2026-09-25 | DONE | WP5–WP6：EC-04 = **PASS**（8 条 AC 逐条成立，见 `RECHECK-20260925-185`）；GOAL-017 转 **ACHIEVED**。 |

## 影响报告

- **改动**：**零产品代码 / 零判据 / 零阈值**。只增两个记录文件（本 PLAN + RECHECK-185）
  并改 GOAL-017 的收口面（EC 状态表、迭代日志第 3 行、状态历史、`child_plans` /
  `latest_recheck`）+ `ALL_PLAN` 一行。
- **lint/typecheck/test**：`ruff check` / `ruff format --check` / `mypy` 在 cycle 2 的最终修订上
  全绿且本 cycle **未触碰被它们覆盖的任何文件**；本 cycle 的验证重心是复检脚本两路 + 按压 + m0。
- **Domain/API/schema 变化**：**无**。
- **安全/凭据变化**：**无**（本 cycle **零出网**；复检脚本只读树 + 跑本地判据）。
- **兼容性/迁移风险**：**无**（只动记录面）。
- **上游版本影响**：**无**。
- **下一项任务**：GOAL-017 收口后，下一轮输入 = **13 项表里仍「未授权」的 4 项**
  （D-04 / D-05 / D-06 与 D-01(a) / D-02(a) / D-12(a) 面）与承继残余
  （`R-M1` 的 Mimosa 结论 / `R-D1` 的 `undici` 8 条 + `yaml` 1 条）。
