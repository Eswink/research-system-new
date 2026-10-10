---
id: PLAN-20261010-373
slug: goal-043-third-instance-text-anchor-realignment
title: GOAL-20261010-043 收口后补正：第三处文本锚点失配（goal031 字面量搬家）+ 该类机器化
status: DONE
created_at: 2026-10-10
updated_at: 2026-10-10
latest_recheck: .cursor/plans/rechecks/RECHECK-20261010-374-goal-043-third-instance.md
memory_entries: []
parent_goal: GOAL-20261010-043
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261010-043 的残余 `U-2`（「其它历史复检资产的同类脆弱性未普查」）。授权原文见该
    GOAL 的 `authorization.ref`。**本 PLAN 专属边界**：**不重写**任何历史 GOAL 的复检结论；
    受判面**只许等价或更宽**；**改既有判据必须走自证清单**（`MEM-20261009-210`）；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    修 `goal031_closeout_assertions.py` 的第三处**文本锚点失配**（字面量随 GOAL-042 的
    「唯一构造点」重构**搬了家**，行为逐字保持而判据盯错位置）⇒ 改**结构判据**（受判面等价）
    + 把该**类**机器化（断言集在本树**不得有判负**）+ 两向反证。
exit_criteria:
  - id: AC-1
    criterion: >-
      **缺陷实测**：`verify_goal031_closeout.py` 的判词里有 **1 条判负**
      （`ec03-run-completed-carries-the-skip-facts`，其谓词是 `'"skipped"' in runner` 的**文本**要求）；
      而**行为**逐字保持（`run_completion_payload.py` 仍写 `payload["skipped"]`）。
    verify: >-
      `verify_goal031_closeout.py --verdict-only | grep FAIL` ⇒ 1 条；`rg '"skipped"'` 在被引的
      构造点里命中。
    status: PASS
  - id: AC-2
    criterion: >-
      **结构判据修正**：`_run_completed_carries_the_skip_facts` 接受两种形态
      （字面量在原模块 / 载荷由**被调用的构造点**产出），**任一缺 ⇒ 判负**（等价受判面）；
      goal031 验证器转 **0 判负**。
    verify: >-
      `verify_goal031_closeout.py --verdict-only` ⇒ **80 判词 / 0 判负**。
    status: PASS
  - id: AC-3
    criterion: >-
      **该类机器化**：新增 `test_every_named_assertion_set_reports_no_negative_on_this_tree`
      （断言集在本树上**不得有判负**）；**两向**：P-3（把 goal031 改回纯文本）⇒ **必红**。
    verify: >-
      `pytest tests/tooling/test_closeout_verifiers_run_their_own_assertions.py -q` ⇒ **8 passed**；
      P-3 按压红 + 二进制复原 raw `sha256` 一致。
    status: PASS
---

# PLAN-20261010-373 — GOAL-043 收口后补正（第三处文本锚点失配）

> **主线归属**：`GOAL-20261010-043`（MAINLINE 程序表**序 11**）的残余 `U-2`。

## 验收条件

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 缺陷实测（goal031 1 条判负 + 行为逐字保持） | PASS |
| AC-2 | 结构判据修正（goal031 转 0 判负） | PASS |
| AC-3 | 该类机器化（新判据 + P-3 必红） | PASS |

## 实施清单

- [x] WP-1 实测第三处失配（13 个验证器逐个跑 ⇒ 只有 goal031 有判负）
- [x] WP-2 改结构判据（`_run_completed_carries_the_skip_facts`；两种形态）
- [x] WP-3 该类机器化（`test_every_named_assertion_set_reports_no_negative_on_this_tree`）
- [x] WP-4 两向反证（P-3 红 + 二进制复原 raw `sha256` 一致 + 归档更新）

## 证据

| 门 | 读数 |
| --- | --- |
| 缺陷（修正前） | `verify_goal031` **1 条判负**：`ec03-run-completed-carries-the-skip-facts` |
| 修正后 | `verify_goal031` **80 判词 / 0 判负** |
| 全量普查 | **13 个收口验证器全部可执行且 0 判负** |
| 新判据 | `test_closeout_verifiers_run_their_own_assertions.py` **8 passed** |
| 两向反证 | `P-3` **红**；二进制复原 raw `sha256` 一致；归档 `GOAL-20261010-043-press-two-way.txt`（165 B / `CR=0`） |

## 改既有判据的申报（承 `MEM-20261009-210`）

| 文件 | 改动 | 谓词比对 | `numstat` |
| --- | --- | --- | --- |
| `tools/goal031_closeout_assertions.py` | 文本谓词 ⇒ **结构判据** + 助手 | **等价**（同一件事：载荷带 `skipped` 键；两种形态任一缺 ⇒ 判负） | 见 RECHECK |
| `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` | **新增**一条判据（该类机器化） | — | 见 RECHECK |

## 影响报告

- **Domain / API / schema 变化**：零。**安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：无（历史 GOAL 的终态与结论**未触碰**）。**上游版本影响**：无。
- **下一项任务**：无（序 11 已收口；`U-1`/`U-3` 仍登记）。

## 无可复用事实

本 cycle 的发现与修法已由 `MEM-20261010-212`（复检资产必须跑自己的断言）承载 ——
本 PLAN **不**新增第二条记忆（同一族事实，避免重复条目）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-10 | IN_PROGRESS | 第三处失配实测 + 结构判据修正 + 该类机器化 + P-3 按压红。 |
| 2026-10-10 | DONE | goal031 80 判词 / 0 判负；13 个验证器全绿；`RECHECK-20261010-374` 独立复检。 |
