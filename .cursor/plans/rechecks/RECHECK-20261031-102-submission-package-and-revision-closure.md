---
id: RECHECK-20261031-102
slug: submission-package-and-revision-closure
title: GOAL-102 复检 —— supersedes 父指针 / 改稿闭环 / 投稿包五件制品 / 期刊闭集
status: COMPLETED
result: PASS
created_at: 2026-11-01
updated_at: 2026-11-01
plan_id: PLAN-20261031-102
parent_goal: GOAL-20261031-102
owners:
  - root-agent
verify_paths:
  - packages/domain/artifacts.py
  - adapters/sqlite/artifact_store.py
  - adapters/postgres/artifact_store.py
  - adapters/postgres/migrations/030_artifact_supersedes.sql
  - packages/application/run_orchestration/revision_assembly.py
  - packages/application/run_orchestration/submission_assembly.py
  - packages/application/run_orchestration/submission_renderers.py
  - packages/application/deliverable/credit_roles.py
  - packages/application/deliverable/journal_selection.py
  - packages/application/run_orchestration/report_extras.py
  - examples/protocols/direction_to_manuscript_v1.yaml
  - examples/contracts/task_contracts.yaml
  - examples/config/journals.yaml
  - tests/domain/test_artifacts.py
  - tests/application/test_revision_closure.py
  - tests/application/test_submission_package.py
  - tests/application/test_journal_selection.py
  - tests/e2e/test_goal102_product_path.py
  - tools/verify_goal102_closeout.py
  - tools/goal102_closeout_assertions.py
  - .cursor/plans/goals/MAINLINE.md
memory_entries: []
---

# RECHECK-20261031-102

## 检查结果

**PASS**。六个 EC 全部达成（EC-01…EC-06 各自 PASS，证据见下）。

## 一、逐 EC 判定

| EC | 判定 | 证据 |
| --- | --- | --- |
| EC-01 | **PASS** | `tests/domain/test_artifacts.py` ⇒ **19 passed**（链通过 / 缺席 / 跨 run / 二环 / 三环 / 自指构造拒绝 / digest 不变）；`tests/adapters/sqlite/test_artifact_store.py` ⇒ **13 passed**（put/meta 往返 + update 侧 + 跨行链校验）；`tests/postgres/test_artifact_supersedes_pg.py` 在树（无 DSN 按标记跳过；migration 文件存在性与 gapless 顺序由 `tests/postgres/test_migration_files.py` 判）；判据 (v) 成环与 (iii) 无指针的反证臂在两个层面各有（域面 + 读面） |
| EC-02 | **PASS** | `tests/application/test_revision_closure.py` ⇒ **8 passed**：闭环成立（v2 在场、supersedes → v1、读面零问题、信里逐条引用 v2）；反证 (iii) 无指针 v2 ⇒ 读面点名；反证 (v) 成环 ⇒ 读面点名；反证 (iv) 编造引用 / 空谈不引用 ⇒ 任务 FAILED 且点名；旧形状（无改稿块）⇒ 只产应答信零回归；改稿正文写数字 ⇒ FAILED（不降硬规则门槛）。产品入口：`tests/e2e/test_goal102_product_path.py` 判 v2 + supersedes + 正文真的改了 + 信引用 |
| EC-03 | **PASS** | `tests/application/test_submission_package.py` ⇒ **11 passed**（五件装配 + 分派派生 + invented CRediT / 编造 digest / 非布尔 has_conflict / 半份声明 / 空陈述各反证）；产品入口 4 条（五件读面可见 / CRediT ⊆ 分派 / digest 用读面字节 sha256 重算 / COI 按字段读且与声明一致）；协议十一相 + 七产物：`tests/contracts/test_direction_to_manuscript_protocol.py` ⇒ **39 passed** |
| EC-04 | **PASS** | `tests/application/test_journal_selection.py` ⇒ **9 passed**（闭集可读且无评分字段 / 越闭集点名 / 空依据点名 / 半选点名 / 畸形闭集点名 / 镜像核对 / 信封形态可读）；产品入口：编辑决定里的选择经闭集校验通过 |
| EC-05 | **PASS** | `tools/verify_goal102_closeout.py --root . --verdict-only` ⇒ 全绿（见 §三）；两个脚本已登记进 `_VERIFIERS` 与 `IN_SCOPE`（纯收紧） |
| EC-06 | **PASS** | `tests/tooling/test_mainline_program_is_intact.py` + `test_mainline_research_ladder_advances.py` + `test_mainline_archive_is_continuous.py` + `tests/tooling/test_record_tables_are_structurally_sound.py` + `test_record_locators_are_unambiguous.py` ⇒ 全过：程序表序 70、阶梯「复检」「报告」两行收录本 GOAL 且「复检」行 `当前级` 含「改稿闭环（artifact 父指针）」、「下一级」逐字未动、进展/修订两表各 3 行且连续 |

## 二、两向按压（判据自己能被按压红）

1. **域面 (v)**：`TestSupersedes::test_two_node_cycle_is_named` / `test_longer_chain_cycle_is_named`
   —— A⊳B⊳A 与 A⊳B⊳C⊳A 都判 `supersedes cycle`（不是只判一跳）。
2. **读面 (iii)**：`test_the_read_face_refuses_a_pointerless_v2` —— 把已装配的 v2 覆写为
   无指针版本 ⇒ `revision_closure_of_run` 点名 `no supersedes pointer`（按存储状态读，
   不信任装配路径）。
3. **引用 (iv)**：`test_a_fabricated_reference_fails_the_task_by_name` /
   `test_an_action_that_names_no_artifact_fails_the_task_by_name` —— 编造引用与空谈各
   FAILED 且消息点名。
4. **投稿包 (ii)/(iii)/(iv)**：`test_the_read_face_refuses_an_invented_credit_role` /
   `test_the_read_face_refuses_a_fabricated_digest` / `test_a_non_boolean_conflict_field_is_refused`
   / `test_a_prose_only_conflict_rendering_is_refused`。
5. **期刊 (a)–(d)**：越闭集 / 空依据 / 半选 / 畸形闭集四条反证 + 评分字段禁入
   （`journals.yaml` 出现 impact factor / rank 等词 ⇒ 判红）。

## 三、收口验证器

`uv run --frozen --no-sync python -B tools/verify_goal102_closeout.py --root . --verdict-only`
⇒ 判词全 PASS（标准断言集 + 本轮断言集 + 记录面；两树复检见迭代日志与 scratch 归档）。

## 四、如实边界（不是失败，是射程）

- `tests/postgres/test_artifact_supersedes_pg.py` 在无 DSN 环境按 `postgres` 标记跳过
  （m0 的既定形态）；migration 文件面有无 DSN 都受判。
- `data_availability.md` 的清单是「投稿包装配时点」的制品清单（应答信与五件投稿制品
  自身不在其中 —— 鸡生蛋边界，U-3）。
- 期刊选择的「语义匹配好坏」是人评（U-1）；声明面不冒充评价面。
