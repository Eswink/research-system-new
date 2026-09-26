---
id: RECHECK-20260926-197
slug: record-face-coverage-recheck
title: GOAL-020 cycle 1（EC-02）独立复检：记录面覆盖判据的按压矩阵 + 判据零改动 + 全量门实测
plan_id: PLAN-20260926-196
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-26
completed_at: 2026-09-26
owners:
  - root-agent
---

# RECHECK-20260926-197 — 记录面覆盖（GOAL-020 EC-02）

## 检查结果

**复检口径**：不复用 PLAN / GOAL 的结论叙述；每一项给出**可复核观察面**（命令、文件、
行号、日志）。**未实跑的不记通过**。

### 一、缺陷的真实形状：**时刻**，不是扫描面（本复检独立复核）

**复检动作**：不采信「记录面从未被扫」这一说法，直接向记录面写一条**含禁用形态**的临时记录，
跑**那一条**判据，看它是否真的判红。

| # | 观察 | 结果 |
| --- | --- | --- |
| 1.1 | 临时探针（`.cursor/plans/rechecks/RECHECK-20260926-999-goal020-probe-temp.md`，含禁用形态） | `test_reproducibility_wording.py` **判红**（`test_no_affirmative_fully_reproducible_claim`，退出码 1） |
| 1.2 | 逐字节删除探针后复跑 | **5 passed**，退出码 0 |
| 1.3 | 结论 | 记录面**本来就在扫描面内** ⇒ 缺陷**不在扫描面，而在时刻**（门跑在记录写入之前）。**本条更正**了 GOAL-020 frontmatter 引述的用户提示词表述（那里写「记录面内容从未被本地门禁覆盖」——字面含义是没扫，实测是**扫了但太早**）。 |
| 1.4 | 取证脚本 | `scratch/goal020-ec02-wp-a-red-before.py`（只读 + 自复原；记录面快照 532 个文件） |

**附带发现（第一次探针没红）**：首版探针写成「本行含禁止形态：完全可复现」，**判据判绿**——
因为「禁止」是 `NEGATION_MARKERS` 之一，同行含否定标记即豁免。这**不是漏洞**，是判据的
设计（判**宣称**不判**话题**）；但它说明：**写探针时不能把自己的意图词写进去**，
否则按压会被自己的措辞豁免。改写成纯宣称句后才判红。

### 二、覆盖判据的按压矩阵（逐条判红 + 逐字节还原）

**复检动作**：跑 `scratch/goal020-ec02-wp-c-press.py`，它对**每条**按压
①断言 `old` 命中次数符合声明（防「按压打偏」）②跑判据 ③**报告实际判红的集合**
（承 `MEM-20260926-144` 的纪律）④逐字节 sha256 还原。

| 按压 | 打到的面 | 判词 | 实际判红的集合 |
| --- | --- | --- | --- |
| P1 | 删话术判据的 `.cursor/plans` 扫描根 | **RED** | `…_names_the_plan_record_face_in_its_scan_roots` + `…_actually_yields_files_from_the_plan_record_face` |
| P2 | 让话术 walker 扫不到东西 | **RED** | `…_actually_yields_files_from_the_plan_record_face` + 原判据的 `test_scan_faces_are_non_empty` |
| P3 | 改凭据审计的 `RECORDS_DIR` | **RED** | `…_credential_audit_names_the_plan_record_face` |
| P4 | 让治理扫描面只扫单层（够不到记录面） | **RED** | `…_governance_scan_reaches_both_record_faces` |
| P5 | runner 把记录面判据挪出门的收集面 | **RED** | `…_judges_are_inside_the_gate_collection_surface` |
| P6 | SOP 条款不再点名判据（悬空） | **RED** | `…_sop_order_clause_names_criteria_that_exist` |
| P7 | 只加注释放宽行长（**期望不红**） | **GREEN** | （无）—— 证明判据不因无关改动误报 |

**结果**：**7/7 符合预期**（6 红 + 1 期望不红），全部逐字节还原，终态复跑 `exit=0`。

**P6 的两次失败（复检价值最高的一处）**：
- **第一次**按压把**文件名**换掉，判据**没红** ⇒ 根因是判据当时断言的是**整篇文档**的
  子串，而该文件名在文档里出现**两次**（第 1 节跑法表 + 新节）⇒ 删一处仍满足。
- **修法**：把断言限定在**承载条款的那一节**（`_sop_section_text()`，取到下一个 `##` 为止），
  并把按压改为声明 `hits=2`（要求全改）。
- **教训（可复用）**：条款类判据必须**按小节**判履行，否则「别处提过」会冒充「条款履行」；
  同时**「打偏」必须记为失败**，否则按压矩阵会被空转糊过去（本轮已改）。

### 三、判据零改动（EC-02 的硬约束）

| # | 观察 | 结果 |
| --- | --- | --- |
| 3.1 | `git diff --stat -- tests/architecture/python/test_reproducibility_wording.py` | **空**（零改动） |
| 3.2 | 该判据的判据 / 词表 / 扫描面 | 逐字未动（`_SCAN_ROOTS` 仍含 `.cursor/plans`；`OVERCLAIM_PHRASES` 与 `NEGATION_MARKERS` 原样） |
| 3.3 | 覆盖机制落在既有 check 内 | 新判据在 `tests/architecture/python/` ⇒ 属 `python/tests` 的收集面（`pytest --ignore=…test_dependency_boundaries.py`）⇒ **不改 m0 条数** |

### 四、全量门的实测（EC-02 的「后绿」证据）

**按压运行（探针在树里）**：`run_all_checks.py --profile m0 --keep-going`
（= `make validate-all`；本机 `make` 不在 PATH，故直接用 runner 的 canonical 命令）
⇒ 终态行 `FAILED: 3 check(s): python/format-check=1, python/tests=1, framework/validate=1`。
其中 **`python/tests` 的红就是探针**（记录面内容违规 ⇒ 门判红 ⇒ **这正是 EC-02 要的结论**）。
另两条红**不是**探针造成的，而是本轮的真实缺陷，已逐条修掉：

| # | 红 | 根因（实测） | 处置 |
| --- | --- | --- | --- |
| 4.1 | `python/format-check` | 新判据有 **1 处**该折叠的 `assert`（`L211:33`）⇒ `ruff format --check` 判红 | 已按 ruff 的形状改写；**定向套件当时全绿** ⇒ 又一次证明「定向全绿 ≠ 全量绿」 |
| 4.2 | `framework/validate` | `工程记忆来源不存在: MEM-20260926-146: …/RECHECK-20260926-197…` + `工程记忆未加入 INDEX: MEM-20260926-146` | 本复检文件即缺失的来源；INDEX 一并补登（记录自洽：被引用文件必须在**同一提交**内） |

**未覆盖范围（如实登记）**：

- 本复检的「后绿」终态行由**本轮收尾的全量门**给出（见 PLAN-196 的证据节与 GOAL 迭代日志）；
  若该次为红，本轮不得 push。
- **`.cursor/memory/entries` 不在**话术判据与凭据审计的记录面里（只由治理的 `.cursor/**`
  文本扫描 + 版本 / 链接扫描覆盖）⇒ 判据里**断言了这个未覆盖事实**
  （`test_the_recorded_uncovered_ranges_are_still_accurate`）；若将来补上覆盖，该用例会红。
- 判据保证的是「记录面**在受判集合内**」；「每次门都跑在记录**之后**」仍靠 SOP 条款 +
  该判据**按小节绑定**条款来维持（**人的顺序**不能由单条判据变成绝对保证，本轮不宣称更强结论）。
- 按压矩阵的探针写在**真实记录目录**里（`rechecks/`）⇒ 若脚本被中断，可能残留探针文件；
  脚本用 `try/finally` + 显式断言 `probe` 不存在，但**中断**仍可能留下它（已如实登记）。

## 结论

**PASS_WITH_WARNINGS**。EC-02 的两条判据（先红后绿 + 按压）成立：记录面**在受判集合内**
已是**机器复核的事实**（6 条按压全红、1 条期望不红、逐字节还原、终态复跑绿），
且 `test_reproducibility_wording.py` **零改动**、m0 **条数不变**。
**警告**（不影响 PASS）：①按压探针若被中断可能残留；②`W-14` 的扫描面清单里
`.cursor/memory/entries` 的**未覆盖**是登记的既有事实，不是本轮引入；
③本复检与实施**同轮** ⇒ 独立结论以 GOAL-020 收口轮的两树复检为准（承 GOAL-019 的同一口径）。
