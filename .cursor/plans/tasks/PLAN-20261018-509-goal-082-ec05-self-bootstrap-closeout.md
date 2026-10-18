---
id: PLAN-20261018-509
slug: goal-082-ec05-self-bootstrap-closeout
title: GOAL-082 cycle 2 — 自举收口 + EC-04 的 BLOCKED 判定（EC-05）
status: DONE
created_at: 2026-10-18
updated_at: 2026-10-18
parent_goal: GOAL-20261018-082
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261018-510-goal-082-ec05-self-bootstrap-closeout.md
memory_entries: []
---

# PLAN-20261018-509 — GOAL-082 cycle 2

## 验收条件

- [x] 验证器进树（`tools/verify_goal082_closeout.py`）+ 本轮断言集
      （`tools/goal082_closeout_assertions.py`，**由验证器自己加载**）
- [x] 本树 `--verdict-only` 全 PASS（**62 条**）
- [x] 两树复检（`tools/two_tree_recheck.py`）判词逐行相同 + `sha256` 相同
- [x] as-is m0 **23/23**（在全部记录写入之后、**静止工作树**）
- [x] 治理绿 + 凭据审计四面 `offenders=0`
- [x] 三处清单同轮登记（`tools/` 射程分区 / `IN_SCOPE` / 验证器分类清单）
- [x] **EC-04 的判定**：评估「改判内容采纳」→ **否决**（有实测依据），改记 **BLOCKED** + 解除条件
- [x] 阶梯「迭代」行前移并收录本 GOAL
- [x] CI 台账逐提交（`cancelled` / rerun 如实登记 + 原因）

## 目标

**EC-05**：让本 GOAL 的收口**可被机器复检**，复检**自举**，两树给出**同一组判词**；
并给 **EC-04** 一个**有据的终态**（不是含糊的「待办」）。

## EC-04 的判定（本轮最重要的决定，附实测）

候选 A：把判据从「引用 `memory_id`」改成「采纳记忆内容」。
**否决**，理由是**它会假绿**：

- 三次真实 run 的计划里 `duplicate_pairs` 取值为 **30 / 30 / 10**（不一致）；
- 而 `duplicate_pairs` **本来就在**实验参数白名单（`ALLOWED_PARAMETERS`）里 ——
  「文中出现这个名字」既可能是采纳，也可能只是设计实验时的自然用词；
- 前序记忆写的是固定值，两次 run 都没照它 ⇒ **内容采纳不可判别**；
- 把不可区分的形态写成判据 = **放宽判据**（GOAL 的 `forbidden` 明确禁止）。

⇒ EC-04 记 **BLOCKED**，阻塞点逐条（模型侧 / 判据侧 / 产品侧已无缺口），并写明**解除条件**：
给每条记忆一个 DOI 式稳定短标识，或引入结构化的「引用了哪条记忆」字段（均属产品结构改动）。

## 实施清单

1. **WP-A**：`tools/goal082_closeout_assertions.py` —— 例数下界、落点形态、两段**并列**、
   上限**导入**自 `retrieval_context`、两组合根接线、**EC-04 未达成的事实仍在树**。
2. **WP-B**：`tools/verify_goal082_closeout.py` —— 标准断言集 + 本轮断言 + 记录面；
   自指两条（`self-loads-its-own-assertions` / `ladder-records-this-goal`）。
3. **WP-C**：三处清单登记 + 两树 + m0 + 治理 + 凭据 + CI 台账。

## 影响报告

- **产品代码**：零改动（本 cycle 只加收口资产与记录）。
- **判据面**：新增两个 `tools/` 脚本（纳入射程 ⇒ 过 ruff / 规模四道门）；
  `goal-ec04-status` 断言从「达成 ∪ 待办」**扩展到**「达成 ∪ 待办 ∪ 阻塞」——
  **仍然拒绝「缺失」**（漏一格状态块与「记成 PASS」同样不可接受）。这是**随事实收紧**，
  不是放宽：它让「如实记 BLOCKED」这条合法路径可通过，而「漏写」照旧判红。
- **记录面**：阶梯「迭代」行前移（收录本 GOAL）。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化。**

## 残余与未覆盖

- **EC-04 阻塞**（解除条件见 GOAL）；多轮累积衰减、`RUN → PROJECT` 提升策略仍不做。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| 本树判词 | **62 PASS / 0 FAIL** | `uv run --frozen --no-sync python -B tools/verify_goal082_closeout.py --root . --verdict-only` |
| 两树复检 | `COMPARE identical=True`，两树 `sha256` 相同 | `uv run --frozen --no-sync python -B tools/two_tree_recheck.py --script tools/verify_goal082_closeout.py --root . --script-mode shared --base-ref HEAD` |
| as-is m0 | **`PASS: profile=m0; 23 deterministic checks`** | `uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going` |
| 治理 / 凭据 | `Cursor 治理验证通过` / 四面 `offenders=0` | `validate.py` / `tools/credential_audit.py` |
| `tools/` 四道门 | **17 passed** | `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_tooling_scripts_meet_product_gates.py tests/tooling/test_closeout_verifiers_run_their_own_assertions.py -q` |

## 工程记忆

**无可复用事实**（本轮口径写进 PLAN 与 RECHECK-510 的可复核观察面；判据文件即事实面）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-18 | IN_PROGRESS | cycle 2 建档（自举收口 + EC-04 判定）。 |
| 2026-10-18 | DONE | 验证器 **62 PASS / 0 FAIL**；两树 `sha256` 相同；as-is m0 **23/23**；**EC-04 记 BLOCKED**（否决「内容采纳」改判，理由有实测）。 |
