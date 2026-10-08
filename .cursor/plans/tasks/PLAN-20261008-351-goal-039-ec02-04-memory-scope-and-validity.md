---
id: PLAN-20261008-351
slug: goal-039-ec02-04-memory-scope-and-validity
title: GOAL-039 cycle 1（EC-02/EC-03/EC-04）：`scope` 落库 + 声明式时效 + 到期可观测
status: DONE
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-352-goal-039-ec02-04-memory-scope-and-validity.md
memory_entries: []
parent_goal: GOAL-20261008-039
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-039 的 **EC-02 / EC-03 / EC-04**。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：**只加列 + 缺省回填**（不删改既有行语义）；
    **不改门链语义**（仍是 schema → provenance → policy → gate → commit）；
    时效判定**不读挂钟**（时点由调用方给 ⇒ 可复现）；缺省路径**逐字不变**（判据钉住）；
    **新读面按既有纪律同轮同步**（读面登记 + OpenAPI 快照 + 出口普查）；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让「适用范围」与「时效」成为**可判定的事实**：① **`scope` 落库**（域记录 + 迁移 018
    只加列 + 两适配器往返 + Fake 同契约 + 读面披露）；② **声明式时效**（提案可声明两时点；
    缺省路径逐字不变）；③ **到期可观测**（纯函数三态判定 + `GET .../memory/validity?at=`
    逐条披露；三反证）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **`scope` 落库且往返一致**：`MemoryRecord` 增 `scope`（缺省 `"project"`，空串拒绝）；
      迁移 `018_memory_scope_and_validity.sql`（`ADD COLUMN IF NOT EXISTS ... DEFAULT
      'project'`）；SQLite / PG / Fake **三实现同契约**（提交回执与写面一致）；
      读面 `MemoryRecordDto.scope` 逐条披露。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters tests/api -q` ⇒ 全绿。
    status: PASS
  - id: AC-2
    criterion: >-
      **声明式时效（缺省不变）**：提案增 `review_after` / `expires_at`（可选）；两适配器
      **写真实值**（PG 不再硬编码 `None`）；未声明 ⇒ 两时点保持 `None`。
    verify: >-
      同上判据文件的「声明 ⇒ 真实值 / 未声明 ⇒ None」两条。
    status: PASS
  - id: AC-3
    criterion: >-
      **到期可观测（三态 + 三反证）**：`validity_at(record, now)` 给 `EXPIRED` /
      `REVIEW_DUE` / `None`（**不读挂钟**）；边界 `expires_at == now` ⇒ 已过期；
      读面 `GET /projects/{id}/memory/validity?at=`（GET ⇒ 读面族、不进写面）；
      反证：未到期不报 / 到期必报 / **未声明不被误报**；同瞬判定相同。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters tests/api -q` ⇒ 全绿。
    status: PASS
  - id: AC-4
    criterion: >-
      **门链 + 记录面**：四道门绿；受影响套件全绿；新读面同轮同步（读面登记 + OpenAPI +
      出口普查）；治理 `validate.py` 绿；记录（本 PLAN、`RECHECK-20261008-352`）。
    verify: >-
      门读数逐条 + 广面套件读数。
    status: PASS
---

# PLAN-20261008-351 — GOAL-039 cycle 1（EC-02/03/04）

## 验收条件

见 frontmatter `exit_criteria`。

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | `scope` 落库且往返一致（三实现同契约 + 读面披露） | PASS |
| AC-2 | 声明式时效（缺省不变） | PASS |
| AC-3 | 到期可观测（三态 + 三反证；GET 读面） | PASS |
| AC-4 | 四道门 + 新读面同轮同步 + 记录面 | PASS |

## 实施清单

- [x] `packages/domain/memory.py`：`MemoryRecord.scope`（+ 空串拒绝）/ `MemoryWriteProposal`
      增两时点。
- [x] `adapters/postgres/migrations/018_memory_scope_and_validity.sql`：只加列 + 缺省回填
      （含既有两时效列的就位说明）。
- [x] `adapters/sqlite/memory_store.py`：schema 加列 + 读写带上 + **占位符按列数生成**
      （此前硬编码 12 个 `?`）；`adapters/postgres/memory_store.py`：INSERT 带 `scope` +
      **写真实时点**（不再硬编码 `None`）+ 回执带 scope/两时点；`adapters/fakes/memory_store.py`
      同契约。
- [x] `packages/application/memory/validity.py`：三态纯函数（**不读挂钟**）。
- [x] `services/api/routers/memory.py` + `dto/memory.py`：读面披露 `scope`；新 GET
      `/projects/{id}/memory/validity?at=`（逐条判定 + 原始两时点）。
- [x] 同轮同步：读面登记（零命中档 + 理由）、OpenAPI 快照重生成。
- [x] 判据：`tests/adapters/sqlite/test_memory_scope_and_validity.py`（11 例）+
      `tests/api/test_memory_api.py` 三例新增。
- [x] 记录面：本 PLAN、`RECHECK-20261008-352`、GOAL 行、`ALL_PLAN`、m0。

## 证据

| 门 | 读数 |
| --- | --- |
| 新判据（适配器面） | `tests/adapters/sqlite/test_memory_scope_and_validity.py` **11 passed** |
| 新判据（API 面） | `tests/api/test_memory_api.py` **9 passed**（含三条新增） |
| 新判据（**PG 面**） | `tests/postgres/test_memory_scope_pg.py` **2 passed**（真库往返：`scope` + 两时点；未声明 ⇒ `None`）—— live PG 实测 `migration_version` 最新 = **18**、`m12_memory` 列表实见 `scope` |
| 广面（api + adapters + domain + application + contracts + loaders + tooling + observability + postgres） | **4503 passed, 82 skipped** |
| 隐私读面 | `tests/observability` **133 passed, 2 skipped** |
| `mypy`（strict） | `Success: no issues found in 1166 source files` |

> **三处真红并修（本地，如实登记）**：① SQLite 的 `INSERT` **硬编码 12 个占位符** —— 加列后
> 变 13 列 ⇒ `12 values for 13 columns`；处置 = **按列数生成占位符**（不再手数）。
> ② 新路由首版写成 **POST** ⇒ 写面枚举告警线 63 → 64：复核后判定它是**读面**（判定只依赖
> canonical × 显式时点，无业务写入）⇒ 改为 **GET**（写完面计数回 63，且不占幂等键面）。
> ③ 三处读面登记同步（新 GET 需逐条表态）：首版放错「声明内容」档 ⇒ 触发声明面上界
> （16 > 15）⇒ 更正为**零命中档**（它只给 id/scope/时间戳/三态，正文在兄弟路由）。
> ④ **第四次真红**：`tests/api/test_memory_api.py` 的判定用例 **53 行**（超 50 上限）⇒
> **抽 helper**（`_commit_expiring`），不调阈值。

## 无可复用事实

本 cycle 的可复用事实与既有记录同族（「加列必须同时改占位符数」属通用实现常识；
「只读判定用 GET 不占写面」已由 `services/api/middleware.py` 的分层注释承载）；
本轮未产生新的可复用工程事实。

## 影响报告

- **Domain / API / schema 变化**：`MemoryRecord` 增 `scope`（缺省 `"project"`）；
  提案增两可选时点；PG 迁移 **018**（只加列 + 缺省）；新读面一条（GET）。
- **安全 / 凭据变化**：无（不动放行面 / 不动门链语义）。
- **兼容性 / 迁移风险**：**低** —— 只加列 + 缺省回填（既有行读出 `"project"` / `None`）；
  缺省路径由判据钉住逐字不变。
- **观测隐私**：新读面**零命中档**（只给元数据与判定，不含记忆正文）；读面登记同轮。
- **上游版本影响**：无。
- **下一项任务**：EC-05（自举收口 + GOAL 收口）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | IN_PROGRESS | 三条 AC 落地：域 / 迁移 018 / 三适配器同契约 / 三态纯函数 / 新 GET 读面；判据 11 + 3 例全绿；广面 4379 passed。 |
| 2026-10-08 | DONE | 四条 AC 全 PASS；`RECHECK-20261008-352` 独立复检（PASS_WITH_WARNINGS：三处真红并修 + SQLite 旧表加列边界如实登记）。 |
