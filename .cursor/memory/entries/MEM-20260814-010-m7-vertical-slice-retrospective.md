---
id: MEM-20260814-010
title: M7 Reliable Mock Vertical Slice 完成事实（retrospective）
status: ACTIVE
created_at: 2026-08-14
updated_at: 2026-08-14
scope: repository
confidence: 0.9
review_after: 2026-11-14
source_plans:
  - .cursor/plans/tasks/PLAN-20260814-010-m7-vertical-slice-retrospective.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260814-010-m7-vertical-slice-retrospective.md
supersedes: []
tags: [m7, vertical-slice, retrospective, e2e, sqlite]
---

# MEM-20260814-010 — M7 Reliable Mock Vertical Slice 完成事实

## 做了什么

M7（Reliable Mock Vertical Slice）以 commit `782887d`（2026-08-14）落地
全 E2E 编排链：`packages/application/run_orchestration/`（11 模块）实现
Compile → Preflight → Freeze → TeamResolve → Execute → Evidence/Claim →
Gate → Complete；`adapters/sqlite/`（10 模块）实现 SqliteWorkflowEngine
（tasks/leases/idempotency_records/outbox_events）、SqliteArtifactStore
（内容寻址 blob）与 SqliteOutboxEventPublisher（Transactional Outbox）。
Reference Scenario 为 `examples/protocols/sort_analysis_v1.yaml`
（2-phase，execution + review/QUALITY_GATE）；E2E 证据为 `tests/e2e/`
（12 文件，故障注入 F-01..F-12、幂等、cancel/resume、重启恢复）。

M7 完成后 `Foundation / Executable Research Kernel = completed`，仓库
进入产品能力建设阶段。

本记忆由 2026-08-14 文档对账任务事后重建（M7 原开发窗口无独立
Plan/Recheck/Memory）；事实证据为 git log、当前工作区代码/测试与重跑的
validator，详见 PLAN-20260814-010。

## 为什么这样做

M7 是核心基础设施阶段的 Integration Milestone：它首次把 M1-M6 的全链
契约（Domain / Compiler / Preflight / Ports / OpenHands Adapter）以
可执行、可故障注入的方式集成验证，并冻结编排与可靠性语义（at-least-once
+ idempotency + outbox + lease/heartbeat）。该语义是后续所有产品能力
（Tool Plane / Real Experiment Runtime / Console）的承载层。

## 怎么做与复现

1. E2E：`uv run --frozen --no-sync python -B -m pytest -p no:cacheprovider -q tests/e2e`
2. 持久化契约：`uv run --frozen --no-sync python -B -m pytest -p no:cacheprovider -q tests/adapters/sqlite tests/contracts`
3. 全量回归：`python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going`

## 适用边界

- 适用于：M7 完成状态与证据入口的引用；编排链与可靠性语义的当前事实；
  新副作用入口必须继承 F-01..F-12 故障矩阵的验收要求。
- 不适用于：PostgreSQL 生产实现（技术债，BACKLOG）；容器化 Sandbox
  （ExecutionBackend 未实现）；M7 开发窗口内讨论/评审的重建（本记忆
  不包含此类陈述）。

## 失效与复核触发器

- 到达 `review_after`（2026-11-14）时先复核再引用。
- `packages/application/run_orchestration/` 或 `adapters/sqlite/` 的
  Port 契约变化时，以 `tests/contracts/` 与 PORTS.md 为当前事实源。
- 若新增 PostgreSQL adapter 并替换 SQLite 为主路径，本记忆的
  "SQLite 为当前实现" 陈述需更新。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20260814-010-m7-vertical-slice-retrospective.md` | M7 重建记录与 DoD 核对 |
| recheck | `.cursor/plans/rechecks/RECHECK-20260814-010-m7-vertical-slice-retrospective.md` | 2026-08-14 实际重跑验证 |
| git | `782887d` | M7 实现 commit |
| repository | `packages/application/run_orchestration/`、`adapters/sqlite/` | 编排与持久化实现 |
| repository | `tests/e2e/`（12 文件）、`examples/protocols/sort_analysis_v1.yaml` | E2E 证据与参考场景 |