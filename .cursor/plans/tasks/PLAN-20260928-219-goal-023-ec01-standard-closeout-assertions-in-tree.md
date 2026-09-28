---
id: PLAN-20260928-219
slug: goal-023-ec01-standard-closeout-assertions-in-tree
title: GOAL-023 cycle 1（EC-01）：标准收口断言集进树 —— 公共断言集 + 判据 + 规范页点名 + 两树留档 + 跨提交形态实测
status: DONE
created_at: 2026-09-28
updated_at: 2026-09-28
parent_goal: GOAL-20260928-023
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260928-023 的 **EC-01**（标准收口断言集进树，收 `RECHECK-20260928-218` 的 `W-3`）。
    授权沿用该 GOAL 的 `authorization.ref`：范围严格限定为「**复检资产归档化** +
    `tools/` 受判面以**新增判据**形式收口 + **受判射程边界机械化**」三件事 + **修被新判据证明的缺陷**
    + **文档同源更新**；**不加新能力、不改安全策略、不放宽任何判据、不修改任何既有判据**；
    push-to-main-for-CI 口径（**只推 main、不 force、不重写历史、不推旁支**）；
    默认 runtime 保持 **Fake**、默认 CI **离线**、默认门**一律离线**。
    **本 PLAN 专属边界**：**不得**改任何既有判据 / 门禁 / 阈值 / 放行面（只**新增**）；
    **不得**改 `PRODUCT_ROOTS` / m0 条数 / 作业结构；**不得**新增依赖；
    **不得**把 token 写进任何地方；**不得**宣称项目安全（`R-M1` 未收口）。
exit_criteria:
  - id: AC-1
    criterion: >-
      断言集**在树**（`tools/closeout_recheck_assertions.py`，标准库、`--root` 参数化、
      `--verdict-only`、判词纯且路径无关），其判据落在 `tests/**`（m0 收集面内 ⇒ 条数仍 23）
    status: PASS
  - id: AC-2
    criterion: >-
      用既有入口 `tools/two_tree_recheck.py` 以 `--script-mode tree` 对「当前树 + 干净 checkout」
      跑**同一份断言集字节**，两路判词**各自落盘** + `sha256` + `cmp`，入口退出码 `0`
    status: PASS
  - id: AC-3
    criterion: 规范页 `docs/architecture/RECHECK_SCRIPT_CONVENTIONS.md` 的断言集小节点名它，且**条款不得悬空**（被点名文件按 AST 真的声明 `standard_verdicts`）
    status: PASS
  - id: AC-4
    criterion: >-
      **反证**：改名断言集公开入口 ⇒ 判据判红；抽走断言集命名 ⇒ 判据判红；两者**逐字节复原**
      （raw `sha256`）⇒ 绿。另：**空树不空转**（空树上必须有一批 `FAIL`，承 MEM-156）
    status: PASS
  - id: AC-5
    criterion: >-
      **跨提交形态实测**（承 GOAL-022 `W-2`）：用 `--base-ref` 指向**非 HEAD** 的提交跑同一断言集，
      **如实登记**观察到的形态（入口原样报 `DIFF` / `NOT-GREEN` / `TWO-TREE RED`，**不得**归一化）；
      本项**只作形态实测与登记**，**不作**「必须一致」的判据
    status: PASS
  - id: AC-6
    criterion: >-
      as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`，且运行**在记录写入之后**（承 MEM-145）；
      治理 `validate.py` 绿；CI 台账到终态
    status: PASS
latest_recheck: .cursor/plans/rechecks/RECHECK-20260928-220-goal-023-ec01-standard-closeout-assertions.md
memory_entries:
  - .cursor/memory/entries/MEM-20260928-157-a-naming-can-be-satisfied-twice-inside-one-section.md
---

# PLAN-20260928-219 — GOAL-023 cycle 1（EC-01）：标准收口断言集进树

**主题**：把「**任何 GOAL 的收口复检都要断言的公共事实**」从 gitignored 的 `scratch/` 搬进树，
让未来的收口复检**只写自己特有的断言**。这收的是 `RECHECK-20260928-218` 的 **`W-3`**：
GOAL-022 的 12 条判词**可复跑但不可归档**，他人 clone 仓库后无法直接复核。

**交付面**：`tools/closeout_recheck_assertions.py`（18 条公共判词）+ 判据
（`tests/tooling/test_closeout_assertions_are_in_tree.py`，6 例）+ 规范页增补小节
（`## 标准收口断言集`）。**零产品代码改动、零既有判据改动、零新依赖。**

## 验收条件

| # | 条件 | 状态 |
| --- | --- | --- |
| AC-1 | 断言集在树 + 判据在 `tests/**`（m0 仍 23） | **PASS** |
| AC-2 | `--script-mode tree` 两树实跑：18 条判词逐行相同、`sha256` 相同、两路各自落盘且 `cmp` 一致、退出码 `0` | **PASS** |
| AC-3 | 规范页小节点名它，且被点名文件按 **AST** 真的声明 `standard_verdicts` | **PASS** |
| AC-4 | 按压两处（公开入口改名 / 小节点名抽走）各判红；raw `sha256` 逐字节复原 ⇒ 绿；空树不空转 | **PASS** |
| AC-5 | 跨提交形态**如实登记**（非 HEAD 的 `--base-ref` ⇒ `DIFF` / `NOT-GREEN` 原样） | **PASS** |
| AC-6 | as-is m0 23/23（记录之后）+ 治理绿 + CI 台账终态 | **PASS** |

## 实施清单

- [x] WP1（`743297d`）：`tools/closeout_recheck_assertions.py` —— 18 条公共判词，公开面
      `Verdict` / `standard_verdicts` / `emit`；`--root` 参数化、`--verdict-only`、判词路径无关。
- [x] WP2（`da6e904` / `a895093`）：判据 6 例 + 规范页 `## 标准收口断言集` 小节（点名断言集与其判据）。
- [x] WP3：两树实跑留档（`tree` 模式）+ 跨提交形态实测 + 两处按压与逐字节复原。
- [x] WP4：记录（本 PLAN / `RECHECK-20260928-220` / `MEM-20260928-157` / GOAL 回写）+ m0 + push + CI 台账。

## 证据

**自查（新交付物必须自洽通过既有门）**

| 观察 | 结果 |
| --- | --- |
| `ruff check` / `ruff format --check` | 两个新文件**全绿** |
| `mypy`（含 `strict = true`） | `Success: no issues found in 1 source file`（两个文件同） |
| 规模门自查（口径 `end_lineno - lineno + 1`；文件 `splitlines()`） | 断言集 **388 行** / 判据 **145 行**；**无**超 50 行函数 |
| 断言集自跑 | `--verdict-only` ⇒ **18 条全 PASS**、退出码 `0` |
| 定向套件 | 新判据 **6 passed**；+ 既有入口 11 例 + 规范钉条款 6 例 + 多路证据 9 例 = **32 passed** |

**两树实跑（AC-2；`--script-mode tree` ⇒ 两棵树各取自己 checkout 里的同一份断言集字节）**

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
| 逐行比对 | `COMPARE identical=True`、**零** `DIFF`、**零** `NOT-GREEN` |
| 入口退出码 | `TWO-TREE PASS` / `EXIT=0` |
| 落档 | `scratch/goal023-ec01-verdict-current.txt` / `…-clean.txt`；两文件 raw `sha256` **同为** `b6ae3dac…`，`cmp` = 一致 |
| 运行记录 | `scratch/goal023-ec01-two-tree.log` |

**跨提交形态实测（AC-5；`--base-ref 743297d` = 非 HEAD 的提交，那一棵树上还没有判据与规范页小节）**

| 观察 | 结果 |
| --- | --- |
| 当前树 | `exit=0 verdicts=18 sha256=b6ae3dac…` |
| 干净 checkout @ `743297d` | `exit=1 verdicts=18 sha256=09f01aceb0eaded9beb55eb9876522dbf48668c2b6a0e3c71ced6f3e1b53f89b` |
| 比对 | `COMPARE identical=False` + **3 条 `DIFF`**（退出码 + 2 条判词行） |
| 不绿理由 | **2 条 `NOT-GREEN`**（`closeout-assertions-judge-present` / `conventions-name-the-entry-and-the-assertions`） |
| 入口终局 | `TWO-TREE RED` / `EXIT=1` —— **原样报出，未归一化** |
| 运行记录 | `scratch/goal023-ec01-crosscommit.log`；判词落档 `…-crosscommit-{current,clean}.txt` |

**按压与逐字节复原（AC-4；按压 / 复原一律用 Edit 工具）**

| # | 按压内容 | 判据结果 | 复原证据 |
| --- | --- | --- | --- |
| 1 | 把断言集公开入口 `standard_verdicts` **改名**（定义与调用点同改，模块仍可运行） | **`3 failed, 3 passed`** —— 红的是「AST 读公开面」「规范页点名文件的 AST 复核」「抽走 ⇒ 翻转」 | raw `sha256` 回到 `dc18919b23b29168cad6698d51557bc511febd51517c54a2cd760d03cb300b2a`（与按压前一致）；复跑 **6 passed** |
| 2 | 把规范页小节里**两处**点名（条款句 + 用法片段）都抽走 | **`2 failed, 4 passed`** —— 红的是「输出纯度且本树全绿」（公共判词出现 `FAIL`）与「小节点名 + AST 复核」 | raw `sha256` 回到 `5ec43a9963e8c074f0057adf9aacec2b9f04f31b97f9b1859a99301421d4adea`（与按压前一致）；复跑 **23 passed** |

**空树不空转（承 MEM-156）**：判据第 4 例在 `tmp_path` 的空树上要求**至少 5 条判红**
且退出码非 `0` ⇒ 「全绿」不是恒真。

**as-is 本机 m0（记录写入之后、独占、仓库 `.venv`、DSN 固化）**

| 观察 | 结果 |
| --- | --- |
| 终态行 | `PASS: profile=m0; 23 deterministic checks`（退出码 `0`） |
| `PASS [` 行数 | **24**（`release-assets-immutable` 在计数之外） |
| 用例计数 | **4649 passed / 21 skipped**（较交付前 **+7** = 新判据 6 例 + 新文件进入规模门参数化面 1 项） |
| `FAILED` / `ERROR` | **零** |
| 日志与时刻 | `scratch/goal023-c1-m0.log`，文件时刻 **晚于**本 PLAN 与 `RECHECK-220` 的写入时刻 ⇒ 门在记录之后 |
| 治理 | `validate.py` = `Cursor 治理验证通过` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-28 | IN_PROGRESS | 建档并开始 WP1；EC-02 的判据（必备清单）依赖本 PLAN 的断言集文件，故本 PLAN 先行。 |
| 2026-09-28 | DONE | 六条验收全部成立且有实跑证据（两树同结论 + 跨提交形态如实登记 + 两处按压逐字节复原 + 空树不空转）；`RECHECK-20260928-220` = `PASS_WITH_WARNINGS`。 |

## 影响报告

- **Domain / API / schema**：**零改动**。
- **安全 / 凭据**：**零改动**；未新增任何 token 字面量（判据不用凭据）。
- **兼容性 / 迁移风险**：**无**。新增的是**公共断言集 + 判据 + 规范页小节**；
  判据只读仓库事实，不改任何既有判据的强度。
- **上游版本影响**：**零依赖改动**。
- **未覆盖范围（原样保留）**：读面未认证 / 多租户与 RBAC 未做 / BOLA·BFLA 未做 /
  部署面未验证 / `R-M1` 未收口（**不得**宣称项目安全）。
- **下一项任务**：GOAL-023 EC-02（`tools/` 受判面以**新增判据**收口；首个受判对象是入口自身
  的 53 行 `main` 与复杂度 14 > 10）。
