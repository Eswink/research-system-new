---
id: PLAN-20260923-147
slug: experiments-read-face-in-browser
title: 实验读面在浏览器里用真实数据渲染产物与指标（GOAL-012 EC-05，可选）
status: DONE
created_at: 2026-09-23
updated_at: 2026-09-23
parent_goal: GOAL-20260923-012
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260923-012 建档授权（2026-09-23 用户 goal 模式指令）的 EC-05：
    **前端消费实验读面**（`GET /runs/{id}/experiments` 的产物/指标在页面上用**真实数据**渲染）。
    EC-05 明文**可选**：空间不足则**如实登记为下一轮输入**，**不得**为它降级 EC-01…EC-04。
    本 PLAN 的改动面严格限于：`tests/api/console_api_app.py` 的**只服务 live e2e 的受控夹具**、
    `apps/web/tests/e2e/` 的新 live spec 与 suite 清单、以及 `scratch/` 的读面快照与截图
    （**不进仓库**）。**不改**产品 UI 代码、**不改** API/DTO、**不改**门禁、**不改** stub e2e 基线；
    零出网（浏览器只打本机 127.0.0.1 的 live app 与 vite dev）、零凭据读取、零真实 LLM 调用。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260923-148-experiments-read-face-in-browser.md
memory_entries:
  - .cursor/memory/entries/MEM-20260923-113-live-page-equals-read-face-judge.md
---

# PLAN-20260923-147 — 实验读面在浏览器里用真实数据渲染（GOAL-012 EC-05）

## 目标

让 EC-01…EC-03 打通的**实验读面**（`GET /runs/{id}/experiments`）在**浏览器里**用
**真实数据**渲染：实验页显示这次实验的**产物引用数、镜像指纹、指标字段**与详情抽屉里的
**指标原始投影**；判据形态是 **「页面 == 读面」**（先经 HTTP 取读面，再与 DOM 逐值比对），
并配一条**成对反证**（同一个组件、另一条**没有指标**的实验 ⇒ 页面照实显示空态，
证明页面不是在渲染前端常量）。

## 计划开始前的定案（写死）

- **D-1 形态**：**live e2e**（真实 HTTP + 真实浏览器），不是 stub 套件。理由：EC-05 要的是
  「真实数据下渲染」，而 stub 套件按定义喂的是替身响应。新增
  `apps/web/tests/e2e/live-experiments.spec.ts`，并在**单一来源**清单
  `apps/web/tests/e2e/live-specs.ts` 的 `LIVE_SUITES` 里加一项（该清单同时是 stub 配置的
  `testIgnore`：漏加会让 stub 套件收进一个必然失败的用例）。
- **D-2 数据来源 = **产品自己的写入路径**：受控 run 的实验记录**不手写 DTO JSON**，而是走
  `packages.application.experiments.register_experiment_evidence`（run 链调用的**同一个**
  准入函数）写 SourceRecord/Evidence/Claim+关系；指标由**内容寻址制品**的 JSON 承载
  （读面 `_metrics_for` 就这么取）。夹具只服务 live e2e，**不进入任何生产路径**。
- **D-3 诚实边界**（写进 spec 文件头与复检）：夹具的**执行**不是真容器跑出来的——真实容器
  全链在 pytest 层已有（`tests/e2e/test_ec02_experiment_chain_offline.py`、
  `test_ec03_experiment_evidence_chain.py`）。本 PLAN 判的是「**读面 → DTO → 页面**」
  这一段，**不**声称「页面上那次实验真的在容器里跑过」。
- **D-4 成对反证**：第二条受控 run 的实验**只有非 JSON 制品** ⇒ 读面的 `metrics` 为空
  ⇒ 页面显示「没有已记录指标」空态。两条实验走**同一页面、同一组件**，差别只在数据。
- **D-5 产物落 `scratch/`**：读面快照（`GET /runs/{id}/experiments` 的 JSON）+ 页面截图，
  由 spec 按环境变量 `EC05_SNAPSHOT_DIR` 写入（缺省 `scratch/goal012-c5/`）；**不进仓库、
  不上传外部服务**。

## 验收条件（逐条如实）

| # | 条件 | 判据（可复跑命令 + 期望值） | 结论 |
| --- | --- | --- | --- |
| AC-1 | 读面能用真实数据回答 | 夹具 run 的 `GET /runs/{id}/experiments` 返回**恰 1 次实验**，含 `artifact_ids`（2 件）、`image_digest`、`environment_digest`、`metrics`（2 个字段） | **通过**：读面快照 `scratch/goal012-c5/read-face.json`（实测 `artifact_ids` 2 件、`metrics` = `corpus_size` 2048 / `worst_case_comparisons` 19960） |
| AC-2 | 页面渲染的就是读面的值 | live spec 先 HTTP 取读面，再断言表格「制品引用」「指标字段」「镜像指纹」与抽屉里的**指标原始投影** == 读面值 | **通过**：主干用例 **passed**（断言全部按读面值比对；`scratch/goal012-c5/page-values.json` 存下页面侧的取值） |
| AC-3 | 成对反证 | 第二条 run（无指标制品）在同一页面照实显示空态；两条 run 的读面本身就不同 | **通过**：反证用例 **passed**（先断言读面 `metrics` 为空 + 恰 1 件制品，再断言页面没有指标 `<pre>` 且显示空态） |
| AC-4 | 快照落 `scratch/` | `scratch/goal012-c5/` 下有读面 JSON + 截图（**不在 git 里**） | **通过**：`read-face.json` / `read-face-bare.json` / `page-values.json` / 两张 PNG；`git status` 无这些文件（`scratch/` 在 `.gitignore`） |
| AC-5 | web 门与既有套件不回归 | `m0` **23/23**（含 `typescript/web-{lint,test,typecheck,build}`）+ **stub 套件**（`playwright.config.ts`）仍绿：新 live spec 被 `testIgnore` 排除 | **通过**：m0 **`PASS: profile=m0; 23 deterministic checks`**（`python/tests` 4411 passed / 19 skipped）；stub 套件 **96 passed** |
| AC-6 | 零出网/零凭据 | spec 只打 `127.0.0.1`；`judged N; blocked M` 里无真实目的地；未读凭据 | **通过**：m0 出站 `judged 788; blocked 8`（8 条全是故意探针 `tests/architecture/python/test_default_egress_guard.py`）；live app 与 vite 都绑 `127.0.0.1`；零凭据读取 |

## 实施清单

- [x] **WP1** 夹具：`tests/api/console_api_app.py` 增 `_with_experiment_catalog`（两条受控 run + 走产品准入路径的实验记录 + 内容寻址制品）。
- [x] **WP2** 判据：`apps/web/tests/e2e/live-experiments.spec.ts`（主干 + 成对反证 + 快照/截图）。
- [x] **WP3** 投影：`live-specs.ts` 加 suite 项；本 PLAN + `ALL_PLAN` 行 + GOAL `child_plans`（同一提交）。
- [x] **WP4** 门与收口：live e2e 实跑（2 passed）+ stub 套件（96 passed）+ `m0` 23/23 +
  `RECHECK-20260923-148`（PASS）+ GOAL 回写（EC-05 状态、迭代日志第 5 行、状态历史、`memory_entries`）。

## 证据

| # | 事实 | 取数方式 |
| --- | --- | --- |
| E-1 | 读面由 canonical 证据行聚合 | `services/api/routers/experiments.py::_experiments_of_run`（claim → relation → evidence，`experiment_run_id`/`artifact_id`/两个 digest） |
| E-2 | 指标从制品内容取 | 同文件 `_metrics_for`（内容寻址读 JSON 的 `metrics` 键） |
| E-3 | 准入路径是产品的一条 | `packages/application/experiments/evidence_admission.py::register_experiment_evidence`（run 链同一函数） |
| E-4 | 页面组件 | `apps/web/src/features/experiments/{ExperimentsPage,ExperimentMetadata}.tsx`（本 PLAN **不改**它） |
| E-5 | 本 PLAN 的实跑产物 | live e2e **2 passed**（`scratch/goal012-c5-live-green.txt`）；两处按压红（`scratch/goal012-c5-press{1,2}.txt`）；两棵树复检 `scratch/verify_goal012_c5.py`（当前树 32/32、基线树 `2e5b218` 15 红）；m0 `scratch/goal012-c5-m0-rerun.log`；快照 `scratch/goal012-c5/` |

## 影响报告

- **Domain / API / schema**：无（只加测试夹具与 e2e 用例）。
- **前端产品代码**：**零改动**（渲染面已存在；本 PLAN 判它）。
- **测试**：新增 1 个 live spec + 1 个受控夹具函数；stub 套件与 pytest 计数不变。
- **CI / workflow**：不改（`console-frontend` 作业跑 stub 套件；live 套件按既有口径本机跑）。
- **安全 / 凭据**：浏览器只访问 `127.0.0.1`；无凭据、无真实 LLM、无出网。
- **下一项任务**：EC-06（收口重检）。

## 状态历史

- 2026-09-23：derive（EC-05 子计划）。定案 D-1…D-5 写死。

## 收口（cycle 5）

- **复检**：`RECHECK-20260923-148` = **PASS**（live 实跑 + 两处按压 + 两棵树成对 + 门）。
- **状态**：`DONE`；`latest_recheck` 指向该复检（仓库相对路径）。
- **工程记忆**：`MEM-20260923-113`（「页面 == 读面」的判据形态；按压要按页面那一段）。
- **零产品面改动**：前端页面/组件/DTO 类型/导航/API 路由/DTO/egress 判据两棵树同指纹；
  本 PLAN 只加受控夹具、live spec 与 suite 登记。零出网、零凭据读取。
