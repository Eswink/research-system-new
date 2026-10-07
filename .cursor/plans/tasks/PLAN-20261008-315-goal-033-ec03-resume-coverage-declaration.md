---
id: PLAN-20261008-315
slug: goal-033-ec03-resume-coverage-declaration
title: GOAL-033 cycle 3（EC-03）：续跑覆盖矩阵机械化 —— 受判面 = 声明集（穷尽枚举 + 与源码对账）
status: DONE
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-316-goal-033-ec03-resume-coverage-declaration.md
memory_entries:
  - a-declared-set-needs-an-explicit-binding-not-prose-matching
parent_goal: GOAL-20261008-033
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-033 的 **EC-03**（续跑覆盖矩阵机械化）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：**只新增**判据与声明集，**不改**任何既有
    判据（`tests/e2e/test_research_continuity_coverage_matrix.py` 一字未动）；
    **受判面不得是交集 / 过滤 / 空集恒真**（`MEM-160` / `MEM-20261005-187`）；
    **不得**宣称安全（`R-M1`），**不得**宣称投递语义为恰好一次（**明确否认**）。
objective: >-
    把 GOAL-032 `W-4` 登记的「『不处理』清单是代表而非穷尽」推进到**声明集穷尽枚举**：
    ① 把 `services/api/run_resume.py::rebuild_and_resume` 的结局面写成**声明集**
    （每条 = 情形 + 判定 + **判据落点**或**理由**，没有第三种状态）；② 声明集里的每条
    `evidence` 必须**真的存在**（文件 + 用例名，AST 核）；③ 与**入口源码**对账
    （拒绝面字面量逐条有归属，且归属**恰好一条**）；④ 受判面 = 声明集本身（规模下界 +
    三面各自下界），**不是** `declared ∩ evidence`；⑤ 两向反证（幽灵条目 / 规模缩水
    各判红）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **声明集穷尽枚举**：`tests/tooling/resume_coverage_declaration.py` 的
      `DECLARED_CASES` 覆盖入口的**全部**结局面 —— 成功面（2）/ 本入口拒绝面（6）/
      不归本入口管（5），共 **14** 条（下界 14）；三条判定面各有下界（2/6/5）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_resume_coverage_declaration_matches_source.py -q` ⇒
      `test_the_declared_set_is_well_formed` 绿。
    status: PASS
  - id: AC-2
    criterion: >-
      **判据落点无幽灵引用**：每条 `evidence` 的 `文件::用例名` 必须真的被定义
      （`ast` 找函数定义）。建档首版我凭印象写了 **7 个不存在的用例名** ⇒ 本条当场全抓出
      ⇒ 证明受判面非空。
    verify: >-
      同文件的 `test_every_declared_evidence_really_exists` ⇒ 绿。
    status: PASS
  - id: AC-3
    criterion: >-
      **与源码对账（按字段，不按散文）**：入口的**可枚举**拒绝字面量
      （`ResumeAttempt(refusal="…")` 两条）各自被**恰好一条**声明条目认领
      （`source_literals` 字段）；漏认领 / 重复认领 / 绑定的字面量在源码里不存在 ⇒ 判红。
    verify: >-
      同文件的 `test_every_source_literal_is_bound_to_exactly_one_declared_case` ⇒ 绿。
    status: PASS
  - id: AC-4
    criterion: >-
      **反掩蔽**：受判面是**声明集本身**（逐条遍历），不是交集；并自证
      `findings()` 对**规模缩水**与**整面抽掉**都会报出问题（否则空集是空真）。
    verify: >-
      同文件的 `test_the_overlay_is_not_an_intersection` ⇒ 绿（含两组合成面自证 +
      构造期不变量 `pytest.raises(ValueError)`）。
    status: PASS
  - id: AC-5
    criterion: >-
      **两向反证（各独立、二进制安全、sha 归因）**：① 往声明集加一条幽灵条目 ⇒ 判红；
      ② 删掉一条（规模压到下界以下 + 拒绝面缩水）⇒ 判红；复原后逐字节相同。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal033-cycle3-press.py` ⇒
      `P1_RED exit=1 1 failed` / `P2_RED exit=1 3 failed` / `RESTORED True` /
      `FINAL_MATCHES_BASELINE True`；留档 `scratch/goal033-cycle3/press-matrix.log`（CR=0）。
    status: PASS
  - id: AC-6
    criterion: >-
      **既有判据零改动**：`tests/e2e/test_research_continuity_coverage_matrix.py`
      **一字未动**（本 PLAN 只**新增**两个文件）；`git diff --numstat` 对既有判据零条目。
    verify: >-
      `git status --short` 逐条读数 + `git diff --numstat -- tests/e2e` 读数为空。
    status: PASS
  - id: AC-7
    criterion: >-
      **门绿**：`ruff check` / `ruff format --check` / `mypy` / 规模门；`tests/tooling`
      全绿（1364 passed）。
    verify: >-
      四道门读数 + `uv run --frozen --no-sync python -B -m pytest tests/tooling -q`。
    status: PASS
---

# PLAN-20261008-315 — GOAL-033 cycle 3（EC-03）：续跑覆盖矩阵机械化

## 验收条件

见 frontmatter `exit_criteria`（AC-1…AC-7）。

## 实施清单

- [x] `tests/tooling/resume_coverage_declaration.py`（声明集 + 自审器 `findings()`）。
- [x] `tests/tooling/test_resume_coverage_declaration_matches_source.py`（6 例）。
- [x] 按压脚本 `scratch/goal033-cycle3-press.py`（AST 定位 + 二进制安全 + sha 归因）。
- [x] 记忆 `a-declared-set-needs-an-explicit-binding-not-prose-matching`。

## 证据

### 声明集（14 条，三面）

| 面 | 条数 | 例子 |
| --- | --- | --- |
| `HANDLED`（成功续跑） | 2 | 自包含重建 / 来源依赖重建 |
| `REFUSED`（本入口点名拒绝） | 6 | 无来源 / 无冻结 digest / 来源不可解析 / preflight 不过 / 语义漂移 / 服务未装配 |
| `NOT_THIS_ENTRY`（不归本入口管） | 5 | 租约过期 / 死信 / 已成功不重跑 / 重启后自动派发 / run 级自动继续 |

**第 6 条 `NOT_THIS_ENTRY`（装配面差异）走 `reason` 面**，理由非空且够长（≥30 字符），
由 `test_entries_with_a_reason_instead_of_evidence_say_something_substantive` 钉住。

### 判据自身抓到的第一次错（**幽灵引用**）

建档首版我凭印象写了 7 个用例名（例如
`test_a_run_with_a_frozen_body_rebuilds_without_touching_sources`），全都不存在
（真实名是 `test_a_rebuild_from_the_frozen_body_finishes_the_remaining_work` 等）
⇒ `test_every_declared_evidence_really_exists` **一次全抓出**。这条是本 PLAN 的
最有价值读数：**声明集的受判面不是空的**。

### 第二次错（判据形态）：按散文猜关键词

首版「与源码对账」用中文关键词去匹配英文口径（找 `服务` / `preflight`）——
那是拿**措辞**当**绑定**：换一个词的写法就会误判。改成 `source_literals` 字段后，
绑定是显式的（漏认领 / 重复认领 / 绑定字面量不存在各判红）。

### 按压（单变量，各独立）

```
BASELINE_GREEN 6 passed in 0.09s
P1_RED exit=1 1 failed, 5 passed in 0.18s
P2_RED exit=1 3 failed, 3 passed in 0.19s
RESTORED True resume_coverage_declaration.py 6f40eef99d10->6f40eef99d10
FINAL_MATCHES_BASELINE True 6 passed in 0.08s
```

- **P1**（幽灵条目）⇒ `1 failed`（存在性判据）。
- **P2**（删一条）⇒ `3 failed`（规模下界 + 三面下界 + 字面量归属）。
- **P3（按压脚本自己的错，已修）**：首版 P2 用字符串切片删条目，被条目内多行
  `reason=(...)` 的 `),` 骗到 ⇒ 产出**语法错** ⇒ `exit=2`（收集错）。
  **那读数不能用**（它不是「规模下界判红」）。改为 **AST 定位**后 `exit=1 3 failed`。

## 影响报告

- **Domain / API / schema 变化**：**无**。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：无。
- **观测隐私**：无新增出口（两个新文件都在 `tests/`）。
- **上游版本影响**：无。
- **下一项任务**：cycle 4 = EC-04（自举收口）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | DONE | cycle 3 落地：声明集 14 条（2/6/5）+ 与源码按字段对账 + 幽灵引用自查（首版 7 个假用例名全被抓出）+ 两向按压判红。既有判据一字未动。`latest_recheck` = `RECHECK-20261008-316`。 |
