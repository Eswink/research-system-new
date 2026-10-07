---
id: RECHECK-20261008-312
slug: goal-033-ec01-dead-letter-product-entry
title: 独立复检：GOAL-033 cycle 1（EC-01）死信人工恢复的**产品**入口
plan_id: PLAN-20261008-311
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-08
completed_at: 2026-10-08
owners:
  - root-agent
---

# RECHECK-20261008-312 — GOAL-033 cycle 1（EC-01）独立复检

复检对象：`PLAN-20261008-311`（死信人工恢复的产品入口）。**复检独立于实施**：本节逐条
重跑判据与门，不引用 PLAN 的结论作为证据。

## 检查结果

### 1. 交付面在位（逐文件核实）

| 文件 | 形态 | 读数 |
| --- | --- | --- |
| `services/api/routers/tasks.py` | 新增（路由） | 存在；只调 `.requeue(`，**无** `ResearchTaskState.transition`、**无**直接写任务行 |
| `services/api/dto/tasks.py` | 新增（DTO） | 存在；`TaskRetryDto` 三字段 |
| `services/api/app.py` | `+2 / -0` | `import tasks` + `include_router(tasks.router)` 各一行 |
| `tests/api/test_task_retry_api.py` | 新增 9 例 | 全绿 |
| 同步集①~⑤ | 见 PLAN AC-7 | 逐条 `git diff --numstat` 核实 |

### 2. 主判据重跑（不复用 PLAN 结论）

```
tests/api/test_task_retry_api.py ......... [100%]  9 passed
```

- **成功路径三读数**（AC-1）：端点 200 + `result=restored`；任务面回 `QUEUED`；
  **恢复后 `acquire_lease` 成功**（下游消费证据 —— 这一条是本 EC 的关键，
  它把「状态写回了」与「自动路径真的认它了」分开）。
- **三类点名拒绝**（AC-2）：404 / 409 / 503 逐条实测，消息含任务 id 与状态/原因。
- **幂等两层**（AC-3）：重放复用首次响应且**事件计数不增**（取样在重放**之前**）；
  新 key 打在已恢复任务上 ⇒ 409 且零新副作用。
- **调用证据 + 不建第二套**（AC-4）：源码断言与行为断言配对。
- **认证面自动覆盖**（AC-6）：端点进入 OpenAPI 且方法为 POST。

### 3. 门（独立重跑）

| 门 | 读数 |
| --- | --- |
| `ruff check` | 绿（新增三文件 + 受影响文件） |
| `ruff format --check` | 绿 |
| `mypy` | 绿（新增三文件） |
| 规模门 | 绿（`tests/tooling/test_python_source_limits.py`：1147 passed） |
| `tests/api` + `tests/contracts` | **1123 passed / 76 skipped** |
| `tests/domain` + `tests/adapters/sqlite` + `tests/tooling` + `tests/observability` | 首跑 **1 failed** ⇒ 定位为**真信号**（新端点触发 `failure-payload` 受判出口未分类，门在正常工作）⇒ 按清单口径显式认领（**受判**而非豁免）后 **132 passed / 3 skipped**（observability） |
| 记录面判据（三道） | 绿 |

### 4. 两向反证（独立重跑）

```
BASELINE_GREEN 9 passed
P1_RED exit=1 8 failed, 1 passed
P2_RED exit=1 4 failed, 5 passed
RESTORED True {'tasks.py': '1f328fc53022->1f328fc53022', 'app.py': 'cac8dc281f5d->cac8dc281f5d'}
FINAL_MATCHES_BASELINE True 9 passed
```

- P1（摘掉端点注册）⇒ 8 failed；P2（点名拒绝改静默）⇒ 4 failed。**两条都真的判红**。
- `RESTORED True` 带 **sha 归因**（哪个文件、什么值）—— 首跑曾出现一次无归因的
  `RESTORED False`，复检要求把它变成可归因读数后重跑四次均 True（见 W-3）。
- 留档 `scratch/goal033-cycle1/press-matrix.log`（260 B、**CR=0**）。

### 5. 同步集核查（逐条「强度未降」）

- ① 文档：把「未提供」改成事实（输入登记面，无判据读它）。
- ② OpenAPI 生成物：由生成器重新生成 ⇒ 快照判据的判法未动。
- ③ 快照测试：**追加**路径断言（既有断言逐字未动）。
- ④ 写面告警线：计数 60 → 61（该文件自己声明的用途）；保护面定义
  `_MUTATING_METHODS` 与全部断言未动。
- ⑤ `test_privacy_exit_census.py`：`failure-payload`（**JUDGED**）producer 清单 +1 行；
  **不是豁免**、不是新出口面。

## 结论

**result: PASS_WITH_WARNINGS**。

四条 AC 面（成功路径+下游消费证据 / 三类点名拒绝 / 幂等两层 / 调用证据不建第二套）与
认证面自动覆盖、两向反证、同步集逐条经独立重跑成立。**无产品缺陷**。

### Warnings

- **W-1（射程）**：本端点**只**覆盖人工恢复一条死信任务。**未覆盖**：自动恢复
  （超时自动重生）、按 run 批量恢复、恢复的审批门、**恢复后 run 的自动继续**
  （run 级入口仍是 `POST /runs/{id}/resume`）—— 后者是 GOAL-033 **EC-02** 的靶子。
- **W-2（同步集超出预设）**：建档时预估同步集 4 条，实测第 5 条
  （`test_privacy_exit_census.py`）。处置：它属「既有判据的显式清单需登记新成员」，
  **零断言改动、零豁免**，已在 GOAL 的同步集清单里**追加为第 5 条**并登记理由。
  **不改口径**：这仍是「纯扩张式同步」，不是放宽。
- **W-3（按压脚本的读数可归因性）**：首跑 `RESTORED False` 是**无归因**读数
  （未记录是哪个文件、什么值），无法判定真伪 ⇒ 已给脚本加 sha 归因面并重跑四次均为
  True；**归因面已固化在脚本里**，后续复检不会再现不可归因读数。
  **未**据此改动任何产品代码（`git diff` 核实：两次按压均逐字节复原）。
- **W-4（前端类型面）**：`apps/web` 零改动。本仓无 `types.ts` 生成器（建档实测）⇒
  新端点暂未进前端手写类型；若前端要暴露该动作，属**手写面**，不在本 EC 的判据内。
- **W-5（未覆盖范围照旧）**：读面未认证 / 多租户 / RBAC / BOLA·BFLA / 部署面未验证 /
  `R-M1` 未收口。**不得**据此宣称项目安全；**不得**宣称投递语义为「恰好一次」
  （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
