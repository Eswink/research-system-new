---
id: PLAN-20261012-433
slug: goal-062-ec01-05-a-conflict-declaration-is-no-longer-one-way
title: GOAL-20261012-062 cycle 1（EC-01…EC-05）：反向链接可读 + 处置面分派 + 两向反证
status: IN_PROGRESS
created_at: 2026-10-12
updated_at: 2026-10-12
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261012-062
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261012-062 的 **EC-01…EC-05**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只加**反向链接**（被声明方读得出谁声明了与它冲突）与它在
    **处置面**的分派；`contradictions` 的**声明**语义与**正向**读法**一字不动**；
    **不**做自动消解 / **不**做自动失效 / **不**做内容级语义比较；缺省形态**逐字不变**；
    新判据**两向实测**、反证脚本**带基线门**；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**冲突声明的被声明方**也读得出：① 勘察定稿（反向面零命中 + 实跑缺口 + 先例 +
    正向读法未动，EC-01）→ ② 反向链接与分派（被声明方逐条披露 + 处置同类不同因；
    缺省逐字不变；跨范围点名）（EC-02）→ ③ 两读面同源 + 既有键逐字不变 + 快照同轮（EC-03）→
    ④ 两向反证 `Y-1`…`Y-4` 全红（EC-04）→ ⑤ 自举收口（EC-05）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-reverse-conflict.py` 逐条读出 ——
      ① 反向面**零命中**（四组候选标识符 × 三个产品根）；② **实跑**：A 声明与 B 冲突 ⇒
      A 侧 `CONFLICTED` / **B 侧 `contradictions=[]` 且无反向键、`disposition=USE`**；
      ③ 先例 `superseded_by_index` 的形态逐条读出；④ 两个读面的 `contradictions` 读法
      **逐字仍是一向**。`git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-reverse-conflict.py`；
      GOAL 的「事实层结论」表逐行与实测对齐。
    status: PENDING
  - id: WP-2
    criterion: >-
      **反向链接与分派（EC-02）**：新增反向索引（**扫同批记录**，与序 18 同一手法）；
      被声明方读面**逐条披露**（谁是声明方）；处置面据此分派（**同类不同因**：判词点得出
      「**是谁**声明了与它冲突」）；**缺省形态逐字不变**；跨范围（看不见 ≠ 不存在）**点名**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application tests/domain -q` ⇒ 全绿
      + 新用例（反向可读 / 缺省逐字不变 / 跨范围不猜）。
    status: PENDING
  - id: WP-3
    criterion: >-
      **两读面同源（EC-03）**：编排面与 HTTP 读面**同源**（同一批纯函数）披露反向链接；
      **既有键逐字不变**（`contradictions` 语义一字不改）；动 DTO ⇒ **同轮**重生成并提交
      `docs/api/openapi.m13.json`（+ `apps/web/src/api/types.ts` 若本轮触及）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/adapters tests/contracts -q`
      ⇒ 全绿 + 新用例（两处同值 / 既有键逐字不变 / 快照含新键）。
    status: PENDING
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`Y-1` 反向链接被摘掉 ⇒ RED；`Y-2` 处置面**不**按反向分派 ⇒ RED；
      `Y-3` **缺省形态**被改动 ⇒ RED；`Y-4` 跨范围被当成同批 ⇒ RED。基线门 GREEN；
      复原用二进制读写 + raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal062_press.py` ⇒ 全 `RED` +
      `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PENDING
  - id: WP-5
    criterion: >-
      **自举收口（EC-05）**：收口验证器 + 断言集进树（`IN_SCOPE` 纯收紧 + 射程清单）；
      两树复检 `TWO-TREE PASS` + 判词归档（二进制写盘 / `CR=0`）；as-is m0 **23/23**
      （记录写完之后）；治理 + 宪章判据绿；CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal062_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PENDING
---

# PLAN-20261012-433 — GOAL-20261012-062 cycle 1

## 背景

`GOAL-20261012-062`（MAINLINE 程序表**序 30**，轴 = 质量）。**实测起点**：
`contradictions` 是**单方向**的声明 —— A 声明与 B 冲突 ⇒ **B 那侧读不出来**；
**实跑**：B 的 `contradictions=[]`、**无**反向键，且 `disposition=USE`（照用）
⇒ **一条被别人声明冲突的记忆照样进下一步**；而序 18 的 `superseded_by_index`
就是同族的**反向索引**解法（正向链接写在新记录上 ⇒ 必须扫同批记录）。

## 验收条件

| EC | 判据 | 证据 |
| --- | --- | --- |
| EC-01 | 四段读数（零命中 + 实跑缺口 + 先例 + 正向未动）（WP-1） | `scratch/probe-reverse-conflict.py` |
| EC-02 | 反向链接可读 + 处置分派 + 缺省逐字不变（WP-2） | `pytest tests/application tests/domain -q` |
| EC-03 | 两读面同源 + 既有键逐字不变 + 快照同轮（WP-3） | `pytest tests/api tests/adapters tests/contracts -q` |
| EC-04 | 四向反证全红 + 基线门 + `sha256` 复原（WP-4） | 归档判词（`CR=0`） |
| EC-05 | 自举收口（WP-5） | 验证器全 `PASS` + 两树 + m0 23/23 |

## 实施清单

1. **WP-1**：定稿探针（只读；四段读数）。
2. **WP-2**：反向索引 + 处置面分派 + 跨范围点名。
3. **WP-3**：两读面同源披露 + 快照同轮。
4. **WP-4**：按压脚本（四条）+ 基线门 + 归档。
5. **WP-5**：收口验证器 + 断言集 + 两树 + m0 + 治理 + 台账。

## 证据

（逐 WP 回填：命令 + 读数 + commit。）

## 影响报告

- **Domain / API / schema 变化**：（EC-02 回填：反向索引；EC-03 回填：读面键 + 快照）
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：（EC-02 回填：纯附加披露 ⇒ 既有数据逐字不变）
- **上游版本影响**：无。
- **下一项任务**：按 EC 顺序推进。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-12 | IN_PROGRESS | cycle 1 建档：反向链接 + 处置分派 + 四向反证。 |
