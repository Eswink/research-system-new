---
id: PLAN-20261103-105
slug: citation-readings-and-review-driven-revision
title: GOAL-105 子计划 —— 引用充分性读数 + retmax 缺省抹平 + 判词驱动改稿
status: DONE
created_at: 2026-11-03
updated_at: 2026-11-03
parent_goal: GOAL-20261103-105
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261103-105-citation-readings-and-review-driven-revision.md
memory_entries:
  - .cursor/memory/entries/MEM-20261103-239-a-field-default-is-not-a-declaration.md
---

# PLAN-20261103-105

## 背景与靶子

GOAL-20261103-105 的七个 EC。按**提交面**分三个 cycle：

1. **cycle 1（先把既有缺陷修掉）**：`retmax` 缺省抹平（EC-03 第一步）+ 两条今天会红的
   判据。放第一个是因为它是本轮**唯一**的既有缺陷，且其余两件的判据都依赖「未声明」这个
   一等事实在不在。
2. **cycle 2（两个新面）**：引用充分性读数（EC-01）+ 脚注透出（EC-02）；判词驱动改稿
   （EC-04）。两件互不依赖，各自带反证臂。
3. **cycle 3（同类型扩展 + 收口）**：协议相级 `retmax`（EC-03 第二步）+ 文档同步（EC-05）
   \+ 收口资产（EC-06）+ 宪章记账（EC-07）。

## 交付面（checkbox）

- [x] WP-A `ProjectSettings.retmax: int | None = None` + `_retmax_of` 缺省 None（EC-03①）
- [x] WP-B 三条缺陷判据 + 改写 `test_project_settings_defaults_retmax_to_three`（EC-03①）
- [x] WP-C `citation_sufficiency.py` 三个读数 + 四条判据（EC-01）
- [x] WP-D 脚注透出三个读数 + 逐字一致判据（EC-02）
- [x] WP-E `ProtocolPhase.run_chain_arguments` + `CompiledPhase` + schema + spec 搬运
      + 优先级决策 + 三条判据（EC-03②③）
- [x] WP-F `validate_action_references(points=...)` 实词重叠 + 四条判据（EC-04）
- [x] WP-G `MANUSCRIPT_QUALITY.md` §6 残余补句，§7 不动（EC-05）
- [x] WP-H `verify_goal105_closeout.py` + `goal105_closeout_assertions.py` + 登记（EC-06）
- [x] WP-I 宪章记账（EC-07）

## 复检

收口复检：`tools/verify_goal105_closeout.py --root . --verdict-only`（两树入口跑
`--script-mode shared`，`verify_paths` ≥ 2 路，见 GOAL 的 `latest_recheck`）。
待收口时填实测读数。

## 影响报告

（首行写「预判」，收口时改成「实测」。）

- **Domain/API/schema**：`schemas/protocol.schema.json` 的 `$defs.phase` 加**一个可选属性**
  `run_chain_arguments` ⇒ 既有 28 份出厂协议零 diff、零 migration。`ProjectSettings.retmax`
  的缺省从 `3` 改成 `None` 是**语义修复**（未声明不再施加），不产生 API 形状变化
  （该字段不进任何 DTO）。
- **安全/凭据**：零变化（无新凭据、无新出网面、无新工具面）。协议相级 `retmax` 仍在
  既有 `literature.search` 调用面上，非法值点名拒绝。
- **兼容性/迁移**：零 migration。需登记的行为变化：`ProjectSettings.retmax is None`
  现在是「未声明」的**唯一**表示（此前 `3` 兼作两种含义）。
- **上游**：零依赖变化。

## 验收条件

| EC | 判定 | 证据 |
| --- | --- | --- |
| EC-01 | **PASS** | `test_citation_sufficiency.py` 10/10；硬编码读数反证 3 红 |
| EC-02 | **PASS** | `test_manuscript_citation_readings.py` 4/4；脚注三数与函数返回值逐项相等 |
| EC-03 | **PASS** | `test_retmax_undeclared_is_a_fact.py` 5/5 + `test_retmax_protocol_phase.py` 16/16；两条缺陷臂反证红 |
| EC-04 | **PASS** | `test_revision_review_points.py` 7/7；重叠判定短路反证红 |
| EC-05 | **PASS** | `test_manuscript_quality_strong_criterion.py` 5/5；文档 4 插入 0 删除 |
| EC-06 | **PASS** | `verify_goal105_closeout.py --verdict-only` 0 FAIL；两处登记命中 |
| EC-07 | **PASS** | `MAINLINE.md` 四处记账；两行 `下一级` 逐字未动、五项禁词零命中 |

## 实施清单

（与「交付面」逐条对应；全部 DONE，详见上表与 `RECHECK-20261103-105` 的逐条读数表。）

## 证据

（全部为**真实执行**的读数，非「文件在树」。）

- **定向套件**：`test_citation_sufficiency` / `test_manuscript_citation_readings` /
  `test_revision_review_points` / `test_retmax_undeclared_is_a_fact` /
  `test_retmax_protocol_phase` / `test_retmax_project_setting` / `test_retmax_is_configurable`
  / `test_revision_closure` / `test_manuscript_assembler` / `test_manuscript_quality`
  / `test_manuscript_quality_strong_criterion` ⇒ **139 passed**。
- **缺陷实测（修复前 → 修复后）**：`RESEARCHOS_RETMAX=9` 构造期 `{'retmax': 9}` /
  运行期 `{'retmax': 3}` → `{'retmax': 9}`；`retrieval_calls(7)` 构造期 `{'retmax': 7}` /
  运行期 `{'retmax': 3}` → `{'retmax': 7}`。
- **反证臂（全部实测，随后逐字节还原）**：
  - 三个读数改硬编码 ⇒ `test_adding_one_citation_moves_both_readings` 等 **3 红**；
  - `ProjectSettings.retmax` 缺省改回 `3` ⇒ env 臂 / 显式臂 / 「不新造对象」**3 红**，
    而「项目声明压过 env」仍绿（证「未声明是一等事实」而非叠覆盖）；
  - `retmax_for_phase` 忽略协议值 ⇒ 协议臂**2 红**，三个回落臂仍绿；
  - 重叠判定短路成 `if False and …` ⇒ `test_an_action_with_no_shared_word_names_the_point_id`
    **1 红**（`DID NOT RAISE`）；
  - 阈值填值而不给标定来源 ⇒ `uncalibrated_thresholds()` 点名该常量。
- **静态门**：`ruff check` + `ruff format --check` 全绿；`mypy` 对 10 个产品文件 +
  7 个新判据/工具文件零问题；`test_python_source_limits.py` **1408 passed**
  （`phase_capabilities.py` 恰 450 行、`task_executor.py` 449 行、
  `test_tooling_scripts_meet_product_gates.py` 恰 450 行）。
- **协议面**：`validate_bundle.py` ⇒ `验证通过`；出厂协议十一相加载与编译后
  `run_chain_arguments` 全 `None`（文档零改动）。
- **收口验证器**：`tools/verify_goal105_closeout.py --root .` ⇒ 全 PASS；
  `--verdict-only` 输出里 `D:\` / `D:/` 命中 **0**。
- **凭据面**：`tools/credential_audit.py` 四面 `offenders=0`（`tracked` 5058 /
  `records` 1097 / `config_db` 1 / `logs` 940）。
- **全量 m0**：见 GOAL 的 CI 台账（本文件收口时按实测填终态行）。

## 收口审计修复

收口审计抓到一条**未达成**的逐字要求，已修：`citation_sufficiency.py` 曾自带第三份
`_CITATION = re.compile(...)`（且上一行注释自称「直接复用」）。现改为与
`_SENTENCE_SPLIT` 同行导入 `_CITATION`，并给收口验证器加两向判据
（`readings-do-not-redefine-the-citation-grammar` / `readings-import-the-shared-citation-grammar`），
按压留证。详见 `RECHECK-20261103-105` 的 `D-7` 与 GOAL 残余 `W-4`。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-11-03 | CREATED | 建档（承 GOAL-20261103-105）。三个 cycle 按提交面划分。 |
| 2026-11-03 | DONE | 三件交付完成；七条 EC 全 PASS；收口复检 `RECHECK-20261103-105` PASS。 |
