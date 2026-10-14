---
id: RECHECK-20261014-465
slug: goal-077-research-report-and-the-end-to-end-research-arc
title: GOAL-20261014-077 复检 — 报告汇编器与端到端研究弧
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-14
updated_at: 2026-10-14
plan_id: PLAN-20261014-464
parent_goal: GOAL-20261014-077
reviewer: root-agent
owners:
  - root-agent
---

# RECHECK-20261014-465 — GOAL-077

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | 报告汇编器在树 | **PASS** | `packages/application/deliverable/research_report.py`（四节 + 制品名 + MIME 常量） |
| AC-2 | 汇编器判据成对且全绿 | **PASS** | `tests/application/test_research_report_assembler.py` **7 passed**（四节齐全 / 事实逐字 / 缺事实声明 / 确定性 / 空 run_id 点名 / 局限节诚实 / 制品名与 MIME） |
| AC-3 | 合约在树 | **PASS** | `examples/contracts/task_contracts.yaml` 新增 `research_report_plan`（含 `minimum_retrieved_sources: 1`）与 `research_report_deliverable`（`ARTIFACT_EXISTS: research_report.md`）；合约总数 22 → **24** |
| AC-4 | GOAL 结构合规 | **PASS** | `validate.py` = 治理通过（含七节标题、frontmatter、`latest_recheck` 相对路径） |
| AC-5 | 宪章阶梯记账 | **PASS** | 宪章 `进展记录` 新增本 GOAL 一行（能力域 = 报告）；阶梯「报告」域依据面收录（`test_mainline_research_ladder_advances.py` 核心不变式） |
| AC-6 | EC-02/EC-03/EC-04 | **未完成** | 报告经产品路径产出 / 立题由检索派生 / 新站实跑 —— **本轮未完成**，见「未覆盖的面」 |

## 警告（如实登记）

- **`W-1`（最要紧）**：**EC-02 / EC-03 / EC-04 均 未完成** —— 本 GOAL 的实际交付
  目前**只有汇编器与它的判据**（EC-01），**端到端报告还没有经产品路径产出过一次**。
  宪章阶梯的「报告」域因此记为 **L0.5（汇编器在树，未经产品路径产出）**，
  **不得**读成 L1。
- **`W-2`**：新协议 `research_report_chain_v1` **尚未创建**（EC-03 的载体）⇒
  「立题由检索产出派生」这一条**未取证**。
- **`W-3`**：新站真实 run 只跑到**既有**协议（`real_research_task_v1`）为止，
  **没有**产出报告 ⇒ 「真实研究报告」这一格仍是空的。
- **`W-4`**：`R-M1` 未收口；本记录**不**作任何安全结论；投递语义**不是**「恰好一次」
  （口径只能是 at-least-once + idempotency + deduplication）。

## 未覆盖的面

- 报告**经产品路径**产出（EC-02，`W-1`）；
- 五 phase 新协议与「立题派生」（EC-03，`W-2`）；
- 报告在新站真实 run 里的落盘与 digest 记账（EC-04，`W-3`）；
- 报告撰写由模型承担（阶梯「报告」域的**再下一级**，本 GOAL 明确不做）。

## 结论

**PASS_WITH_WARNINGS。** EC-01 成立且实跑取证（汇编器 + 7 例判据全绿）；合约面已就位
（2 个新合约）。**EC-02/EC-03/EC-04 仍 未完成** —— 端到端报告弧**尚未跑通**，
阶梯的「报告」域按**如实读数**记为「汇编器在树、未经产品路径产出」。
