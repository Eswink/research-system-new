---
id: RECHECK-20261014-467
slug: goal-077-ec02-03-report-on-the-product-path
title: GOAL-20261014-077 cycle 1 复检 — 报告经产品路径产出 + 立题由检索派生
status: COMPLETED
result: PASS
created_at: 2026-10-14
updated_at: 2026-10-14
plan_id: PLAN-20261014-466
parent_goal: GOAL-20261014-077
reviewer: root-agent
owners:
  - root-agent
---

# RECHECK-20261014-467 — GOAL-077 cycle 1

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。
本记录**独立于** PLAN 作者的结论：每条断言都由复检脚本重新执行判据本体（不是读 PLAN 的表）。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | 新协议在树且可编译 | **PASS** | `examples/protocols/research_report_chain_v1.yaml`（4 phase）；`compile_protocol` ⇒ `plan is not None` 且 findings 为空 |
| AC-2 | 报告经**产品路径**产出 | **PASS** | `tests/e2e/test_research_report_arc_offline.py::TestTheRunProducesAHumanReadableReport` ⇒ run `SUCCEEDED`；报告制品 `{run_id}:research_report.md` 在 `GET /runs/{id}/artifacts` 上；`GET /artifacts/{id}/content` ⇒ 200 + `text/markdown` |
| AC-3 | 报告四节齐全 + 自陈汇编边界 | **PASS** | 四条 `SECTION_HEADINGS` 逐条在位；抬头标「**汇编时状态**」（不冒充终态）；局限节自陈「确定性汇编 ⇒ 逐字节相同」与「不是模型的叙述性撰写」 |
| AC-4 | 每个数字可溯源（逐字） | **PASS** | 真 PMID `39284801` / `40601758` 与真标题片段逐字出现在报告里；指标值与 `GET /runs/{id}/experiments` 的**同一读面**逐字相同（`_metric_text` 重写读面规则当受判面，未 import 产品 helper）；判词段给出 gate 的逐字决定 |
| AC-5 | 内容寻址（digest 由内容重算） | **PASS** | `_content_addressed` 用 `Digest.of_bytes(report)` 与制品读面的 digest 比对 ⇒ 相等 |
| AC-6 | **立题由检索派生**（EC-03） | **PASS** | `GET /runs/{id}/reviews` 里 `research_report_plan` 的判词逐字为 `EVIDENCE_COVERAGE: 3 >= 1 sources; 2 >= 1 retrieved`（**两维都在**），且运行链真的执行了两步（离线传输记录含 `EXT_ID:` 请求） |
| AC-7 | 反证 A（摘检索 ⇒ 立题判拒并点名） | **PASS** | 同一条链、同一份协议，只不接运行链检索 ⇒ run `FAILED`、工具证据为零、失败消息含 `retrieved sources` |
| AC-8 | 反证 B（摘汇编器 ⇒ 点名拒绝且无报告） | **PASS** | 只不接报告汇编器缝 ⇒ run `FAILED`、失败消息含 `no report assembler is wired`、制品面**无** `research_report.md`；检索与实验**照跑**（失败只出在 report 格） |
| AC-9 | 复合执行体声明互斥 | **PASS** | 构造同时声明 `report` 与 `experiment` 的合约 ⇒ `ValueError` 点名「which body executes this work would be undecidable」 |
| AC-10 | 既有判据零放宽 | **PASS** | 架构 + 工具面 252 + 1741（两轮）；应用层 / 域 / 适配器 / API **2739 passed, 8 skipped**；e2e / 集成 / 合约 **865 passed, 85 skipped**；汇编器既有 7 例仍绿。三份同源判据的**字面量清单扩面**（新受判对象登记进原谓词）—— 谓词一条未改 |
| AC-11 | 规模门 | **PASS** | `test_python_source_limits`：新增 5 个模块（365 / 240 / 82 / 63 / 59 行）+ 1 个 e2e 模块（410 行），全部 ≤ 450；无超 50 行函数（一次修正：e2e 的长用例拆成 3 个） |
| AC-12 | 报告**不是**模型撰写 | **PASS** | 报告由 `build_research_report` 确定性产出（同输入 ⇒ 逐字节相同，EC-01 既有判据），执行体是编排层派发的汇编器（`report: {}` 声明 ⇒ `dispatch_report`）；**无**会话被创建（`report` phase 的 `strategy: deterministic`） |

## 警告（如实登记）

- **`W-1`**：**EC-04 / EC-05 仍未完成** —— 本 cycle 只做到「离线链上报告经产品路径产出」；
  新站真实 run 与自举收口属 cycle 2 / cycle 3。
- **`W-2`**：报告的指标格**只覆盖 `experiment_result.json` 的 `metrics` 块**（与 HTTP 读面
  同一份字节）。实验的 `metrics` 制品（合约 `ARTIFACT_EXISTS` 判的那一件）内容**未被合并** ——
  两件在本仓是同一批值的两种写法，但**只读一处**是刻意的：读两处会让「报告与读面一致」
  这条判据在两者不一致时失去意义。
- **`W-3`**：报告在 run **内**汇编 ⇒ 抬头是「汇编时状态」（`RUNNING`），run 的最终终态不在
  报告里；读者要终态须读 `GET /runs/{id}`。这是如实边界。
- **`W-4`**：**检索内容不进模型上下文**（阶梯「检索」域的下一级，本 GOAL 明确不做）；
  报告只保证「站在真检索上」（来源逐条入报告 + 覆盖两维判过）。
- **`W-5`**：`R-M1` 未收口 ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」
  （口径只能是 at-least-once + idempotency + deduplication）。
- **`W-6`**：报告**不做跨 run 聚合**（只覆盖本 run），也不判定上游 phase 的结论可靠性 ——
  两条都写在报告的「局限」节里（自陈，不是外部声明）。

## 未覆盖的面

- 新站真实 run 跑完整协议的落盘与 digest 记账（EC-04）；
- 自举收口（EC-05：验证器 / 两树 / m0 终态 / 治理 / CI 台账）;
- 报告的**叙述性撰写**（模型写正文；阶梯「报告」域的再下一级）；
- 活检索结果进模型上下文（阶梯「检索」域的下一级）。

## 结论

**PASS。** 报告的产出路径从「汇编器在树、没有产品路径」变成「**经产品路径产出、可复核**」：
`report: {}` 声明 ⇒ 编排派发 ⇒ 读本 run 的持久事实 ⇒ 汇出 `research_report.md` ⇒
四节齐全、每个数字逐字可溯源、内容寻址。立题格的两维覆盖判据（计数 + 性质）在
**同一次实跑**上判过，且两条反证各自点名（摘检索 ⇒ 立题判拒；摘汇编器 ⇒ report 格判拒）。
既有判据与规模门零放宽（3 份同源判据只扩字面量清单）。
