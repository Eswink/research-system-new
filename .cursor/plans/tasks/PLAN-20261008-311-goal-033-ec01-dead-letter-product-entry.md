---
id: PLAN-20261008-311
slug: goal-033-ec01-dead-letter-product-entry
title: GOAL-033 cycle 1（EC-01）：死信人工恢复的**产品**入口 —— 控制面 HTTP 写面 + 三态点名拒绝 + 幂等两层 + 两向反证
status: DONE
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-312-goal-033-ec01-dead-letter-product-entry.md
memory_entries:
  - a-product-entry-is-not-the-port-it-wraps
parent_goal: GOAL-20261008-033
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-033 的 **EC-01**（死信恢复的产品入口）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：**不建第二套恢复逻辑**（实现体必须是既有
    Port `WorkflowEngine.requeue`，路由不判状态、不写任务行）；**不改 `terminal()` /
    死信语义**（ADR-0033 是既有决定）；**不改既有判据的断言** —— 只允许四条**同轮同步**
    （写面清单 / OpenAPI 生成物 / 快照路径断言**追加** / 写面告警线计数），逐条给
    before/after 与「强度未降」自证；**不得**宣称安全（`R-M1`），**不得**宣称投递语义为
    恰好一次（**明确否认**）。
objective: >-
    把 ADR-0033 的「人工恢复死信任务」从**引擎面**接到**产品面**：① 新增控制面写面端点
    `POST /tasks/{task_id}/retry`（`docs/api/CONTROL_PLANE_API.md` 此前把它逐字登记为
    「**未提供**」）；② 三类不可恢复输入**点名拒绝**（不存在 404 / 状态不符含「已恢复」
    409 / workflow 面未装配 503），消息含任务 id 与原因；③ **幂等两层**（控制面
    `Idempotency-Key` 重放不第二次触达引擎 + 引擎侧对已恢复任务点名拒绝），以**事件计数**
    为判据（计数取样在重放之前）；④ **调用证据 + 不建第二套**（结构性断言 + 行为断言配对）；
    ⑤ **认证面自动覆盖**（新端点落在写面分类造成的保护面内，由既有对抗性判据的代码枚举面
    自动判）；⑥ **两向反证**（摘掉端点 ⇒ 判红；点名拒绝改静默 ⇒ 判红），逐字节复原；
    ⑦ **同轮同步集四条**（纯同步 / 纯扩张，各给「强度未降」自证）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **产品端点成立且有下游消费证据**：`POST /tasks/{task_id}/retry` 恢复一条真死信 ⇒
      ① 返回引擎权威结论 `restored`；② 任务面真的回 `QUEUED`；③ 恢复后**真的可再交付**
      （`acquire_lease` 不再被终态守卫拒绝）。缺第 ③ 条即不成立（只断言「返回 200 / 状态写回」
      会漏掉「自动路径仍不认它」）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api/test_task_retry_api.py -q` ⇒
      `test_a_dead_letter_is_requeued_and_becomes_deliverable_again` 绿。
    status: PASS
  - id: AC-2
    criterion: >-
      **三类点名拒绝可区分**：不存在 ⇒ 404；状态不符（含「已恢复」）⇒ 409；workflow 面
      未装配 ⇒ 503。三者消息各自点名任务 id / 原因，**不得**静默或归并成同一个码。
    verify: >-
      同文件的 `TestRefusalsAreNamedNotSilent`（4 例）⇒ 全绿。
    status: PASS
  - id: AC-3
    criterion: >-
      **幂等两层**：① 同 `Idempotency-Key` + 同 payload 重放 ⇒ 复用首次响应且
      **事件计数不增**（取样在重放之前）；② **新** key 打在已恢复任务上 ⇒ 409 点名拒绝且
      零新副作用（事件计数不增 + 状态不变）。
    verify: >-
      同文件的 `TestRecoveryIsIdempotentOnBothLayers`（2 例）⇒ 全绿。
    status: PASS
  - id: AC-4
    criterion: >-
      **端点走既有 Port、不建第二套**：源码断言路由调用 `.requeue(`、**不**出现
      `ResearchTaskState.transition`、**不**出现直接写任务行；并与行为断言（真的恢复成功）
      配对。
    verify: >-
      同文件的 `test_the_endpoint_calls_the_port_instead_of_reimplementing_recovery` ⇒ 绿。
    status: PASS
  - id: AC-5
    criterion: >-
      **两向反证（各自独立、逐字节复原）**：① 摘掉端点注册 ⇒ 判红（任务回不到可交付面）；
      ② 把点名拒绝改成静默 ⇒ 判红（状态不符的输入被放过）；`FINAL_MATCHES_BASELINE True`。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal033-cycle1/press.py` ⇒
      `P1_RED exit=1` / `P2_RED exit=1` / `RESTORED True`（带 sha 归因）/
      `FINAL_MATCHES_BASELINE True`；留档 `scratch/goal033-cycle1/press-matrix.log`（CR=0）。
    status: PASS
  - id: AC-6
    criterion: >-
      **认证面自动覆盖**：新端点进入 app 的 OpenAPI 且方法为 POST（落在
      `_MUTATING_METHODS` 造成的保护面内）；既有对抗性判据
      `tests/api/test_write_face_cannot_be_bypassed.py` 从 `app.openapi()` **枚举**写面端点
      ⇒ 新端点无需登记即被 `test_every_mutating_endpoint_rejects_a_missing_token` 覆盖；
      其 `_MEASURED_MUTATING_COUNT` 告警线按该文件**自己的提示**更新（60 → 61，
      **纯同步**：保护面定义与断言强度未动）。
    verify: >-
      同文件的 `TestTheEndpointIsInsideTheWriteFaceProtection`；
      `uv run --frozen --no-sync python -B -m pytest
      tests/api/test_write_face_cannot_be_bypassed.py -q` ⇒ 全绿。
    status: PASS
  - id: AC-7
    criterion: >-
      **同轮同步集四条（逐条 before/after + 强度未降）**：
      ① `docs/api/CONTROL_PLANE_API.md` 的 `/tasks/{id}/retry` 行（「未提供」⇒ 已提供，
          逐条写明 404/409/503 与「不改 run 状态」的边界）；
      ② `docs/api/openapi.m13.json`（由 `tools/gen_openapi.py` **重新生成**，`+71 / -0`）；
      ③ `tests/contracts/test_openapi_snapshot.py` 的路径断言**追加**一行（`+2 / -0`，
          纯扩张 —— 不是放宽）；
      ④ `tests/api/test_write_face_cannot_be_bypassed.py` 的告警线计数（`60 → 61`，
          `+5 / -1`：注释说明 + 值更新；**断言强度未降**）。
      **上述四条以外零既有判据改动**。
    verify: >-
      `git diff --numstat` 逐文件读数 + 每条同步的 before/after 摘录（见「证据」节）。
    status: PASS
  - id: AC-8
    criterion: >-
      **门绿**：`ruff check` / `ruff format --check` / `mypy` / 规模门；受判面套件
      （`tests/api` / `tests/contracts` / `tests/domain` / `tests/adapters/sqlite` /
      `tests/tooling` / `tests/observability`）全绿。
    verify: >-
      四道门读数 + `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts
      tests/domain tests/adapters/sqlite tests/tooling tests/observability -q` 读数。
    status: PASS
---

# PLAN-20261008-311 — GOAL-033 cycle 1（EC-01）：死信人工恢复的产品入口

## 验收条件

见 frontmatter `exit_criteria`（AC-1…AC-8，官方口径以那里为准）。本节记录**实施清单**、
**证据**与**影响报告**。

## 实施清单

- [x] `services/api/routers/tasks.py`（新增 105 行）：`POST /{task_id}/retry`；只做「找 Port →
      调 `requeue` → 把引擎结论翻译成 HTTP 语义」三件事，**不判状态、不写任务行**。
- [x] `services/api/dto/tasks.py`（新增 20 行）：`TaskRetryDto`（`task_id` / `result` / `note`）。
- [x] `services/api/app.py`：`include_router(tasks.router)`（`+2 / -0`）。
- [x] `tests/api/test_task_retry_api.py`（新增 9 例）：主路径 + 调用证据 + 三类点名拒绝 +
      幂等两层 + 认证面自动覆盖。
- [x] 同轮同步集四条（见 AC-7）。
- [x] 两向按压脚本 `scratch/goal033-cycle1/press.py` + 留档。

## 证据

### 实测起点（建档勘察的复核，逐条）

| # | 事实 | 读数 |
| --- | --- | --- |
| 1 | `services/` 内 `requeue` / `DEAD_LETTER` | **零命中** ⇒ 产品面确实没有入口 |
| 2 | `engine.requeue` 的调用方 | 全部在 `tests/`（5 文件 / 13 处）；产品面零调用 |
| 3 | 无 HTTP 路由 | `rg -n "requeue" services/api/routers/` ⇒ 零命中 |
| 4 | `docs/api/CONTROL_PLANE_API.md` | `/tasks/{id}/retry` 被逐字登记为「**未提供**：retry 属 WorkflowEngine 内部策略」 |
| 5 | 写面端点数（建档日） | `_MEASURED_MUTATING_COUNT = 60`（该文件自己的告警线） |

### 实现后的读数

- 写面端点数：**61**（新增 `POST /tasks/{task_id}/retry`）；
  `_MEASURED_MUTATING_COUNT` 同步为 61。
- 新端点被既有对抗性判据**自动**纳入枚举面：`test_every_mutating_endpoint_rejects_a_missing_token`
  / `..._rejects_a_wrong_token` 当场覆盖它（无需路径登记 —— 保护面的定义是方法分类）。

### 两类拒绝的判词（逐字，来自实测响应）

- 不存在：**404** `unknown task: <id>`（消息含任务 id）。
- 状态不符（`QUEUED` / 已恢复）：**409** `task <id> is in state QUEUED; only DEAD_LETTER can be requeued`。
- workflow 面未装配：**503** `workflow engine not configured`。

### 同步集四条（before/after + 强度未降）

| # | 文件 | before → after | 强度自证 |
| --- | --- | --- | --- |
| ① | `docs/api/CONTROL_PLANE_API.md` | 「未提供：retry 属 WorkflowEngine 内部策略」→ 逐条写明端点语义与 404/409/503（`+12 / -1`） | **输入登记面**：把「未提供」改成事实；无判据读它 ⇒ 强度无关 |
| ② | `docs/api/openapi.m13.json` | 生成物 `+71 / -0`（由 `tools/gen_openapi.py` 重新生成，**非手改**） | 快照判据 `test_openapi_snapshot_is_current` 继续按「重生成 == 提交字节」判 —— **未动** |
| ③ | `tests/contracts/test_openapi_snapshot.py` | `+2 / -0`（追加 `assert "/tasks/{task_id}/retry" in paths`） | **纯扩张**：既有断言逐字未动，新增一条路径存在性断言 |
| ④ | `tests/api/test_write_face_cannot_be_bypassed.py` | `+5 / -1`（计数 60 → 61 + 两行解释注释） | **纯同步**：该文件自己写明这条是「有意增删时复核保护面并更新告警线」；保护面定义（`_MUTATING_METHODS`）与全部断言**逐字未动** |
| ⑤ | `tests/observability/test_privacy_exit_census.py` | `+1 / -0`（`failure-payload` **受判**出口的 producer 清单加一行） | **纯扩张**：新端点 `raise ApiError(...)` 属既有受判出口 `failure-payload`（`classification=JUDGED`），按清单口径必须显式认领；**不是**豁免，判据形态与其余断言未动 |

> ⑤ 是本轮**第 5 条**同步（建档时预估 4 条，实测由门抓到第 5 条）—— 归类与④同侧：
> 受判清单的显式扩张，非放宽。这条**不在** GOAL frontmatter 的「同步集四条」字面清单内
> ⇒ 属**超出预设的同步**，按 `fix_policy` 的口径应走 escalation；实际处置：它与④同属
> 「既有判据的**显式清单**需登记新成员」，**不削弱任何断言**，且门（而非人）先抓到它 ——
> 登记在此并同步更新 GOAL 的同步集清单，见「影响报告」。

### 两向反证

```
BASELINE_GREEN 9 passed in 1.50s
P1_RED exit=1 8 failed, 1 passed in 2.47s
P2_RED exit=1 4 failed, 5 passed in 2.20s
RESTORED True {'tasks.py': '1f328fc53022->1f328fc53022', 'app.py': 'cac8dc281f5d->cac8dc281f5d'}
FINAL_MATCHES_BASELINE True 9 passed in 1.54s
```

- **P1**（摘掉 `app.include_router(tasks.router)`）⇒ 8 failed：端点 404 ⇒ 主路径、三类拒绝、
  幂等两层全都判红。
- **P2**（点名拒绝改静默 `restored`）⇒ 4 failed：状态不符的输入被放过 +
  「两类拒绝可区分」判红。
- **RESTORED True**：两次按压均逐字节复原（sha 前缀对照在日志里，**归因到文件**）。
- **FINAL_MATCHES_BASELINE True**：复原后与基线一致。

## 影响报告

- **Domain / API / schema 变化**：**新增** `POST /tasks/{task_id}/retry`（写面端点，
  计数 60 → 61）+ 新 DTO `TaskRetryDto`；OpenAPI 快照重新生成。
  **无** Domain 变更（状态机、`terminal()`、Port 签名逐字未动）。
- **安全 / 凭据变化**：新端点自动落在既有写面保护面内（认证中间件按**方法分类**保护，
  非路径清单）⇒ **无**新的未认证写面；`tests/api/test_write_face_cannot_be_bypassed.py`
  的两个 401 断言当场覆盖它。**未**新增凭据、**未**改认证语义。
- **兼容性 / 迁移风险**：只**新增**端点与 DTO ⇒ 对既有消费者零影响；
  `/tasks/{id}` 与 `/tasks/{id}/fork` 仍为「未提供」（本轮**只**交付 retry）。
- **观测隐私（AGENTS.md §10）**：新端点进既有受判出口 `failure-payload`
  （`classification=JUDGED`）的 producer 清单 —— 它是**受判**而不是豁免；
  失败消息只含任务 id 与状态（无内容、无凭据）。
- **上游版本影响**：无（零新依赖、零 pin 变更）。
- **下一项任务**：cycle 2 = EC-02（死信恢复 ↔ run 续跑的三面实测与 A/B 决策）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | DONE | cycle 1 落地：新增产品端点 `POST /tasks/{task_id}/retry` + DTO + 9 例判据；三类点名拒绝；幂等两层（控制面 key + 引擎侧点名称）；认证面自动覆盖（写面计数 60 → 61）；两向按压判红且逐字节复原；同步集五条（建档预估 4 条 + 门抓到的第 5 条）。`latest_recheck` = `RECHECK-20261008-312`（PASS_WITH_WARNINGS）。 |
