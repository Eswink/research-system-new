---
id: RECHECK-20260925-185
plan_id: PLAN-20260925-184
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-25
completed_at: 2026-09-25
reviewer: root-agent-goal-017-cycle3（独立复检：`scratch/goal017-ec04-closeout-recheck.py` 两路 + 5 处按压 + 干净 `git worktree` 对照）
baseline_ref: cycle 2 推送 tip `505f2ab`（推送区间 `9cfba09..505f2ab`，CI `run_attempt=1` 八 job 全绿）
checked_head: cycle 3 工作树（收口记录面；**零产品代码改动**）
---

# RECHECK-20260925-185 — GOAL-017 收口复检（EC-04）

> **状态**：**已完成**。8 条 AC 逐条复核，结论见文末。

## 检查范围

EC-04 的四件交付物（两树复检脚本 / m0 终态行 / 13 项 `D-NN` 终态表 / CI 台账到终态）
+ 授权边界在收口面的**零扩面**（本 cycle 不改产品代码 / 判据 / 阈值）+ 承继残余逐条在位。

## 检查结果

### 一、AC-1｜复检两路同时成立（成立）

复检脚本 `scratch/goal017-ec04-closeout-recheck.py`（295 行，**不提交**）**不复用 GOAL 的叙述**：
每一件事都用「**脚本自己重读树**」的结构断言 + 把该 EC 的判据文件在**被测树**里
`subprocess` 实跑（`cwd = --root`，`.venv` 解释器，`-p no:randomly`）两路同时成立。

- **结构半 14 条全 `PASS`**（`scratch/goal017-ec04-worktree.out`）：EC-01 三条（输入面由 git 决定 =
  `git_decided_inputs` + `--cached` ∪ `--others --exclude-standard`；不可用时**点名硬失败** =
  声明行 `GIT_FACE_UNAVAILABLE = "not_a_git_tree"` + 点名消息 + 非 0；成对判据文件在场）、
  EC-02 四条（常量**一个**声明点 = `['RESEARCHOS_LIVE_E2E']`；环境**一个**读取点 =
  `['tests/e2e/live_switch_support.py']`；runbook §4 的操作者命令逐字同源；`egress_guard` 不提开关
  ⇒ 放行面未拓宽）、EC-03 四条（阈值 `_MAX_RSS_GROWTH_MIB = 128.0` 与 `_MAX_TELEMETRY_THREADS = 4`
  逐字在位；`observability-overhead` 专用作业且命令点名该判据；`quality-*` 侧带 `--ignore=`；
  无 `continue-on-error`）、收口两条（EC-01…EC-03 = `PASS`；`D-NN` 行数 = 13）。
- **判据半 5 个目标全过**：`tests/tooling/test_validate_bundle_git_decided_input_face.py` = **`3 passed`**、
  `tests/architecture/python/test_live_switch_is_single_source.py` = **`14 passed`**、
  `tests/e2e/test_ec04_live_gate_offline.py` = **`18 passed`**、
  `tests/observability/test_telemetry_overhead.py` = **`3 passed`**、
  `tests/tooling/test_m0_ci_coverage.py` = **`5 passed`**；末行 `EC04-RECHECK: PASS`。
- **反向独立**：读取点判据**不**沿用仓库判据的 AST 走法，改用「表达式正则 + 反向 AST」；
  两次收窄都是本脚本自己的跑数逼出来的（① 把「提到常量」也算 ⇒ 5 个文件误报；
  ② 缺**词边界** ⇒ `RESEARCHOS_LIVE_E2E_ENDPOINT` / `_KEY` 这两个**另外的**变量被当成开关）。

### 二、AC-2｜非恒真（成立，5/5）

五处按压**只改内存**（`overlay` 文本替换，**不写仓库文件**；跑完 `git status --short` 里除
GOAL-017 的记录面与**别人**的在制品外无改动）：

| 按压 | 改坏的东西 | 结构半红在哪 |
| --- | --- | --- |
| `dnn-table` | GOAL 的 `\| D-11 \|` → `\| D-XX \|` | 「收口 13 项终态表在位」 |
| `switch-name` | 产品常量值 → `"X"` | 「EC-02 常量一个声明点」 |
| `job-structure` | workflow 作业名加后缀 | 「EC-03 判据跑在专用作业里」 |
| `threshold` | 阈值 `128.0` → `256.0` | 「EC-03 阈值与语义未动」 |
| `git-face` | `GIT_FACE_UNAVAILABLE` → `GIT_FACE_GONE` | 「EC-01 不可用时点名硬失败」 |

日志 `scratch/goal017-ec04-press.log`：`5/5 PRESS-RED-OK`，**零 `PRESS-GREEN-BAD`**。
**一次按压抓出判据自身漏检**（如实登记）：`git-face` 第一次是 **GREEN-BAD**——原检查写的是
「文中出现过 `GIT_FACE_UNAVAILABLE`」，而替换后 `validate_bundle.py` 的 docstring 里仍**引用**
着这个词 ⇒ 恒真。改为**绑到声明行**（`GIT_FACE_UNAVAILABLE = "not_a_git_tree"`）后判红。
**这与 GOAL-017 cycle 2 的同类发现是同一个病**（文本判据会被文档/注释喂饱）——已是第二次，
形态是「看见一个词」而不是「看见那个赋值」。

### 三、AC-3｜两棵树同结论（成立）

`--only all` 在**工作树**与**干净 checkout**（`git worktree`：`D:\rs-ec04-clean`，detached
HEAD = `505f2ab`，即 cycle 2 的推送 tip）两路各跑一次：
`scratch/goal017-ec04-worktree.out` / `scratch/goal017-ec04-clean.out`，两份都以
`EC04-RECHECK: PASS` 结尾。

**如实登记两版的差异（不为「diff 为空」这句话而清洗证据）**：

- **EC-04 翻状态之前**（两树的 GOAL 里 EC-04 都还没翻成 PASS）：整份输出**逐字相同**。
- **EC-04 翻成 `PASS` 之后**（本 RECHECK 定稿版）：**19 行判词行（14 结构 + 5 判据）逐行相同**，
  但整份输出有**恰一行**差异——「收口 EC-01…EC-03 = PASS」那行的**明细文字**
  （工作树多列一个 `'EC-04': 'PASS'`），因为干净树停在 `505f2ab`、其 GOAL 里 EC-04 还没翻成 PASS。
  ⇒ 原始 `diff` = `scratch/goal017-ec04-twotree.diff`（**243 字节、一行**）；
  **只比判词列**（去明细、去耗时）的 `diff` = `scratch/goal017-ec04-twotree-verdicts.diff`
  = **0 字节**。**没有一条判据在两树间给出不同结论**；差异只在**记录面**（见 `W-2`）。

### 四、AC-4｜m0 终态行（成立）

**as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`**（终态行逐字；`PASS [` = 24，
其中 `release-assets-immutable` 在 23 项计数之外）。跑法 = `Makefile` 里 `validate-all` 目标的
**展开命令**（`uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py
--profile m0 --keep-going`），副本 `.venv` + 独占（无并发跑门、跑门期间未改工作树）。
日志 `scratch/goal017-c3-m0-as-is.log`（`M0_EXIT=0`；`RUN [` = 23、`PASS [` = **24**、`FAIL` 零行）；
终端锚点复核 = **size `97141` / sha256 `748ece31349a61e1aa8818821c38c1098c153a1a100f790f74452c8bc20c82d7`**。
**`R-3` 已消除** ⇒ 本 GOAL **不再需要** GOAL-015/016 那种「代管跑法」的分行标注。

### 五、AC-5｜13 项 `D-NN` 终态表（成立）

GOAL-017 的终态表 **13 行**（`D-01`…`D-13`）逐行在位（结构半的「`D-NN` 行数 = 13」也是
按压面之一）。三条本轮授权项已从「需授权未实施」改为**已实施**：`D-10`（EC-01 / PLAN-180）、
`D-11`（EC-02 / PLAN-182）、`D-13`（EC-03 / PLAN-182）；**未授权 4 项**（`D-04` / `D-05` /
`D-06` 与 `D-01(a)` / `D-02(a)` / `D-12(a)` 的 (a) 面）逐条写明「未实施 + 阻断依据 + 原样保留」，
且**未**被本 GOAL 收口或掩盖。

### 六、AC-8｜承继残余逐条在位（成立）

`R-F1` / `R-F2` / `R-F3` / `R-M1` / `R-D1` / `R-B1` / `R-N1` / `W-1…W-7` 在 GOAL-017 里
逐条在位（`R-F3` 的处置已随 EC-01 落地：同一事实既是「`R-3` 消失」也是「`R-F3` 收口」；
`W-7` 的**残余部分**——「开关 + 凭据下 live 用例仍会真出网」——按设计保留）。

### 七、AC-6 / AC-7（治理面 + CI 台账）

见文末「收口补充」（治理 `validate.py` / `DOCS-CHECK` 的实测 + 本 cycle 推送 run 的终态口径）。

## 警告（不阻断收口，原样登记）

- **W-1｜`make` 在本机不可用**：GOAL 的 EC-04 `verify` ④ 写的是 `make validate-all` 的终态行；
  本机 Git Bash **没有 `make`**，实际跑的是 `Makefile` 里该目标的**展开命令**（同一 runner、
  同一 `--keep-going`、同一 `.venv`）⇒ 终态行的**判据面相同**，但**不是** `make` 本身这一层。
- **W-2｜两树 `diff` 的覆盖面**：两树对照的是**复检脚本的输出**，不是整棵树——cycle 3 的
  **记录面**（GOAL 收口 / 本 PLAN / 本 RECHECK）在两树里**本就不同**（干净树停在 `505f2ab`）。
  这不是「设计上无所谓」，而是**必须逐字说清**：翻 EC-04 状态之前整份输出逐字相同；
  翻之后差异**恰一行**，且只落在**明细文字**（EC 状态字典多一个键）上——**判词列 19/19 相同**、
  只比判词列的 `diff` 为 **0 字节**。要「两树整份输出逐字相同」就得让干净树也含收口记录，
  那等于用工作树的内容去**污染**用来做对照的基线 ⇒ **不这么做**。
- **W-3｜按压抓出的判据自身漏检**（见 AC-2）：词出现 ≠ 声明在位。同类已出现两次
  （cycle 2 的「唯一读取点」第一版按文本判），**下一次写「某处必须存在 X」的判据时先问：
  文档/注释里出现这个词算不算**。
- **W-4｜干净树停在上一个 tip**：`D:\rs-ec04-clean` 是 `505f2ab` 的 detached checkout，
  复检后应清理（本 PLAN 的 WP3 已登记）；另有两个更早的遗留 worktree（`g013final` /
  `goal015-c3-clean`）不属于本 GOAL。
- **W-5｜复检脚本不提交**：`scratch/goal017-ec04-*` 与按压日志按仓库惯例留在工作区
  （`.gitignore:43` 的 `scratch/`），**不进 git** ⇒ 证据的可复核性依赖工作树仍在本机。

**残余风险**：本 cycle **零出网**、零产品代码改动 ⇒ 复检的独立性来自**另一个观察者视角**
（脚本自己重读树 + 子进程实跑 + 干净树对照）+ **非恒真按压**，不来自新的人工确认。

## 收口补充（治理面 + CI 台账终态）

### AC-6 实测

- `.cursor/skills/governance-check/scripts/validate.py` = `Cursor 治理验证通过`（exit 0；
  含 `ALL_PLAN / Task Plan / Recheck / Memory 交叉引用一致` 与
  `GOAL 循环记录（plans/goals/）结构合规；push 授权显式登记` 两组判词）。
- `DOCS-CHECK` = `PASS: 6 deterministic checks`（`scratch/goal017-c3-docs-check.log`）。
- **时序如实登记**：m0 的终态行取自**记录已落盘**的那一版修订；m0 之后只再落了
  「m0 行 / 治理行」这类**记录文字**填充，并对填充后的修订**重跑** `validate.py` +
  framework profile ⇒ 仍绿（不是「先跑门再补记录就不管了」）。

### AC-7 实测

本 GOAL 的 CI 台账四行（建档 `25d802b` / cycle 1 `9cfba09` / cycle 2 `958c321`+`505f2ab` /
cycle 3 = 本收口提交）逐行在位；**cycle 3 行所在提交的 run 终态在回合汇报给出**
（收口惯例：写入台账那一行的提交，其 run 在其自身推送后才知道结论）。

## 结论

**`result: PASS_WITH_WARNINGS`** —— 8 条 AC **逐条成立**（AC-1 复检两路 / AC-2 5/5 按压非恒真 /
AC-3 两树同结论 / AC-4 m0 终态行 / AC-5 13 项终态表 / AC-6 治理面绿 / AC-7 CI 台账到终态 /
AC-8 承继残余在位），**5 条警告原样登记**（`W-1` 本机无 `make`、`W-2` 两树 `diff` 的覆盖面、
`W-3` 判据自身的「词出现 ≠ 声明在位」（AC-2 抓出的同类第二次）、`W-4` 干净树待清理 +
两个更早遗留 worktree、`W-5` 复检脚本按惯例不提交）。

**本 cycle 零产品代码改动、零出网、零新依赖**：复检的独立性来自「另一个观察者视角」
（脚本自己重读树 + 子进程实跑 + 干净 `git worktree` 对照）+ **非恒真按压**，不来自新的人工确认。
⇒ **EC-04 可判 PASS**，GOAL-017 可转 **ACHIEVED**（四条 EC 全 PASS，且每条都有实跑证据 +
独立复检）。
