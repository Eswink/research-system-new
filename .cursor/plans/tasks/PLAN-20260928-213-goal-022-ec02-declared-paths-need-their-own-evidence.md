---
id: PLAN-20260928-213
slug: goal-022-ec02-declared-paths-need-their-own-evidence
title: GOAL-022 cycle 2（EC-02）：多路证据判据（绑结构化字段；只跑一路 ⇒ 判红；含实时按压与逐字节复原）
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
    承 GOAL-20260928-022 的 **EC-02**（多路证据判据，把 GOAL-021 的 `W-0` 机械化）。
    授权沿用该 GOAL 的 `authorization.ref`：范围严格限定为「**复检过程机械化 + 判据固化 +
    环境口径固化**」三件事 + 文档同源；**不加新能力、不放宽任何判据、不改安全策略**；
    push-to-main-for-CI 口径（**只推 main、不 force、不重写历史、不推旁支**）；
    默认 runtime 保持 **Fake**、默认 CI **离线**。
    **本 PLAN 专属边界**：**不得**放宽任何既有判据 / 门禁 / 阈值 / 放行面；
    **不得**新增依赖；**不得**把 token 写进任何地方；**不得**宣称项目安全（`R-M1` 未收口）；
    **不得**回填历史记录（历史 RECHECK 是不可变证据 —— 只登记剩余面，不改写）。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260928-214-goal-022-ec02-declared-paths-need-their-own-evidence.md
memory_entries:
  - .cursor/memory/entries/MEM-20260928-155-pressing-a-record-face-judge-means-injecting-a-record.md
---

# PLAN-20260928-213 — GOAL-022 cycle 2（EC-02）：多路证据判据

**主题**：把 `RECHECK-20260927-210` 的 `W-0`（条款写明两路、首轮只跑一路却记 PASS）从
「一条教训」变成**可判红的结构化义务**。

## 验收条件

| # | 条件 | 判据 |
| --- | --- | --- |
| AC-1 | 新判据在树、落在既有 check 的收集面内 | `tests/architecture/python/test_declared_recheck_paths_have_evidence.py`；**9 passed**；m0 条数仍 23 |
| AC-2 | 绑**结构化字段**而非散文（承 MEM-141） | `::test_the_judgement_ignores_prose_wording`：字段齐全而措辞不提「两树」⇒ 通过；只在散文里声称两路而字段只一条 ⇒ **判红** |
| AC-3 | **实时按压**：往被扫描目录注入违规记录 ⇒ 判红 | 注入「两路共用同一证据」的临时 RECHECK ⇒ `test_no_obligated_closeout_recheck_has_a_declaration_gap` **1 failed** |
| AC-4 | 补齐互不相同的证据 ⇒ 复绿；**逐字节复原** | 改注入记录为两条独立证据且正文各自引用 ⇒ **9 passed**；删除注入记录 ⇒ 文件数回到 **184**、残留 **0**、`git status --short .cursor/plans/rechecks/` 空 ⇒ 既有记录**零改动** |
| AC-5 | **判据自身非空洞**（按压判据逻辑） | `declared_path_problems` 首行插 `return []` ⇒ **5 failed, 4 passed**；恢复后 raw `sha256` 一致 ⇒ **9 passed** |
| AC-6 | **剩余面逐条登记**（不回填历史） | `::test_historical_closeout_rechecks_remain_out_of_scope` + `::test_the_rechecks_directory_is_actually_scanned`（非空断言，防「空集合假绿」） |
| AC-7 | 只跑一路 ⇒ 判红（把 `W-0` 机械化） | 收口复检须声明 **≥ 2** 路（由规范页「收口复检必须两树」条款推出）；`::test_a_single_declared_path_is_rejected` |

## 实施清单

- [x] **WP1 判据文件**：`verify_paths` 结构化义务（≥2 路 / 各自具名 / 证据互不相同 /
      必须在正文被引用 / 仓库内路径须存在・`scratch/` 归档落点豁免）。
- [x] **WP2 实时按压**：注入违规记录 ⇒ 判红 ⇒ 补齐 ⇒ 复绿 ⇒ 删除 ⇒ 复原（报**实际判红集合**）。
- [x] **WP3 判据自身按压**：中性化谓词 ⇒ 5 条断言判红 ⇒ 逐字节复原。
- [x] **WP4 记录**：本 PLAN + `RECHECK-20260928-214` + `MEM-20260928-155` + GOAL 回写 + ALL_PLAN 投影。

## 证据

| 面 | 观察 | 结果 |
| --- | --- | --- |
| 交付 | 判据文件 | 在位；`ruff format --check` clean、`ruff check` passed；raw `sha256` = `d83550137032ac31c2d248674d5268113ee4012d82efb79fe5244bc8044e47c0` |
| 判据 | 定向套件 | **9 passed** |
| 按压 | 实时注入（共用证据） | **1 failed**（`test_no_obligated_closeout_recheck_has_a_declaration_gap`） |
| 按压 | 补齐独立证据 | **9 passed** |
| 按压 | 删除注入记录（复原） | 文件数 **185 → 184**（184 为注入前基线）；残留 **0**；既有记录 `git status` **空** |
| 按压 | 中性化谓词 | **5 failed, 4 passed**；复原后 `sha256` 一致 ⇒ **9 passed** |
| 非空 | 扫描面产出 | 收口复检记录**非空**（防空断言）；历史集合与受判集合**互不重叠** |
| 射程 | 历史剩余面 | `created_at < 2026-09-28` 的历史收口复检**不在**受判集合内（**不回填**，如实登记） |
| 受保护判据 | 零改动 | 六个受保护判据文件自 `2f87812` 起 UNCHANGED |
| 全量门 | 一次通过 | **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` = 24、**4635 passed / 21 skipped**、零 `FAILED` / `ERROR`；日志 `scratch/goal022-c2-m0.log`）⇒ 本轮**未**命中 `WinError 5` flake（本轮 1/1） |
| 产品代码 | 零改动 | 无 `apps/` `services/` `packages/` `adapters/` 改动；**零**依赖改动 |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-28 | IN_PROGRESS | derive（GOAL-022 cycle 2）。判据落地；实时按压与判据自身按压均通过。 |
| 2026-09-28 | DONE | WP1–WP4 完成；`RECHECK-20260928-214` = `PASS_WITH_WARNINGS`。 |

## 影响报告

- **改动面**：新增 1 个判据文件（+ 记录）。**零**产品代码改动、**零**既有判据改动、**零**依赖改动。
- **Domain / API / schema**：无变化（不触 DTO / OpenAPI / 设计基线）。
- **安全 / 凭据**：无凭据面改动；判据不含 token 值。
- **兼容性 / 迁移风险**：**新增义务**只作用于 `created_at >= 2026-09-28` 的收口复检
  （历史记录不回填 ⇒ 无迁移）。将来一条收口复检若未声明 `verify_paths`，会在
  `python/tests` 里判红 —— 这是**预期行为**（义务从这一天起生效）。
  该「起点截断」本身是**射程边界**，已在判据与复检里逐条登记，**不得**读成「全仓已覆盖」。
- **上游版本影响**：无。
- **下一项任务**：GOAL-022 cycle 3 = **EC-03**（规范六条各自的判据计数 + `docs/INDEX.md` 登记 + 钉条款判据）。
