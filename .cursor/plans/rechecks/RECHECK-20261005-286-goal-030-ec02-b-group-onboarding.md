---
id: RECHECK-20261005-286
slug: goal-030-ec02-b-group-onboarding
title: 复检：GOAL-030 EC-02 —— B 组承接（`run.read` 接线；`citation.validate` 经实测判定不可行）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-05
updated_at: 2026-10-05
plan_id: PLAN-20261005-285
reviewer: root-agent
parent_goal: GOAL-20261005-030
verify_paths:
  - >-
    uv run --frozen --no-sync python -B -m pytest
    tests/adapters/canonical/test_run_read_onboarding.py -q ⇒ 10 passed
  - >-
    uv run --frozen --no-sync python -B -m pytest tests/architecture/python
    tests/application/preflight tests/contracts tests/adapters -q ⇒ 全绿
  - >-
    uv run --frozen --no-sync python -B -m pytest tests/e2e tests/api tests/loaders
    tests/tooling tests/application/evidence -q ⇒ 全绿（3471 passed / 89 skipped 合跑）
owners:
  - root-agent
---

# RECHECK-20261005-286 — GOAL-030 EC-02

## 结论

**PASS_WITH_WARNINGS**。`run.read` 的承接**四条**（声明 + 实现 + 绑定 / 真读得到 / 缺依赖
点名 / 承接≠放行可区分）**实测到场**，射程四面**同轮同步**且全绿。`citation.validate` 的
**不可行判定**逐条取证并登记为受限面 —— **没有为凑数硬接**。

## 检查结果

| EC-02 要求 | 判据 | 实测 |
| --- | --- | --- |
| B 组承接（以核实为准） | `tests/adapters/canonical/test_run_read_onboarding.py` | **10 passed** |
| 判定规则可复核 | 本轮的 B 组里 `run.read` 不需要判定语义（读既有域字段）；`citation.validate` 的判定语义**已写出**但**未落地**（受限面） | 见「如实边界」 |
| 反证两向 | 撤回能力映射 ⇒ **3 failed**，各自点名 `run.read`；复原 `sha256` 全 `OK` | 判词逐字见 PLAN 的「按压记录」 |
| 射程同源 | `tool_providers.yaml` / `_IN_SCOPE` / `POLICY_SURFACE_AUDIT.md` / provider 夹具 **同一轮**更新 | 四面全绿（含差集判据与下界断言） |
| 承接≠放行可区分 | 同用例内断言「目录声明」+「策略 DENY + used default policy effect」 | 实测通过 |

## 按压（两向）

见 PLAN 的「按压记录」：撤回 `_TOOL_CAPABILITIES` 的 `run_read` 条目 ⇒ 3 failed（实现面 /
声明-实现落差 / 射程下界，三条各自点名）；复原后 `sha256sum -c` 三文件 `OK`。

## 如实边界

- **`citation.validate` 未落地**：取数面（`_elink`）与判定规则（`pmc_links` 非空 ⇒ 通过）
  都已核实可写，但**声明它**会打红 `tests/contracts/**` 的两条既有 pin 判据，而该面被本
  GOAL `fix_policy` 明文禁改 ⇒ 判定**不可行**并登记为受限面。**不得**把「判定语义已想清楚」
  冒充成「已承接」。
- **`run.read` 已承接但未放行**：与另五条读能力同 —— 不可协议可达（`policy.yaml` 无 `allow`）。
  本判据把这条**可区分性**钉死，**不以承接冒充满通**。
- 装配改动只经**既有** Port（`RunStore`），**零**新依赖、**零**新凭据面；`policy.yaml` 未动。

## 残余（W-NN）

- **`W-1`｜`RunStore` 的读面语义未与 HTTP 读面逐字比对**：本判据断言的是「逐字段等于
  store 里的域事实」，而 HTTP 面 `GET /runs/{id}` 走 `_run_state_dto`（有额外投影）。
  **两者共用 `get_run`**（同一查询口径），但**投影不比对** —— 如实登记。
- **`W-2`｜`_SqliteStoreParts.runs_store` 与 `ApiDeps.runs_store` 现在共享实例**：这消除了
  「第二个 store 实例」，但也意味着两者**不再可能各配各的**（原本各自构造）。这是本轮为
  守住 450 行硬上限所做的最小改动；语义上更正确（同一 run 的读写必须同一实例），但属**行为
  面变化**，故登记。
- **`W-3`｜`composition.py` 恰在 450 行**：本轮的净增为 0（靠复用实例 + 压缩两处注释达成）。
  下一次再往它上面接线会**立刻**撞硬上限 —— 结构性压力未解（与 GOAL-029 的登记同源）。
- **`W-4`｜`citation.validate` 的解除条件依赖外部授权**：它属「既有 pin 判据的同轮同步」，
  需用户拍板；本轮**不自行**改那两条判据。
- **`W-5`｜`run.read` 未进任何协议的 `required_capabilities`**：它是本轮新承接，与 EC-01 的
  三条不同 —— 那三条已放行、已进协议；本能力**未放行**⇒ 不能进协议。

## 未覆盖范围（原样保留）

读面未认证 / 多租户未做 / RBAC 未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口 /
D 组审批通道未接通。**不得**据此宣称项目安全；**不得**宣称投递语义为「恰好一次」
（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
