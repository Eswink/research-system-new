---
id: PLAN-20261114-113
slug: memory-last-mile
title: GOAL-113 子计划 —— 记忆的最后一米 + 压缩护栏与测量
status: DONE
created_at: 2026-11-14
updated_at: 2026-11-15
parent_goal: GOAL-20261114-113
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261115-113-memory-last-mile.md
memory_entries:
  - .cursor/memory/entries/MEM-20261115-243-canonical-rejects-float-in-manifest-bound-objects.md
---

# PLAN-20261114-113

## 背景与靶子

序 81。建档实测：记忆机制完备（9 模块 / gate 7 阶段）但全仓 200 个 run 库
`m12_memory` 全 0 —— 根因是**组合根从未注入 `memory_gate`**（缺四行装配）。
压缩不存在但当前不需要（5–12 个 view event vs 阈值 80，差一个数量级）⇒ 护栏 + 测量。

## 交付面（checkbox）

- [x] 四行装配：`OrchestrationDependencies.memory_gate` + 两组合根 + `runner_wiring`
- [x] `TaskContract.memory_export` + `MemoryExportSpec`（confidence 用 `Decimal`——
      canonical 序列化拒绝 float，实测 float 让整条链的 manifest digest 判红）
- [x] `promote_memory` 读声明 → `curator_approved=True`（`gate.py` 一行不改）
- [x] 四条判据（正例 / 零回归两条 / curator 门仍咬 / 下一轮读得到）
- [x] `research_manuscript` 声明 `memory_export: {tier: PROJECT}`；真实 run 后
      `m12_memory` 非空
- [x] condenser 护栏（两处 kwarg）+ 三条判据（在 / 不触发 / 真的会压）
- [x] view-event 与 prompt-token 只读读数进 telemetry
- [x] 文档同步（CONTEXT_ENGINE §6.1 + §9）
- [x] 宪章记账（程序表序 81、阶梯「迭代」行、两表各 3 行）
- [x] 收口资产 + `_VERIFIERS` + `IN_SCOPE`

## 实施清单

- [x] STEP-01：四行装配（dependencies / runner_wiring / composition / pg_composition）
- [x] STEP-02：声明面（domain spec + schema + loader + research_manuscript YAML）
- [x] STEP-03：晋升缝（promote_memory 迁址 + curator_approved 直通）
- [x] STEP-04：四条判据 + IG-1 链级加严
- [x] STEP-05：condenser 护栏 + 只读测量 + 两 metric 名
- [x] STEP-06：live run（F-1/F-2 修复后 SUCCEEDED）+ 读数落盘
- [x] STEP-07：文档 + 宪章 + 收口资产 + 登记

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | STEP-01/03 | test | `tests/application/run_orchestration/test_memory_export_declaration.py` | 5 passed |
| EV-02 | STEP-04 | test | `tests/integration/test_ig1_phase_runner.py` | passed（tier/scope/provenance 三向断言） |
| EV-03 | STEP-05 | test | `tests/adapters/openhands/test_session_guardrail_and_readings.py` | 5 passed |
| EV-04 | STEP-06 | digest/check | `.cursor/plans/goals/evidence/GOAL-20261114-113-live-m12-memory.json` | run `8ba73c2a` SUCCEEDED、`m12_memory`=1、渲染行逐字 |
| EV-05 | STEP-06 | test | `tests/e2e/test_direction_to_manuscript_product_path.py` | 9 passed（F-1/F-2 复绿） |
| EV-06 | STEP-07 | check | `tools/verify_goal113_closeout.py --root . --verdict-only` | 90 判词 0 failed |

## 复检

`.cursor/plans/rechecks/RECHECK-20261115-113-memory-last-mile.md`

## 验收条件

- 十条 EC 全部 PASS；
- 真实 run 的 `m12_memory` 非空且 PROJECT 档可被下一轮 `prior_knowledge` 读到；
- 全量 m0 witness 绿 + 两树复检 sha256 相同 + CI 八 job 全绿。

## 状态历史

- 2026-11-14：建档；四行装配 + 声明面 + condenser 护栏落地。
- 2026-11-15：真跑抓到 F-1（canonical 拒 float ⇒ `Decimal`）与 F-2（白名单脚本缺
  `metrics` 制品）并修复；live run `8ba73c2a` SUCCEEDED、`m12_memory` 非空且下一轮
  可读；十条 EC 全 PASS；复检 PASS_WITH_WARNINGS。

## 影响报告

- **Domain/API/schema**：`TaskContract.memory_export`（新授权声明槽位）、
  `task-contract.schema.json` 新 `memoryExport`、`OrchestrationDependencies.memory_gate`、
  两个新 metric 名（闭集词表 +2）。既有 34 份合约行为逐字不变（缺省 `None`）。
- **安全/凭据**：无新凭据面；`gate.py` 一行未改（curator 门不放宽）；
  记忆写面默认 deny（缺声明不晋升）。
- **兼容性/迁移**：无 migration；schema 新属性可选 ⇒ 旧合约照载。
- **上游**：openhands-sdk==1.42.0 的 `LLMSummarizingCondenser` 参数面
  （`keep_first`/`max_size`）与 `@observe ignore_output` 缺口（`W-1`，登记不修）。

## 状态

DONE（收口见复检文件与 GOAL 迭代日志）。
