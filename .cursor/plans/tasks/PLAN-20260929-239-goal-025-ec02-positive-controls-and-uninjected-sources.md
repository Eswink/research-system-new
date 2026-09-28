---
id: PLAN-20260929-239
slug: goal-025-ec02-positive-controls-and-uninjected-sources
title: GOAL-025 cycle 2（EC-02）：正控制矩阵与未注入面的判定化 —— 6 条载体建正控制 + 3 条取不到路由的机械事实 + 4 个源的结构化陈述
status: DONE
created_at: 2026-09-29
updated_at: 2026-09-29
parent_goal: GOAL-20260929-025
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260929-025 的 **EC-02**（收 GOAL-024 的残余 `G24-6` 与 `G24-1` 的离线可判定部分）。
    授权沿用该 GOAL 的 `authorization.ref`：范围 = 「**新增判据**（一律落 `tests/**`，落在既有
    `python/tests` 收集面内 ⇒ m0 条数仍 `23`）」+「**测试侧夹具 / 探针**」；push-to-main-for-CI
    口径（**只推 main、不 force**、不重写历史、不推旁支；push 前 `git pull --ff-only`）。
    **本 PLAN 专属边界**：**只新增**文件（`positive_control_support.py` +
    `test_privacy_positive_controls.py`），**不修改**任何既有判据 / 夹具 / 清单 / 门禁 / 阈值 /
    放行面（点名：`test_privacy_read_face_canary.py`、`read_face_route_registry.py`、
    `read_face_canary_support.py`、`content_canary_support.py`、`test_privacy_canary.py`、
    `test_privacy_exit_census.py`、`test_privacy_content_canary_end_to_end.py`、
    `test_privacy_boundary_clauses_are_pinned.py`、`test_privacy_read_face_headers.py`、
    三道记录面判据、多路证据判据、射程边界判据、`test_tooling_scripts_meet_product_gates.py`、
    `tests/egress_guard.py`）；**不动** `examples/protocols/` 的参考资产（被别的套件复用，
    改它们等于改夹具的失败形态 ⇒ 本题用**换入注入实例**代替）；**不改** `PRODUCT_ROOTS` /
    m0 条数 / 作业结构；**零**新依赖；**全离线**（无真实出网）；
    金丝雀一律**测试内构造的合成串**；**不得**把真实 prompt / token / 凭据写进任何地方；
    **不得**用 `skip` / `xfail` 处理取不到的路由；**不得**宣称项目安全（`R-M1` 未收口）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **6 条无正控制载体建正控制**：模板 ×2 / 记忆 / 交付物 / 库 ×2 各自**看到**它声明承载的
      内容（合成金丝雀），且**正控制面有下界**（不许把正控制改判成机械理由来收缩必做面）。
    status: PASS
  - id: AC-2
    criterion: >-
      **3 条取不到路由的判定化**：`/library/{resource_id}` 经产品写面建成**可取到**；
      2 条 workspace 快照路由把「为何取不到」断言成**机械事实**（离线装配
      `deps.workspace_snapshots is None` ⇒ 实测 503 守卫在位）—— **不 skip、不 xfail**。
    status: PASS
  - id: AC-3
    criterion: >-
      **4 个无注入面源的结构化陈述**：`task_input` / `tool_arguments` / `tool_output` /
      `failure_message` 各给出**机械断言**（结构 / 属性 / 枚举 / 行为），并把「需要真实
      runtime 才能取证」的那一半逐条登记为 **待真实 runtime 取证项 + 理由**（理由非空；
      GOAL 记录面把这一档称作不可判定登记）。
    status: PASS
  - id: AC-4
    criterion: >-
      **终态**：四道门全绿；既有判据**逐字节未改**且与本轮新判据合跑全绿；
      三处源码按压**先红后绿**且 raw `sha256` 逐字节复原；as-is 本机 m0 =
      `PASS: profile=m0; 23 deterministic checks`（**记录写入之后**）；治理 `validate.py` 绿；
      CI 台账到终态（八 job + CodeQL + `run_attempt`）。
    status: PASS
latest_recheck: .cursor/plans/rechecks/RECHECK-20260929-240-goal-025-ec02-positive-controls.md
memory_entries:
  - .cursor/memory/entries/MEM-20260929-164-positive-control-means-the-carrier-shows-its-content.md
---

# PLAN-20260929-239 — GOAL-025 cycle 2（EC-02）：正控制矩阵与未注入面的判定化

**动因**：GOAL-024 收口时如实登记了两件事：**6 条声明载体没有正控制**（清单只要求「取得到
响应」，**没有**要求「看得到它声明的内容」）、**3 条路由取不到**；以及 **4 个金丝雀源在默认
离线链上没有注入面**，而那四个源当时只有一句**散文**式「未验证」。本 PLAN 把这三件事
从「未验证」推进为**可判定陈述**。

## 验收条件

见 frontmatter `AC-1`…`AC-4`（全部 PASS，证据见下）。

## 实施清单

- [x] WP1：`tests/observability/positive_control_support.py`（**250 行**）—— 载体判定矩阵
      （正控制 6 / 机械理由 2）+ 源判定矩阵（4 条，各带机械证据与待取证理由）+
      富化读面现场（换入金丝雀模板目录、经**产品写面**落记忆与库条目、seed 交付物制品）。
- [x] WP2：`tests/observability/test_privacy_positive_controls.py`（**196 行 / 11 例**）——
      矩阵覆盖性（必做面**从 GOAL-024 登记推出**）、正控制下界、逐载体正控制、库条目路由
      变可取到、快照路由的 503 守卫**真跑**、四个源的机械断言、两向反证。
- [x] WP3：`RECHECK-20260929-240`（独立复检）。
- [x] WP4：记录（本 PLAN / GOAL 回写）+ 四道门 + as-is m0 + push + CI 台账终态。

## 证据

| 观测 | 数值 / 结论 |
| --- | --- |
| 新判据 | `test_privacy_positive_controls.py` **11 passed** |
| 正控制 | **6** 条载体逐条看到它声明承载的金丝雀（模板 ×2 / 记忆 / 交付物 / 库 ×2）；下界 `MIN_POSITIVE_CARRIERS = 6` |
| 取不到 → 可取到 | `/library/{resource_id}` 经 `POST /projects/{id}/library` 建成可取到（200 + 声明的正文） |
| 取不到 → 机械事实 | 2 条快照路由**真跑**：`deps.workspace_snapshots is None` ⇒ 实测 **503**（守卫在位），**无 skip / xfail** |
| 四个源 | `task_input` / `tool_arguments` / `tool_output` / `failure_message` 各 1 条机械断言 + 1 条待真实 runtime 取证的理由（非空） |
| 两向反证 | ①**不加**注入时 `/protocol-templates` 看不到金丝雀 ⇒ 正控制由本轮注入造成；②载体看不到声明内容 ⇒ 判红点名路由与 kind |
| 按压（源码级，先红后绿） | Q1 抽空一条机械理由 ⇒ `这些行没有理由:[…]`；Q2 下界 6→7 ⇒ `正控制载体只有 6 条 < 下界 7`；Q3 把一条正控制降级成机械理由 ⇒ `正控制载体只有 5 条 < 下界 6` |
| 逐字节复原（raw `sha256`） | 三处按压后均回到 `d9f85f1cb79dfc0b1fbe10985be26e8d77ce84a29257b2c8612611d9e24f2faf`（`MATCHES_BASELINE True`），复绿 11 passed；证据 `scratch/goal025-ec02-press-matrix.log`（**二进制写盘**） |
| 四道门 | `ruff format --check` = `2 files already formatted`；`ruff check` = `All checks passed!`；`mypy` = `Success: no issues found in 2 source files`；规模 **250 / 196 行**（规模门定向跑 **2 passed**） |
| 既有判据未改 | `tests/observability/` 全目录 **124 passed, 1 skipped**（GOAL-024 cycle 4 收口时 100 + 1；本轮 cycle 1 后 113 + 1 ⇒ **+11** 恰为本轮新判据） |
| m0 / 治理 / CI | 见 GOAL 迭代日志与 CI 台账（**记录写入之后**才跑；终态行 `PASS: profile=m0; 23 deterministic checks`） |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-29 | IN_PROGRESS | 建档（GOAL-025 cycle 2，EC-02）。 |
| 2026-09-29 | DONE | 两个新文件进树（11 例全绿）、四道门绿、三处源码按压先红后绿且 raw `sha256` 逐字节复原、RECHECK-240 `PASS_WITH_WARNINGS`。 |

## 影响报告

- **Domain/API/schema**：无（`tests/**` + 记录）。
- **安全/凭据**：无凭据改动；新判据全离线、金丝雀为测试内合成串；未动 `examples/protocols/` 参考资产。
- **兼容性/迁移风险**：无（纯新增文件；既有判据逐字节未改，m0 条数仍 `23`）。
- **上游版本影响**：无（零依赖改动）。
- **下一项任务**：GOAL-025 cycle 3（EC-03：读面白名单的契约派生与差异清单）。
