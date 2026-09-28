---
id: RECHECK-20260928-226
slug: goal-023-closeout-recheck
title: GOAL-023 收口复检：验证器进树并自举两树（33 条判词 sha256 相同）+ 按压 3/3 红与逐字节复原 + 残余与未覆盖范围逐条
plan_id: PLAN-20260928-225
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-28
completed_at: 2026-09-28
verify_paths:
  - path: 当前树（主干工作树，`D:/research-system`）
    evidence: scratch/goal023-ec04-verdict-current.txt
  - path: 干净 checkout（`git worktree add --detach` @ `b5a83b5`，落点 `D:/research-system-clean-tree`，用后由入口移除）
    evidence: scratch/goal023-ec04-verdict-clean.txt
owners:
  - root-agent
---

# RECHECK-20260928-226 — GOAL-023 收口复检

**复检口径**：不复用任何 PLAN / GOAL 的叙述；每项给出**可复核观察面**。**未实跑的不记通过**。
本轮最要紧的一件事是**换掉了收口复检的载体**：GOAL-022 的断言集在 gitignored 的 `scratch/`（不可归档），
本 GOAL 的断言集与**本轮收口验证器**都在**树内**，且验证器**自己**过产品同款的四道门。

## 检查结果

### 一、交付面（EC-01 / EC-02 / EC-03 / EC-04 各自可判）

| 交付物 | 观察面 | 结论 |
| --- | --- | --- |
| `tools/closeout_recheck_assertions.py`（**388 行 / 18 条公共判词**） | 在树；按 **AST** 声明 `Verdict` / `standard_verdicts` / `emit` | 成立 |
| `tests/tooling/test_closeout_assertions_are_in_tree.py`（6 例） | 在树；空树 ≥ 5 红（不空转） | 成立 |
| `tests/tooling/test_tooling_scripts_meet_product_gates.py`（8 例） | 必备清单 **3** 条 + 规范页点名 **2** 条（并集去重）；遗留 **37** 条逐条带理由 | 成立 |
| `tests/architecture/python/test_recheck_scope_boundary_is_mechanical.py`（6 例） | 受判起点 `2026-09-28`、射程外**恰好四条**、两向反证 | 成立 |
| `tools/verify_goal023_closeout.py`（**283 行 / 14 函数**，最长 **31** 行） | 本轮收口验证器；`--root` / `--verdict-only`；纯 + 路径无关 | 成立 |
| 规范页 `docs/architecture/RECHECK_SCRIPT_CONVENTIONS.md` | 断言集小节点名断言集与**本轮验证器**；`docs/INDEX.md` 已登记 | 成立 |

**验证器**复用**标准断言集**（`standard_verdicts` / `emit` / `Verdict`），
本文件只复核它**特有**的那 15 条断言（`ec01-*` 3 / `ec02-*` 4 / `ec03-*` 3 / `ec04-*` 5）——
这正是 EC-01 想要的形态：「**未来的收口复检只写自己特有的断言**」。

### 二、两树实跑（EC-04 ①，**自举**）

用 EC-01 的入口跑本轮验证器，**同一份脚本字节**（`--script-mode tree`：两棵树各取自己
checkout 里的同一份文件）：

```text
TREE current=D:\research-system exit=0 verdicts=33 sha256=8b65f78ec8dee6205779cda86474e46fa5684d27c3f49ab26ab28bc97d3070aa
TREE clean=D:\research-system-clean-tree exit=0 verdicts=33 sha256=8b65f78ec8dee6205779cda86474e46fa5684d27c3f49ab26ab28bc97d3070aa
COMPARE identical=True
TWO-TREE PASS
```

- 两路判词**各自留档**：`scratch/goal023-ec04-verdict-current.txt` 与
  `scratch/goal023-ec04-verdict-clean.txt`；raw `sha256` **两者同为** `8b65f78e…`；
  `cmp` = `IDENTICAL`（**不是**同一份文件，两份文件各自落盘）。
- 入口退出码 **0**；运行记录 `scratch/goal023-ec04-two-tree.log`。
- 干净 checkout 由入口 `git worktree add --detach @ b5a83b5` 建立、**用后自行移除** ⇒
  复核 `git worktree list` 只剩工作树与三条**历史遗留** worktree（属 GOAL-013/015/018，
  **不在本 GOAL 范围、原样保留**）；`ls -d ../*-clean-tree` **无残留**。

### 三、按压矩阵（**先红后绿**，每次 raw `sha256` 逐字节复原）

| # | 按压 | 实测判词 | 复原 |
| --- | --- | --- | --- |
| P1 | GOAL 的 `EC-01` 终态改回**未完成态**（治理判据把那个占位词判为通过记录里的残留 ⇒ 本表**不复写**该字面量；逐字判词归档 `scratch/goal023-ec04-press1.txt`） | `EXIT=1`、`32 PASS / 1 FAIL`：`FAIL ec04-ec01-to-ec03-are-pass`，detail **点名 `EC-01`** 并与另两条 `PASS` 对照 | 复原后 `sha256` = `46654d21…`，`git diff` **空** |
| P2 | GOAL 正文里 `W-12` **两处全删**（承 MEM-157：谓词是「存在」，按压必须让所有出现消失） | `EXIT=1`、`32 PASS / 1 FAIL`：`FAIL ec04-residuals-are-registered -> GOAL 正文缺少这些残余登记：['W-12']` | 复原后 `sha256` = `46654d21…`，`git diff` **空** |
| P3 | 必备清单撤掉本轮验证器 | `EXIT=1`、`32 PASS / 1 FAIL`：`FAIL ec02-scope-pins-the-three-scripts -> 必备清单缺少 ['tools/verify_goal023_closeout.py']` | 复原后 `sha256` = `34d51ec9…`，`git diff` **空** |

三次按压后未按压态复跑 **33/33 PASS**、`EXIT=0`。判词留档 `scratch/goal023-ec04-press{1,2,3}.txt`。

**非空转取证**：空树（`mktemp -d`）⇒ `FAIL goal023-standard-assertions-loadable` + `EXIT=2`
（**fail-closed**：拿不到标准断言集就拒绝服务，而不是「没断言就算绿」；留档
`scratch/goal023-ec04-empty-tree.txt`）。**分界如实登记**：这一跑**不**等价于「15 条特有断言
在空树上各自判红」——那些断言的**非空转**证据由上面三次按压承担。

### 四、验证器自己的四道门（EC-02 的**首个真实受判对象**延伸）

`tools/verify_goal023_closeout.py` 是本轮**新增的受判对象**，逐门实测（判据的同一份实现）：

| 门 | 结果 |
| --- | --- |
| `ruff format --check` | **clean**（首版被自己的门判红 **2 处**：`factory(...)` 长行与列表化 → 已按 `ruff format` 重排） |
| `ruff check` | **passed**（首版 2 条 `line-too-long (101 > 100)` → 已修） |
| 规模（函数 ≤ 50 / 文件 ≤ 450） | **通过**（283 行；最长函数 31 行） |
| `mypy`（既有 `strict`） | **Success: no issues found** |

**自跑抓到自己的一个真缺陷（在提交前）**：验证器把「公开面」按 AST 判时**只收 `FunctionDef`**，
而 `Verdict` 是 `@dataclass`（`ClassDef`）⇒ 它对 `tools/closeout_recheck_assertions.py`
**判红**（`断言集缺失或公开面不全：['Verdict']`）。修法 = 同时收 `ClassDef`（与既有判据
`test_closeout_assertions_are_in_tree.py` 同口径）⇒ 复跑 **33/33 PASS**。
**这是「先红后绿」的第五处真实证据，且红来自新工具对自己队友的断言**，不是造的。

### 五、承继残余逐条在位（EC-04 ⑤）+ **新增三条**（EC-04 ⑦）

承继 12 个 ID 逐条在位（`R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` /
`W-4` / `W-5` / `W-6` / `W-10` / `W-11` / `W-12`），由验证器的
`ec04-residuals-are-registered` **机械**断言（`W-12` 的按压 P2 证明它真的在判）。

**新增三条**（GOAL-023 正文，逐条可复核）：

| 残余 | 内容 | 为什么它不是待办 |
| --- | --- | --- |
| 新增① | 历史遗留 `tools/` 脚本**仍不受任何判据覆盖**（37 条只在清单 + 理由里） | 纳入射程 = 逼改历史资产（既有 73 条 lint 错误 / 10 个待重排文件）⇒ **需另行授权** |
| 新增② | 射程外四条历史收口复检**仍不可回填** | 它们是**不可变证据**；回填等于改写历史 ⇒ 只登记，不做 |
| 新增③ | 断言集**可复跑性 ≠ 跨平台复验** | 本机只在 Windows 实跑过；别平台差异不在本轮证据内 |

### 六、未覆盖范围逐条明写（EC-04 ⑥）

- **读面未认证**（`/health` 等 GET 面按设计**不加认证** ⇒ 本轮**不含**读面授权结论）；
- **多租户 / RBAC / organization scope 未做**；
- **BOLA / BFLA 一个都没做**（`W-11` 原样保留）；
- **部署面未验证**（反代 / TLS / 多副本，`W-12` 原样保留）；
- **`R-M1` 未收口**（Mimosa 钩子侧 `scanner_enobufs` 未得完整结论）
  ⇒ **不得**据此宣称项目安全；**有机器门 ≠ 项目安全**。

### 七、零改动面（**受保护对象逐个核对**）

- 十个受保护判据自 `6bf3c9c`（建档）起**逐字节未改**：由标准断言集的
  `protected-judges-present` **机械**断言（它是 18 条公共判词之一，本轮两树实跑里同样全绿）；
- `tools/verify_goal023_closeout.py` **不修改**任何既有判据；EC-02 判据的改动只有
  **必备清单加一条 + docstring 一行**（**收紧**射程，不是放宽）；
- `PRODUCT_ROOTS` 未改、m0 条数仍 **23**（公共判词 `runner-product-roots-unchanged` /
  `scale-judge-product-roots-unchanged` / `m0-check-count-stable` 三面各判一次，
  `m0` 条数由**门运行器自己算出**而非字面量）；
- `.github/workflows/**` 未改、零依赖改动、零产品代码改动；
- **零历史回填**：`git status --short .cursor/plans/` 在收口后**只**含本轮新增/更新的记录。

### 八、as-is 本机 m0（**记录写入之后**，承 MEM-145）

**顺序纪律**：记录先落盘 ⇒ 记录面判据 ⇒ **独占**跑全量 m0（仓库 `.venv` + DSN 固化 +
Makefile 的 `--keep-going`，跑门期间**不改工作树**），跑完 `tasklist` 确认 python 进程 **0**。
**实测的终态行与日志时刻**（`scratch/goal023-ec04-m0.log`）在**紧随其后的补记提交**里逐字追加
—— 本行**不预先声明**未跑出的结论（承「未实跑不得记 PASS」）。

### 九、本次复检**未**复核的面（如实登记）

- **未**跨平台复验（本机只有 Windows；「两树同结论」是**本机**结论）；
- **未**复核射程内记录的**实质质量**（EC-03 判据只判**边界**，本文件也不改这一点）；
- **未**验证断言集的**完备性**（它只覆盖它列出的那些公共事实）；
- **未**做任何真实出网 / 部署面验证（本 GOAL 全离线）；
- **未**在任何一步宣称项目安全（`R-M1` 仍在）。

## 结论

**GOAL-023 的 EC-01…EC-04 全部 PASS，四条各有实跑证据；本复检结论 = `PASS_WITH_WARNINGS`。**

**收口判词七项逐条成立**（GOAL 前置要求）：

1. **断言集进树与两树实跑证据**：断言集 `tools/closeout_recheck_assertions.py`（388 行）在树；
   本轮验证器**复用它**并在两树上跑出 **33 条判词逐行相同**、`sha256` **同为** `8b65f78e…`、
   两路各自留档且 `cmp` 一致、`TWO-TREE PASS` / `EXIT=0`。**这条正是 GOAL-022 `W-3`
   （「断言集在 `scratch/`，不可归档」）的正面收口**。
2. **EC-02 的首个真实受判对象（入口自身的红）与修复证据**：受判面开门第一件就是
   `tools/two_tree_recheck.py` 自己的红 —— `main` **53 行 > 50**、`ruff check`
   `complex-structure: main is too complex (14 > 10)`；重构为 5 个助手 ⇒ `main` **21 行**、
   `ruff check` **passed**，且既有 **11 例行为判据一字未改、全绿**（cycle 2 实测；本轮读取面复核）。
3. **按压与逐字节复原记录**：本轮**三次**按压（P1 / P2 / P3，见第三节）各自 `EXIT=1` + 1 条
   `FAIL` 逐字点名被按压的事实，raw `sha256` 复原（`46654d21…` / `34d51ec9…`）后
   `git diff` **空**、**33/33** 复绿。
4. **受判射程边界（起点 + 四条 + 计数）**：起点 `2026-09-28`、射程外**恰好四条**
   （`goal-018` / `019` / `020` / `021-closeout-recheck`）、射程内计数 ≥ 1 且两集互斥 ——
   由 EC-03 判据**机械**断言（本轮新增本记录后，射程内**1 → 2**：`RECHECK-218` + 本记录）。
5. **as-is 本机 m0 的终态行**：**在记录写入之后**独占跑；实测终态行与日志时刻见补记（第八节）。
6. **未覆盖范围**：第六节逐条明写。
7. **新增残余登记**：第五节三条逐条登记。

**同时如实登记五条警告**：

- **`W-1`（最要紧）并集型射程会掩盖「必备清单」的收缩**：射程 = 必备清单 **∪** 规范页点名。
  实测按压 P3 时，验证器判红，**EC-02 判据自己仍然 `8 passed`** —— 因为该脚本**也被规范页点名**，
  并集把它留住了。「必备清单不得收缩」**只有**验证器那条断言看得见。⇒ 两处**必须**同步维护
  （已沉淀 `MEM-20260928-160`）。
- **`W-2` 收口验证器是「薄壳」**：拿不到标准断言集时它**短路**（单条 `FAIL` + `EXIT=2`），
  「15 条特有断言在空树上各自判红」**没有**被证明；非空转靠按压矩阵（第三节）。
- **`W-3` 两树比的是**同 tip**（`--base-ref HEAD` = `b5a83b5`）：它证明「结论不依赖工作树里
  未提交的残留」（当前树带着 4 个**与本 GOAL 无关的**并发改动，判词仍逐行相同），
  **不**证明跨提交 / 跨平台。EC-01(e) 的跨提交形态实测只作**登记**，**不是**一致性保证。
- **`W-4` 残留面原样**：37 个历史 `tools/` 脚本仍无机器门；四条历史收口复检仍在射程外 ——
  「本仓所有收口复检都被判据覆盖」「`tools/` 已被门覆盖」**两句都不成立**。
- **`W-5` 本轮不含任何授权面 / 认证面新结论**：`W-10` / `W-11` / `W-12` / `R-M1`
  **原样保留**；**不得**宣称项目安全。
