---
id: PLAN-20261014-459
slug: goal-075-ec01-05-empty-values-for-declared-params-are-not-silently-treated-as-filters
title: GOAL-20261014-075 cycle 1（EC-01…EC-05）：空值形态点名拒绝 + 两向反证
status: DONE
created_at: 2026-10-14
updated_at: 2026-10-14
latest_recheck: .cursor/plans/rechecks/RECHECK-20261014-460-goal-075-ec01-04-empty-values-for-declared-params-are-not-silently-treated-as-filters.md
memory_entries: []
parent_goal: GOAL-20261014-075
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261014-075 的 **EC-01…EC-05**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只给守卫**新增空值臂**（**已声明**参数空值 ⇒ 422 + 点名 +
    明写「不接受空值」）；**`list` 声明**与**缺省（不传）**形态**一字不动**；
    前四面（序 37/40/41/42）**不回归**；新判据**两向实测**、反证脚本**带基线门**；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**已声明参数的空值**形态**不再被静默当成筛选值**：① 勘察定稿（空值两行为 + 射程清单 +
    影响面 + 缺省基线，EC-01）→ ② 空值臂（422 + 逐个点名 + 明写「不接受空值」；缺省与 list
    逐字不变）（EC-02）→ ③ **射程如实**（四面 + 写面体 + 事件流不回归）+ live e2e + 快照同轮
    （**预期零 diff**）（EC-03）→ ④ 两向反证 `V5-1`…`V5-4` 全红（EC-04）→ ⑤ 自举收口（EC-05）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-empty-query-values.py` 逐条读出 ——
      ① 空值**两行为**逐条点名（静默筛 0 vs 422）；② 射程清单（已声明参数给空值的现行为）；
      ③ 影响面（web/tests 是否发空值 —— 实测 web 已挡）；④ 缺省基线（状态码 + 关键键）。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-empty-query-values.py`；
      GOAL 的「事实层结论」表逐行与实测对齐。
    status: PASS
  - id: WP-2
    criterion: >-
      **空值臂（EC-02）**：已声明参数空值 ⇒ **422 + 逐个点名 + 明写「不接受空值」**
      （与「未知」「重复」**三分辨**）；缺省与 `list` 逐字不变。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿
      + 新用例（空值点名 / 多个逐个 / 缺省不变 / 三臂措辞分辨）。
    status: PASS
  - id: WP-3
    criterion: >-
      **射程如实 + 无回归（EC-03）**：四面（序 37/40/41/42）+ 写面体（序 39）+ 事件流（序 38）
      判据全绿；**live e2e** 全绿；快照同轮（**预期零 diff**）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts tests/tooling -q`
      ⇒ 全绿 + `pnpm --dir apps/web test:e2e:live` ⇒ 全绿。
    status: PASS
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`V5-1` 空值又被静默当成筛选值 ⇒ RED；`V5-2` `list` 声明被误伤 ⇒ RED；
      `V5-3` 缺省形态被改动 ⇒ RED；`V5-4` 重复臂被误伤 ⇒ RED。基线门 GREEN；
      复原用二进制读写 + raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal075_press.py` ⇒ 全 `RED` +
      `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PASS
  - id: WP-5
    criterion: >-
      **自举收口（EC-05）**：收口验证器 + 断言集进树（`IN_SCOPE` 纯收紧 + 射程清单）；
      两树复检 `TWO-TREE PASS` + 判词归档（二进制写盘 / `CR=0`）；as-is m0 **23/23**
      （记录写完之后）；治理 + 宪章判据绿；CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal075_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PASS
---

# PLAN-20261014-459 — GOAL-20261014-075 cycle 1

## 背景

`GOAL-20261014-075`（MAINLINE 程序表**序 43**，轴 = 质量）。**实测起点**：
前四面（未知 / 未声明 / 写面 / 重复）已接通，而**空值**形态**各路由不一致**
（`?scope=` 静默筛 0 条 vs `?at=` 422）⇒ 调用方**读不出**「我给空了」还是「确实没匹配」。

## 验收条件

| EC | 判据 | 证据 |
| --- | --- | --- |
| EC-01 | 四段读数（空值两行为 / 射程清单 / 影响面 / 缺省基线）（WP-1） | `scratch/probe-empty-query-values.py` |
| EC-02 | 空值 422 + 逐个点名；缺省与 list 逐字不变（WP-2） | `pytest tests/api -q` |
| EC-03 | 射程如实（四面 / 写面体 / 事件流不回归）+ live + 快照同轮（WP-3） | `pytest ...` + live |
| EC-04 | 四向反证全红 + 基线门 + `sha256` 复原（WP-4） | 归档判词（`CR=0`） |
| EC-05 | 自举收口（WP-5） | 验证器全 `PASS` + 两树 + m0 23/23 |

## 实施清单

1. **WP-1**：定稿探针（只读；四段读数）。
2. **WP-2**：守卫新增空值臂（共享守卫一处声明）。
3. **WP-3**：四面 / 写面体 / 事件流回归 + live e2e + 快照同轮。
4. **WP-4**：按压脚本（四条）+ 基线门 + 归档。
5. **WP-5**：收口验证器 + 断言集 + 两树 + m0 + 治理 + 台账。

## 证据

| WP | 命令 | 读数 | commit |
| --- | --- | --- | --- |
| WP-1 | `uv run --frozen --no-sync python -B scratch/probe-empty-query-values.py` | `?scope=` ⇒ 200 且 `records: []`（载荷含 `filtered_out` ⇒ 走「筛」支）；`?at=` / `?kind=` ⇒ 422；**分界 = 类型面**（str 型静默 / 校验型拒绝：`endpoint_id` 200 vs `limit`/`date_from`/`horizon_days` 422）；web 已挡空值（`!== ""`）；缺省基线 | （本轮） |
| WP-2 | `pytest tests/api -q` | **672 passed**（新 6 例）；空值臂落地（措辞三分辨） | `2e195bf3` |
| WP-3 | `pytest tests/api tests/contracts tests/tooling -q` + `tests/e2e` + **live e2e** | 2680 + 307 + **53 passed**；快照 `git diff --numstat` ⇒ **零 diff** | `2e195bf3` |
| WP-4 | `uv run --frozen --no-sync python -B scratch/goal075_press.py` | **BASELINE GREEN**（30 passed）；V5-1/V5-2/V5-3/V5-4 全 **RED**；逐条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`；**两条锚点首跑未命中**（缩进 / 非唯一）⇒ 按纪律改唯一锚点后全红；归档 `evidence/GOAL-20261014-075-press-two-way.txt`（二进制、`CR=0`）；零进程泄漏 | （本轮） |

## 影响报告

- **Domain / API / schema 变化**：（EC-02 回填）请求处理链的校验面 —— 不动签名
  ⇒ 快照**预期零 diff**；**无迁移**。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：（EC-02 回填：只拒绝**空值** ⇒ 缺省调用与 web 客户端
  （已挡空值）逐字不变；依赖旧「空值当筛选」语义的调用按 EC-01 ③ 逐条处理）
- **上游版本影响**：无。
- **下一项任务**：按 EC 顺序推进。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-14 | IN_PROGRESS | cycle 1 建档：空值形态点名拒绝 + 四向反证。 |
