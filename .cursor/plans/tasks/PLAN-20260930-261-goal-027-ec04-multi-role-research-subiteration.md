---
id: PLAN-20260930-261
slug: goal-027-ec04-multi-role-research-subiteration
title: GOAL-027 cycle 4（EC-04）：多 role 科研子迭代 — 3 phase × 3 role + HandoffBundle + 评审真判定 + 四维输入 + 离线终态
status: DONE
created_at: 2026-09-30
updated_at: 2026-09-30
latest_recheck: .cursor/plans/rechecks/RECHECK-20260930-262-goal-027-ec04-multi-role-research-subiteration.md
memory_entries:
  - .cursor/memory/entries/MEM-20260930-177-handoff-digests-carried-task-ids-and-the-same-field-was-never-consumed.md
parent_goal: GOAL-20260929-027
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260929-027 的 **EC-04**（多 role 科研子迭代；本 GOAL 的目标形态）。授权沿用该
    GOAL 的 `authorization.ref`：「**新增 / 扩展协议与 phase 声明**（`examples/protocols/`、
    `examples/contracts/`），使一次 run 能覆盖**多个 role × 多个能力**」+「**修实现过程中
    发现的真缺陷**」+「新增判据 / 夹具 / 探针（落 `tests/**` ⇒ m0 条数仍 `23`）」；
    push-to-main-for-CI 口径（**只推 `main`**、不 force、不重写历史、不推旁支；
    push 前 `git pull --ff-only origin main`）。
    **本 PLAN 专属边界**：**不修改**任何既有判据 / 门禁 / 阈值 / 放行面（点名：
    `tests/e2e/test_run_chain_retrieval_offline.py`、`test_real_experiment_research_offline.py`、
    `tests/application/run_orchestration/test_run_chain_capabilities.py`、
    `tests/architecture/python/test_run_chain_capability_exposure.py`、
    `tests/egress_guard.py`、`tests/application/test_m2_audit.py`、
    `tests/application/preflight/**`、规模门、三道记录面判据、两树入口判据）；
    **不动** capabilities 词表 / `_CAPABILITY_SCOPE` / `policy.yaml`；**不改** `PRODUCT_ROOTS` /
    m0 条数 / 作业结构（终态行仍 `23`）；**零**新依赖；**默认门离线**（判据的检索走
    `httpx.MockTransport`；实验那段是真容器，沿用既有 `requires_docker` 放行面）；
    示例与夹具**零真实凭据**；**不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为
    「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
    **受控的既有文件改动（逐条留档、最小面）**：
    (1) `examples/contracts/task_contracts.yaml` —— **只追加**两份新契约
    （`multi_role_scouting` / `multi_role_review`），既有六份**一字未改**；
    (2) `packages/application/run_orchestration/outcomes.py` + `phase_runner.py` ——
    **修一处真缺陷**（EC-04 授权对象）：`RunOutcome.handoff_digests` 此前装的是
    `tuple(sorted(handoffs))`，而 `handoffs` 的键是 **task id** ⇒ 名叫 digests 的字段装的
    其实是任务 id（实测三条 UUID）。全仓**零消费者**（`rg` 实测）⇒ 错名从未暴露；
    EC-04 要求「HandoffBundle 的 digest 序列」可取证 ⇒ 修正为真 digest
    （`getattr(bundle, "digest")`，确定性排序；缺属性的裸 dict **跳过**不伪造）。
    修正面 = 新增一个**纯函数** + 两处调用点替换；`phase_runner.py` 因此超 450 行 ⇒
    函数落在 `outcomes.py`（既有模块，61 行）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **≥3 phase × ≥3 role（各绑不同 role）**：新协议 `multi_role_research_v1.yaml` 的
      `scouting` / `experiment` / `review` 三 phase 分别绑 `literature_scout` /
      `experiment_engineer` / `scientific_reviewer`；**文档面**（YAML 逐字）与**编译产物面**
      （`plan.phase_assignments`）两侧都断言。
    status: PASS
  - id: AC-2
    criterion: >-
      **HandoffBundle 传递结构化结果**：`RunOutcome.handoff_digests` 逐**执行过的任务**一条
      （2 会话 + 1 实验 = 3），各条是 `sha256:<64hex>`、互不相同、确定性排序。
      （本 EC 同时修掉「字段装 task id」的真缺陷；按压 P-I 证明判据有牙。）
    status: PASS
  - id: AC-3
    criterion: >-
      **评审 phase 真判定（两向都在判据里）**：臂一 —— 摘掉运行链检索接线 ⇒ **侦察 phase**
      的性质维度判拒（判词点名 `retrieved sources`）；臂二 —— 评审的声明依据缺席 ⇒
      链在**声明它**的 phase 上 fail closed（判词点名制品 id），**不得**有任何 phase 被判成功。
    status: PASS
  - id: AC-4
    criterion: >-
      **四维验收输入 + 对照**：实跑含一个**真实沙箱实验** phase（`experiment_execution` 的
      `experiment: {}` 声明 + 装配方给的脚本/镜像）⇒ `tests` / `metrics` / `policy_decision`
      三维由 `_experiment_facts` 从**真实事实**填充；`schema_check` 由合约声明的
      `output_schema` 取。**对照臂**：摘掉实验执行体缝 ⇒ 实验 phase 点名拒绝
      （`no experiment runner is wired`），run `FAILED`。
    status: PASS
  - id: AC-5
    criterion: >-
      **离线实跑终态 + 回归**：主判据跑到 `SUCCEEDED`（冻结真的发生、两个会话任务 `SUCCEEDED`、
      检索真 PMID 进证据链且 `RETRIEVED`、实验制品来自容器且含 `metrics`）；
      既有 run-chain / 实验 / 编排判据**一字未改**复跑全绿；按压三条先红后绿 + 逐字节复原。
    status: PASS
---

## 验收条件

| AC | 判据（简） | 判据文件 / 交付物 | 状态 |
| --- | --- | --- | --- |
| AC-1 | ≥3 phase × ≥3 role；文档与编译产物两侧可证 | `examples/protocols/multi_role_research_v1.yaml` | **PASS** |
| AC-2 | HandoffBundle digest 逐任务一条、互不相同（含**真缺陷修复**） | `packages/application/run_orchestration/{outcomes,phase_runner}.py` + 新判据 | **PASS** |
| AC-3 | 评审真判定两向（侦察性质维度 / 评审依据缺席） | 新判据 | **PASS** |
| AC-4 | 四维输入 + 对照臂（摘缝 ⇒ 点名拒绝） | 新判据（`requires_docker`） | **PASS** |
| AC-5 | 离线实跑 `SUCCEEDED` + 既有判据一字未改 + 按压 | 新判据 + 回归矩阵 | **PASS** |

## 目标

GOAL-027 的 **EC-04**（本 GOAL 的**目标形态**）：让一次 run 覆盖**多个 role × 多能力**，
产出可审的科研交付物。三个会话 phase 各绑不同 role，phase 间经 `HandoffBundle` 传递结构化
结果（不依赖聊天记录），其中实验 phase 是**四维验收输入**里三条的唯一来源，
评审 phase 的判据**真的会判负**。

## 实施清单

- [x] WP-1：勘察（phase_assignments / HandoffBundle 构造点 / `_experiment_facts` 的填充条件 /
  会话工具列表的冻结集语义 / 既有两段执行体缝的接线方式）
- [x] WP-2：新增协议 `examples/protocols/multi_role_research_v1.yaml`（3 phase × 3 role）
- [x] WP-3：`examples/contracts/task_contracts.yaml` 追加两份契约（侦察 / 评审）
- [x] WP-4：**修真缺陷** —— `RunOutcome.handoff_digests` 装的其实是 task id
- [x] WP-5：新增判据（5 类断言 + 2 反证臂）+ 支持件扩展（`OutcomeRecorder`）
- [x] WP-6：按压三条（P-I digest / P-K 评审依据 / 对照臂）+ 逐字节复原
- [x] WP-7：记录（PLAN / RECHECK / MEM / GOAL 回写 / ALL_PLAN）+ m0 + push + CI

## 设计要点（本 EC 的实测事实）

1. **会话工具列表由冻结集减法给出**：`session_tool_ids(frozen, run_chain_ids)`；某 phase
   若**不**在 `required_capabilities` 里覆盖某个 provider，它就会落进**该 phase** 的会话
   工具列表 ⇒ 生产装配（无 provider→SDK 映射）会**点名失败**。实验 phase 的
   `workspace.read` / `code.execute` 与 review phase 的 `literature.*` 覆盖都因此必要。
2. **`EVIDENCE_COVERAGE` 只数本任务可见的来源**（`registration.evidence_source_count`）⇒
   评审 phase 必须**自己声明输入**才有东西可判（上游证据是另一个任务的自产面，不进它的
   计数）。这是 GOAL-010 的既有语义，本 EC 的评审契约因此把「判定依据」写成声明输入。
3. **`minimum_retrieved_sources` 是「本任务的系统取得来源」**⇒ 只有做了检索的 phase
   （侦察）能声明它；评审 phase 声明它就是要求评审者为自己没做的事背书 ——
   **本 EC 不这么写**，并把这条边界写进契约注释（如实边界）。
4. **`_experiment_facts` 只在带实验事实的 phase 上填充三维**（`tests` / `metrics` /
   `policy_decision`）⇒ EC-04 的实跑必须含实验 phase（本协议的第二 phase）。
5. **两段执行体缝**（运行链检索 / 合约声明的沙箱实验）由装配方按既有接法补上
   （`with_capabilities` / `with_contract_declared_experiment`），**不改产品代码**；
   产品组合根今天不自己接（`F-10` 登记）。
6. **`map_tools=True`** 是**测试侧**补 EC-05 的 provider→SDK 映射（与 `sort_analysis_v1`
   的既有判据同一手法）：本协议含真实会话 phase ⇒ 生产装配下会话创建会点名失败
   （既有产品缺口，**如实登记**，不在本 GOAL 内修）。

## 证据

### ① 判据实跑（6 passed）

```text
uv run --frozen --no-sync python -B -m pytest tests/e2e/test_multi_role_research_offline.py -q
⇒ 6 passed in 10.53s
⇒ egress guard: judged 9 connection attempt(s); blocked 0
```

| 面 | 实测 |
| --- | --- |
| AC-1 文档 | `phases` 三条；`scouting→literature_scout` / `experiment→experiment_engineer` / `review→scientific_reviewer` |
| AC-1 编译产物 | `plan.phase_assignments` 逐 phase 含对应 role |
| AC-5 终态 | `run.state=SUCCEEDED`、`manifest_digest` 在场、`protocol_id=multi_role_research_v1_0_0`、`failures=[]` |
| AC-2 任务面 | 任务投影两条（**会话**任务）：`multi_role_scouting`（`scout_a`）/ `multi_role_review`（`reviewer_a`），均 `SUCCEEDED`；实验任务在 experiment 面 |
| AC-2 Handoff | `handoff_digests` = 三条 `sha256:<64hex>`、互不相同（含实验任务那条） |
| AC-5 检索 | 工具证据 `source_trust_label=RETRIEVED`，真 PMID `39284801` / `40601758` 出现在 `id` / `source_ref` |
| AC-4 实验 | `experiments` 一条；`image_digest` 在场（制品来自容器）；`metrics` 制品在 `artifact_ids` |
| AC-3 臂一 | 摘检索接线 ⇒ `FAILED` + 零工具观测 + 判词含 `retrieved sources` |
| AC-3 臂二 | 摘 brief 制品 ⇒ `FAILED` + 判词点名 `input-brief:real_research_v1` + 零 phase 成功 |

### ② 真缺陷修复（本 EC 的授权对象）

**实测（修复前）**：`RunOutcome.handoff_digests` 的三条值是
`21c79561-54a7-4399-81bf-f03715fa3193` 型的 **UUID（task id）**——
来自 `tuple(sorted(handoffs))` 排的是字典**键**。全仓 `rg handoff_digests` 实测**零消费者**
（只有定义与本次新判据）⇒ 错名从未被暴露。
**修复后**：三条值为 `sha256:13e1c629…` / `sha256:838304b2…` / `sha256:9d483c90…`（真 Bundle digest）。
**修法**：新增纯函数 `outcomes.handoff_digests(handoffs)`（取 `bundle.digest`，确定性排序，
缺属性的裸 dict **跳过**不伪造）+ 两处调用点替换；函数落 `outcomes.py`（`phase_runner.py`
因此保持 **449** 行 ≤ 450）。

### ③ 按压矩阵（三条，先红后绿 + 逐字节复原）

| 按压 | 改动 | 实测（红） | 复原验证 |
| --- | --- | --- | --- |
| P-I | `handoff_digests` 改回装 task id（缺陷原形） | **1 failed**（主判据的 handoff 断言） | `e26761de6d18bf60b83b44ff1bd233fd277395b91c170ec28d27ab1b37e05a89`（= 基线）⇒ 6 passed |
| P-J | 评审 phase 改声明侦察契约（**未判红** —— 两份契约判据同形，**如实登记这次按压设计不足**） | 2 passed（无区分度） | 复原后 6 passed |
| P-K | 摘掉评审 phase 的 `inputs` 声明 | **1 failed**（主判据） | `e6eeb05110b9fd93e92439a671463eab11ef4dff3f12e1c0d1d12efdca39e318`（= 基线）⇒ 6 passed |

### ④ 回归面（既有判据逐字节未改）

| 套件 | 结果 |
| --- | --- |
| `tests/e2e/test_multi_role_research_offline.py` + `test_run_chain_retrieval_offline.py` | 8 passed（后者一字未改） |
| `tests/e2e/` + `tests/loaders/` + `tests/application/run_orchestration/` + `tests/architecture/python/` + `tests/tooling/`（一次合并运行，canonical DSN pin） | **1739 passed, 12 skipped**（EXIT=0） |

### ⑤ 静态门

```text
ruff check tests/e2e/ packages/application/run_orchestration/   ⇒ All checks passed!
ruff format --check                                              ⇒ 已格式化
mypy（strict；新判据 + 支持件 + outcomes + phase_runner）        ⇒ Success: no issues found
规模：288 / 315 / 449 / 61 行（均 ≤ 450）、无超 50 行函数
validate_bundle.py                                               ⇒ 验证通过（含 Task / Protocol 引用一致）
```

### ⑥ as-is 本机 m0（记录写入之后，独占运行，首跑即终态）

```text
uv run --frozen --no-sync python -B \n  .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
⇒ PASS: profile=m0; 23 deterministic checks      ← 终态行（条数仍是 23）
⇒ PASS [ 行数 = 24、FAIL [ 行数 = 0、EXIT=0
⇒ 4928 passed, 21 skipped（python/tests 段 in 649.76s）
⇒ 日志 scratch/goal027-c4-m0.log（canonical DSN pin、不接管道、零 python 残留）
```

用例数 4928（cycle 3 收口 4921）⇒ **只增不减**，与「新增判据 ⇒ m0 条数仍 23」一致。
**首跑即终态**（无红点）。

### ⑦ CI 台账

**M0 [`36680932995`](https://github.com/Eswink/research-system-new/actions/runs/36680932995) 八 job 全 `success` + Push-on-main（CodeQL）[`36680932701`](https://github.com/Eswink/research-system-new/actions/runs/36680932701) 3/3 `success`**；两者 `run_attempt=1`（**一次成功、无 flake**；原始 JSON 实查 `jobs=8 ok=8 bad=[]` / `jobs=3 ok=3 bad=[]`，`head_sha=9d29c045…` 与推送 sha 一致；轮询日志 `scratch/goal027-c4-ci-poll.log`）。


## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-30 | IN_PROGRESS | cycle 4 派生：EC-04 = 多 role 科研子迭代。勘察已定：评审必须自带声明输入才能判；实验 phase 是三维输入的来源；两段执行体缝由装配方补。 |
| 2026-09-30 | DONE | **cycle 4 收口**：AC-1…AC-5 全部 PASS。**修一处真缺陷**（`handoff_digests` 装的是 task id；零消费者 ⇒ 从未暴露）。**按压三条**：P-I / P-K 先红后绿且逐字节复原；**P-J 未判红（按压设计不足，如实登记）**。既有判据一字未改；消费者 1739 passed。**残余**：`W-1` 评审契约不声明性质维度（理由写在契约注释）/ `W-2` 生产装配缺 provider→SDK 映射（会话 phase 靠测试侧 `map_tools=True`）/ `W-3` 实验 phase 不在任务投影里（读面分工）/ `W-4` 本 EC 未重测策略 DENY 面 / `W-5` P-J 未提供区分度。 |

## 影响报告

- **Domain/API/schema**：**零** Domain 类型变化、**零** OpenAPI 变化、**零** migrations。
  新增：1 个协议 + 2 份契约 + 1 份判据；产品侧新增 1 个纯函数
  （`outcomes.handoff_digests`）+ 2 处调用点修复。
- **安全/凭据**：新协议复用既有能力名 ⇒ 词表 / `_CAPABILITY_SCOPE` / `policy.yaml` **三处零改动**；
  判据检索走离线 Mock、实验走**既有**沙箱镜像（`requires_docker` 放行面未动）；
  **零真实凭据**。**不宣称**项目安全（`R-M1` 未收口）。
- **兼容性/迁移**：`handoff_digests` 的语义**改变**（task id → 真 digest）；实测**零消费者**
  ⇒ 无迁移、无破坏面；`none`/空 dict 输入仍返回空元组。契约与协议是纯追加。
- **上游版本影响**：零新依赖。
- **可靠性口径**：编排链沿用既有语义；**不宣称**投递语义为「恰好一次」
  （**明确否认**；口径固定为 at-least-once + idempotency + deduplication）。
- **剩余差距 / 下一项任务**：本 EC 的**未覆盖范围** —— 生产装配的 provider→SDK 映射缺口
  （会话 phase 需测试侧补）；实验任务不出现于任务投影；phase 间并行仍不可执行。
  cycle 5 = **EC-05**（自举收口：验证器进树 + 两树复检 + m0 + 台账 + 残余）。
