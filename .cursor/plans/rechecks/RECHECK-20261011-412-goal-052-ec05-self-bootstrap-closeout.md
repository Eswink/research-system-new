---
id: RECHECK-20261011-412
slug: goal-052-ec05-self-bootstrap-closeout
title: 独立复检：GOAL-20261011-052 EC-05 自举收口（验证器 / 两树 / 归档 / 门链 / §8 纪律落地）
plan_id: PLAN-20261011-411
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-11
completed_at: 2026-10-11
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（含 cycle 1/2 全部交付与记录）
    evidence: .cursor/plans/goals/evidence/GOAL-20261011-052-verdict-current.txt
  - path: 干净 checkout（`git worktree add --detach HEAD`，同一份断言集）
    evidence: .cursor/plans/goals/evidence/GOAL-20261011-052-verdict-clean.txt
---

# RECHECK-20261011-412 — GOAL-20261011-052 EC-05 自举收口 独立复检

复检对象：`PLAN-20261011-411`。独立重跑下列机械面，不引用 PLAN 结论当证据。
**`verify_paths` 声明：2 路**（本树 + `--base-ref` 的干净 checkout，同一份断言集）。

## 检查结果

### 1. 收口面进树与四道门（AC-1，独立重跑）

| 检查 | 读数 |
| --- | --- |
| 两个脚本在树 | `tools/verify_goal052_closeout.py` / `tools/goal052_closeout_assertions.py` |
| `ruff check` / `ruff format --check` | 全绿 |
| `mypy`（strict） | Success: no issues found |
| 规模门 | 文件 ≤ 450 行、函数 ≤ 50 行（全绿） |
| `IN_SCOPE` **纯收紧** | `+2` 行；判据全绿 |
| 射程分区清单（GOAL-043 立）**同步登记** | `+1` 行 + 下界 21→22；判据全绿 |

**判词集覆盖本 GOAL 的 EC（逐条）**：`ec02-*`（四样在场 / **既有 13 字段一个不改名** /
四处形态 / `validity` 不猜）· `ec03-*`（三个助手都在路由里被调用 / 反向链接**按同一批扫一次** /
**同源关系三条**（判定在应用层 / 两个读面都从同一来源取 / 无一面自写第二套）/ 快照含四样）·
`ec04-*`（四条用例逐条点名 + **基线门** + 四按压全红与复原一致）。

**cycle 3 补充的两条**（`ec03-both-faces-take-the-judgement-from-the-one-source` /
`ec03-neither-face-redefines-a-second-copy`）：用 **AST** 读 import 与模块级定义
—— 补的是「判关系不判位置」修法**自身**开的口子（合并文本能治假红，但标记在任一处即绿 ⇒
「编排面不再取单一来源」会漏判）。**独立两向实测**：真树三条全绿；合成「路由自写一套」⇒ 两条红；
合成「编排面不取」⇒ 一条红；合成「应用层变空」⇒ **另一条**红 —— **三条互补、无一条冗余**。

### 2. 两树复检与归档（AC-2，独立重跑）

**bootstrap 轮**：两份归档 missing（归档由本次调用写出、尚在提交之前）⇒ `TWO-TREE RED`；
两路 `COMPARE identical=True`（差异**只**在归档项）。**终态轮**（`--base-ref HEAD`）：
终局行 **`TWO-TREE PASS`**。**cycle 3 后重跑**（修复架构契约违例改动了受判文件 ⇒ 必须重跑）：
两路 **67 判词**、`sha256` 相同 `3cbe00f5633feb63057f776ddf13650e285d7137ef5d484907c11776f2889e27`。
归档两份各 **2590 B / 67 行 / `CR=0` / 0 FAIL**（二进制写盘）。

### 3. §8 新增纪律（**判据不得恒假**）的落地复核

| # | 措施 | 独立读数 |
| --- | --- | --- |
| 3.1 | **字段读取用 AST**（`MemoryRecordDto` 类体的 `AnnAssign` 目标） | 真树 **17 字段** = 13 既有 + 4 新增 |
| 3.2 | **非空性三条实测** | 空源码 ⇒ **空集**；合成只含 `id` 的 DTO ⇒ **只读到 `id`**；真树 ⇒ 17 ⇒ 判据**不恒真/不恒假** |
| 3.3 | **反证脚本的基线门**（未按压必须绿） | cycle 1 正是靠它抓到 `N-4` 的**假反证臂**（受判面区分不了两件事）⇒ 已换受判面 |
| 3.4 | 归档含**基线行** | `GOAL-20261011-052-press-two-way.txt` 首行为 `BASELINE…: GREEN` |

### 4. 门链与记录面（AC-3，独立重跑）

`validate.py` 通过；`test_mainline_program_is_intact.py` 绿（本 GOAL 的 id 已在程序表**序 20**）；
**cycle 3 后重跑**：`tests/architecture`（经 `uv run`）**287 passed**（分层契约
`2 kept, 0 broken`）；定向套件 `tests/{application,api,e2e,domain,adapters,postgres,contracts,tooling}`
**4780 passed, 196 skipped**。**as-is m0**：`PASS: profile=m0; 23 deterministic checks`
（`PASS [` 24 / `FAILED [` 0 / passed/skipped 读数**待全量 m0 实测回填**；在全部记录写完之后、
独占、仓库 `.venv`、不接管道）。

### 4b. cycle 3 的**真缺陷**（全量 m0 抓到，已修 —— 独立复核）

**逐字**：`services.api.routers is not allowed to import adapters:
services.api.routers.memory -> adapters (l.27)`（`.importlinter.api` 的
「控制面 API 不得 import 具体适配器」契约）。**成因**：EC-03 的「两处同源」第一版把共用判定
留在**适配器**里由路由调用。**本地四道门**（`ruff` / `format` / `mypy` / 规模门）
**不做分层判定** ⇒ 只被 **m0 / CI** 抓到。**修法**：判定搬去
`packages/application/memory/disposition.py`（两个读面都能 import 的那一层），
`memory_read` **显式再导出**（严格 mypy 要求 `__all__`）—— **判定实现一字未动**。
**独立复核**：`uv run --frozen --no-sync python -B -m pytest tests/architecture -q` ⇒ **287 passed**。

### 4c. cycle 3 的**判据面缺口**（自查补上 —— 独立复核）

四处既有断言（`goal042` / `045` / `050` / `051`）从**钉位置**改成**合并文本**后，
判据**不再能发现「编排读面不再取单一来源」**（标记仍留在应用层模块里 ⇒ 合并文本仍命中）。
这是**修法自身开的口子**，属 GOAL-052 §8 「判据不得恒假」针对的形态。
**补法**：新增两条 **AST** 判据（判 import 的**指向**、判模块级**是否自写第二套**）。
**独立两向实测读数**（复跑合成缺陷面）：

| 合成面 | 判定在应用层 | 两处同取一源 | 无一面自写 |
| --- | --- | --- | --- |
| 真树 | PASS | PASS | PASS |
| 路由自写一套 | PASS | **FAIL** | **FAIL** |
| 编排面不再取 | PASS | **FAIL** | PASS |
| 应用层变空 | **FAIL** | PASS | PASS |

### 5. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | 改动 | 谓词比对 | 删除行 |
| --- | --- | --- | --- |
| `tests/tooling/test_tooling_scripts_meet_product_gates.py` | `IN_SCOPE` **+2 行** | **纯收紧**（只加） | **0** |
| `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` | 射程清单 **+1 行** + 下界 21→22 | **纯收紧** | **0** |
| `tools/goal050_closeout_assertions.py`（cycle 1） | 钉助手**名字** ⇒ 改判**关系** | **等价**（同一件事：存在「把 `supersedes` 汇总成反向表」的助手；**两种名字都过**、助手不存在则红 —— 已两向实测）| 仅原比对式 |
| `tools/goal042_closeout_assertions.py`（cycle 3） | 4 条：单文件文本 ⇒ **可能落点合并文本** | **等价偏强**（标记不存在仍判红；已两向实测）| 6 |
| `tools/goal045_closeout_assertions.py`（cycle 3） | 同上 + 1 条接受**封装形态**（形态 B）| **等价**（形态 B 仍由 `_appends_conflict_note` 在模块文本上**另判一次**）| 7 |
| `tools/goal050_closeout_assertions.py`（cycle 3） | 2 条同上 | **等价偏强** | 3 |
| `tools/goal051_closeout_assertions.py`（cycle 3） | 2 条同上 + 两条助手抽为命名函数 | **等价**（抽出只为规模门）| 4 |

> 删除行读数取自 `git diff --numstat 39ba0eb~1 39ba0eb -- tools/`。
> **这四处命中 `escalation_triggers` 第 5 条形态**（改同轮同步集以外的既有判据断言）⇒ **在此如实登记**；
> 触发原因 = **架构契约修复的必然后果**（判定搬迁 ⇒ 钉位置的断言会**假红**），
> 修法是 **`MEM-20261010-215`「判关系不判位置」** 的形态，并**同时**补两条只判关系的判据
> 把「同源」判得**更紧**（见 §4c）。

**收窄受判面？** **无一处收窄**；四处是**放宽了「标记在哪」**（不是放宽判据强度 ——
「位置」本身是**假红源**），**同时**新增两条关系判据补偿（并已两向实测无冗余）。
**未**改任何阈值、**未**放宽任何既有断言。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-5 逐条独立成立：收口面进树且过四道门、
两树 `TWO-TREE PASS`（cycle 3 后重跑：67 判词 / `sha256` 相同）、归档与最终一轮同结论、
治理与宪章判据绿、`tests/architecture` 287 例绿（分层契约恢复 `0 broken`）、定向套件 4780 例绿、
CI 台账逐提交；且 §8 的新增纪律（**判据不得恒假**）**落成了机械面**（AST 读字段 +
三条非空性实测 + 反证脚本基线门 + cycle 3 补的两条同源关系判据）。

### Warnings

- **W-1（HTTP 面的时点判定不在本轮；承 `DD-1`）**：HTTP 面**仍不**做「按时点判时效」。
- **W-2（其他读面未普查；承 `DD-2`）**：本轮对齐的是**记忆**的两个读面；**别的实体**是否有同类
  差集**未普查** —— 这是本 GOAL 登记的**最实的一条**后续候选。
- **W-3（一致性判据只在记忆面；承 `DD-3`）**：**未**做全仓通用的一致性判据。
- **W-4（cycle 1 的两处如实登记，均已修）**：① **假反证臂**（`N-4` 受判面区分不了两件事 ——
  「有断言」≠「断言在下判断」）；② `goal050` 钉助手**名字** ⇒ 改名公开后假红 ⇒ 改判**关系**。
- **W-5（`superseded_by_index` 改名公开，承 cycle 1 的 `W-5`）**：原私有 `_reverse_links` 被两个面
  共用 ⇒ 改名公开（**判定与算法一字未动**）。
- **W-7（cycle 3 的**真缺陷**：架构契约违例，已修 —— 如实登记）**：`services.api.routers.memory`
  → `adapters` 违反 `.importlinter.api` 的「控制面 API 不得 import 具体适配器」。
  **成因** = EC-03「两处同源」第一版把判定留在适配器里。**本地四道门不做分层判定** ⇒
  只有 **m0 / CI** 能抓（这正是「全量门不是重复劳动」的又一取证）。修法 = 判定搬去应用层
  （两个读面都能 import 的那一层）+ `memory_read` **显式再导出**；**判定实现一字未动**。
- **W-8（cycle 3 的**判据面缺口**：自查补上 —— 如实登记）**：「判关系不判位置」的修法
  **自身会开口子**：合并多个可能落点能治假红，但标记在任一处即绿 ⇒
  「编排读面不再取单一来源」会**漏判**。**补**两条 **AST** 判据（判 import **指向** /
  判模块级**是否自写第二套**），**三条互补、无一条冗余**（两向实测读数见 §4c）。
  这处缺口**不是**被测出来，是**自查出来**的 —— 属 §8 纪律要求的形态，如实记录。
- **W-9（cycle 3 触发的申报义务）**：四处既有断言（`goal042` / `045` / `050` / `051`）
  被改动，命中 `escalation_triggers` 第 5 条形态 ⇒ 已在 §5 逐条登记（改动面 / 删除行读数 /
  谓词比对），**无一处收窄受判面**。
- **W-6（承继残余原样保持）**：GOAL-051 的 `CC-1`…`CC-3`；GOAL-050 的 `BB-1` / `BB-3`；
  GOAL-049 的 `AA-1`…`AA-3`；GOAL-048 的 `Z-1`…`Z-3`；GOAL-047 的 `Y-1`…`Y-3`；
  GOAL-046 的 `X-1`…`X-3`；GOAL-045 的 `W-2` / `W-3`；GOAL-044 的 `V-1`…`V-3`；
  `R26-*` 终态；未覆盖范围逐条保持。**不得**据此宣称项目安全（`R-M1`）；
  **不得**宣称投递语义为那四个字（**明确否认**）。
