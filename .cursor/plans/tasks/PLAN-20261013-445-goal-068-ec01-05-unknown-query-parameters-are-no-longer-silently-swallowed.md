---
id: PLAN-20261013-445
slug: goal-068-ec01-05-unknown-query-parameters-are-no-longer-silently-swallowed
title: GOAL-20261013-068 cycle 1（EC-01…EC-05）：未知参数点名拒绝（射程两个 GET）+ 两向反证
status: DONE
created_at: 2026-10-13
updated_at: 2026-10-13
latest_recheck: .cursor/plans/rechecks/RECHECK-20261013-446-goal-068-ec01-04-unknown-query-parameters-are-no-longer-silently-swallowed.md
memory_entries: []
parent_goal: GOAL-20261013-068
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261013-068 的 **EC-01…EC-05**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只让**记忆读面的两个 GET** 对**未知查询参数**点名拒绝；
    **已知**参数（`?scope=` / `?proposed_by=` / `?at=`）与**缺省**形态**一字不动**；
    **不**做全仓未知参数拒绝 / **不**改写面 / **不**做模糊匹配；新判据**两向实测**、
    反证脚本**带基线门**；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**未知查询参数不再被静默吞掉**（记忆读面）：① 勘察定稿（实跑 + 对照 + 零命中 +
    射程逐个 + 全仓计数，EC-01）→ ② 未知参数**点名拒绝**（422 + 点进正文；多个逐个；
    已知与缺省逐字不变）（EC-02）→ ③ **射程如实**（对照组逐条仍照旧）+ 快照同轮（EC-03）→
    ④ 两向反证 `Z-1`…`Z-4` 全红（EC-04）→ ⑤ 自举收口（EC-05）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-unknown-query-param.py` 逐条读出 ——
      ① 实跑（未知 ⇒ 200 + 无披露）；② 对照（已知 ⇒ 筛 + 披露）；③ 零命中；
      ④ 射程逐个（两个 GET）；⑤ 全仓 GET 计数（65 —— 「不做全仓」是**有意边界**）。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-unknown-query-param.py`；
      GOAL 的「事实层结论」表逐行与实测对齐。
    status: PASS
  - id: WP-2
    criterion: >-
      **未知参数点名拒绝（EC-02）**：两个 GET 对未知查询参数 ⇒ **422 + 正文点名**；
      **多个未知逐个点名**；**已知**参数与**缺省**形态**逐字不变**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿
      + 新用例（未知点名 / 多个逐个 / 已知不变 / 缺省不变）。
    status: PASS
  - id: WP-3
    criterion: >-
      **射程如实（EC-03）**：**只**那两个 GET 受此纪律；**对照组**（其余路由**逐条读出**）
      仍照旧；既有读面键一字不动；若动 DTO ⇒ **同轮**重生成并提交
      `docs/api/openapi.m13.json`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts -q` ⇒ 全绿
      + 新用例（对照组）。
    status: PASS
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`Z-1` 未知参数被忽略 ⇒ RED；`Z-2` 已知参数被误拒 ⇒ RED；
      `Z-3` 缺省形态被改动 ⇒ RED；`Z-4` 多个未知只报第一个 ⇒ RED。基线门 GREEN；
      复原用二进制读写 + raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal068_press.py` ⇒ 全 `RED` +
      `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PASS
  - id: WP-5
    criterion: >-
      **自举收口（EC-05）**：收口验证器 + 断言集进树（`IN_SCOPE` 纯收紧 + 射程清单）；
      两树复检 `TWO-TREE PASS` + 判词归档（二进制写盘 / `CR=0`）；as-is m0 **23/23**
      （记录写完之后）；治理 + 宪章判据绿；CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal068_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PASS
---

# PLAN-20261013-445 — GOAL-20261013-068 cycle 1

## 背景

`GOAL-20261013-068`（MAINLINE 程序表**序 36**，轴 = 质量）。**实测起点**：
序 35 让**名字对的**参数通到了 Port，而**打错名字的**参数**照样 200 + 全量**
（**实跑**：`?definitely_not_a_param=1` ⇒ 200 + 键仍只有 `['records','scope_note']`）
⇒ 调用方**以为筛过了**；**对照**已知参数会筛并披露其键。

## 验收条件

| EC | 判据 | 证据 |
| --- | --- | --- |
| EC-01 | 五段读数（实跑 / 对照 / 零命中 / 射程 / 全仓计数）（WP-1） | `scratch/probe-unknown-query-param.py` |
| EC-02 | 未知参数点名拒绝 + 多个逐个 + 已知与缺省逐字不变（WP-2） | `pytest tests/api -q` |
| EC-03 | 射程如实（对照组照旧）+ 快照同轮（WP-3） | `pytest tests/api tests/contracts -q` |
| EC-04 | 四向反证全红 + 基线门 + `sha256` 复原（WP-4） | 归档判词（`CR=0`） |
| EC-05 | 自举收口（WP-5） | 验证器全 `PASS` + 两树 + m0 23/23 |

## 实施清单

1. **WP-1**：定稿探针（只读；五段读数）。
2. **WP-2**：两个 GET 的未知参数拒绝（422 + 点名；多个逐个）。
3. **WP-3**：射程对照组判据 + 快照同轮（若动 DTO）。
4. **WP-4**：按压脚本（四条）+ 基线门 + 归档。
5. **WP-5**：收口验证器 + 断言集 + 两树 + m0 + 治理 + 台账。

## 证据

（逐 WP 回填：命令 + 读数 + commit。）

## 影响报告

- **Domain / API / schema 变化**：（EC-02 回填：读面参数校验面）——**无迁移**。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：（EC-02 回填：只拒绝**未知**参数 ⇒ 既有调用逐字不变）
- **上游版本影响**：无。
- **下一项任务**：按 EC 顺序推进。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-13 | IN_PROGRESS | cycle 1 建档：未知参数点名拒绝（射程两个 GET）+ 四向反证。 |
| 2026-10-13 | DONE | cycle 1 收口：WP-1…WP-5 全 PASS（独立复检 `RECHECK-20261013-446` = PASS_WITH_WARNINGS）。**交付**：`_reject_unknown_query_params` 守卫 + 已知集常量 + 两个 GET 接线；判据 8 例；四向反证全红 + 归档（`CR=0`）。 |
