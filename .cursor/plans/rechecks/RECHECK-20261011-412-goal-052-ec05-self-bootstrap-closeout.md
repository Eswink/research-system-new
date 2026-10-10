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
判定仍属编排面 / 快照含四样）· `ec04-*`（四条用例逐条点名 + **基线门** +
四按压全红与复原一致）。

### 2. 两树复检与归档（AC-2，独立重跑）

**bootstrap 轮**：两份归档 missing（归档由本次调用写出、尚在提交之前）⇒ `TWO-TREE RED`；
两路 `COMPARE identical=True`（差异**只**在归档项）。**终态轮**（`--base-ref HEAD`）：
终局行 **`TWO-TREE PASS`**；两路 **63 判词**、`sha256` 相同 `b976f18c0b872d31…`。
归档两份各 **2341 B / 63 行 / `CR=0` / 0 FAIL**（二进制写盘）。

### 3. §8 新增纪律（**判据不得恒假**）的落地复核

| # | 措施 | 独立读数 |
| --- | --- | --- |
| 3.1 | **字段读取用 AST**（`MemoryRecordDto` 类体的 `AnnAssign` 目标） | 真树 **17 字段** = 13 既有 + 4 新增 |
| 3.2 | **非空性三条实测** | 空源码 ⇒ **空集**；合成只含 `id` 的 DTO ⇒ **只读到 `id`**；真树 ⇒ 17 ⇒ 判据**不恒真/不恒假** |
| 3.3 | **反证脚本的基线门**（未按压必须绿） | cycle 1 正是靠它抓到 `N-4` 的**假反证臂**（受判面区分不了两件事）⇒ 已换受判面 |
| 3.4 | 归档含**基线行** | `GOAL-20261011-052-press-two-way.txt` 首行为 `BASELINE…: GREEN` |

### 4. 门链与记录面（AC-3，独立重跑）

`validate.py` 通过；`test_mainline_program_is_intact.py` 绿（本 GOAL 的 id 已在程序表**序 20**）；
定向套件 `tests/{application,api,e2e,domain,adapters,postgres,contracts,tooling}`
**4956 passed, 18 skipped**。**as-is m0**：`PASS: profile=m0; 23 deterministic checks`
（`PASS [` 24 / `FAILED [` 0 / passed/skipped 读数**待全量 m0 实测回填**；在全部记录写完之后、
独占、仓库 `.venv`、不接管道）。

### 5. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | 改动 | 谓词比对 | 删除行 |
| --- | --- | --- | --- |
| `tests/tooling/test_tooling_scripts_meet_product_gates.py` | `IN_SCOPE` **+2 行** | **纯收紧**（只加） | **0** |
| `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` | 射程清单 **+1 行** + 下界 21→22 | **纯收紧** | **0** |
| `tools/goal050_closeout_assertions.py`（cycle 1） | 钉助手**名字** ⇒ 改判**关系** | **等价**（同一件事：存在「把 `supersedes` 汇总成反向表」的助手；**两种名字都过**、助手不存在则红 —— 已两向实测）| 仅原比对式 |

**收窄受判面？** 无。**未**放宽任何既有断言。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-5 逐条独立成立：收口面进树且过四道门、
两树 `TWO-TREE PASS`、归档与最终一轮同结论、治理与宪章判据绿、定向套件 4956 例绿、
CI 台账逐提交；且 §8 的新增纪律（**判据不得恒假**）**落成了机械面**（AST 读字段 +
三条非空性实测 + 反证脚本基线门）。

### Warnings

- **W-1（HTTP 面的时点判定不在本轮；承 `DD-1`）**：HTTP 面**仍不**做「按时点判时效」。
- **W-2（其他读面未普查；承 `DD-2`）**：本轮对齐的是**记忆**的两个读面；**别的实体**是否有同类
  差集**未普查** —— 这是本 GOAL 登记的**最实的一条**后续候选。
- **W-3（一致性判据只在记忆面；承 `DD-3`）**：**未**做全仓通用的一致性判据。
- **W-4（cycle 1 的两处如实登记，均已修）**：① **假反证臂**（`N-4` 受判面区分不了两件事 ——
  「有断言」≠「断言在下判断」）；② `goal050` 钉助手**名字** ⇒ 改名公开后假红 ⇒ 改判**关系**。
- **W-5（`superseded_by_index` 改名公开，承 cycle 1 的 `W-5`）**：原私有 `_reverse_links` 被两个面
  共用 ⇒ 改名公开（**判定与算法一字未动**）。
- **W-6（承继残余原样保持）**：GOAL-051 的 `CC-1`…`CC-3`；GOAL-050 的 `BB-1` / `BB-3`；
  GOAL-049 的 `AA-1`…`AA-3`；GOAL-048 的 `Z-1`…`Z-3`；GOAL-047 的 `Y-1`…`Y-3`；
  GOAL-046 的 `X-1`…`X-3`；GOAL-045 的 `W-2` / `W-3`；GOAL-044 的 `V-1`…`V-3`；
  `R26-*` 终态；未覆盖范围逐条保持。**不得**据此宣称项目安全（`R-M1`）；
  **不得**宣称投递语义为那四个字（**明确否认**）。
