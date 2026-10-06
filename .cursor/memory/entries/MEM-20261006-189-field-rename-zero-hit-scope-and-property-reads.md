---
id: MEM-20261006-189
title: "改一个读面字段名：受判面要从**文件本身推出来**（按上下文标记），且扫描模式必须把**属性读**算命中——否则判据是空转"
status: ACTIVE
created_at: 2026-10-06
updated_at: 2026-10-06
scope: repository
confidence: 0.94
review_after: 2027-04-06
source_plans:
  - .cursor/plans/tasks/PLAN-20261006-299-goal-031-ec04-lineage-label-rename.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261006-299-goal-031-ec04-lineage-label-rename.md
supersedes: []
tags: [field-rename, zero-hit-scan, ast-vs-text, false-green, goal-031, plan-299]
---

## 做了什么

GOAL-031 EC-04 把 `LineageNodeDto.label` / `ProjectLineageNodeDto.label` 改名为 `text`
（值从来不是「标签」——claim 节点填 `claim.statement` 正文、source/evidence 填
`source_ref`、artifact/model 填 id/ref）。配套判据要断言「旧名零命中」，**两处判据自缺口
（都是自己发现、自己修）**：

1. **扫描模式首版把 `.` 也排除在词边界外** ⇒ 对 `row.label`（TS 里读旧字段的**真实形态**）
   **不报** ⇒ 反证臂（把旧名放回 `lineageColumns.tsx`）**首跑判绿** = 判据是**空转**的。
   修：属性读 `.label` 单列一条命中模式；`-` / `_` 的排除保留（`aria-label` /
   `trust_label` 是**别的字段**，不得误报——两条自检用例逐条钉住这两种方向）。
2. **全仓扫描会收进隐藏目录的会话状态文件**（`apps/web/.mimosa/hook-state/*.json`，
   客户端产物、随会话变化）⇒ **受判集不稳定**（同一判据在不同会话下扫描面不同）。
   修：明写排除隐藏目录，受判面因此确定为 **11 个文件**（逐条列出）。

**受判面的正确形态**：「凡出现血缘 DTO / 投影 / 列定义标记的文件」——从**文件本身推出来**
的集合（11 个），不是白名单；新增一个承载该 DTO 的文件会自动进面。该集合之外的两个
血缘前端件（`provenanceModel.ts` / `ProvenanceGraph.tsx`）用**自己的视图模型** `label`
（值取自 `ClaimDto.statement` / `EvidenceDto.id`），不 import 血缘 DTO ⇒ 判据把那句
「不得出现 `LineageNodeDto`」写成断言（兼容性实测的机械形态）。

## 为什么这样做

「旧名零命中」这类判据最容易**看起来绿**：全文扫描若模式写窄一点（排除 `.`），
所有属性读都漏掉；受判面若含会话相关文件，判据在不同会话结果不同（不可复现）。
两个坑都**不改变断言语义**，只改变受判面与模式——所以全套门（m0 23/23、两树、治理）
**全绿也照不出**，只有**按压反证**（注入旧名）才暴露。

## 怎么做与复现

- **受判面**：从文件内容推（标记法），逐文件列出；含 `node_modules` / 隐藏目录 / 判据
  文件自身的排除要**明写理由**（判据必须点名旧字段才能测它）。
- **模式**：属性读（`.label`）、构造点（`label=`）、JSON 键（`"label":`）三种形态各一条；
  另加两条**反向自检**（扫描会报 / 不误报别的字段）。
- **改名顺序**：DTO → 生产投影 → web 类型 → web 渲染 → e2e 夹具 → **再生成 OpenAPI 快照**
  （`uv run --frozen --no-sync python -B tools/gen_openapi.py`；既有
  `test_openapi_snapshot.py` 会再生成并比对，漂移即红）。
- **UI 文案不动**：列头「标签 / Label」**逐字保留**（显示文案不是字段语义，且被
  `apps/web/tests/e2e/design-outlines.json` 结构签名钉住）。
- 复现：
  `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_lineage_label_rename_is_complete.py -q`
  ⇒ 11 passed；反证：把 `row.text` 改回 `row.label` ⇒ 3 failed 点名该文件。

## 适用边界

本仓所有**改名 / 迁移 / 零命中**类判据；`tsc -b` 会在源树落 `.d.ts` 产物（实测 787 个），
类型门要用仓库既有的 `pnpm --dir apps/web run typecheck`（`tsc --noEmit`），别用 `-b`。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20261006-299-goal-031-ec04-lineage-label-rename.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20261006-299-goal-031-ec04-lineage-label-rename.md`
- 事实：`tests/tooling/test_lineage_label_rename_is_complete.py`（11 passed；两次反证注入）
  + 判词归档 `.cursor/plans/goals/evidence/GOAL-20261006-031-ec04-rename-and-zero-hit-ledger.txt`
