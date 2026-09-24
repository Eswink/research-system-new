---
id: PLAN-20260925-161
slug: cross-suite-isolation-census-and-fix
title: 跨套件隔离归零：红项普查 + 两处真实共享来源修复（草稿列表序 tie / 默认门凭据泄漏）（GOAL-015 EC-01）
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
    条目（GOAL-015 EC-03）。push-to-main-for-CI（只推 main、不 force、不重写历史、不推旁支）；
    默认 runtime 保持 Fake、默认 CI 离线；**本 PLAN 零真实出网调用**（真实端点判据不属于本目标）。
    **本 PLAN 的两处改动都在「真实共享来源」上**：① 三个 `ProtocolDraftStore` 实现里
    `list()` 的**排序不是全序**（`created_at` 相同时按 `draft_id` 升序，与「按新近」语义相反）
    —— 修法是让 tie-break 与新近一致（**不改任何断言**）；② 测试进程里 `litellm` 导入期
    `load_dotenv()` 把本机 gitignored `.env` 的**凭据键**注入进程环境，使**未标记 live 的**
    「未配置控制面」用例从诚实失败变成**真的去探端点** ⇒ 出站结构判据按设计判红整轮
    —— 修法是**夹具隔离**（默认门不得看见 live 凭据），**判据一字不动**。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260925-163-cross-suite-isolation-census-and-fix.md
memory_entries:
  - .cursor/memory/entries/MEM-20260925-130-order-red-needs-a-frozen-input.md
  - .cursor/memory/entries/MEM-20260925-131-default-gate-must-not-see-live-credentials.md
---

# PLAN-20260925-161 — 跨套件隔离归零（GOAL-015 EC-01）

## 目标

把「同一套件组合合并跑红、单独跑绿」的**顺序 / 共享状态依赖归零**，并且**只修真实来源**：
不 skip、不 xfail、不改收集顺序、不放宽任何判据或阈值。

## 验收条件

- **AC-1｜普查表落盘**：`docs/evaluation/CROSS_SUITE_ISOLATION_AUDIT.md` 列出 ① 已知签名
  （`W-D` 的 4 条历史签名 + 历史同类修法）② 用**既有 m0 全量配方**（`--profile m0
  --keep-going`，DSN 固化）跑出的**实际红项**，每条给出**可复现最小命令**、根因、修法、终态。
- **AC-2｜R-1 修复（草稿列表序 tie）**：同一 `created_at` 下 `list()` 的返回序与「按新近」
  语义一致，且是**全序**；三个实现（SQLite / PostgreSQL / InMemory）**同语义**。
- **AC-3｜R-2 修复（默认门凭据隔离）**：未标记 `requires_live_llm` 的用例**不得**看见出厂
  目录声明的 `credential_ref` 对应环境变量；夹具与出厂目录**由机械判据双向对齐**。
- **AC-4｜同一组合连续两轮全绿**：m0 的 `python/tests` 组合（`pytest
  --ignore=tests/architecture/python/test_dependency_boundaries.py`）**连续两轮** `0 failed`；
  出站判据**只有判据自身的探针**被拦，无整轮红灯。
- **AC-5｜成对反证（先红后绿）**：把修前的代码状态**重新构造出来**跑同两条判据 ⇒
  **R-1 判红、R-2 按压命令判红**；还原后**逐字节**复核一致、`git diff` 无残留。
- **AC-6｜判据只增不减**：逐用例 ID 差集说明用例数变化，**零删除**、零断言削弱；
  `tests/egress_guard.py` / `framework/validate_bundle` / m0 阈值**逐字节未改**（`git diff` 证明）。

## 实施清单

- [x] **WP1 — 普查**：两类红项的最小复现命令固化为可复跑证据，并落
      `docs/evaluation/CROSS_SUITE_ISOLATION_AUDIT.md`（红项 / 最小命令 / 根因链 / 修法 / 终态
      + `W-D` 历史签名复核 + R-4 的定向跑挂死复现）。
      装置：`scratch/goal015_c1_order_tie_probe.py`（冻结时钟的三实现 tie 探针）、
      `scratch/goal015_c1_credential_refs_probe.py`（出厂目录 active `credential_ref` 枚举）。
- [x] **WP2 — R-1 修复**：`adapters/sqlite/protocol_draft_store.py` 与
      `adapters/postgres/protocol_draft_store.py` 的 `ORDER BY created_at DESC, d.draft_id`
      ⇒ `…, d.draft_id DESC`；`packages/application/protocol_authoring/memory_store.py` 的排序键
      ⇒ `(created_at, draft_id)` 反序（三实现同语义）。新增判据
      `tests/contracts/test_protocol_draft_store_order_tie.py`（修前 3 failed → 修后 3 passed）。
- [x] **WP3 — R-2 修复**：新增 `tests/default_gate_credentials.py`（名单 + 出厂目录解析）；
      `tests/conftest.py` 增设 autouse 夹具（未标记 `requires_live_llm` 的用例隐藏凭据键）；
      新增判据 `tests/architecture/python/test_default_gate_credential_isolation.py`
      （名单 ↔ 出厂目录双向对齐 / 非空真隔离断言 / 子进程按压）。
- [x] **WP4 — 本地验证**：实测 as-is m0 基线 21/23（两红项）→ 修后 `python/tests` **连续两轮
      `4455 passed / 0 failed`**（`egress guard: FAIL` 计数 0）；定向套件 `993 passed, 2 skipped`；
      `validate.py` 绿；`DOCS-CHECK PASS: 6`；m0 全量终态见「证据」。
- [x] **WP5 — 成对反证 + 记录**：`git stash push -- <显式四路径>` 重建修前状态 ⇒ R-1 判据
      `3 failed`、R-2 按压 `blocked 2`；`git stash pop` 后 `sha256sum -c` 四行全 `OK`；
      RECHECK 定稿；GOAL-015 回写（EC-01 / 迭代日志 / 台账 / 续点）。

## 证据

- **修前 / 修后（同一配方）**：`scratch/goal015-c1-m0-census.log`（`FAILED: 2 check(s):
  python/tests=1, framework/validate_bundle=1`；`1 failed, 4445 passed, 19 skipped in 569.15s`；
  `egress guard: … blocked 10`）→ `scratch/goal015-c1-roundA.log` / `-roundB.log`
  （`4455 passed, 19 skipped` ×2；`egress guard: FAIL` 计数 0）。
- **判据先红后绿**：`scratch/goal015-c1-press-r1-before.txt`（3 failed）→ 修后 `12 passed`；
  `scratch/goal015-c1-press-r2-after-revert.txt`（`blocked 2` + 整轮红）→ 修后 `blocked 0`。
- **成对反证与逐字节还原**：`scratch/goal015-c1-press-files-before.sha256`（四行 `OK`）。
- **用例数归因**：`4446 → 4455` = **+9 / 零删除**（+6 新判据逐 ID、+3 规模门禁对新增 `.py`
  的参数化），实测 `--collect-only` 逐 ID 列出。
- **本地门**：`scratch/goal015-c1-m0-final.log`（终态行见 GOAL-015 迭代日志）；
  `python .cursor/skills/governance-check/scripts/validate.py` = `Cursor 治理验证通过`；
  `tools/docs_consistency_check.py` = `DOCS-CHECK PASS: 6 deterministic checks`。
- **一处如实登记的返工**：首轮 8 分钟跑判红 `test_real_repo_is_clean`，根因是本 PLAN 新增文档里
  的 backtick 引用 `tests/postgres/conftest` 不存在（缺 `.py`）⇒ 修正后重跑，两轮全绿取自
  修正后的树。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-25 | IN_PROGRESS | derive：GOAL-015 cycle 1。普查完成（as-is 21/23，四个红项各有最小复现命令）。 |
| 2026-09-25 | IN_PROGRESS | WP2 / WP3 落地：R-1 三实现 tie-break 与新近一致；R-2 夹具隔离 + 与出厂目录双向对齐判据。 |
| 2026-09-25 | DONE | WP4 / WP5 收口：同一组合连续两轮 `4455 passed / 0 failed`；成对反证先红后绿 + 逐字节还原；RECHECK-20260925-163 = `PASS_WITH_WARNINGS`。 |

## 影响报告

- **Domain / API / schema**：**零**。改动落在三个 `ProtocolDraftStore` 适配器/实现的
  `list()` 排序与测试隔离面；无 DTO / 路由 / 快照 / 迁移变化（OpenAPI 与设计基线未动）。
- **行为变化（可见面）**：`protocol_drafts` 列表在 `created_at` 同刻时由「旧的在先」变为
  「新的在先」——这正是 port 契约「按新近」的语义；跨实现（SQLite / PostgreSQL / InMemory）
  从此**同语义**。消费面（`services/api/routers/protocol_drafts.py`、web 草稿列表）无契约变化。
- **安全 / 凭据**：**判据未动**。新增的是**收窄**：默认门（非 live 用例）不再继承
  operator `.env` 的凭据键；live 面照旧（同一 `ALLOW_MARKER`）。不新增任何凭据字面量，
  不写 `.env`，不改出站判定。
- **兼容性 / 迁移风险**：无数据迁移；无 pin / 依赖变化；`R-4` 的定向跑挂死**未在本 PLAN 修**
  （已登记去 cycle 2），故「PG 不可达时定向跑 postgres 用例」仍是挂死形态。
- **上游版本影响**：无（未新增 / 未升级任何依赖）。
- **下一项任务**：GOAL-015 cycle 2 = **EC-02 本地判定确定性**（跑法协议 + 机械三分类 +
  两条具名起点终态），其中含本 PLAN 普查出的 **R-4** 实施（把 postgres 跳过守卫提为加载无关）。
