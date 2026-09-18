---
id: MEM-20260918-069
title: "没人读的声明只能二选一：给消费者，或从声明面移除——绝不发明语义"
status: ACTIVE
created_at: 2026-09-18
updated_at: 2026-09-18
scope: repository
confidence: 0.9
review_after: 2027-09-18
source_plans:
  - .cursor/plans/tasks/PLAN-20260918-095-declaration-clearing.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260918-095-declaration-clearing.md
supersedes: []
tags:
  - contract-surface
  - failure-policy
  - claim-request
  - evidence
  - counter-evidence
---

# 声明未消费项清账：移除 vs 发明语义

## 做了什么

GOAL-005 cycle 3（EC-03）把 GOAL-004 收口登记的两条「声明了没人读」清账：

- `ClaimRequest.lease_ttl_seconds`（默认 300 + `>= 1` 校验）——三实现只读**引擎级**
  `self._lease_ttl`，19 个 `ClaimRequest(...)` 构造点**无一传它** ⇒ **移除**该字段
  （`packages/application/ports/workflow_engine.py`），钉住用例
  `tests/contracts/test_claim_fencing_contract.py::test_claim_request_declares_no_lease_ttl_field`。
- 示例契约 `examples/contracts/task_contracts.yaml` 的 `failure_policy`——`on_validation_failure`
  与同类的 `allow_partial_evidence` 都只进 `unhonored`（无消费者）⇒ **从示例移除**，
  只留被消费的 `on_task_failure: FAIL_RUN`；不变量用例
  `tests/loaders/test_contract_loaders.py::test_example_contracts_declare_only_honored_failure_policy_keys`
  对**每个**示例契约断言 `failure_policy_view().unhonored == ()`。

## 为什么这样做

- **注册表（`unhonored`）不是消费者**：一个键被"点名"只说明系统知道自己没读它；
  运维抄了示例却拿到一条不生效的策略，是**示例在骗人**。示例只该示范会被执行的写法。
- **没有需求方时，发明语义比删声明更糟**：把请求级 TTL 做成真的会与 `renew_lease`
  打架（初始租约按请求给、续租按引擎给 ⇒ 同一租约两个 TTL），做对要动 `leases` 行
  schema；而**今天没有任何调用方要这个能力**。删掉声明的成本是零，收益是契约不再撒谎。
- **有些"没有消费者"是 canonical 约束，不是懒**：`on_validation_failure` 的消费者要求
  在**验收门拒收后**处置一条已经 durable `SUCCEEDED` 的任务行（`task_executor._attempt_once`
  先 `engine.complete(...)`，`register_and_gate` 才 `evaluate_gate`）⇒ 需要 canonical
  状态机决策（改写回 `DEAD_LETTER` / 新增终态），属 ADR 边界，登记为后继入口。
- **清账的判据必须是"可判定差异"**：光删代码/改文档不算——两条处置各配一件**用例**，
  并且**反证**证明用例会红。

## 怎么做与复现

```bash
# 反向搜索（判据 1：谁是读者、谁是写者）
grep -rn "lease_ttl_seconds" --include=*.py . | grep -v node_modules
grep -rn "on_validation_failure" --include=*.py --include=*.yaml --include=*.md . 
# 定向
uv run --frozen --no-sync python -B -m pytest tests/loaders tests/contracts/test_claim_fencing_contract.py -q
# 反证 A：把 lease_ttl_seconds 放回 ClaimRequest ⇒ 期望 1 failed（钉住用例）
# 反证 B：把 on_validation_failure 放回示例契约 ⇒ 期望 1 failed（不变量用例）
```

判据落在**声明面本身**（`dataclasses.fields` / 示例契约的 `unhonored`），不是注释；
两件反证各只红对应用例（实跑：`1 failed, 18 passed, 9 skipped` / `1 failed, 21 passed`）。

## 适用边界（踩过的坑）

- **只覆盖平台自带声明面**：任意用户契约里的未知键仍会进 `unhonored` 被点名而不生效——
  这是**设计**（不猜语义），不是残留；不要把"无死声明"读成"所有声明都生效"。
- **同名但不同物的白名单**：`AttributeKey.lease_ttl_seconds`
  （`packages/application/observability/attributes.py`）是**属性键白名单**条目，不承诺
  有人发射它（同表 4/34 条在仓库内未被引用），白名单测试强制的是"发射的键必须在表内"。
  清账时不要把它当同类删掉。
- **引擎级配置是被读的**：`SqliteWorkflowEngine/PostgresWorkflowEngine(lease_ttl_seconds=…)`
  被 claim / `renew_lease` / 过期回收共用（`tests/adapters/sqlite/test_dispatch_ownership.py:122`
  以 `expires_at == START + TTL` 钉住）⇒ 删它会砍真实能力。
- 相关：[[MEM-20260917-061]]（"声明要么有消费者、要么被点名"的上一轮口径；本条把
  "被点名"与"进示例"分开）、[[MEM-20260813-007]]（示例与实现一致性的同类要求）。

## 来源

- PLAN-20260918-095 / RECHECK-20260918-095（GOAL-20260918-005 cycle 3 = EC-03）。
- 上游：RECHECK-20260917-086 W-1、RECHECK-20260917-089 W-1（GOAL-004 收口结论表第 3 项）。
