---
id: PLAN-20261022-094
slug: goal-094-ledger-judge-and-the-model-written-report
title: GOAL-094 全五个 EC —— 跨 GOAL 台账判据 + 报告由模型撰写（数字仍在事实表）
status: DONE
created_at: 2026-10-22
updated_at: 2026-10-22
parent_goal: GOAL-20261022-094
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261022-094-goal-094-ledger-judge-and-the-model-written-report.md
memory_entries:
  - MEM-20261022-228
---

# PLAN-20261022-094 — GOAL-094 全五个 EC

## 验收条件

- [x] **EC-01**：`tests/tooling/test_goal_ledger_covers_every_commit.py` **遍历**树里所有终态 GOAL（不靠清单登记、不靠验证器传参），判「`CI 台账` 的 `提交` 列里每个哈希都出现在某条 cycle 行的 `commits` 格里」；**只认 `commits` 列**；台账为空 / 台账行没写提交 / 日志无数据行 / 缺小节分别点名。
- [x] **EC-02**：祖父条款两向（序 ≥ 61 进受判面；序 60 被如实跳过且 docstring 写明「不回填历史 = 不改写历史记录」）；两向按压（压日志 ⇒ 点名缺席提交；删 `33e48f57` ⇒ 点名它）各判红，raw `sha256` 逐字节复原并复绿。
- [x] **EC-03**：GOAL-093 台账补 `ff7546d7` / `c626aced` / `2998649d`（一提交一行，零 run 写 `covered_by`）并折进 cycle 2 ⇒ **7 行 = 7 个提交**；判据**未因它而改**；`verify_goal093_closeout.py` 仍全 PASS。
- [x] **EC-04**：报告由模型撰写（第 1…4 节）而数字只在汇编器写的事实表（第 5 节）；模型写数字 ⇒ 点名拒绝；事实表逐行带来源；接叙述者 ⇒ `created_by=model:<endpoint>/<returned>` + 元数据 `narrative` 块；没接 ⇒ 逐字节回到确定性汇编。
- [x] **EC-05**：记录 → `git add` 全部受判文件（含未跟踪）→ 记录面判据 → **最后**跑 m0 写见证 → 提交推送 → CI 到终态；阶梯「报告」行同轮升级；程序表序 62；两表归档各移出最旧 1 条。

## 五、EC 落点

| EC | 落点 | 判据 |
| --- | --- | --- |
| EC-01 | `tests/tooling/test_goal_ledger_covers_every_commit.py`（`ledger_problems` 唯一谓词 + `_terminal_goals_in_scope` 遍历） | 同左（8 条） |
| EC-02 | 同上（`_CUTOFF_SEQ = 61` / `_CUTOFF_DATE`）+ 按压记录 | 同左（`test_the_scope_reaches_this_generation_and_skips_the_grandfathered_ones`）+ RECHECK 第三节 |
| EC-03 | `.cursor/plans/goals/GOAL-20261022-093-...md`（台账 +3 行、cycle 2 `commits` 格 + 自指边界补正） | 新判据 + `tools/verify_goal093_closeout.py` |
| EC-04 | `deliverable/report_narrative.py`（渲染 / 校验 / 事实表 / 任务书）、`run_orchestration/report_narrative_task.py`（`narrate` / `llm_narrator`）、`report_task.py`（`narrator` 缝 + `_body` + `_admission_blocker`）、`report_support.py`（`narrative_runner`） | `tests/application/test_report_narrative.py`（17）+ `tests/application/test_report_narrative_on_the_product_path.py`（7） |
| EC-05 | GOAL / PLAN / RECHECK / MEM / 宪章（序 62 + 阶梯「报告」+ 进展记录 + 归档）+ 见证 | `tools/verify_goal094_closeout.py` + 见证 `terminal_line` |

## 实施清单

- [x] **WP-1**：跨 GOAL 台账判据（唯一谓词 + 遍历受判面 + 祖父条款 + 8 条用例，含表格边界与标题行首两条）。
- [x] **WP-2**：两向按压 + `sha256` 逐字节复原（`scratch/goal094-press/`）。
- [x] **WP-3**：GOAL-093 台账补 3 行 + cycle 2 `commits` 格补齐 + 自指边界补正说明。
- [x] **WP-4**：`report_narrative.py`（四键叙述 / 数字禁令 / 事实表 / 任务书）。
- [x] **WP-5**：`report_narrative_task.py`（`narrate` / `llm_narrator` / `NarratorUnavailable`）。
- [x] **WP-6**：`report_task.py` 接入（`ReportTaskDeps.narrator` / `_body` / `ReportAdmission.narrative` / `created_by` 随作者）。
- [x] **WP-7**：`report_support.narrative_runner` 产品闭包（与 `report_task_runner` 同形同层）。
- [x] **WP-8**：24 条报告判据（两块面 / 数字禁令 / 来源列 / 零回归 / 四态点名 / 归因同源）。
- [x] **WP-9**：宪章（序 62 / 阶梯「报告」行升级 / 进展记录 / 两表归档）。
- [x] **WP-10**：记录面（GOAL / PLAN / RECHECK / MEM）+ 见证 + CI 台账。

## 证据

| 证据 | 读数 |
| --- | --- |
| 新台账判据（真树） | `tests/tooling/test_goal_ledger_covers_every_commit.py` ⇒ **8 passed** |
| 按压①（压日志） | 判红：`CI 台账里的 4 个提交没有任何 cycle 行的 commits 格收录：['33e48f57', '3d53676e', '7fa4f651', 'a905c6c3']`；`sha256` `89e2fda8…` → `c9dcb895…` → 复原 `89e2fda8…` |
| 按压②（删 `33e48f57`） | 判红：`CI 台账里的 1 个提交没有任何 cycle 行的 commits 格收录：['33e48f57']`；`sha256` `89e2fda8…` → `fb67595f…` → 复原 `89e2fda8…` |
| GOAL-093 台账 | 补后 **7 行 = 7 个提交**（`7fa4f651` / `33e48f57` / `a905c6c3` / `3d53676e` / `ff7546d7` / `c626aced` / `2998649d`） |
| 报告面判据 | 两文件 ⇒ **24 passed** |
| 报告面反证 | 撤掉数字禁令 ⇒ **3 failed**（`test_a_numeral_in_the_narrative_is_refused_by_name` ×3）；复原后 `sha256` `91198c6c…` 复绿 |
| 受影响套件 | `tests/application` + `tests/e2e/test_research_report_arc_offline.py` ⇒ **1297 passed / 1 skipped** |
| 规模门 | `tests/tooling/test_python_source_limits.py` ⇒ **1324 passed**（`report_task.py` 418 行、`execute_report_task` 拆分后 ≤ 50 行） |
| 三面清零 | `ruff format --check`（8 files）/ `ruff check` / `mypy`（8 source files）⇒ 全过 |
| 上一轮残余读取器 | `tools/next_round_charter.py` 读 GOAL-093 ⇒ `exit 0`、`W-1…W-5` **5 条**、`sha256:d0aaae8f…` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-22 | **DONE** | 五个 EC 全部达成；判据面本地全绿（台账 8 条 + 报告 24 条 + 受影响 1297 条 + 规模 1324 条）；两向按压各判红并以 raw `sha256` 逐字节复原。 |

## 影响报告

- **Domain / API / schema**：无变化。`ReportAssemblySpec`（契约声明面）**未动**；`ReportInputs` /
  `SECTION_HEADINGS` / `REPORT_ARTIFACT_NAME` 一字未改 ⇒ OpenAPI 快照与 `types.ts` **无需更新**。
- **新增可选面（两处，缺省零回归）**：`ReportTaskDeps.narrator`（`None` = 确定性汇编）与
  `ReportAdmission.narrative`（`None` = 没有模型作者）。`report_metadata(inputs, narrative=None)`
  的缺省键集**逐字不变**。
- **安全 / 凭据**：`llm_narrator` 经既有的 `CredentialResolver.resolve` 取凭据（**不读值、
  不回显、不落盘**）；没有新增出网路径（网关是既有 Port）。`tools/credential_audit.py`
  四面 `offenders=0`。
- **兼容性 / 迁移风险**：无迁移。既有确定性汇编路径的**报告字节逐字节不变**
  （`test_the_compiled_form_is_byte_identical_without_a_narrator` 钉住）；`created_by` 只在
  **接上叙述者**时变化。
- **上游版本影响**：无新增依赖、无 pin 变更。
- **判据面变化**：新增 `tests/tooling/test_goal_ledger_covers_every_commit.py`（8 条，跨 GOAL）+
  `tests/application/test_report_narrative.py`（17 条）+ `test_report_narrative_on_the_product_path.py`
  （7 条）。`tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE` **追加两行**
  （纯收紧）。**没有改任何既有判据的断言。**
- **下一项任务**：报告域 `下一级` = 「叙述质量与事实一致性可判」（需人评或把叙述拆成可核对
  断言）；证据域「跨记录的语义矛盾聚合」仍需先做迁移成本评估；深度轴三行仍待用户拍板。
