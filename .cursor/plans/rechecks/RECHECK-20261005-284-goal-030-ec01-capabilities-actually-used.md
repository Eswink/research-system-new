---
id: RECHECK-20261005-284
slug: goal-030-ec01-capabilities-actually-used
title: 复检：GOAL-030 EC-01 —— 三条已放行承接读能力进入真实 run（调用证据 + 下游消费 + 反证点名）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-05
updated_at: 2026-10-05
plan_id: PLAN-20261005-283
reviewer: root-agent
parent_goal: GOAL-20261005-030
verify_paths:
  - >-
    uv run --frozen --no-sync python -B -m pytest
    tests/e2e/test_capabilities_really_used_in_a_run.py -q ⇒ 8 passed
  - >-
    uv run --frozen --no-sync python -B -m pytest tests/application/preflight
    tests/architecture/python tests/loaders tests/tooling tests/application/evidence
    tests/application/run_orchestration -q ⇒ 1746 passed
  - >-
    uv run --frozen --no-sync python -B -m pytest tests/e2e tests/api -q ⇒
    770 passed / 17 skipped
owners:
  - root-agent
---

# RECHECK-20261005-284 — GOAL-030 EC-01

## 结论

**PASS_WITH_WARNINGS**。GOAL-030 EC-01 的四半（≥3 条真实使用 + 调用证据 + 下游消费证据 +
反证点名）**实测到场**，实跑终态 `SUCCEEDED`；过程中发现并修掉一处**真缺陷**（evidence id
跨 phase 相撞）。既有判据**逐字节未改**。

## 检查结果

## 逐条核对

| EC-01 要求 | 判据 | 实测 |
| --- | --- | --- |
| ≥3 条承接读能力被使用 | `TestThreeCapabilitiesAreReallyCalled` | `artifact.read` / `evidence.read` / `workspace.read` **三条逐条**有调用证据；**逐 phase** 再断言一次 |
| 调用证据 | 同上 | 三条工具证据的 `tool_refs` = `("m12_artifact", <tool_id>)` |
| 下游消费 | `TestTheDownstreamPhaseConsumesIt` | `review` 的 `evidence_read` **返回内容**里含 `probe` 三条工具证据的 id（逐条比对，缺一即点名） |
| 反证点名 | `TestAMissingImplementationIsNamed` | 不给 provider 实例 ⇒ run `FAILED`，判词含 provider 名 + `has no registered instance` + 能力/工具名；且**零工具证据** |
| 实跑终态 | `TestThreeCapabilitiesAreReallyCalled::test_the_run_真的冻结过` | `SUCCEEDED` + `manifest_digest` 在场 + `manifest.frozen` 事件在 |
| 修真缺陷 | `AC-6` | evidence id 补 `task_id`；按压撤回 ⇒ 2 failed 且判词逐字复现 `conflicting evidence registration`；复原 `sha256sum -c` 全 OK |

## 按压记录（两向，各自独立，全部逐字节复原）

1. **撤回缺陷修复**（`tool_evidence.py` 的 evidence id 去掉 `result.task_id`）⇒
   **2 failed**：`assert 'FAILED' == 'SUCCEEDED'` + 判词
   `run-chain capability step failed: conflicting evidence registration:
   evidence:<run>:artifact_read`（**缺陷签名逐字复现**）⇒ 复原后三文件 `sha256` 全 `OK`、
   8 passed。
2. **协议改回会话语义**（`review` phase 删 `capability_execution: run_chain`）⇒ **4 failed**
   （含 `test_the_protocol_declares_a_run_chain_phase_and_the_three_capabilities`，
   点名「声明面变了」）⇒ 复原后 8 passed。

## 如实边界

- 三条读的是**本次 run 自己的 canonical 状态**，**不是外部检索**；不声称读结果影响了
  交付物的科学结论。
- **只用已放行的三条**：另五条无 `allow`（写进协议会打红既有差集判据 —— 实测），
  属 `D-02(b)` 待拍板；受限面逐条登记在 GOAL 记录。
- 装配走 run-ready 夹具，证的是**链路与判据**，不是「真实控制面」。

## 残余（W-NN）

- **`W-1`｜判据侧的 phase 归属靠交付物名推断**：`_phase_of_task` 由 `{task_id}:probe_report`
  / `{task_id}:review_decision` 反推 phase。若将来有人给两个 phase 声明同名交付物，
  该推断会失效 —— 届时判据需改为直接读 `tasks` 读面的 `agent_id`/`contract_id`。
  **当前两 phase 交付物名不同，推断成立**（判据自己也断言了两条契约名）。
- **`W-2`｜运行链按 provider id 过滤（不是能力级）**：`execute_run_chain_capabilities`
  只按 `call.provider_id in spec.run_chain_tool_ids` 筛选，`RunChainCall.capability`
  不参与筛选（现有语义，本 PLAN 未改）。⇒ 本判据的「三条能力各一次」由**装配方的 call
  列表**保证，不由执行层保证。已单列用例固定该前提（`test_the_declared_call_set_covers_the_three_capabilities`）。
- **`W-3`｜`run_id_argument` 是新取参来源，尚未被别的协议使用**：当前只有本协议用；
  它是**有界**的（缺 run id 时点名拒绝），但没有第二个消费者证明其一般性。
- **`W-4`｜两条 `evidence.read` 返回内容靠制品 id 的 task 段区分**：若同一 task 内两次调用
  同名工具，`operation_key` 相同 ⇒ 制品 id 也会相同。当前每 phase 各调一次，未触及该边界。
- **`W-5`｜不改既有判据是「未改」而非「不可改」**：本轮未触及 `EXPECTED_REGISTERED = 15`
  等既有钉死面；受限面（五条未放行能力）的解法仍**待用户拍板**（`D-02(b)`）。

## 未覆盖范围（原样保留）

读面未认证 / 多租户未做 / RBAC 未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口 /
D 组审批通道未接通。**不得**据此宣称项目安全；**不得**宣称投递语义为「恰好一次」
（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
