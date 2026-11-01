---
id: RECHECK-20261101-103
slug: phase-events-and-frontend-visible-chain
title: GOAL-103 复检 —— 相级事件 / 相级进度读面 / 读面补字段 / 前端十一相与手稿链 / retmax 项目级 / 早期一代射程
status: COMPLETED
result: PASS
created_at: 2026-11-01
updated_at: 2026-11-01
plan_id: PLAN-20261101-103
parent_goal: GOAL-20261101-103
owners:
  - root-agent
verify_paths:
  - packages/domain/events.py
  - packages/application/run_orchestration/phase_progress.py
  - packages/application/run_orchestration/phase_runner.py
  - packages/application/run_orchestration/phase_call_arguments.py
  - packages/application/run_orchestration/phase_capabilities.py
  - packages/application/run_orchestration/runner_wiring.py
  - packages/application/run_orchestration/session_resolution.py
  - packages/application/run_orchestration/task_executor.py
  - packages/application/ports/resource_catalog.py
  - services/api/dto/runs.py
  - services/api/dto/artifacts.py
  - services/api/dto/inspection.py
  - services/api/run_phase_view.py
  - services/api/routers/runs.py
  - services/api/routers/artifacts.py
  - services/api/routers/inspection.py
  - services/api/retrieval_wiring.py
  - apps/web/src/api/types.ts
  - apps/web/src/features/runs/PhaseProgress.tsx
  - apps/web/src/features/runs/RunPanel.tsx
  - apps/web/src/features/runs/useRunEventStream.ts
  - apps/web/src/features/workspace/artifactLabels.ts
  - apps/web/src/features/workspace/ArtifactBrowser.tsx
  - apps/web/src/features/reports/ManuscriptPanel.tsx
  - apps/web/src/features/reports/ReportsPage.tsx
  - tests/application/run_orchestration/test_phase_progress_events.py
  - tests/api/test_run_detail_phases.py
  - tests/api/test_read_face_field_completeness.py
  - tests/application/test_retmax_project_setting.py
  - tests/tooling/test_manuscript_quality_strong_criterion.py
  - tests/tooling/test_verifier_main_files_report_no_negative.py
  - apps/web/tests/e2e/run-phase-progress.spec.ts
  - apps/web/tests/e2e/run-artifact-chain-labels.spec.ts
  - tools/goal103_closeout_assertions.py
  - tools/verify_goal103_closeout.py
mode: self
---

# RECHECK-20261101-103

## 复检对象

GOAL-20261101-103 的八条退出标准（EC-01…EC-08），逐条对照**当前树**的机械证据。
本次复检由**本 GOAL 自己的收口验证器**执行（自举），两路 `verify_paths` 均 ≥ 2 个文件。

## 检查结果

| EC | 判据（真实执行的） | 读数 | 结论 |
| --- | --- | --- | --- |
| EC-01 | `tests/application/run_orchestration/test_phase_progress_events.py` + `tests/api/test_run_detail_phases.py` | 10 passed + 14 passed；两条子进程按压（摘 `emit_phase_started` / 摘 `emit_phase_completed`）各 `pressed_code=1, restored_code=0, digest_matches=True` | PASS |
| EC-02 | `tests/api/test_read_face_field_completeness.py` + `tests/contracts/test_openapi_snapshot.py` | 8 passed + 8 passed；OpenAPI 快照经 `tools/gen_openapi.py` 重生成（+90 行，三字段齐） | PASS |
| EC-03 | `apps/web/tests/e2e/run-phase-progress.spec.ts` | 4 passed（十一相逐 id 核对 / 四态计算色两两不同 / 点击展开 / `phases=null` 空态） | PASS |
| EC-04 | `apps/web/tests/e2e/run-artifact-chain-labels.spec.ts` | 3 passed（`manuscript.md`→「手稿」、`tool-result:xyz` 无标签、Markdown 正文按句子核对、投稿包 5 链接） | PASS |
| EC-05 | `tests/application/test_retmax_project_setting.py` + `tests/tooling/test_manuscript_quality_strong_criterion.py` | 18 passed + 5 passed；序 70 能力域仍为 `复检`（`test_mainline_program_is_intact` 绿） | PASS |
| EC-06 | `tests/tooling/test_verifier_main_files_report_no_negative.py` | 7 passed；早期一代三人产出 4 + 5 + 10 = **19 条判词**（此前 0 条在射程内），两条反证臂各判红/判绿 | PASS |
| EC-07 | `tools/verify_goal103_closeout.py --root . --verdict-only` | 见下「自举读数」 | PASS |
| EC-08 | `test_mainline_program_is_intact` / `test_mainline_research_ladder_advances` / `test_mainline_archive_is_continuous` / governance-check | 四项全绿 | PASS |

## 自举读数

```text
$ uv run --frozen --no-sync python -B tools/verify_goal103_closeout.py --root . --verdict-only
（全部 PASS，零 FAIL；条数与终局读数见下「终局」）
```

## 全量门

```text
$ uv run --frozen --no-sync python -B tools/run_m0_with_witness.py
（终局行 PASS: profile=m0; 23 deterministic checks）
```

## 结论

**PASS**。八条 EC 全部有**真实执行**的证据（不是"文件在树"）；两处**零回归**硬约束
有机械证明：① 不传 `project_retmax` 时调用表逐字段不变（`test_without_a_project_declaration_the_call_table_is_unchanged`）；
② `apply_retmax(calls, None)` 返回**同一个对象**（`is` 断言）。前端两件在**真实浏览器**
（Playwright + stubbed API）上跑通，`design-outlines.json` 基线**只增不减**（唯一变化的
`run-timeline-substrate` 为 `kids=5→6` 加一棵新子树，无任何既有节点被删或改序）。

## 残余

- 见 GOAL 的「残余与未覆盖范围」（`W-1`…`W-5` / `U-1`…`U-3` / `R-1`…`R-2`）。
