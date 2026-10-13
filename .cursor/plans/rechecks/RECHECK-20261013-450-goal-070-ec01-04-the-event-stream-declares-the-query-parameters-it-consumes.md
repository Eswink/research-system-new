---
id: RECHECK-20261013-450
slug: goal-070-ec01-04-the-event-stream-declares-the-query-parameters-it-consumes
title: 独立复检：GOAL-20261013-070 cycle 1（EC-01…EC-04）—— 事件流路由声明它消费的查询参数
plan_id: PLAN-20261013-449
status: COMPLETED
result: PASS
created_at: 2026-10-13
completed_at: 2026-10-13
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: services/api/routers/run_events.py（`Query(` 声明 cursor/poll）
  - path: 独立重跑判据（事件流 7 例 + 序 37 全员覆盖 11 例 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261013-070-press-two-way.txt
---

# RECHECK-20261013-450 — GOAL-20261013-070 cycle 1 独立复检

复检对象：`PLAN-20261013-449`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-event-stream-params.py` —— 五段读数与 GOAL 表逐条一致：

| # | 事实 | 独立读数 |
| --- | --- | --- |
| 1 | 消费却不声明的路由 | **唯一** = `services/api/routers/run_events.py`（差集扫描，守卫模块除外） |
| 2 | OpenAPI 声明面 | `/runs/{run_id}/events` 的 `parameters[in=query]` = `[]`（改动前） |
| 3 | 实跑静默吞掉 | `?po11=0` ⇒ **200**；`?nonsense=1` ⇒ **200**（JSON replay 有界） |
| 4 | SSE 语义危害 | 打错 `poll` ⇒ 默认 `poll=1` ⇒ **保持轮询**（探针须 `timeout` 收口） |
| 5 | 正确形态基线 | `?poll=0` 有界 200；`?cursor=zzz` 裁剪 0 条；`Last-Event-ID` 头 200 |

### 2. EC-02 声明出来（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ **647 passed**；
新模块 `tests/api/test_event_stream_declares_query_parameters.py` ⇒ **7 passed**。逐条复核：

- 签名**声明**两个参数（OpenAPI `parameters[in=query]` = `["cursor", "poll"]`）；
- **声明缺省被钉**（`poll` schema `default == "1"`；`cursor` 无缺省）—— 这是 `V-2`
  首跑假绿抓出的缺口补丁；
- **守卫自动接管**：`?po11=0` ⇒ 422 点名（`known: cursor, poll`）；`?nonsense=1` ⇒ 422；
- **正确形态逐字**：`?poll=0` 有界快照（`text/event-stream` + 帧）；`?cursor=zzz` 裁 0 条；
- **头路径不变**：`Last-Event-ID` 裁剪语义同形；头**优先**（`or` 短路逐字保留）；
- **缺省全量**：不传参数 ⇒ 非空数组且每条含 `event_id`；
- **反证臂**：另一条 run 的事件键集相同（声明没收窄载荷）。

### 3. EC-03 射程如实（独立重跑）

`pytest tests/contracts tests/tooling tests/e2e -q` ⇒ **2304 passed / 85 skipped**。

- **SSE 帧格式判据在树**（`id:` / `event:` / `data:` 三件套）；
- **序 37 的判据未改断言**：其受判面清单 9 → **10**（加本轮新声明的路由行）——
  该清单是「app 声明面投影」的**设计行为**（清单与 app 声明面必须相等）；对照臂
  从 `/runs/{id}/events` 换成 `/runs/{id}/telemetry`；路径模板归一化补 `{run_id}`。
  本项属**射程扩大**（非收窄），逐条登记；
- **快照同轮**：`tools/gen_openapi.py` 后 `git diff --numstat` = **+31/−1**
  （两个参数进 schema + docstring 成为 public description）—— 与序 36/37 的「零 diff」
  形态相反，如实登记为**预期变化**并同轮提交。

### 4. EC-04 两向反证（独立重跑）

`uv run --frozen --no-sync python -B scratch/goal070_press.py`：

- **BASELINE（未按压）GREEN**（18 passed）；
- `V-1`（声明被移除）/ `V-2`（缺省被改动）/ `V-3`（`poll=0` 语义被破坏）/
  `V-4`（`cursor` 续传被破坏）⇒ **全 RED**；
- `V-2` **首跑 GREEN**（判据面缺口：缺省无人钉）⇒ 补 OpenAPI `default=="1"` 断言后 RED ——
  **同签名 1 次修复，未超 `fix_policy`**（`same_signature_retries: 2`）；
- `V-3` 的 RED 形态 = **TIMEOUT**（无限流挂死本身就是危害）；按压脚本 `taskkill /T /PID`
  只杀子树（不用 `/IM`：会连脚本自己一起杀）；跑完**零进程泄漏**（实测）；
- 逐条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`；
- 归档 `.cursor/plans/goals/evidence/GOAL-20261013-070-press-two-way.txt`（二进制、`CR=0`）。

## 结论

**PASS**。EC-01…EC-04 各自有独立重跑证据；四向反证全红且字节复原；快照变化如实登记；
射程如实（SSE 语义逐字不动；序 37 只扩受判面）。**残余**：无声明参数路由的面（另成一面）、
写面请求体字段（pydantic 既有面）—— 逐条保留在 GOAL 的「残余与受限面」一节。
**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
