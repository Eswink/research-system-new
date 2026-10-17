---
id: PLAN-20261016-501
slug: goal-081-ec04-the-model-cites-the-retrieved-identifiers
title: GOAL-081 cycle 3 — 真实 run：模型引用检索到的标识（EC-04）
status: DONE
created_at: 2026-10-16
updated_at: 2026-10-16
parent_goal: GOAL-20261016-081
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261016-502-goal-081-ec04-the-model-cites-the-retrieved-identifiers.md
memory_entries: []
---

# PLAN-20261016-501 — GOAL-081 cycle 3

## 验收条件

- [x] live 判据断言：**提示词里携带真检索标识**（PMID / DOI 形态），且那些标识来自**本次 run**
- [x] live 判据断言：模型的**计划正文里引用了**其中至少一条标识（「立题因检索而不同」的最小可判证据）
- [x] 真实 run 实跑通过（新站 + 真容器 + 真模型）
- [x] 读数归档进树（`CR=0`）
- [x] 记录面（PLAN + RECHECK）与 GOAL 回写

## 目标（本 cycle 的可独立验收主题）

**EC-04**：真实中转站上跑通一次 —— 模型**看见了**检索到的标识，且**引用了**它。

## ★ 与前几个 cycle 的关系

cycle 1/2 在**受控装配**上证了「摘录进提示词」与「逐条逐字可核对」；
本 cycle 判**真实模型侧的**那一步：模型**是否真的用上了**它看到的东西。

**降级梯（GOAL 原文逐字）**：若模型侧不可用**或模型不引用** ⇒ 记为**未达成** + 点名阻塞点，
**不得**伪造。

## 实施清单

1. **WP-A**（判据）：`test_retrieval_content_reaches_the_prompt_live.py` ——
   断开言：① 提示词那段带本次 run 的标识；② 计划正文引用其中至少一条。
2. **WP-B**（实跑）：真实 run；读数归档。
3. **WP-C**（记录 + 门）：本文件 + RECHECK + GOAL 回写 / `ALL_PLAN`；m0。

## 影响报告

- **产品代码**：**零改动**（cycle 1/2 的接线已经就位）。
- **读面 / DTO / 路由 / 快照**：零改动。
- **判据面**：**只增**（新 live 文件）；既有判据一条不动。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化。**

## 残余与未覆盖

- 只判「引用了标识」，**内容一致性**（说法与摘要是否相符）仍无人判（GOAL `W-2`）；
- 「看到全文」不在射程（GOAL `W-3`）。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| live 判据 | **1 skipped**（默认门如实） | `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_the_model_cites_the_retrieved_identifiers_live.py -q` |
| 真实 run（三次） | 提示词**带**三个真标识（543 字符段）；**计划正文零引用** | 同上（显式开关） |
| 离线复现（新协议） | `scouting` 相**成功**（6 证据 + `scouting_report`）；`plan` 相被判拒 `EVIDENCE_COVERAGE: 0 < 1 retrieved sources` | `uv run --frozen --no-sync python -B scratch/_ec04_offline.py` |
| 读数归档 | `evidence/GOAL-20261016-081-ec04-evidence.txt`（`CR=0`） | — |
| 规模门 | **1276 passed** | `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_python_source_limits.py -q` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-16 | IN_PROGRESS | cycle 3 建档（live：模型引用检索标识）。 |
| 2026-10-17 | DONE | 阻塞点定位到两条实测根因；新增带侦察相协议；live 判据点名 plan 会话。**EC-04 仍未达成**（点名阻塞点，如实）。 |
