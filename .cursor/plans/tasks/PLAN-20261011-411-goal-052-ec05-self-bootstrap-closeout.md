---
id: PLAN-20261011-411
slug: goal-052-ec05-self-bootstrap-closeout
title: GOAL-20261011-052 cycle 2/3（EC-05）：自举收口 —— 验证器进树 + 两树 + 归档 + 门链 + 台账；cycle 3 修全量 m0 抓到的架构契约违例
status: DONE
created_at: 2026-10-11
updated_at: 2026-10-11
latest_recheck: .cursor/plans/rechecks/RECHECK-20261011-412-goal-052-ec05-self-bootstrap-closeout.md
memory_entries: []
parent_goal: GOAL-20261011-052
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261011-052 的 **EC-05**（自举收口）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：复用既有收口机器（`tools/closeout_recheck_tools`
    + `tools/closeout_recheck_assertions.standard_verdicts`，**一行未重写**）；
    两处射程**纯收紧**（只增不删）；判词归档**二进制写盘 / `CR=0`**；
    **新判据必须两向实测**（**不得恒假** —— 承 GOAL-051 §8）；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    把 GOAL-20261011-052 收口：① 收口验证器 + 本轮断言集进树并加入 `IN_SCOPE`（纯收紧）
    **与** GOAL-043 立的射程清单；② **两树复检**（`--script-mode shared` + `--base-ref`）
    ⇒ `TWO-TREE PASS` + 判词归档进树；③ as-is m0 **23/23**（在**全部记录写入之后**）、
    治理绿、宪章判据绿；④ CI 台账逐提交；⑤ 承继残余与未覆盖范围逐条在位。
exit_criteria:
  - id: AC-1
    criterion: >-
      **收口面进树**：两个脚本在树且过**四道门**（含规模门）；`IN_SCOPE` **纯收紧**（+2 行）；
      射程分区清单**同步登记**（+1 行）；判词集**逐条**覆盖本 GOAL 的 EC
      （HTTP 披露 / 同源 / 两向四条按压）；**字段读取用 AST**（不按行首正则 ⇒ 不恒假）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_tooling_scripts_meet_product_gates.py
      tests/tooling/test_closeout_verifiers_run_their_own_assertions.py -q` ⇒ 全绿。
    status: PASS
  - id: AC-2
    criterion: >-
      **两树复检**：`tools/two_tree_recheck.py --script tools/verify_goal052_closeout.py
      --script-mode shared --base-ref HEAD` ⇒ **`TWO-TREE PASS`**；判词归档**进树**
      （两份、`CR=0`、与最终一轮同结论）。
    verify: >-
      终局行 `TWO-TREE PASS`；
      `.cursor/plans/goals/evidence/GOAL-20261011-052-verdict-{current,clean}.txt`。
    status: PASS
  - id: AC-3
    criterion: >-
      **记录面自洽**：本 PLAN + `RECHECK-20261011-412` 在位；GOAL 的 EC / 迭代日志 /
      状态历史 / `latest_recheck` / `child_plans` 回写；`ALL_PLAN` 投影一致；
      治理 `validate.py` 绿 + 宪章判据绿。
    verify: >-
      `uv run --frozen --no-sync python -B .cursor/skills/governance-check/scripts/validate.py`
      ⇒ 通过；`tests/tooling/test_mainline_program_is_intact.py` 绿。
    status: PASS
  - id: AC-4
    criterion: >-
      **as-is m0 23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）。
    verify: >-
      终局行 `PASS: profile=m0; 23 deterministic checks`（`PASS [` 24 / `FAILED [` 0）。
    status: PASS
  - id: AC-5
    criterion: >-
      **CI 台账逐提交**（`cancelled` / `failure` 如实登记 + 原因 + `covered_by`；
      空集合 = 未取证；自我指涉边界明写并封闭）。
    verify: >-
      `scratch/poll_ci_all.sh <sha>` 遍历该 sha 全部 run + `/jobs`；台账表见 GOAL 正文。
    status: PASS
---

# PLAN-20261011-411 — GOAL-20261011-052 cycle 2（EC-05 自举收口）

> **主线归属**：`GOAL-20261011-052`（MAINLINE 程序表**序 20**）的 **EC-05**。

## 验收条件

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 收口面进树 + 四道门 + 两处射程纯收紧 | PASS |
| AC-2 | 两树 `TWO-TREE PASS` + 判词归档进树 | PASS |
| AC-3 | 记录面自洽 + 治理 + 宪章判据绿 | PASS |
| AC-4 | as-is m0 **23/23**（记录写完之后） | PASS（cycle 3 独占重跑回填：`PASS [` 24 / `FAILED [` 0 / 5613 passed, 21 skipped） |
| AC-5 | CI 台账逐提交 | PASS |

> **AC-4 / AC-5 的更正过程（如实登记，不抹掉）**：cycle 2 曾把两条标 PASS，但那轮 as-is m0
> **实测为 `FAILED`**（架构契约违例 —— 见上节），CI 台账也尚未产生 ⇒ **属过早**（违规形态：
> 「未实跑不得记 PASS」）。cycle 3 起两条先**回退为待验**（`ALL_PLAN` 投影同步回退），
> **修复 + 独占重跑拿到实测读数之后**才回填 PASS。形态与 `GOAL-20261010-046` 的修复轮一致。

## 实施清单

- [x] WP-1 验证器 + 断言集进树
- [x] WP-2 两处射程纯收紧（`IN_SCOPE` +2 行 / 射程清单 +1 行、下界 21→22）
- [x] WP-3 两树复检（bootstrap 轮 + 终态轮）
- [x] WP-4 判词归档进树（两份 / 二进制写盘 / `CR=0`）
- [x] WP-5 记录面：本 PLAN + `RECHECK-20261011-412` + GOAL 回写 + `ALL_PLAN` + MAINLINE 进展行
- [x] WP-6 治理 + 宪章判据 + as-is m0 + CI 台账

## 证据

| 门 | 读数 |
| --- | --- |
| 收口验证器（本树） | **65 判词 / 0 FAIL**（cycle 3 后；cycle 2 为 63 —— 新增两条同源关系判据） |
| 两树复检 | **`TWO-TREE PASS`**（两路 **65 判词** / `sha256` 相同 `6034fee2f039103f…`）|
| 判词归档 | 两份各 **2483 B / 65 行 / `CR=0` / 0 FAIL**（二进制写盘） |
| 按压归档 | **710 B / `CR=0`**（**基线 GREEN** + `N-1`…`N-4` 全 `RED` + 复原一致） |
| 两处射程 | `IN_SCOPE` **+2 行**；射程分区清单 **+1 行**（下界 21→22）—— 均**纯收紧** |
| 治理 | `validate.py` 通过 |
| 宪章判据 | `test_mainline_program_is_intact.py` 绿 |
| **as-is m0** | **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` **24** / `FAILED [` **0** / **5613 passed, 21 skipped** / `EXIT=0`；**独占**、仓库 `.venv`、不接管道、**在全部记录写完之后**）；日志 `scratch/m0-goal052-c3.log` |

> **m0 条数 = 23**（终局行逐字）；`PASS [` 行数 **24** = 23 + `release-assets-immutable`（在计数之外）。
> **passed 读数差（cycle 2 **5610** → cycle 3 **5613**，+3）的逐条归因**：①
> 架构契约违例修复后 `tests/architecture` 的 **2 条失败转为通过**（+2）；② 新增产品文件
> `packages/application/memory/disposition.py` 进入 `tests/tooling/test_python_source_limits.py`
> 的**参数化面**（`PRODUCT_ROOTS` 含 `packages`，每个 `.py` 一个用例）（+1）。**无**其他计数来源。

### 本轮全量 m0 **真红**（架构契约违例，已修 —— 如实登记）

**逐字**：`FAILED tests/architecture/python/test_services_api_boundaries.py::
test_control_plane_api_has_no_adapter_leak_outside_composition` ——
`services.api.routers is not allowed to import adapters: services.api.routers.memory -> adapters (l.27)`。

**成因**：EC-03 要求「两处**同源**」，我第一版把共用判定留在**适配器**里
（`adapters/canonical/memory_read.py`）由路由**调用** —— 那**直接违反** `.importlinter.api`
的契约：控制面 API **不得** import 具体适配器（组合根除外）。
**为什么本地四道门没抓到**：`ruff` / `format` / `mypy` / 规模门都**不做分层判定**；
分层由 `import-linter` 判，而它只在 **m0 / CI** 里跑（本地直连 `.venv/Scripts/python.exe`
还会因 `lint-imports` 不在 PATH 而**假红** —— 必须 `uv run`）。

**修法（正确的同源落点）**：把共用判定搬去**应用层**
`packages/application/memory/disposition.py` —— 那是**两个读面都能 import 的那一层**
（HTTP 面本来就在 import `packages.application.memory.*`）。`memory_read` **显式再导出**
（严格 mypy 要求 `__all__`，否则 `attr-defined` 判红）⇒ 既有调用方与判据不受影响，
**判定实现一字未动**。

**连带**：四个既有收口断言集（`goal042` / `045` / `050` / `051`）把读面的**位置**
写死（`READ_FACE = "adapters/canonical/memory_read.py"`）⇒ 搬迁后**假红**
（被「零判负」判据当场报出）。四处均改为**「可能落点的合并文本」**
（`*_FACE_SOURCES`，含 `disposition.py`）—— **判关系不判位置**（承 `MEM-20261010-215`）；
`goal045` 的那条还额外接受**封装形态**（`disposition_reason` 把拼接收进应用层）。

### 本轮把 §8 的新增纪律（**判据不得恒假**）落成了机械面（如实登记）

| # | 措施 | 读数 |
| --- | --- | --- |
| 1 | **字段读取改用 AST**（读 `MemoryRecordDto` 类体的 `AnnAssign` 目标） | **不**按行首正则（那会随缩进/换行静默失配 ⇒ **可能恒假**）|
| 2 | **非空性实测**（真树 / 空源码 / 合成缺字段三条） | 真树 **17 字段**（13 既有 + 4 新增）；空源码 ⇒ **空集**；合成无该字段 ⇒ **读不到** ⇒ 判据**不恒真** |
| 3 | **反证脚本带基线门** | 基线（未按压）必须 **GREEN**、每条按压必须 **RED**，否则**非 0 退出** —— cycle 1 正是靠它抓到 `N-4` 的**假反证臂** |

### cycle 3（修复轮）：修完全量 m0 的**真红**后，把判据面的**同源关系**补成机械面

修复轮的两件事分列（前者是被 m0 抓到的真缺陷，后者是修复**顺带暴露**的判据面缺口）：

**① 真缺陷已修**（详见上节）：判定搬去应用层 ⇒ `import-linter` 恢复 `2 kept, 0 broken`。
`uv run --frozen --no-sync python -B -m pytest tests/architecture -q` ⇒ **287 passed**
（本地直连 `.venv/Scripts/python.exe` 会因 `lint-imports` 不在 PATH 而**假红 14 条** —— 承既有教训）。

**② 判据面缺口（本次自查补上，如实登记）**：搬迁后我把四处既有断言从**钉位置**
改成**「可能落点的合并文本」**。那个改法**能把假红治好，但也**开了一个口子** ——
标记只要**出现在合并文本里的任一处**即判绿：若编排读面**不再**从单一来源取判定
（自己另写一套），合并文本里仍会有那些标记（它们还在应用层模块里）⇒ **判据不响**。
这正是本 GOAL §8 「判据不得恒假 / 必须两向实测」针对的形态，**当场补两条关系判据**：

| 新增判据 | 判什么**关系**（不是位置、不是文本巧合） | 读数 |
| --- | --- | --- |
| `ec03-both-faces-take-the-judgement-from-the-one-source` | 用 **AST** 读两个读面的 `ImportFrom`：两者都**必须**从同一模块 import 那三个名字 | 真树 **PASS**（router 3/3、编排面 3/3）|
| `ec03-neither-face-redefines-a-second-copy` | 用 **AST** 读模块级 `FunctionDef`：两个读面**都不得自己定义**那三个名字（只能引用 / 再导出）| 真树 **PASS**（router 0 处、编排面 0 处）|
| `ec03-the-judgement-lives-in-the-application-layer`（改写：文本口径 ⇒ **AST 口径**）| 那三个名字**由应用层模块定义**（原版判 `"def X(" in text` —— **按写法判**，`async def` / 换行即失配）| 真树 **PASS** |

**两向实测**（每条都实测会响；承 §8，**不得**只声明判了关系）：

| 实测面 | `judgement-lives-…` | `both-faces-…one-source` | `neither-…redefines` |
| --- | --- | --- | --- |
| 真树（必须绿） | PASS | PASS | PASS |
| 合成缺陷：路由**自己定义**一套 | PASS（判定确实还在应用层 —— 该条不管这件事）| **FAIL** ✓ | **FAIL** ✓ |
| 合成缺陷：编排读面**不再**从单一来源取 | PASS | **FAIL** ✓ | PASS（它没定义，只是不取）|
| 合成缺陷：应用层模块**变空** | **FAIL** ✓ | PASS | PASS |
| 空源码 / 取错模块 / 缩进内定义 | — | 空 ⇒ `set()`；取错模块 ⇒ 不命中 | 缩进内 ⇒ 不算模块级 |

**这张表要读出的两件事（都是实测，不是推断）**：

1. **三条判据互补、无一条冗余**：每条**只在**它负责的那一面响 —— 应用层变空 ⇒ 只有
   `judgement-lives-…` 响；路由自写一套 ⇒ 只有「取」和「不重定义」两条响；
   编排面不取 ⇒ 只有「取」响。
2. **`both-faces-…` 的射程边界（如实登记）**：应用层模块**变空**时它**不响** ——
   因为它判的是**两个读面的 import 语句指向同一模块**，而语句**仍在**。
   「模块里到底有没有那三个定义」由 `judgement-lives-…` 负责。
   两条**必须同时在**才盖住这件事；任何一条单看都有盲区。**不**假装单条足够。

**③ 连带（两处既有断言随搬迁重测）**：`goal042` / `045` / `050` / `051` 的四处钉位置断言已改判关系
（详见下节申报）；**五个收口验证器全 0 FAIL**（`goal042: 64` / `goal045: 64` / `goal050: 66` /
`goal051: 68` / `goal052: 65`）。

### cycle 3 的**改既有判据申报**（承 `MEM-20261009-210`，逐条自证）

`git diff --numstat 39ba0eb~1 39ba0eb -- tools/` 读数（删除行 = 第二列）：

| 文件 | +/- | 改了什么 | 谓词比对 | 属同轮同步集？ |
| --- | --- | --- | --- | --- |
| `tools/goal042_closeout_assertions.py` | +25 / -6 | 4 条从**单文件文本**改判**可能落点合并文本** | **等价偏强**：原判「标记在该文件」⇒ 今判「标记在两个可能落点之一」；标记不存在仍判红（两向实测见下）| **否** ⇒ 本表如实登记（命中 `escalation_triggers` 第 5 条形态 ⇒ 已在 RECHECK 登记）|
| `tools/goal045_closeout_assertions.py` | +44 / -7 | 同上 + 1 条接受**封装形态**（形态 B）| **等价**：形态 B 只有在该助手**确实**把冲突点名拼进理由时才成立 —— 由 `_appends_conflict_note` 在模块文本上**另判一次**（该步仍在）| **否** ⇒ 同上 |
| `tools/goal050_closeout_assertions.py` | +16 / -3 | 2 条同上 | **等价偏强** | **否** ⇒ 同上 |
| `tools/goal051_closeout_assertions.py` | +32 / -4 | 2 条同上 + 两条助手抽出为命名函数 | **等价**（同一件事；抽出只为规模门）| **否** ⇒ 同上 |
| `tools/goal052_closeout_assertions.py` | 见末轮 | 1 条文本口径 ⇒ **AST 口径**；**新增 2 条**同源关系判据；`SHARED_HELPERS` 里助手名随搬迁更新 | 该文件是**本 GOAL 新写**的（非既有判据）；两条新增已两向实测 | 不适用（属本轮**新增**面）|

**收窄受判面？** **无一处收窄**；两处（`goal042` / `goal045` / `goal050` / `goal051`）实际是**放宽**了
判「标记在哪」，但那**不是**放宽判据强度 —— 它正是**「判关系不判位置」**（`MEM-20261010-215`）的形态：
把「位置」当受判对象本身就是**假红源**（GOAL-052 连续踩到）。**同时**补了两条**只判关系**的判据
把「同源」这件事**判得更紧**（见上表②）。**未**放宽任何断言、**未**改任何阈值。

## 影响报告

- **Domain / API / schema 变化**：零（本轮只新增 `tools/` 机械面与记录）。
- **安全 / 凭据变化**：无。**兼容性 / 迁移风险**：无。**上游版本影响**：无。
- **下一项任务**：GOAL 收口。

## 无可复用事实

cycle 3 的可复用做法：**「判关系不判位置」的修法本身会开口子** —— 把「钉一个落点」改成
「合并多个可能落点」能治假红，但若**不再另判「这些落点确实被用上」**，判据会**静默变松**；
正确形态是**两条并行**：①「标记在合并面里」+ ②「关系取自同一来源」。后者必须用 **AST**
（`ImportFrom` / 模块级 `FunctionDef`）读，**不**按写法判。

## CI 台账（逐提交）

| commit | run/结论 | 备注 |
| --- | --- | --- |
| `2a3ca6c`（cycle 1 实现） | 见 GOAL 正文台账 | 四样补齐 + 同源 + 快照同轮 |
| `f526fcc`（cycle 1 记录面） | 见 GOAL 正文台账 | PLAN-409 + RECHECK-410 + GOAL 回写 |
| `de6f6a1` / `c0826bd` / `05c6e06`（EC-05 首轮 + 两轮归档） | 见 GOAL 正文台账 | 验证器 + 两处射程 + 归档定格 |
| （收口提交） | 见 GOAL 正文台账 | 本 PLAN + RECHECK + GOAL 回写 + 宪章进展行 |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-11 | IN_PROGRESS | 验证器 + 断言集进树；两处射程纯收紧；bootstrap 轮时序登记。 |
| 2026-10-11 | IN_PROGRESS | 两树 `TWO-TREE PASS`；归档定格；`RECHECK-20261011-412` 独立复检。**m0 这一路当时未回读 ⇒ AC-4 的 PASS 属过早**（实测为 FAILED）。 |
| 2026-10-11 | IN_PROGRESS | **cycle 3 修复轮**：架构契约违例修复（判定搬去应用层）+ 四处既有断言改判关系 + 两条同源 AST 判据；两树重跑（67 判词）；AC-4 / AC-5 **回退为待验**（收口依据更正）。 |
| 2026-10-11 | DONE | as-is m0 **23/23** 实测回填（`PASS [` 24 / `FAILED [` 0 / 5613 passed, 21 skipped）+ CI 台账逐提交；`RECHECK-20261011-412` 独立复检。 |
