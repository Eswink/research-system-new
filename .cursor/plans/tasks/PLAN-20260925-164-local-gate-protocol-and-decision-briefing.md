---
id: PLAN-20260925-164
slug: local-gate-protocol-and-decision-briefing
title: 本地判定确定性：跑法协议 + 机械三分类 + 代管脚本 + 决策简报（GOAL-015 EC-02 / EC-03）
status: DONE
created_at: 2026-09-25
updated_at: 2026-09-25
parent_goal: GOAL-20260925-015
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260925-015 的 **2026-09-25 用户授权（goal 模式）**：授权**修测试隔离与本地判定
    确定性**，且**不改判据强度、不放宽门禁**。**明确禁止**：为消灭本地红而放宽任何判据 / 门禁 /
    放行面（含 `tests/egress_guard.py` 的目的地判定、`framework/validate_bundle` 的检查项、
    m0 任一 check 的阈值）；改 `tests/application/test_m2_audit.py` 的镜像一致性判据；
    skip / xfail / 删除测试 / 调整收集顺序掩盖顺序失败；豁免 fake-IP（`198.18.0.0/15`）或任何
    目的地址类别。**若根因判定为门禁自身 scoping 有误 ⇒ 不在本循环改门禁**，改产出决策简报
    条目（EC-03）。push-to-main-for-CI（只推 main、不 force、不重写历史、不推旁支）；
    默认 runtime 保持 Fake、默认 CI 离线；**本 PLAN 零真实出网调用**。
    **本 PLAN 的三处改动都在「真实共享来源 / 装置」上**：① postgres 与 distributed 标记的
    **跳过守卫**写在子目录 conftest 里 ⇒ 定向跑（不收集该目录）既不跳过也不快失败而是**挂死**
    —— 修法是把它提为**加载无关**（根级 collection hook + 共享模块），**判据一字不动**；
    ② 默认门凭据隔离的**判据本体**在模块导入期注入凭据键「制造泄漏」，结果泄漏给整个 pytest
    会话（CI 实测：live 用例不再 skip、真去调端点 ⇒ `AuthenticationError` 判红默认门）
    —— 修法是**把注入限定在子进程内**，并加一个**会被常规收集**的探针用例；
    ③ 本地红的**分类与代管**从「每轮现场归因」变成**脚本化**（协议文档 + 只读归因脚本 +
    逐字节代管脚本）。**EC-03 的产出是文档（零实施）**：把散在各 GOAL 的待拍板项收成一份
    六要素简报，并由机械判据与 GOAL 人工面**双向对齐**。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260925-165-local-gate-protocol-and-decision-briefing.md
memory_entries:
  - .cursor/memory/entries/MEM-20260925-132-skip-guards-must-be-load-independent.md
  - .cursor/memory/entries/MEM-20260925-133-judge-injection-must-be-subprocess-scoped.md
---

# PLAN-20260925-164 — 本地判定确定性 + 决策简报（GOAL-015 EC-02 / EC-03）

## 目标

让**每一次本地红**都能**机械**落进三类（真实缺陷 / 环境专属 / 门禁 scoping），并把
GOAL-013 那次「临时移出 → 跑 → 移回」的动作**脚本化、可复跑、可逐字节复核**；
同时把散在各 GOAL 的待拍板项收成一份**可拍板**的简报（**零实施**）。

## 验收条件

- **AC-1｜跑法协议落盘**（EC-02）：`docs/architecture/LOCAL_GATE_PROTOCOL.md` 给出 canonical 的
  m0 调用方式（DSN 固化、独占运行、`--keep-going`、终态行判据）、**支持的跑法**与
  **不支持的跑法**（含 `CURSOR_FRAMEWORK_ROOT` 用于全量跑）、三分类的**判定条件**与
  **可复跑归因命令**、以及两条具名起点的终态。
- **AC-2｜机械三分类**（EC-02）：`tools/classify_local_gate_reds.py` 只读日志、不 import 仓库
  代码、零出网；对 `FAILED [<check>]` 逐项给出类别 + 归因命令；**表外红打印 `UNCLASSIFIED`
  并非零退出**（不得读成「已忽略」）。
- **AC-3｜代管脚本**（EC-02）：`tools/quarantine_and_run_m0.py` 把**未跟踪**的仓库外文件移出
  （**拒绝**跟踪文件）→ 跑 m0 → **`finally` 还原** → 逐字节复核（`sha256` / `size` / `mtime_ns`），
  并打印「本终态行取自**代管后的树**」。
- **AC-4｜R-4 修复（加载无关的跳过守卫）**：`postgres` / `distributed` 标记的跳过**不再依赖
  「谁被收集」**；PG 不可达时定向跑**跳过而不是挂死**，且 `RESEARCHOS_REQUIRE_POSTGRES=1` 时
  **fail-closed**（硬失败并点名不可达）。
- **AC-5｜CI 红的真实根因修复**：默认门凭据隔离判据**不得**污染自身会话的进程环境；注入只允许
  发生在**子进程**内；探针用例在**有环境凭据时仍绿**、在 `--noconftest` 下**判红**（按压）。
- **AC-6｜决策简报齐备且双向对齐**（EC-03）：简报条目 ≥ 9、每条**六要素非空**；与 GOAL-015
  「不进入循环 / 需人工拍板」节**双向对齐**（GOAL 每条编号项在简报里有行；简报每条被引用），
  由 `tests/tooling/test_pending_decisions_briefing.py` 强制，且**删一项 / 空一格 / 删一行**三种
  变体**各自判红**。
- **AC-7｜判据只增不减**：零删除用例、零断言削弱；`tests/egress_guard.py`、
  `framework/validate_bundle` 的检查项、m0 任何阈值**逐字节未改**（`git diff` 证明）；
  EC-03 若触及门禁 scoping，**只登记不改**。

## 实施清单

- [x] **WP1 — 跑法协议（EC-02）**：`docs/architecture/LOCAL_GATE_PROTOCOL.md`
      （canonical 调用 / DSN 固化 / 独占运行 / 支持与不支持的跑法 / 三分类判定 / 归因命令 /
      代管配方与三条纪律 / 两条具名起点的终态）。
- [x] **WP2 — 只读归因脚本（EC-02）**：`tools/classify_local_gate_reds.py`
      （`BY_CHECK` + `python/tests` 内的 `SUB_SIGNATURES`；表外红 `UNCLASSIFIED` + exit 3）。
- [x] **WP3 — 逐字节代管脚本（EC-02）**：`tools/quarantine_and_run_m0.py`
      （拒绝跟踪文件 / 写者静置窗口 / `finally` 还原 / `sha256`·`size`·`mtime_ns` 复核 / exit 4）。
- [x] **WP4 — R-4 修复（EC-02）**：`tests/postgres_guard.py`（共享模块：`postgres_dsn` /
      `postgres_available` / `apply_reachability_skips` / `RESEARCHOS_REQUIRE_POSTGRES` fail-closed）
      + `tests/conftest.py` 的根级 `pytest_collection_modifyitems` 第一步调用它 +
      `tests/postgres/conftest.py` 与 `tests/distributed/conftest.py` 去掉各自向的收集钩子 +
      4 处 `_postgres_dsn` 调用点改为共享模块 + 新判据
      `tests/architecture/python/test_postgres_skip_is_load_independent.py`（跳过方向与
      fail-closed 方向各一条，子进程、不可达 DSN = `127.0.0.1:1`）。
- [x] **WP5 — CI 红的真实根因修复（AC-5）**：把
      `tests/architecture/python/test_default_gate_credential_isolation.py` 的注入从
      **模块导入期**改为**子进程内**；新增会被常规收集的探针
      `tests/architecture/python/test_default_gate_isolation_probe.py`（`--noconftest` 即红）。
- [x] **WP6 — 决策简报（EC-03）**：`docs/roadmap/OPEN_DECISIONS_BRIEFING.md`（12 条决策项
      D-01…D-12，每条六要素 + 与 GOAL 人工面的对齐表）+ 机械对齐判据
      `tests/tooling/test_pending_decisions_briefing.py`（3 种变体按压）。
- [x] **WP7 — 记录**：本 PLAN + `RECHECK-20260925-165` + `MEM-20260925-132` / `MEM-20260925-133`
      + GOAL-015 回写（EC-02 / EC-03 状态、迭代日志、`child_plans` / `memory_entries`、
      CI 台账）。

## 证据（本地）

- **R-4 判据**：`tests/architecture/python/test_postgres_skip_is_load_independent.py` ⇒
  `2 passed`（不可达 DSN 下定向跑**跳过**且 exit 0；`RESEARCHOS_REQUIRE_POSTGRES=1` 下
  **非零退出**且判词点名 `not reachable` / `fail-closed`）。
- **集中化后定向套件**：`tests/postgres` + `tests/distributed` + 4 个 `postgres` 标记的 API 用例
  ⇒ `143 passed`（改前有 4 个模块 import 失败：它们从 conftest 借 `_postgres_dsn`）。
- **CI 红的按压**：`LLM_MAIN_KEY=<任意值> pytest --noconftest
  tests/architecture/python/test_default_gate_isolation_probe.py -q` ⇒ **1 failed**；
  带根 conftest ⇒ **1 passed**（`blocked 0`）。
- **命名门**：`default_gate_isolation_probe.py` 首版**不以 `test_` 开头**、又放在 `tests/` 下
  ⇒ `tests/architecture/test_module_file_naming.py` 判红（m0 全量轮实测）；改名为
  `test_default_gate_isolation_probe.py` 后该门 + 两条隔离判据合计 `33 passed`。
  **不加豁免名单**（加豁免即「改门禁使其通过」）。
- **EC-03 判据**：`tests/tooling/test_pending_decisions_briefing.py` ⇒ `5 passed`（含三种变体按压）。
- **分类脚本实跑**：对 cycle 1 的 as-is m0 日志 ⇒ `framework/validate_bundle ⇒ (iii) 门禁
  scoping`，exit 0。
- **m0 终态**：见本 PLAN 的收口回写与 `RECHECK-20260925-165`。

## 残余（本 PLAN 不处置）

- `R-3`（`framework/validate_bundle` 扫描 gitignored 工作区）⇒ **(iii)**，**只登记**为决策简报
  **D-10**；**不改门禁**。
- live 判据的开门条件（环境里恰好有凭据即真出网）⇒ **只登记**为决策简报 **D-11**；**不改判据**。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-25 | IN_PROGRESS | WP1–WP6 实施（协议 / 两脚本 / R-4 / CI 红修复 / 简报与判据） |
| 2026-09-25 | DONE | WP7 记录落盘；m0 终态见 `RECHECK-20260925-165`；本 PLAN 的每条 AC 均有实跑证据 |

## 影响报告

- **Domain / API / schema**：无变化（未触碰 `packages/domain`、`services/api`、migration）。
- **安全 / 凭据**：无新增凭据面；未记录任何凭据值；`.env` 不删不改。
  **本 PLAN 收紧**了默认测试门（未标记 live 的用例不得看见出厂目录声明的凭据键），
  这是**隔离面**收紧，不是放行面变化。
- **兼容性 / 迁移风险**：`tests/postgres_guard.py` 成为共享模块，四个测试模块的 import 改向；
  `tests/postgres/conftest.py` 与 `tests/distributed/conftest.py` 不再承担收集期跳过。
  产品代码、路由、DTO、OpenAPI 快照、web 类型均未动。
- **上游版本影响**：无（未改依赖 / pin；两个脚本只用标准库）。
- **下一项任务**：GOAL-015 EC-04（收口复检 + 残余登记 + CI 台账到终态）。
