---
id: PLAN-20260928-227
slug: goal-024-ec01-privacy-exit-census
title: GOAL-024 cycle 1（EC-01）：非 canonical 出口清单显式分类 —— 发射点普查 + 受判/豁免登记 + 未分类与陈旧判红 + 按压
status: DONE
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
    status: PASS
  - id: AC-2
    criterion: >-
      **分类清单写在判据源码里且逐条显式**：新判据
      （`tests/observability/test_privacy_exit_census.py`）含 `EXIT_SURFACES`（出口清单：
      `judged` / `exempt` + 理由 + 观测方式）与 `EMITTER_CLASSIFICATION`（每个候选
      `(module, kind)` → 归属出口 **或** 带理由的豁免）；**不存在第三种状态**。
    status: PASS
  - id: AC-3
    criterion: >-
      **未分类的新出口判红 + 陈旧判红**（承 MEM-158）：hermetic 反证 ①新增未登记发射点
      ⇒ 判红并点名 `(module, kind)`；②登记里的生产者消失 ⇒ 判红；③豁免理由抽空 ⇒ 判红；
      ④**清单下界收缩 ⇒ 判红**（承 MEM-160）；每次按压**逐字节复原**（raw `sha256` + 二进制读写）。
    status: PASS
  - id: AC-4
    criterion: >-
      **受判出口非空且非空转**：被判为 `judged` 的出口**至少 5 个**，每个都声明
      **观测方式**（EC-02 据此扫描）；`exempt` 每条有**非空理由**；判据在**空登记**上不空转
      （必须有一批 `FAIL` 且退出码非 `0`）。
    status: PASS
  - id: AC-5
    criterion: >-
      新判据与新夹具自洽过门：`ruff check` / `ruff format --check` / 规模（文件 ≤ 450 行、
      函数 ≤ 50 行）/ `mypy`；既有 `test_privacy_canary.py` **逐字节未改**且仍全绿；
      as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`（**记录写入之后**，承 MEM-145）；
      治理 `validate.py` 绿；CI 台账到终态。
    status: PASS
latest_recheck: .cursor/plans/rechecks/RECHECK-20260928-228-goal-024-ec01-privacy-exit-census.md
memory_entries:
  - .cursor/memory/entries/MEM-20260928-161-exit-census-must-be-a-partition-with-reasons.md
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

- [x] WP1：`tests/observability/privacy_exit_census.py` —— 出口/发射点类型 + AST 普查 + 分区判据的机械部分（**259 行**）。
- [x] WP2：`tests/observability/test_privacy_exit_census.py` —— `EXIT_SURFACES` /
      `EMITTER_CLASSIFICATION` 清单 + 13 例断言（分区 / 自洽 / 下界 / 金丝雀源 / 未覆盖面 / 非空转 / 6 组反证 / 形态自检）。
- [x] WP3：按压矩阵 4 向（真实树新增出口 / 清单条目消失 / 空理由 / 下界不一致）+ 逐字节复原（raw `sha256`）。
- [x] WP4：记录（本 PLAN / `RECHECK-20260928-228` / `MEM-20260928-161` / GOAL 回写）+ 记录面判据 + as-is m0 + push + CI 台账。

## 证据

- **普查剖面**：113 个候选（`application_log` 2 / `stdout` 4 / `otlp_span` 12 / `otlp_metric` 11 /
  `disk_write` 8 / `read_face` 29 / `failure_payload` 47）；受判出口 6 + 豁免出口 1 + 豁免生产者 25。
- **四道门**：`ruff format --check` = `2 files already formatted`；`ruff check` = `All checks passed!`；
  规模 259 / 407 行、超 50 行函数 0；`mypy` = `Success: no issues found in 2 source files`。
- **既有判据未改**：`test_privacy_canary.py` 逐字节未改；与其合跑 **20 passed**（13 新 + 7 既有）。
- **按压四向**：P1 真实树新增 `print` 模块 ⇒ `未分类…press_probe_module.py [stdout]`；
  P2 清单删一行 ⇒ `未分类…scheduler.py [otlp_span]`；P3 空理由 ⇒ 两条 `缺少理由`；
  P4 下界加非受判 id ⇒ `必备受判出口缺失:['stdout-stderr']`。四条均 `1 failed, 12 passed`，
  复原后 raw `sha256` 回到 `076fad378c48c794df3fa4e672614a7e379f10bc69f2e81d7eb5e7ce42aac74f` ⇒ 13 passed。
- **自跑抓到的两处自己的错**：重复分类（`adapters/otel/failsafe.py`）与形态自检样本位形写错（`read_face`），当场修掉。
- **as-is 本机 m0** 与 **CI 台账**：见 GOAL-024 迭代日志 cycle 1 行（记录写入之后跑）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-28 | IN_PROGRESS | 建档（GOAL-024 cycle 1，EC-01）。 |
| 2026-09-28 | DONE | 交付 2 个进树文件（`privacy_exit_census.py` 259 行 / `test_privacy_exit_census.py` 407 行）；普查 113 候选全覆盖（受判 6 / 豁免 25 + 豁免出口 1）；四道门绿；四向按压先红后绿 + 逐字节复原；既有隐私判据逐字节未改且全绿；`RECHECK-20260928-228` = `PASS_WITH_WARNINGS`（`W-1`…`W-6`）。 |

## 影响报告

- **Domain/API/schema**：无（只新增 `tests/**`）。
- **安全/凭据**：无新增凭据面；金丝雀为测试内构造的合成串。
- **兼容性/迁移**：无。
- **上游版本影响**：无（零依赖改动）。
