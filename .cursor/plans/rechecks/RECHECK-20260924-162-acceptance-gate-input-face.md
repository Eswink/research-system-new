---
id: RECHECK-20260924-162
plan_id: PLAN-20260924-160
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-24
completed_at: 2026-09-24
reviewer: root-agent-goal-014-cycle6 + 独立复检脚本（scratch/verify_goal014_c6.py，只读 / 标准库 / 不 import 仓库代码）
baseline_ref: af05b6a（cycle 6 判词落盘提交）
checked_head: 当前树（cycle 6 实施 + 收口记录）
---

# RECHECK-20260924-162 — 验收门输入面接通 + 真实控制面带真实实验到 `SUCCEEDED`（cycle 6）

## 检查范围

① 用户判词「取 A」的四项是否**按判词**接通（数据来源全是产品路径上**已真实产生**的事实）；
② EC-02 的正向判据在**无 `preflight_override`** 的真实控制面上是否**实跑到** `SUCCEEDED`
且三读面齐备；③ 成对反证（撤 allow / 去自报产物）是否**先红后绿**且判词点名；
④ 边界条件（`default_effect: DENY` / 三个决策列表 / `AcceptanceCriteria` / `classify_risk` /
`WARN` 语义）是否**逐字节未动**；⑤ 本地门（规模 / 快照 / m0 / 定向套件 / web）与 CI 是否到终态；
⑥ 记录自洽（`latest_recheck` / `child_plans` / `memory_entries` / `ALL_PLAN` 同一提交）。

## 检查结果

### 一、四项接线：来源都是已存在的事实（不是给门加原告）

| 判词项 | 落地位置 | 值的来源 | 反面（未接通/无事实时仍是既有恒判词） |
| --- | --- | --- | --- |
| a) `schema_check` 注入 | `evaluation_gate.EvaluationInputs.schema_check` → `evaluate_contract`；构造点 `task_phase_helpers.evaluate_gate` | 合约**自己**声明的 `output_schema`（仓内 `schemas/`）经 `output_schema_check_for` 工厂 | `schema validator unavailable` |
| b) `metrics` 透传 | `experiment_gate_inputs.metric_inputs` | 域实体字段 `ExperimentRunResult.metrics`（只取 `Decimal` 值） | `metric <name> missing` |
| c) `policy_decision` **记录** | `GovernedExperimentExecutor._enforce_policy` 返回决定表 → `ExperimentExecutionOutcome.policy_decisions` → `recorded_policy_decision`（最不宽松者说了算） | **执行期已经发生**的那次逐能力求值 | `policy decision unknown` |
| d) `tests` 按自报产物 | `experiment_gate_inputs.reported_tests` | `experiment_result.json` / `stdout.log` / `stderr.log` 的**字节**（每项带判词，如 `experiment_result.json:declared_status_SUCCEEDED`） | `no test results provided` |

判据：`tests/application/run_orchestration/test_acceptance_gate_input_face.py` **8 passed**
（四维各有正反两面 + 一条「把自报面抽掉 ⇒ 门判拒并逐句点名」）。
编排层**没有**构造 `tests` / `metrics`（无 `{"pass": True}` 之类）：值只出现在
`ExperimentRunResult` / 制品字节 / 已发生的策略决定里。

### 二、EC-02 正向判据：真实控制面（无 override）实跑到 `SUCCEEDED`

- 判据：`tests/e2e/test_real_control_plane_experiment_live.py`（`requires_live_llm`）。
  跑法：`set -a; . ./.env; set +a` + `RESEARCHOS_AGENT_RUNTIME=openhands`（**单条命令内联前缀**），
  `-q -rs -p no:randomly`。跑前 `EnvCredentialResolver().has('LLM_MAIN_KEY')` 为 True；
  跑后环境与 `.env` **未留**开关。
- 结果：**`1 passed in 15.89s`**，`egress guard: judged 3 connection attempt(s); blocked 0`。
- 样张（**不进仓库**）：`scratch/goal014-c6-real-experiment-sample.json`，逐字事实：
  `state = SUCCEEDED`、`protocol_id = real_experiment_research_v1_0_0`、
  `manifest_digest = sha256:369ee794…`、`failures = []`、控制面 `override = None` +
  `NativePolicyEvaluator` + `policy 0.4.0` + `ncbi_eutils HEALTHY` + `NcbiEutilsProvider`；
  **实验面 1 条**（此前该类 run 为 **0 条**）——`image_digest = sha256:e95de242…`（容器制品）、
  制品 4 件含 `…:metrics`、`metrics = {agreement: True, comparison_reduction_ratio: 7990.0,
  duplicates_expected/found: 40/40, indexed_comparisons: 40, n_items: 800,
  pairwise_comparisons: 319600, seed: 7}`；**证据面 8 条**（`RETRIEVED` 带 `tool_refs` + 真 PMID）；
  **预算面** 1 条 `AGENT_TURNS`（`cost_status UNKNOWN`）。
- 判据自身的限制：本判据跑**一次** run、**一次**真实 LLM 会话、**2 次**真实 NCBI 调用
  （`retmax=3`），不重试、不批量。

### 三、成对反证：两条都是实测的「红 → 绿」

- **(a) 撤 allow ⇒ 冻结前终止**：`scratch/goal014-c6-press-allow-withdrawn.py`（**带保险闸**：
  被撤能力仍在 allow 里就 `REFUSED` 拒跑，保证不可能跑成正向链路；用默认 Fake 会话 runtime，
  被按的是策略面，故绝不会产生真实模型调用）。**三次实测**：
  1. 撤 `literature.search`（**本协议真的链式执行**的那条检索能力）+ `real_experiment_research_v1`
     ⇒ `scratch/goal014-c6-press-allow-withdrawn.txt`：`state = FAILED`、
     `manifest_digest = null`、`failures = ["preflight failed: POLICY_DENIED, TOOL_RISK_ELEVATED"]`、
     `tool_observed = []`、`task/experiment/evidence = 0/0/0`。**这就是本 EC 的按压。**
  2. 撤 `evidence.read` + 同一协议 ⇒ **不动它**（`scratch/goal014-c6-press-evidence-read-withdrawn.txt`）：
     run **照样冻结**（`manifest_digest = sha256:c4248b62…`）、`analysis` 相位跑完
     （1 task / 4 条证据），只在实验相位收在「缝没接」上（按压装配不接实验执行体）。
     **如实结论**：`evidence.read` 不在本协议任何相位的 `required_capabilities` 里 ⇒
     撤它对这条 run 不是反证（是**混淆**）。AC 原写「撤 `evidence.read`」的口径
     **就在 PLAN 的 AC-3 里改对并登记**，不拿混淆结果冒充反证。
  3. 撤 `evidence.read` + `sort_analysis_v1`（cycle 2 的原按压协议，它**真的**要这条能力）
     ⇒ `scratch/goal014-c6-press-evidence-read-cycle2-protocol.txt`：签名与 cycle 2
     **逐字同形**（`FAILED` / `manifest_digest: null` / `POLICY_DENIED, TOOL_RISK_ELEVATED` /
     零面）⇒ 原按压**保留在位**、未被本轮接线削弱。
  **还原**（三次按压共用同一份原文件）：`cp` 回备份，`sha256` **两次一致**
  （`e00bdcb3…`，见 `scratch/goal014-c6-policy-before.sha256`），`git diff --stat` 为空。
  绿的那一半 = 上面第二节（同一协议、同一控制面、allow 在场 ⇒ `SUCCEEDED`）。
- **(b) 去掉实验自报产物 ⇒ 门判拒并点名**：两处。① 单元面
  `test_removing_the_self_report_makes_the_gate_reject_and_name_the_criteria`（同一套代码、
  同一组合约，抽掉自报面后逐句出现 `artifact metrics missing` / `no test results provided` /
  `policy decision unknown`）；② **真实容器面**
  `test_real_experiment_research_offline.py::test_removing_the_self_reported_artifact_makes_the_gate_reject_and_name_it`
  （把脚本的 `artifact_refs` 改成空后**真跑容器**）⇒ `FAILED` + `acceptance gate rejected`
  且判词点名 `ARTIFACT_EXISTS` 与 `metrics`。

### 四、边界条件：逐字节未动（有据）

- 改动面（`git status --short`，本 cycle 自己的文件）：
  产品代码 8 处（`evaluation_gate.py` / `task_phase_helpers.py` / `dependencies.py` /
  `phase_runner.py` / `service.py` / 新增 `experiment_gate_inputs.py` /
  `output_schema_check.py` / `experiments/types.py` + `experiments/governed.py`）、
  出厂面 2 个新文件（协议 + 实验脚本）、判据 3 个新文件 + 3 处记录性 docstring 就地改对。
- **未动**：`examples/config/policy.yaml`（`default_effect: DENY`、`deny` /
  `require_approval` / `allow_with_constraints` 列表、allow 条目数）——按压已逐字节还原；
  `examples/contracts/task_contracts.yaml`（**合约判据一字未改**）；
  `packages/domain/acceptance.py`（`classify_risk` / `WARN` 语义未动）；
  `test_m2_audit.py` 的镜像一致性判据未动。
- 与 `examples/` 无关的三处工作树改动（`apps/web/.../ModelDetails.tsx`、
  `packages/domain/model_drift.py`、`services/api/dto/models.py`）**不是本 cycle 的产物**：
  `git diff --numstat` 对三者**无内容差异**（仅行尾），故不在提交面内、也不影响任何门。

### 五、本地门与 CI

- 规模门禁自查：本 cycle 全部文件 `<= 450` 行、无 `> 50` 行函数（`violations: 0`）；
  `service.py` 恰 450（贴线，未越界）。
- 定向套件（`scratch/goal014-c6-targeted-final.log`）：**67 passed / exit 0**
  = 四维接线 8 + 离线链路含两条按压 3 + 沙箱实验缝容器判据 + evals +
  凭据审计 + `tests/application/preflight/` + `test_m2_audit.py` +
  运行链暴露面架构判据；`egress guard: judged 7; blocked 0`。
- 受影响全量套件（earlier run）：**1251 passed / 2 skipped**，另 3 条
  `tests/api/test_worker_plane_composition.py` 因**本机 DSN 环境**判红（非本改动，
  与 m0 的 DSN pin 配方同源）。
- 凭据审计：本 cycle 的 `scratch/goal014-c6-affected-suite.log` 曾因 traceback 里的
  **DSN 内联口令**被判 offender（6 处）⇒ 已就地掩码（`://user:***@`），
  `tools/credential_audit.py` 现为 **`PASS: 四面扫描无明文凭据命中`**。
- m0（全量 23 项）与 CI 台账：见本 RECHECK 的「六」「七」两节（跑后追加）。

### 六、本地 m0：三次运行逐条归因（含两条环境型判红，**不以「跑绿为止」收场**）

- **第一次**（`scratch/goal014-c6-m0.log`，未代管 `R-F3`）：
  `FAILED: 4 check(s): python/product-lint=1, python/format-check=1, python/tests=1,
  framework/validate_bundle=1`。逐条归因：
  - `product-lint` / `format-check` = **本 cycle 自己的新文件**（6 处超长行 + 2 处 import 次序）；
    已修，`ruff check` / `ruff format --check` 对全部改动文件复绿。
  - `python/tests` = `tests/tooling/test_credential_audit.py` 判红，根因是**本 cycle 的
    scratch 日志里带了 DSN 内联口令**（见第五节）⇒ 掩码后复绿（**不是**改判据）。
  - `framework/validate_bundle` = 环境型残余 **`R-F3`**（仓库外并发写者的 gitignored
    `scratch/self-governance-bootstrap-prompt.md`）。
- **第二 / 第三次**（`scratch/goal014-c6-m0-final-attempt1.log` /
  `scratch/goal014-c6-m0-final.log`，`R-F3` 文件**代管在外**、条数门禁与治理门全绿）：
  **同一形态两次**——`FAILED: 1 check(s): python/tests=1`，而 pytest 的判词是
  **`4446 passed / 19 skipped / 0 failed`**：红来自 **`tests/egress_guard.py` 的结构判据**
  （`egress guard: FAIL — the default gate attempted 2 non-loopback destination(s)`，
  两条都是 `198.18.0.83:443 (kind=private)`，归因到
  `tests/api/test_runs_api.py::test_start_run_unprovisioned_control_plane_reports_actionable_failure`
  的 `build_endpoint_health → _probe_endpoint → probe_connectivity → list_models`，
  即**产品目录里那条真实 endpoint 的探测**）。
  **归因（实测，不是推断）**：同一命令在**干净基线树**（`git worktree` @ `140dcec`，
  无本轮任何改动）上跑出**同一条** `egress guard: FAIL`（`scratch/goal014-c6-baseline-pytests.log`
  第 63 行，同样是 2 条 `198.18.0.83:443`）⇒ **本机 DNS 走 fake-IP 代理（198.18/15）**
  把真实域名解析成该段地址，判据据实判红，与既有记忆
  `local-m0-egress-guard-fake-ip-red` **同源**；**与本轮改动无关**（基线复现），
  **判据一字未动、未绕过**。基线树的其它失败（13 条，含
  `tests/architecture/python/test_services_api_boundaries.py` 与
  `tests/observability/test_collector_evidence.py`）属**干净 worktree 缺 gitignored 物**的
  环境差异，不影响本条归因。
- **`R-F3` 代管**：`sha256:7af32093…` / 69944 B / mtime `2026-09-24 02:17:04 +0800`，
  代管期间两次运行结束后**原样还原**并逐项复核（同 sha256、同字节数、同 mtime）。
- **如实的终局口径**：本机 as-is m0 = **22 PASS / 1 FAILED**（唯一未绿 = 上述 fake-IP DNS
  触发的 `egress_guard` 结构判据；`python/tests` 的**判词**本身是 0 failed）。
  **不得**把它写成「本机 23/23」；**CI（无本机 DNS 代理）是这一项的仲裁**，
  CI 结论见 GOAL 的台账尾巴。
- 其余本地门：`validate.py` = `Cursor 治理验证通过`；`DOCS-CHECK PASS: 6 deterministic checks`；
  web 门 **stub e2e 98 passed（3.5m）** + **live e2e 53 passed（52.7s）**（`tsc` / `eslint` /
  unit / build 由 m0 的 typescript 组承担，全绿）。

### 七、CI 台账与残余

- CI 到终态（`b9c687d`，推送区间 `af05b6a..b9c687d`）：M0
  [36023332433](https://github.com/Eswink/research-system-new/actions/runs/36023332433)
  **六 job 全 success**（`quality-windows-latest` / `collector-quality` /
  `quality-ubuntu-latest` / `eval-gate` / `container-quality` / `console-frontend`）；
  同次推送另触发 CodeQL
  [36023332464](https://github.com/Eswink/research-system-new/actions/runs/36023332464)
  = **success**（3/3）。**这条同时是第六节那项归因的仲裁**：同一 tip 在无 fake-IP DNS 的
  CI 上 `python/tests` 全绿 ⇒ 本机那次判红确属环境型。
- **承继残余**：`R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` / `R-F3` 与
  13 条人工面**原样保留**（本 cycle 未处置、未降级）。
- **本 cycle 新登记的边界（不粉饰）**：① `TEST_PASSES` 的来源是**实验自报**
  （合约 pin 的脚本或装配方给的脚本在沙箱里产出的受控报告），**不是**独立跑测框架；
  ② `POLICY_COMPLIANT` 是**执行期已经发生**的策略求值的**如实记录**，不是门的第二次裁决；
  ③ 真实调用**按次**取最小必要（本轮：正向 1 次 run + 按压 0 次真实模型调用）。
- **一处流程事实**：本轮 live 判据第一次跑时判红在**判据自己的断言**上
  （`KeyError: 'state'` —— 实验读面 DTO 没有 `state` 字段），改判据为既有字段
  （`experiment_run_id` / `image_digest` / 制品名）后复跑 **passed**；**未**放宽任何产品判据。

## 结论

**`PASS_WITH_WARNINGS`** —— ① 四维输入面按用户判词（取 A）接通，四项的值各有唯一来源、
各保留既有反面的恒判词，编排层零构造；② EC-02 正向在**无 `preflight_override`** 的真实
控制面上实跑到 `SUCCEEDED`，三读面齐备（实验 **1** 条 · 证据 **8** 条 · 预算 **1** 条）；
③ 成对反证实测（撤 `literature.search` ⇒ 冻结前终止、零三面；去掉自报产物 ⇒ 门判拒并点名），
另有一次**如实记为混淆**的 `evidence.read` 口径更正（按不动的能力**不当反证**）；
④ 边界逐字节未动（策略面按压已还原 `sha256 e00bdcb3…`、合约判据与域判据文件与 HEAD 内容一致）；
⑤ 独立复检 `scratch/verify_goal014_c6.py` ⇒ `checked=33 failures=0`（分组 A/B/C/D 全零）；
⑥ 记录自洽（`latest_recheck` 相对路径、`child_plans` / `memory_entries` / `ALL_PLAN` /
记忆索引同一提交）。

**WARN**：① `TEST_PASSES` 的来源是**实验自报**、`POLICY_COMPLIANT` 是**执行期已发生**那次
求值的**如实记录**——二者**不是**独立验证，本 EC 只证明产品路径能跑完闭环，不证明实验结论；
② 环境型残余 `R-F3` 仍影响本机 as-is m0（终局行按代管口径给出，**不得**读成「本机一直 23/23」）；
③ `M-1` / 读类能力成类预放行 / 三项残余（升 pin / L3 检测层 / 450 行）仍是**需拍板项**；
④ 承继残余 `R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` / `R-F3` 与 13 条人工面原样保留。
