---
id: PLAN-20260813-007
slug: m6-openhands-runtime-adapter
title: M6 OpenHands Runtime Adapter
status: DONE
created_at: 2026-08-13
updated_at: 2026-08-13
cursor_plan_uri: c:\Users\googl\.cursor\plans\m6_openhands_runtime_adapter_9d354088.plan.md
owners:
  - root-agent
authorization:
  source: user-request
  ref: "M6 OpenHands Runtime Integration 启动提示词（用户明确授权实施）"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260813-007-m6-openhands-runtime-adapter.md
memory_entries:
  - MEM-20260813-007
---

# PLAN-20260813-007 — M6 OpenHands Runtime Adapter

## 目标

Research OS AgentSession 能通过 OpenHands runtime（openhands-sdk v1.42.0）
可靠执行：AgentRuntime Port → OpenHandsRuntimeAdapter → OpenHands SDK →
用户 LLM Relay → Tools / Workspace / Runtime Events，所有 OpenHands 细节
严格停留在 `adapters/openhands/` 边界。

## 范围

- 包含：adapter 实现（runtime/llm/tool/policy/event/error/workspace/usage
  八个模块）；M5 Contract Suite 共享复用；S7 端到端 spike；fault
  injection；cancellation/error/security 验证；文档收口。
- 不包含：M7 Vertical Slice（Protocol Compiler/Team Resolver/Evidence
  Ledger/Claim Evaluation/Research Workflow）；MCP live 集成；DockerWorkspace
  容器链路验证；resume Manifest compatibility 检查。

## 架构与数据流

```text
AgentRuntime Port (packages/application/ports/agent_runtime.py)
→ OpenHandsRuntimeAdapter (adapters/openhands/runtime_adapter.py)
  → llm_factory (LLMEndpoint/ModelDefinition/SecretValue → OpenHands LLM)
  → tool_mapping + policy_wrapper (frozen tool set + PolicyEvaluator 门禁)
  → workspace_adapter (LocalWorkspace 主路径；host shell 默认 deny)
  → event_mapping / error_mapping (SDK 事件/错误 → Port 归一化)
  → usage_mapping (ConversationStats → UsageLedgerEntry)
→ OpenHands SDK v1.42.0（PyPI openhands-sdk==1.42.0）
```

Canonical State 不变：PostgreSQL Domain Entity 是业务真相；OpenHands
Conversation 只是 runtime reference。

## 验收条件

- [x] AC-01：OpenHandsRuntimeAdapter 实现 AgentRuntime Protocol 全 6 方法，
      通过共享 contract suite（Fake 与真实 adapter 同一套通用契约测试）。
- [x] AC-02：LLM Relay 三要素（base_url/api_key/model）端到端可用（S7 mock
      端点实证）；无厂商绑定；API Key 不进 Agent Context/日志/Domain
      Event/Artifact/Manifest 明文/exception。
- [x] AC-03：cancel 语义显式收敛 CANCELLED 终态（R-01）；重复 cancel 幂等；
      终端后 cancel no-op；cancel 后 close 幂等清理。
- [x] AC-04：Policy Wrapper 独占 execute_tool 直通面（R-03）；DENY 阻断不
      触达 SDK；REQUIRE_APPROVAL 发 approval.requested 事件并阻塞。
- [x] AC-05：错误映射覆盖 model failure/auth/timeout/tool failure/workspace
      failure/policy denied/cancellation/malformed/upstream SDK failure；
      SDK 异常类型零越过边界（负测）。
- [x] AC-06：Workspace LocalWorkspace 路径绝对化 + 根校验（R-17）；host
      shell 默认 deny（R-04）；DockerWorkspace 映射 + 探测式 smoke。
- [x] AC-07：Usage 归一化入 BudgetLedger（token/request/cost）；ledger 仍
      Research OS 拥有。
- [x] AC-08：全量回归绿（ruff/mypy strict/pytest/validators/m0 profile）；
      openhands_sdk=ADOPTED 且 bundle validator PASS。

## 实施清单

- [x] STEP-01：openhands-sdk==1.42.0 入 pyproject + uv lock；
      UPSTREAM_COMPONENTS.yaml PLANNED→ADOPTED；LICENSE_MATRIX 更新；
      revision lock status 更新；validate_bundle.py PASS。
- [x] STEP-02：Contract Suite 拆分（通用契约参数化 + Fake 专属 advance）；
      Fake 全绿。
- [x] STEP-03：adapter-core（runtime_adapter/event_mapping/error_mapping +
      单测）。
- [x] STEP-04：llm_factory + usage_mapping（含 runtime model identifier
      变换 M6-3）。
- [x] STEP-05：tool_mapping + policy_wrapper（DENY/REQUIRE_APPROVAL）。
- [x] STEP-06：workspace_adapter（LocalWorkspace 路径归一化 + host shell
      deny；Docker 映射 + 探测）。
- [x] STEP-07：full-adapter（cancellation 全矩阵）。
- [x] STEP-08：S7 端到端 spike（mock OpenAI 端点）。
- [x] STEP-09：registry 注册真实 adapter + fault injection；全绿。
- [x] STEP-10：文档收口（OPENHANDS_ADAPTER.md 实现状态、BACKLOG 勾选、
      M5_CORRECTIONS_LOG 增补、INDEX 同步、all-plan 计划、recheck
      RECHECK-20260813-007 PASS、工程记忆 MEM-20260813-007、
      m0 profile 全量回归：mypy 184 files Success / pytest 815 passed /
      ruff PASS / validate_bundle PASS / governance PASS）。

## 子代理使用

Subagent 默认不启用。需要并行时，每个 wave 最多 3 个；多 wave 必须在前一波
完成并整合后才可开始。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| — | 未使用 | 0 | — | — |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | STEP-01 | check | `validate_bundle.py` | PASS（2026-08-13） |
| EV-02 | STEP-01 | file | `pyproject.toml` dev group `openhands-sdk==1.42.0`；`uv.lock` sdist sha256 4706ae2c… | 一致 |
| EV-03 | STEP-02 | test | `pytest tests/contracts` | 128 passed（拆分后） |
| EV-04 | STEP-03 | test | `pytest tests/adapters/openhands` | 15 passed（core） |
| EV-05 | STEP-04 | test | `pytest tests/adapters/openhands/test_llm_relay.py` | 5 passed |
| EV-06 | STEP-05 | test | `pytest tests/adapters/openhands/test_tool_policy.py` | 8 passed |
| EV-07 | STEP-06 | test | `pytest tests/adapters/openhands/test_workspace.py` | 7 passed |
| EV-08 | STEP-07 | test | `pytest tests/adapters/openhands/test_full_adapter.py` | 11 passed |
| EV-09 | STEP-08 | test | `pytest tests/adapters/openhands/test_spike_e2e.py` | 1 passed（S7 链路） |
| EV-10 | STEP-09 | test | `pytest tests/contracts` + `tests/adapters/openhands` | 192 passed（共享复用 5 项） |
| EV-11 | STEP-10 | check | m0 profile 全量回归 | mypy 184 files Success；pytest 815 passed；ruff PASS；validate_bundle PASS；governance PASS（hook eval 例外见 RECHECK） |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-13 | RuntimeEventKind 增补 MESSAGE（M6-1） | OpenHands MessageEvent 是会话消息投影，Port 枚举原缺对应值 | 最小 Port 增补；Fake 不产生该事件，contract 不受影响 |
| 2026-08-13 | 错误模型修正为事件驱动（M6-2） | SDK 无 ConversationRunError 类；错误经 ConversationErrorEvent + ErrorClassification 闭集暴露 | error_mapping 按 kind 映射 |
| 2026-08-13 | 非知名 model 加 openai/ 前缀（M6-3） | litellm 无法推断 provider（S7 实证） | 变换只存在于 llm_factory |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-13 | — | IN_PROGRESS | 用户授权的 Cursor Plan 落地执行 | M6 启动提示词 |

## 影响报告

- Domain/API/schema：RuntimeEventKind 增补 `MESSAGE`（Port 输出枚举，最小
  必要修正；无 schema 变化）。
- 安全/凭据：API Key 仅经 CredentialResolver 密封注入；S7 断言 key 不出现在
  calls/result/repr；host shell 默认 deny。
- 兼容性/迁移：openhands-sdk==1.42.0 进入 dev group；mypy strict 通过；
  contract suite 共享复用，无既有行为变化。
- 上游版本：openhands_sdk PLANNED→ADOPTED（UPSTREAM_COMPONENTS.yaml）；
  upgrade gate 按 UPSTREAM_POLICY.md 执行。
- 下一项任务：M7 Reliable Vertical Slice（需 ToolResolver P1 链、审批循环、
  DockerWorkspace 全量验证等；见 M6 计划 §7 Entry Contract）。