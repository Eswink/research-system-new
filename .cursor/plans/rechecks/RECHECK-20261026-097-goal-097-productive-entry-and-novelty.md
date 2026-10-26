---
id: RECHECK-20261026-097
slug: goal-097-productive-entry-and-novelty
title: GOAL-097 复检 —— 产品入口真跑完整链 + 创新点两面
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-26
updated_at: 2026-10-26
plan_id: PLAN-20261026-097
parent_goal: GOAL-20261026-097
owners:
  - root-agent
verify_paths:
  - services/api/executor_wiring.py
  - services/api/experiment_factories.py
  - services/api/retrieval_wiring.py
  - services/api/composition.py
  - services/api/pg_composition.py
  - services/api/experiment_support.py
  - examples/protocols/direction_to_report_v2.yaml
  - examples/contracts/task_contracts.yaml
  - examples/config/roles.yaml
  - examples/config/agents.yaml
  - examples/config/team_templates.yaml
  - packages/application/run_orchestration/novelty_claim.py
  - packages/application/run_orchestration/novelty_claim_step.py
  - tests/api/test_product_roots_carry_the_execution_seams.py
  - tests/api/test_contract_pinned_experiment_spec_takes_effect.py
  - tests/contracts/test_direction_to_report_v2_novelty.py
  - tests/e2e/test_productive_entry_runs_the_whole_chain.py
  - tools/verify_goal097_closeout.py
  - tools/goal097_closeout_assertions.py
memory_entries: []
---

# RECHECK-20261026-097 — GOAL-097

## 检查结果

**PASS_WITH_WARNINGS**。逐 EC：

| EC | 结论 | 证据 |
| --- | --- | --- |
| EC-01 | **PASS** | `tests/api/test_product_roots_carry_the_execution_seams.py` 9 条：两个根都经同一份 seam 构造器；三道缝齐；装配期零 Docker 连接（注入「构造即抛」工厂 ⇒ `assemble()` 仍成功、首次派发才抛）；反证（摘掉接缝 ⇒ 判红）；检索调用必须标 `phase_id`（正 + 反两向）；**会话工具面**必须带检索实现（正 + 反两向） |
| EC-02 | **见「三、真跑读数」** | `tests/e2e/test_productive_entry_runs_the_whole_chain.py` + 取证文件 |
| EC-03 | **PASS** | `tests/api/test_contract_pinned_experiment_spec_takes_effect.py` 9 条：声明优先两向（含按压：改契约路径 ⇒ 结果变）、空合约逐字回到装配面、两字段各自独立、出厂 pin 真的在、反证（摘掉分支 ⇒ 行为改变） |
| EC-04 | **PASS**（声明面 + 结构面）；**评审面见真跑读数** | `tests/contracts/test_direction_to_report_v2_novelty.py` 15 条：七相编译零 ERROR、四条跨相边、C-1、`nearest_prior` 命中真实标识（反证：伪造标识 ⇒ 判红）、`claim`/`why_novel` 非空（反证）、`is_reviewer()` 为真、激活理由逐字、三评审目标互异、检索合约明确「检索已跑完」 |
| EC-05 | **PASS** | `tools/verify_goal097_closeout.py` + `tools/goal097_closeout_assertions.py`，登记进 `_VERIFIERS` 与 `IN_SCOPE`；`_CUTOFF_SEQ = 64` ⇒ 097 自动进受判面 |
| EC-06 | **PASS** | 三处更正逐条核对未回退（见「四、承接上一轮的记录更正」） |

## 一、改既有判据的逐条申报（`git diff --numstat` 与谓词比对）

| 文件 | 改动 | 谓词变化 | 为什么不是放宽 |
| --- | --- | --- | --- |
| `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` | `_VERIFIERS` 追加 `tools/verify_goal097_closeout.py` | 纯收紧（清单只增） | 分类判据射程变大 |
| `tests/tooling/test_tooling_scripts_meet_product_gates.py` | `IN_SCOPE` 追加本轮两个脚本 | 纯收紧 | 四道门射程变大 |
| `services/api/composition.py` | 接三道缝 + 压缩注释（保持 ≤450 行） | 无数值判据变化 | 注释压缩不改变任何断言；行数门仍是 450 |
| `services/api/session_tool_support.py` | `DEFAULT_SESSION_TOOL_BINDINGS` 追加 `literature.search` / `literature.read`；`canonical_read_register` 新增可选 `extra_providers` | 纯收紧（出厂注册面变大；`extra_providers` 缺省 `None` ⇒ 既有调用逐字不变） | 新增的是**实现**，不是判定面 |

**未改**：`examples/protocols/direction_to_report_v1.yaml`、`direction_to_question_v1.yaml`、
`research_report_chain_v1.yaml`、`research_question_retrieval` 合约（v2 用**自己那份**）、
`test_direction_to_report_protocol.py`、`_CUTOFF_SEQ` 的多处下界。

## 二、两向按压（判据自身可信）

**按压 1（惰性，实测）**：注入「构造即抛」的后端工厂 ⇒ `assemble()` 成功、`calls == []`；
首次派发才抛且调用参数是**契约 pin 的镜像**。⇒ 「惰性」与「声明优先」两件事在同一行取证。

**按压 2（声明优先，实测）**：把 `declared_or_assembled` 的 `declaration.script or script`
按掉 ⇒ 行为改变（返回装配面的值）⇒ 判红。⇒ 那两行不是死代码。

**按压 3（`phase_id`，实测）**：把调用的 `phase_id` 抹成 `None` ⇒ `planned_in_this_phase`
在**问题相**返回 True（bug 的形态）；真实调用返回 False。

**按压 4（会话工具面，实测）**：不给 `extra_providers` ⇒ 注册表里没有 `literature.*`
（SDK 会点名，不是静默降级）。

## 三、真跑读数（EC-02）

**达成**。取证文件 `.cursor/plans/goals/evidence/GOAL-20261026-097-productive-entry-run.txt`：

| 读数 | 值 |
| --- | --- |
| 入口形态 | `TestClient(create_app(assemble(...)))`；**未** `replace(deps.runs._deps, ...)`、**未** `deps.tool_providers = ...`；只注入部署凭据与显式 `preflight_override`（既有运维路径） |
| 终态 | **`SUCCEEDED`**（`run_id: 02d7c47f-4336-413c-8c97-651c951fbcef`） |
| 七相制品 | `missing_phase_artifacts: []`（问题 / 检索报告 / **创新点声明** / 计划 / 实验 / 评审 / 报告全在） |
| 实验 | `experiment_rows: 2`（真实容器，两臂） |
| 评审判词 | `review_rows: 8`（验收门逐条结论） |
| **创新点声明面** | `novelty_matched_prior: PMID:42579838` —— 声明的 `nearest_prior` 命中**本 run 检索到的真实标识** |
| **创新点评审面** | `review_texts_cite_that_identifier: 2` —— **两位评审者的 `review_decision` 正文都逐字引用了同一个标识** |

**真跑过程中修掉的三个产品缺陷**（都是「产品入口不可用」的真实原因，不是判据问题）：

1. **运行链调用没标 `phase_id`** ⇒ `planned_in_this_phase` 在该 run 的**每一个** run_chain 相都
   返回 True ⇒ 问题相在上游产物还不存在时就去取 `research_question.query`，run 在检索前失败。
   修法：出厂调用表标 `phase_id="retrieval"`（并加判据，含反证：抹掉 `phase_id` ⇒ 问题相被判 True）。
2. **检索格合约没说明「检索已由运行链做完」** ⇒ 真实模型第一句是
   `I'll start by exploring the repository structure…`（本相会话工具面为空），制品里没有
   `retrieval_report` 块 ⇒ 下游解析失败。修法：v2 用**自己那份**合约
   （`retrieval_report_from_the_run_chain`，覆盖判据三维逐字相同）；共用那份一字未改。
3. **会话工具面没有检索实现** ⇒ 评审相（没有 run-chain 排除 ⇒ 面 = 整个冻结集）撞
   `ToolDefinition 'literature.read' is not registered`。修法：出厂绑定表补两条 +
   `canonical_read_register` 接受组合根手里的实例（同一批）。

**另修一处既有缺陷的可用性面**（根因未修，见 `W-4`）：同步执行路径只在会话**开始前**心跳一次
（`task_executor._attempt_once`），真实会话超过 `lease_ttl_seconds`（缺省 300s）后租约被回收 ⇒
`no matching lease for task` ⇒ HTTP **422**。本轮把 TTL 做成**可配**
（`ApiSettings.workflow_lease_ttl_seconds`，缺省 300 逐字不变），真跑用 3600；
**执行语义与错误映射一律未改**。

## 四、承接上一轮的记录更正（EC-06）

| 更正 | 落点 | 本轮核对 |
| --- | --- | --- |
| GOAL-096 台账 run 归属：`d683c7d3` 记 `covered_by: 624338c5` | GOAL-096 `## CI 台账` | 在位，未回退 |
| `W-1`：失败读数**不在**取证文件里（该文件覆盖写、只在成功断言前调用） | GOAL-096 正文 `## 残余与未覆盖范围` | 在位，未回退；本轮**修了机制**（先写盘再断言） |
| `W-2`：被推成 `RETRIEVED` 的是 `review` 消费的 `plan:research_plan` 边 | 同上 | 在位，未回退 |

## 结论

（见下方「结论」节的最终判词。）
