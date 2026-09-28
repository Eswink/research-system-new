---
id: PLAN-20260928-227
slug: goal-024-ec01-privacy-exit-census
title: GOAL-024 cycle 1（EC-01）：非 canonical 出口清单显式分类 —— 发射点普查 + 受判/豁免登记 + 未分类与陈旧判红 + 按压
status: IN_PROGRESS
created_at: 2026-09-28
updated_at: 2026-09-28
parent_goal: GOAL-20260928-024
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260928-024 的 **EC-01**（金丝雀源与出口清单：显式分类，承 MEM-158）。
    授权沿用该 GOAL 的 `authorization.ref`：范围严格限定为「**新增金丝雀判据与夹具**（一律落
    `tests/**`）+ **修被新判据证明为真缺陷**（只允许收紧记录面）+ **文档同源更新**」；
    **不加新能力、不放宽任何判据、不改安全策略、不修改任何既有判据**；
    push-to-main-for-CI 口径（**只推 main、不 force、不重写历史、不推旁支**）；
    默认 runtime 保持 **Fake**、默认 CI **离线**、默认门**一律离线**。
    **本 PLAN 专属边界**：**不得**修改 `tests/observability/test_privacy_canary.py` /
    `canary_support.py` / `otlp_receiver.py`（**只读**）；**不得**改 `PRODUCT_ROOTS` /
    m0 任一 check / m0 条数（仍 `23`）；**不得**新增依赖（标准库 + 现有栈）；
    **不得**做真实出网；金丝雀一律**测试内构造的合成串**；
    **不得**宣称项目安全（`R-M1` 未收口）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **普查面在树且可机械复算**：新夹具（`tests/observability/privacy_exit_census.py`）
      按 **AST 发射形态**枚举产品根（`apps` / `services` / `packages` / `adapters`）下的
      发射点，产出 `(module, kind)` 候选集；形态谓词与扫描根**写在源码里**（不靠散文）。
    status: PENDING
  - id: AC-2
    criterion: >-
      **分类清单写在判据源码里且逐条显式**：新判据
      （`tests/observability/test_privacy_exit_census.py`）含 `EXIT_SURFACES`（出口清单：
      `judged` / `exempt` + 理由 + 观测方式）与 `EMITTER_CLASSIFICATION`（每个候选
      `(module, kind)` → 归属出口 **或** 带理由的豁免）；**不存在第三种状态**。
    status: PENDING
  - id: AC-3
    criterion: >-
      **未分类的新出口判红 + 陈旧判红**（承 MEM-158）：hermetic 反证 ①新增未登记发射点
      ⇒ 判红并点名 `(module, kind)`；②登记里的生产者消失 ⇒ 判红；③豁免理由抽空 ⇒ 判红；
      ④**清单下界收缩 ⇒ 判红**（承 MEM-160）；每次按压**逐字节复原**（raw `sha256` + 二进制读写）。
    status: PENDING
  - id: AC-4
    criterion: >-
      **受判出口非空且非空转**：被判为 `judged` 的出口**至少 5 个**，每个都声明
      **观测方式**（EC-02 据此扫描）；`exempt` 每条有**非空理由**；判据在**空登记**上不空转
      （必须有一批 `FAIL` 且退出码非 `0`）。
    status: PENDING
  - id: AC-5
    criterion: >-
      新判据与新夹具自洽过门：`ruff check` / `ruff format --check` / 规模（文件 ≤ 450 行、
      函数 ≤ 50 行）/ `mypy`；既有 `test_privacy_canary.py` **逐字节未改**且仍全绿；
      as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`（**记录写入之后**，承 MEM-145）；
      治理 `validate.py` 绿；CI 台账到终态。
    status: PENDING
latest_recheck: null
memory_entries: []
---

# PLAN-20260928-227 — GOAL-024 cycle 1（EC-01）：非 canonical 出口清单显式分类

**动因**：`RECHECK-20260928-226` 之前的 M15 WP4 只验证了**词汇层**（「不存在内容通道」+
键集闭合），并**明文**把「把内容硬塞进 identity 字段（例如往 `endpoint_id` 里写 prompt）」
交给调用方；**产品代码会不会这么做，从未被验证**。本 PLAN 先做**扫描面的地基**：
把「非 canonical 出口」从散文变成**源码内、可复算、无第三种状态**的清单。

**口径（本 GOAL 的边界，必须写清）**：**canonical state（PG 域实体 / SQLite 域表）
允许持有用户自己的任务输入** —— 那是业务真相，**不是泄漏**；受判面是**非 canonical 出口**。

## 验收条件

1. **AC-1** 普查面（AST 发射形态 + 扫描根）**在树且可机械复算**。
2. **AC-2** 出口清单与发射点分类**写在判据源码里**，逐条显式，无第三种状态。
3. **AC-3** 未分类 / 陈旧 / 空理由 / 下界收缩**各自判红**，按压后**逐字节复原**。
4. **AC-4** 受判出口 ≥ 5 且各有观测方式；空登记**不空转**。
5. **AC-5** 四道门自洽 + 既有判据逐字节未改且全绿 + as-is m0 23/23（记录之后）+ 治理绿 + CI 终态。

## 实施清单

- [ ] WP1：`tests/observability/privacy_exit_census.py` —— 出口/发射点类型 + AST 普查 + 分区判据的机械部分。
- [ ] WP2：`tests/observability/test_privacy_exit_census.py` —— `EXIT_SURFACES` /
      `EMITTER_CLASSIFICATION` 清单 + 5 组断言（分区 / 存活性 / 理由与观测 / 下界 / 形态自检）。
- [ ] WP3：按压矩阵 4 向 + 逐字节复原（raw `sha256`）。
- [ ] WP4：记录（本 PLAN / RECHECK / MEM / GOAL 回写）+ 记录面判据 + as-is m0 + push + CI 台账。

## 证据

（执行后填：普查计数、按压前后 raw `sha256`、四道门输出、m0 终态行、CI run。）

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-28 | IN_PROGRESS | 建档（GOAL-024 cycle 1，EC-01）。 |

## 影响报告

- **Domain/API/schema**：无（只新增 `tests/**`）。
- **安全/凭据**：无新增凭据面；金丝雀为测试内构造的合成串。
- **兼容性/迁移**：无。
- **上游版本影响**：无（零依赖改动）。
