---
id: RECHECK-20260918-098
plan_id: PLAN-20260918-098
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-18
completed_at: 2026-09-18
reviewer: root-agent-goal-005-cycle6
baseline_ref: 1189336
checked_head: worktree
---

# RECHECK-20260918-098 — 重建能力读面（GOAL-005 cycle 6 = EC-06）

## 检查范围

PLAN-20260918-098 声称的交付面：分类器（应用层纯函数）、读面字段（API + OpenAPI + web
类型/夹具）、`/resume` 拒绝文案同源、同源文档（`CONTROL_PLANE_API.md` / `EVENT_MODEL.md`）、
用例与反证。**不在本轮**：EC-06 的 (a) 迁移/回填（`tools/snapshot_migrate.py` 仍是显式
opt-in 运营动作，本循环不跑）与 (c) "不可回填"裁决（产品决策）。

## 检查结果

| 复查项 | 检验方式 | 结果 |
| --- | --- | --- |
| 历史行与当前行在读面可区分 | 用例：自足行 vs 旧 run 形态 vs 旧事件形态三种取值 | PASS（`SELF_CONTAINED` / `REFUSED` + `missing` 点名两条装配输入 / `REFUSED` + 点名语义 digest） |
| 拒因点名事实 | 用例：`/resume` 拒绝文案含被点名的事实 | PASS（"no recorded protocol source" / "no frozen protocol body" / "lacks a semantic digest" 三条路径各有既有或新增用例） |
| 读面与拒因**同源** | 读 `run_resume.py`：两条早退与异常前缀都取自 `rebuild_readiness(run)` | PASS（结构性：`early_refusal()` / `dependency_prefix()` 是分类器方法，`run_resume` 不再自己枚举事实） |
| 判定不越界 | 读分类器：只读行上四个字段，不读文件/不解析来源 | PASS（读面无 IO；`REFUSED` 只表示"重建会被拒"，不裁决"不可回填"） |
| 反证有效 | 去掉 `manifest_semantic_digest` 判定后重跑 | PASS（**6 failed / 25 passed**，还原后 **31 passed**） |
| 既有拒绝语义未被削弱 | 既有 3 条点名用例 + e2e 收敛/漂移用例 | PASS（条件与文案逐字不变；首轮实现曾在"缺正文且缺语义 digest"的行上丢前缀 ⇒ 修的是**产品判定**（显式带出 `body_frozen`），未改断言） |
| 旧事件回填分支有覆盖 | 新增 2 条用例（`from_payload({"digest":…})` ⇒ None；该行读面点名） | PASS（此前无用例；`tests/api/test_api_restart_recovery.py` 的 run 行自带语义 digest，走不到该分支） |
| 文档同源 | `CONTROL_PLANE_API.md`（读面三态 + 诚实边界 + opt-in 运营工具）/ `EVENT_MODEL.md`（旧 payload 形态与点名） | PASS |
| 快照与前端一致 | `tools/gen_openapi.py` + `types.ts` + e2e 夹具 | PASS（快照新增 DTO 与必填字段；web lint/typecheck/unit/build/stub e2e/live e2e 全绿） |
| 规模门禁 | `test_python_source_limits.py` | PASS（935 passed；未碰 50 行/450 行阈值） |

## 反证与实测

- **反证（实跑）**：`if False and run.manifest_semantic_digest is None:`（临时去掉该事实
  判定）⇒ 三条分类器矩阵用例 + 两条读面用例 + 一条旧事件用例红（**6 failed / 25 passed**）；
  还原后 **31 passed**。
- **定向**（DSN pin 配方）：`tests/api tests/contracts tests/application tests/adapters tests/e2e`
  ⇒ **2053 passed / 7 skipped**（322.87s）。
- **web 门**：lint（`--max-warnings 0`）/ typecheck / unit **76 passed** / build /
  stub e2e **83 passed**（4.8m）/ live e2e **36 passed**（44.7s）。
- **结构判据**：`missing` 的取值集合 ⊆ `dataclasses.fields(ResearchRun)` 的字段名（用例钉住）；
  值对象不变量三条（REFUSED 必须点名 / 非 REFUSED 不得带 missing / `body_frozen` 与
  `protocol_body` 不得矛盾）。

## 告警（W）

- **W-1（只回答"输入齐不齐"）**：读面不预测重建结果——漂移校验与 preflight 仍要真跑
  `/resume` 才知道。`SELF_CONTAINED` + `REFUSED` 之外没有"重建必过"这一档，这是有意的
  （避免读面承诺它判不了的事）。
- **W-2（(a)/(c) 未做）**：本 PLAN 只做 (b)。"这些历史行要不要 re-freeze/fork"仍是运营
  决策（`tools/snapshot_migrate.py` 显式 opt-in，未接线到任何服务/Makefile target）；
  读面 `REFUSED` **不等于**"不可回填"。
- **W-3（前端未消费）**：`rebuild` 已进 TS 类型与夹具，但控制台页面暂未展示（EC-06 只要求
  读面可区分；页面呈现属产品决策）。
- **W-4（`missing` 是字段名，不是人话）**：字段名（`manifest_semantic_digest` 等）对 API
  消费者可读，但 UI 若要展示需自行映射文案；本轮不做映射层。

## 结论

**PASS_WITH_WARNINGS**。EC-06 走 (b)：把"这份记录够不够重建、缺哪条事实"做成一等读面
（`RunDetailDto.rebuild`，三态 + `missing` 点名行字段），历史行与当前行在读面**可区分**、
拒绝原因**点名事实**且与 `/resume` **同源**（同一个分类器，`run_resume` 不再自己枚举）；
旧事件形态（`manifest.frozen` 只有 `digest`）此前没有用例，本轮补上并把"落到 None 后
读面怎么回答"钉住。反证有效（去掉一条事实判定 ⇒ 6 条红）。W-1…W-4 是适用边界
（不预测重建结果、不裁决可回填性、前端未消费、字段名不做文案映射）。

## 门禁

- 定向 / web 门：见「反证与实测」。
- m0 全量：见 GOAL-005 迭代日志 cycle 6 行与「状态历史」。
