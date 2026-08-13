---
id: RECHECK-20260813-007
plan_id: PLAN-20260813-007
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-08-13
completed_at: 2026-08-13
reviewer: root-agent-independent-pass
baseline_ref: PLAN-20260813-007 实施完成（M6 DoD 证据齐备，实测 192 contract + S7 spike）
checked_head: working-tree
---

# RECHECK-20260813-007 — M6 OpenHands Runtime Adapter 复检

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260813-007-m6-openhands-runtime-adapter.md`
- 验收条件：AC-01 至 AC-08（M6 用户提示词 10 项最终输出 + DoD）
- 复审目标：回答"OpenHandsRuntimeAdapter 是否真正通过 OpenHands runtime
  可靠执行一个 Research OS AgentSession，且 OpenHands 细节严格停留在
  adapter 边界？"
- 基线：计划处于实施完成状态；本次复检以工作区代码、可执行测试与
  验收条件为事实来源，不默认实现/Checklist 正确。

## 检查结果

| Gate | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| G-01 | AgentRuntime Protocol 全 6 方法 + 共享 contract suite | `pytest tests/contracts tests/adapters/openhands` 192 passed（registry 注册真实 adapter 工厂，Fake 与真实 adapter 同一套通用契约测试复用 5 项） | PASS |
| G-02 | LLM Relay 端到端 | S7 `test_spike_e2e.py`：本地 mock OpenAI 端点 → build_llm 三要素 → Agent → Conversation → safe tool → Workspace → 事件 → SUCCEEDED；mock relay 收到请求且 model 透传 | PASS |
| G-03 | Secret 边界 | S7 断言 key 不出现在 calls/result/repr；`test_llm_relay` repr/model_dump 断言；fault injection redaction 断言（错误消息含 key 被脱敏） | PASS |
| G-04 | Provider 类型零泄漏 | fault injection 负测：ports/domain 目录文本级扫描无 openhands/litellm 引用 | PASS |
| G-05 | Cancellation 矩阵 | full-adapter：run 前 cancel→CANCELLED；重复 cancel 幂等；终端后 cancel no-op；close 幂等清理；run 中 cancel 由 SDK interrupt 收敛（`_drive_until_terminal` 取消信号短路） | PASS |
| G-06 | Policy Wrapper 门禁 | tool-policy：ALLOW 放行、DENY 阻断不触达 SDK、REQUIRE_APPROVAL 发事件并阻塞、ALLOW_WITH_CONSTRAINTS 放行 | PASS |
| G-07 | Workspace 安全 | workspace：host shell 默认 deny；路径绝对化 + 根校验（../ 与绝对越界拒绝）；Docker 映射代码 + 探测 | PASS |
| G-08 | Error 映射 | fault injection 参数化：AUTH/RATE/TIMEOUT/BUDGET/RELAY_UNAVAILABLE → 正确 PortError 类型 + FailureCategory + retryable；SDK 类型零越过 | PASS |
| G-09 | Usage 归一化 | llm-relay：token/request/cost → UsageLedgerEntry；entry_id 幂等；零用量无条目 | PASS |
| G-10 | lint/typecheck/test/validators | m0 profile：ruff lint+format PASS；mypy 184 files Success；pytest 815 passed；dependency boundaries PASS；validate_bundle PASS；governance validate PASS | PASS（见下） |
| G-11 | 依赖采用 | openhands-sdk==1.42.0 dev group + uv.lock sdist sha256 4706ae2c…；UPSTREAM_COMPONENTS PLANNED→ADOPTED（resolution/license/upgrade_gate 齐备）；revision lock status ADOPTED；LICENSE_MATRIX 更新 | PASS |

## 发现与修复

| ID | 严重度 | 发现 | 处理 | 证据 |
| --- | --- | --- | --- | --- |
| R-001 | ERROR（P0） | `RuntimeEventKind` 原枚举缺 MESSAGE 投影（M5R 审计要求 message 覆盖但 Port 无对应值） | Port 最小增补 `MESSAGE = "message"`（M5_CORRECTIONS_LOG M6-1）；Fake 不产生该事件，contract 不受影响 | `packages/application/ports/agent_runtime.py` |
| R-002 | MAJOR（P1） | SDK 无 ConversationRunError；错误模型为事件驱动（M5R 记"双通道"与实测不符） | error_mapping 按 ErrorClassification.kind 闭集映射（M6-2） | `adapters/openhands/error_mapping.py` + M5_CORRECTIONS_LOG M6-2 |
| R-003 | MAJOR（P1） | 非知名 model + 自定义 base_url 时 litellm 拒绝请求（S7 实证；M5R R-08 预测命中） | llm_factory `resolve_runtime_model_name` 探测失败加 `openai/` 前缀（M6-3） | `adapters/openhands/llm_factory.py` + test_llm_relay |
| R-004 | MAJOR（P1） | Agent.tools 要求 Tool 对象；ToolDefinition 实例 name 自动推导 | `_default_agent` 装配 `Tool(name=...)`；自定义工具按 snake_case 推导名（M6-4/M6-5） | `adapters/openhands/runtime_adapter.py` |
| R-005 | 注意 | 首次 m0 回归 format/tests 失败（新文件未格式化 + runtime_adapter 335 行/usage_mapping 67 行超限） | ruff format；runtime_adapter 拆分 session_types（状态映射/依赖结构独立模块）；usage_mapping 拆分 helper | 拆分后 815 passed + format PASS |

## 例外（非本阶段引入，不在授权范围）

- `framework/run_cursor_hook_evals`：会话前已存在的未提交用户改动
  （.cursor/hooks/distillation_gate.py + run_cursor_hook_evals.py +
  .cursor/experience/）引用不存在的经验条目 EXP-20260812-999，
  HOOK EVAL FAILED。M6 未触碰这些文件；CI 全量回归需用户在
  该改动闭环后重跑。
- DockerWorkspace 容器链路 / MCP live / resume Manifest check：明确不在
  M6 范围（M6 计划 §7 Entry Contract 记录为 M7 前置）。

## 独立复审记录（2026-08-13 二次，端到端完成度复审）

复审者独立重跑/重验后追加；本次复审不默认 M6 开发窗口结论，以当前代码、
M5 契约、pinned v1.42.0 源码为事实来源，并执行 Fault Injection 闭环。

### 复审结论

M6 DoD 逐项核对 PASS（8/8）；M6 最终状态 = **PASS**。M5 Port 零结构修正
（修复全部为 adapter 层：M5_CORRECTIONS_LOG M6-6 至 M6-12）。

### 复审新增证据

| Gate | 复审检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| R-G-01 | Policy 门禁全链路（agent loop + execute_tool 直通面） | `tests/adapters/openhands/test_policy_enforcement.py` 5 passed：DENY 阻断不触达 executor、REQUIRE_APPROVAL 发事件、ALLOW 放行、gated 直通 DENY/ALLOW | PASS（修复 M6-6） |
| R-G-02 | Usage 入 BudgetLedger（接线 + 失败不阻断） | `test_usage_ledger.py` 3 passed：ledger 收到 entry、记账失败 run 仍 SUCCEEDED、无 ledger no-op | PASS（修复 M6-7） |
| R-G-03 | fork override 生效 | `test_fork_override.py` 3 passed：model_override 重建 LLM、无 override 深拷贝、缺注入拒绝 | PASS（修复 M6-8） |
| R-G-04 | 错误双通道归一化 | `test_error_cancel_integration.py` 错误 4 项：LLM 异常 → FAILED 事件单发、SDK 类型零越过、timeout → TransientPortError、secret 不进事件/错误 | PASS（修复 M6-9/M6-10） |
| R-G-05 | run 中 cancel（真实并发） | `test_cancel_during_run_converges_cancelled` + `test_cancel_running_then_cleanup`：工具执行中 cancel → CANCELLED；cancel 后 close 幂等 | PASS |
| R-G-06 | 事件流完整性 | 实测 `session.created → session.started → message → message → session.succeeded`；SESSION_SUCCEEDED 计数 1 | PASS（修复 M6-11） |
| R-G-07 | 全量回归 | pytest 840 passed；mypy strict 183 files Success；ruff PASS；lint-imports domain/relay 8 passed；validate_bundle PASS；governance validate PASS | PASS |
| R-G-08 | Pinned upstream 一致性 | clone head 391fbb8d = v1.42.0；uv.lock openhands-sdk 1.42.0；PyPI sdist sha256 4706ae2c… 实测一致；litellm 注释修正为 1.96.2（uv.lock 实测） | PASS |

### 复审例外（非阻断）

- 上游 GitHub latest 已发布 v1.42.1（2026-08-12）；M6 保持 v1.42.0 pin
  符合 M5R revision lock，升级按 Upgrade Gate 执行（风险登记）。
- `packages/domain/enums.py::BackendKind.OPENHANDS_NATIVE` 为 M1 既有枚举
  值（非类型依赖、非 M6 引入）；名称含 OPENHANDS 属命名泄漏候选，改名为
  Domain 抽象（如 NATIVE_AGENT_RUNTIME）需用户授权，不阻塞 M6。
- DockerWorkspace 容器链路 / MCP live / resume Manifest check：仍为
  M7 前置，不在 M6 范围。

## 结论

M6 DoD 逐项核对 PASS；M6 最终状态 = **PASS**（除上述会话前既有
hook eval 例外，该例外与 M6 变更无关）。

M7 Reliable Vertical Slice readiness = **NOT READY**（M7 需先补：
ToolResolver P1 真实链、REQUIRE_APPROVAL 交互式审批循环、DockerWorkspace
全量容器验证、M3 fallback 执行、Evidence Ledger；计划已停在 M6 边界，
不自动开始 M7）。