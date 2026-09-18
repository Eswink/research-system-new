---
id: PLAN-20260918-095
slug: declaration-clearing
title: 声明未消费项清账：ClaimRequest.lease_ttl_seconds 与示例契约的 failure_policy 未消费键（EC-03）
status: DONE
created_at: 2026-09-18
updated_at: 2026-09-18
parent_goal: GOAL-20260918-005
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260918-005 cycle 3 = EC-03（GOAL-004 收口结论表第 3 项 / RECHECK-086 W-1 + RECHECK-089 W-1）。授权来源：2026-09-18 用户 goal 模式指令（新建承接 GOAL-005 并自动化循环推进）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260918-095-declaration-clearing.md
memory_entries:
  - MEM-20260918-069
---

# PLAN-20260918-095 — 声明未消费项清账（GOAL-005 cycle 3 = EC-03）

## 目标

GOAL-004 收口把两条「声明了没人读」登记为残留（收口结论表第 3 项）：

- `ClaimRequest.lease_ttl_seconds`（RECHECK-089 W-1）；
- `on_validation_failure`（RECHECK-086 W-1）。

本 PLAN 按 EC-03 的判据**逐条二选一处置**（给真实消费者 / 从契约与文档移除并写明），
先反向搜索、再决定，不照抄上游告警的描述。

## 反向搜索（实测事实，判定依据）

### 1. `ClaimRequest.lease_ttl_seconds`

- **声明面**：`packages/application/ports/workflow_engine.py:57`（默认 300 +
  `__post_init__` 校验 `>= 1`）。
- **读者：零**。三个实现的取租路径都只用**引擎构造时**的 `self._lease_ttl`
  （`adapters/sqlite/workflow_engine.py:66`、`adapters/postgres/workflow_engine.py:90`，
  Fake 同形）；全树搜不到任何一处读 `request.lease_ttl_seconds`。
- **写者：零**。19 处 `ClaimRequest(...)` 构造点（含生产 `services/api/worker_gateway/jobs.py:133`）
  **没有一处**传该字段；`tests/contracts/test_claim_fencing_contract.py` 的
  `_request(**overrides)` 只覆盖 capabilities / partitions / worker_id。
- 后果只有两种：让人以为传了会改 TTL（假 affordance），或传 `0` 被一个**没有效果的校验**
  挡下（响亮失败指向一个不存在的能力）。
- **处置 = 移除**。理由：把"每次 claim 自定义 TTL"做成真的会与既有语义打架——
  `renew_lease` 按引擎 TTL 续租，初始租约若按请求给、续租按引擎给，同一个租约就有了两个
  TTL；要做对必须把 TTL 落到 `leases` 行（schema + 迁移），而**今天没有任何调用方要这个
  能力**。给一个没有需求方的字段发明语义，比删掉声明更糟。租约 TTL 仍是**引擎级配置**
  （`SqliteWorkflowEngine/PostgresWorkflowEngine(lease_ttl_seconds=…)`），能力没有减少。

### 2. `on_validation_failure`

- **声明面**：`examples/contracts/task_contracts.yaml:20`（`DEAD_LETTER`）。
- **读者：零**。`failure_policy_view()` 把它列进 `unhonored`，行为按缺省
  （`packages/domain/failure_policy.py:70`）。
- **为什么没有消费者（实测的 canonical 约束，不是"没来得及做"）**：验收门在任务行**已经
  durable `SUCCEEDED` 之后**才跑——`task_executor._attempt_once` 先
  `engine.complete(… outcome="SUCCEEDED")`，`register_and_gate` 之后才
  `evaluate_gate`。门拒收时任务行已是终态；要按 `DEAD_LETTER` 处置就得把一条
  `SUCCEEDED` 行**改写回去**，那是 canonical 状态机的改动（ADR 边界），属产品语义决策，
  不是本循环能单方面做的（GOAL-004 已登记为后继入口）。
- **处置 = 从示例契约移除**（连同同文件同类、同样无消费者的 `allow_partial_evidence`）。
  示例只保留**被消费**的键；`unhonored` 机制本身**不动**——用户契约里写未知键照样被点名，
  只是**平台自带的示例不再示范一条不生效的策略**。

## 口径

- 两条各自独立处置；判据是**反向搜索 + 可判定差异**，不是改注释/改文案。
- 移除的是**声明**，不是能力：租约 TTL 仍在引擎构造参数上；`unhonored` 点名机制不变。
- 不改门禁、不改快照、不动 canonical 状态机、不新增迁移。
- 用例两件：①「移除钉住」——防止死声明悄悄回流；②示例契约不变量——
  `failure_policy_view().unhonored == ()`，示例只能声明消费得到的键。
- `on_validation_failure` 作为**用户可声明键**的点名用例（域 + 应用）保留：移除示例里的
  声明 ≠ 假装这个键不存在。

## 验收条件

- **AC-01**：`ClaimRequest` 不再有 `lease_ttl_seconds`；全树反向搜索只剩"移除记录"
  （本 PLAN / RECHECK / MEM / GOAL 正文）与引擎级同名配置项；钉住用例实跑通过。
- **AC-02**：示例契约的 `failure_policy` 只含被消费键（`unhonored == ()` 用例钉住）；
  同时 `on_validation_failure` 作为用户可声明键仍被点名（域用例实跑）。
- **AC-03**：文档写明两条各自的处置与原因（`PORTS.md` / `TASK_HANDOFF.md §2.1` /
  `failure_policy.py` docstring / port `ClaimRequest` docstring）。
- **AC-04**：**反证**——把移除掉的东西放回去，两条新用例各自变红（判据有判别力）。
- **AC-05**：定向测试 + m0 全绿；CI 六 job 到终态并记账。

## 实施清单

### WP-A — 移除 `ClaimRequest.lease_ttl_seconds`（已完成）

- `packages/application/ports/workflow_engine.py`：删字段与那条 `>= 1` 校验；docstring
  写明"TTL 是引擎级配置、续租同值、声明过但没人读 ⇒ 移除而不是补实现"。
- `docs/architecture/PORTS.md`（M16 增量段）：写明 TTL 在引擎构造参数上、请求不携带，
  以及为什么不是补实现。
- 钉住用例：`tests/contracts/test_claim_fencing_contract.py::test_claim_request_declares_no_lease_ttl_field`
  （`dataclasses.fields(ClaimRequest)` 不含该名）。

### WP-B — 示例契约清账（已完成）

- `examples/contracts/task_contracts.yaml`：`domain_discovery.failure_policy` 只留
  `on_task_failure: FAIL_RUN`（显式写出的缺省值），并注明为什么未消费键不进示例。
- `docs/architecture/TASK_HANDOFF.md §2.1`：改写"未消费的键"段——示例只声明被消费的键、
  用户契约里的未知键仍被点名、`on_validation_failure` 为什么仍未做（canonical 约束）。
- `packages/domain/failure_policy.py`：模块 docstring 同步。
- 用例：`tests/loaders/test_contract_loaders.py` 的示例断言改到被消费键 +
  新不变量用例 `test_example_contracts_declare_only_honored_failure_policy_keys`。

### WP-C — 验证与记录（已完成）

- 反证两跑、定向套件、m0、RECHECK-20260918-095、MEM-20260918-069、`ALL_PLAN`、
  `memory/INDEX.md`、GOAL-005 回写、CI 轮询到终态。

## 证据

- **反向搜索（清账后）**：`lease_ttl_seconds` 的剩余命中全部是 ① 引擎级构造参数
  （`adapters/sqlite|postgres/workflow_engine.py`、`services/api/worker_gateway/composition.py`、
  测试夹具）② 观测白名单条目 `AttributeKey.lease_ttl_seconds` ③ 文档/记录；**没有任何一处**
  是"请求级字段被读或被传"。`on_validation_failure` 的剩余命中 = ③ 类 + 三处**用例**
  （域/应用/loader）刻意钉住"用户声明它仍被点名、行为按缺省"。
- **反证 ①（实跑）**：把 `lease_ttl_seconds` 放回 `ClaimRequest` ⇒
  `1 failed, 18 passed, 9 skipped`，红的正是
  `test_claim_request_declares_no_lease_ttl_field`（`assert 'lease_ttl_seconds' not in {...}`）。
- **反证 ②（实跑）**：把 `on_validation_failure: DEAD_LETTER` 放回示例契约 ⇒
  `1 failed, 21 passed`，红的正是
  `test_example_contracts_declare_only_honored_failure_policy_keys`
  （`Left contains one more item: 'on_validation_failure'`）。
- **定向套件**（DSN pin 配方）：`tests/api tests/adapters tests/e2e tests/contracts
  tests/application tests/domain tests/loaders` ⇒ **2474 passed / 7 skipped**（355.46s）；
  首跑小集 `tests/loaders + 三条域/应用用例 + claim 契约` ⇒ **101 passed**（11.44s）；
  恢复树后复跑 `loaders + claim 契约` ⇒ **41 passed / 9 skipped**。
- **门禁**：`framework/validate_bundle` 单跑**验证通过**；m0 首跑 **22/23**
  （唯一红 = `framework/validate` 治理校验，原因 = 本 PLAN 当时仍是草稿、缺五个章节且未进
  `ALL_PLAN`，属流程中间态）；记录写完后复跑 m0 见「状态历史」。

## 状态历史

- 2026-09-18 建档（GOAL-20260918-005 cycle 3 = EC-03，driver=client-goal /
  owner=root-agent）：先反向搜索两条声明的全树命中，逐条判定处置（移除 / 移除）；
  `status: IN_PROGRESS`。
- 2026-09-18 反证中间态：`framework/validate` 因草稿 PLAN 缺章节 + 未进 ALL_PLAN 而红，
  其余 22 项绿（**不是**产品缺陷，是记录未写完）。
- 2026-09-18 收口：WP-A/B/C 完成，反证 2 红（各只红对应用例）；`status: DONE`。

## 影响报告

- **Domain / API / schema**：Domain/API 无变化；唯一契约面变化是
  `ClaimRequest` 少一个从未被读的字段（构造点无人传）与示例契约少两条不生效的键。
  `schema/task-contract.schema.json` 的 `failure_policy` 是自由 map（`additionalProperties`），
  未与示例的键耦合，无需改动。
- **持久化 / 迁移**：无迁移；`leases` 行结构与 TTL 写入路径未变。
- **安全 / 凭据**：无凭据面变化（`failure_policy` 不产出凭据、`ClaimRequest` 不携带秘密）。
- **兼容性 / 迁移风险**：低但**有一个外部可见面**——若有人按示例契约抄了
  `on_validation_failure` / `allow_partial_evidence`，它们本来就不生效（今天也不生效），
  变化只在"示例不再示范"。`ClaimRequest.lease_ttl_seconds` 若有外部调用方传入，
  会在构造时 `TypeError`（内部 19 个构造点已全查，无人传）。
- **上游版本影响**：无（未新增/移除依赖）。
- **下一项任务**：GOAL-005 cycle 4 = EC-04（时钟/时序风险逐文件判定）。
