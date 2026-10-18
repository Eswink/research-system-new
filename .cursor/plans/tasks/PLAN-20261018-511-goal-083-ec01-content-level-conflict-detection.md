---
id: PLAN-20261018-511
slug: goal-083-ec01-content-level-conflict-detection
title: GOAL-083 cycle 1 — 记忆的内容级冲突检测（EC-01…EC-04）
status: DONE
created_at: 2026-10-18
updated_at: 2026-10-18
parent_goal: GOAL-20261018-083
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261018-512-goal-083-ec01-content-level-conflict-detection.md
memory_entries: []
---

# PLAN-20261018-511 — GOAL-083 cycle 1

## 验收条件

- [x] **EC-01**：确定性纯函数判定三种可机械判形态（否定极性 / 数值方向 / 反义谓词），
      零出网零模型（源码级断言钉住）；对称、可复现
- [x] **EC-02**：接进既有门链的 `contradiction` 阶段；未声明但相反 ⇒ **判拒并点名 id 与形态**；
      引用完整性（存在 / 不自指）**逐字不变**；声明优先；三条边界（同 scope / 不重复判已声明 /
      `active=False` 不参与）；**按压**：关掉判定 ⇒ 通过
- [x] **EC-03**：两种来源的判词**分得开**（门链层 + 反证）；**并钉住 API 缺口**
      （`MemoryProposalDto` 不含 `contradictions`）
- [x] **EC-04**：真实语料**零误报**（同义 / 无关 / 真实语料三组 + 射程边界组 + 非空转对照）
- [x] 零回归（application 1171 passed）+ ruff + mypy + 规模门
- [x] **EC-05 不在本 cycle 的射程**（如实登记：它是收口 cycle 的交付物；本 PLAN 只做 EC-01…EC-04）

## 目标

让**两条记忆的说法真的相反**这件事判得出来 —— 阶梯「证据」域的 `下一级`。

## ★ 建档实测（为什么这是缺口）

1. `detect_content_conflict` / `conflicts_with` / `content_conflict` 三词**全仓零命中**；
2. 门链 `contradiction` 阶段只查**引用完整性**（正文一个字都不看）；
3. 读面 `CONFLICTED` 只来自**声明**（`_unresolved_declarers`）；
4. ⇒ 说法真的相反、但无人声明时，读面照旧报 `USE`（照用）。

## 实施清单

1. **WP-A**（判定）：`packages/application/memory/content_conflict.py` —— 三种形态 +
   对称性 + 射程边界（只判可机械判的形态）。
2. **WP-B**（门链）：`gate._content_conflict_check` + `_active_records_in_scope` ——
   同 scope、不重复判已声明、跳过 `active=False`。
3. **WP-C**（判据）：四个文件、**60 条**（detection 21 / gate 10 / read_face 5 / precision 24）。

## 影响报告

- **产品代码**：新增一个纯函数模块；`gate.py` 增加一个阶段内的子检查（**不**新造门链阶段）。
- **读面 / DTO / 路由 / 快照**：**零改动**（`MemoryProposalDto` 未动）。
- **判据面**：**只增**（四个新文件）；既有 `tests/application/memory/**` 与
  `tests/api/test_memory_api.py` **零改动**、全绿。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化、无模型调用。**

## 工程记忆

**无可复用事实**（本轮口径写进 PLAN 与 RECHECK-512 的可复核观察面；判据文件即事实面）。

## 残余与未覆盖

见 GOAL 的「残余与未覆盖范围」：`W-2`（判不了世界知识级矛盾）、`W-3`（不做存量补判）、
**`W-5`（HTTP 写面没有声明冲突入口 —— 本轮实测发现）**、**`W-6`（无单位数字不判）**。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| EC-01 判定 | **21 passed** | `uv run --frozen --no-sync python -B -m pytest tests/application/memory/test_content_conflict_detection.py -q` |
| EC-02 门链 + 按压 | **10 passed** | `... test_content_conflict_gate.py -q` |
| EC-03 来源可分 + API 缺口 | **5 passed** | `... test_content_conflict_read_face.py -q` |
| EC-04 零误报 | **24 passed** | `... test_content_conflict_precision.py -q` |
| 零回归 | **1171 passed, 1 skipped**（application + memory api） | — |
| 静态门 | ruff 绿 / mypy **1269 files no issues** / 规模门在限内 | — |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-18 | IN_PROGRESS | cycle 1 建档（内容级冲突检测）。 |
| 2026-10-18 | DONE | EC-01…EC-04 全 PASS（60 条判据）；EC-03 **改判**（API 无声明入口）+ 新增缺口断言；`W-5`/`W-6` 如实登记。 |
