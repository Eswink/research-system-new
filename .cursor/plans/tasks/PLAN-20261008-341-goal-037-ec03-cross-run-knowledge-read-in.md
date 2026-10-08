---
id: PLAN-20261008-341
slug: goal-037-ec03-cross-run-knowledge-read-in
title: GOAL-037 cycle 3（EC-03）：跨 run 知识累积 —— `research_state.read` 承接 + 后一轮读到前一轮结论
status: DONE
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-342-goal-037-ec03-cross-run-knowledge-read-in.md
memory_entries:
  - a-run-must-know-its-program-before-it-executes
parent_goal: GOAL-20261008-037
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-037 的 **EC-03**（跨 run 知识累积，质量轴）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：承接面**只为这一件事**扩容（承接词表里
    已登记但未承接的 `research_state.read`，**不扩词表**）；「被用上」要**下游消费证据**
    （读到的与落库逐字一致），不是「调了两遍工具」；读面**按 run id 归属**区分轮次
    （不靠顺序猜）；**不改**任何既有判据的断言（登记面同步按既有纪律，断言强度一格未动）；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    把「跨 run 知识累积」落成**实跑可见**的能力：① **承接链五件事** —— 实现
    （`adapters/canonical/research_state_read.py`：读本 run 所属程序内**前序 run** 的
    落库结论）+ 声明（`tool_providers.yaml`）+ 绑定（会话工具表）+ 接线（两组合根）+ 放行
    （`policy.yaml` 一条只读 allow）；② **真的被用上** —— 程序跑**两轮 run**，第 2 轮经
    能力面读到第 1 轮的落库判词（**下游消费**：判词值逐字在场；按 run id 归属区分）；
    ③ **两向反证** —— 缺 provider ⇒ 点名；未放行 ⇒ preflight 点名 `POLICY_DENIED`；
    ④ 同轮同步（读面登记 / 出口普查 / 策略面镜像 / 登记计数 / 夹具）+ as-is m0。
exit_criteria:
  - id: AC-1
    criterion: >-
      **承接链五件事齐**：实现（`research_state_read.py`，入口 = run_id → 程序归属；
      缺依赖 / 不属于任何程序 ⇒ **点名**）+ 声明（`tool_providers.yaml` 的 `m12_artifact`）
      + 绑定（`("research_state.read", "m12_artifact", "research_state_read")`）+ 接线
      （SQLite / PG 两个组合根各把自己的 `ProgramStore` 传进会话工具注册面）+ 放行
      （`policy.yaml` **一条只读 allow**，scope `project`；其余段零变化）。
    verify: >-
      `rg` 逐条读数；`uv run --frozen --no-sync python -B -m pytest tests/adapters tests/api -q`
      ⇒ 全绿。
    status: PASS
  - id: AC-2
    criterion: >-
      **后一轮真的读到前一轮的结论（+ 两向反证）**。(a) 程序跑两轮，第 2 轮的
      `research_state.read` 工具结果里 `prior_runs[0].run_id` == 第 1 轮 run id、
      `verdicts` 含第 1 轮落库的**判决值**（逐字）、`reviewed_by` 逐字；
      (b) 第 1 轮的读结果是**构造性空集**（`prior_run_count == 0`，如实给，不是「读不到」）；
      (c) 两组结果落在**不同**的内容寻址制品上；(d) 反证①：撤 provider ⇒ 点名
      provider / 工具 / 能力；(e) 反证②：删 allow ⇒ preflight 点名该能力的 `POLICY_DENIED`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e -q` ⇒ 全绿；新增判据文件全绿。
    status: PASS
  - id: AC-3
    criterion: >-
      **登记面与读数**：分类判据把 `research_state.read` 从「登记理由」移入**射程内**
      （**纯收紧**）+ 出厂形态夹具同轮 + 策略面镜像表 + 差集文档（该行离开差集、进交集、
      计数 7→6 / 17→18）+ 两处登记计数（`EXPECTED_REGISTERED` 8→6、`_RELEASED` +1 /
      `_UNRELEASED_READS` −1 / scope 期望表 +1）。**谓词、阈值、受判形态一字未改**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/preflight
      tests/architecture -q` ⇒ 全绿；覆盖读数逐条给出。
    status: PASS
  - id: AC-4
    criterion: >-
      **门链 + 记录面**：ruff / format / mypy / 规模四道门绿；记录（本 PLAN、
      `RECHECK-20261008-342`）；治理 `validate.py` 绿；记录面判据绿；as-is m0 **23/23**
      （记录写完之后）。
    verify: >-
      门读数逐条 + `PASS: profile=m0; 23 deterministic checks`。
    status: PASS
---

# PLAN-20261008-341 — GOAL-037 cycle 3（EC-03）跨 run 知识累积

## 验收条件

见 frontmatter `exit_criteria`。

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 承接链五件事齐（实现 / 声明 / 绑定 / 两组合根 / 放行） | PASS |
| AC-2 | 后一轮读到前一轮结论 + 两向反证 | PASS |
| AC-3 | 登记面与读数（纯收紧） | PASS |
| AC-4 | 四道门 + 记录面 + 治理 + as-is m0 23/23 | PASS |

## 实施清单

- [x] `adapters/canonical/research_state_read.py`：实现（入口 = run_id → 程序归属；
      前序 run 的终态 + 逐字判词）。
- [x] `adapters/canonical/{read_surface,read_provider}.py`：工具面描述子 / 能力映射 /
      依赖位 / handler / 委派。
- [x] `services/api/session_tool_support.py` + `pg_composition.py` + `composition.py`：
      会话绑定行 + 装配回调依赖位 + 两个组合根接线。
- [x] `examples/config/tool_providers.yaml`（声明）+ `examples/config/policy.yaml`
      （**一条只读 allow**）+ `packages/application/preflight/policy_check.py`（镜像表）。
- [x] 新协议 `examples/protocols/cross_run_knowledge_v1.yaml` + 合约
      `cross_run_consumption_deliverable`（`examples/contracts/task_contracts.yaml`）。
- [x] `tests/e2e/cross_run_support.py` + `tests/e2e/test_cross_run_knowledge_on_the_run_path.py`。
- [x] 同步面：覆盖判据（射程 +1、登记 −1）、出厂形态夹具 +1、差集文档、两处登记计数。
- [x] `services/api/routers/programs.py`：起 run 时**先落 run 行**（含程序归属）再执行 ——
      读链工具在执行期要靠这一行反查程序（否则点不到）。
- [x] 记录面：本 PLAN、`RECHECK-20261008-342`、GOAL 行、`ALL_PLAN`、m0。

## 证据

### 交付面（WP）

| # | WP | 交付面 |
| --- | --- | --- |
| WP-1 | 实现 | `adapters/canonical/research_state_read.py`（`research_state_read`：run_id → 程序归属 → 前序 run 逐条） |
| WP-2 | 工具面 | `adapters/canonical/read_surface.py`（描述子 + 能力映射）、`read_provider.py`（依赖位 + handler + 委派） |
| WP-3 | 绑定与接线 | `services/api/session_tool_support.py`（绑定行 + `program_store` 依赖位）、`services/api/pg_composition.py`、`services/api/composition.py` |
| WP-4 | 声明与放行 | `examples/config/tool_providers.yaml`、`examples/config/policy.yaml`、`packages/application/preflight/policy_check.py` |
| WP-5 | 协议与合约 | `examples/protocols/cross_run_knowledge_v1.yaml`、`examples/contracts/task_contracts.yaml` |
| WP-6 | 判据 | `tests/e2e/cross_run_support.py`、`tests/e2e/test_cross_run_knowledge_on_the_run_path.py`（6 例） |
| WP-7 | 同步面 | `test_capability_coverage_is_implemented.py`、`test_canonical_read_provider.py`、`POLICY_SURFACE_AUDIT.md`、`test_read_grant_is_per_item.py`、`test_release_expansion_is_read_only.py` |

### 判据（逐条可被单变量按压）

| 轴 | 断言（摘要） | 落点 |
| --- | --- | --- |
| 真被用上 | 第 2 轮工具结果 `prior_runs[0].run_id` == 第 1 轮 run id、`verdicts` 含落库判决值逐字、`reviewed_by` 逐字 | `tests/e2e/test_cross_run_knowledge_on_the_run_path.py` |
| 归属正确 | 工具结果 `program_id` == 程序 id；第 1 轮 `prior_run_count == 0`（构造性空集） | 同上 |
| 可复核 | 结果落内容寻址制品、digest 在场；两轮的制品 id **不同** | 同上 |
| 反证① | 撤 provider ⇒ `run.failed` 消息点名 provider / 工具 / 能力 | 同上 |
| 反证② | 删 allow ⇒ preflight `FAIL` 且 finding 点名 `POLICY_DENIED` + 该能力 | 同上 |

> **一次真红并修（m0 首跑，如实登记）**：`python/format-check` 判红 ——
> `tests/architecture/python/test_capability_coverage_is_implemented.py`（删登记条留下的空行）
> 与 `adapters/canonical/research_state_read.py` 未过 `ruff format`。处置 = **格式化这两个文件**
> （不调阈值、不改判据），随后**重跑全量 m0** 取终局读数。

### 门（实测读数）

| 门 | 读数 |
| --- | --- |
| `ruff check` | `All checks passed!` |
| `ruff format --check`（apps/services/packages/adapters/tests） | 绿（首跑红 ⇒ 格式两个文件后绿） |
| `mypy`（strict） | `Success: no issues found in 1160 source files` |
| 新判据 | `tests/e2e/test_cross_run_knowledge_on_the_run_path.py` **6 passed** |
| 广面 | e2e + application + architecture + adapters + contracts + loaders + observability + tooling + api **4583 passed, 95 skipped** |
| as-is m0 | **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` **24** / `FAILED [` **0** / **5417 passed, 20 skipped**；收集数 +9 = 新判据 6 例 + 源文件参数化（新模块 3 个 × 规模门）逐文件分解；`skipped` 20 未升）。日志 `scratch/m0-goal037-cycle3-rerun.log`（gitignored）（首跑**真红**于 `python/format-check` ⇒ 格式化后重跑取值） |

## 影响报告

- **Domain / API / schema 变化**：无新域类型（复用 `ResearchRun.program_id` +
  `ProgramStore`）；新增一份协议 / 一条合约 / 一条策略 allow。
- **安全 / 凭据变化**：新增**一条只读**放行（`research_state.read`，scope `project`）；
  `default_effect` / `deny` / `require_approval` / `allow_with_constraints` 一格未动。
- **兼容性 / 迁移风险**：无迁移；起 run 的写序在**程序面**改为「先落行再执行」
  （HTTP 面保持不变）—— 理由：执行期读链要靠那一行反查程序归属。
- **观测隐私**：读面载荷只含判词取值 / 状态 / digest（不含新敏感面）；读面登记与出口普查
  同轮同步。
- **上游版本影响**：无。
- **下一项任务**：EC-04（幂等与中断）/ EC-05（自举收口）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | IN_PROGRESS | 立项：承接链五件事 + 两向反证 + 同步面；判据 6 例已落地（全绿）。 |
| 2026-10-08 | DONE | 四条 AC 全 PASS：承接链五件事齐；两轮实跑 6 例全绿（下游消费 = 前一轮判决值逐字 + 按 run id 归属）；两向反证（撤 provider 点名 / 删 allow ⇒ preflight 点名 `POLICY_DENIED`）；同步面（覆盖判据 / 夹具 / 差集文档 / 两处登记计数）；四道门绿。**一处实现期真红并修**：起 run 需**先落行**（读链执行期靠它反查程序）—— 已登记 `RECHECK-20261008-342` W-1。`RECHECK-20261008-342` 独立复检。 |
