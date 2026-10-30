---
id: RECHECK-20261030-101
slug: goal-101-narrative-quality-and-verifier-coverage
title: GOAL-101 复检 —— 叙述质量弱口径 / 负判扫描补主文件侧面 / run 归属校验
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-30
updated_at: 2026-10-30
plan_id: PLAN-20261030-101
parent_goal: GOAL-20261030-101
owners:
  - root-agent
verify_paths:
  - packages/application/deliverable/manuscript_quality.py
  - packages/application/deliverable/manuscript.py
  - packages/application/run_orchestration/manuscript_assembly.py
  - docs/architecture/MANUSCRIPT_QUALITY.md
  - tests/application/test_manuscript_quality.py
  - tests/tooling/test_verifier_main_files_report_no_negative.py
  - tests/tooling/test_record_locators_are_unambiguous.py
  - tests/tooling/test_ledger_run_attribution_stays_offline.py
  - tools/charter_progress.py
  - tools/charter_parse.py
  - tools/closeout_recheck_tools.py
  - tools/check_ledger_run_attribution.py
  - tools/verify_goal101_closeout.py
  - tools/goal101_closeout_assertions.py
  - .cursor/plans/goals/MAINLINE.md
memory_entries: []
---

# RECHECK-20261030-101

## 检查结果

**PASS_WITH_WARNINGS**。六个 EC 全部达成（EC-01…EC-06 各自 PASS，证据见下）。
三条 WARN 逐条登记在末节，**都不是**达成失败，而是本轮明确**不覆盖**的面。

## 一、逐 EC 判定

| EC | 判定 | 证据 |
| --- | --- | --- |
| EC-01 | **PASS** | `pytest tests/application/test_manuscript_quality.py` ⇒ **21 passed**；`tests/application/test_manuscript_{assembler,assembly,reference_order}.py` + `test_citation_numbers_reach_the_prompt.py` + e2e 手稿产品路径 ⇒ **48 passed**；两条**真文件按压**见 §二 |
| EC-02 | **PASS** | 17 个验证器逐个 `--verdict-only` ⇒ **0 FAIL**（修前实测 **28** 条假负：14 个验证器 × 2）；`test_verifier_main_files_report_no_negative.py` ⇒ **4 passed**；`test_closeout_verifiers_run_their_own_assertions.py` ⇒ **11 passed** |
| EC-03 | **PASS** | `test_ledger_run_attribution_stays_offline.py` ⇒ **8 passed**；在线读数 10 个终态 GOAL：`SUMMARY rows=72 problems=6 online=True`（存档 `scratch/goal101-20261030/ledger-attribution-online.txt`） |
| EC-04 | **PASS** | `test_record_locators_are_unambiguous.py` ⇒ **6 passed**（两条判据各带反证臂） |
| EC-05 | **PASS** | `tools/verify_goal101_closeout.py --root . --verdict-only` ⇒ 见 §四；两个脚本已登记进 `_VERIFIERS` 与 `IN_SCOPE` |
| EC-06 | **PASS** | `pytest tests/tooling/test_mainline_program_is_intact.py tests/tooling/test_mainline_research_ladder_advances.py tests/tooling/test_mainline_archive_is_continuous.py tests/tooling/test_record_tables_are_structurally_sound.py` ⇒ 全过 |

## 二、两条真文件按压（改事实 ⇒ 判据翻向）

按压的对象是**产品文件**，不是判据文件；每次都记录 `sha256` 并逐字节复原。

1. **摘掉装配面的品质调用**（`manuscript_assembly.py` 删掉
   `validate_manuscript_quality(sections, facts.references)` 那一行）⇒
   `TestWiredIntoTheAssemblyPath::test_the_assembly_function_calls_the_quality_gate`
   **判红 1 条**。复原后 `sha256 = 3dd4617a075fdad486a48d186dba90774af41e60c78e279e9ae22e433bcd68b3`
   （前后相同）。
2. **把引用判据改成恒真**（`manuscript_quality.py` 在 `check_citation_alignment` 开头
   直接 `return`）⇒ `TestCitationAlignment` **判红 3 条**。复原后
   `sha256 = 791d8173cffb113771cbb791b55ce9101aebf985496279fef86f40d1fd3d3edc`（前后相同）。

**两条按压都真的翻向**（不是「判据沉默、对象也沉默」那种假绿）。

## 三、如实登记：本轮**不是**「叙述质量已判」

这是本复检最重要的一段。落地的是**三条必要不充分判据**：

- 过不了 ⇒ 一定是错的；
- 过了 ⇒ **不代表对**。

`manuscript_quality.NOT_JUDGED` 逐条声明**不判**：引用是否**支持**那句话（只判「不是无关」）／
论证是否成立／方法学是否合适／引用是否充分／文风。

因此阶梯「报告」行的 `下一级`（「叙述质量与事实一致性可判」）**原文未改**，
`当前级` 只写到「**弱口径成立**」。把这一格读成已达成属于 `fix_policy.forbidden` 的
「伪造或夸大验证证据」。

## 四、收口验证器

`tools/verify_goal101_closeout.py`（标准断言集 + 本轮断言集 + 记录面三段）与
`tools/goal101_closeout_assertions.py`（本轮特有断言）。两者均已登记进
`tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的 `_VERIFIERS`，
以及 `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`。

## 五、WARN（逐条）

- `WARN-1`｜**强口径未判**：论证是否成立需要人评或模型评，本轮只做了可机械判的那三条。
  这是 GOAL 的 `W-1`，也是阶梯 `下一级` 未改的原因。
- `WARN-2`｜**run 归属的 6 条真实缺陷未修**：GOAL-091 三行（`7f5446ab` 名下挂着
  `eff7c34d` 的 run 两条；`aec28e2c` 无 run 且无 covered_by）、GOAL-099 三行
  （`covered_by` 写成 `<HEAD>` / `<HEAD-of-seq-68>` 占位符）。**不改历史台账**的理由：
  改写当时写下的记录 = 往历史里编造。若要修正，须在各自的 GOAL 上按当时的 API 读数重记。
- `WARN-4`｜**CI 的 Windows `quality` job 卡在 20 分钟超时**（`m0-quality.yml:20` 的
  `timeout-minutes: 20`）：实测两次都恰好 20 分 9 秒、日志无任何失败行，GitHub 报成 `cancelled`。
  **不是**门判红，**也不是**绿。解除要改 `.github/workflows/**`（须用户拍板）⇒ 登记为待拍板
  （GOAL 的 `W-5`）。同一链里四条 run 八 job 全 success，那才是全绿证据。
- `WARN-3`｜**`main()` 端到端不在射程内**：主文件判据只跑 `record_verdicts`（记录面），
  不跑 `main()`（标准集 + 本轮集 + 记录面的联合）。前两段由原判据覆盖，联合面不在射程。
  如实登记为 `U-2`。

## 六、判据改动申报（改既有判据逐条）

| 文件 | 改动 | 为什么不是放宽 |
| --- | --- | --- |
| `tools/charter_parse.py` | `_W_ITEM` 从「只认加粗」改为「加粗或不加粗」 | **纯放宽的唯一被允许方向**：多认一种**已经写下**的形态（87/109 条）。加粗形态照旧解析；附回归钉 + 反证臂（`test_the_plain_residual_form_is_read_too` 证明「两种都不是」时仍拒） |
| `tools/closeout_recheck_tools.py` | 新增 `progress_rows` / `progress_context` / `progress_sources`（委托共享 helper） | **纯新增**，不改任何既有函数 |
| 17 个 `tools/verify_goal0NN_closeout.py` | 进展行读取从「只读活跃面」改为 `TOOLBOX.progress_rows`（活跃面或归档） | **收紧的等价替换**：断言集合与判词名一字未改；改的是**读取面**（此前读错面 ⇒ 假负）。判据数量不变，判定对象从「活跃面有没有」变成「活跃面或归档有没有」—— 这正是「归档是正常结果」的机械含义 |
| `tests/tooling/test_next_round_charter.py` | 新增 2 条用例 | 纯新增 |
| `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` | **未改**（只读它的清单） | 本轮新增的扫描面单列一个文件，正是为了不动它（它里面还有按文件名读 `_VERIFIERS` 的历史断言） |

**一处「改夹具而非改判据」的申报**：新判据打红了 5 处既有夹具（`T1`/`T2` 两字符假标题、
每节同一句话的正文）。处置 = **改夹具**（换成真形状的标题与互不相同的节），
**判据一字未放宽**。这是本轮「按压不是放宽」的具体例子，逐条记在 PLAN 的
「做的时候发现的事实」第 1 条。

## 结论

**PASS_WITH_WARNINGS**。六个 EC 全部达成（逐条证据见 §一）。三条 WARN 都不是达成失败，而是本轮**明确不覆盖**的面：强口径未判（`WARN-1`）、6 条历史台账缺陷只登记不改写（`WARN-2`）、`main()` 端到端不在射程（`WARN-3`）。

本轮最容易被误读的一点，在这里写死：**三条叙述质量判据是弱判据** —— 过不了就是错的，过了**不代表对**。把这一轮读成「叙述质量已判」属于夸大验证证据。
