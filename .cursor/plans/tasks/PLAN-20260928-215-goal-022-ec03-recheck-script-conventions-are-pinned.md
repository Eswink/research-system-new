---
id: PLAN-20260928-215
slug: goal-022-ec03-recheck-script-conventions-are-pinned
title: GOAL-022 cycle 3（EC-03）：复检脚本规范 —— 六条口径各自可检查、≥3 条有机械判据、INDEX 登记、条款不得悬空
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
    承 GOAL-20260928-022 的 **EC-03**（复检脚本编写规范：文档 + 判据 + `docs/INDEX.md` 登记）。
    授权沿用该 GOAL 的 `authorization.ref`：范围严格限定为「**复检过程机械化 + 判据固化 +
    环境口径固化**」三件事 + **文档同源更新**；**不加新能力、不放宽任何判据、不改安全策略**；
    push-to-main-for-CI 口径（**只推 main、不 force、不重写历史、不推旁支**）；
    默认 runtime 保持 **Fake**、默认 CI **离线**。
    **本 PLAN 专属边界**：**不得**放宽任何既有判据 / 门禁 / 阈值 / 放行面；**不得**新增依赖；
    **不得**把 token 写进任何地方；**不得**宣称项目安全（`R-M1` 未收口）；
    **不得**改 `docs/architecture/LOCAL_GATE_PROTOCOL.md` 里被
    `test_record_face_is_covered_by_the_gate.py` 点名的那一节。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260928-216-goal-022-ec03-recheck-script-conventions-are-pinned.md
memory_entries: []
---

# PLAN-20260928-215 — GOAL-022 cycle 3（EC-03）：复检脚本规范

**主题**：把历史踩过的环境坑固化成**一页规范**，并让「**每条都附了判据或可复跑检查**」
成为**可复核的事实**（而不是一句自述）。

## 验收条件

| # | 条件 | 判据 |
| --- | --- | --- |
| AC-1 | 规范页在树 + `docs/INDEX.md` **登记** | `docs/architecture/RECHECK_SCRIPT_CONVENTIONS.md`；`::test_the_conventions_doc_is_in_the_tree_and_registered` |
| AC-2 | **六条口径逐条在位**（结构性锚点） | `::test_all_six_convention_items_are_present` |
| AC-3 | **≥ 3 条有机械判据**（计数断言） | 实测 **4/6** 条有判据（共用解释器 / 纯度 / 落点断言 / 路径无关输出）；`::test_at_least_half_of_the_items_have_a_mechanical_judge` |
| AC-4 | **条款不得悬空**：被点名的判据按 **AST 读声明**且必须存在 | `::test_every_named_judge_points_at_a_real_declaration`（**不用文本出现名字判** ⇒ 承 MEM-141） |
| AC-5 | 无判据的两条必须有**可复跑检查**小节 | `::test_items_without_a_judge_carry_a_reproducible_check` + `::test_every_item_is_covered_by_either_a_judge_or_a_check` |
| AC-6 | **按压**：抹掉一条规范小节标题 ⇒ 判红；逐字节复原 ⇒ 绿 | 改写 `### ⑤ 的可复跑检查` ⇒ **2 failed, 4 passed**；复原后 raw `sha256` 一致 ⇒ **6 passed** |
| AC-7 | 第 ③ 条的可复跑检查**在本机可复现**（不是照抄历史结论） | 实测临时文件 `byte-identical False`（Windows） |

## 实施清单

- [x] **WP1 规范页**（cycle 1 落地）：条款小节 + 六条口径 + 两条可复跑检查。
- [x] **WP2 INDEX 登记**：`docs/INDEX.md` 的 Architecture 节登记本页；
      同时**补登记**同族却遗漏的 `architecture/LOCAL_GATE_PROTOCOL.md`（**未改其内容**）。
- [x] **WP3 钉条款判据**：`tests/architecture/python/test_recheck_script_conventions_are_pinned.py`
      （条目标签 + 判据映射 + AST 声明检查 + INDEX 登记 + 可复跑检查小节）。
- [x] **WP4 按压与复原**：抹标题 ⇒ 判红；逐字节复原 ⇒ 绿。
- [x] **WP5 记录**：本 PLAN + `RECHECK-20260928-216` + GOAL 回写 + ALL_PLAN 投影。

## 证据

| 面 | 观察 | 结果 |
| --- | --- | --- |
| 交付 | 规范页 | 在位；raw `sha256` = `d80446dee9653aafa42646f2d08c9db9e182dd487e4eb1567b4ed0f6be5b73cc`（按压前后一致） |
| 交付 | 判据文件 | 在位，raw `sha256` = `d37381b4a4eac13c2f66da75c5108994520d3772e986cd3190f6bf4c49ed3888`；`ruff format --check` clean、`ruff check` passed |
| 判据 | 定向套件 | **6 passed** |
| 计数 | 有机械判据的口径 | **4 / 6**（下界 3）⇒ 满足「至少半数」 |
| INDEX | 登记 | 本页 + **补登记** `architecture/LOCAL_GATE_PROTOCOL.md`（同族遗漏；**未改该文档**） |
| 按压 | 抹掉 `### ⑤ 的可复跑检查` 标题 | **2 failed, 4 passed**（两条覆盖断言同时判红） |
| 按压 | 逐字节复原 | raw `sha256` 与按压前**一致** ⇒ 复跑 **6 passed** |
| 可复跑检查 | 第 ③ 条 | 临时文件实测 `byte-identical False`（Windows：`\n` → `\r\n`）⇒ 不是照抄历史结论 |
| 受保护判据 | 零改动 | 六个受保护判据文件自 `2f87812` 起 UNCHANGED |
| 全量门 | 一次通过 | **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` = 24、**4642 passed / 21 skipped**、零 `FAILED` / `ERROR`；日志 `scratch/goal022-c3-m0.log`）⇒ 本轮**未**命中 `WinError 5` flake（本轮 1/1） |
| 产品代码 | 零改动 | 无 `apps/` `services/` `packages/` `adapters/` 改动；**零**依赖改动 |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-28 | IN_PROGRESS | derive（GOAL-022 cycle 3）。规范页 + INDEX 登记 + 钉条款判据落地；按压与复原通过。 |
| 2026-09-28 | DONE | WP1–WP5 完成；`RECHECK-20260928-216` = `PASS_WITH_WARNINGS`。 |

## 影响报告

- **改动面**：新增 1 个判据文件；改 `docs/INDEX.md`（登记两页）；**零**产品代码改动、
  **零**既有判据改动、**零**依赖改动、**零** m0 check 增删。
- **Domain / API / schema**：无变化。
- **安全 / 凭据**：无凭据面改动；文档与判据均无凭据字面量。
- **兼容性 / 迁移风险**：新增判据会**钉住**规范页的小节标题与判据函数名 ——
  将来改这些名字会**判红**，这是**预期行为**（条款不得悬空）；改文案时需同步本判据的映射。
- **上游版本影响**：无。
- **无可复用事实**：本轮把 `MEM-20260925-141`（用语法结构判，不用文本巧合判）与
  `MEM-20260928-154`（引号豁免只认引号字符）的教训**用成判据**，**未产生新的可复用事实**；
  同 GOAL 的 EC-01 / EC-02 已各自沉淀 `MEM-20260928-154` / `MEM-20260928-155`。
- **下一项任务**：GOAL-022 cycle 4 = **EC-04**（**用 `tools/two_tree_recheck.py` 自举**本轮收口复检 ⇒
  两树同结论 + as-is m0 23/23 + 治理 + CI 台账 + 残余与未覆盖范围逐条）。
  **注意**：EC-04 的收口复检 `slug` 必须以 `closeout-recheck` 结尾且 `created_at >= 2026-09-28`
  ⇒ 它将是 **EC-02 判据的第一条真实受判记录**，**必须**声明 `verify_paths`（≥2 路：当前树 + 干净 checkout）。
