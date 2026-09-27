---
id: PLAN-20260928-211
slug: goal-022-ec01-two-tree-recheck-entry
title: GOAL-022 cycle 1（EC-01）：两树复检的机械化（可复用入口 + 三条环境口径 + SOP 条款 + 反证红）
status: DONE
created_at: 2026-09-28
updated_at: 2026-09-28
parent_goal: GOAL-20260928-022
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260928-022 的 **EC-01**（两树复检的机械化）。授权沿用该 GOAL 的
    `authorization.ref`：范围严格限定为「**复检过程机械化 + 判据固化 + 环境口径固化**」
    三件事 + 文档同源；**不加新能力、不放宽任何判据、不改安全策略**；
    push-to-main-for-CI 口径（**只推 main、不 force、不重写历史、不推旁支**）；
    默认 runtime 保持 **Fake**、默认 CI **离线**。
    **本 PLAN 专属边界**：**不得**放宽任何既有判据 / 门禁 / 阈值 / 放行面；
    **不得**新增依赖（入口只用标准库 + 既有 `git`）；**不得**把 token 写进任何地方；
    **不得**给读面加认证、**不得**引入多租户 / RBAC / BOLA·BFLA；
    **不得**宣称项目安全（`R-M1` 未收口）。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260928-212-goal-022-ec01-two-tree-recheck-entry.md
memory_entries:
  - .cursor/memory/entries/MEM-20260928-154-quote-exemption-takes-quote-characters-not-backticks.md
---

# PLAN-20260928-211 — GOAL-022 cycle 1（EC-01）：两树复检的机械化

**主题**：把 GOAL-020 / GOAL-021 两次**手工补跑**的「两树同结论」做成**可复用入口**——
一个入口对「当前树 + 干净 checkout」跑**同一组断言**、**逐行比对判词**、以退出码表达结论，
并把两次踩过的三个环境坑（解释器 / 输出纯度 / 路径无关）**写进工具本身**。

## 验收条件

| # | 条件 | 判据 |
| --- | --- | --- |
| AC-1 | 可复用入口在树，对两棵树跑**同一组断言**并**逐行比对判词**，含两份 `sha256` 与退出码 | `tools/two_tree_recheck.py` 在树；`tests/tooling/test_two_tree_recheck_entry.py::test_both_trees_agree_when_assertions_agree` **11 passed** |
| AC-2 | **反证必须真的会红**：第二树跑出不同结果 ⇒ 入口**非 0** 且**点名差异行** | `::test_second_tree_differing_makes_the_entry_red`；入口实测 `COMPARE identical=False` + `DIFF 第 1 行：…` + `EXIT=1` |
| AC-3 | **三条环境口径各有一条行为判据**：① 共用解释器 ② 输出纯度 ③ 路径无关 | `::test_both_trees_use_the_same_interpreter` / `::test_impure_output_is_refused_not_filtered` / `::test_path_dependent_verdict_is_refused_not_normalized` |
| AC-4 | **只跑一路不可能**：干净树拿不到时入口拒绝服务，**绝不**降级成单树 PASS | `::test_missing_clean_tree_never_degrades_to_single_tree_pass`（实测 `SETUP` + `EXIT=2`，无 `TWO-TREE PASS`） |
| AC-5 | **SOP 条款 + 判据钉住**（条款不得悬空） | `docs/architecture/RECHECK_SCRIPT_CONVENTIONS.md` 的 `## 收口复检必须两树` 小节；`::test_the_clause_section_names_live_files` |
| AC-6 | **两树实跑各留档**（判词文件 + `sha256`，逐行相同） | 真实干净 checkout 实跑 12 判词 ×2、`sha256` 相同 `7af577bb…`、落档 `scratch/goal022-ec01-verdict-{current,clean}.txt` |
| AC-7 | 判据**被按压过**（临时破坏 ⇒ 判红 ⇒ **逐字节复原**） | 按压：`compare_runs` 首行插入 `return True, []` ⇒ `1 failed, 10 passed`；复原后 raw `sha256` **相同**（`3c6262c0…`，**在终态字节上重做**）⇒ `11 passed` |
| AC-8 | 既有判据 **零改动**；未新增 m0 check（条数仍 23） | 六个受保护判据文件自 `2f87812` 起全部 UNCHANGED；新判据落 `tests/tooling/`（`python/tests` 收集面内）⇒ 本条由全量门实测确认 |
| AC-9 | **全量门 `python/format-check` 绿**（定向判据绿**不等于**全量门绿） | 首跑全量门**判红** `python/format-check=1`（两个新文件的探测串引号形态）⇒ **修**（`5e73211`）⇒ 复跑全量门到 `PASS: profile=m0; 23 deterministic checks`（**第 5 轮**才拿到终态行；其间 3 轮红为 `framework/run_cursor_framework_evals` 的 `WinError 5` 环境类 flake，已单独取证） |

## 实施清单

- [x] **WP1 入口**：新增 `tools/two_tree_recheck.py`（标准库 + 既有 `git`；两树共用本进程解释器；
      只收判词行；路径相关判词拒绝；超时按进程树杀；`git worktree` 用完即移除）。
- [x] **WP2 行为判据**：新增 `tests/tooling/test_two_tree_recheck_entry.py`（11 例；
      夹具探针在 `tmp_path` 运行时生成，不落仓库）。
- [x] **WP3 规范页 + 条款**：新增 `docs/architecture/RECHECK_SCRIPT_CONVENTIONS.md`，
      含 `## 收口复检必须两树` 小节（点名入口与判据文件）+ 六条环境口径（每条附判据或可复跑检查）。
- [x] **WP4 真实两树实跑**：以 `--base-ref HEAD` 建同 tip 干净 checkout ⇒ 12 判词 ×2 全 PASS、
      `sha256` 相同、落档逐字节相同、worktree 用完移除、零孤儿进程。
- [x] **WP5 按压矩阵**：破坏比对逻辑 ⇒ 判据判红；逐字节复原（raw `sha256`）⇒ 复绿。
- [x] **WP6 记录**：本 PLAN + `RECHECK-20260928-212` + `MEM-20260928-154` + GOAL 回写 + ALL_PLAN 投影。

## 证据

| 面 | 观察 | 结果 |
| --- | --- | --- |
| 交付 | `tools/two_tree_recheck.py` | 在位（**301 行**，纯 LF；`tools/` 不在 `PRODUCT_ROOTS` ⇒ 自愿遵守规模/风格约束）；raw `sha256` = `3c6262c0070b33f86dac51d10382e326df6202c07c8fdd509d6b107a13b1560e` |
| 交付 | `tests/tooling/test_two_tree_recheck_entry.py` | 在位，**11 passed** |
| 交付 | `docs/architecture/RECHECK_SCRIPT_CONVENTIONS.md` | 在位（含条款小节 + 六条口径） |
| 行为 | 两树同结论 | `TWO-TREE PASS`、`exit=0`、两份判词 `sha256` 相同 |
| 行为 | 第二树不同（反证） | `COMPARE identical=False` + `DIFF 第 1 行：…` + `TWO-TREE RED` + `exit=1` |
| 行为 | 输出不纯 | `SETUP 入口失败：输出不纯：出现非判词行 -> 'elapsed 0.0000s'` + `exit=2` |
| 行为 | 判词嵌路径 | `SETUP 入口失败：判词与路径相关（含 …）` + `exit=2` |
| 行为 | 干净树缺失 | `SETUP 入口失败：干净树不存在：…` + `exit=2`（**无** `TWO-TREE PASS`） |
| 行为 | 两树脚本字节不同 | `SETUP 入口失败：两树的复检脚本字节不同 ⇒ 比的不是同一组断言` |
| 行为 | 两树都不绿但判词相同 | `NOT-GREEN` 登记 + `exit=1`（「一致」不等于「成立」） |
| 真实两树 | 12 判词 ×2 | 全 `PASS`、`sha256` **相同** `7af577bbfb76f6bb53502f77a910bd966cb53c48976fc1d042a3ff1e6acc0843` |
| 真实两树 | 落档 | `scratch/goal022-ec01-verdict-current.txt` / `-clean.txt` **逐字节相同**（`cmp` IDENTICAL） |
| 进程卫生 | worktree / 孤儿 | worktree **已移除**；`tasklist` python 进程 **0** |
| 按压 | 破坏比对逻辑 | `1 failed, 10 passed`（红的是 `test_second_tree_differing_makes_the_entry_red`） |
| 按压 | 逐字节复原 | `3c6262c0070b33f86dac51d10382e326df6202c07c8fdd509d6b107a13b1560e`（前后一致，**在终态字节上重做**）⇒ 复跑 **11 passed** |
| 全量门 | 首跑抓到**真红** | `FAILED: 1 check(s): python/format-check=1`：`tests/tooling/test_two_tree_recheck_entry.py` 的探测串用 `'''`，`ruff format` 要求 `"""` ⇒ **定向判据绿 ≠ 全量门绿**（承 GOAL-021 的同一教训）；`tools/` 侧不在该 check 的扫面内，但**一并归一**以符合自愿纪律 ⇒ `5e73211` |
| 全量门 | 修复后复跑 | **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` = 24、**4625 passed / 21 skipped**、零 `FAILED` / `ERROR`；日志 `scratch/goal022-c1-m0-final3.log`） |
| 全量门 | 环境类 flake（如实登记） | 5 轮里 **3 轮**红在 `framework/run_cursor_framework_evals`，签名恒为 `PermissionError [WinError 5]` at `hooks/common.py:161` 的 `os.replace` ⇒ **环境类**。取证：**单跑 3/3 全 PASS**；**复现实验**（连跑「前一个 check + 该 check」3 轮 ⇒ 第 1 轮红、第 2/3 轮绿）⇒ 根因是**前序活动遗留的文件句柄**的竞态；**未改 check、未改阈值** |
| 口径可复跑检查 | 文本模式读写会改字节 | 临时文件实测 `byte-identical False`（Windows：`\n` 被写成 `\r\n`） |
| 受保护判据 | 零改动 | `test_control_plane_auth_same_source.py` / `test_reproducibility_wording.py` / `test_record_face_is_covered_by_the_gate.py` / `test_m2_audit.py` / `tests/egress_guard.py` 全部 UNCHANGED |
| 产品代码 | 零改动 | 本 cycle 未改任何 `apps/` `services/` `packages/` `adapters/` 代码 |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-28 | IN_PROGRESS | derive（GOAL-022 cycle 1）。入口 + 判据 + 规范页落地；按压与复原通过。 |
| 2026-09-28 | DONE | WP1–WP6 全部完成；`RECHECK-20260928-212` = `PASS_WITH_WARNINGS`。 |

## 影响报告

- **改动面**：新增 3 个文件（1 工具 + 1 判据 + 1 文档）+ 1 个格式化提交；**零**产品代码改动；
  **零**既有判据改动；**零**依赖改动；**零** m0 check 增删（仍 23）。
- **本轮被全量门抓到的真红（1 处，已修）**：`python/format-check` 判红
  （新判据文件的探测串引号形态不符合 `ruff format`）。**定向判据全绿**却仍被全量门判红
  ⇒ 再次实测「**定向套件绿 ≠ 全量门绿**」（该 check 只有全量门跑到，与 GOAL-021 cycle 1
  的 `python/typecheck` 是同一形态）。修复提交 `5e73211`（纯格式化，无语义变化）。
- **Domain / API / schema**：无变化（不触 DTO、OpenAPI、设计基线 ⇒ 无快照重生成）。
- **安全 / 凭据**：无凭据面改动；判据不含 token 值；文档与判据均未引入凭据字面量。
- **兼容性 / 迁移风险**：入口是新工具，无消费者迁移；`docs/architecture/` 新增一页，
  不在既有判据的扫描约束内（仍在 `docs/` 的面内，故话术判据适用且已过）。
- **上游版本影响**：无（零依赖改动）。
- **下一项任务**：GOAL-022 cycle 2 = **EC-02**（多路证据判据：绑 `slug` / `created_at` /
  `verify_paths` 结构化字段，含按压与逐字节复原）。
