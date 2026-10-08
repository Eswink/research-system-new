---
id: MEM-20261008-205
title: "离线控制面的 agent 池是 8 个：协议角色按实际在场的池选，不为判据过而塞 agent"
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
scope: repository
confidence: 0.95
review_after: 2027-04-08
source_plans:
  - .cursor/plans/tasks/PLAN-20261008-333-goal-036-ec03-04-consumption-and-registry.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261008-334-goal-036-ec03-04-consumption-and-registry.md
supersedes: []
tags: [run-fixtures, agent-pool, protocol-design, run-chain, goal-036]
---

## 做了什么

新建一条 2-phase 协议时，`consume` phase 我按语义选了 `meta_reviewer`（它在 `roles.yaml`
里声明了 `review.read`），实跑立刻在 preflight 报 `AGENT_MISSING` —— 本地 run-ready 装配的
agent 池里**没有**该角色的实例。实测池内容（`make_run_ready_deps()` 的 catalog）：

```
director(research_director) domain_a(domain_researcher) engineer(experiment_engineer)
reviewer_a / reviewer_b(scientific_reviewer) scout_a / scout_b(literature_scout) writer(research_writer)
```

⇒ 协议角色必须按**实际在场**的池选（`review.read` 的消费相位改用另一位 `scientific_reviewer`，
语义上正是「同池的另一位评审者读前序结论」）。

## 为什么这样做

两个理由，方向相反但都对：

- **不为判据过而改夹具**：给夹具加一个 `meta_reviewer` agent 会让判据变绿，但那把
  「跑一次真实装配」偷换成「跑一次为这条判据定制的装配」—— 判据的证据价值下降。
- **`AGENT_MISSING` 是编译期的**：`protocol_compile/resolution.py` 按 `agent.role` 从
  `catalog.agents` 筛候选，不足 `min_instances` 即报；它**不**看角色是否声明了能力。
  所以「角色声明了能力」与「池里有该角色的 agent」是**两件事**，协议设计时要分开查。

**连带的两条同族事实**（同一轮实测，写在这里免得再踩）：

1. **运行链调用不能写死 run 标识**：`RunChainCall(run_id_argument=True)` 是读「本 run 自己」
   的唯一正确取键（执行期才有该标识）；写死只可能读到别的 run 或读空。
2. **运行链证据落在 ledger 的 `tool_refs` 上**：`tool_refs = [provider_id, tool_id]`
   （provider 侧 id，不是能力名）；按能力名过滤会看不到它。

## 怎么做与复现

```bash
# 查池子（设计协议前先看一眼）
PYTHONPATH=. uv run --frozen --no-sync python -B -c "
from tests.api.run_fixtures import make_run_ready_deps
ctx = make_run_ready_deps().preflight_override
print(sorted((str(a.id), str(a.role)) for a in (ctx.catalog.agents or {}).values()))"
# 症状：preflight failed: AGENT_MISSING（在 run.failed 事件里，tasks 为空）
```

处置顺序：① 先按池里**已有**角色改写协议（首选）；② 确实需要新角色时，加 agent 是**夹具
变更** —— 与「出厂目录」同轮同步并写明理由，**不得**只为了让某条判据变绿。

## 适用边界

- 适用于**离线 / 受控装配**（`make_run_ready_deps` / `openhands_deps`）下的协议设计。
- **不**适用于生产装配（角色池由运维配置决定）—— 那里 `AGENT_MISSING` 是真缺口，要补配置。
- 本条**不**声称池子内容的长期稳定性：池变化时（新增角色/agent）本条的清单要重新实测。

## 来源

- `.cursor/plans/tasks/PLAN-20261008-333-goal-036-ec03-04-consumption-and-registry.md`
- `.cursor/plans/rechecks/RECHECK-20261008-334-goal-036-ec03-04-consumption-and-registry.md`
