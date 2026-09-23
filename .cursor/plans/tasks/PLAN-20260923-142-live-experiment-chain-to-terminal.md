---
id: PLAN-20260923-142
slug: live-experiment-chain-to-terminal
title: 真实实验执行链跑到终态：sort_analysis_v1 + 声明式沙箱实验 + 既有 Docker 后端（GOAL-012 EC-02）
status: DONE
created_at: 2026-09-23
updated_at: 2026-09-23
parent_goal: GOAL-20260923-012
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260923-012 建档授权（2026-09-23 用户 goal 模式指令）：用户**已拍板路径 (A)** 并由
    PLAN-20260923-140 落地冻结通道；本 PLAN 是其后的 EC-02——**授权真实实验执行**（既有 Docker
    后端 `research-os-sandbox:m9-test`、本机容器，遵守既有安全姿态：不挂 docker socket、不
    privileged、不 host home）与**live-gated 真实调用**（登记端点 + `agnes-2.5-flash`，凭据仅
    来自 gitignored `.env` 的 `LLM_MAIN_KEY`，**次数取最小必要**）。凭据纪律照旧：值**不得**写入
    任何 tracked 文件 / DB / 记录 / 日志 / 回显（含片段）；`RESEARCHOS_AGENT_RUNTIME` **只作单条
    命令的内联前缀**、不写入 `.env`。默认姿态不变（默认 runtime=Fake、默认 CI 离线；出站判据
    `tests/egress_guard.py` **不放宽**，live 用例挂 `requires_live_llm`）。
    本 PLAN 明文不做：放宽 `classify_risk` / `PreflightStatus` 语义；放宽 §9 任一条默认 deny 面；
    为跑通而改策略面 **或** 改共享夹具使其通过；skip/删除测试或降低断言强度；`git add -A`；
    伪造或夸大验证证据。**若本 PLAN 必须在「放宽默认 deny / 放宽出站判据 / 把 live 开关写进
    默认配置」三者中择一才能走通 ⇒ 立即停止并记 BLOCKED。**
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260923-143-live-experiment-chain-to-terminal.md
memory_entries:
  - .cursor/memory/entries/MEM-20260923-110-multi-provider-session-judge.md
---

# PLAN-20260923-142 — 真实实验执行链跑到终态（GOAL-012 EC-02）

## 目标

让「合约声明的沙箱实验」在**真实执行体**下经**真实运行链**跑到**终态**：真实 LLM 驱动
`sort_analysis_v1`，执行阶段的合约声明 `experiment` ⇒ 派发到**既有** `DockerExecutionBackend`
（`research-os-sandbox:m9-test`）⇒ 容器产出 `analysis_report` 满足验收门 ⇒ review 阶段会话登记
⇒ run `SUCCEEDED` 且**三项读面**（实验产物 / 证据 / 预算）齐备。**不新增执行后端、不新增依赖。**

## 计划开始前的定案（写死）

- **D-1 载体**：`sort_analysis_v1.yaml`（EC-02 判据点名的协议）。实验的**声明**留在装配面
  （`preflight_override` 的目录 + `ExperimentExecutionSpec(script, image)`，GOAL-011 EC-03 的既有
  载体），**不动协议文件、不动共享夹具**——`sort_analysis_v1` 是 M7 参考场景，它的执行阶段被
  10+ 条已判绿用例按**会话**语义驱动。
- **D-2 两段判据（离线成对 + 真实一次）**：
  1. **离线**（`tests/e2e/test_ec02_experiment_chain_offline.py`，`requires_docker`）：同一条链
     零出网跑到 `SUCCEEDED` + 三项读面；**成对反证**：撤掉 `code.execute` 的显式允许 ⇒ 拒冻 ⇒
     零 task / 零 experiment / 无 digest。
  2. **真实**（`tests/e2e/test_ec02_experiment_live.py`，`requires_live_llm`）：一次 run 到终态，
     判据 = 冻结留痕在场（EC-01 的端到端形态）+ `SUCCEEDED` + 三项读面；默认门如实 skip。
- **D-3 W-B 的处置（cycle 1 登记）**：冻结之后的堵点是「会话结果无结构化输出」⇒
  `register_session_result` **如实拒绝**（既有语义，**一字不改**）。离线判据因此给受控执行体
  **显式声明**它交付了什么（`FakeAgentRuntime(structured_output=…)`）；**不**改
  `make_run_ready_deps` 的缺省（那会改掉 10+ 条既有用例的失败形态），改的是
  `with_sandbox_experiment(..., runtime=None)` 多一个**可选**参数（缺省沿用既有执行体）。
- **D-4 W-A 的处置**：真实**控制面**（`NativePolicyEvaluator` + `examples/config/policy.yaml`）对
  `sort_analysis_v1` 的 `evidence.read` 判 `DENY` ⇒ 该协议在**真实控制面**上是 `FAIL`。用户已定：
  **登记为需拍板项，不自行放宽策略面**。本 PLAN 的 live 路径走**既有**装配面
  （`preflight_override` + 夹具求值器，GOAL-009/010/011 全部真实 run 的同一条路径），
  **不修改** `examples/config/policy.yaml`，也不新增策略规则。
- **D-5 不改的清单**（反证面）：`classify_risk`；`PreflightStatus` / `passed`；冻结通道
  （`policy_acceptance.py`）；`register_session_result` 的空交付物拒绝；`tests/egress_guard.py`；
  `.env`（`RESEARCHOS_AGENT_RUNTIME` 只作内联前缀）；`examples/config/policy.yaml`。
- **D-6 依赖与姿态**：**不新增依赖**；live 调用**取最小必要**（一次 run；真实端点每次调用
  都不可白得，不重试、不批量）。

## 验收条件（逐条如实）

| # | 条件 | 判据（可复跑命令 + 期望值） | 结论 |
| --- | --- | --- | --- |
| AC-1 | **离线链**：声明式沙箱实验经真实 preflight/冻结/编排跑到 `SUCCEEDED` | `pytest tests/e2e/test_ec02_experiment_chain_offline.py -q` ⇒ **2 passed**（第二条为成对反证） | **达成** |
| AC-2 | **三项读面**：实验产物 / 证据 / 预算都从既有 API 可读 | 同文件：`GET /runs/{id}/experiments`（镜像+环境摘要、`analysis_report`、脚本指标）、`/evidence`（非空且指向本 run 制品）、`/usage` | **达成** |
| AC-3 | **反证（先红后绿）**：撤掉显式允许 ⇒ **拒冻**、执行前终止 | 同文件第 2 条：`state=FAILED`、`manifest_digest is None`、`tasks == []`、`experiments == []` | **达成** |
| AC-4 | **真实一次 run 到终态**：真实执行体 + 容器实验 | `set -a; . ./.env; set +a; RESEARCHOS_AGENT_RUNTIME=openhands pytest tests/e2e/test_ec02_experiment_live.py -q -rs` ⇒ **1 passed**（`judged 2; blocked 0`） | **达成** |
| AC-5 | **冻结留痕在场**（EC-01 的端到端形态） | 同 live 判据 + 样张：`manifest_digest` 非空；`accepted_policy_exceptions` **4 条**含 `code.execute`，`decision=ALLOW`、`accepted_at` 非空 | **达成** |
| AC-6 | **门与治理**：规模门禁 + 定向套件 + m0 23/23 + `validate.py` 绿 | m0 第 3 轮 **`PASS: profile=m0; 23 deterministic checks`**（第 1 轮红在 typecheck、第 2 轮红在 `framework/validate`＝文档尚未落盘，均在当轮修掉）；`tests/e2e` 116 passed / 10 skipped、`tests/api`+`tests/application` 1212 passed / 1 skipped、`mypy` 995 files 干净 | **达成** |
| AC-7 | **零出网（默认门）**：live 用例默认 skip，其余离线 | 定向 pytest 逐条 `egress guard: judged N; blocked 0`；未开 live 开关时 live 判据逐字 skip（已实测：`agent runtime is not configured … credential 'LLM_MAIN_KEY' is not resolvable`） | **达成** |
| AC-8 | **真实端点上的一次成功终态** | `scratch/goal012-c2-live-sample.json`：终态恰为 `SUCCEEDED`、失败面为空、六条证据（含声明输入）、`MODEL_TOKENS 9738` | **达成** |

## 实施清单

- [x] **WP1** 判据（离线）：`tests/e2e/test_ec02_experiment_chain_offline.py`（主判据 + 成对反证）+
  `with_sandbox_experiment` 的可选 `runtime` 参数（D-3）。提交 `dcade8c`；**2 passed**。
- [x] **WP2** 判据（真实）：`tests/e2e/test_ec02_experiment_live.py`（`requires_live_llm`，
  默认门如实 skip；一次 run 取样）。提交 `dcade8c`。
- [x] **WP3** 真实取样：`set -a; . ./.env; set +a` + 内联 `RESEARCHOS_AGENT_RUNTIME=openhands`
  跑 WP2 到终态 ⇒ **1 passed**，样张 `scratch/goal012-c2-live-sample.json`（`SUCCEEDED`）。
  **第一次取样失败**（`Duplicate tool names found: {'inert'}`）⇒ 修惰性替身的命名 + 新增离线判据
  （按压逐字复现），见 RECHECK §四。
- [x] **WP4** 门与收口：m0 + 定向套件 + `validate.py`；`RECHECK-20260923-143` + `MEM-110` + GOAL 回写。

## 证据

| # | 事实 | 取数方式 |
| --- | --- | --- |
| E-1 | 冻结之后的堵点在**会话交付物**：`register_session_result` 对空 `structured_output` 如实拒绝 | 读 `packages/application/run_orchestration/result_handler.py`；离线判据给受控执行体显式声明交付物后链子跑通 |
| E-2 | 实验脚本**已经**产出验收门要的那件产物 | `examples/experiments/sort_analysis_baseline.py` 写 `analysis_report`（文件名即合约声明的 artifact 名，`artifact_view` 按 `:` 后最后一段匹配） |
| E-3 | 执行阶段不再起会话 | `phase_runner` 按 `tctx.contract.experiment is not None` 派发实验（声明化，非按 id 硬编码） |
| E-4 | 离线链结果 | `pytest tests/e2e/test_ec02_experiment_chain_offline.py -q` ⇒ 2 passed；第一次尝试的失败逐字记录（指标名断言按**脚本实际产出**重钉，不是放宽） |
| E-5 | 真实一次 run | `tests/e2e/test_ec02_experiment_live.py` ⇒ **1 passed**；样张 `scratch/goal012-c2-live-sample.json`：`SUCCEEDED` + 4 条留痕 + 1 次实验（`analysis_report` 等 4 件产物、镜像 `sha256:e95de2424c65…`）+ 6 条证据（含 `USER_PROVIDED` 声明输入）+ `MODEL_TOKENS 9738` |
| E-6 | 两件 provider 的会话面 | `test_ec03_real_runtime_offline_chain.py::test_a_two_provider_frozen_set_starts_a_session`（离线）绿；按压（共用惰性类）⇒ 逐字红（`scratch/goal012-c2-press-duplicate.txt`） |
| E-7 | 独立复检两棵树成对 | `python scratch/verify_goal012_c2.py` ⇒ 当前树 `checked=29 failures=0`；`git worktree` 到 `c6cf330` ⇒ `checked=29 failures=10`（红项恰为本 cycle 新增面） |

## 影响报告

- **Domain / API / schema**：无（本 PLAN 只加判据 + 装配面一个**可选**参数）。
- **产品代码**：无（`with_sandbox_experiment` 是测试侧装配面；可选参数缺省行为逐字不变）。
- **夹具**：`make_run_ready_deps` 的缺省 runtime **不动**（D-3）；`sort_analysis_v1` 的会话语义
  与既有 10+ 条用例的失败形态**不受影响**。
- **CI / workflow**：不改；live 判据在默认门上如实 skip（`requires_live_llm`）。
- **安全 / 凭据**：live 调用只作单条命令的内联前缀；凭据值只在进程内传递，不落盘、不回显；
  容器遵守既有姿态（无 docker socket / 非 privileged / 不挂 host home）。
- **上游版本影响**：无。
- **下一项任务**：EC-03（实验产出的证据链 + 成对反证）。

## 状态历史

- 2026-09-23：derive（EC-02 子计划）。定案 D-1…D-6 写死；离线判据先落并跑绿，真实取样在 WP3。
