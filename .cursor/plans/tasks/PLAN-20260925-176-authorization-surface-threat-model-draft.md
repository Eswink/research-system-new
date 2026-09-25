---
id: PLAN-20260925-176
slug: authorization-surface-threat-model-draft
title: D-12(b) 授权面威胁模型草案：BOLA / BFLA 实况 + 未覆盖范围 + M18 边界 + (a) 的范围与代价
status: DONE
created_at: 2026-09-25
updated_at: 2026-09-25
parent_goal: GOAL-20260925-016
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260925-016 的 **2026-09-25 用户拍板（goal 模式）第 (7) 条**：
    **D-12 → 取 (b)** —— 先出**文档级**威胁模型草案（覆盖 BOLA / BFLA / 授权面），
    **不改代码、不改门禁、不加判据、不改阈值**。交付物必须写明
    **覆盖了什么 / 未覆盖什么 / 下一步 (a) 的范围与代价**，并写明与 **M18 边界**的关系。
    **本 PLAN 的硬边界**：diff **只含 `docs/`**（`git diff --name-only` 取证）；
    既有 106 行内容**不得删除**（纯增量）；不得新增测试 / allow / 阈值 / 判据；
    不得把草案写成安全结论。push-to-main-for-CI（只推 main、不 force、不重写历史、
    不推旁支）。**越界即 BLOCKED**（触发 escalation_triggers 的「改门禁/阈值」条）。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260925-177-authorization-surface-threat-model-draft.md
memory_entries:
  - .cursor/memory/entries/MEM-20260925-138-threat-model-draft-needs-a-scope-fence.md
---

# PLAN-20260925-176 — D-12(b) 授权面威胁模型草案（GOAL-016 / EC-05）

## 目标

把 D-12 从「授权面覆盖缺一项系统性论证」变成**可引用的实况清单**：在
`docs/security/THREAT_MODEL.md` **增量补第 6 节**，用**树上可复核的事实**说明今天的
授权面在 BOLA / BFLA 上的样子，并明确**划出射程之外**的东西。

**本 PLAN 不产生安全性**：它不修任何东西、不加任何判据，只把「缺什么」写清楚，
让下一步 (a) 的范围与代价可以被估算。

## 验收条件

- **AC-1｜结构**：第 6 节含 `### 6.3 未覆盖范围（明确不覆盖什么）`、BOLA / BFLA 字样、
  以及 `### 6.4 与 M18 边界的关系`。
- **AC-2｜纯增量**：`git diff --numstat docs/security/THREAT_MODEL.md` **删除数为 0**
  （既有 106 行一字未删）。
- **AC-3｜diff 只含 docs**：本 cycle 的改动集**只含** `docs/` 下的文件
  （`git status --porcelain` 逐条核对；三个并发写者文件不在内）。
- **AC-4｜事实可复核**：6.2 的每条实况都有 `file:line` 或符号名出处；
  **不得**出现无出处的断言。
- **AC-5｜口径不越界**：6.6 明写「不得引作安全结论」，并给出**唯一**可引用口径。
- **AC-6｜门与记录**：`DOCS-CHECK` = PASS（反引号引用须可解析）；治理 `validate.py` 绿；
  m0 终态行（标明树与跑法）+ 本 PLAN / RECHECK / MEM + GOAL-016 回写。

## 实施清单

- [x] WP1：只读勘察授权面（124 条路由 / 认证机制 / 策略层 / 归属字段 / M18 定义 /
      `docs/security/` 现状 / 既有安全判据清单）。
- [x] WP2：写第 6 节（6.1 术语 / 6.2 覆盖了什么 / **6.3 未覆盖范围** /
      **6.4 与 M18 边界的关系** / 6.5 若取 (a) 的范围与代价 / 6.6 引用约束）。
- [x] WP3：`docs/INDEX.md` 的 Security 节给该行加注（仍是 docs-only）。
- [x] WP4：取证（numstat 删除数 0 / diff 只含 docs / `DOCS-CHECK` PASS）。
- [x] WP5：m0 + 记录（本 PLAN + RECHECK + MEM）与 GOAL-016 回写。

## 证据（本地）

- **纯增量**：`git diff --numstat docs/security/THREAT_MODEL.md`
  ⇒ **`146  0  docs/security/THREAT_MODEL.md`**（146 增、**0 删**）；
  文件由 **106 行 → 252 行**。
- **结构**：`未覆盖范围` 命中在 `:166`；`M18` 关系节在 `:194`；
  `BOLA` / `BFLA` 命中 **6** 处。
- **diff 只含 docs**：本 cycle 改动集 =
  `docs/security/THREAT_MODEL.md` + `docs/INDEX.md`（**两个 docs 文件**）；
  工作树里另外三个文件是**并发写者**的未提交条目，**未**被纳入（**未** `git add`）。
- **doc 一致性门**：`uv run --frozen --no-sync python -B tools/docs_consistency_check.py`
  ⇒ **`DOCS-CHECK PASS: 6 deterministic checks`**。
- **治理门**：`validate.py` ⇒ `Cursor 治理验证通过`。
- **m0**：见 GOAL-016 的 CI 台账与 `RECHECK-20260925-177`（终态行标明树与跑法）。

## 残余（本 PLAN 不处置）

- **D-12(a) 未做**（且**未**被本 PLAN 缩权）：6.5 只给出范围与代价估算；
  真正做 (a) 需要**主体模型**（M18 或其明文授权的等价子集）——**没有第二个主体可测**。
- **控制面无认证这一事实仍在**：本 PLAN 只登记（6.2 第 2 条 / 6.3 第 1 条），
  **不修、不加门**。⇒ 部署仍必须以「单用户、本机 / 受信网络」为前提。
- **`FRAMEWORK_MANIFEST.json` 的该条快照会过期**：该文件是**发布快照**
  （`docs/operations/REPOSITORY_HYGIENE.md:21`：只由显式发布流程生成），本项目**不**在
  本 cycle 重新生成它（否则 diff 会含非 docs 文件，违反 AC-3）。
  实测该快照**本就已过期**（220 条中 131 条 hash 与现树不符）⇒ 不是本 cycle 引入的问题；
  刷新属**发布动作**，**不在**本 GOAL 范围。
- **本节无自动发现能力**：树变了它不会红（这正是 (b) 的固有代价，已写进 6.3 第 6 条与 6.5）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-25 | IN_PROGRESS | derive：从 GOAL-016 的 EC-05 圈定 D-12(b)，本文件 + `ALL_PLAN` 投影 + `parent_goal` 同提交。 |
| 2026-09-25 | IN_PROGRESS | WP1：只读勘察完成（事实来源见 6.2 与「证据」）。**零代码改动**。 |
| 2026-09-25 | DONE | WP2–WP5：第 6 节落盘（146 增 0 删）；`INDEX` 加注；`DOCS-CHECK PASS`；m0 与记录回写完成；复检 `RECHECK-20260925-177` 见 `latest_recheck`。 |

## 影响报告

- **改动**：`docs/security/THREAT_MODEL.md`（第 6 节，**纯增量**）、
  `docs/INDEX.md`（Security 行加注）；记录文件。
- **lint / typecheck / test**：无代码改动 ⇒ 相关面不适用；`DOCS-CHECK` = PASS；
  治理 `validate.py` = 通过；m0 终态行见 RECHECK-177。
- **Domain / API / schema 变化**：**无**。
- **安全 / 凭据变化**：**零改动**。本 PLAN **降低**了「授权面缺口不可见」的风险
  （登记成可引用依据），但**没有**提高任何访问控制强度——**不得**读成安全改进。
- **兼容性 / 迁移风险**：无（文档）。
- **上游版本影响**：无。
- **下一项任务**：GOAL-016 的 **EC-06（收口复检 + 13 项 `D-NN` 终态表 + CI 台账）**。
