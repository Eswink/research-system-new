---
id: PLAN-20260925-168
slug: missing-executor-must-be-named
title: D-01(b) 判据化：缺执行体 ⇒ preflight 逐字点名能力（反向搜索 + 成对反证）
status: DONE
created_at: 2026-09-25
updated_at: 2026-09-25
parent_goal: GOAL-20260925-016
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260925-016 的 **2026-09-25 用户拍板（goal 模式）第 (1) 条**：
    **D-01 → 取 (b)** —— 出厂组合根**不**自己接执行体缝（维持 `ApiDeps.tool_providers`
    生产为空）；交付 = 把「缺执行体时 preflight **点名**哪个能力没人执行」钉成**机械判据**，
    **不是**新增点名逻辑。**已核实**点名逻辑已存在（`packages/application/preflight/checks.py`
    的 `check_tools`：`PreflightFindingCode.TOOL_UNAVAILABLE` +
    `"no provider is available for capability {…}"`）⇒ 本 PLAN 的交付是**判据 + 反向搜索证据**
    （证明它是稳定事实、而非「碰巧在场」），**既有实现不得改动**；若判据要求改点名词，属
    **改产品行为** ⇒ **停下并登记**，不自行改。**D-01 的 (a)（组合根自己接执行体缝）明确不取**。
    **本 PLAN 的边界**：只增一个**判据测试文件** + 记录，**零产品代码改动**、**零策略面改动**、
    **零门禁改动**、**不新增依赖**、**零真实出网调用**（判据全部离线跑：夹具目录 + 编译 +
    预检纯函数）。push-to-main-for-CI（只推 main、不 force、不重写历史、不推旁支）。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260925-169-missing-executor-must-be-named.md
memory_entries:
  - .cursor/memory/entries/MEM-20260925-134-naming-contract-needs-a-pair-and-a-single-source.md
---

# PLAN-20260925-168 — D-01(b) 判据化（GOAL-016 / EC-01）

## 目标

把用户拍板的 **D-01(b)** 从「口径」变成**可复核的机械判据**：出厂组合根**不**接执行体缝
（`ApiDeps.tool_providers` 生产为空）时，preflight 必须**逐字点名哪个能力没人执行**。

**本 PLAN 不改产品行为**：点名逻辑已在树（`check_tools`），本 PLAN 只**钉住**它，并给出
「这不是碰巧」的证据。

## 验收条件

- **AC-1｜行为证据（正向）**：把**出厂目录**（`services.api.catalog` = 产品路径）的
  `tool_providers` 置空后，经**产品入口** `compile_and_preflight` 编译 + 预检 ⇒
  计划里**每一条** `ToolRequirement` 都得到一条 `TOOL_UNAVAILABLE`，消息**逐字等于**
  `no provider is available for capability {能力名}`，且归属指向**该 phase**。
- **AC-2｜行为证据（反证成对）**：同一协议、同一判据，**只**恢复出厂 provider ⇒
  上述点名**全部消失**，且该码在报告中**计数归零**。
- **AC-3｜反向搜索**：点名模板 `no provider is available for capability` 在**生产源**
  （`packages/` / `services/` / `adapters/`）里**只有一个来源**
  （`packages/application/preflight/checks.py`）⇒ 命名是**单一实现点的稳定事实**。
- **AC-4｜按压自身**：把消息模板改坏（**内存内变体**）⇒ 匹配器判空 ⇒ 判据不是恒真。
- **AC-5｜零产品行为改动**：`git diff` 证明 `packages/application/preflight/` 下的**产品代码
  零改动**；策略面（`examples/config/policy.yaml`）与门禁零改动。

## 实施清单

- [x] WP1：写判据 `tests/application/preflight/test_missing_executor_is_named.py`
  （走产品入口 + 出厂目录；四个断言面 = AC-1…AC-4）。
- [x] WP2：实证「缝为空」的形态——探针确认 `provider_ids == ()` 且报告里**同时**出现
  **编译面**（`no tool provider exposes capability …`，`CompileFindingCode`）与
  **预检面**（`no provider is available for capability …`，`PreflightFindingCode`）两条链；
  判据只断言**后者**（前者是另一条链，写进判据的性质披露）。
- [x] WP3：修一处**真实的判据缺陷**——首版按「能力名」配对，被
  `workspace.read`（**两个 phase** 都需要）判红 ⇒ 改成按 `(phase_id, capability)` 配对。
  这是判据自身的缺陷，**未**改产品代码。
- [x] WP4：lint / 规模门禁自查（`ruff check` + `ruff format --check` +
  `test_python_source_limits.py` + `test_module_file_naming.py`）。
- [x] WP5：记录（本 PLAN + RECHECK + MEM）与 GOAL-016 回写。

## 证据（本地）

- 判据：`tests/application/preflight/test_missing_executor_is_named.py`（4 个测试）。
  - `uv run --frozen --no-sync python -B -m pytest
    tests/application/preflight/test_missing_executor_is_named.py -q` ⇒ **`4 passed`**。
- 探针（只有观测，不是判据）：`scratch/goal016_c1_probe.py` ⇒ 缝为空时
  `tool_requirements` 的 6 条 `provider_ids` 全为 `()`；报告里 6 条预检面点名 +
  6 条编译面点名；恢复 provider 后该码计数 **0**；反向搜索命中
  **仅** `packages/application/preflight/checks.py`。
- 规模 / 命名门禁：`test_python_source_limits.py` + `test_module_file_naming.py` ⇒
  **`1054 passed`**；新文件 **213 行**（软阈值 300 行以内）。
- lint：`ruff check` = `All checks passed!`；`ruff format --check` = `1 file already formatted`。
- m0：见 GOAL-016 的 CI 台账（本 PLAN 所在 cycle 的终态行）与 RECHECK-169。

## 残余（本 PLAN 不处置）

- **点名在**「provider 已声明但**全部不可用**」（健康 / 信任面）时有**另一条**消息
  （`no healthy provider is available for capability {…}`）。它属第三种形态，
  本 PLAN 的判据**不**覆盖（已在判据里披露），**不**声称已覆盖。
- 编译面的同名码（`CompileFindingCode.TOOL_UNAVAILABLE`）**不**在本判据的断言面内。
- **`M-1` 本身仍是待拍板项**：本 PLAN 只落地 D-01(b) 的判据，**不**改变「出厂组合根不接
  执行体缝」这一事实。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-25 | IN_PROGRESS | derive：从 GOAL-016 的 EC-01 圈定主题（D-01(b) 判据化），本文件 + `ALL_PLAN` 投影 + `parent_goal` 同提交。 |
| 2026-09-25 | IN_PROGRESS | WP1–WP3：判据落盘；探针实证两条链；修判据自身的「按能力名配对」缺陷（`workspace.read` 跨两 phase）。 |
| 2026-09-25 | IN_PROGRESS | WP4：`ruff check` / `ruff format --check` / 规模门禁 / 命名门禁全绿；判据 `4 passed`。 |
| 2026-09-25 | DONE | WP5：记录与 GOAL-016 回写完成；复检 `RECHECK-20260925-169` 见 `latest_recheck`。 |

## 影响报告

- **改动**：新增一个判据测试文件（`tests/application/preflight/`）；无产品代码改动。
- **lint / typecheck / test**：`ruff check` = `All checks passed!`、
  `ruff format --check` = 已格式化；判据 `4 passed`；规模 + 命名门禁 `1054 passed`。
- **Domain / API / schema 变化**：无。
- **安全 / 凭据变化**：无（判据零出网、零凭据读取；`egress guard` 判词 = `blocked 0`）。
- **兼容性 / 迁移风险**：无——纯新增判据，不改任何既有断言与门禁。
- **上游版本影响**：无（未新增依赖、未改 pin）。
- **下一项任务**：GOAL-016 的 **EC-02（D-02(b) 口径判据：读能力逐条授权、不成类放行）**。
