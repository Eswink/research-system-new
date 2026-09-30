---
id: RECHECK-20260930-262
slug: goal-027-ec04-multi-role-research-subiteration
title: GOAL-027 EC-04 复检：多 role 科研子迭代（3 phase × 3 role / HandoffBundle / 评审真判定 / 四维输入 / 离线终态）
plan_id: PLAN-20260930-261
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-30
completed_at: 2026-09-30
owners:
  - root-agent
---

# RECHECK-20260930-262 — GOAL-027 EC-04 复检

**复检口径**：不采信工具自己的叙述，也不采信「源码里写着判据」；本文件给出**可复核观察面**
（命令 / 判词行 / `rc` / raw `sha256` / 实测值）。**未实跑的不记通过**。

## 检查结果

### 1. 交付物属实

- `examples/protocols/multi_role_research_v1.yaml`：三 phase（`scouting` / `experiment` /
  `review`），各绑**不同** role；`experiment` 由**既有出厂合约** `experiment_execution`
  声明（`experiment: {}`），`scouting` 声明 run-chain 检索。
- `examples/contracts/task_contracts.yaml`：**追加**两份契约（`multi_role_scouting` /
  `multi_role_review`），既有六份**一字未改**。
- `tests/e2e/test_multi_role_research_offline.py`（**288 行**）+
  `tests/e2e/literature_chain_support.py` 扩展（`OutcomeRecorder`，**315 行**）。
- 产品侧：`packages/application/run_orchestration/outcomes.py` 新增纯函数
  `handoff_digests`（**61 行**）+ `phase_runner.py` 两处调用点替换（**449 行** ≤ 450）。
- 四道门：`ruff check` / `ruff format --check` / `mypy`（strict）全绿；规模四条均 ≤ 450、
  无超 50 行函数；`validate_bundle.py` ⇒ `验证通过`（含 Task / Protocol 引用一致）。

### 2. 判据实跑（6 passed）

```text
uv run --frozen --no-sync python -B -m pytest tests/e2e/test_multi_role_research_offline.py -q
⇒ 6 passed in 10.53s
⇒ egress guard: judged 9 connection attempt(s); blocked 0
```

- **AC-1**：YAML 逐字（`scouting→literature_scout` / `experiment→experiment_engineer` /
  `review→scientific_reviewer`）+ 编译产物 `plan.phase_assignments` 两侧一致。
- **AC-2**：任务投影两条会话任务均 `SUCCEEDED`（`scout_a` / `reviewer_a`）；
  `handoff_digests` 三条 `sha256:<64hex>`、互不相同。
- **AC-3 臂一**：摘检索接线 ⇒ `FAILED` + 零工具观测 + 判词含 `retrieved sources`。
- **AC-3 臂二**：摘 brief 制品 ⇒ `FAILED` + 判词点名 `input-brief:real_research_v1` +
  零 phase 被判成功。
- **AC-4**：`experiments` 一条、`image_digest` 在场、`metrics` 制品在；
  **对照臂**：摘实验缝 ⇒ `FAILED` + 判词含 `no experiment runner is wired`。
- **AC-5**：`run.state=SUCCEEDED`、`manifest_digest` 在场、`protocol_id` 逐字、
  `failures=[]`；真 PMID `39284801` / `40601758` 进证据链且 `RETRIEVED`。

### 3. 真缺陷修复（授权对象）

**修复前实测**：`RunOutcome.handoff_digests` 三条值为
`21c79561-54a7-4399-81bf-f03715fa3193` 型 UUID —— `tuple(sorted(handoffs))` 排的是
字典**键**（task id）。`rg handoff_digests` 全仓实测**零消费者** ⇒ 错名从未暴露。

**修复后实测**：`sha256:13e1c629…` / `sha256:838304b2…` / `sha256:9d483c90…`（真 Bundle digest）。

**语义变更的影响面（如实登记）**：`handoff_digests` 从「任务 id 集合」变为「Bundle digest 集合」。
零消费者 ⇒ 无破坏面；空 dict / 无 `digest` 属性的对象 ⇒ 返回空元组或跳过该项（不伪造）。

### 4. 按压矩阵（三条；一条未能判红，如实登记）

| 按压 | 改动 | 实测 | 复原验证 |
| --- | --- | --- | --- |
| P-I | `handoff_digests` 改回装 task id | **1 failed**（handoff 断言） | `e26761de…05a89`（= 基线）⇒ 6 passed |
| P-J | 评审 phase 改声明侦察契约 | **2 passed（未判红）** | 复原后 6 passed |
| P-K | 摘评审 phase 的 `inputs` 声明 | **1 failed**（主判据） | `e6eeb051…318`（= 基线）⇒ 6 passed |

**P-J 的如实登记**：两份契约的验收判据**同形**（`ARTIFACT_EXISTS` + `EVIDENCE_COVERAGE`）
⇒ 换契约不改变判定结果，因此这条按压**没有区分度**。它没有伪造一处假绿：
被压的是「契约选择」，而判据断言的是「三条 role 绑定 + 三条 digest + 终态」，
本来就不该由契约 id 决定。⇒ 登记为**按压设计不足**（不改判据、不改产品）。

### 5. 回归面（既有判据逐字节未改）

| 套件 | 结果 |
| --- | --- |
| 本 EC + `tests/e2e/test_run_chain_retrieval_offline.py`（一字未改） | 8 passed |
| `tests/e2e/` + `tests/loaders/` + `tests/application/run_orchestration/` + `tests/architecture/python/` + `tests/tooling/`（一次合并运行，canonical DSN pin） | **1739 passed, 12 skipped**（EXIT=0） |

### 6. 离线纪律

判据的检索走 `httpx.MockTransport`（真解析、不出网）；实验那段走**既有**沙箱镜像
（`research-os-sandbox:m9-test`，沿用 `requires_docker` 放行面，**未动**）。
`tests/egress_guard.py` **一字未改**。

### 7. 未覆盖范围（明写，不夸大）

- **生产装配缺 provider→SDK 映射**（既有缺口，`F-10` 同族）：本协议的会话 phase 在
  **默认装配**下会话创建会点名失败 ⇒ 判据用测试侧 `map_tools=True` 补上
  （与 `sort_analysis_v1` 既有判据同一手法）。**本 EC 不修该缺口。**
- **实验任务不在任务投影里**（既有读面分工）：`GET /runs/{id}/tasks` 只列会话任务，
  实验任务在 `GET /runs/{id}/experiments` ⇒ 判据按两个读面各自的真实内容断言。
- 评审契约**不声明** `minimum_retrieved_sources`（要求评审者为自己没做的检索背书
  是错的）⇒ 性质维度只由侦察契约承担；这条边界写在契约注释里。
- 本 EC 未重测策略 `DENY` 面对本协议的分支（既有判据在 `test_run_chain_capabilities.py`
  覆盖 `ncbi` 侧）。
- 读面认证 / 多租户 / BOLA·BFLA / 部署面 / `R-M1` —— 承继 GOAL-027 的未覆盖范围，逐条在位。
- **不宣称**项目安全（`R-M1` 未收口）；**不宣称**投递语义为「恰好一次」
  （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。

### 9. as-is 本机 m0 与 CI 台账（推送 `9d29c04`；原始 JSON 实查）

```text
uv run --frozen --no-sync python -B \n  .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
⇒ PASS: profile=m0; 23 deterministic checks      ← 终态行（条数仍是 23）
⇒ PASS [ 行数 = 24、FAIL [ 行数 = 0、EXIT=0
⇒ 4928 passed, 21 skipped（python/tests 段 in 649.76s）
⇒ 日志 scratch/goal027-c4-m0.log（canonical DSN pin、不接管道、零 python 残留）
```

用例数 4928（cycle 3 收口 4921）⇒ **只增不减**，与「新增判据 ⇒ m0 条数仍 23」一致。
**首跑即终态**（无红点）。

M0 [**36680932995**](https://github.com/Eswink/research-system-new/actions/runs/36680932995) 八 job 全 `success`；Push-on-main（CodeQL）[**36680932701**](https://github.com/Eswink/research-system-new/actions/runs/36680932701) 3/3 `success`。两者 `run_attempt=1`。

```text
run=36680932995 name='M0 Quality Gates' conclusion=success attempt=1 head=9d29c045 jobs=8 ok=8 bad=[]
run=36680932701 name='Push on main' conclusion=success attempt=1 head=9d29c045 jobs=3 ok=3 bad=[]
```

轮询日志 `scratch/goal027-c4-ci-poll.log`；取值文件 `scratch/goal027-c4-run-{36680932995,36680932701}{,-jobs}.json`。

## 结论

`PASS_WITH_WARNINGS`。五条 AC 全部 PASS：三 phase 三 role（文档 + 编译产物，AC-1）；
HandoffBundle digest 逐任务一条（含**真缺陷修复**，AC-2）；评审真判定两向各自点名（AC-3）；
四维输入来自真实实验事实 + 对照臂点名拒绝（AC-4）；离线实跑 `SUCCEEDED` + 既有判据逐字节
未改 + 按压逐字节复原（AC-5）。

**警告（残余，逐条在位）**：

- `W-1`：评审契约不声明性质维度（理由已写进契约注释）；若将来有人「顺手补齐」，会把
  「评审者为自己没做的检索背书」这种假要求引进来 —— 判据不防这一点。
- `W-2`：生产装配缺 provider→SDK 映射 ⇒ 会话 phase 靠测试侧 `map_tools=True` 才跑通；
  产品路径今天跑不动本协议（如实登记，不在本 GOAL 内修）。
- `W-3`：实验任务不出现于任务投影（读面分工）；判据因此按两个读面分别断言，
  两处合起来才是「全部 phase」。
- `W-4`：本 EC 未重测策略 `DENY` 面；`FakePolicyEvaluator` 默认 ALLOW。
- `W-5`：按压 P-J 未提供区分度（两份契约判据同形）—— 按压设计不足，非判据缺陷。
