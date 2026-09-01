---
id: PLAN-20260831-026
title: 确定性并行 Agent 编排（Cursor SDK 编排器）
status: DONE
created_at: 2026-08-31
updated_at: 2026-08-31
subagent_parallel_limit: 3
approval:
  source: "用户批准的 Cursor Plan Mode 计划（c:/Users/googl/.cursor/plans/确定性并行编排_8eeb3644.plan.md，2026-08-31 确认）"
latest_recheck: ".cursor/plans/rechecks/RECHECK-20260831-026-deterministic-parallel-orchestration.md"
memory_entries: []
---

# PLAN-20260831-026 — 确定性并行 Agent 编排

计划来源：用户在 Cursor Plan Mode 批准的计划（批准记录见上方 `approval.source`）。
背景：父模型（含 GPT 系）对"单条消息批量发出多个 Task 调用"的遵循是 best-effort，
需要运行时保证的并行 Agent 能力；约束是不得放宽 3 路上限/no-nesting/安全门禁。

## 验收条件

- AC-01：GPT 父 Agent 不再需要单消息批量 Task 调用即可获得并行 Agent 运行（TypeScript
  `@cursor/sdk` 编排器实际并发启动多个独立会话）。
- AC-02：每 wave 最多 3、超 3 分波顺序执行、无累计上限、禁止嵌套。
- AC-03：区分启动失败/运行失败/取消；单项失败不污染他项；句柄全路径释放。
- AC-04：请求/解析模型、agent/run/request id、重叠区间、digest 可审计；模型缺失或
  静默 fallback 时 fail closed。
- AC-05：默认输出脱敏（无 prompt/结果正文/key/环境变量/workspace 内容）；只读任务不修改工作树。
- AC-06：确定性单测不依赖真实 LLM/网络/凭据；手工 smoke 标记 NOT VERIFIED 而非伪造 PASS。
- AC-07：SDK 版本、digest、许可证、升级门禁在 package.json/lockfile/UPSTREAM/许可证/qualification 一致。
- AC-08：Rule/Knowledge/Hook 只把模型行为记为 caveat，无 GPT 特例；三路上限/no-nesting/fail-closed 不变。
- AC-09：相关治理/Framework/TypeScript/回归校验通过；发布 Manifest 由 release 流程管理。

## 实施清单

- [x] 固定 `@cursor/sdk@1.0.30`（exact）入 `package.json`/`pnpm-lock.yaml`；登记
  `UPSTREAM_COMPONENTS.yaml`（cursor_sdk，NPM 分支）、`LICENSE_MATRIX.md`、
  `docs/references/upstream/CURSOR_SDK_QUALIFICATION.md`、`docs/INDEX.md`；`SOURCES.yaml` 增 T1 源 `cursor-sdk-typescript`。
- [x] `validate_bundle.py` 增加 NPM 来源 ADOPTED 分支（与 PyPI 分支同等强度：exact pin、
  lockfile 条目、tarball sha256、license/gate/matrix）+ 回归测试 `tests/tooling/test_validate_bundle_npm.py`。
- [x] 实现 `.cursor/skills/parallel-agent-orchestration/`：types/waves/model-preflight/runner/sdk-adapter/cli/fakes；
  三路 wave、`Promise.allSettled` 失败隔离、model preflight 与 drift fail-closed、SIGINT 取消收敛、脱敏摘要。
- [x] Skill（`disable-model-invocation: true`）与 `pnpm run agents:parallel` / `agents:parallel:test` 脚本；
  tsconfig/eslint/prettier 纳入。
- [x] 治理同步：`10-agent-delegation.mdc`、`SUBAGENT_DESIGN.md`、`KNOWN_CAVEATS.md`、
  `CURSOR_PRIMITIVES.md`、`knowledge/INDEX.md`、`session_context.py`、`CURSOR_COMPATIBILITY.yaml`（新增
  `sdk_parallel_wave`/`sdk_model_catalog` 探针声明）；Hook 三路上限与 `framework.json` 未改。
- [x] 确定性单测 15 项（AgentFactory fake）与 NPM 校验测试 8 项全绿；完整门禁见 recheck。

## 证据

- 复检：`.cursor/plans/rechecks/RECHECK-20260831-026-deterministic-parallel-orchestration.md`
  （G-01..G-06 逐项命令输出、AC-01..AC-09 映射、Findings F-01..F-04）。
- 上游资格：`docs/references/upstream/CURSOR_SDK_QUALIFICATION.md`（分辨率、许可证、
  已验证面、NOT VERIFIED 清单、风险与升级门禁）。
- 工程记忆：无可复用事实——模型行为差异与 SDK 运行时能力分别由 KNOWN_CAVEATS caveat
  与 qualification 文档承载，未验证的运行时行为不写入 `.cursor/memory/`。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-08-31 | DRAFT → APPROVED | 用户在 Plan Mode 批准计划并指示执行 |
| 2026-08-31 | IN_PROGRESS | SDK 固定、编排器/Skill/测试/治理文档落地 |
| 2026-08-31 | VERIFYING → DONE | RECHECK-20260831-026 = PASS_WITH_WARNINGS（两处 WARNING 均为并行 M16 会话共享工作区状态，非本任务引入） |

## 影响报告

- 改动：见 recheck 冻结范围白名单；产品 Domain/Application/API/Schema/Canonical State 零改动。
- lint/typecheck/test：见 recheck G-03（TypeScript profile 9/9、单测 15/15、NPM 测试 8/8、
  framework/hook/learning evals PASS；全量 pytest 2558 passed，2 个失败均为并行 M16 提交引入的
  pre-existing 状态，归属证据见 recheck F-01/F-02）。
- Domain/API/schema 变化：无。
- 安全/凭据变化：新增编排 CLI 仅接受环境变量 `CURSOR_API_KEY`，摘要默认脱敏，沙盒与只读工具集启用；
  未降低任何既有 fail-closed 门禁。
- 兼容性/迁移风险：`@cursor/sdk` 为 beta 上游，升级走 `UPSTREAM_COMPONENTS.yaml` 门禁；
  运行时并发/沙盒负测待真实凭据 smoke（NOT VERIFIED）。
- 上游版本影响：Node 22.18/TS 6.0.3 兼容；`@statsig/js-client` 遥测面已登记 caveat。
- 下一项任务：手工 smoke（待用户提供临时 key）；M16 会话收口其共享工作区回归。
