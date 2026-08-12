---
id: PLAN-20260812-006
slug: m5r-upstream-qualification
title: M5R Upstream Source Intelligence & Runtime Qualification
status: DONE
latest_recheck: .cursor/plans/rechecks/RECHECK-20260812-006-m5r-upstream-qualification.md
memory_entries:
  - .cursor/memory/entries/MEM-20260812-006-m5r-upstream-qualification.md
created_at: 2026-08-12
updated_at: 2026-08-12
cursor_plan_uri: "m5r-upstream-qualification"
owners:
  - root-agent
authorization:
  source: cursor-plan
  ref: "M5R — Upstream Source Intelligence & Runtime Qualification（用户批准，planUri m5r_upstream_qualification_0948dcd2）"
subagent_parallel_limit: 3
---

# PLAN-20260812-006 — M5R Upstream Source Intelligence & Runtime Qualification

## 目标

以真实 OpenHands Software Agent SDK 源码与最小可执行实验对 M5 的 14 个 Port
Contract 与 Fake Implementations 做现实校验，产出可追溯的源码审计、Port 兼容
矩阵、证据驱动的必要修正与 M6 readiness 裁决。本阶段不实现正式 M6
OpenHandsRuntimeAdapter。

核心链路：

```text
真实 upstream 源码
→ 可追溯源码调查
→ executable spike
→ Research OS Port reality check
→ Adapter mapping
→ 风险与差异分析
→ M6 readiness
```

## 范围

- 包含：OpenHands Software Agent SDK 源码级研究（v1.42.0 / 391fbb8d）、
  14 Port 兼容矩阵、executable spikes（mock credential）、证据驱动的 M5 最小
  修正、M6 Adapter Design Notes / Risk Register / Readiness Report、
  machine-readable upstream revision lock、经验沉淀（EXP-20260812-002）。
- 不包含：实现 M6 OpenHandsRuntimeAdapter；将 openhands-sdk 加入 uv.lock；
  upstream 源码混入主代码树；fork/修改 upstream；将 OpenHands 类型反向写入
  Domain；向 UPSTREAM_COMPONENTS.yaml 写入 PLANNED 禁止的采用证据字段；
  真实用户凭据与高风险外部操作；Docker 类 spike（门控确认后单独执行）。

## 架构与数据流

```text
d:\upstream\openhands-software-agent-sdk（v1.42.0 隔离 clone，只读）
d:\upstream\.venv-sdk（独立 spike 环境，不入仓库 uv.lock）
→ 源码审计（3 路并行子代理，Wave A）
→ 14 Port Compatibility Matrix（docs/references/upstream/）
→ executable spikes（tools/upstream-spikes/，mock credential）
→ 证据驱动的 M5 最小修正（pytest + m0 profile + 双 validator 回归）
→ M6 readiness 裁决（PASS/FAIL + READY/NOT READY），停止在阶段边界
```

Domain 边界不变：OpenHands 类型不得进入 packages/domain；
Port 输入输出只使用 packages.domain 类型与本包 DTO（M5 契约资产）。

## 验收条件

- [x] AC-01：官方仓库以 v1.42.0 / commit `391fbb8d` 克隆至仓库外隔离位置；
  revision lock 机器可读；MIT 许可证据记录。
- [x] AC-02：10 个研究领域均有 file:path:symbol 级证据，结论可追溯到具体
  源码/测试/commit。
- [x] AC-03：14 个 Port 全部有兼容矩阵标记（DIRECT_MAPPING /
  ADAPTER_REQUIRED / SHIM_REQUIRED / RESEARCH_OS_OWNED / NOT_SUPPORTED /
  NEEDS_SPIKE）与证据。
- [x] AC-04：spike 全部以 mock credential 执行并保存命令与结果；每个 spike
  有明确结论是否足以支撑 Adapter 决策；不可执行项记录原因。
- [x] AC-05：任何 M5 修正均有上游证据驱动；修正后 pytest + m0 profile +
  双 validator 全绿。
- [x] AC-06：docs/INDEX.md / CHANGELOG.md / BACKLOG.md 更新；artifact 交叉
  引用完整。
- [x] AC-07：独立 recheck PASS；M5R 与 M6 readiness 裁决明确；未开始 M6。
- [x] AC-08：EXP-20260812-002 更新（occurrences +1 + 本会话证据）且
  INDEX 同步；未新建重复条目；未擅自晋升 Rule/Skill。

## 实施清单

- [x] STEP-00：基线冻结——git HEAD c31c8b7；m0 profile 18/18 PASS；
  pytest 732 passed；mypy 166 files Success；双 validator PASS。
- [x] STEP-01：计划登记——本文件 + ALL_PLAN Active 索引。
- [x] STEP-02：经验沉淀——EXP-20260812-002 occurrences 2→3 + 本会话
  复现证据（source_refs 追加），INDEX 同步（Summary 不变）。
- [x] STEP-03：上游获取——clone v1.42.0 到 d:\upstream\；记录 LICENSE/
  revision/sdist digest；建 d:\upstream\.venv-sdk（python 3.12）。
- [x] STEP-04：OPENHANDS_REVISION_LOCK.yaml + LICENSE_MATRIX.md revision
  行 + docs/INDEX.md 登记。
- [x] STEP-05：Wave A 三路并行源码审计（A1 Agent/Conversation/Events、
  A2 LLM/Tools/MCP、A3 Workspace/Context/Persistence/Security）。
- [x] STEP-06：综合审计产物 OPENHANDS_SOURCE_AUDIT.md；Wave B 未启动
  （A1/A2/A3 证据已覆盖全部 mismatch 判定点）。
- [x] STEP-07：M5_PORT_COMPATIBILITY_MATRIX.md（14 Port 标记 + 证据）。
- [x] STEP-08：executable spikes S1-S6（tools/upstream-spikes/ + README，
  mock credential，全 PASS）。
- [x] STEP-09：SWE-ReX README 级对照（ExecutionBackend 独立抽象为通用
  模式）；Cline 未纳入（REFERENCE_ONLY，无需对照）。
- [x] STEP-10：M5 修正评估——零代码修正（M5_CORRECTIONS_LOG.md 记录
  5 项候选驳回）；m0 profile 18/18 PASS 回归。
- [x] STEP-11：产物收口——M5_CORRECTIONS_LOG / M6_ADAPTER_DESIGN_NOTES /
  M6_RISK_REGISTER / M6_READINESS_REPORT；INDEX/CHANGELOG/BACKLOG 更新。
- [x] STEP-12：独立 recheck（RECHECK-20260812-006）PASS → 计划 DONE →
  M5R = PASS、M6 readiness = READY，停止在阶段边界。

## 子代理使用

Wave A（Phase 2）三路并行；Wave B 按 mismatch 需要。每 wave ≤3；
前一波完成并整合后才可开始下一波；禁止嵌套委派。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| A | Agent/Conversation/Events、LLM/Tools/MCP、Workspace/Context/Persistence/Security | 3 | done | OPENHANDS_SOURCE_AUDIT.md（A1/A2/A3 输出经根代理综合与交叉核对） |
| B | 定向深挖（cancel/resume/fork 等 mismatch） | 0 | 未启动 | 不适用：Wave A 证据已覆盖全部 mismatch 判定点（cancel→PAUSED、resume open-or-create、fork 语义均有源码+测试+spike 佐证） |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-00 | STEP-00 | check | `uv run --frozen python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0` | 18/18 PASS；pytest 732；mypy 166；双 validator PASS |
| EV-01 | STEP-03 | git | `git clone --depth 1 --branch v1.42.0 https://github.com/OpenHands/software-agent-sdk d:\upstream\openhands-software-agent-sdk` | HEAD=`391fbb8d`；LICENSE=MIT |
| EV-02 | STEP-04 | file | `docs/references/upstream/OPENHANDS_REVISION_LOCK.yaml` | 存在；repo/revision/license/digest 齐备 |
| EV-03 | STEP-05/06 | file | `docs/references/upstream/OPENHANDS_SOURCE_AUDIT.md` | 存在；10 领域 + file:path:symbol 证据 |
| EV-04 | STEP-07 | file | `docs/references/upstream/M5_PORT_COMPATIBILITY_MATRIX.md` | 存在；14 Port 标记 + 证据 + 汇总 |
| EV-05 | STEP-08 | spike | `tools/upstream-spikes/` S1-S6 | 全 PASS（s1-s6.out 共 9 处 PASS）；mock credential |
| EV-06 | STEP-09 | 对照 | SWE-ReX README（官方） | ExecutionBackend 独立为通用模式 |
| EV-07 | STEP-10 | file | `docs/references/upstream/M5_CORRECTIONS_LOG.md` | 零代码修正；5 项候选驳回 |
| EV-08 | STEP-11 | file | M5_CORRECTIONS_LOG / M6_ADAPTER_DESIGN_NOTES / M6_RISK_REGISTER / M6_READINESS_REPORT | 全部存在 |
| EV-09 | STEP-12 | recheck | `RECHECK-20260812-006` | PASS（AC-01 至 AC-08 全核） |
| EV-10 | STEP-02 | file | `.cursor/experience/entries/EXP-20260812-002.md` | occurrences=3 + 本会话 source_ref |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-12 | 初始化 | 用户批准的 Cursor Plan | 无 |
| 2026-08-12 | revision lock 独立成文（docs/references/upstream/）而非写入 UPSTREAM_COMPONENTS.yaml | validator 禁止 PLANNED 组件声明 resolution/license/upgrade_gate | 采用证据等 M6 ADOPTED 时再登记 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-12 | — | APPROVED | 用户确认 M5R Cursor Plan（planUri m5r_upstream_qualification_0948dcd2） | Cursor Plan |
| 2026-08-12 | APPROVED | IN_PROGRESS | 基线冻结完成（EV-00） | m0 profile 18/18 PASS |
| 2026-08-12 | IN_PROGRESS | VERIFYING | STEP-00 至 STEP-12 完成，DoD 证据齐备；DONE 需独立 recheck 通过 | EV-01 至 EV-10 |
| 2026-08-12 | VERIFYING | DONE | 独立复检 RECHECK-20260812-006 PASS（AC-01 至 AC-08 全核，0 处高于 INFO 的发现） | RECHECK-20260812-006 |

## 影响报告

- Domain/API/schema：无变化（零代码修正；M5 14 Port 契约保持冻结）。
- 安全/凭据：spike 全部 mock credential；无真实 secret 入仓；revision lock
  不含凭据；安全承接点（execute_tool 直通、host shell、digest pin）移交
  M6_ADAPTER_DESIGN_NOTES + M6_RISK_REGISTER。
- 兼容性/迁移：openhands-sdk 保持 PLANNED（不入 uv.lock）；研究锁定 v1.42.0 /
  391fbb8d；M6 采用时按 Upgrade Gate + contract suite 验收。
- 上游版本：revision lock 建立（docs/references/upstream/
  OPENHANDS_REVISION_LOCK.yaml）；周更风险登记 R-13。
- 下一项任务：M6 OpenHands Runtime Integration（本阶段停止，未开始）。