---
id: PLAN-20260924-160
slug: acceptance-gate-input-face-wiring
title: 验收门输入面接通：四维饥饿面接线 + 真实控制面（无 override）带真实实验跑到 SUCCEEDED（GOAL-014 EC-02）
status: IN_PROGRESS
created_at: 2026-09-24
updated_at: 2026-09-24
parent_goal: GOAL-20260924-014
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260924-014 的 2026-09-24 **第二条用户判词（取 A：接通验收门输入面）**，
    授权范围**严格限于四项**且每项数据来源必须是**产品路径上已真实产生的事实**：
    a) `schema_check` 注入（构造点 `packages/application/run_orchestration/task_phase_helpers.py`
    的 `evaluate_gate`；声明点 `evaluation_gate.py` 的 `EvaluationInputs`）；
    b) `metrics` 透传（源 = 域实体字段 `ExperimentRunResult.metrics: tuple[MetricValue, ...]`）；
    c) **记录被执行的** `policy_decision`（`GovernedExperimentExecutor._enforce_policy` 已真的
    求值并执行；**如实记录已发生的事实，不新造判定**）；
    d) `tests` 按**实验自报产物**接进（源 = `experiment_result.json` / `stdout.log` /
    `stderr.log` 与 `ExperimentRunResult` 既有字段；**不得**写死 `{"pass": True}` 之类）。
    **边界（触及任一条 ⇒ 立即 BLOCKED）**：`default_effect: DENY` 不变；`deny` /
    `require_approval` / `allow_with_constraints` 列表不变；**不再新增任何策略面 allow**；
    **不放宽任何 `AcceptanceCriteria`（合约里的判据一字不改）**；不改 `classify_risk`；
    不动 `WARN` 语义。
    **随行披露（必须进记录，不得读成独立验证）**：接通后 `TEST_PASSES` 的来源是
    **实验自报**（合约 pin 的脚本/装配方给的脚本在沙箱里产出的受控报告），**不是**独立跑测框架；
    `POLICY_COMPLIANT` 的来源是**执行期已经发生**的那次策略求值的如实记录。
    live-gated 真实调用承 GOAL-014 建档授权（端点 `agnes-anthropic`，凭据仅在本机 gitignored
    `.env` 的 `LLM_MAIN_KEY`；真实检索仅出网 `eutils.ncbi.nlm.nih.gov`；**次数取最小必要**）；
    本机 Docker 用于既有实验执行后端；`RESEARCHOS_AGENT_RUNTIME` 只作单条命令内联前缀；
    默认 runtime 保持 Fake、默认 CI 离线；push-to-main-for-CI（只推 main、不 force）。
    **本 PLAN 明文不做**：改 validator / 门禁 / 快照 / 测试断言使其通过；skip/删除测试或
    降低断言强度；`git add -A`；伪造或夸大验证证据；**放宽验收门凑成功**；为跑通而放宽
    出站判据；在授权范围外放宽任何策略面；改 `test_m2_audit.py` 的镜像一致性判据。
    **本 PLAN 的一处具名声明补全（`M-2`，承 `F-9` 先例）**：无 `preflight_override` 的 run
    里实验只能由**出厂目录**声明（brief §六），而**没有任何出厂协议同时声明「运行链检索」与
    「已 pin 的沙箱实验」**（`real_retrieval_research_v1` 无实验阶段；`m12_reference_research_v1`
    的检索不是 run_chain，且被 `tests/architecture/python/test_run_chain_capability_exposure.py`
    的 `_UNDECLARED` 字面量钉住）⇒ 新增**一份出厂协议** `examples/protocols/real_experiment_research_v1.yaml`
    **配对两份既有合约**（`real_retrieval_deliverable` + `experiment_execution`），
    **判据一字不改、策略面一字不改**；回退面 = 单 WP 提交（`git rm` 该协议 + 该脚本）。
    `M-1`（出厂组合根是否自己接执行体缝）**不在本轮自行决定**：按 `F-10` 既有处置由
    **装配方补执行体**（`tests/e2e/live_control_plane_support.py`）并实测。
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260924-160 — 验收门输入面接通（GOAL-014 EC-02）

## 目标

把 `F-11` 的**四维饥饿面**（`SCHEMA_VALID` / `TEST_PASSES` / `METRIC_THRESHOLD` /
`POLICY_COMPLIANT`）按用户判词 **A** 接到**产品路径上已真实产生的事实**，并据此在
**无 `preflight_override`** 的真实控制面上跑出一次带**真实 LLM + 真实检索 + 真实实验**的
run 到终态 `SUCCEEDED`，三读面齐备。

## 计划开始前的定案（写死）

- **D-1｜「接通」= 把已存在的事实送进门，不是给门加原告**：四项的**值**必须来自产品路径上
  已经产生的对象（合约 `output_schema` / `ExperimentRunResult.metrics` / `_enforce_policy`
  的求值结果 / 实验产物字节）。**编排层不得构造** `tests` / `metrics`（例如 `{"pass": True}`）。
- **D-2｜缺省一律 fail-closed（既有语义逐字保持）**：没有装配回调 / 没有读数 / 没有决定 ⇒
  维持既有恒判词（`schema validator unavailable` / `no test results provided` /
  `metric … missing` / `policy decision unknown`）。判据强度**只增不减**。
- **D-3｜`schema_check` 来自合约自己声明的 `output_schema`**：装配方给出
  「schema 名 → 校验器」的**工厂**（复用既有 `adapters/contracts/base.load_json_schema`
  与既有依赖 `jsonschema`），应用层不读文件、不新造第二张映射表。
- **D-4｜`policy_decision` 是记录、不是判定**：`_enforce_policy` 逐能力求值后的决定**原样
  带出**（新增可选字段），验收门拿到的聚合值是**这些已发生决定的保守合成**
  （任一 `ALLOW_WITH_CONSTRAINTS` ⇒ 报 `ALLOW_WITH_CONSTRAINTS`）；**不做**第二次裁决。
- **D-5｜`tests` 的每个布尔都有出处**：逐项由实验产物**算出**并保留**判词**（哪件产物、
  哪个字段、哪个值），缺产物 ⇒ 空映射（⇒ 门报 `no test results provided`），
  **不**用 False 冒充「跑了但失败」以外的东西。
- **D-6｜无 override 的执行体缝由装配方补（`F-10` 既有处置）**：产品组合根今天不接
  `tool_providers` / `capabilities` / `experiment_task`；本轮沿用 `live_control_plane_support`
  的**只注入执行体、绝不注入判词**纪律，把第三段缝（`experiment_task`）一并补上并实测。

## 验收条件

- [ ] **AC-1｜四维接线在册且可复跑（离线、零出网）**：新增判据同时覆盖四维
      ——schema 回调注入后 `SCHEMA_VALID` 真的按合约声明的 schema 判、`metrics` 透传后
      `METRIC_THRESHOLD` 真的比较、`policy_decision` 记录后 `POLICY_COMPLIANT` 真的判、
      `tests` 由实验产物算出后 `TEST_PASSES` 真的判；四条**各自**保留 fail-closed 的反面。
- [ ] **AC-2｜真实控制面（无 `preflight_override`）带真实实验到 `SUCCEEDED`**：
      `override is None` 实测；终态**恰为** `SUCCEEDED`；三读面齐备
      （实验 ≥1 条 **且此前为 0 条**、证据可读、预算归账）；判词与样张逐字落 `scratch/`（**不进仓库**）。
- [ ] **AC-3｜成对反证（先红后绿）**：a) 撤 `evidence.read` 的 allow ⇒ 真实控制面回到
      冻结前终止（零 task / 零实验）；b) **去掉实验自报产物**（`metrics` / `tests` 来源）⇒
      验收门**判拒**且判词**点名**是哪条判据缺什么（证明接通的是真实事实，不是喂门通过）。
- [ ] **AC-4｜本地门全绿**：规模门禁自查（50 行/函数、450 行/文件）+ 快照类门禁
      （OpenAPI / 设计基线）+ `make validate-all`（m0 全量 23 项）+ 受影响定向套件 +
      web 门（tsc / eslint / unit / build / stub / live e2e）；**默认门一律离线**。
- [ ] **AC-5｜记录自洽 + 无越权**：改动面逐条登记（含 `M-2` 的具名声明补全与回退面）；
      策略面 / `AcceptanceCriteria` / `classify_risk` / `WARN` 语义**逐字节未动**
      （以 `git diff` 证据）；RECHECK 独立复检 `PASS` / `PASS_WITH_WARNINGS`；CI 到终态。

## 实施清单

- [ ] **WP1｜`EvaluationInputs` 增四维（声明面）**：`tests` / `metrics` / `policy_decision` /
      `schema_check` 四个字段 + `to_criterion_inputs()` 透传 + `evaluate_task_gate` 把
      `schema_check` 交给 `evaluate_contract`；缺省值保持 fail-closed（D-2）。
- [ ] **WP2｜实验事实 → 门输入（唯一生产者）**：新模块把
      `ExperimentRunResult.metrics`（NUMBER 类）→ `CriterionInputs.metrics`；
      实验产物（`experiment_result.json` / `stdout.log` / `stderr.log`）→ `tests`（每项带判词）；
      `_enforce_policy` 的逐能力决定 → 保守聚合的 `policy_decision`。
- [ ] **WP3｜策略决定的如实记录**：`GovernedExperimentExecutor._enforce_policy` 返回决定表，
      `ExperimentExecutionOutcome` 增可选字段承载（additive；缺省不改变既有语义）。
- [ ] **WP4｜产品路径的 schema 回调接线**：`PhaseRunnerDeps` / `OrchestrationDependencies`
      增「schema 名 → 校验器」工厂字段；产品组合根与 run-ready 装配同侧提供实现
      （复用 `load_json_schema` + `jsonschema`）；`evaluate_gate` 按合约 `output_schema` 取回调。
- [ ] **WP5｜`M-2` 配对声明 + 真实实验脚本**：新增出厂协议（run_chain 检索 + 沙箱实验两相位）
      + 一个真实、确定性的沙箱实验脚本（产出合约判据 `ARTIFACT_EXISTS(metrics)` 要求的
      `metrics` 制品与 `experiment_result.json`），**两份既有的出厂合约一字不改**。
- [ ] **WP6｜live 判据**：`tests/e2e/test_real_control_plane_experiment_live.py`
      （`requires_live_llm` + live 门 skip；真实调用取最小必要：1 次 run），
      含成对反证的**离线**部分（撤 allow / 去自报产物）。
- [ ] **WP7｜本地验证 + 收口回写**：AC-4 的全部门 + GOAL 回写 + RECHECK + MEM。

## 证据

（收尾时补齐：判据实跑输出、真实 run 样张路径、反证红/绿对照、m0 终局行、CI run/结论。）

## 状态历史

- 2026-09-24：**建档**（`status: IN_PROGRESS`）。承 GOAL-014 的 cycle 6 = 用户判词**取 A**；
  子 PLAN 与 `ALL_PLAN` 投影**同一提交**落地。开局已核实：本机 Docker daemon 可用
  （`research-os-sandbox:m9-test` 在场）、`.env` 的 `LLM_MAIN_KEY` 在场 ⇒ 用户判词 §四.4 的
  「真实实验不可用 ⇒ 记 PENDING 并停止」**不成立**，本轮必须真跑。

## 影响报告

- **Domain / API / schema**：Domain 无改动（`MetricValue` / `ExperimentRunResult` 原样读）；
  应用层 `EvaluationInputs` 与 `ExperimentExecutionOutcome` 为 **additive** 字段（缺省保持
  既有语义）；**无 API 契约与快照改动**（收尾复核 OpenAPI / 设计基线）。
- **安全 / 凭据**：无新增凭据面；真实调用只走已登记端点与 provider 声明的 `network_domains`；
  凭据值不落盘、不回显、不进记录。
- **兼容性 / 迁移**：无 DB / schema 迁移；`tests` / `metrics` / `policy_decision` 缺省为空 ⇒
  既有装配的判词**逐字不变**（含 `W-A` 一类恒拒行为只在真的接了数据时才改变）。
- **上游版本影响**：无新依赖、无 pin 变更（`jsonschema` 与 `PyYAML` 已在依赖内）。
