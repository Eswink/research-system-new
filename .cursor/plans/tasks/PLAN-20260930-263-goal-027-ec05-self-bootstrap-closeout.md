---
id: PLAN-20260930-263
slug: goal-027-ec05-self-bootstrap-closeout
title: GOAL-027 cycle 5（EC-05）：自举收口 — 收口验证器进树 + 两树复检 + IN_SCOPE 纯收紧 + 残余与未覆盖逐条
status: DONE
created_at: 2026-09-30
updated_at: 2026-09-30
latest_recheck: .cursor/plans/rechecks/RECHECK-20260930-264-goal-027-ec05-self-bootstrap-closeout.md
memory_entries:
  - .cursor/memory/entries/MEM-20260930-178-closeout-verifier-reuses-the-standard-face-and-bites-two-ways.md
parent_goal: GOAL-20260929-027
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260929-027 的 **EC-05**（自举收口）。授权沿用该 GOAL 的 `authorization.ref`：
    「新增判据 / 夹具 / 探针（落 `tests/**` ⇒ m0 条数仍 `23`）」+「**新增真实现的 MCP server**
    （落 `tools/` 或既有结构，**必须**加进 `IN_SCOPE`）」（EC-05 的收口验证器同一条口径）+
    push-to-main-for-CI 口径（**只推 `main`**、不 force、不重写历史、不推旁支；
    push 前 `git pull --ff-only origin main`）。
    **本 PLAN 专属边界**：新增件一律落**新文件**；**不修改**任何既有判据 / 门禁 / 阈值 /
    放行面（点名：`tools/two_tree_recheck.py`、`tools/closeout_recheck_assertions.py`、
    `tests/tooling/test_two_tree_recheck_entry.py`、
    `tests/tooling/test_closeout_assertions_are_in_tree.py`、`tests/egress_guard.py`、
    三道记录面判据、`tests/application/test_m2_audit.py`、`tests/application/preflight/**`、
    规模门）；**不改** `PRODUCT_ROOTS` / m0 条数 / 作业结构（终态行仍 `23`）；**零**新依赖；
    **不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为「恰好一次」
    （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
    **一处对既有文件的受控改动（纯收紧、逐条留档）**：
    `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE` ——
    **只追加** `tools/verify_goal027_closeout.py` 一个条目（EC-05 的 verify 明文要求），
    不删任何既有条目、不改任何断言。
exit_criteria:
  - id: AC-1
    criterion: >-
      **收口验证器进树且过四道门**：`tools/verify_goal027_closeout.py` 复用
      `tools/closeout_recheck_assertions.py` 的公共判词（`standard_verdicts`），
      只写本轮特有断言；**显式加入 `IN_SCOPE`**（纯收紧）；`ruff check` /
      `ruff format --check` / `mypy`（strict）/ 规模（≤ 450 行）全绿。
    status: PASS
  - id: AC-2
    criterion: >-
      **两树复检同结论**：`tools/two_tree_recheck.py --script tools/verify_goal027_closeout.py
      --script-mode shared` 跑**当前树 + 干净 checkout** ⇒ 判词**逐行相同** + 两份判词文件
      `sha256` 相同 + `TWO-TREE PASS` / `EXIT=0`；留档与判词**一律二进制写盘**。
    status: PASS
  - id: AC-3
    criterion: >-
      **as-is 本机 m0 到 23/23**：终态行 `PASS: profile=m0; 23 deterministic checks`；
      **运行发生在记录写入之后**（承 MEM-145）；独占运行、canonical DSN pin、
      不接管道、零进程残留。
    status: PASS
  - id: AC-4
    criterion: >-
      **治理与记录面**：`validate.py` 绿（含 `DOCS-CHECK`）；三道记录面判据绿；
      `latest_recheck` 是仓库相对路径且指向通过取值的复检；`child_plans` /
      `memory_entries` 与 EC 表、迭代日志互相对齐。
    status: PASS
  - id: AC-5
    criterion: >-
      **CI 台账到终态 + 残余与未覆盖逐条**：逐 run 逐 job 实查（原始 JSON）；
      **空集合 / 空字段一律按「未取证」处理**；cancelled 如实登记；
      承继残余（各 EC 的 `W-N`）与未覆盖范围（读面未认证 / 多租户未做 /
      BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口）逐条在位；本轮新增残余照录。
    status: PASS
---

## 验收条件

| AC | 判据（简） | 判据文件 / 交付物 | 状态 |
| --- | --- | --- | --- |
| AC-1 | 验证器进树 + 复用公共判词 + 四道门 + `IN_SCOPE` 纯收紧 | `tools/verify_goal027_closeout.py` | **PASS** |
| AC-2 | 两树逐行相同 + `sha256` 相同 + `TWO-TREE PASS` | 两树入口 + 判词留档 | **PASS** |
| AC-3 | as-is m0 终态行（记录写入之后） | `scratch/goal027-c5-m0.log` | **PASS** |
| AC-4 | 治理 + 记录面 + 交叉引用一致 | `validate.py` + 三道记录面判据 | **PASS** |
| AC-5 | CI 台账到终态 + 残余与未覆盖逐条 | CI 台账 + GOAL 的残余/未覆盖节 | **PASS** |

## 目标

GOAL-027 的 **EC-05**：用**本 GOAL 自己的机器**（GOAL-023 起建立的收口装置）把五个 EC 收口 ——
验证器进树（复跑即可复核）、两树同结论（排除「结论依赖未提交产物」）、m0 到 23/23、
治理与记录面自洽、CI 台账到终态、残余与未覆盖范围逐条明写。

## 实施清单

- [x] WP-1：新增 `tools/verify_goal027_closeout.py`（复用 `standard_verdicts`，只写本轮特有断言）
- [x] WP-2：`IN_SCOPE` 显式追加（纯收紧）
- [x] WP-3：两树复检（当前树 + 干净 checkout）+ 判词二进制写盘
- [x] WP-4：as-is 本机 m0（记录写入之后，独占运行）
- [x] WP-5：治理 `validate.py` + 记录面判据 + 交叉引用对齐
- [x] WP-6：CI 台账到终态（原始 JSON 实查）
- [x] WP-7：记录（PLAN / RECHECK / MEM / GOAL 回写 / ALL_PLAN）+ 残余与未覆盖逐条

## 设计要点

1. **复用公共判词**（承 GOAL-026 的 449/450 行教训）：`standard_verdicts(root)` 覆盖
   受保护判据 / 规模门上限 / 产品根 / m0 条数 / 两树入口 / 规范页 / 记录自洽 ——
   本文件**一行都不重写**，只加 GOAL-027 特有断言（逐 EC 判据存在 + 例数下界 /
   三处缺陷修复（AST）/ 文献源 pin 面 / MCP server 与 `IN_SCOPE` / 协议声明 / 记录与规模）。
2. **缺陷修复用 AST 判定**：`_defines` / `_references_attr` 读**声明与属性取用**，
   不靠「文本里出现某个词」——文本巧合会在重构时给出假绿。
3. **例数下界是契约**：每份判据文件给一个下界（缺文件、例数掉下去，两向都判红）；
   下界取本轮实测值，不虚报。
4. **判词纯度与路径无关**（规范页 ② / ⑥）：只打印 `PASS` / `FAIL` 行，不含树的绝对路径
   —— 否则两树入口会（正确地）拒绝。
5. **EC-05 的时序**：GOAL 的 EC-05 在收口复检跑之前仍是**待判定**（判词就是本文件产出的），
   `goal-records-five-ec-pass` 因此断言 **≥4** —— 这是**时序**，不是放宽。

## 证据

见「状态历史」收口行与 `RECHECK-20260930-264`。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-30 | IN_PROGRESS | cycle 5 派生：EC-05 = 自举收口。装置已由 GOAL-023 建立（标准断言集 + 两树入口 + 判词纯度）；本轮只写特有断言。 |
| 2026-09-30 | DONE | **cycle 5 收口**：AC-1…AC-5 全部 PASS。验证器 **X 条判词**（标准集 + 本轮特有），`IN_SCOPE` 纯收紧；**两树逐行相同 + `sha256` 相同 + `TWO-TREE PASS`**；as-is m0 终态行（记录写入之后）；治理 + 记录面绿；CI 台账到终态。 |

## 影响报告

- **Domain/API/schema**：**零** Domain / OpenAPI / migrations 变化。
  新增：1 个 `tools/` 验证器；`IN_SCOPE` 追加 1 条（纯收紧）。
- **安全/凭据**：验证器只读文件与跑 AST 断言，**零出网、零凭据**；
  未放宽任何门禁。**不宣称**项目安全（`R-M1` 未收口）。
- **兼容性/迁移**：纯追加；`IN_SCOPE` 的追加只会让四道门覆盖**更多**文件（纯收紧）。
- **上游版本影响**：零新依赖。
- **可靠性口径**：**不宣称**投递语义为「恰好一次」
  （**明确否认**；口径固定为 at-least-once + idempotency + deduplication）。
- **剩余差距 / 下一项任务**：GOAL 收口后无后续 cycle；残余与未覆盖范围见 GOAL 的对应节。
