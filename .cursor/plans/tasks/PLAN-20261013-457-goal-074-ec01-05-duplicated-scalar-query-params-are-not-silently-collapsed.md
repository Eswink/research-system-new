---
id: PLAN-20261013-457
slug: goal-074-ec01-05-duplicated-scalar-query-params-are-not-silently-collapsed
title: GOAL-20261013-074 cycle 1（EC-01…EC-05）：标量查询参数重复点名拒绝 + 两向反证
status: IN_PROGRESS
created_at: 2026-10-13
updated_at: 2026-10-13
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261013-074
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261013-074 的 **EC-01…EC-05**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只给守卫**新增一臂**（**标量声明**的参数重复 ⇒ 422 + 点名 +
    明写「只接受一个值」）；**`list` 声明**的参数**一字不动**（web 合法重复）；
    未知 / 未声明 / 写面三面（序 37/40/41）**不回归**；单值 / 缺省形态**逐字不变**；
    新判据**两向实测**、反证脚本**带基线门**；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**标量声明的查询参数重复出现**时**不再被静默折叠**：① 勘察定稿（重复实跑 + list 边界 +
    标量清单 + 单值基线，EC-01）→ ② 守卫新增重复臂（422 + 逐个点名 + 明写「只接受一个值」；
    list 与单值逐字不变）（EC-02）→ ③ **射程如实**（三面 + 写面体 + 事件流不回归）+
    live e2e + 快照同轮（**预期零 diff**）（EC-03）→ ④ 两向反证 `W5-1`…`W5-4` 全红（EC-04）→
    ⑤ 自举收口（EC-05）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-duplicate-query-params.py` 逐条读出 ——
      ① 实跑：标量参数重复 ⇒ **200 + 末值生效**（≥2 条路由，含序 38 的 `cursor`）；
      ② list 声明确认（`expected_digests` ⇒ 重复**合法**，web 客户端循环追加）；
      ③ 标量声明的查询参数**逐条清单**；④ 单值基线（状态码 + 关键键）。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-duplicate-query-params.py`；
      GOAL 的「事实层结论」表逐行与实测对齐。
    status: PENDING
  - id: WP-2
    criterion: >-
      **重复臂（EC-02）**：标量参数重复 ⇒ **422 + 逐个点名 + 明写「只接受一个值」**；
      `list` 声明**一字不动**；单值 / 缺省逐字不变。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿
      + 新用例（标量重复点名 / 多个逐个 / list 不回归 / 单值不变）。
    status: PENDING
  - id: WP-3
    criterion: >-
      **射程如实 + 无回归（EC-03）**：三面（序 37/40/41）+ 写面体（序 39）+ 事件流（序 38）
      判据全绿；**live e2e** 全绿；快照同轮（**预期零 diff**）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts tests/tooling -q`
      ⇒ 全绿 + `pnpm --dir apps/web test:e2e:live` ⇒ 全绿。
    status: PENDING
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`W5-1` 重复又静默折叠 ⇒ RED；`W5-2` list 声明被误伤 ⇒ RED；
      `W5-3` 单值形态被改动 ⇒ RED；`W5-4` 未知面被误伤（序 37 靶子回退）⇒ RED。
      基线门 GREEN；复原用二进制读写 + raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal074_press.py` ⇒ 全 `RED` +
      `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PENDING
  - id: WP-5
    criterion: >-
      **自举收口（EC-05）**：收口验证器 + 断言集进树（`IN_SCOPE` 纯收紧 + 射程清单）；
      两树复检 `TWO-TREE PASS` + 判词归档（二进制写盘 / `CR=0`）；as-is m0 **23/23**
      （记录写完之后）；治理 + 宪章判据绿；CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal074_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PENDING
---

# PLAN-20261013-457 — GOAL-20261013-074 cycle 1

## 背景

`GOAL-20261013-074`（MAINLINE 程序表**序 42**，轴 = 质量）。**实测起点**：
三面（未知 / 未声明 / 写面）已接通，而**同名参数重复出现**时框架**静默取末值**
（`?limit=1&limit=2` ⇒ 200，无披露）—— 且射程**必须**按声明类型分
（`expected_digests` 是 `list[str]`，web 客户端合法重复）。

## 验收条件

| EC | 判据 | 证据 |
| --- | --- | --- |
| EC-01 | 四段读数（重复实跑 / list 边界 / 标量清单 / 单值基线）（WP-1） | `scratch/probe-duplicate-query-params.py` |
| EC-02 | 标量重复 422 + 逐个点名；list 与单值逐字不变（WP-2） | `pytest tests/api -q` |
| EC-03 | 射程如实（三面 / 写面体 / 事件流不回归）+ live + 快照同轮（WP-3） | `pytest ...` + live |
| EC-04 | 四向反证全红 + 基线门 + `sha256` 复原（WP-4） | 归档判词（`CR=0`） |
| EC-05 | 自举收口（WP-5） | 验证器全 `PASS` + 两树 + m0 23/23 |

## 实施清单

1. **WP-1**：定稿探针（只读；四段读数）。
2. **WP-2**：守卫新增重复臂（共享守卫一处声明）。
3. **WP-3**：三面 / 写面体 / 事件流回归 + live e2e + 快照同轮。
4. **WP-4**：按压脚本（四条）+ 基线门 + 归档。
5. **WP-5**：收口验证器 + 断言集 + 两树 + m0 + 治理 + 台账。

## 证据

| WP | 命令 | 读数 | commit |
| --- | --- | --- | --- |
| WP-1 | `uv run --frozen --no-sync python -B scratch/probe-duplicate-query-params.py` | `?limit=1&limit=2` ⇒ **200**（静默末值）；`?endpoint_id=a&endpoint_id=b` ⇒ 200；序 38 的 `?cursor=a&cursor=b` ⇒ 200；**标量 16 个 / list 1 个**（判别器更正：`list[str] \| None` 是 `anyOf` ⇒ 只看顶层 type 会误判，首版探针已修）；单值基线（200 + 两键） | （本轮） |
| WP-2 | `pytest tests/api -q` | **672 passed**（新 7 例）；**★ 实测更正**：`QueryParams.keys()` **去重** ⇒ 计数必须用 `multi_items()`（首版用 keys() ⇒ 永远数不到重复）；射程由**签名注解**导出（`list[...]` 判型；本版 FastAPI 的 ModelField 类型面全 None）；序 37 判据抓到我 docstring 里的示例字样 ⇒ 改写措辞（判据意图未动） | `2ef490c6` |
| WP-3 | `pytest tests/contracts tests/tooling -q` + `tests/e2e` + **live e2e** | 2001 + 307 + **53 passed**；快照 `git diff --numstat` ⇒ **零 diff** | `2ef490c6` / `23a20c34` |
| WP-4 | `uv run --frozen --no-sync python -B scratch/goal074_press.py` | **BASELINE GREEN**（24 passed）；W5-1/W5-2/W5-3/W5-4 全 **RED**（**首跑即全红**）；逐条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`；归档 `evidence/GOAL-20261013-074-press-two-way.txt`（二进制、`CR=0`）；零进程泄漏 | （本轮） |

## 影响报告

- **Domain / API / schema 变化**：（EC-02 回填）请求处理链的校验面 —— 不动签名
  ⇒ 快照**预期零 diff**；**无迁移**。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：（EC-02 回填：只拒绝**标量参数的重复** ⇒ 单值调用与
  `list` 声明的重复调用逐字不变；依赖旧折叠语义的调用按 EC-01 ③ 逐条处理）
- **上游版本影响**：无。
- **下一项任务**：按 EC 顺序推进。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-13 | IN_PROGRESS | cycle 1 建档：标量查询参数重复点名拒绝 + 四向反证。 |
