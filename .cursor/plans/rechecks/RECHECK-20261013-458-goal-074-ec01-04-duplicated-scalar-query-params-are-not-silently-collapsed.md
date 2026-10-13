---
id: RECHECK-20261013-458
slug: goal-074-ec01-04-duplicated-scalar-query-params-are-not-silently-collapsed
title: 独立复检：GOAL-20261013-074 cycle 1（EC-01…EC-04）—— 标量查询参数重复不再被静默折叠
plan_id: PLAN-20261013-457
status: COMPLETED
result: PASS
created_at: 2026-10-13
completed_at: 2026-10-13
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: services/api/query_param_guard.py（`multi_items()` 计数 + 声明类型导出面）
  - path: 独立重跑判据（重复面 7 例 + 序 37 的 11 例 + 序 40 的 6 例 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261013-074-press-two-way.txt
---

# RECHECK-20261013-458 — GOAL-20261013-074 cycle 1 独立复检

复检对象：`PLAN-20261013-457`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-duplicate-query-params.py` —— 四段读数与 GOAL 表逐条一致：

| # | 事实 | 独立读数 |
| --- | --- | --- |
| 1 | 实跑（改动前） | `/notifications?limit=1&limit=2` ⇒ **200**（静默末值）；`/models?endpoint_id=a&endpoint_id=b` ⇒ 200；`/runs/{id}/events?cursor=a&cursor=b` ⇒ 200 |
| 2 | `list` 声明边界 | `/evaluations/trend?expected_digests` 声明 `list[str] \| None`；web 客户端 `params.append(...)` 循环追加 |
| 3 | 射程清单 | **标量 16 个 / list 1 个**（判别器更正：`anyOf` 里找 `type: array`） |
| 4 | 单值基线 | `/notifications?limit=5` ⇒ 200（两键）；缺省 ⇒ 200（同键） |

### 2. EC-02 重复臂接通（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ **672 passed**；
新模块 `tests/api/test_duplicate_scalar_query_params_are_refused.py` ⇒ **7 passed**。逐条复核：

- **标量重复 ⇒ 422 + 点名 + 明写「accept exactly one value」**（与「未知」措辞分辨）；
- **多个重复逐个点名**（`date_from` / `date_to` 都在）；
- **`list` 声明的重复不被本纪律拒绝**（射程边界）；
- **单值 / 缺省逐字不变**（200 + 两键）；
- **前两面不回归**（未知给 known 清单；未声明给「不接受」措辞）；
- **写面重复同样被拒**（序 41 接通写面后重复臂自动覆盖）；
- **提取面机制判**（`list[...]` 被识别 / 无 endpoint 不推断）。

**★ 实测更正（本轮最关键）**：Starlette 的 `QueryParams.keys()` **去重**
（`?limit=1&limit=2` 的 `keys()` 只出一个）⇒ 计数必须用 `multi_items()`
（首版实现用 `keys()` ⇒ 永远数不到 >1 ⇒ 若照此收口，**按压面会假绿**）。

### 3. EC-03 射程如实（独立重跑）

`pytest tests/contracts tests/tooling -q` ⇒ **2001 passed / 72 skipped**；
`tests/e2e` ⇒ **307 passed / 13 skipped**；**live e2e** ⇒ **53 passed**。

- **三面（序 37/40/41）与写面体（序 39）判据全绿**；
- **快照零 diff**（`tools/gen_openapi.py` 后 `git diff --numstat` ⇒ 空 —— 本轮不动签名）；
- 一处**同轮修**：mypy 真红（`staticmethod` 包装的类型面传 `object`）⇒ 类型面收窄
  （判据语义未变），`2ef490c6` / `23a20c34`。

### 4. EC-04 两向反证（独立重跑）

`uv run --frozen --no-sync python -B scratch/goal074_press.py`：

- **BASELINE（未按压）GREEN**（24 passed）；
- `W5-1`（重复又静默折叠）/ `W5-2`（`list` 声明被误伤）/ `W5-3`（单值形态被改动）/
  `W5-4`（未知面被误伤）⇒ **全 RED，且首跑即全红（无假绿）**；
- `W5-1` 的按压形态 = 退回 `keys()` 计数（**首版实现的真实误**）⇒ 按压面与实现面同源可证；
- 逐条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`；零进程泄漏（实测）；
- 归档 `.cursor/plans/goals/evidence/GOAL-20261013-074-press-two-way.txt`（二进制、`CR=0`）。

## 结论

**PASS**。EC-01…EC-04 各自有独立重跑证据；四向反证全红且字节复原（首跑即全红）；
射程如实（`list` 边界、单值不变、三面不回归、快照零 diff）。
**残余**：作者鉴权 / 三维以上闸门组合 / 无路由路径（404 既有语义）—— 逐条保留在 GOAL 的
「残余与受限面」一节。
**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
