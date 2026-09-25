---
id: PLAN-20260925-182
slug: live-switch-and-observability-job-isolation
title: D-11 live 显式开关（凭据由充分降为必要）+ D-13 观测阈值判据的作业隔离
status: DONE
created_at: 2026-09-25
updated_at: 2026-09-25
parent_goal: GOAL-20260925-017
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260925-017 的 **EC-02**（D-11 取 (a)，用户 2026-09-25 拍板授权实施）
    与 **EC-03**（D-13 取 (a) 的协议 + 授权接近 (b) 的作业隔离）。授权边界（严格）：
    **D-11**：a) 默认门（无开关）必须**仍离线、仍不跑 live 用例**且**行为可判**；
    b) 开关 + 凭据**都有** ⇒ 跑；开关有、凭据缺 ⇒ **如实 skip 或具名失败**（二选一，
    口径写进 runbook）；c) **所有** live 用例必须经**同一道**开门逻辑 —— **无第二套判据**；
    d) **不得**拓宽 `tests/egress_guard.py` 的放行面（放行面仍是 marker 一个；开关只决定
    「进不进 run」）；e) 文档同源：`docs/integration/LIVE_MODEL_RUNBOOK.md` 与其命令按新
    口径**逐字**更新。**D-13**：a) **不**抬阈值、**不**改测量语义（RSS 仍是整进程 RSS，
    不得换成相对基准绕过）；b) **不**改成非阻断 / warning（那等于废掉这道门）；
    c) 拆分后**「本作业红 ⇒ 整体 CI 红」必须保持**；d) workflow 是治理面 ⇒ 改动必须
    **最小可复核**（逐行理由 + 前后作业结构 + 失败传播路径留档）。**先核实现状**；
    若判定「现状已足够」⇒ **如实登记 + 证据，不为交付物而改**。
    push-to-main-for-CI（只推 main、不 force、不重写历史、不推旁支）。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260925-183-live-switch-and-observability-job-isolation.md
memory_entries:
  - .cursor/memory/entries/MEM-20260925-141-one-switch-one-reader-and-one-job-per-threshold.md
---

# PLAN-20260925-182 — D-11 live 显式开关 + D-13 作业隔离（GOAL-017 EC-02 / EC-03）

## 目标

**WP1（D-11）**：把「环境里恰好有凭据」从 live run 的**充分**条件降为**必要**条件——
开门要一个**显式开关**（`RESEARCHOS_LIVE_E2E`，值**恰为** `1`）。开关名**只有一个声明点**
（产品常量 `LIVE_RUN_SWITCH`），环境**只有一个读取点**（`tests/e2e/live_switch_support.py` 的
`live_e2e_switch_enabled`），全部 live 用例（12 个模块）经**同一道**开门逻辑；runbook 逐字同源。

**WP2（D-13）**：把**整进程资源阈值**判据（`tests/observability/test_telemetry_overhead.py` 的
`_MAX_RSS_GROWTH_MIB = 128.0` 与线程上限）从 `quality-*` 的 4400+ 用例进程里**拆到专用作业**
单独执行——判据、阈值、测量语义**一字不动**；矩阵与拆前一致（ubuntu + windows）⇒ 平台覆盖不减；
作业失败 ⇒ 整体 CI 红（与拆前同一条传播路径）。

## 验收条件

- **AC-1｜单一开关声明 + 单一读取点**：`LIVE_RUN_SWITCH` 在产品层**只赋值一次**；含该字面量的
  文件是**显式清单**；`os.environ`/`getenv` 与开关名字同现的文件**只有一个**
  （`tests/e2e/live_switch_support.py`——**单一职责小模块**，理由见「实施清单」的最后一条）；
  `packages/application/**` **零**环境读取（开关是**必填**参数 ⇒ 漏传即 `TypeError`）。
- **AC-2｜无第二套判据**：12 个带 `requires_live_llm` 的模块**全部**经门（`live_switch=`）或经
  同一谓词；模块清单**逐条列出**（新加一个就红）。
- **AC-3｜三态实跑**：① 凭据在场、开关关 ⇒ live 用例 **skip 且点名开关**、`blocked 0`；
  ② 开关开、凭据缺 ⇒ **如实 skip 并点名凭据**（口径 b）、`blocked 0`；
  ③ 开关 + 凭据 + runtime 齐备 ⇒ 门**开**且真实 run **跑到终态**（本 GOAL 唯一一次真实出网，
  最小必要次数）。
- **AC-4｜门禁面零放宽**：`tests/egress_guard.py` 的放行面仍是 marker 一个（判据 + 按压取证）；
  判据面只**收紧**（理由逐条点名 → 未满足条件全列）。
- **AC-5｜runbook 同源**：§4 写两个开关的分工 + 三条件 + 操作者命令（`RESEARCHOS_LIVE_E2E=1` 逐字）；
  §7 两行 live 证据行点名开关；§8 记「撤销只关三条件里的一格」。判据按**常量**比对。
- **AC-6｜D-13 判据零改动**：`git diff -- tests/observability/test_telemetry_overhead.py` 为**空**；
  阈值常量逐字未改。
- **AC-7｜D-13 前后结构 + 传播留档**：作业数 6 → 7；新作业无 `continue-on-error` / `if:`
  （与既有作业同形态）⇒ 失败传播路径不变；`tests/tooling/test_m0_ci_coverage.py` 全绿
  （新作业按序先预热 tokenizer；`gate_jobs` 反证仍成立）。
- **AC-8｜静态门 + as-is 本机 m0**：`ruff check` / `ruff format --check` / `mypy` 全绿；
  as-is 本机 m0 取终态行。

## 实施清单

- [x] WP1-A 产品侧：`LIVE_RUN_SWITCH` 常量 + `live_switch` **必填**参数 + 理由文案（开关排最前）。
- [x] WP1-B 操作者边界：`live_e2e_switch_enabled()`（**唯一**环境读取点）+ `live_run_switch_off_reason()`。
- [x] WP1-C 12 个 live 模块全部接到同一道逻辑（8 处经门、4 处经谓词）。
- [x] WP1-D 4 个既有门判据按三条件更新（**只收紧**）；`test_ec04_live_first_run.py` 的离线判据
      改为**独立重算未满足条件并逐条核对**（原「二选一」写法在「只配 runtime 忘开开关」时
      会误红——本 cycle 实测发现并修掉）。
- [x] WP1-E 新判据 `tests/architecture/python/test_live_switch_is_single_source.py`（14 条）+ 6 次按压。
- [x] WP1-F runbook §4 / §7 / §8 逐字同源。
- [x] WP2-A 新作业 `observability-overhead`（ubuntu + windows）+ `quality-*` 侧
      `PYTEST_ADDOPTS: --ignore=tests/observability/test_telemetry_overhead.py`。
- [x] WP2-B 机制取证（collect-only 3 → 0）+ 隔离进程实跑 + 阈值零改动 + 传播键计数。
- [x] WP1-G **搬迁（m0 实跑抓出的真缺陷）**：第一次把两个开关函数放进
      `tests/e2e/live_run_support.py` ⇒ 该文件 **477 行 > 450 行硬上限** ⇒ m0 第 1 跑
      `FAILED: 1 check(s): python/tests=1`（`tests/tooling/test_python_source_limits.py`
      的 `test_python_source_size_limits[tests\e2e\live_run_support.py]`）。**处置 = 拆出
      `tests/e2e/live_switch_support.py`（单一职责、43 行）并把 12 处 import 改指向它**，
      `live_run_support.py` 回到 **449 行**；**未**动 450 / 50 这两个阈值（那是放宽）。

## 证据面（实跑）

| 面 | 命令 / 判据 | 结果 |
| --- | --- | --- |
| 新判据 | `pytest tests/architecture/python/test_live_switch_is_single_source.py` | `14 passed` |
| 按压（6 处，逐次还原） | `python scratch/goal017-d11-press.py` | `pressed=6 failures=[]`（6/6 `RED-OK`，每次 sha256 核对**逐字节还原**；**搬迁后复跑仍 6/6**） |
| 三态 ① | `RESEARCHOS_AGENT_RUNTIME=openhands pytest tests/e2e/test_ec04_live_first_run.py` | `1 passed, 1 skipped`；skip 理由 = `live run switch is not on (set RESEARCHOS_LIVE_E2E=1 to open)`；`blocked 0` |
| 三态 ② | `LLM_MAIN_KEY= RESEARCHOS_LIVE_E2E=1 RESEARCHOS_AGENT_RUNTIME=openhands pytest …` | `1 passed, 1 skipped`；skip 理由 = `credential 'LLM_MAIN_KEY' is not resolvable`；`blocked 0` |
| 三态 ③（**最终修订版**） | `RESEARCHOS_LIVE_E2E=1 RESEARCHOS_AGENT_RUNTIME=openhands pytest …` | `1 passed, 1 skipped`（**live 用例 passed**、离线判据因门开而 skip）；`judged 3 connection attempt(s); blocked 0`；81.14s；日志 `scratch/goal017-c2b-state3-live.log`（搬迁前的同结论在 `scratch/goal017-c2-state3-live.log`） |
| 规模门禁 | `pytest tests/tooling/test_python_source_limits.py` | `1029 passed`（搬迁后；`live_run_support.py` **449/450**、`live_switch_support.py` 43 行） |
| 判据面 | `pytest`（4 个门判据 + runbook 同源 + CI 结构 + 措辞面） | `92 passed, 1 skipped` |
| 静态门 | `ruff check` / `ruff format --check` / `mypy` | `All checks passed!` / `1028 files already formatted` / `Success: no issues found in 1018 source files` |
| D-13 阈值零改动 | `git diff -- tests/observability/test_telemetry_overhead.py` | **空** |
| D-13 机制 | `pytest tests/observability --collect-only`（带/不带 `PYTEST_ADDOPTS`） | 3 → **0** |
| D-13 隔离实跑 | `pytest tests/observability/test_telemetry_overhead.py`（独立进程） | `3 passed in 2.71s` |
| D-13 传播 | `grep -cE "continue-on-error\|^\s+if:" .github/workflows/m0-quality.yml` | `0`（无豁免键） |
| CI 结构判据 | `pytest tests/tooling/test_m0_ci_coverage.py` + `validate_cursor_framework.py` | `5 passed` / `PASS: Cursor framework 0.4.0 validated` |
| as-is 本机 m0 | `uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going`（= Makefile `validate-all` 的展开命令；本机 shell 无 `make`；独占跑、仓库 `.venv`） | **第 1 跑红（真实缺陷，已处置）** `FAILED: 1 check(s): python/tests=1`（`tests\e2e\live_run_support.py` **477 > 450**）⇒ 搬迁后**第 2 跑 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = 24；日志 `scratch/goal017-c2b-m0-as-is.log`） |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-25 | IN_PROGRESS | cycle 2 开工：WP1（D-11）与 WP2（D-13）并行推进；先核实现状再改。 |
| 2026-09-25 | IN_PROGRESS | **m0 第 1 跑红（真实缺陷，本 PLAN 引入）**：`python/tests` 唯一失败 = `test_python_source_size_limits[tests\e2e\live_run_support.py]`（**477 > 450**）。处置 = 把开关两函数拆到单一职责模块 `tests/e2e/live_switch_support.py` + 12 处 import 改指向；**未动阈值**。 |
| 2026-09-25 | DONE | 两个 WP 全部落地并取证（见上表）；两次**实测发现**：① `test_ec04_live_first_run.py` 的离线判据在「只配 runtime、忘开开关」时会误红 ⇒ 改为独立重算未满足条件；② 贴线文件的 450 行上限会抓住「顺手把新东西塞进已有大文件」⇒ 拆模块而非调阈值。 |

## 影响报告

- **改动**：产品层 1 个模块（`packages/application/model_relay/live_run_gate.py`：加常量 + 必填参数 +
  理由文案）；测试侧 **2 个**支持模块（新增 `tests/e2e/live_switch_support.py` 43 行；
  `tests/e2e/live_run_support.py` 回到 449 行）+ 12 个 live 模块 + 4 个门判据 + 1 个新判据；
  文档 1 份（runbook §4/§7/§8）；CI 1 份（workflow：新作业 + 一条 env）。
- **lint/typecheck/test**：`ruff check` / `ruff format --check` / `mypy` 全绿；定向套件
  `92 passed, 1 skipped`；新判据 `14 passed`；6 次按压 6/6 红。
- **Domain/API/schema 变化**：**无**。没有新域实体、没有 DTO / OpenAPI 变化、没有 migration。
- **安全/凭据变化**：**收紧**。默认门不再因「环境里恰好有凭据」而改变行为；真实出网需要
  **显式开关 + 凭据**；放行面（`egress_guard` 的 marker）**未**拓宽（判据 + 按压）。本 cycle
  唯一一次真实出网是 AC-3③ 的最小必要一次；凭据值**未**进入任何记录（日志只含判词与计数），
  开关**未**留在环境或 `.env`（内联前缀，命令级）。
- **兼容性/迁移风险**：live 用例的操作者命令多了**一个前置变量**（`RESEARCHOS_LIVE_E2E=1`），
  runbook 已逐字更新；不设它的环境**行为不变**（仍 skip）。CI 侧的作业拆分不改变任何被判内容。
- **上游版本影响**：**无**（本 PLAN 未动任何 pin；`undici` / `yaml` 仍未授权）。
- **下一项任务**：GOAL-017 `EC-04` 收口复检（两树复检 + m0 终态行 + 13 项 `D-NN` 终态表 + CI 台账）。
