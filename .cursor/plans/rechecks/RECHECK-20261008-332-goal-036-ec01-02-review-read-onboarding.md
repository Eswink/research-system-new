---
id: RECHECK-20261008-332
slug: goal-036-ec01-02-review-read-onboarding
title: 独立复检：GOAL-036 cycle 1（EC-01/EC-02）`review.read` 的勘察定稿 + 端到端承接链
plan_id: PLAN-20261008-331
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-08
completed_at: 2026-10-08
owners:
  - root-agent
---

# RECHECK-20261008-332 — GOAL-036 cycle 1（EC-01/EC-02）独立复检

复检对象：`PLAN-20261008-331`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 勘察定稿（AC-1）

| # | 事实 | 独立读数 |
| --- | --- | --- |
| 1 | 词表里有 `review.read` | `capabilities.yaml` 46 条含它 |
| 2 | 声明面零承接（建档时） | `tool_providers.yaml` distinct **19**（**不含**它）；本轮 = 20 |
| 3 | 策略面零放行（建档时） | `allow` 无它 ⇒ `default_effect: DENY`；本轮新增**一条** `allow` |
| 4 | 分类理由过期 | 判定：`_OUT_OF_SCOPE_REASONS` 原文指向「评审走 task/handoff 面」，被 GOAL-035 EC-01 推翻 |
| 5 | 承接机制（可选依赖） | `read_provider.py` 的 `budget_ledger` / `experiment_store` / `run_store` 三条先例，缺省 `None` ⇒ 点名不可用 |
| 6 | 规模约束 | `read_provider.py` 建档时 **410 / 450** ⇒ 新实现另立模块 |

### 2. 承接链五件事（AC-2，逐条件独立 `rg` 取证）

| # | 件 | 读数 |
| --- | --- | --- |
| ① 实现 | `adapters/canonical/review_read.py`（**68 行**）在树；`review_read(findings, args)` 读 `for_run` | 三条边独立探针：正路 `count=1` + 逐条判词在场；**缺依赖 ⇒ 点名**（`requires a ReviewFindingStore, which is not in this assembly`）；**空 run_id ⇒ 点名**（`requires a non-empty run_id`） |
| ② 工具面 | `read_surface.py` 描述子 + `_TOOL_CAPABILITIES["review_read"]="review.read"`；`read_provider.py` handler + 委派方法（**421 / 450**） | 在树 |
| ③ 绑定 | `DEFAULT_SESSION_TOOL_BINDINGS` += `("review.read", "m12_artifact", "review_read")` | 在树 |
| ④ 接线 | `canonical_read_register(review_store=…)` + `sqlite_session_tools` 传 `ports.review_findings` + PG 根传 `c["review_findings"]` | 两条组合根路径都在树 |
| ⑤ 声明 + 放行 | `tool_providers.yaml`（`m12_artifact` capabilities += 一条）；`policy.yaml` **新增一条** `allow`（scope `project`） | 在树；其余三段 + `default_effect` 由段指纹判据钉住（见下） |

### 3. 同轮同步面（独立复核「加法 / 搬迁登记」而非改断言）

| # | 落点 | 改动形态 | 断言强度核对 |
| --- | --- | --- | --- |
| 1 | `tests/adapters/canonical/test_canonical_read_provider.py` | `_PROVIDER.capabilities` **+1** | 不涉谓词 |
| 2 | `tests/architecture/python/test_capability_coverage_is_implemented.py` | `_IN_SCOPE` **+1**、登记表 **−1**（搬迁） | 主判据（声明 ⇒ 实现）**仍绿**；反证两向仍绿 |
| 3 | `examples/config/policy.yaml` | `allow` **+1** | `require_approval`/`deny` **段指纹判据仍绿**（`test_the_deny_segment_body_is_byte_identical_to_the_baseline`）；`default_effect: DENY` 判据仍绿 |
| 4 | `packages/application/preflight/policy_check.py::_CAPABILITY_SCOPE` | **+1** | 并集相等判据（`test_m2_audit`）**仍绿** |
| 5 | `docs/architecture/POLICY_SURFACE_AUDIT.md` + 两处登记计数 | 行**离开差集**进交集清单、计数 8→7 / `_RELEASED`+1 / `_UNRELEASED_READS`−1 / scope 表+1 | 两条策略面判据（差集完备性 / 逐条形态 + 两向反证）**仍绿** |

**「未改断言」的机械证据**：三处 pin 的**反证臂**（非只读能力代入 ⇒ 点名；删一条放行 ⇒
回落 `default_effect`；注入进真实 `allow` ⇒ 扩集断言报出）在本轮**全部仍绿** ——
若谓词被放松，反证臂会先失效。

### 4. 门（独立重跑）

| 门 | 读数 |
| --- | --- |
| `ruff check`（触及面 10 文件） | `All checks passed!` |
| `ruff format --check` | `141 files already formatted` |
| `mypy`（strict，新模块 + provider + surface） | `Success: no issues found in 3 source files` |
| 规模 | `review_read.py` **68** 行 / `read_provider.py` **421 / 450** |
| 全量 python 套件 | **5361 passed, 20 skipped**（相对建档基线收集数 **+1** = 新模块进源文件参数化面，逐文件分解过） |
| `tests/application/preflight` | **60 passed** |
| **as-is m0**（在全部记录写入之后独占跑，记录写完之后） | **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` 24 / `FAILED [` 0 / **5359 passed, 20 skipped**；收集数 **+1** 逐文件分解 = 新模块 `adapters/canonical/review_read.py` 进源文件参数化面（1151→1152）；`skipped` 20 未升） |

### 5. 未覆盖 / 一等边界

- **本轮只证「读得到」**：`review.read` 的**内容正确性**不在范围（它只回既有 canonical 记录的
  既有字段）；**「真的被一次实跑用上」是 EC-03**，本复检**不**声称已用上；
- **空结果 ≠ 不可用**：store 在场而 run 无结论 ⇒ `count=0 / findings=[]`（可区分的事实）；
  store 缺席 ⇒ **点名拒绝**；两者**不得**互相顶替（判据两侧各有一条独立探针）；
- **放行面只增一条且只为读**：写面 / 执行面 / 审批面零变化（段指纹 + 逐条判据）；
- **不得**声明项目安全（`R-M1` 未收口）；**不得**宣称投递语义为那四个字（**明确否认**）。

## 结论

**result: PASS_WITH_WARNINGS**。EC-01、EC-02 逐条独立成立；**无产品缺陷**。

### Warnings

- **W-1（同轮同步面清单在建档时不全）**：放行一条读能力会牵动**策略面登记表族**（5 处），
  建档时只枚举了 2 处 ⇒ cycle 1 门链实测后**修正 `fix_policy`**（GOAL 决策 ⑥）。这不是
  放宽断言（谓词 / 阈值 / 受判形态一字未改，反证臂全绿），但**必须如实登记**：清单外的
  既有判据仍禁改，触达即 BLOCKED。
- **W-2（EC-03 未做）**：「真的被用上」（下游消费证据 + 两向反证）留给 cycle 2；
  本复检**不**声称放行后已产生使用面读数。
- **W-3（承继残余原样保持）**：GOAL-035 的 `N-1`…`N-6`、`R26-*` 终态、未覆盖范围逐条保持。
- **W-4（GOAL 级未覆盖）**：读面未认证 / 多租户 / RBAC / BOLA·BFLA / 部署面未验证 /
  `R-M1` 未收口；**不得**据此宣称项目安全；**不得**宣称投递语义为那四个字（**明确否认**）。
