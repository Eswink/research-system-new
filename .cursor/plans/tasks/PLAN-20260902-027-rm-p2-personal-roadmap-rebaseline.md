---
id: PLAN-20260902-027
slug: rm-p2-personal-roadmap-rebaseline
title: "RM-P2 — Post-M16 Personal Roadmap Rebaseline"
status: DONE
created_at: 2026-09-02
updated_at: 2026-09-02
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "用户 2026-09-02 会话 RM-P2 任务书；Plan Mode 调查与实施计划经用户批准"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260902-027-rm-p2-personal-roadmap-rebaseline.md
memory_entries: []
---

# PLAN-20260902-027 — RM-P2 Post-M16 Personal Roadmap Rebaseline

## 目标

M16 完成后正式执行个人路线 rebaseline：M17 收缩为 Remote GPU Execution /
Personal Scale Baseline；M18/M19 转 DEFERRED（含激活条件）；新增非产品
Gate SI-1 / PA-1 / PA-1R 与 Personal Production Baseline / Usage-driven
Development 定义。docs-only；M16 = DONE / 独立复审 PASS 保持不变；
M0–M16 历史记录零改写。

## 范围

- 包含：`docs/roadmap/MILESTONES.md`、`BACKLOG.md`、`docs/INDEX.md`、
  `docs/roadmap/M16_COMPLETION_RECORD.md`（仅文末追加）、新增
  `docs/adr/ADR-0028-personal-scale-rebaseline.md`、本计划与 recheck 记录。
- 不包含：任何代码/Domain/API/schema/依赖变化；M17 立项与实施；
  M0–M16 Completion/Review Record 正文改写；为 Deferred 项做任何
  Fake/Mock 实现。

## 架构与数据流

不适用（纯文档）。权威链：`docs/roadmap/MILESTONES.md` Post-M7 节
（唯一权威）→ `BACKLOG.md` / `docs/INDEX.md` 投影 → ADR-0028 决策记录
→ M16 完成记录注记（历史正文保持）。

## 验收条件

- [x] AC-01：MILESTONES.md 总览表/DAG/Integration Gates/分层/主开发路径/
      upstream 时间表/下一阶段推荐与 M17/M18/M19/SI-1/PA-1/PA-1R 节
      内部一致，且文首状态块同步。（RECHECK G-02）
- [x] AC-02：M17 Active Scope 为任务书 8 项能力；Deferred Scope 15 项
      正式清单 + 4 条规则（不删除/不标记完成/不作为 PASS 条件/禁止
      Fake-Mock 宣称 supported）。（MILESTONES.md M17 节）
- [x] AC-03：M18、M19 节顶部有 DEFERRED 状态块；M18 含激活条件；
      M19 注明单用户有价值项归 PA-1 且不提前做 M19。
- [x] AC-04：SI-1 / PA-1 / PA-1R / Personal Production Baseline /
      Post-baseline Usage-driven Development 定义落在 MILESTONES.md
      新节（`# Personal Scale Baseline`，四小节）。
- [x] AC-05：M16 状态保持 DONE/PASS；`M16_COMPLETION_RECORD.md` 仅文末
      追加 RM-P2 注记；git diff 证明 M0–M16 历史 record 无正文改写
      （0 deletions）。
- [x] AC-06：BACKLOG.md 状态块补 M15/M16/RM-P2；Next Capability 表
      M17 改写、M18/M19 DEFERRED、新增 3 Gate 行；债务表 M19 目标标注
      DEFERRED。
- [x] AC-07：docs/INDEX.md 状态块修正 M12 stale 行并补 RM-P2 行；
      Roadmap/Versioning 描述更新；ADR-0028 条目加入。
- [x] AC-08：ADR-0028 建立（extended header 风格，Context/Decision/
      Consequences 完整）。
- [x] AC-09：一致性验证（grep 矩阵 + git diff 审计 + governance
      validator）全部通过；RECHECK-20260902-027 判定 PASS。
- [x] AC-10：不自动开始 M17；无代码/schema/依赖变化（git status 仅含
      本计划列出的文档文件）。

## 实施清单

- [x] STEP-01：建立本计划 + ALL_PLAN 行（IN_PROGRESS）。
- [x] STEP-02：MILESTONES.md 13 处编辑（状态块/产品现实节/总览/DAG/
      Gates/分层/主线/上游表/下一阶段推荐/M17 重写/M18/M19 状态块/
      Personal Scale Baseline 节）。
- [x] STEP-03：新建 ADR-0028。
- [x] STEP-04：BACKLOG.md 同步。
- [x] STEP-05：docs/INDEX.md 同步。
- [x] STEP-06：M16_COMPLETION_RECORD.md 文末追加注记。
- [x] STEP-07：一致性验证（grep 矩阵、git diff 审计、docs
      consistency + system-spec validator）。
- [x] STEP-08：RECHECK-20260902-027 → PASS → 计划 DONE + ALL_PLAN
      投影。
- [x] STEP-09：单次 commit（显式路径，禁 git add -A）。

## 子代理使用

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| — | 未使用 | 0 | — | — |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | AC-05/AC-10 | git diff | `git status --short`（5 modified + 2 new，全在计划清单内）；`git diff docs/roadmap/M16_COMPLETION_RECORD.md`（0 deletions，纯文末追加） | PASS |
| EV-02 | AC-01/02/03/04/06/07 | grep 矩阵 | `grep -c "Remote GPU Execution"`（MILESTONES 5 / INDEX 3 / BACKLOG 2 / ADR-0028 1）；`grep -n "SI-1 → PA-1 → PA-1R"`（MILESTONES 153/187/237）；`grep -n "GPU / HPC"`（仅 3 处标注性残留） | PASS |
| EV-03 | AC-09 | validator | `uv run python -B tools/docs_consistency_check.py` → DOCS-CHECK PASS: 6 deterministic checks；`uv run python -B .cursor/skills/system-spec-check/scripts/validate_bundle.py` → 验证通过 | PASS |
| EV-04 | AC-09 | recheck | `.cursor/plans/rechecks/RECHECK-20260902-027-rm-p2-personal-roadmap-rebaseline.md`（result: PASS，G-01..G-06 全过，无 findings） | PASS |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-09-02 | 初始化 | 用户批准的 RM-P2 实施计划（Plan Mode） | 无 |
| 2026-09-02 | 不更新 CHANGELOG.md | CHANGELOG 记录产品能力交付；RM-P2 为路线治理事件，权威落点 MILESTONES.md + ADR-0028；最小必要原则 | 无 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-09-02 | — | APPROVED | Plan Mode 调查 + 实施计划获用户批准 | 本会话 |
| 2026-09-02 | APPROVED | IN_PROGRESS | 开始文档编辑 | STEP-02 起 |
| 2026-09-02 | IN_PROGRESS | VERIFYING | 全部编辑 + 一致性验证完成 | EV-01..EV-03 |
| 2026-09-02 | VERIFYING | DONE | RECHECK-20260902-027 = PASS，AC-01..AC-10 全满足 | EV-04 |

工程记忆：无可复用事实——本计划为 docs-only rebaseline，路线收缩决策与
Deferred 清单已由 ADR-0028 + MILESTONES.md 权威记录，无跨会话可复用的
工程教训需要单独入账。

## 影响报告

- 改动：`docs/roadmap/MILESTONES.md`（rebaseline 核心 13 处）、
  `BACKLOG.md`、`docs/INDEX.md`、`docs/roadmap/M16_COMPLETION_RECORD.md`
  （文末注记）、新增 `docs/adr/ADR-0028-personal-scale-rebaseline.md`、
  本计划与 RECHECK 记录、`ALL_PLAN.md` 投影。
- lint/typecheck/test：docs-only；docs_consistency_check PASS（6 checks）+
  system-spec-check validate_bundle 验证通过；无 Python/TS 改动，
  pytest/m0 不适用。
- Domain/API/schema：无变化。
- 安全/凭据：无凭据变化；文档层面重申 GPU 凭据仅经环境变量/密钥服务、
  Deferred 项禁止 Fake/Mock 宣称 supported。
- 兼容性/迁移：M18/M19 依赖边与 IG-4/IG-5 门保留（DEFERRED 不删除）；
  M17 Hard Deps M16+M9 不变；M0–M16 历史记录零改写。
- 上游版本影响：M17 upstream 行由 Slurm/云 GPU API 改为单机 GPU 运行时
  qualification（实施时按 M5R 模式执行 qualification 再立项）。
- 下一项任务：按新 M17 定义立项（Plan Mode），或执行用户指定的其他
  工作；本计划不自动开工 M17。
