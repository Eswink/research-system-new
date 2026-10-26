---
id: MEM-20261026-231
title: "产品入口不可用的三件具体事：运行链调用必须标 phase、合约要说明「检索已跑完」、会话工具面要有实现"
status: ACTIVE
created_at: 2026-10-26
updated_at: 2026-10-26
scope: repository
confidence: 0.95
review_after: 2027-04-26
source_plans:
  - .cursor/plans/tasks/PLAN-20261026-097-goal-097-productive-entry-and-novelty.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261026-097-goal-097-productive-entry-and-novelty.md
supersedes: []
---

# 产品入口不可用的三件具体事

## 做了什么

从**产品入口**（`TestClient(create_app(assemble(...)))`，不补缝）跑七相链，把三件互相独立的
缺陷逐条定位并修掉；同时把任务租约 TTL 做成可配（根因未修）。

## 为什么这样做

三件缺陷都只在**真实入口**上暴露：e2e 的手工装配分别补掉了它们（标 `phase_id` 的调用表、
离线替代的检索实现、`replace()` 补的缝）。**从产品入口跑**才是用户目标的真实形态。

## 可复用的坑

1. **运行链调用必须逐条标 `phase_id`**：`planned_in_this_phase` 对 `phase_id is None`
   一律返回 True ⇒ 该调用在**每一个** run_chain 相都执行 ⇒ 问题相在上游产物不存在时取参失败。
2. **合约要说明「工作已经做完了」**：只写覆盖判据的合约会让真实模型去探索仓库/装包，而
   该相会话工具面为空 ⇒ 制品里没有模型声明块 ⇒ 下游解析失败。
3. **会话工具面要的是「实现」不是「provider id」**：`session_tool_ids` 给 provider id、
   `session_tool_bindings` 翻成能力名、**注册表**才决定能不能用；缺名字时 SDK 点名
   `ToolDefinition '<能力名>' is not registered`。
4. **同步执行的租约只心跳一次**：会话超过 `lease_ttl_seconds`（缺省 300s）后租约被回收 ⇒
   `no matching lease for task` ⇒ HTTP **422**（内部失败被报成请求不合法）。

## 射程边界（本记忆**不**声称的）

- 不声称「检索格取名成别的 id 的协议也能跑」——`phase_id` 是常量（登记为 `W-2`）。
- 不声称租约问题已修：只把 TTL 变可配，**会话期心跳与错误映射未改**（`W-4`）。

## 怎么做与复现

```bash
set -a; . ./.env; set +a
RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1   uv run --frozen --no-sync python -B -m pytest   tests/e2e/test_productive_entry_runs_the_whole_chain.py -q -rs
```

判据（离线、默认门）：`tests/api/test_product_roots_carry_the_execution_seams.py`。

## 适用边界

适用于「协议里 `capability_execution: run_chain` 的相 + 会话相混排」的任何协议；对纯会话协议
与纯 deterministic 协议不适用（它们没有 run-chain 排除与跨相取参这两件事）。

## 来源

- `.cursor/plans/tasks/PLAN-20261026-097-goal-097-productive-entry-and-novelty.md`
- `.cursor/plans/rechecks/RECHECK-20261026-097-goal-097-productive-entry-and-novelty.md`
- `.cursor/plans/goals/evidence/GOAL-20261026-097-productive-entry-run.txt`
