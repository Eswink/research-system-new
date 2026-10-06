---
id: RECHECK-20261006-299
slug: goal-031-ec04-lineage-label-rename
title: 复检：GOAL-031 EC-04 —— `LineageNodeDto.label` → `text`（改名 + 四处同步 + 旧名零命中 + 两向反证）
status: COMPLETED
result: PASS
created_at: 2026-10-06
updated_at: 2026-10-06
plan_id: PLAN-20261006-299
reviewer: root-agent
parent_goal: GOAL-20261006-031
verify_paths:
  - >-
    uv run --frozen --no-sync python -B -m pytest
    tests/tooling/test_lineage_label_rename_is_complete.py -q ⇒ 11 passed
  - >-
    uv run --frozen --no-sync python -B -m pytest tests/api tests/observability
    tests/contracts tests/tooling -q ⇒ 2573 passed / 76 skipped
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261006-031 的 EC-04 与 fix_policy；复检两路（判据面 + 定向回归面），
    另以 scratch 脚本**实跑**生成判词归档（含两次反证注入）。**不改任何既有判据** ——
    `tests/contracts/test_openapi_snapshot.py` 等既有文件 `git diff --numstat` 为**空**。
---

# RECHECK-20261006-299：EC-04 复检

## 检查结果

EC-04 的五条分支（(a) 改名落地 / (b) 四处同步 / (c) 旧名零命中 / (d) 既有快照判据未改且绿 /
(e) 两向反证）**逐条实测通过**：

- 判据 `tests/tooling/test_lineage_label_rename_is_complete.py` **11 passed**（含两条自检：
  「扫描会报」与「不误报别的字段」）；
- 全仓血缘上下文扫描：受判面 **11 个文件**、旧名命中 **0**；
- 定向回归（api + observability + contracts + tooling）**2573 passed / 76 skipped**；
- web 门 typecheck / lint / test（94 pass）/ build 全绿；
- 两向反证判红原文归档（下述）。

**零警告**：本 EC 没有需要登记的残余（`RECHECK` 里不掩盖任何观察）。

## 结论

**PASS**。改名与四处同步落地，旧名在全仓血缘面零命中且判据自带反证与自检；既有判据
（含 OpenAPI 快照判据）**一字未改**；兼容性经**实测**（不是推定）确认不破坏仓内消费者，
且本仓不对外发布该 DTO ⇒ 无外部契约承诺面被破坏。

## 复核路径（`verify_paths` 两路）

### 路径 1：判据面（新增判据）

```
uv run --frozen --no-sync python -B -m pytest tests/tooling/test_lineage_label_rename_is_complete.py -q
⇒ 11 passed
```

五个测试类逐条对上 EC-04 分支：`TestTheFieldIsRenamed`（(a)）/
`TestTheFourPlacesAreSynchronised`（(b)）/ `TestTheOldFieldNameHasZeroHits`（(c) + 两条自检）/
`TestTheConsumersOutsideTheSurface`（(d) 兼容性实测）/ `TestTheSnapshotJudgeIsUntouchedAndGreen`（(e)）。

### 路径 2：定向回归面

```
uv run --frozen --no-sync python -B -m pytest tests/api tests/observability tests/contracts tests/tooling -q
⇒ 2573 passed, 76 skipped, 105 warnings
```

覆盖血缘 API 判据（`test_reports_integrations_lineage_api` / `test_project_lineage_api`）、
既有快照判据（`test_openapi_snapshot`）、读面金丝雀（`tests/observability` —— 其登记面
的注记文字随本轮改名同步）与全部工具门。

### 补充门（web + 本轮改动文件）

- `pnpm --dir apps/web run {typecheck,lint,test,build}` ⇒ 全绿（unit 94 pass / 0 fail）。
- `ruff check` / `ruff format --check` ⇒ 全绿。

## 判据面逐条取证（判词原文，逐字抄自归档）

归档：`.cursor/plans/goals/evidence/GOAL-20261006-031-ec04-rename-and-zero-hit-ledger.txt`
（二进制写盘、CR=0；由 `scratch/goal031-cycle4` 内联脚本**实跑**生成）。

### (a) 改名（AST 读类体注解名）

```
LineageNodeDto: ['id', 'kind', 'text', 'run_id']
ProjectLineageNodeDto: ['id', 'kind', 'text', 'run_ids', 'shared']
```

### (b) 旧名零命中：全仓血缘上下文扫描

```
受判面（承载血缘 DTO 的文件）: 11 个
  services/api/dto/inspection.py
  services/api/lineage_projection.py
  services/api/project_lineage.py
  services/api/routers/lineage.py
  apps/web/src/api/types.ts
  apps/web/src/features/lineage/lineageColumns.tsx
  apps/web/src/features/lineage/LineageProjection.tsx
  apps/web/src/features/lineage/projectLineageColumns.tsx
  tests/api/test_project_lineage_api.py
  tests/observability/read_face_route_registry.py
  docs/api/openapi.m13.json
旧名命中: 0
```

### (c) 反证① 把旧名放回生产构造点（`services/api/lineage_projection.py`）

```
exit=1
FAILED …::TestTheOldFieldNameHasZeroHits::test_no_surface_file_carries_the_old_field_name
FAILED …::TestTheOldFieldNameHasZeroHits::test_no_lineage_context_file_carries_the_old_field_name
2 failed, 9 passed
```

### (c) 反证② 把旧名放回 web 渲染读取点（`lineageColumns.tsx`）

```
exit=1
FAILED …::TestTheOldFieldNameHasZeroHits::test_no_surface_file_carries_the_old_field_name
FAILED …::TestTheOldFieldNameHasZeroHits::test_no_lineage_context_file_carries_the_old_field_name
FAILED …::TestTheConsumersOutsideTheSurface::test_the_consumers_outside_the_surface_do_not_read_the_old_field
3 failed, 8 passed
```

### (d) 兼容性实测结论（EC-04(d)：测出来的，不是推定的）

- 仓内消费者（web 两列定义 + e2e 夹具 + 快照 + 两条 API 判据）**同轮同步**；
- 受判面**之外**的两个血缘前端件（`provenanceModel.ts` / `ProvenanceGraph.tsx`）的 `label`
  是**它们自己的视图模型字段**（值取自 `ClaimDto.statement` / `EvidenceDto.id`），
  **不 import 血缘 DTO** ⇒ 与本次改名无关（判据把那两个文件里不得出现 `LineageNodeDto`
  写成断言）；
- 本仓**不对外发布**该 DTO（无外部契约承诺面）⇒ **无兼容性破坏**；无需双写/弃用方案。

## 两处判据自缺口（自己发现、自己修，如实登记）

1. **扫描模式首版把 `.` 排除在词边界外** ⇒ 对 `row.label`（TS 里读旧字段的**真实形态**）
   **不报** ⇒ 反证臂（把旧名放回 `lineageColumns.tsx`）首跑判**绿** = 判据是空转的。
   修：属性读 `.label` 单列一条模式（`-` / `_` 的排除保留，`aria-label` / `trust_label`
   仍不算命中）；修后两次反证都判红。
2. **全仓扫描会收进隐藏目录的会话状态文件**（`apps/web/.mimosa/hook-state/*.json`，
   客户端产物、随会话变化）⇒ 受判集会**不稳定**。修：明写排除隐藏目录（判据内注释说明
   理由），受判面因此是确定的 11 个文件。

两处都是**判据构造**的缺陷（受判面与模式），**强度未降**：修完后反证臂按压判红、
自检用例逐条钉住。

## 残余与未覆盖（原样保留 + 本轮新增）

- 承继：`R-M1` / `R26-1` / `R26-5` / `R26-7` / `R26-8` / `W27-*` / `W10-12` / `G24-5`；
  GOAL-019…030 的未覆盖范围**原样保留**。
- 本轮：`W31-1`（放行 ≠ 被用）/ `W31-2`（同步集是重新定基）/ `W31-3`（`_PROVIDERS` 单行 tuple）/
  `W31-4`（触发面新机制）/ `W-EC02-1/2/3` / `W-EC03-1/2`。
- 本 EC **不声称**：改名对**外部**消费者无损（本仓不对外发布该 DTO，无外部面可测）；
  web 显示文案的语义（「标签 / Label」列头**保持不变**，它是 UI 文案不是字段语义，
  且被 `design-outlines.json` 结构签名钉住）。
