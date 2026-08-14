---
id: PLAN-20260814-008
slug: m0-m7-doc-reconciliation
title: M0-M7 Documentation Reconciliation & Engineering Record Completion
status: DONE
created_at: 2026-08-14
updated_at: 2026-08-14
cursor_plan_uri: c:\Users\googl\.cursor\plans\m0-m7文档对账_725aca0c.plan.md
owners:
  - root-agent
authorization:
  source: cursor-plan
  ref: "M0-M7 Documentation Reconciliation & Completion Prompt（用户已审阅并确认执行计划）"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260814-008-m0-m7-doc-reconciliation.md
memory_entries:
  - MEM-20260814-009
  - MEM-20260814-010
---

# PLAN-20260814-008 — M0-M7 文档对账与工程记录补全

## 目标

在不修改产品代码、不伪造历史的前提下，使 M0-M7（含 M5R）的工程记录
（Plan / Recheck / DoD 证据 / 索引 / Roadmap / Backlog / 架构引用 / 完成
状态）真实、完整、自洽、可追溯地反映已完成的系统实现，并明确
`Foundation / Executable Research Kernel = completed` 的正式工程状态。

## 范围

- 包含：M0/M7 Retrospective Reconstruction 记录；Completion Matrix 与
  M7 Completion Record；BACKLOG 三区重构；MILESTONES / VERTICAL_SLICE /
  CHANGELOG 更新；README / CODEX_BOOTSTRAP / docs/INDEX.md /
  SYSTEM_ARCHITECTURE.md 导航与状态校准；全量 validators 与文档一致性审计。
- 不包含：任何产品代码修改；validator 本身修改；git commit（除非用户
  明确要求）；新阶段开发启动；`docs/` 之外的历史改写。

## 架构与数据流

文档事实来源优先级（从高到低）：当前实际代码 → 可执行测试与 validator →
git history → 既有 Plan/Recheck/DoD 证据 → Accepted ADR → 当前架构与
specification → BACKLOG/roadmap → 其他说明性文档。任何 Markdown 声称的
`DONE` 均以代码、测试、commit 三方可执行证据复核；无法以当前证据支撑的
历史性描述一律不写入，缺失记录以 `RETROSPECTIVE_RECONSTRUCTION: true`
显式重建并注明证据来源与重建时间（2026-08-14）。

## 验收条件

- [x] AC-01：M0 与 M7 各存在一份带 `RETROSPECTIVE_RECONSTRUCTION: true`
      标记的阶段记录（Plan + Recheck），证据仅引用 git log、当前代码/
      测试与本次重跑的 validator，无虚构历史。
- [x] AC-02：`docs/roadmap/COMPLETION_MATRIX_M0_M7.md` 覆盖 M0-M7/M5R
      全部阶段，Scope/Implementation/Plan/Recheck/DoD/Git/Status 与
      本次调查事实矩阵一致。
- [x] AC-03：`docs/roadmap/M7_COMPLETION_RECORD.md` 逐项回答 Reference
      Scenario 的 E2E chain，每项引用真实测试文件或 commit。
- [x] AC-04：BACKLOG 重构为 Completed / Remaining Technical Debt / Next
      Product Capability 三区；M6 勾选矛盾与未定义 M8 引用修正；未勾项
      获得 P 级与目标归属。
- [x] AC-05：MILESTONES 含 M5R、真实完成顺序与依赖 DAG、每阶段
      Status=DONE 与证据链接；VERTICAL_SLICE 标注已实现状态；CHANGELOG
      补齐 M6/M7 条目。
- [x] AC-06：README「当前阶段」、CODEX_BOOTSTRAP「Current Engineering
      State」、docs/INDEX.md 导航与快速问答、SYSTEM_ARCHITECTURE 状态
      表述与当前实现一致。
- [x] AC-07：system-spec / governance / cursor-framework validators 与
      全量 pytest 通过；改动的 Markdown 链接全部有效；最终一致性审计
      无 stage/version/path/upstream revision 矛盾残留。

## 实施清单

- [x] STEP-01：读取 governance validator 与 all-plan/recheck skill 格式
      约束；创建 PLAN-20260814-009（M0 retrospective）与
      PLAN-20260814-010（M7 retrospective），登记 ALL_PLAN。
- [x] STEP-02：创建 `docs/roadmap/COMPLETION_MATRIX_M0_M7.md` 与
      `docs/roadmap/M7_COMPLETION_RECORD.md`。
- [x] STEP-03：重构 BACKLOG.md；更新 MILESTONES.md、VERTICAL_SLICE_V0_4_0.md、
      CHANGELOG.md。
- [x] STEP-04：更新 README.md、CODEX_BOOTSTRAP.md、docs/INDEX.md、
      docs/architecture/SYSTEM_ARCHITECTURE.md。
- [x] STEP-05：全量验证（validators + pytest + 链接检查 + 一致性审计）；
      009/010/008 置 DONE 并附 retrospective recheck。

## 子代理使用

Subagent 默认不启用。需要并行时，每个 wave 最多 3 个；多 wave 必须在前一波
完成并整合后才可开始。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| W1 | 三路只读调查（plans/memory 证据、docs 一致性、代码与 git 证据） | 3 | 完成 | 调查结论汇总于本计划"事实基线" |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | STEP-01 | file | `git log --oneline --pretty=format:"%h %ad %s" -80` | 18 commits；真实顺序 M0→M1→M3→M2→M4→M5→M5R→M6→M7 |
| EV-02 | STEP-01 | file | `.cursor/plans/tasks/` 与 `rechecks/` 清单 | M1/M3/M2/M4/M5/M5R/M6 有 Plan+PASS Recheck；M0/M7 无 |
| EV-03 | STEP-02 | test | `tests/e2e/`（12 文件）与 `examples/protocols/sort_analysis_v1.yaml` | M7 E2E 证据齐备 |
| EV-04 | STEP-03 | file | BACKLOG.md 三区重构 diff | 未勾项全部获得归属 |
| EV-05 | STEP-04 | file | README/CODEX_BOOTSTRAP/INDEX/SYSTEM_ARCHITECTURE diff | 状态表述与实现一致 |
| EV-06 | STEP-05 | check | uv 环境：`validate_bundle.py` + `governance-check/validate.py` | 均 PASS（2026-08-14） |
| EV-07 | STEP-05 | test | `run_all_checks.py --profile m0`（uv run --frozen --no-sync） | python/tests 989 passed；dependency-boundaries PASS；TypeScript 全 PASS；framework 全 PASS；product-lint/format/typecheck/learning-evals 为既有 FAIL（见 RECHECK W-01） |
| EV-08 | STEP-05 | check | 最终一致性审计 | stage/version/upstream revision 无矛盾残留 |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-14 | M0/M7 缺失的 Plan/Recheck 以 retrospective 形式重建 | 不伪造原开发窗口记录 | 文档标注 RETROSPECTIVE_RECONSTRUCTION 与证据来源 |
| 2026-08-14 | BACKLOG 中 M7 完成日期以 git commit `782887d`（08-14）为准修正 | 原标注 08-13 与 commit 日期不一致 | CHANGELOG/BACKLOG 同步为 08-14 |
| 2026-08-14 | PostgreSQL（ADR-0002 目标）vs SQLite（M7 实现）差异显式记录，不改 ADR | 规格目标与当前实现分层如实呈现 | SYSTEM_ARCHITECTURE 增补说明，作为技术债条目 |
| 2026-08-14 | m0 profile 首次以系统 Python 3.11 运行产生假失败，改用 `uv run --frozen --no-sync` 重跑 | README 定义的正确入口为 uv 环境 | 以 uv 环境结果为准（RECHECK-20260814-008 W-02） |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-14 | — | IN_PROGRESS | 用户审阅确认 Cursor Plan，授权实施 | Plan URI |
| 2026-08-14 | IN_PROGRESS | DONE | RECHECK-20260814-008 PASS_WITH_WARNINGS（仅含仓库既有工程债 warning） | RECHECK 文件 |

## 影响报告

- Domain/API/schema：无产品代码修改。
- 安全/凭据：无凭据相关变更。
- 兼容性/迁移：文档层校准，无迁移。
- 上游版本：openhands v1.42.0@391fbb8d 保持；仅文档引用核对。
- 下一项任务：BACKLOG Remaining Technical Debt 中 M7 收尾工程债
  （ruff lint/format、mypy 16 errors、learning registry）立项处理；随后
  进入 Next Product Capability 首个能力（推荐 Research Tool Plane）。