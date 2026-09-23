---
id: RECHECK-20260923-141
plan_id: PLAN-20260923-140
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-23
completed_at: 2026-09-23
reviewer: independent-verify-script + root-agent-goal-012-ec01
baseline_ref: 5920172
checked_head: 5ae2d56
---

# RECHECK-20260923-141 — 冻结门的显式策略通道（GOAL-012 EC-01 / PLAN-140）

## 检查范围

**不采信本 cycle 的自我陈述**，而是分成两层各自成立：

1. **独立复检脚本** `scratch/verify_goal012_c1.py`——**只读 / 只用标准库 / 不 import 仓库代码**，
   在当前树与**基线树**（`git worktree` 到 `ccb8f3e`，即本 cycle 之前的 tip）上各跑一遍；
2. **实跑层**——本 cycle 的判据 / 套件 / m0 / CI 的原始输出（逐条落 `scratch/`）。

脚本断言的是**授权边界**（用户拍板的三条：不放宽 `classify_risk`、不改 `PreflightStatus.WARN`
与 `passed` 的语义、不让 WARN 无条件可冻）与**通道本体**（接受条件四条、留痕七键、拒冻消息的
既有前缀 + 逐条点名），加上三处按压记录的条数。

## 检查结果

### 一、独立复检脚本（两棵树成对）

| 树 | 结果 | 说明 |
| --- | --- | --- |
| **当前树**（`5ae2d56`） | `checked=28 failures=0`（exit 0） | 28 条断言全绿（授权边界 4 + 通道本体 21 + 按压记录 3） |
| **基线树**（`ccb8f3e`，本 cycle 之前的 tip；`git worktree` 到仓外） | `checked=22 failures=19`（exit 1） | **判据不空转**：19 条红覆盖通道本体（`policy_acceptance.py` 不存在、留痕七键、拒冻消息、事件 payload）与三处按压记录缺失；而 `classify_risk` / `passed` / `_status` 三条**在基线树上是绿的**——它们本就未被本 cycle 改动 |

⇒ **成对成立**：新判据在改动前红、改动后绿；而「不得放宽」的四条在**两棵树上都绿**。

### 二、授权边界（逐条，脚本 + 源码）

| # | 边界 | 判据 | 结论 |
| --- | --- | --- | --- |
| B-1 | `classify_risk(EXECUTE, …) → HIGH` **无条件** | `packages/domain/tools.py` 的正则断言（两棵树皆绿） | **未动** |
| B-2 | `PreflightReport.passed` 仍「PASS 才 passed」 | `packages/domain/protocols.py` 逐字断言 | **未动** |
| B-3 | `_status()`：ERROR→`FAIL` / WARNING→`WARN` / 否则 `PASS` | `preflight.py` 函数体断言 | **未动** |
| B-4 | 通道只认 `TOOL_RISK_ELEVATED` + `EffectClass.EXECUTE`；允许集只有 `ALLOW` / `ALLOW_WITH_CONSTRAINTS` | `policy_acceptance.py` 三条常量断言 | **在位** |

### 三、行为层（实跑，全部离线）

| 判据 | 命令 | 结果 |
| --- | --- | --- |
| 通道本体（AC-1…AC-5） | `pytest tests/application/preflight/test_policy_allowed_execute_freeze.py -q` | **8 passed**（`egress guard: judged 0; blocked 0`） |
| 真实 preflight 路径上的三段（含成对反证） | `pytest tests/e2e/test_sandbox_experiment_reachability.py -q` | **4 passed**（其中 1 条 `requires_docker`；`-m "not requires_docker"` ⇒ 3 passed / 1 deselected） |
| API 级端到端（真 run 过编排、冻结 + 事件留痕） | `pytest tests/api/test_runs_api.py tests/api/test_failed_run_semantic_digest_api.py -q` | **26 passed** |
| 既有 preflight/冻结语义（不得削弱） | `pytest tests/application/test_m2_policy_budget.py test_m2_audit.py test_protocol_compiler.py test_m12_manifest_freeze.py -q` | **40 passed**（两处旧的拒冻面 `BUDGET_RESOURCE_UNMAPPED` / `POLICY_APPROVAL_REQUIRED` **仍拒冻**，断言一字未改） |

### 四、按压层（三处，先红后绿，记录落 `scratch/`）

| # | 按压 | 期望 | 实测 |
| --- | --- | --- | --- |
| 1 | 把留痕写成空列表（`preflight.py`） | 只有留痕类判据红 | **2 failed / 6 passed**，红的两条恰是 `test_a_policy_allowed_execute_risk_may_freeze` + `test_the_freeze_event_carries_the_same_trace`（`scratch/goal012-c1-press1.txt`）；复原 ⇒ 8 passed |
| 2 | 停用通道（恢复「非 PASS 一律拒冻」） | 通道类 + 点名类红 | **5 failed / 3 passed**，且三条**点名**断言逐字失败于旧消息 `cannot freeze manifest before a passing preflight`（`scratch/goal012-c1-press2.txt`）——正好证明拒绝语义**点名缺失事实**这条要求真的被判据看着；复原 ⇒ 8 passed |
| 3 | 让任意警示可转换 + 非 EXECUTE 也可接受 | 两条「不可转换面」红 | **2 failed / 6 passed**（`scratch/goal012-c1-press3.txt`）；复原 ⇒ 8 passed |

### 五、门与治理（本 cycle 实跑）

| 门 | 结果 |
| --- | --- |
| 本机 m0（`--profile m0 --keep-going`，CI 同形 env：DSN 钉住 + `LLM_MAIN_KEY=""`） | **23/23**：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24 行**（含资产封印）、**0 FAIL / 0 ERROR**、exit 0（`scratch/goal012-c1-m0.log`） |
| `python/tests`（同上日志） | **4403 passed / 18 skipped / 0 failed**；`egress guard: judged 779; blocked 8`（8 条是判据对 `198.51.100.1` 的**故意**探针） |
| 定向套件（`tests/api tests/application tests/e2e`） | **1319 passed / 11 skipped**；5 条红**全部溯源**：4 条为既有跨套件顺序签名（`test_worker_plane_composition`×3 + `test_pg_crash_restart`，**单独跑 7 passed**），1 条是本 cycle 的**真回归**（见下）并当轮修好 |
| `ruff check` / `ruff format --check` / `mypy` | 全绿（含新模块与新判据文件） |
| 治理 `validate.py` | 绿 |
| 规模门禁（50 行函数 / 450 行文件） | `tests/tooling/test_python_source_limits.py` **1003 passed** |
| CI | tip `5ae2d56`：M0 [35820350936](https://github.com/Eswink/research-system-new/actions/runs/35820350936) **六 job 全 success**（逐 job 实查，终态 `completed`）；CodeQL [35820350713](https://github.com/Eswink/research-system-new/actions/runs/35820350713) **3/3 success** |

## 本 cycle 自己撞到并处置的两件事（如实登记）

1. **真回归（1 条）**：`tests/api/test_failed_run_semantic_digest_api.py::test_a_failed_run_without_a_freeze_event_has_no_semantic_digest`
   用 `sort_analysis_v1` 当「永不冻结」的载体 ⇒ 通道落地后该 run 会冻结，用例红。
   **处置**：把该 fixture 的**允许撤掉**（`code.execute` 判 `DENY`）⇒ run 真的在冻结前被拒，
   「没有 `manifest.frozen` ⇒ 引用必须是 None」这条边界语义被**更精确**地钉住（不是删掉它）。
2. **既有的真实控制面缺口（新登记，未修）**：真实控制面的 preflight 求值是
   `NativePolicyEvaluator` + `examples/config/policy.yaml`，而该策略**未放行**
   `sort_analysis_v1` 的 `evidence.read` ⇒ 该协议在真实控制面上是 **`FAIL`**（不是 `WARN`）⇒
   通道根本不会被走到。本 cycle **不**自行放宽策略面（那是放宽安全面，需拍板），
   只登记为 **W-A**。

## 结论

**PASS_WITH_WARNINGS**：PLAN-140 的 AC-1…AC-9 全部达成且证据成对（判据先红后绿、授权边界
两棵树都绿、m0 23/23、零出网）。本 PLAN 的剩余风险**不外溢**：通道只在「显式允许 + 留痕」
下开启，未声明一律拒冻并点名。

**W 列表（本 PLAN 的残余，交给 GOAL-012 的残余节）**

- **W-A**：真实控制面（`NativePolicyEvaluator` + `examples/config/policy.yaml`）对
  `sort_analysis_v1` 的 `evidence.read` 判 `DENY` ⇒ 该协议在真实控制面上是 `FAIL` 而非 `WARN`；
  本 cycle 的端点级证据取自 run-ready/live 装配（GOAL-009/010/011 全部真实 run 的同一载体）。
  **不在本循环自行放宽策略面**；EC-02 若要跑真实控制面，需要一次拍板。
- **W-B**：run-ready 装配下 `sort_analysis_v1` 冻结**之后**收敛 `FAILED`，逐字判词
  `task … produced malformed result: session result for task … carries no structured output`
  ⇒ 冻结门**不再是**阻断点，剩下的堵点在会话/结构化输出这条路上（EC-02 的输入）。
- **W-C**：`evidence.read` 这条既有缺口与本 cycle 的通道**无关**，但会让「真实控制面」与
  「run-ready 装配」对同一协议给出不同结论（`FAIL` vs `WARN`）——口径差异如实登记。
- 4 条跨套件顺序失败（`test_worker_plane_composition`×3 + `test_pg_crash_restart`）**单独跑全绿**，
  与本次改动无关（既有签名）。
