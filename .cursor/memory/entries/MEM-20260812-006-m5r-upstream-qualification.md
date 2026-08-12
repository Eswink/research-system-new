---
id: MEM-20260812-006
title: M5R OpenHands 源码审计与 M6 Adapter 承接边界
status: ACTIVE
created_at: 2026-08-12
updated_at: 2026-08-12
scope: repository
confidence: 0.9
review_after: 2026-11-12
source_plans:
  - .cursor/plans/tasks/PLAN-20260812-006-m5r-upstream-qualification.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260812-006-m5r-upstream-qualification.md
supersedes: []
tags: [m5r, upstream, openhands, adapter, port-validation]
---

# MEM-20260812-006 — M5R OpenHands 源码审计与 M6 Adapter 承接边界

## 做了什么

以 OpenHands Software Agent SDK v1.42.0（commit `391fbb8d`，MIT）真实源码 +
6 个 executable spike（全部 mock credential）对 M5 的 14 个 Port 做现实校验，
裁决 M5R = PASS、M6 readiness = READY，零 Port 代码修正。

关键验证事实：

1. **cancel 语义**：OpenHands `interrupt()` 结果为 PAUSED（可恢复），无终态
   CANCELLED（`ConversationExecutionStatus`）；重复 run 幂等返回同一终态。
   Research OS cancel→CANCELLED 是 Port 契约，adapter 必须显式收敛。
2. **resume 语义**：OpenHands resume = 显式传 conversation_id + persistence_dir
   重新构造（`ConversationState.create` open-or-create + `agent.verify` 校验
   类与工具集）；未传 id 则新建会话。
3. **LLM 三要素**：`LLM(model/base_url/api_key)` 直接映射 M3 的
   LLMEndpoint/ModelDefinition；自定义 base_url 原样透传；litellm kwargs 由
   SDK 在请求层组装（`LLMProvider` kwargs 无 api_base 字段）。
4. **安全边界**：`execute_tool()` 官方明言绕过 confirmation/security；
   LocalWorkspace 是 host shell；插件 pin 仅 commit-SHA 无 digest——全部必须
   Research OS 外层强制（AGENTS.md §5/§9 成立）。
5. **Port 边界**：AgentRuntime/ModelGateway/ToolProvider/WorkspaceBackend/
   ExecutionBackend 需 adapter 承接（cancel/resume/安全/lease/snapshot 为
   主要映射点）；其余 9 个 Port 完全 Research OS 自有；SWE-ReX 对照确认
   命令执行独立于 workspace 是通用模式。

## 为什么这样做

- 用真实 upstream 证据攻击 M5 抽象，而非 README 推断；结论全部可追溯到
  file:path:symbol 与 spike 输出。
- 不因"像 OpenHands"重写架构：5 项候选 Port 修正全部驳回（驳回理由见
  M5_CORRECTIONS_LOG.md），差异移交 adapter 层承接。
- revision lock 独立成文而非写入 UPSTREAM_COMPONENTS.yaml（validator 禁止
  PLANNED 组件声明采用证据）。

## 怎么做与复现

1. clone：`git clone --depth 1 --branch v1.42.0 https://github.com/OpenHands/software-agent-sdk d:\upstream\openhands-software-agent-sdk`
2. spike 环境：`uv venv d:\upstream\.venv-sdk --python 3.12` +
   `uv pip install --python d:\upstream\.venv-sdk\Scripts\python.exe -e d:\upstream\openhands-software-agent-sdk\openhands-sdk`
3. 运行 spike：`d:\upstream\.venv-sdk\Scripts\python.exe tools\upstream-spikes\S{n}_*.py`
   （S1-S6 全部 PASS；TestLLM 脚本化响应驱动 run 循环，无需真实 LLM）
4. 校验命令：`uv run --frozen python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0`
   （18/18 PASS；pytest 732；mypy 166 files；双 validator PASS）

## 适用边界

- 适用于：M6 OpenHandsRuntimeAdapter 实施（以 M6_ADAPTER_DESIGN_NOTES.md +
  M6_RISK_REGISTER.md 为承接清单）；后续 upstream 升级评审（revision lock）。
- 不适用于：其他 Runtime（Temporal/Codex/ACP 未审计）；非 OpenHands 的
  Port 校验结论；M5 契约本身（以 PORTS.md 为权威，本记忆是校验记录）。

## 失效与复核触发器

- 到达 `review_after`（2026-11-12）或 SDK 版本升级越过 v1.42.0 时先复核
  再引用（周更频率，风险 R-13）。
- OpenHands 若新增终态 CANCELLED / 会话级 timeout / digest pin，本记忆的
  cancel/resume/插件结论需更新。
- 架构、Schema 或 Port 契约变化时以 PORTS.md + contract suite 为准。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20260812-006-m5r-upstream-qualification.md` | M5R 执行与裁决 |
| recheck | `.cursor/plans/rechecks/RECHECK-20260812-006-m5r-upstream-qualification.md` | AC-01 至 AC-08 独立核对 PASS |
| repository | `docs/references/upstream/OPENHANDS_SOURCE_AUDIT.md` | 10 领域 file:path:symbol 证据 |
| repository | `docs/references/upstream/M5_PORT_COMPATIBILITY_MATRIX.md` | 14 Port 标记 |
| repository | `docs/references/upstream/M6_READINESS_REPORT.md` | M5R=PASS / M6=READY |
| repository | `tools/upstream-spikes/` + `d:\upstream\s1-s6.out` | spike 执行结果（全 PASS） |
| repository | `d:\upstream\openhands-software-agent-sdk` HEAD=`391fbb8d` | 研究 revision 锁定 |