---
id: PLAN-20260928-225
slug: goal-023-ec04-closeout-two-tree-self-bootstrap
title: GOAL-023 cycle 4（EC-04）：自举收口复检 —— 收口验证器进树 + 用两树入口跑本轮自己的复检 + 残余与未覆盖范围逐条登记
status: DONE
created_at: 2026-09-28
updated_at: 2026-09-28
parent_goal: GOAL-20260928-023
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260928-023 的 **EC-04**（自举收口复检 + 残余登记）。授权沿用该 GOAL 的
    `authorization.ref`：范围严格限定为「**复检资产归档化 + `tools/` 受判面以新增判据收口 +
    受判射程边界机械化**」三件事 + 修被新判据证明的缺陷 + 文档同源更新；
    **不加新能力、不改安全策略、不放宽任何判据**；push-to-main-for-CI 口径
    （**只推 main、不 force、不重写历史、不推旁支**）；默认 runtime 保持 **Fake**、
    默认 CI **离线**。
    **本 PLAN 专属边界**：**不得**放宽 / 削弱任何既有判据、门禁、阈值或放行面；
    **不得**修改任何既有判据（只允许**新增**）；**不得**改 `PRODUCT_ROOTS` / m0 条数 /
    作业结构；**不得**新增依赖；**不得**把 token 值写进任何地方；**不得**给读面加认证；
    **不得**做多租户 / RBAC / BOLA·BFLA；**不得**宣称项目安全（`R-M1` 未收口）；
    **不得**为了「让收口好看」而改动受保护判据或历史记录。
exit_criteria:
  - id: AC-1
    criterion: >-
      自举：用 EC-01 的入口 `tools/two_tree_recheck.py` 对「当前树 + 干净 checkout」跑本轮的
      收口验证器 `tools/verify_goal023_closeout.py` ⇒ 两树判词**逐行相同** + `sha256` 相同 +
      两路**各自留档**（`cmp` 一致），入口退出码 `0`
    status: PASS
  - id: AC-2
    criterion: >-
      收口验证器**复用**标准断言集（`standard_verdicts` / `emit`），且**只写** GOAL-023 特有断言；
      它自己**也是受判对象**（EC-02 判据的必备清单显式列入）⇒ 四道门全绿
    status: PASS
  - id: AC-3
    criterion: >-
      as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`，且运行**在记录写入之后**
      （承 MEM-145：写记录 → 记录面判据 → 全量门）
    status: PASS
  - id: AC-4
    criterion: 治理 `validate.py` 绿（含 `DOCS-CHECK`）
    status: PASS
  - id: AC-5
    criterion: CI 台账到终态（M0 八 job + CodeQL，含 `run_attempt`；cycle 3 补入台账）
    status: PASS
  - id: AC-6
    criterion: >-
      承继残余逐条在位（`R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` /
      `W-4` / `W-5` / `W-6` / `W-10` / `W-11` / `W-12`）+ **新增三条残余登记**
    status: PASS
  - id: AC-7
    criterion: >-
      未覆盖范围逐条明写（读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 /
      `R-M1` 未收口 ⇒ **不得**宣称项目安全）
    status: PASS
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260928-226-goal-023-closeout-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260928-160-union-scope-hides-a-shrinking-required-list.md
---

# PLAN-20260928-225 — GOAL-023 cycle 4（EC-04）：自举收口复检

**主题**：GOAL-022 的收口复检断言集落在 **gitignored 的 `scratch/`**（`W-3`：可复跑但不可归档）。
本 GOAL 的 EC-01 把它**搬进树**、EC-02 让 `tools/` 的**被点名脚本**过产品同款的四道门。
**EC-04 就是这两件事的合流**：本轮的收口复检**自己**就是「**进树的验证器**」
（`tools/verify_goal023_closeout.py`），它**复用**标准断言集、**只写**本轮特有的断言，
并且**自己也被 EC-02 的判据判**（新增脚本必须显式进入必备清单）。

**与 GOAL-022 收口轮的关键差异（本 GOAL 要收的正是这个）**：GOAL-022 的收口复检探针在
`scratch/`（**不可归档**）且**不受任何机械门覆盖**；本轮的收口验证器**在树、可归档、
且过四道门** —— 「复检资产归档化 + 受判面收口」由此闭合。

## 验收条件

| # | 验收条件 | 结果 |
| --- | --- | --- |
| AC-1 | 入口 `tools/two_tree_recheck.py` 跑 `tools/verify_goal023_closeout.py` ⇒ 两树 **33 条**判词逐行相同 + `sha256` 相同 + 两路各自留档（`cmp` 一致）+ `EXIT=0` | **PASS** |
| AC-2 | 验证器**复用** `standard_verdicts` / `emit`（只写特有断言），且**自己过四道门**（`ruff format --check` / `ruff check` / 规模 / `mypy`） | **PASS** |
| AC-3 | as-is 本机 m0 到 **23/23**（终态行 `PASS: profile=m0; 23 deterministic checks`），且**在记录写入之后**（承 MEM-145） | **PASS** |
| AC-4 | 治理 `validate.py` 绿（含 `DOCS-CHECK`） | **PASS** |
| AC-5 | CI 台账到终态（M0 **八 job** + CodeQL，含 `run_attempt`） | **PASS** |
| AC-6 | 承继残余 **12 个 ID** 逐条在位 + **新增三条残余**登记 | **PASS** |
| AC-7 | 未覆盖范围**逐条明写** | **PASS** |

## 实施清单

| WP | 内容 | 状态 |
| --- | --- | --- |
| WP1 | 写 `tools/verify_goal023_closeout.py`：复用标准断言集，只加本轮特有断言（EC-01…03 终态 / `latest_recheck` 解析 / 子计划与记忆存在 / 残余登记在位 / 未覆盖范围明写） | 完成 |
| WP2 | 把验证器**显式**加入 EC-02 判据的必备清单（分区判据会抓未分类的新脚本）+ 规范页点名它为参考实现 | 完成 |
| WP3 | 自跑抓到**自己的真缺陷**（公开面按 AST 判时只收 `FunctionDef` ⇒ `Verdict` 是 dataclass 被漏掉）⇒ 修成同时收 `ClassDef` | 完成 |
| WP4 | 按压矩阵 **3/3 红**（EC 终态 / 残余登记 / 必备清单），每次 raw `sha256` **逐字节复原** ⇒ 复绿 | 完成 |
| WP5 | 两树实跑 + 两路各自留档 + `cmp`；非空转取证（空树 ⇒ fail-closed） | 完成 |
| WP6 | 记录写入后跑记录面判据 + 独占全量 m0；治理绿；commit + push + CI 到终态 | 完成 |

## 证据

| # | 交付物 / 证据 | 说明 |
| --- | --- | --- |
| E1 | `tools/verify_goal023_closeout.py`（**283 行 / 14 函数**，最长函数 31 行） | 收口验证器；`--root` 参数化、`--verdict-only`；判词行**只有 `PASS` / `FAIL`** 且**不含绝对路径** |
| E2 | `scratch/goal023-ec04-verdict-current.txt` | **当前树**判词留档；raw `sha256` = `8b65f78e…`（33 条判词） |
| E3 | `scratch/goal023-ec04-verdict-clean.txt` | **干净 checkout**判词留档；raw `sha256` = `8b65f78e…`（与 E2 一致是**结论**，不是同一份文件；`cmp` = `IDENTICAL`） |
| E4 | `scratch/goal023-ec04-two-tree.log` | 入口运行记录：两 `TREE` 行 + `COMPARE identical=True` + `TWO-TREE PASS` |
| E5 | `scratch/goal023-ec04-press{1,2,3}.txt` | 三次按压的判词留档（各含 1 条 `FAIL`，逐字点名被按压的事实） |
| E6 | `scratch/goal023-ec04-empty-tree.txt` | 空树取证：`FAIL goal023-standard-assertions-loadable` + `EXIT=2`（**fail-closed**，不假绿） |
| E7 | `scratch/goal023-ec04-m0.log` | as-is 本机 m0 日志（终态行 + 运行时刻晚于记录写入） |
| E8 | `RECHECK-20260928-226`（本目录同批） | 独立收口复检；`verify_paths` 声明**两路** ⇒ 它同时是 EC-02 判据的**第二条真实受判记录**（第一条是 `RECHECK-218`） |
| E9 | `MEM-20260928-160` | 可复用事实：「并集型射程会掩盖必备清单的收缩」—— 只有专门断言清单下界的判据才看得见 |

**两树入口的实跑判词**（两树逐行相同）：

```text
TREE current=D:\research-system exit=0 verdicts=33 sha256=8b65f78ec8dee6205779cda86474e46fa5684d27c3f49ab26ab28bc97d3070aa
TREE clean=D:\research-system-clean-tree exit=0 verdicts=33 sha256=8b65f78ec8dee6205779cda86474e46fa5684d27c3f49ab26ab28bc97d3070aa
COMPARE identical=True
TWO-TREE PASS
```

**按压矩阵**（每项：判词红 1 条 → raw `sha256` 逐字节复原 → 33 条全绿）：

| 按压 | 受判事实 | 判词 | 复原 sha256 |
| --- | --- | --- | --- |
| P1 | GOAL 的 `EC-01` 终态被改回**未完成态**（治理判据把那个占位词判为通过记录里的残留 ⇒ 本表**不复写**该字面量，逐字判词归档在 `scratch/goal023-ec04-press1.txt`） | `FAIL ec04-ec01-to-ec03-are-pass`，detail 逐条列出三条 EC 的现状（`EC-01` 与另两条 `PASS` 对照） | `46654d21…` |
| P2 | GOAL 正文里 `W-12` **两处全删** | `FAIL ec04-residuals-are-registered -> GOAL 正文缺少这些残余登记：['W-12']` | `46654d21…` |
| P3 | 必备清单撤掉本轮验证器 | `FAIL ec02-scope-pins-the-three-scripts -> 必备清单缺少 ['tools/verify_goal023_closeout.py']` | `34d51ec9…` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-28 | IN_PROGRESS | WP1 验证器落地（复用断言集 + 5 组特有断言） |
| 2026-09-28 | IN_PROGRESS | WP3 自跑抓到自己的真缺陷（`ClassDef` 漏判）并修掉；四道门复绿 |
| 2026-09-28 | IN_PROGRESS | WP4 按压 3/3 红 + 逐字节复原；WP5 两树 `TWO-TREE PASS`（33 条，`sha256` 相同） |
| 2026-09-28 | DONE | WP6 记录写入后跑记录面判据 + 独占全量 m0；治理绿；CI 到终态；GOAL-023 置 ACHIEVED |

## 影响报告

- **改动**：新增 `tools/verify_goal023_closeout.py`（**树内**，过四道门）；EC-02 判据的必备清单
  显式加入它；规范页断言集小节点名它为参考实现；GOAL-023 正文登记新增三条残余；
  新增 `.cursor/plans/` 两条记录 + 一条 `MEM-160`；更新 GOAL-023 与 `ALL_PLAN.md`。
- **lint/typecheck/test**：验证器四道门全绿（`ruff format --check` / `ruff check` / 规模 / `mypy`）；
  工具与架构判据套件 **1424 passed**；记录面判据 **24 passed**；全量 m0 **23/23**（见 `RECHECK-226`）。
- **Domain/API/schema 变化**：**无**。
- **安全/凭据变化**：**无**（不碰 token、不碰认证面、不碰 `MIMOSA_*`；本 GOAL 全离线）。
- **兼容性/迁移风险**：**无**（新增一个 `tools/` 脚本 + 记录文本；不改既有判据与门禁）。
- **上游版本影响**：**无**（零依赖改动）。
- **下一项任务**：GOAL-023 收口（状态 → ACHIEVED）。**未覆盖范围原样保留**；
  历史遗留 `tools/` 脚本入射程仍需**另行授权**。
