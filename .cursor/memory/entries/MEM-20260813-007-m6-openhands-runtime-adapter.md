---
id: MEM-20260813-007
title: M6 OpenHands Runtime Adapter 实现事实
status: ACTIVE
created_at: 2026-08-13
updated_at: 2026-08-13
scope: repository
confidence: 0.9
review_after: 2026-11-13
source_plans:
  - .cursor/plans/tasks/PLAN-20260813-007-m6-openhands-runtime-adapter.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260813-007-m6-openhands-runtime-adapter.md
supersedes: []
tags: [m6, openhands, adapter, runtime, contract-suite]
---

# MEM-20260813-007 — M6 OpenHands Runtime Adapter 实现事实

## 做了什么

在 `adapters/openhands/` 实现 OpenHandsRuntimeAdapter（AgentRuntime Port 的
OpenHands SDK 实现），openhands-sdk==1.42.0 采用为 ADOPTED；真实 adapter 与
Fake 共享同一套 M5 contract suite；S7 端到端 spike（mock OpenAI-compatible
端点）通过。

关键验证事实：

1. **SDK 错误模型是事件驱动**：v1.42.0 无 `ConversationRunError` 类；错误经
   `ConversationErrorEvent`（含 ErrorClassification 闭集
   AUTH/QUOTA/RATE_LIMIT/CONFIG/TRANSIENT/AGENT_ACTION/INTERNAL/UNKNOWN +
   retryable）暴露，run() 抛错路径为 `_emit_run_limit_error` 发事件。
   error_mapping 按 classification.kind 映射 Port 错误，SDK 类型零越过边界。
2. **非知名 model + 自定义 base_url 需要 runtime model identifier 变换**：
   litellm 无法推断 provider（`get_llm_provider` 抛错），加 `openai/` 前缀
   强制 OpenAI-compatible 路由（MVP 唯一协议）；变换只存在于 llm_factory。
3. **cancel 语义实证**：SDK interrupt() 置信号、结果 PAUSED；adapter 显式
   收敛为 domain CANCELLED 终态；重复 cancel 幂等；终端后 cancel no-op。
4. **Agent.tools 要求 Tool 对象**（Pydantic 校验），非字符串列表；
   ToolDefinition 实例 name 由类名 snake_case 自动推导（`__init_subclass__`）。
5. **共享 contract suite 注册机制**：tests/contracts/registry.py
   `PORT_IMPLEMENTATIONS` 单一事实源；真实 adapter 用无参工厂
   （TestLLM 脚本化 + 隔离临时目录），通用契约测试自动复用。

## 为什么这样做

- M5R 已 pin revision v1.42.0 并审计 10 领域；M6 只做实现与契约验证，
  不重复上游研究（仅按实现暴露的问题做针对性核对）。
- OpenHands 类型严格停留在 adapter 边界（fault injection 负测覆盖
  ports/domain 零 import）；Canonical State 仍是 PostgreSQL Domain Entity。

## 怎么做与复现

1. 依赖采用：`uv add --dev openhands-sdk==1.42.0`（sdist sha256 4706ae2c…）
2. 运行测试：`uv run --frozen --no-sync python -B -m pytest -p no:cacheprovider -q tests/adapters/openhands tests/contracts`
   （192 passed）
3. S7 spike：`tests/adapters/openhands/test_spike_e2e.py`（本地 HTTP mock，
   无真实网络/凭据；断言 key 不出现在 calls/result/repr）
4. 全量回归：`python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going`
   （mypy 184 files Success；pytest 815 passed；validate_bundle PASS；
   governance PASS）

## 适用边界

- 适用于：M6 之后的 M7 Vertical Slice（runtime 侧复用）；upstream 升级评审
  （v1.42.0 → 更高版本需重跑 contract suite + upgrade gate）。
- 不适用于：其他 Runtime；M5 Port 契约本身（以 PORTS.md 为权威）；
  DockerWorkspace 容器链路（未验证，延后 M7 部署配置阶段）；
  resume Manifest compatibility（M6 会话无 resume 入口）。

## 失效与复核触发器

- 到达 `review_after`（2026-11-13）或 SDK 升级越过 v1.42.0 时先复核再引用。
- OpenHands 若新增终态 CANCELLED / 命令级 timeout / digest pin，本记忆的
  cancel/timeout/插件结论需更新。
- 架构、Schema 或 Port 契约变化时以 PORTS.md + contract suite 为准。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20260813-007-m6-openhands-runtime-adapter.md` | M6 执行与验收 |
| repository | `adapters/openhands/` | 实现位置与模块职责 |
| repository | `tests/adapters/openhands/`（59 项） | 单测 + S7 spike + fault injection |
| repository | `tests/contracts/registry.py` | 共享 contract suite 注册 |
| repository | `docs/references/upstream/M5_CORRECTIONS_LOG.md`（M6 增补 M6-1..M6-5） | mismatch 记录 |
| repository | `docs/integration/OPENHANDS_ADAPTER.md`（M6 实现状态节） | 实现事实与边界 |