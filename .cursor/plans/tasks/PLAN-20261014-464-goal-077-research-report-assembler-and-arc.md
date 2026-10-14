---
id: PLAN-20261014-464
slug: goal-077-research-report-assembler-and-arc
title: GOAL-077 EC-01 — 报告汇编器 + 判据；EC-03/EC-04 的新协议与实跑
status: IN_PROGRESS
created_at: 2026-10-14
updated_at: 2026-10-14
parent_goal: GOAL-20261014-077
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261014-465-goal-077-research-report-and-the-end-to-end-research-arc.md
memory_entries: []
---

# PLAN-20261014-464 — GOAL-077

## 验收条件

- [x] EC-01 报告汇编器在树（`packages/application/deliverable/research_report.py`）
- [x] EC-01 判据 7 例全绿（四节齐全 / 事实逐字 / 缺事实声明 / 确定性 / 空 run_id 点名 / 局限诚实 / 制品名与 MIME）
- [x] 两个合约在树（`research_report_plan` / `research_report_deliverable`）
- [x] 宪章阶梯记账（本轮被「报告」域收录）
- [ ] EC-03 新协议 `research_report_chain_v1`（5 phase：scouting → plan → experiment → review → report）
- [ ] EC-02 报告经**产品路径**产出（真落 canonical 的 markdown，内容可复核）
- [ ] EC-04 新站真实 run 跑完整协议 + 报告落盘 + 记账
- [ ] EC-05 自举收口（验证器 + 两树 + m0 + 治理 + 台账）

## 实施清单

1. **报告汇编器**（EC-01，已完成）：`ReportInputs` → `build_research_report` 确定性产出
   四节 markdown；`REPORT_ARTIFACT_NAME = "research_report.md"`；缺事实写「无 + 原因」；
   局限节自陈「汇编而非撰写」。
2. **合约**（已完成）：`research_report_plan`（要求 `minimum_retrieved_sources: 1`
   ⇒ 立题站在真检索上）、`research_report_deliverable`（要求 `research_report.md`）。
3. **新协议**（EC-03，待做）：`examples/protocols/research_report_chain_v1.yaml`，五 phase ——
   `scouting`（run_chain 真检索）→ `plan`（会话 phase，合约要求消费检索产出）→
   `experiment`（既有沙箱实验合约）→ `review`（既有评审合约）→ `report`（新合约）。
4. **报告接线**（EC-02，待做）：report phase 的制品构造点（复用既有 `register_session_result`
   或等价的 canonical 写入路径）+ 读面可读（`GET /artifacts/{id}/content` 内联 markdown）。
5. **实跑**（EC-04，待做）：新站 + 真实 runtime 跑五 phase；报告落盘；记 run id / digest /
   §4 漂移事实。
6. **收口**（EC-05，待做）：验证器 + 两树 + m0 + 治理 + 台账 + 残余。

## 证据

| 面 | 读数 |
| --- | --- |
| 汇编器判据 | `tests/application/test_research_report_assembler.py` ⇒ **7 passed** |
| 合约数 | `task_contracts.yaml` 22 → **24**（两个新合约在树） |
| 治理 | `validate.py` = `Cursor 治理验证通过` |
| 真实 run（既有协议） | `tests/e2e/test_real_protocol_run_live.py` ⇒ **1 passed in 258.50s**（新站） |
| relay probe | `RELAY SMOKE OK`；返回名 `dsv4-flash-vision` ≠ 声明名（§4 记录） |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-14 | IN_PROGRESS | EC-01 落地（汇编器 + 7 例判据 + 2 合约 + 治理绿）；EC-02/03/04/05 待做 |

## 影响报告

- **产品代码**：新增一个模块（`packages/application/deliverable/research_report.py`）
  —— **纯新增**，不改既有模块；
- **合约面**：`examples/contracts/task_contracts.yaml` **追加**两个合约（不改既有）；
- **宪章**：`MAINLINE.md` 加阶梯小节 + 两表各加一列 + 序 45 行 + 序 44 置 PAUSED；
- **判据面**：新增 `test_mainline_research_ladder_advances.py`（7 例）、
  `test_research_report_assembler.py`（7 例）；**改** `test_mainline_program_is_intact.py`
  两处列契约（谓词未放宽）+ 一处合成夹具；
- **中转站**：配置切到新站（见 PLAN-462）；
- **无 schema 迁移、无依赖变化、无放行面变化**。

## 残余与未覆盖

见 `RECHECK-20261014-465` 的 `W-1`…`W-4`：**端到端报告弧尚未跑通**（EC-02/03/04 PENDING）；
新协议未创建；阶梯「报告」域如实记为「汇编器在树、未经产品路径产出」。
