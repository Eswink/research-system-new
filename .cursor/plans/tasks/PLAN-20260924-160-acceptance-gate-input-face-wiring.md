---
id: PLAN-20260924-160
slug: acceptance-gate-input-face-wiring
title: 验收门输入面接通：四维饥饿面接线 + 真实控制面（无 override）带真实实验跑到 SUCCEEDED（GOAL-014 EC-02）
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
latest_recheck: .cursor/plans/rechecks/RECHECK-20260924-162-acceptance-gate-input-face.md
memory_entries:
  - .cursor/memory/entries/MEM-20260924-128-run-chain-declaration-must-cover-plan-wide-tool-set.md
  - .cursor/memory/entries/MEM-20260924-129-press-scripts-need-an-arming-guard.md
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

- [x] **AC-1｜四维接线在册且可复跑（离线、零出网）**：新增判据同时覆盖四维
      ——schema 回调注入后 `SCHEMA_VALID` 真的按合约声明的 schema 判、`metrics` 透传后
      `METRIC_THRESHOLD` 真的比较、`policy_decision` 记录后 `POLICY_COMPLIANT` 真的判、
      `tests` 由实验产物算出后 `TEST_PASSES` 真的判；四条**各自**保留 fail-closed 的反面。
- [x] **AC-2｜真实控制面（无 `preflight_override`）带真实实验到 `SUCCEEDED`**：
      `override is None` 实测；终态**恰为** `SUCCEEDED`；三读面齐备
      （实验 ≥1 条 **且此前为 0 条**、证据可读、预算归账）；判词与样张逐字落 `scratch/`（**不进仓库**）。
- [x] **AC-3｜成对反证（先红后绿）**：a) 撤 allow ⇒ 真实控制面回到冻结前终止（零 task /
      零实验 / 零工具观测）；b) **去掉实验自报产物**（`metrics` / `tests` 来源）⇒
      验收门**判拒**且判词**点名**是哪条判据缺什么（证明接通的是真实事实，不是喂门通过）。
      **按压口径就地改对（本轮实测的发现，如实登记）**：AC 原写「撤 `evidence.read`」，
      实测撤 `evidence.read` **不按不动本协议的这条 run**——`evidence.read` 不在
      `real_experiment_research_v1` 任何相位的 `required_capabilities` 里，撤掉它 run 照样
      冻结、`analysis` 照样跑完（1 task / 4 条证据），只在实验相位收在「缝没接」上 ⇒ 那是
      **混淆**、不是反证。本协议**真的链式执行**的能力是 `literature.search`（run-chain 检索）
      ⇒ 按压取它，签名为 `POLICY_DENIED` / `manifest_digest: null` / 零面。
      `evidence.read` 那一条按**它真正相关的协议**（`sort_analysis_v1`，cycle 2 的原按压）
      重测，签名与 cycle 2 逐字同形 ⇒ 原按压**保留在位**。三次按压的原始输出都在
      `scratch/`（见「证据」）。
- [x] **AC-4｜本地门全绿**：规模门禁自查（50 行/函数、450 行/文件）+ 快照类门禁
      （OpenAPI / 设计基线）+ `make validate-all`（m0 全量 23 项）+ 受影响定向套件 +
      web 门（tsc / eslint / unit / build / stub / live e2e）；**默认门一律离线**。
- [x] **AC-5｜记录自洽 + 无越权**：改动面逐条登记（含 `M-2` 的具名声明补全与回退面）；
      策略面 / `AcceptanceCriteria` / `classify_risk` / `WARN` 语义**逐字节未动**
      （以 `git diff` 证据）；RECHECK 独立复检 `PASS` / `PASS_WITH_WARNINGS`；CI 到终态。

## 实施清单

- [x] **WP1｜`EvaluationInputs` 增四维（声明面）**：`tests` / `metrics` / `policy_decision` /
      `schema_check` 四个字段 + `to_criterion_inputs()` 透传 + `evaluate_task_gate` 把
      `schema_check` 交给 `evaluate_contract`；缺省值保持 fail-closed（D-2）。
- [x] **WP2｜实验事实 → 门输入（唯一生产者）**：新模块把
      `ExperimentRunResult.metrics`（NUMBER 类）→ `CriterionInputs.metrics`；
      实验产物（`experiment_result.json` / `stdout.log` / `stderr.log`）→ `tests`（每项带判词）；
      `_enforce_policy` 的逐能力决定 → 保守聚合的 `policy_decision`。
- [x] **WP3｜策略决定的如实记录**：`GovernedExperimentExecutor._enforce_policy` 返回决定表，
      `ExperimentExecutionOutcome` 增可选字段承载（additive；缺省不改变既有语义）。
- [x] **WP4｜产品路径的 schema 回调接线**：`PhaseRunnerDeps` / `OrchestrationDependencies`
      增「schema 名 → 校验器」工厂字段；产品组合根与 run-ready 装配同侧提供实现
      （复用 `load_json_schema` + `jsonschema`）；`evaluate_gate` 按合约 `output_schema` 取回调。
- [x] **WP5｜`M-2` 配对声明 + 真实实验脚本**：新增出厂协议（run_chain 检索 + 沙箱实验两相位）
      + 一个真实、确定性的沙箱实验脚本（产出合约判据 `ARTIFACT_EXISTS(metrics)` 要求的
      `metrics` 制品与 `experiment_result.json`），**两份既有的出厂合约一字不改**。
- [x] **WP6｜live 判据**：`tests/e2e/test_real_control_plane_experiment_live.py`
      （`requires_live_llm` + live 门 skip；真实调用取最小必要：1 次 run），
      含成对反证的**离线**部分（撤 allow / 去自报产物）。
- [x] **WP7｜本地验证 + 收口回写**：AC-4 的全部门 + GOAL 回写 + RECHECK + MEM。

## 证据

- **四维接线的离线判据**：`tests/application/run_orchestration/test_acceptance_gate_input_face.py`
  **8 passed**；定向套件（含它 + 下面两条 e2e + `tests/application/preflight/` + `test_m2_audit.py`
  + 运行链暴露面 + 凭据审计）**67 passed / exit 0**，`egress guard: judged 7; blocked 0`
  （`scratch/goal014-c6-targeted-final.log`）。
- **真实控制面（无 override）正向**：`tests/e2e/test_real_control_plane_experiment_live.py`
  **`1 passed in 15.89s`**，`egress guard: judged 3 connection attempt(s); blocked 0`；
  样张 `scratch/goal014-c6-real-experiment-sample.json`（**不进仓库**）：
  `state = SUCCEEDED` / `manifest_digest = sha256:369ee794…` / `failures = []` /
  `override = None` + `NativePolicyEvaluator` + `ncbi_eutils HEALTHY`；
  实验面 **1 条**（此前 0 条，`image_digest = sha256:e95de242…`，制品含 `…:metrics`，
  指标 `n_items 800 / pairwise 319600 / indexed 40 / ratio 7990.0 / duplicates 40/40 /
  agreement True / seed 7`）、证据面 **8 条**（`RETRIEVED` + 真 PMID）、预算面 1 条。
- **按压（a）**：`scratch/goal014-c6-press-allow-withdrawn.py`（带保险闸）⇒
  `scratch/goal014-c6-press-allow-withdrawn.txt`（撤 `literature.search`：`FAILED` /
  `POLICY_DENIED, TOOL_RISK_ELEVATED` / `manifest_digest: null` / 零 task·实验·证据）、
  `scratch/goal014-c6-press-evidence-read-withdrawn.txt`（撤 `evidence.read` 于**本协议**
  ⇒ 不动它：run 照样冻结、analysis 跑完（1 task / 4 证据）、收在实验相位「缝没接」——
  如实记为**混淆**，不是反证）、
  `scratch/goal014-c6-press-evidence-read-cycle2-protocol.txt`（撤 `evidence.read` 于
  `sort_analysis_v1` ⇒ 与 cycle 2 逐字同形 ⇒ 原按压保留在位）。还原：`sha256` 两次一致
  （`e00bdcb3…`），`git diff --stat` 为空。
- **按压（b）**：单元面 `test_removing_the_self_report_makes_the_gate_reject_and_name_the_criteria`
  （抽掉自报面 ⇒ 逐句 `artifact metrics missing` / `no test results provided` /
  `policy decision unknown`）；**真实容器面**
  `tests/e2e/test_real_experiment_research_offline.py::test_removing_the_self_reported_artifact_makes_the_gate_reject_and_name_it`
  （改脚本 `artifact_refs` 为空后真跑容器 ⇒ `FAILED` + `acceptance gate rejected` + 点名
  `ARTIFACT_EXISTS` / `metrics`）。
- **独立复检**：`scratch/verify_goal014_c6.py`（只读 / 标准库 / 不 import 仓库代码）
  ⇒ `checked=33 failures=0`（分组：A 四项接线 10 / B 边界未动 6 / C 判据在册 6 / D 记录自洽 11）。
- **本地门**：规模门禁自查 `violations: 0`（所有本 cycle 文件 ≤450 行、无 >50 行函数）；
  定向套件见上；`validate.py` 绿 + `DOCS-CHECK PASS: 6 deterministic checks`；
  web 门 **stub e2e 98 passed（3.5m）** + **live e2e 53 passed（52.7s）**（`tsc` / `eslint` /
  unit / build 由 m0 的 typescript 组承担，全绿）。**m0**：条数门禁 / 类型 / 依赖边界 /
  治理 / 文档 / web 组全绿；`python/tests` 的**判词**是 `4446 passed / 19 skipped / 0 failed`，
  但进程退出 1 —— 红来自 `tests/egress_guard.py` 的结构判据（2 条到 `198.18.0.83:443` 的探测：
  **本机 fake-IP DNS** 把产品 endpoint 域名解析到 198.18/15），**同一形态在干净基线树
  @ `140dcec` 上复现**（`scratch/goal014-c6-baseline-pytests.log`）⇒ 环境型、与本轮改动无关、
  判据未动。故**本机 as-is m0 = 22 PASS / 1 FAILED，不写成 23/23**；CI 是该项仲裁
  （结论见 GOAL 的 CI 台账尾巴）。**CI 已到终态**：M0 [36023332433](https://github.com/Eswink/research-system-new/actions/runs/36023332433) 六 job 全 success + CodeQL [36023332464](https://github.com/Eswink/research-system-new/actions/runs/36023332464) 3/3 ⇒ 该项（本机环境型判红）由 CI 仲裁为过。

## 状态历史

- 2026-09-24：**建档**（`status: IN_PROGRESS`）。承 GOAL-014 的 cycle 6 = 用户判词**取 A**；
  子 PLAN 与 `ALL_PLAN` 投影**同一提交**落地。开局已核实：本机 Docker daemon 可用
  （`research-os-sandbox:m9-test` 在场）、`.env` 的 `LLM_MAIN_KEY` 在场 ⇒ 用户判词 §四.4 的
  「真实实验不可用 ⇒ 如实挂起并停止」**不成立**，本轮必须真跑。
- 2026-09-24：**实施完成**（WP1–WP6 全部落地 + WP7 的本地验证）。四项按判词接通
  （a–d 各有唯一来源、各有反面的既有恒判词）；`M-2` 配对协议与实验脚本落地（**两份既有合约
  一字未改**）；真实控制面（无 override）带真实 LLM + 真实检索 + 真实实验跑到 `SUCCEEDED`，
  三读面齐备；两条按压实测（并就地改对了 AC-3 里一条**按不动的**能力口径——见 AC-3 与
  RECHECK 第三节）。一处如实登记的返工：首跑真实容器链路判红
  `ToolDefinition 'openhands_workspace' is not registered`，根因是相位级运行链声明没有覆盖
  计划级冻结工具集 ⇒ 以**声明面**修（并入 `MEM-20260924-128`），未动冻结语义、未动策略面。
- 2026-09-24：**收口**（`status: DONE`）。独立复检 `checked=33 failures=0`；本地 m0 与 CI
  终态见 GOAL-014 的 CI 台账尾巴与本 PLAN 的「证据」段。

## 影响报告

- **Domain / API / schema**：Domain 无改动（`MetricValue` / `ExperimentRunResult` 原样读）；
  应用层 `EvaluationInputs` 与 `ExperimentExecutionOutcome` 为 **additive** 字段（缺省保持
  既有语义）；**无 API 契约与快照改动**（收尾复核 OpenAPI / 设计基线）。
- **安全 / 凭据**：无新增凭据面；真实调用只走已登记端点与 provider 声明的 `network_domains`；
  凭据值不落盘、不回显、不进记录。
- **兼容性 / 迁移**：无 DB / schema 迁移；`tests` / `metrics` / `policy_decision` 缺省为空 ⇒
  既有装配的判词**逐字不变**（含 `W-A` 一类恒拒行为只在真的接了数据时才改变）。
- **上游版本影响**：无新依赖、无 pin 变更（`jsonschema` 与 `PyYAML` 已在依赖内）。
