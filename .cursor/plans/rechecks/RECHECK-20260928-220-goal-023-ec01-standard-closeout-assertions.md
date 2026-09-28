---
id: RECHECK-20260928-220
slug: goal-023-ec01-standard-closeout-assertions
title: GOAL-023 EC-01 复检：标准收口断言集在树、可跑、不空转、条款不悬空（两树同结论 + 跨提交形态如实登记 + 两处按压逐字节复原）
plan_id: PLAN-20260928-219
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-28
completed_at: 2026-09-28
owners:
  - root-agent
---

# RECHECK-20260928-220 — GOAL-023 EC-01 复检

**复检口径**：不复用 PLAN / GOAL 的叙述；每项给出**可复核观察面**；**未实跑的不记通过**。
本轮的独立面是「**断言集真的在树且真的会在被破坏时判红**」，而不是「有一份看起来齐全的判词」。

## 检查结果

### 一、交付面与自洽门

| # | 观察 | 结果 |
| --- | --- | --- |
| 1.1 | 断言集 `tools/closeout_recheck_assertions.py` | **在树**（不是 `scratch/` 探针 —— 这正是 `W-3` 的收口面） |
| 1.2 | 其判据 `tests/tooling/test_closeout_assertions_are_in_tree.py` | **在树**（落在 `tests/**` ⇒ m0 收集面内） |
| 1.3 | `ruff check` + `ruff format --check` | 两个新文件**全绿** |
| 1.4 | `mypy`（`strict = true`） | 两个文件各 `Success: no issues found in 1 source file` |
| 1.5 | 规模门自查（口径 `end_lineno - lineno + 1`；文件 `splitlines()`） | 断言集 **388 行**、判据 **145 行**；**无**超 50 行函数 |
| 1.6 | 断言集自跑（`--root . --verdict-only`） | **18 条全 `PASS`**、退出码 `0` |
| 1.7 | 定向套件 | 新判据 **6 passed**；与既有入口判据（11）+ 规范钉条款（6）+ 多路证据（9）合跑 **32 passed** |
| 1.8 | 零改动面 | 既有判据 / 门禁 / 阈值 / 产品代码 / 依赖 **零改动**；`git status` 对按压涉及的两个文件为空 |

### 二、两树实跑（AC-2）

命令（`--script-mode tree` ⇒ 两棵树各自从**自己的 checkout** 取同一份断言集字节，
这正是「断言集**进树**」后才能用的模式）：

```text
uv run --frozen --no-sync python -B tools/two_tree_recheck.py \
  --script tools/closeout_recheck_assertions.py --script-mode tree --root . --base-ref HEAD \
  --verdict-current scratch/goal023-ec01-verdict-current.txt \
  --verdict-clean  scratch/goal023-ec01-verdict-clean.txt
```

| 观察 | 结果 |
| --- | --- |
| 当前树 | `exit=0 verdicts=18 sha256=b6ae3dac32b8ed54905b81a65605a71ebddea8d8599146f1c517e1f15597a0e5` |
| 干净 checkout | `exit=0 verdicts=18 sha256=b6ae3dac32b8ed54905b81a65605a71ebddea8d8599146f1c517e1f15597a0e5` |
| 比对 | `COMPARE identical=True`、**零** `DIFF`、**零** `NOT-GREEN` |
| 入口终局 | `TWO-TREE PASS` / `EXIT=0` |
| 落档 | 两路各自落盘；两文件 raw `sha256` **同为** `b6ae3dac…`，`cmp` 判**一致** |
| 运行记录 | `scratch/goal023-ec01-two-tree.log` |
| 进程卫生 | 干净树由入口自建自删；跑后 `git worktree list` 只剩主树与三个历史遗留 worktree，`tasklist` python 进程 **0** |

### 三、跨提交形态实测（AC-5；**只作形态实测与登记**）

用同一断言集、`--base-ref 743297d`（**非 HEAD** 的提交：那一棵树上**还没有**判据与规范页小节）。

| 观察 | 结果 |
| --- | --- |
| 当前树 | `exit=0 verdicts=18 sha256=b6ae3dac…` |
| 干净 checkout @ `743297d` | `exit=1 verdicts=18 sha256=09f01aceb0eaded9beb55eb9876522dbf48668c2b6a0e3c71ced6f3e1b53f89b` |
| 比对 | `COMPARE identical=False` |
| `DIFF` | **3 条**：`退出码不同：current=0 clean=1`；第 7 行 `closeout-assertions-judge-present`；第 17 行 `conventions-name-the-entry-and-the-assertions` |
| `NOT-GREEN` | **2 条**（上述两条判词在干净树上是 `FAIL`） |
| 入口终局 | `TWO-TREE RED` / `EXIT=1` —— **原样报出，未归一化** |
| 运行记录 | `scratch/goal023-ec01-crosscommit.log`；判词 `…-crosscommit-{current,clean}.txt` |

**如实登记**：这是「**跨提交确实会报 `DIFF` / `NOT-GREEN`**」的**形态实测**，不是一致性保证。
本项**不作**判据（GOAL 明文：只作形态实测与登记）。

### 四、按压与逐字节复原（AC-4）

按压 / 复原**一律用 Edit 工具**（本仓 Bash 直接写源码会被安全扫描拒绝）。

| # | 按压内容 | 判据结果 | 复原证据（raw `sha256`） |
| --- | --- | --- | --- |
| 1 | 断言集公开入口 `standard_verdicts` **改名**（定义与调用点同改 ⇒ 模块仍可运行，只是不再声明该公开面） | **`3 failed, 3 passed`**：红的是「AST 读公开面」「规范页点名文件的 AST 复核」「抽走 ⇒ 翻转」 | 回到 `dc18919b23b29168cad6698d51557bc511febd51517c54a2cd760d03cb300b2a`（与按压前一致）⇒ 复跑 **6 passed** |
| 2 | 规范页小节里**两处**点名（条款句 + 用法片段）全部抽走 | **`2 failed, 4 passed`**：红的是「输出纯度且本树全绿」（公共判词出现 `FAIL`）与「小节点名 + AST 复核」 | 回到 `5ec43a9963e8c074f0057adf9aacec2b9f04f31b97f9b1859a99301421d4adea`（与按压前一致）⇒ 合跑 **23 passed** |

**抽走 ⇒ 判红（根一级）**：判据第 6 例把断言集从**空树**里「抽走」⇒
`closeout-assertions-present` 这条判词**翻转**（本树绿、空树红）。

**不空转（承 MEM-156）**：判据第 4 例在空树上要求**至少 5 条判红**且退出码非 `0`
⇒ 「全绿」不是恒真。

### 五、条款不得悬空（AC-3）

- 规范页增补小节 `## 标准收口断言集` **在树**，小节点名 `tools/closeout_recheck_assertions.py`
  与其判据文件；
- 判据**按 AST 读声明**核验被点名文件真的声明了 `standard_verdicts`
  ⇒ 改名 / 搬走 / 换成空壳**都判红**（第 4 表 #1 即为实证）；
- 既有两条读该规范页的判据（两树入口 11 例、规范钉条款 6 例）**保持全绿**
  ⇒ 增补**未**破坏既有结构性锚点。

### 六、本次复检**未**复核的面

- **断言集是否完备**：本轮只证明「这 18 条断言在树上成立、在被破坏时会红」，
  **不证明**这 18 条**覆盖了收口复检该断言的所有事**；
- **`tools/` 的类型 / 格式 / 规模门**：**今天仍然没有** —— `tools/` 不在 `PRODUCT_ROOTS`，
  本轮的断言集与判据都只是让入口的**行为**被钉住；给 `tools/` 加机器门是 **EC-02** 的交付面，
  **截至本条复检尚未成立**；
- **跨平台**：所有实测都在本机（Windows）；两树入口的路径无关判据在别的平台上
  是否等价**未复验**；
- **历史遗留 `tools/` 脚本**：仍不受任何判据覆盖（收口需另行授权）。

### 七、as-is 本机 m0（**记录写入之后**，承 MEM-145）

顺序：**写记录 → 记录面判据 → 全量门**。全量门**独占**运行（跑门期间未改工作树），
解释器用仓库 `.venv`（`uv run --frozen --no-sync python -B`），DSN 按既有配方钉死。

| 观察 | 结果 |
| --- | --- |
| 终态行 | `PASS: profile=m0; 23 deterministic checks`（退出码 `0`） |
| `PASS [` 行数 | **24**（`release-assets-immutable` 在计数之外，与既有台账一致） |
| 用例计数 | **4649 passed / 21 skipped**（较本条交付前 **+7**：新判据 **6 例** + 新文件进入既有规模门判据的参数化面 **1 项**） |
| `FAILED` / `ERROR` | **零** |
| 进程卫生 | 跑门前 `tasklist` 零 python 进程；跑门期间不写工作树；跑完仍**零**泄漏 |
| 日志与时刻 | `scratch/goal023-c1-m0.log`，文件时刻 `13:24:29` **晚于**本记录写入时刻 `13:07:28` ⇒ **门在记录之后**（可用 `ls -l` 复核，不依赖此处抄写的时刻字面） |
| 治理 | `validate.py` = `Cursor 治理验证通过`（含「ALL_PLAN / Task Plan / Recheck / Memory 交叉引用一致」与「未发现明显凭据材料」） |

## 结论

**PASS_WITH_WARNINGS。** 六条验收（AC-1…AC-6）**全部成立且有实跑证据**：
断言集**进树**（`tools/closeout_recheck_assertions.py`，388 行、18 条判词）、
其判据在 `tests/**`（6 例）、规范页小节点名且按 **AST** 复核；
**两树实跑**（`tree` 模式）18 条判词**逐行相同**、`sha256` 同为 `b6ae3dac…`、
两路各自落档且 `cmp` 一致、`TWO-TREE PASS` / `EXIT=0`；
**跨提交形态如实登记**（`--base-ref 743297d` ⇒ 3 条 `DIFF` + 2 条 `NOT-GREEN` +
`TWO-TREE RED` / `EXIT=1`，**未归一化**）；
**两处按压**各判红且 raw `sha256` **逐字节复原**；空树**不空转**。
**as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = 24、4649 passed / 21 skipped、
零 `FAILED` / `ERROR`），且**运行在记录写入之后**。
**零产品代码改动、零既有判据改动、零新依赖。**

**警告（如实登记）**：

- **`W-1`**：断言集断言的是**结构性事实**（文件在不在、AST 声明、运行器算出的 m0 条数、
  记录自洽），**不判**任何交付物的**实质质量**；「18 条全绿」**不等于**「这一轮做对了什么」。
- **`W-2`**：两树比的是**同 tip** ⇒ 只证明「结论不依赖工作树里未提交的残留」。
  跨提交那一跑是**形态实测**（证明了入口**会如实报红**），**不是**跨提交一致性保证；
  跨平台面**完全未复验**。
- **`W-3`**：**`tools/` 仍然逃脱 ruff / mypy / 规模门**（`PRODUCT_ROOTS` 不含 `tools`）。
  本条收的是 `RECHECK-20260928-218` 的 **`W-3`（断言集不可归档）**，
  **不是**其 `W-4`（`tools/` 无机器门）—— 后者归 **EC-02**，**截至本条复检尚未成立**。
- **`W-4`**：按压用的是「**改名公开入口**」与「**抽走小节点名**」两种形态（Edit 做、逐字节复原）；
  对**被追踪文件做真实删除 / 改名**的按压**未做**（本仓 Bash 直接改源码会被安全扫描拒绝），
  「抽走」这一形态由**空树**（根一级）覆盖。
- **`W-5`**：本条复检**不含**任何授权面 / 认证面新结论。`W-10` / `W-11` / `W-12` 与
  `R-M1` **原样保留**；**不得**引作安全结论。

**未覆盖范围（承 GOAL-023 的边界，原样保留）**：读面未认证 / 多租户与 RBAC 未做 /
BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口（**不得**宣称项目安全）。
