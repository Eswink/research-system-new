---
id: PLAN-20261008-331
slug: goal-036-ec01-02-review-read-onboarding
title: GOAL-036 cycle 1（EC-01/EC-02）：`review.read` 的勘察定稿 + 端到端承接链（声明 + 实现 + 绑定 + 接线 + 放行）
status: DONE
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-332-goal-036-ec01-02-review-read-onboarding.md
memory_entries:
  - releasing-a-read-capability-moves-registry-pins
parent_goal: GOAL-20261008-036
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-036 的 **EC-01 + EC-02**（勘察定稿 + 端到端承接链）。授权原文见该 GOAL
    的 `authorization.ref`。**本 PLAN 专属边界**：只承接**一条**能力（`review.read`）；
    **不改**写面 / 执行面 / 审批面（只放行**只读**一条）；**不建第二套**读口径（复用既有
    `ReviewFindingStore.for_run`）；缺依赖必须**点名**不可用（**不得**返回空列表冒充
    「没有评审」）；同轮同步面**只限** `_IN_SCOPE` 与出厂形态夹具（**纯收紧**）；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    把 `review.read` 从「词表里有、声明面零承接、策略面零放行」推进到**五件事齐**：
    ① **勘察定稿** —— 为什么是它（读数逐条）+ 承接机制与规模约束（可选依赖形态、450 行
    上限 ⇒ 另立模块）（EC-01）；② **承接链** —— 实现（新模块读 `ReviewFindingStore`）+
    声明（`tool_providers.yaml`）+ 绑定（会话工具表）+ 接线（两个组合根 + 装配回调）+
    放行（`policy.yaml` 新增**一条**只为读的 `allow`）（EC-02）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **勘察定稿**：`review.read` 的四条读数（词表有 / 声明面零 / 策略面零 / 分类理由过期）
      与承接机制读数（可选依赖三条先例 + `read_provider.py` 行数）逐条在场，且**在实现里
      被引用**（模块 docstring 直接说明「为什么另立」）。
    verify: >-
      `rg -n "review.read" examples/ services/ adapters/ packages/` 的逐条读数 + 本 PLAN 的
      「证据」节。
    status: PASS
  - id: AC-2
    criterion: >-
      **承接链五件事齐**：(a) 实现 `adapters/canonical/review_read.py`（缺
      `ReviewFindingStore` ⇒ 点名拒绝；空 run_id ⇒ 点名拒绝；**只读**）；
      (b) 工具面描述子 `read_surface._TOOL_DESCRIPTIONS` / `_TOOL_CAPABILITIES`
      （`review_read` → `review.read`）；(c) provider 执行面 `read_provider.py` 的依赖位 +
      handler（行数仍 ≤ 450）；(d) 绑定 `DEFAULT_SESSION_TOOL_BINDINGS` +
      `canonical_read_register` / `sqlite_session_tools` 的依赖面 + 两个组合根接线；
      (e) 声明 `tool_providers.yaml`（`m12_artifact` capabilities += 一条）；
      (f) 放行 `policy.yaml` 新增**一条** `allow`（`default_effect` / `deny` /
      `require_approval` / `allow_with_constraints` **零变化**，由判据钉住）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters/canonical tests/api
      tests/architecture -q` ⇒ 全绿；`rg` 逐条读数（声明 / 绑定 / 接线 / allow）。
    status: PASS
  - id: AC-3
    criterion: >-
      **门**：两脚本触及面 `ruff check` / `ruff format --check` / `mypy`（strict）/
      规模（450·50）全绿；`tests/architecture/python/test_capability_coverage_is_implemented.py`
      在主判据（声明 ⇒ 实现）上仍绿；策略面差集判据仍绿。
    verify: >-
      四道门命令 + 两条判据的读数。
    status: PASS
---

# PLAN-20261008-331 — GOAL-036 cycle 1（EC-01/EC-02）

## 验收条件

见 frontmatter `exit_criteria`。

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 勘察定稿（四条读数 + 承接机制 + 规模约束） | PASS |
| AC-2 | 承接链五件事齐（实现 / 声明 / 绑定 / 接线 / 放行） | PASS |
| AC-3 | 四道门 + 既有判据（能力覆盖 / 策略面 / m2 审计）仍绿 | PASS |

## 实施清单

- [x] `adapters/canonical/review_read.py`（新，**68 行**）：`review_read(findings, args)`。
- [x] `adapters/canonical/read_surface.py`：描述子与能力映射各 +1。
- [x] `adapters/canonical/read_provider.py`：依赖位 `review_store` + handler + 委派方法（**421 / 450**）。
- [x] `services/api/session_tool_support.py`：绑定 +1；装配回调依赖面 +1。
- [x] `services/api/composition.py`（经 `sqlite_session_tools` 传 `ports.review_findings`）/
      `pg_composition.py`（传 `c["review_findings"]`）：把各自的 `ReviewFindingStore` 传进去。
- [x] `examples/config/tool_providers.yaml`：`m12_artifact` capabilities += `review.read`。
- [x] `examples/config/policy.yaml`：新增**一条** `allow`（`review.read`，scope=project）。
- [x] **同轮同步面（实测发现，见 GOAL 决策 ⑥）**：
      `packages/application/preflight/policy_check.py::_CAPABILITY_SCOPE`（**+1**）、
      `docs/architecture/POLICY_SURFACE_AUDIT.md`（行**离开差集**进交集清单 + 计数 + 变更注）、
      `tests/application/preflight/test_read_grant_is_per_item.py`（`EXPECTED_REGISTERED` 8→7）、
      `tests/application/preflight/test_release_expansion_is_read_only.py`（`_RELEASED`+1 /
      `_UNRELEASED_READS`−1 / scope 表+1）。
- [x] `tests/adapters/canonical/test_canonical_read_provider.py`：出厂形态夹具 +1（同轮同步）。
- [x] `tests/architecture/python/test_capability_coverage_is_implemented.py`：`review.read`
      从登记表移入 `_IN_SCOPE`（**纯收紧**）。

## 证据

### 勘察读数（实测）

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 1 | 词表里有 `review.read` | `examples/config/capabilities.yaml` | 46 条含它 |
| 2 | 声明面零承接 | `tool_providers.yaml` 全量反查 | distinct **19**，**不含** `review.read` |
| 3 | 策略面零放行 | `examples/config/policy.yaml` | `allow` 无 `review.read` ⇒ `default_effect: DENY` |
| 4 | 分类理由过期 | `test_capability_coverage_is_implemented.py::_OUT_OF_SCOPE_REASONS` | 原文指向「评审走 task/handoff 面」—— GOAL-035 EC-01 已改变 |
| 5 | 依赖是**可选**的 | `read_provider.py` 的 `budget_ledger` / `experiment_store` / `run_store` | 缺省 `None` ⇒ 工具点名不可用（不返回空壳） |
| 6 | 450 行上限 | `wc -l adapters/canonical/read_provider.py` | **410 / 450** ⇒ 新实现另立模块（先例 `run_read.py`，50 行） |
| 7 | 夹具同轮同步是既成纪律 | `test_canonical_read_provider.py::_PROVIDER` 注释 | 原文：「夹具少列一条会让……判据假红（实测）」 |

### 实现读数（实测）

| # | 读数 | 值 |
| --- | --- | --- |
| 1 | 新模块行数 / provider 行数 | **68** / **421（≤450）** |
| 2 | 五件事逐条在场 | 实现 / 工具面 / 绑定 / 两组合根接线 / 声明 + 放行（`rg` 读数见 `RECHECK-332` 第 2 节） |
| 3 | 三条边独立探针 | 正路 `count=1` + 逐条判词在场；缺 store ⇒ **点名**；空 run_id ⇒ **点名**；空结果 ⇒ `count=0`（**不**与不可用混同） |
| 4 | 四道门 | `ruff check` 通过 / `format` 通过 / `mypy` `Success`（3 文件）/ 规模 68·421 |
| 5 | 全量 python 套件 | **5361 passed, 20 skipped**（收集数 +1 逐文件分解 = 新模块进源文件参数化面） |
| 6 | 策略面判据（同步面） | `tests/application/preflight` **60 passed**（含两条 pin 的反证臂全绿） |
| 7 | **as-is m0**（冻结树，全部记录写入之后） | **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` 24 / `FAILED [` 0 / **5359 passed, 20 skipped**；收集数 **+1** 逐文件分解 = 新模块 `adapters/canonical/review_read.py` 进源文件参数化面（1151→1152）；`skipped` 20 未升） |

## 影响报告

- **Domain / API / schema 变化**：预期**零**（复用既有 Port 与既有读面口径；无新 DTO / 路由）。
- **安全 / 凭据变化**：`policy.yaml` 新增**一条只读** `allow`（授权 (0) 的「可以决定」面）；
  其余策略面零变化。
- **兼容性 / 迁移风险**：新增声明 / 绑定 / 工具 ⇒ 供应商面**只增**；既有能力的工具面不变。
- **观测隐私**：新工具返回**评审判词**（合同声明判据的逐条判词）—— 与既有
  `GET /runs/{id}/reviews` 同一内容面；出口普查由既有判据覆盖（实现后复核）。
- **上游版本影响**：无。
- **下一项任务**：cycle 2（EC-03 真用判据 + EC-04 登记面与覆盖读数）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | IN_PROGRESS | 勘察定稿 + 承接链实现开工（五件事逐件落地）。 |
| 2026-10-08 | DONE | 五件事齐 + 四道门绿 + 全量套件绿（5361/20）+ 同轮同步面 5 处落定（加法/搬迁，谓词不变，反证臂全绿）。`RECHECK-20261008-332` 独立复检（PASS_WITH_WARNINGS，`W-1` = 同步面清单建档时不全，已修正 `fix_policy`）。 |
