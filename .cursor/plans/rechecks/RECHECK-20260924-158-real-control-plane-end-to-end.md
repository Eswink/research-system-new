---
id: RECHECK-20260924-158
plan_id: PLAN-20260924-156
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-24
completed_at: 2026-09-24
reviewer: root-agent-goal-014-ec02 + 三条可复跑探针（scratch/goal014_c2_*.py）
baseline_ref: 334c9ab（cycle 1 归因更正后的树）
checked_head: 当前树（cycle 2 判据 + 支持模块）+ scratch 探针三份输出
---

# RECHECK-20260924-158 — GOAL-014 EC-02 真实控制面端到端（cycle 2）

## 检查范围

① 可达半边：`real_retrieval_research_v1` 经**产品组合根 + 既有 API**（`preflight_override = None`）
跑到终态，控制面判词是否**全部**由产品自己求值；② 成对反证（撤 allow ⇒ 冻结前终止）；
③ EC-02 判据本体的**实验半**是否可达；④ 有没有为了让判据通过而改动门禁 / 合约 / 策略面。

## 检查结果

### 一、控制面确实是产品自己的（不是夹具给的判词）

判据读面（样张 `plane` 段）：`override = null`、`evaluator = NativePolicyEvaluator`、
`is_native = true`、`policy_version = 0.4.0`（= `examples/config/policy.yaml`）、
`provider_health.ncbi_eutils = HEALTHY`、`adapter = NcbiEutilsProvider`。

**为什么这算「真」**：`provider_health` 是 `build_provider_health(deps, catalog)` 在
**同一份合并目录**上**现场探测**的结果——`UNKNOWN` 的那一支（「控制面未注册可探测的
provider 实例」）被**真适配器**顶掉了，不是被注入的常量顶掉的。对照实测（矩阵探针）：
同一棵树、同一份目录，**不注册**适配器 ⇒ `ncbi_eutils = UNKNOWN` ⇒ 检索类协议 `WARN`
（`TOOL_HEALTH_UNPROVEN`）+ **拒冻**（该警示**没有**接受通道）；**注册** ⇒ `PASS` + 可冻结。
⇒ 这条判据证明的是「产品控制面能**自己**把检索类协议判成可冻结」，而不是「夹具替它判的」。

### 二、终态与读面

`state = SUCCEEDED`、`manifest_digest = sha256:6e0804dc…`、`failures = []`。
证据面 4 条：2 条 `RETRIEVED`（`tool:literature_search:…` 与
`tool:literature_read:…42778281+42778201+42777851`，`tool_refs` 分别为
`[ncbi_eutils, literature_search]` / `[ncbi_eutils, literature_read]`）+ 1 条交付物
（`GENERATED`）+ 1 条声明输入（`USER_PROVIDED`）。预算面 1 条
（`AGENT_TURNS` / `quantity 1` / `cost_status UNKNOWN` — 未定价如实标注，未伪造成本）。
**实验面 = `[]`**：本协议未声明实验，故为空（这正是下面第三节的对象）。

### 三、实验半**不可达**（本复检的核心结论）

**实测**（`scratch/goal014_c2_acceptance_probe.txt`）：把「实验跑成功、制品齐备」时产品路径
**能**给出的事实（`structured_output` 含实验 id/状态/制品引用/指标、`artifacts` 含
`metrics` 与 `experiment_result.json`）喂给**既有**求值器，两份**声明了 `experiment`** 的
出厂合约（`experiment_execution` / `m12_experiment_execution`）仍判 `passed=False`：

- `ARTIFACT_EXISTS → OK`（`metrics` 在场 ⇒ 制品维度**不是**缺口）；
- `TEST_PASSES → FAIL "no test results provided"`；
- `POLICY_COMPLIANT → FAIL "policy decision unknown"`。

**结构性根因**（读代码可核）：`packages/application/run_orchestration/evaluation_gate.py`
的 `EvaluationInputs` **没有** `tests` / `policy_decision` 两个字段，`to_criterion_inputs()`
只搬 `structured_output` / `artifacts` / 来源数 / `review_score` / `human_approved` ⇒
两条判据在这条路径上**永远** fail-closed。实验任务走的就是这条路
（`phase_runner._execute_one_task` → `register_and_gate_experiment` →
`evaluate_gate_experiment` → `evaluate_gate`）⇒ **带真实实验的 run 到不了 `SUCCEEDED`**。

**这不是本 GOAL 该自己决定的事**：GOAL-011 的登记把「`SCHEMA_VALID` / `TEST_PASSES` /
`POLICY_COMPLIANT` 接线」列为**下一轮拍板项 ①②③**。本 cycle **不**绕过、**不**新造一份
判据更弱的出厂合约（那等于「放宽验收门以强行成功」），也**不**改 `EvaluationInputs`（那属
产品验收门本身，超出本 GOAL 的授权面）。⇒ EC-02 置 **BLOCKED**。

### 四、成对反证（两条，均止于**冻结前**）

| 按压 | 协议 | 终态 | manifest | 失败判词 | task | 实验 | 证据 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 撤 `evidence.read` 的 allow | `sort_analysis_v1.yaml` | `FAILED` | `null` | `POLICY_DENIED, TOOL_RISK_ELEVATED` | `[]` | `[]` | `[]` |
| 撤 `literature.{search,read}` 的 allow | `real_retrieval_research_v1.yaml` | `FAILED` | `null` | `DAG_ORPHAN_PHASE, POLICY_DENIED` | `[]` | `[]` | `[]` |

两条都经**同一产品入口**（`create_app` + `POST /projects/example-project/runs`）、
同一套装配（产品组合根 + 真适配器），**零真实 LLM 调用**（止于 preflight）。
按压后两处文件 `git diff --stat` **为空**（逐字节还原）。⇒ 与 EC-01 的判据一致：
cycle 1 放行的那条 allow 在**产品路径**上是**承重**的，且撤掉它在**冻结前**终止。

### 五、有没有为了让判据通过而动别的东西

- `git diff --stat` 对**策略面两文件**为空（按压已还原）；本 cycle **未改**任何产品代码、
  合约、schema、快照、门禁与既有断言。
- 新增的两个文件都是 `tests/e2e/` 下的判据/支持模块，判据挂 `requires_live_llm`：
  离线实跑 `1 skipped`、`judged 0 connection attempt(s)`（**零出网**）。
- 真实调用**最小必要**：1 次真实 LLM 会话（1 个 phase、`quantity = 1` turns）+ 2 次
  NCBI 调用（`retmax = 3`）；无重试、无批量。

## 判据性质披露（必须读的一段）

- **本判据只覆盖 EC-02 的一半**：检索 + 证据面 + 预算面 + 「控制面是产品自己的」。
  **实验面不在射程内**（第三节的阻断）⇒ 用本判据的成功去声称 EC-02 达成本身是**错的**。
- **装配方补了两段缝**（provider 实例、运行链能力步）：这是**执行体**，不是判词
  （D-2 的边界）。真实的产品组合根今天**不接**这两段（`F-10`）⇒ 本判据证明的是
  「产品控制面 + 装配方补执行体」这条路径，**不是**「出厂组合根开箱即跑」。
- **`experiments = []` 是如实结果**，不是读取失败：该协议没有实验阶段。

## 结论

**`PASS_WITH_WARNINGS`**——① 可达半边**达成且实测**（真实控制面判词 + `SUCCEEDED` +
两条 `RETRIEVED` 证据）；② 成对反证两条齐备、逐字节还原；③ EC-02 的**判据本体**
（带真实实验到 `SUCCEEDED`）**不可达**，阻断点 M-1/M-2/M-3 逐条实测（`F-10` / `F-11`）
⇒ EC-02 置 `BLOCKED`，PLAN-156 置 `BLOCKED`。

## 仍未处理项（如实登记）

- `F-11`（验收门三接线）待**用户拍板**——它是 GOAL-011 登记的 ①②③ 同一件事。
- `F-10`（出厂组合根不接执行体缝）待拍板：接（产品能力）/ 不接（保持装配方补）。
- **M-2 的配对声明**（检索 + 已 pin 实验）在 M-3 落地前**没有意义**：验收门不放行，
  配对协议跑不出 `SUCCEEDED`。⇒ 本 cycle **不**新增该声明（避免造一份当下必然判拒的出厂协议）。
- EC-03 / EC-04 / EC-05 未动（下一 cycle 起做 EC-03，**完全在授权内、离线**）。
