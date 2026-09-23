---
id: MEM-20260923-109
title: "冻结门的显式策略通道：接受口径与风险分层解耦——WARN 可冻当且仅当「只有 TOOL_RISK_ELEVATED + provider 是 EXECUTE + 它服务的每条能力都被策略显式允许」，且接受要留痕（策略版本/能力/时刻）"
status: ACTIVE
created_at: 2026-09-23
updated_at: 2026-09-23
scope: repository
confidence: 0.9
review_after: 2027-03-23
source_plans:
  - .cursor/plans/tasks/PLAN-20260923-140-policy-allowed-execute-freeze-gate.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260923-141-policy-allowed-execute-freeze-gate.md
supersedes: []
---

## 做了什么

给 `freeze_manifest` 加了一条**显式、留痕、可审计**的接受通道（GOAL-012 EC-01，用户拍板路径 (A)）：
`WARN` 报告在**当且仅当**满足四条时可以冻结并记为 PASS；接受的事实写进
`RunManifest.accepted_policy_exceptions`（optional，缺省空列表）与 `MANIFEST_FROZEN` 事件 payload
（同源同值），每条含 `capability` / `phase_id` / `provider_id` / `policy_version` / `decision` /
`constraints` / `accepted_at`。`classify_risk`、`PreflightStatus`、`PreflightReport.passed`、
`_status()` 与所有 finding 的生成**逐字未动**。

## 为什么这样做

- **「只认 PASS」与「风险分层」是两件事**：`classify_risk(EXECUTE, …) → HIGH` 是**无条件**的，
  于是任何引用 EXECUTE provider 的计划都拿到 `TOOL_RISK_ELEVATED`（WARNING）⇒ `WARN` ⇒ 拒冻
  （GOAL-011 cycle 6 实测的阻断点）。把「只认 PASS」改宽会让**所有** WARN 都能冻；把风险分层
  改宽会让风控不再保守。解耦的唯一办法是给冻结门加**接受口径**，让三处锚点（`passed` /
  `_status()` / `classify_risk`）逐字不动——它们正是既有判据的锚。
- **成对反证必须包含「点名」这一条**：停用通道时三条「点名」断言逐字失败于**旧消息**
  `cannot freeze manifest before a passing preflight` ⇒ 证明「拒绝语义点名缺哪条策略事实」
  这条要求真的在被判据看着，而不是文案。
- **夹具的失败形态是契约**：两处既有判据拿 `sort_analysis_v1` 的**失败形态**当夹具
  （`test_runs_api` 的拒冻、`test_failed_run_semantic_digest_api` 的「永不冻结」载体）。
  产品行为被授权改变后，正确处置是把夹具改成**新的成立前提**（撤掉允许 ⇒ 仍拒冻），
  而不是删掉那条边界覆盖。

## 怎么做与复现

接受条件（`packages/application/preflight/policy_acceptance.py`）：① 报告是 `WARN`；
② **没有** `TOOL_RISK_ELEVATED` 以外的 WARNING；③ 每条 `TOOL_RISK_ELEVATED` 的 provider 可解析、
`effect_class is EXECUTE`、`classify_risk(...) is HIGH`（只认 EXECUTE，`CRITICAL` 一律拒）；
④ 该 provider 服务的**每一条** `ToolRequirement` 经**同一个** `PolicyEvaluator`（scope 用
`policy_check.policy_scope_for` 同一张表）求值为 `ALLOW` / `ALLOW_WITH_CONSTRAINTS`。
任一条不满足 ⇒ 拒冻，消息保留既有前缀再接**逐条**理由。

复现（全部离线）：

```bash
pytest tests/application/preflight/test_policy_allowed_execute_freeze.py -q      # 8 passed
pytest tests/e2e/test_sandbox_experiment_reachability.py -q                      # 4 passed（含成对反证）
python scratch/verify_goal012_c1.py                                              # 28/28；基线树 19 失败
```

三处按压（`scratch/goal012-c1-press{1,2,3}.txt`）：留痕置空 ⇒ 2 红（恰留痕两条）；停用通道 ⇒
5 红（含三条点名断言）；让任意警示可转换 ⇒ 2 红（恰两条不可转换面）。

## 适用边界

- 通道**只**接受「策略已显式允许的 EXECUTE 风险」这一种警示；`TOOL_HEALTH_UNPROVEN` /
  `TOOL_HEALTH_DEGRADED` / `POLICY_APPROVAL_REQUIRED` / 预算类等警示**一律不可转换**。
- **同一个协议在两套装配下结论可能不同**：run-ready/live 装配（`preflight_override` +
  `FakePolicyEvaluator` 默认放行）对 `sort_analysis_v1` 给 `WARN`；真实控制面
  （`NativePolicyEvaluator` + `examples/config/policy.yaml`）因未放行 `evidence.read` 给 `FAIL`。
  引用「该协议今天是 WARN」时必须写明是**哪一套装配**。
- 留痕进 manifest 的 digest 覆盖字节 ⇒ 同一 run 重复冻结只有 `accepted_at` / `frozen_at` 会变；
  未走通道的 manifest 逐字不变（缺省空列表）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260923-140-policy-allowed-execute-freeze-gate.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260923-141-policy-allowed-execute-freeze-gate.md`
- 上游否决记录：GOAL-011 cycle 6/10（阻断点与「需要一次拍板」的登记）与
  `.cursor/plans/tasks/PLAN-20260922-138-real-experiment-chain-via-m12.md`
