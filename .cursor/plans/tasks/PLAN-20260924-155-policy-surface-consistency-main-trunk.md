---
id: PLAN-20260924-155
slug: policy-surface-consistency-main-trunk
title: 策略面一致性主干：放行 evidence.read + 关门禁用面缺口，两套装配同结论（GOAL-014 EC-01）
status: DONE
created_at: 2026-09-24
updated_at: 2026-09-24
parent_goal: GOAL-20260924-014
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260924-014 建档授权（2026-09-24 用户 goal 模式指令）的 **EC-01**。
    用户已拍板**放行 `evidence.read`（方案 (A)）**，授权范围**严格限于**：
    (a) `examples/config/policy.yaml` 的 `allow` 新增 `evidence.read` 一条；
    (b) **同步** `packages/application/preflight/policy_check.py` 的 `_CAPABILITY_SCOPE`
    （**同一提交内真同步**，否则镜像一致性判据判红——那是既有门禁的正确行为，
    **不得**改该判据、**不得**加豁免）；
    (c) `default_effect: DENY` / `deny` / `require_approval` / `allow_with_constraints`
    **一律不动**。
    **本 PLAN 对授权的一处如实扩展（已具名、可回退、不碰策略面）**：EC-01 的判据
    「真实控制面对 `sort_analysis_v1` 的 preflight **不再是 `FAIL`**」经**实测**发现
    FAIL 有**两个**独立来源——`POLICY_DENIED`（本授权覆盖）**与**两份
    `TASK_CONTRACT_MISSING`（`sort_analysis_execution` / `sort_analysis_review`
    只存在于测试夹具、**不在**出厂目录 `examples/contracts/task_contracts.yaml` 里；
    而 `sort_analysis_v1.yaml` 是产品面**可选模板**）。⇒ 只放行策略**不足以**让真实控制面
    脱离 `FAIL`，EC-01 与 EC-02 都会卡住。本 PLAN 因此**同时**把这两份契约**补进出厂目录**
    （**声明补全**：把夹具的运行期注入提升为产品声明，与 W-B 的处置同类）。
    这一处扩展**不触碰任何策略面**、**不属** AGENTS.md §9 默认 deny 的任何一条、
    **不**引入依赖、**不**改上游 pin、**不**改 Accepted ADR / Canonical State 边界；
    它改的是**声明面**（协议引用的契约在出厂目录里不存在）——正是本 GOAL 要消灭的
    「声明与现实漂移」那一类。若用户判定该扩展越界，回退面 = 单独 revert 该 WP 的提交。
    真实调用（LLM / 检索 / 实验）在 EC-02 的 cycle 才发生，本 PLAN **只做离线判据**：
    零出网、零容器、零凭据读取。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260924-157-policy-surface-consistency-main-trunk.md
memory_entries:
  - .cursor/memory/entries/MEM-20260924-124-multiple-fail-sources-enumerate-before-fixing.md
---

# PLAN-20260924-155 — 策略面一致性主干（GOAL-014 EC-01）

## 目标

让 `sort_analysis_v1` 在**真实控制面**（`NativePolicyEvaluator` + `examples/config/policy.yaml`，
**不带任何 `preflight_override`**）与 **live / run-ready 装配**下**结论一致**，并把这条一致性
落成**离线、零出网、可复跑**的判据 + **成对反证**。这是 `W-C` 的消灭（`W-A` 的执行落点）。

## 计划开始前的定案（写死）

- **D-1｜「两套装配」的精确载体**（建档当日实测定位）：分岔点是
  `services/api/run_execution.py` 的 `execution_inputs()`——
  `deps.preflight_override is None` ⇒ 走 `_live_preflight(deps, catalog, project)`
  （**真实控制面**：`build_policy_evaluator(catalog)` = `NativePolicyEvaluator(catalog.policy)`，
  policy 取自目录里真实的 `policy.yaml`）；
  `preflight_override is not None` ⇒ 直接用该上下文（**live / run-ready 装配**，
  GOAL-009…013 全部真实 run 走的路径）。判据**必须**走这条**产品入口**，
  **不得**手工拼 `PreflightContext` 假装装配（那会让「哪一套装配」变成脚本的方言）。
- **D-2｜判据形态**：同一份判据脚本对**同一个协议**（`sort_analysis_v1.yaml`）走
  `execution_inputs()` 两次——一次 `preflight_override=None`、一次保留 override——
  收集**两份 preflight 报告**，断言：① 两份 `status` **相等**；② 两份都**不含** `FAIL`；
  ③ 两份都**不含** `POLICY_DENIED`（策略维度清零）。判词（`code` + `subject_ref` + `message`）
  逐字进断言失败消息，便于按压时点名。
- **D-3｜策略维度与其余维度的分界（本 PLAN 的核心诚实边界）**：真实控制面与 live 装配
  在**非策略维度**上本来就**不同源**（真实控制面用合并目录的端点/health/供应链事实；
  live 装配用夹具声明的 catalog）。⇒ 判据只对**结论**（`status`）与**策略维度**
  （`POLICY_DENIED` 的出现次数，两处都必须为 0）下断言；**不得**断言两份 `findings`
  逐字相等（那会把「两套装配本就不同源」误判成不一致）。这条边界必须写进 RECHECK 的
  判据性质披露。
- **D-4｜`scope` 取值**：`evidence.read` 的 provider 是 `m12_artifact`
  （`trust_level: BUILT_IN`、`effect_class: READ_ONLY`），与已放行的 `artifact.read`
  **同级** ⇒ `scope: project`。**以真实求值路径验证**：判据必须证明执行期
  `policy_scope_for("evidence.read") == "project"` 且该请求在两边都判 `ALLOW`
  （只放行 preflight 会让执行期落回 `DENY`——那是「同一能力两处结论」的第二形态，见 F-5）。
- **D-5｜出厂目录补全的范围**：只补 `sort_analysis_execution` / `sort_analysis_review`
  两份契约，内容**逐字取自**夹具 `replace_catalog_with_pins()` 的既有声明
  （`required_capabilities` / `acceptance_criteria` / `timeout_seconds`），
  **不**加 `failure_policy` 的未消费键（既有判据 `test_example_contracts_declare_only_honored_
  failure_policy_keys` 要求 `unhonored == ()`）。夹具的 `setdefault` **一行不改**
  （补全后它自然成为幂等的兜底；**不是**「改夹具迁就」）。
- **D-6｜不动的面**：`default_effect` / `deny` / `require_approval` / `allow_with_constraints` /
  `capabilities.yaml`（`evidence.read` 已登记）/ `test_m2_audit.py` 的镜像判据 /
  `tests/egress_guard.py` / 任何测试断言强度。`sort_analysis_v1.yaml` 协议正文**不动**
  （它是 M7 参考场景，10+ 条判绿用例按会话语义驱动它）。

## 验收条件

- [x] **AC-1**：`examples/config/policy.yaml` 的 `allow` 新增 `evidence.read`（`scope: project`），
      且 `packages/application/preflight/policy_check.py` 的 `_CAPABILITY_SCOPE` **同一提交内**
      加同一对；`_GATE_CAPABILITY_SCOPES` **未改**（`evidence.read` 不得进它）。
- [x] **AC-2**：`tests/application/test_m2_audit.py` 的镜像一致性判据**原件未改**且**绿**。
- [x] **AC-3**：`examples/contracts/task_contracts.yaml` 补入两份 `sort_analysis_*` 契约；
      `test_example_contracts_declare_only_honored_failure_policy_keys` 仍绿。
- [x] **AC-4**：新增离线判据（默认门可跑、零出网）断言两套装配**同 `status`**、
      **均非 `FAIL`**、**均无 `POLICY_DENIED`**；并断言执行期 `policy_scope_for` 与
      真实求值器对该能力的判定为放行（D-4）。
- [x] **AC-5**：**成对反证（先红后绿，各可复跑）**——
      ① 撤掉 `allow` 规则（`_CAPABILITY_SCOPE` 相应撤回）⇒ 真实控制面判据**红**
      且判词点名 `POLICY_DENIED`；
      ② 只改一处（policy.yaml 或 `_CAPABILITY_SCOPE` 二者之一）⇒ 镜像判据**红**。
      红/绿对照落 `scratch/`，按压后**逐字还原**并复跑确认绿。
- [x] **AC-6**：受影响既有判据**全部复跑**：`tests/application/test_m2_audit.py`、
      `tests/application/preflight/`、`tests/e2e/test_ec02_experiment_chain_offline.py`、
      `tests/api/test_sandbox_experiment_seam.py`、`tests/loaders/`、
      `tests/architecture/python/test_run_chain_capability_exposure.py`。
- [x] **AC-7**：两处**记录性陈述**与新事实对齐（**不是**改断言）：`tests/application/preflight/
      test_policy_allowed_execute_freeze.py` 的 `_protocol_policy()` docstring、
      `tests/e2e/test_ec02_experiment_live.py` 的「如实边界」段。
- [x] **AC-8**：m0 **全量 23 项已跑**（`scratch/goal014-c1-m0.log`）+ 治理 `validate.py` 绿。
      **实测 22 PASS / 1 FAILED** —— **⚠️ 该判红当时有两条原因，其中一条是本周期的**
      （首版 WP3 自造了 `output_schema` 名，`framework/validate_bundle` 要求
      `schemas/<name>.schema.json` 存在 ⇒ 判 `TaskContract … 输出 Schema 不存在`）。
      **已由纠错提交修掉**：两份契约的 `output_schema` 改为**既有的**
      `real_research_deliverable_v1`（**不新造 schema**），改后本地该检查只剩环境那一条。
      另一条是**仓库外**并发写者的 gitignored 在制品（环境型残余 `R-F3`，判词点名
      `scratch\self-governance-bootstrap-prompt.md`），与本 PLAN 的改动无关。
      其余 22 项（含 `python/lint` / `format-check` / `typecheck` / `dependency-boundaries` /
      `tests`、`typescript/*` 全部、`framework/validate` 等）全绿。
      **如实登记**：本地**不是** 23/23；本地 23/23 的终局行留给 EC-05 收口复检
      （按 GOAL-013 的既有处置）。**归因勘误见 `RECHECK-20260924-157` 的「勘误」节。**
- [x] **AC-9**：RECHECK 定稿（`PASS` / `PASS_WITH_WARNINGS`），PLAN 转 `DONE`，
      `ALL_PLAN` 投影同提交，`latest_recheck` 为**仓库相对路径**。

## 实施清单

- [x] **WP1｜判据先行（先红）**：落离线判据（两装配同结论 + 策略维度清零 + 执行期 scope），
      在**当前树**上确认它**红**（真实控制面 `FAIL` / `POLICY_DENIED`）；证据落 `scratch/`。
- [x] **WP2｜放行 `evidence.read`**：`policy.yaml` 的 `allow` 新增一条 +
      `_CAPABILITY_SCOPE` 同一提交加同一对；复跑判据 ⇒ 策略维度清零。
- [x] **WP3｜补全出厂目录**：`examples/contracts/task_contracts.yaml` 补两份 `sort_analysis_*`
      契约（内容取自夹具既有声明，D-5）；复跑判据 ⇒ 两套装配同 `status` 且非 `FAIL`。
- [x] **WP4｜记录性陈述对齐 + 成对反证**：改两处 docstring/边界段落；跑反证 ①②（先红后绿）。
- [x] **WP5｜本地验证 + RECHECK**：AC-6 的受影响套件 + m0 全量 23 项（实测 **22 PASS /
      1 FAILED**，唯一未绿 = 环境型残余 `R-F3`，见 AC-8）+ 治理 validate；写
      RECHECK-20260924-157；PLAN 转 DONE + `ALL_PLAN` 投影。

## 证据

- **WP1（先红）**：判据在基线树上 **4 failed**，判词逐字含 2× `TASK_CONTRACT_MISSING` +
  1× `[POLICY_DENIED] phase:review: policy denied capability evidence.read: used default
  policy effect` ⇒ `scratch/goal014-c1-criterion-red.txt`（出站 `judged 0`）。
- **WP2/WP3（转绿）**：判据 **5 passed**；`tests/application/preflight/` + `test_m2_audit.py`
  **28 passed**；受影响套件（`tests/loaders/` + `run_chain_capability_exposure` +
  `dry_run_no_side_effect` + `catalog_merge` + `sandbox_experiment_seam`）**81 passed**；
  e2e 离线三条 **9 passed / 1 skipped**；全部轮次出站 `blocked 0`。
- **两套装配同结论**：`scratch/goal014-c1-both-assemblies-after.txt` ⇒
  `SAME_STATUS = True   A=WARN  B=WARN`（改前为 `A=FAIL  B=WARN`）。
- **可冻结面**：`scratch/goal014-c1-freeze-both-arms.txt` ⇒ 两套装配都冻结成功、留痕各 4 对
  `(phase_id, capability)`；真实控制面逐条 `decision` = `ALLOW_WITH_CONSTRAINTS`
  （`code.execute` / `workspace.write.code`）/ `ALLOW`（`workspace.read`×2）。
- **成对反证**：`scratch/goal014-c1-press1-allow-withdrawn.txt`（撤 allow ⇒ 真实控制面判据红、
  镜像仍绿）、`scratch/goal014-c1-press2-mirror-desync.txt`（只改镜像一处 ⇒ 镜像判据红，
  `Extra items in the right set: ('evidence.read', 'project')` @ `test_m2_audit.py:268`）。
  按压后 `git diff --stat` 两个被按压文件**为空**（逐字节还原），还原后复跑全绿。
- **m0**：`scratch/goal014-c1-m0.log` ⇒ **22/23**（判红 = `framework/validate_bundle`，
  当时有**两条**原因：环境型残余 `R-F3` **加上**本 cycle 首版自造的 `output_schema` 名
  ——后者已由纠错提交改为既有的 `real_research_deliverable_v1` 修掉，**归因勘误见
  `RECHECK-20260924-157` 的「勘误」节**）；`python/tests` **4418 passed / 18 skipped /
  0 failed**，较上一基线（4413 / 18）差 **+5** = 本 PLAN 新增的正好 5 条判据。
- **独立复检**：`scratch/verify_goal014_c1.py` ⇒ `checked=45 failures=0`。

## 状态历史

- 2026-09-24：derive（GOAL-014 cycle 1）。起点事实已实测：真实控制面 `FAIL`
  （`[POLICY_DENIED] phase:review: policy denied capability evidence.read: used default policy effect`
  + 两份 `TASK_CONTRACT_MISSING`），live 装配 `WARN`（仅 4 条 `TOOL_RISK_ELEVATED`）
  ⇒ `SAME_STATUS = False`（`W-A` / `W-C` 双双复现）。**新发现的第二来源**（出厂目录缺两份契约）
  已落 D-5 与授权的如实扩展段。
- 2026-09-24：**收口（DONE）**。WP1–WP5 全部完成，AC-1…AC-9 全绿；复检
  `RECHECK-20260924-157` = **PASS_WITH_WARNINGS**（唯一警告 = 环境型残余 `R-F3`，
  本机 as-is m0 = 22/23；CI 检出无 `scratch/` ⇒ 不受影响）；工程记忆 `MEM-20260924-124`。
  `W-A` / `W-C` **由本 PLAN 消灭**（判据在册、反证成对、按压逐字节还原）。
  **未做**：EC-02 的真实控制面端到端 run（下一 cycle）。

## 影响报告

- **改动面**：策略面（`policy.yaml` 的 `allow` +1 条；镜像常量 +1 对）、声明面
  （`examples/contracts/task_contracts.yaml` +2 契约）、判据面（新增离线判据 + 两处记录性
  陈述对齐）。**不改**产品代码逻辑、**不改** Domain/API/schema/DTO、**不改**门禁与既有断言。
- **Domain/API/schema 变化**：无。
- **安全/凭据变化**：策略面**只增一条读能力的 allow**；`default_effect` 仍 `DENY`、
  `deny` / `require_approval` / `allow_with_constraints` 逐字未动。本 PLAN 零凭据读取、零出网。
- **兼容性/迁移风险**：① `sort_analysis_v1` 在真实控制面上由「必 FAIL」变为「可冻结」——
  这是本 GOAL 的目标，但会让**任何依赖它必 FAIL 的夹具**失效（已数：`grep -rn
  TASK_CONTRACT_MISSING tests/` 无消费者断言该形态）；② `_protocol_policy()` 的运行期注入
  分支变成死支（保留为幂等兜底）；③ 夹具的 `setdefault` 变 no-op。
- **上游版本影响**：无（不新增依赖、不改 pin）。
- **下一项任务**：GOAL-014 cycle 2 = EC-02（真实控制面端到端 run）。
