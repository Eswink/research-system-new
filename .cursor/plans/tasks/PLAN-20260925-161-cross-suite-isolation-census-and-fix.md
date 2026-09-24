---
id: PLAN-20260925-161
slug: cross-suite-isolation-census-and-fix
title: 跨套件隔离归零：红项普查 + 两处真实共享来源修复（草稿列表序 tie / 默认门凭据泄漏）（GOAL-015 EC-01）
status: IN_PROGRESS
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
latest_recheck: null
memory_entries: []
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
  出站判据**只有判据自身的探针**被拦（`blocked` 计数等于自身探针数），无整轮红灯。
- **AC-5｜成对反证（先红后绿）**：在**修前提交**（`1d8fe1f`）的临时 worktree 上跑同两条判据
  ⇒ **R-1 判红、R-2 按压命令判红**；回到本树 ⇒ 全绿。反证后临时 worktree 移除、
  `git diff --stat` 无残留。
- **AC-6｜判据只增不减**：逐用例 ID 差集说明用例数变化，**零删除**、零断言削弱；
  `tests/egress_guard.py` / `framework/validate_bundle` / m0 阈值**逐字节未改**
  （`git diff` 证明）。

## 实施清单

- [ ] **WP1 — 普查**：把两类红项的最小复现命令固化成**可复跑的证据**，并落
      `docs/evaluation/CROSS_SUITE_ISOLATION_AUDIT.md`（红项 / 最小命令 / 根因链 / 修法 / 终态）。
      装置：`scratch/goal015_c1_order_tie_probe.py`（冻结时钟的三实现 tie 探针）、
      `scratch/goal015_c1_credential_refs_probe.py`（出厂目录 active `credential_ref` 枚举）。
- [ ] **WP2 — R-1 修复**：`adapters/sqlite/protocol_draft_store.py` 与
      `adapters/postgres/protocol_draft_store.py` 的 `ORDER BY created_at DESC, draft_id` ⇒
      tie-break 与新近一致；`packages/application/protocol_authoring/memory_store.py` 同语义。
      新增**判据** `tests/contracts/test_protocol_draft_store_order_tie.py`（先红后绿可演示）。
- [ ] **WP3 — R-2 修复**：`tests/conftest.py` 增设 autouse 夹具：未标记 `requires_live_llm`
      的用例不得看见出厂目录声明的凭据键（`monkeypatch.delenv`，用例结束自动还原）。
      新增**判据** `tests/architecture/python/test_default_gate_credential_isolation.py`：
      ① 夹具名单 ↔ 出厂目录 active `credential_ref` 双向对齐；② **按压**：把凭据键注入子进程环境
      跑 `tests/api/test_runs_api.py` ⇒ 该轮出站判据不得判红（`blocked 0`）。
- [ ] **WP4 — 本地验证**：`make validate-all`（m0，独占）+ `python/tests` 组合**连续两轮** +
      受影响定向套件 + web 门 + `validate.py` + `DOCS-CHECK`；随后 push 并轮询 CI 到终态。
- [ ] **WP5 — 成对反证 + 记录**：修前提交的临时 worktree 上跑同两条判据 ⇒ 判红；
      RECHECK 定稿；GOAL-015 回写（EC-01 / 迭代日志 / 台账 / 续点）。

## 证据

（收口时补齐：命令 + 真实输出 + 文件路径）

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-25 | IN_PROGRESS | derive：GOAL-015 cycle 1。普查已完成（见 WP1 证据），R-1 / R-2 根因各由最小复现命令钉住。 |

## 影响报告

（收口时补齐）
