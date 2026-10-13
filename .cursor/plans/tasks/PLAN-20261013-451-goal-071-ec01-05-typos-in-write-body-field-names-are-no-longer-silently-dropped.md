---
id: PLAN-20261013-451
slug: goal-071-ec01-05-typos-in-write-body-field-names-are-no-longer-silently-dropped
title: GOAL-20261013-071 cycle 1（EC-01…EC-05）：写面未知字段点名拒绝 + 两向反证
status: DONE
created_at: 2026-10-13
updated_at: 2026-10-13
latest_recheck: .cursor/plans/rechecks/RECHECK-20261013-452-goal-071-ec01-04-typos-in-write-body-field-names-are-no-longer-silently-dropped.md
memory_entries: []
parent_goal: GOAL-20261013-071
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261013-071 的 **EC-01…EC-05**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只给**已声明的写面 DTO** 加「未知字段 ⇒ 422 + 点名」；
    **不**动查询参数面 / 响应模型 / 未声明路由；已知与缺省形态**逐字不变**；
    落地前先做**影响面盘点**（web/tests 有没有带多余字段的写调用）；新判据**两向实测**、
    反证脚本**带基线门**；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让写面请求体里打错的字段名**不再被静默吞掉**：① 勘察定稿（实跑缺口 + 写面 DTO 清单 +
    影响面盘点 + 正确形态基线，EC-01）→ ② 未知字段 422 + 逐个点名（做法由 EC-01 定；
    已知/缺省逐字不变）（EC-02）→ ③ **射程如实**（查询参数面不回归）+ 快照同轮
    （**预期会变**）（EC-03）→ ④ 两向反证 `X-1`…`X-4` 全红（EC-04）→ ⑤ 自举收口（EC-05）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-write-face-extra-fields.py` 逐条读出 ——
      ① 实跑：打错字段名 ⇒ **200 + 无声丢弃**（附正确形态对照）；② 写面 DTO **逐条清单**
      （文件 + 类名 + `extra` 现状）；③ **影响面盘点**：web/tests 里带**非声明字段**的写请求
      （有 ⇒ 逐条点名）；④ 正确形态基线（状态码 + 关键键，供逐字比对）。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-write-face-extra-fields.py`；
      GOAL 的「事实层结论」表逐行与实测对齐。
    status: PASS
  - id: WP-2
    criterion: >-
      **写面纪律（EC-02）**：未知字段 ⇒ **422 + 点名那个字段**（多个**逐个**）；
      **已知/缺省形态逐字不变**（对照 EC-01 ④ 基线）；盘点面发现逐条处置。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿
      + 新用例（逐 DTO 点名 / 多个逐个 / 已知不变 / 缺省不变）。
    status: PASS
  - id: WP-3
    criterion: >-
      **射程如实 + 无回归（EC-03）**：查询参数面（序 37/38 判据）不回归；正确请求的
      响应与副作用逐字不变；快照**同轮**重生成并提交（**预期会变**）；web 侧既有调用全绿。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts tests/tooling -q`
      ⇒ 全绿 + 快照 diff 与声明面一致。
    status: PASS
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`X-1` 未知字段又被静默忽略 ⇒ RED；`X-2` 已知字段被误拒 ⇒ RED；
      `X-3` 多个未知只报第一个 ⇒ RED；`X-4` 正文不点名 ⇒ RED。基线门 GREEN；
      复原用二进制读写 + raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal071_press.py` ⇒ 全 `RED` +
      `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PASS
  - id: WP-5
    criterion: >-
      **自举收口（EC-05）**：收口验证器 + 断言集进树（`IN_SCOPE` 纯收紧 + 射程清单）；
      两树复检 `TWO-TREE PASS` + 判词归档（二进制写盘 / `CR=0`）；as-is m0 **23/23**
      （记录写完之后）；治理 + 宪章判据绿；CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal071_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PASS
---

# PLAN-20261013-451 — GOAL-20261013-071 cycle 1

## 背景

`GOAL-20261013-071`（MAINLINE 程序表**序 39**，轴 = 质量）。**实测起点**：
序 36/37/38 把「未知查询参数」的纪律做成两条读面事实，而**写面**（POST/PUT 的 JSON 体）
打错字段名**照样 200 + 无声丢弃**（实测 `{"protocol_path": …, "trace_di": "typo"}` ⇒ 200）
⇒ 调用方**以为设了那个字段**。本轮把同一纪律**扩到写面**。

## 验收条件

| EC | 判据 | 证据 |
| --- | --- | --- |
| EC-01 | 四段读数（实跑 / DTO 清单 / 影响面盘点 / 正确形态基线）（WP-1） | `scratch/probe-write-face-extra-fields.py` |
| EC-02 | 未知字段 422 + 逐个点名；已知/缺省逐字不变（WP-2） | `pytest tests/api -q` |
| EC-03 | 射程如实（查询参数面不回归）+ 快照同轮（预期变）（WP-3） | `pytest tests/api tests/contracts tests/tooling -q` |
| EC-04 | 四向反证全红 + 基线门 + `sha256` 复原（WP-4） | 归档判词（`CR=0`） |
| EC-05 | 自举收口（WP-5） | 验证器全 `PASS` + 两树 + m0 23/23 |

## 实施清单

1. **WP-1**：定稿探针（只读；四段读数；影响面盘点必须**先**做）。
2. **WP-2**：写面未知字段点名拒绝（做法由 EC-01 定）。
3. **WP-3**：查询参数面回归 + 快照重生成（预期变）+ web 面。
4. **WP-4**：按压脚本（四条）+ 基线门 + 归档。
5. **WP-5**：收口验证器 + 断言集 + 两树 + m0 + 治理 + 台账。

## 证据

| WP | 命令 | 读数 | commit |
| --- | --- | --- | --- |
| WP-1 | `uv run --frozen --no-sync python -B scratch/probe-write-face-extra-fields.py` | 打错字段名 ⇒ **200**（静默吞掉）；正确形态 200 + 15 键；**37 条请求 DTO**（零 `extra=` 设定）；`extra="forbid"` 对照实验 ⇒ 422 且字段名在 `loc` 里；影响面上界 357 调用点（如实登记口径） | （本轮） |
| WP-2 | `pytest tests/api -q` | **647 passed**（新 6 例）；3 处既有调用带多余字段（`POST /projects` 传 `id`）⇒ 逐条修正调用点（断言未动） | `9e868fb0` |
| WP-3 | `pytest tests/contracts tests/tooling -q` + `tests/e2e` | 1998 passed / 72 skipped；e2e **一次组合跑 flake**（隔离与重跑全绿：307 passed）；快照 `git diff --numstat` ⇒ **零 diff**（**实测更正 D-4**：生成器早已强制补写 `additionalProperties: false` ⇒ 契约早就声明闭包，变的是运行时） | `9e868fb0` |
| WP-4 | `uv run --frozen --no-sync python -B scratch/goal071_press.py` | **BASELINE GREEN**（17 passed）；X-1/X-2/X-3/X-4 全 **RED**；逐条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`；**X-2 首跑 GREEN ⇒ 判据面缺口**（只判拒绝 ⇒ 拒绝面过宽假绿）⇒ 补正确形态断言后 RED（同签名 1 次，未超上限）；归档 `evidence/GOAL-20261013-071-press-two-way.txt`（二进制、`CR=0`）；零进程泄漏 | （本轮） |

## 影响报告

- **Domain / API / schema 变化**：（EC-02 回填）写面 DTO 校验形态 + OpenAPI（**预期**）
  —— **无迁移**。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：（EC-02 回填：只拒绝**未知**字段 ⇒ 正确调用逐字不变；
  依赖「多余字段被忽略」的既有调用按 EC-01 ③ 盘点逐条处置）
- **上游版本影响**：无。
- **下一项任务**：按 EC 顺序推进。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-13 | IN_PROGRESS | cycle 1 建档：写面未知字段点名拒绝 + 四向反证。 |
