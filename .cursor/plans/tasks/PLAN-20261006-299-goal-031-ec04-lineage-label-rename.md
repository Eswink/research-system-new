---
id: PLAN-20261006-299
slug: goal-031-ec04-lineage-label-rename
title: GOAL-031 cycle 4（EC-04）：`LineageNodeDto.label` → `text` —— 语义修正 + 四处同步 + 旧名零命中 + 两向反证
status: DONE
created_at: 2026-10-06
updated_at: 2026-10-06
latest_recheck: .cursor/plans/rechecks/RECHECK-20261006-299-goal-031-ec04-lineage-label-rename.md
memory_entries: []
parent_goal: GOAL-20261006-031
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261006-031 的 **EC-04**（授权 3：`G24-4` 读面字段语义修正）。授权原文见该
    GOAL 的 `authorization.ref`：「用户 2026-10-06 明确下放全部权限给驱动」+「**可以有界放宽
    allow**、**不得**放宽判据/断言/门禁/阈值」+ push-to-main-for-CI 口径（只推 `main`、
    不 force、不重写历史；push 前 `git pull --ff-only origin main`）。**本 PLAN 专属边界**：
    本 EC **不放宽任何面**（既无 allow 放宽、也无 pin 追加）—— 它是**字段改名 + 四处同步**；
    既有判据（含 `tests/contracts/test_openapi_snapshot.py`）**一字未改**；零新依赖；
    零真实凭据进树；默认门离线；**不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义
    为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
objective: >-
    `LineageNodeDto.label` / `ProjectLineageNodeDto.label` 的**值**从来不是「标签」
    （`G24-4` 实测：claim 节点填 `claim.statement` 正文、source/evidence 填 `source_ref`、
    artifact/model 填 id/ref）⇒ 改名 `text` 使字段名与语义一致。**四处同轮同步**：
    DTO + OpenAPI 快照（再生成）+ `apps/web` 类型（两类 DTO）+ e2e 夹具。**判据**：
    旧名**全仓**零命中（逐字节扫描 + 行号可诊断）、既有快照判据一字未改且绿、两向反证
    （把旧名放回生产构造点 / web 渲染点 ⇒ 判红并点名文件）。**兼容性实测**（不许推定）：
    受判面之外的消费者（`ProvenanceGraph` / `provenanceModel`）用**自己的视图模型** `label`
    （值取自 `ClaimDto.statement` / `EvidenceDto.id`），**不消费**血缘 DTO ⇒ 改名不破坏兼容。
exit_criteria:
  - id: AC-1
    criterion: >-
      **改名落地**：两个 DTO 的字段声明为 `text`（AST 读类体注解名），生产构造点逐条用
      `text=`；`label` 字段名**不再存在**于两个类体。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_lineage_label_rename_is_complete.py::TestTheFieldIsRenamed -q`
      ⇒ 全绿。
    status: PASS
  - id: AC-2
    criterion: >-
      **四处同轮同步**：DTO（`services/api/dto/inspection.py`）+ OpenAPI 快照
      （`docs/api/openapi.m13.json`，由 `tools/gen_openapi.py` 再生成）+ `apps/web` 类型
      （`apps/web/src/api/types.ts` 两类 DTO）+ e2e 夹具
      （`apps/web/tests/e2e/stub-routes-lineage.ts`）+ 两个渲染列定义 —— **逐文件**断言
      新名在场（缺哪处点名哪处）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_lineage_label_rename_is_complete.py::TestTheFourPlacesAreSynchronised -q`
      ⇒ 全绿。
    status: PASS
  - id: AC-3
    criterion: >-
      **旧名零命中（逐字节）**：受判面 = 「出现血缘 DTO / 投影 / 列定义标记的文件」这一
      **从文件本身推出来**的集合（11 个文件，非白名单）+ 两个 DTO 类体 + 快照 schema；
      命中即判红并**逐条点名文件与行号**。判据文件自身**明写**排除（它必须点名旧字段才能测它）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_lineage_label_rename_is_complete.py::TestTheOldFieldNameHasZeroHits -q`
      ⇒ 全绿（含「扫描会报」与「不误报别的字段」两条自检）；
      配套留档：`.cursor/plans/goals/evidence/GOAL-20261006-031-ec04-rename-and-zero-hit-ledger.txt`。
    status: PASS
  - id: AC-4
    criterion: >-
      **既有快照判据一字未改且绿**：`tests/contracts/test_openapi_snapshot.py` 保持
      「再生成 schema vs 仓库快照」的比对形态（本 EC 不放宽任何既有断言）；
      `git diff --numstat` 对该文件为空。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/contracts/test_openapi_snapshot.py
      tests/api/test_reports_integrations_lineage_api.py tests/api/test_project_lineage_api.py -q`
      ⇒ 全绿。
    status: PASS
  - id: AC-5
    criterion: >-
      **反证两向**：① 把旧名放回**生产构造点**（`services/api/lineage_projection.py`）⇒
      判红并点名该文件；② 把旧名放回 **web 渲染读取点**
      （`apps/web/src/features/lineage/lineageColumns.tsx`）⇒ 判红并点名该文件。
    verify: >-
      两臂判红原文归档
      `.cursor/plans/goals/evidence/GOAL-20261006-031-ec04-rename-and-zero-hit-ledger.txt`；
      web 侧 `pnpm --dir apps/web run {typecheck,lint,test,build}` ⇒ 全绿。
    status: PASS
---

# PLAN-20261006-299（GOAL-031 cycle 4 / EC-04）：读面字段语义修正

## 验收条件

见 frontmatter `exit_criteria`（AC-1 … AC-5，逐条 verify 命令与状态）。

## 实施清单

- [x] ① DTO 改名：`services/api/dto/inspection.py` 的 `LineageNodeDto` /
      `ProjectLineageNodeDto` 字段 `label` → `text`。
- [x] ② 生产投影同步：`services/api/lineage_projection.py`（构造点与 `add_node` 形参）、
      `services/api/project_lineage.py`（`_MergedNode` 字段 / `_merge` 形参 / DTO 构造点）。
- [x] ③ web 类型同步：`apps/web/src/api/types.ts` 两类 DTO 字段。
- [x] ④ web 渲染同步：`lineageColumns.tsx` / `projectLineageColumns.tsx` 的 `render: (row) => row.text`
      （**列头文案「标签 / Label」逐字保留** —— 显示文案不是字段语义，且它被
      `design-outlines.json` 结构签名钉住）。
- [x] ⑤ e2e 夹具同步：`apps/web/tests/e2e/stub-routes-lineage.ts` 三个节点字面量。
- [x] ⑥ 快照再生成：`uv run --frozen --no-sync python -B tools/gen_openapi.py`（10 行增删）。
- [x] ⑦ 判据文件（新增）：`tests/tooling/test_lineage_label_rename_is_complete.py`
      （11 例；含扫描自检与「不误报别的字段」自检）。
- [x] ⑧ 判词归档进树（二进制写盘、CR=0）：
      `.cursor/plans/goals/evidence/GOAL-20261006-031-ec04-rename-and-zero-hit-ledger.txt`。

## 证据

- 判据：`tests/tooling/test_lineage_label_rename_is_complete.py` **11 passed**。
- 归档读数（改名）：`LineageNodeDto: ['id','kind','text','run_id']` /
  `ProjectLineageNodeDto: ['id','kind','text','run_ids','shared']`。
- 归档读数（零命中）：受判面 **11 个文件**（逐条列出），旧名命中 **0**。
- 归档读数（反证①）：`exit=1`，两条 FAILED 点名 `lineage_projection.py` 命中。
- 归档读数（反证②）：`exit=1`，三条 FAILED（含「受判面之外消费者」判据）。
- 定向回归：`tests/api tests/observability tests/contracts tests/tooling`
  ⇒ **2573 passed / 76 skipped**；`tests/tooling` 单跑 **1335 passed**。
- web 门：`typecheck` / `lint` / `test`（94 pass）/ `build` ⇒ 全绿。
- `ruff check` / `ruff format --check` 对本轮改动文件 ⇒ 全绿。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-06 | DONE | cycle 4 落地：改名 + 四处同步 + 全仓零命中判据（11 例）+ 两向反证 + 判词归档。AC-1…AC-5 全 PASS。**两处判据自缺口自查自修**：① 扫描模式首版排除了 `.` ⇒ 对 `row.label` 不报（空转）⇒ 改为属性读算命中；② 全仓扫描会收进隐藏目录的会话状态文件（受判集不稳定）⇒ 明写排除隐藏目录。 |

## 影响报告

- **Domain / API / schema**：域层**零改动**；**API 契约字段改名**（`LineageNodeDto` /
  `ProjectLineageNodeDto` 的 `label` → `text`），OpenAPI 快照同轮再生成（10 行增删）。
- **安全 / 凭据**：零新凭据、零新依赖、零出网（判据只读文件）。
- **兼容性 / 迁移风险**：**已实测**（EC-04(d)）——受判面之外的消费者用**自己的视图模型**
  `label`（值取自 `ClaimDto.statement` / `EvidenceDto.id`），不消费血缘 DTO；本仓**不对外
  发布**该 DTO ⇒ 改名不破坏兼容。仓内消费面（web 两列 + 夹具 + 快照）**同轮同步**。
- **上游版本影响**：无（未动依赖）。
- **下一项任务**：cycle 5 = EC-05（自举收口）。

## 无可复用事实

**无**（产出全部可复用：改名后的四类文件 + 判据 + 判词归档都在树内）。
`memory_entries` 在 GOAL 层回填。
