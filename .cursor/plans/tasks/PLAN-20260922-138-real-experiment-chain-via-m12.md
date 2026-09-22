---
id: PLAN-20260922-138
slug: real-experiment-chain-via-m12
title: 真实实验执行链：把 m12 参考协议补成可跑通的载体并跑一次真实 run（GOAL-011 EC-03）
status: BLOCKED
created_at: 2026-09-23
updated_at: 2026-09-23
parent_goal: GOAL-20260922-011
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-23 用户 goal 模式拍板：**EC-03 取 (B)**——「为 m12_reference_research_v1 补齐 5 份
    phase 合约并接受约 22 次真实检索出网」。授权原文要点：(1) **(B) 拍板本身**：不为 EC-03 改冻结门
    / 放宽 `classify_risk` / 让 `freeze_manifest` 接受 WARN（(A) 一系全部不取）；
    (2) **真实检索出网**（承 GOAL-011 建档授权）：限 `ncbi_eutils` 的 `network_domains`，
    次数取最小必要；本次为满足 discovery phase **既有**的 `minimum_sources: 10`（**不改该判据**），
    装配方声明**分页检索计划**（`fixed_arguments` 只放量：`retstart`/`retmax`），
    ⇒ 预计每会话 ~10 次、2 个会话共 ~20 次真实出网；(3) **live-gated 真实 LLM**（最小必要，
    单条命令内联前缀 `set -a; . ./.env; set +a` + `RESEARCHOS_AGENT_RUNTIME=openhands`）；
    (4) 凭据纪律不放松（值不落 tracked/DB/记录/日志/回显）；(5) 只推 main、不 force、
    push 前 `git pull --ff-only`。
    **本 PLAN 明文不做**：改任何判据/门禁/快照/验收门使其通过；skip/删除测试、降低断言强度；
    `git add -A`；伪造或夸大验证证据；新增依赖或改上游 pin；把 `RESEARCHOS_AGENT_RUNTIME` 写进 `.env`。
    **2026-09-23 cycle 9 追加登记（不改授权边界，只记实际情况）**：拍板 (B) 的**前提被实测否证**
    （见「实测结论」），(B) 想买的「更多检索调用 = 更多来源」在今天的机制上不成立；(B) 的
    **载体**因此停在 discovery 的验收门，EC-03 仍为 PENDING。本 cycle 落的是**能诚实地落的部分**：
    5 份 phase 合约 + 协议声明面 + 实验缝的三处缺陷修复与判据（详见下）。
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260922-138 — 真实实验执行链（GOAL-011 EC-03，取 (B)）

## 目标

EC-03：**真实 LLM 驱动一条实验协议（`sort_analysis_v1` 或 `m12_reference_research_v1`）跑到终态**，
且**实验产物 + 证据 + 预算归账**三者在读面上可读；执行体 = **既有** Docker 后端
（`research-os-sandbox:m9-test`）。

`sort_analysis_v1` 一系命中「改门禁才能过」⇒ **本轮不取**。取 **(B)：把
`m12_reference_research_v1` 补成可跑通的载体**。

## 计划开始前的定案（写死）

- **D-1 取 (B)，不取 (A)**：任何「放宽 `classify_risk` / 让 `freeze_manifest` 接受 WARN /
  把 `code.execute` 从合约里删掉」的修法都不做——那是改门禁凑成功。
- **D-2 5 份新合约按「phase 的真实意图」写判据**，不写「必然能过」的空判据（**已按此落地**）。
- **D-3 来源数由装配方声明，不由协议伪造**：检索的**内容**来自**声明的输入**；量放
  `fixed_arguments`。
- **D-4 离线先证、再真实跑**：先离线证「7 phase 全过 + experiment 真在容器里跑完」，再开真实
  LLM/真实检索；离线阶段**零出网**。
- **D-5 成本上限**：真实检索 ≈ 每 discovery 会话 10 次 × 2 会话；真实 run 最多 **1 次**。

## 实测结论（cycle 9；逐条可复跑，见「证据」）

### 已达成

- **AC-1 ✅ 协议可执行（编译面）**：m12 的 **7 个 phase 全部有可解析的 `task_contract`**；
  离线编译 `SUCCESSFUL: True`、findings 为零；运行期不再有 `phase declares no task contract`。
  落地内容：`schemas/` 新增 5 份输出 schema + `examples/contracts/task_contracts.yaml` 新增
  5 份合约 + `examples/protocols/m12_reference_research_v1.yaml` 补齐引用与声明
  （discovery 的 `capability_execution: run_chain` 与 `inputs: [input-brief:real_research_v1]`）
  + `validate_bundle.py` 的 JSON Schema 注册表登记（只登记，等价断言未改）。
- **AC-3 的机械面 ✅（真实容器，非 live LLM）**：`m12_experiment_execution` **自己 pin** 的
  脚本/镜像/命令经**产品缝**（`sandbox_experiment_runner` + `docker_experiment_assembly`
  ⇒ 既有 `DockerExecutionBackend`）在容器里**真的跑完**：实验 `SUCCEEDED`、6 个指标
  （`baseline_accuracy=0.745`、`candidate_accuracy=0.28`、`n_train=500`、`n_test=200` …）、
  语义指标摘要与镜像摘要非空、4 条证据经唯一准入入口落 canonical、
  `GET /runs/{id}/experiments` 上看得到。**这条路此前从未被派发过**，首次派发连撞
  **三处缺陷**（全部修复 + 判据钉住，见下）。

### 被实测否证（(B) 的前提）

- **AC-2 ❌ 来源数**：`minimum_sources: 10` **不是**靠「多声明几次检索调用」能满足的——
  F-4 的乘法关系（「声明 N 次调用 = N 条来源」）**是错的**。实测机制：
  `phase_capabilities._operation_key` 只在参数里有 `ids` 时把它拼进操作键，而
  `register_tool_evidence` 的 Evidence id = `evidence:{run_id}:{operation_key}`、
  SourceRecord origin = `tool:{tool_id}:{task_id}:{operation_key}` ⇒ **同一 task 内操作键重复的
  两次调用撞同一个 id**：内容相同则记账塌成一条；内容不同则 `register_source` 判
  `conflicting source registration` ——**整步硬失败**（实测：A/B/C 三个方案全红，见证据 E-4）。
  ⇒ 单 task 的**非自产来源上限 = 3**（1 份声明输入 + 1 次检索 + 1 次读取），与门槛 10 有量级差；
  且**再加一次检索不是「凑不够」，是直接失败**。
- **AC-2 ❌ 另一维**：discovery 合约的**第一条**判据 `SCHEMA_VALID` 在**产品路径上不可满足**
  ——`evaluation_gate.build_gate_outcome` 调 `evaluate_contract(...)` 时**不传** `schema_check`，
  而 `_evaluate_schema_valid` 对它缺省即判 `"schema validator unavailable"`（fail-closed）。
  全仓 `schema_check` 只出现在域函数签名、域单测与 memory gate 里 ⇒ 没有任何装配方接过这道线。
- **AC-3 ❌ 载体终态**：即便 discovery 过了，`m12_experiment_execution` 的另两条判据
  **同样未接线**：`TEST_PASSES` 需要的 `tests` 与 `POLICY_COMPLIANT` 需要的 `policy_decision`
  在 `EvaluationInputs.to_criterion_inputs()` 里**都没有来源**（编排层不提供）⇒ 执行阶段的门
  今天判不出 PASS。
- ⇒ **m12 跑不到 `SUCCEEDED`** 的真实原因**不是**「合约缺 5 份」（那已补齐），而是
  **4 个验收判据维度在产品路径上未接线 + 来源数机制的单 task 上限**。实测终态与判词逐字：
  `state: FAILED`；`run.failed` payload = `task <id> rejected by acceptance gate
  (acceptance gate rejected: SCHEMA_VALID: schema validator unavailable;
  EVIDENCE_COVERAGE: 3 < 10 sources)`；`manifest_digest: None`（预检已经冻结过，
  run 死在验收门而不是冻结门）；discovery 的 task 行 `SUCCEEDED`（会话真的跑了）。

### 刻意**没有**做的两件事（写明）

- **没有跑真实 LLM/真实检索的 live run**：验收门是**登记的纯函数**（输入 = 该 task 的
  `ResultRegistration`），离线已把终态判死；花真钱再测一遍同一个 FAILED 不增加任何信息，
  且违背 D-5 的最小必要原则。**授权不是消耗品，本 cycle 一次真实出网都没有发起**。
- **没有为了让它变绿**去：动 `domain_discovery` 的判据、动 `classify_risk`/`freeze_manifest`、
  给 `minimum_sources: 10` 换个更弱的姊妹合约、或把 `SCHEMA_VALID` 从合约里删掉。

## 顺带修复的三处**潜在缺陷**（cycle 6 接缝时从未被派发的后果）

都发生在 `services/api/experiment_support.py` / `packages/application/experiments/governed.py`，
都是「接线没跑过」的缺陷，**不是**为了让判据变绿：

| # | 缺陷 | 症状（修复前实测） | 修法 |
| --- | --- | --- | --- |
| 1 | 计划 id 用 `experiment_run_id_of(f"plan-{task.id}")`，而该函数要求输入**本身是 UUID** | 每次派发在建计划处抛 `ValueError: invalid UUID: 'plan-…'`（容器都起不来） | 改用同模块既有的确定性派生 `derived_id`（并把它从 `_derived_id` 提为公开名 + 参数名 `run_id`→`seed`，因为它今天也被 task id 作种子使用） |
| 2 | `GovernedExperimentExecutor._enforce_policy` 构造 `PolicyRequest` **不带 scope** | 真实 `examples/config/policy.yaml` 下 `artifact.write`（`allow + scope: run`）匹配不上 ⇒ 落到 `default_effect: DENY` ⇒ 实验被拒（「preflight 放行、执行期拒绝」的分裂） | 补齐 `policy_scope_for(capability)`（与工具面 `ScopedPolicy` 同一张表、同一条口径） |
| 3 | 沙箱工作区没在后端 `create_workspace` | 执行链取租约时报 `unknown workspace: sandbox-experiment` | 装配期登记（M12 clean-run 那条路本来就这么做） |

另更正一处**指向不存在的文件**的注释：`test_sandbox_experiment_dispatch.py` 的模块 docstring
把「真实容器那一段」指给 `tests/e2e/test_sandbox_experiment_live.py`——该文件当时**不存在**
（`ls tests/e2e/ | grep sandbox` 只有 `test_sandbox_experiment_reachability.py`），
现在按实际形态落了 `tests/e2e/test_sandbox_experiment_seam_docker.py` 并改正文。

## 验收条件（逐条如实）

| # | 条件 | 结论 |
| --- | --- | --- |
| AC-1 | 7 phase 全部有可解析合约、零 `TASK_CONTRACT_MISSING` | **✅ 达成** |
| AC-2 | `minimum_sources: 10` 一字不改且由装配方声明满足；离线判过且零出网 | **❌ 前提被否证**（上限 3、加调用即硬失败；见「实测结论」） |
| AC-3 | 一次真实 LLM run 跑到终态；execution 由既有 Docker 后端执行，产物+证据+预算可读 | **⚠️ 机械面达成、载体未达成**：容器里真的跑完且读面齐备（判据 `tests/e2e/test_sandbox_experiment_seam_docker.py` 2 passed），但 carrier 协议停在 discovery 验收门 ⇒ **未做 live run** |
| AC-4 | 终态如实（只有 `SUCCEEDED` 记成功） | **✅ 如实**：carrier 终态 `FAILED` + 逐字判词已登记；**不记 PASS** |
| AC-5 | 50 行函数 / 450 行文件两道门绿；m0 23/23；治理 validate 绿 | 文件/函数门绿（`tests/tooling/test_python_source_limits.py` 1008 passed 含新文件）；m0 与治理在 EC-06 收口一轮跑 |
| AC-6 | live 记账：真实出网逐次计数；跑后不留开关与凭据 | **✅ 零真实出网**（`egress guard: judged … blocked 0`；未开 live 开关、未读凭据值） |

## 实施清单

- [x] **WP1** 5 份 phase 合约 + 5 份输出 schema + 注册面。
- [x] **WP2** 协议声明面（discovery 的 run-chain 与声明输入）。
- [x] **WP3** 实验缝的三处缺陷修复 + 离线判据（`tests/api/test_sandbox_experiment_seam.py` 5 passed）
      + 真实容器判据（`tests/e2e/test_sandbox_experiment_seam_docker.py` 2 passed，`requires_docker`）。
- [x] **WP4** 载体终态的**实测**（离线全链；零出网）与**否证记录**（本文「实测结论」）。
- [x] **WP5** 记录 + GOAL 回写（EC-03 status_note / 迭代日志 / 台账）。
- [ ] **WP6（不属于本授权，留给下一轮）**：让 m12 真正达标需要**产品程序**（见下「下一轮输入」）。

## 下一轮输入（需要用户拍板的一项）

让 `m12_reference_research_v1` 跑到 `SUCCEEDED`，至少需要下列**能力面**工作（都不是「改门禁」，
而是把契约已声明、产品未接线的面接上；规模 = 多 cycle 的产品程序）：

1. **`SCHEMA_VALID` 接线**：给验收门提供 `schema_check`（按 `contract.output_schema` 找
   `schemas/<name>.schema.json`；需要选定一个 JSON-Schema 实现，仓库今天没有）。
2. **`TEST_PASSES` 接线**：为实验类合约定义「哪些测试事实算数」（实验 `<id>:experiment_result.json`
   里今天有指标没有测试集合）。
3. **`POLICY_COMPLIANT` 接线**：把本 task 的策略裁决（`GovernedExperimentExecutor` 已经做过）
   交给验收门，而不是在门里缺省未知。
4. **多调用证据键**：`_operation_key` 需按调用参数区分（如带参数摘要），否则多分面检索
   表达不出来（今天第二次检索**直接失败**）。
5. **来源数口径**：`domain_discovery.minimum_sources: 10` 在「单 task 最多 3 条独立来源」的
   机制下如何达标——**要么**把 4 做完并让装配方声明分面检索（成本 ≈ 2×分面数 次真实出网），
   **要么**就这条判据本身做一次决定（降低门槛 / 换用途 / 拆合约）。**这一条必须用户拍板**，
   本 GOAL 的纪律明确禁止「改合约使其匹配现状」。

## 证据

| # | 事实 | 取数方式 |
| --- | --- | --- |
| E-1 | 编译面：7 phase 全有合约、零 findings | `scratch/goal011-c9-m12-compile-probe.py`（`SUCCESSFUL: True | codes: []`） |
| E-2 | 载体终态与逐字判词（`SCHEMA_VALID … unavailable; EVIDENCE_COVERAGE: 3 < 10 sources`） | `PLAN=single EXPERIMENT=0 python scratch/goal011-c9-m12-offline-chain.py`（离线 mock relay + MockTransport；`retrieval http 2`） |
| E-3 | 单 task 来源上限：evidence 面 = `GENERATED / USER_PROVIDED / RETRIEVED×2` ⇒ 非自产 **3** | 同上（`evidence` 行） |
| E-4 | 多调用**硬失败**（不是塌成一条）：`conflicting source registration: tool:literature_search:…` | `python scratch/goal011-c9-runchain-source-count-probe.py`（A/B/C 三方案） |
| E-5 | 判据维度未接线：`schema_check` 无产品调用方；`EvaluationInputs` 无 `tests` / `policy_decision` | 读 `evaluation_gate.py` / `acceptance.py` + 全仓搜索（0 命中） |
| E-6 | 实验缝在真实容器里跑完（修复三处缺陷后） | `python scratch/goal011-c9-m12-experiment-seam.py`（实验 `SUCCEEDED`、6 指标、4 证据、`/runs/{id}/experiments` 可读） |
| E-7 | 三处缺陷的**先红后绿** | `git stash push -- <三个产品文件>` ⇒ 5 failed；`git stash pop` ⇒ 5 passed |
| E-8 | 真实容器判据 | `pytest tests/e2e/test_sandbox_experiment_seam_docker.py -q` ⇒ **2 passed**（`RESEARCHOS_REQUIRE_DOCKER=1`，本机 Linux 容器） |

## 影响报告

- **Domain / API / schema**：新增 5 份合约 + 5 份 schema + JSON Schema 注册表登记（均为加性）；
  协议补声明（m12 此前不可执行 ⇒ 无行为回归面）。
- **产品代码**：`governed.py`（执行期策略补 scope）、`experiment_support.py`（计划 id 派生、
  工作区登记）、`clean_run_stages.py`（`_derived_id` → 公开 `derived_id`，参数名 `run_id` → `seed`）。
- **CI / workflow**：不改；新判据落 `requires_docker`（`container-quality` 作业覆盖）与默认门。
- **安全 / 凭据**：零真实出网、零凭据读取；策略面**只补齐 scope**，拒绝路径仍 fail-closed
  （参数化判据逐能力断言 DENY 仍生效）。
- **上游版本影响**：无。
- **下一项任务**：EC-06 收口复检（并把 133/134/135/136/137/138 一并收口）。

## 状态历史

- 2026-09-23：derive（WP0）。拍板 (B)；只读勘察得到 F-1…F-8；未改任何文件、未发起任何出站。
- 2026-09-23（cycle 9 执行）：WP1/WP2 落地（AC-1 达成）；首次派发实验缝，连撞三处缺陷并修复 +
  判据钉住（先红后绿）；离线全链实测把 (B) 的前提**否证**（来源上限 3、加调用即硬失败、
  `SCHEMA_VALID` 未接线）⇒ AC-2 不成立、AC-3 停在机械面、**未做 live run**（理由见上）。
  本 PLAN 由 IN_PROGRESS 转 **BLOCKED**：它的剩余部分不是本授权内的工程，而是需要拍板的
  能力面工作（见「下一轮输入」）。**零真实出网、零凭据读取、未放宽任何判据。**
