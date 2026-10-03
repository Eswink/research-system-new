---
id: PLAN-20261001-271
slug: goal-028-ec03-multi-role-subiteration-on-the-default-assembly
title: GOAL-028 cycle 3（EC-03）：默认装配上的完整科研子迭代 — 真标识 + 真 metrics + 评审反证 + 读面四列 + Handoff digest
status: IN_PROGRESS
created_at: 2026-10-01
updated_at: 2026-10-01
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261001-028
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261001-028 的 **EC-03**（合并 ①② 的验收：默认装配上的完整闭环）。
    授权沿用该 GOAL 的 `authorization.ref`：「**新增 / 扩展 provider、协议、契约、配置**」+
    「新增判据 / 夹具 / 探针（落 `tests/**`）」+「修实现过程中发现的真缺陷」+
    push-to-main-for-CI 口径（**只推 `main`**、不 force、不重写历史、不推旁支；
    push 前 `git pull --ff-only origin main`）。
    **本 PLAN 专属边界**：允许给 `examples/protocols/multi_role_research_v1.yaml` 的
    **会话 phase** 补 `session_tool_bindings`（承 EC-01 的声明面：**纯新增字段**，
    phase 的 id / role / 能力 / 契约 / 输出**一字不改**）；**不修改**任何既有判据 / 门禁 /
    阈值 / 放行面（点名：`tests/e2e/test_multi_role_research_offline.py`、
    `tests/e2e/test_ec03_real_runtime_offline_chain.py`、`tests/e2e/test_tool_binding_on_the_default_assembly.py`、
    `tests/application/preflight/**`、`tests/egress_guard.py`、规模门、`tests/api/run_fixtures.py`）；
    **不改** `default_effect: DENY`、`PRODUCT_ROOTS` / m0 条数 / 作业结构（终态行仍 `23`）；
    **零**新依赖；**不得**把真实凭据写进任何地方；**不得**放开默认网络；
    **不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为「恰好一次」
    （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **默认装配实跑**：`multi_role_research_v1` 走 `build_agent_runtime` 的**真实缺省**
      （**非** `map_tools=True` 的测试后门）+ 装配方提供的会话工具实现 ⇒ run 到
      **`SUCCEEDED`**，且 `manifest_digest` 在场（冻结真的发生）。
    status: PENDING
  - id: AC-2
    criterion: >-
      **四相位产出逐条可复核**：① 检索 phase 取到**真标识**（真 PMID）且
      `source_trust_label=RETRIEVED`（由 provider 声明的 `network_domains` 决定，
      **不由本步自称**）；② 实验 phase 产出**真 metrics**（沙箱容器制品 + `image_digest` 在场）；
      ③ 评审 phase **真能判不通过**（反证分支：摘掉上游证据 ⇒ 判拒 ⇒ run `FAILED`，
      判词**点名**缺的那一维）；④ 交付物与覆盖来源之间有 **claim relation**：
      `GET /runs/{id}/evidence` 真读得到四列（`id` / `source_ref` / `content_digest` /
      `source_trust_label`）；⑤ **HandoffBundle 的 digest 序列**可取证（逐任务一条
      `sha256:<64hex>`、互不相同）。
    status: PENDING
  - id: AC-3
    criterion: >-
      **既有判据逐字节未改且全绿**：`tests/e2e/test_multi_role_research_offline.py`、
      `tests/e2e/test_ec03_real_runtime_offline_chain.py`、
      `tests/e2e/test_tool_binding_on_the_default_assembly.py` 等 `git diff` 为空且全绿
      （协议只**新增**绑定字段：id / role / 能力 / 契约 / 输出一字不改）。
    status: PENDING
---

## 验收条件

承 GOAL-20261001-028 的 EC-03，三条 AC 见 frontmatter。

**本 cycle 与 cycle 1 的关系**：EC-01 证的是「声明式映射**机制**成立」（用判据自带的
最小协议）；本 cycle 证的是「**真实那条**多 role 协议在默认装配下跑通」——
差别的实质是：EC-01 的协议没有 run-chain、没有实验 phase、没有评审门，
本 cycle 的协议**五件事全都要成立**。

## 实施清单

- [ ] **WP-A 协议补绑定**：给 `multi_role_research_v1.yaml` 的**会话 phase** 补
      `session_tool_bindings`（`review` 的四个 provider → 能力名）；`scouting` 是
      run-chain（会话工具面为空，无需绑定）；`experiment` 是 deterministic（无会话）。
      phase 的其它字段**一字不改**。
- [ ] **WP-B 判据**：新增默认装配实跑判据（五件事逐条 + 反证分支）。
- [ ] **WP-C 记录 + 门 + 提交**：先写记录 → 记录面判据 → 全量 m0（独占、canonical DSN）
      → 显式路径提交 → push → 轮询 CI 到终态 → 台账**逐提交**。

## 证据

（执行中回填。）

## 影响报告

（收口时回填。）

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-01 | IN_PROGRESS | cycle 3 派生：EC-03（默认装配上的完整闭环）。 |
