---
id: RECHECK-20260814-013
plan_id: PLAN-20260814-012
attempt: 2
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-08-14
completed_at: 2026-08-14
reviewer: independent-audit-pass
baseline_ref: RECHECK-20260814-012 PASS（M8 自报完成）
checked_head: working-tree
---

# RECHECK-20260814-013 — M8 独立复审（端到端完成度复审）

## 复审定位

独立于开发窗口的 Plan/Checklist/Commit/测试数量/PASS 结论，以当前代码、
M8 DoD、可执行 Contract Tests、Fault Injection 与实际 production path
为事实来源。不默认 RECHECK-20260814-012 结论正确。

## 复审发现（Finding）

| ID | 严重度 | 发现 | 证据（修复前实测） | 处置 |
| --- | --- | --- | --- | --- |
| F-01 | HIGH | MCP stdio `timeout_seconds` 不生效：慢工具 10.7s 返回 SUCCEEDED（spec=1.0s），超时语义完全缺失 | 运行探针：`FAULT_SLOW` stdio execute 返回 `SUCCEEDED`，耗时 10.7s | 已修复：`call_tool_with_timeout` + initialize/list_tools 硬超时；契约测试 `test_slow_tool_enforces_spec_timeout`（2s spec，断言 <8s） |
| F-02 | HIGH | 超时取消触发 SDK TaskGroup 关闭 `ExceptionGroup` 掩盖原始 `TimeoutError`，被误分类为 `TransientPortError(TOOL_UNAVAILABLE)` 而非 `PortTimeoutError(TOOL_TIMEOUT)` | 修复过程实测：第一次超时修复后测试失败，异常为 `TransientPortError: unhandled errors in a TaskGroup` | 已修复：transport 层 `_derived_from_timeout` 沿异常链（BaseExceptionGroup/`__cause__`/`__context__`）归一化为 `TimeoutError`；provider 同时接受 `httpx.TimeoutException` |
| F-03 | HIGH | MCP v1 废弃入口 `streamablehttp_client(timeout=)` 只约束 connect，读超时默认 300s（`sse_read_timeout`）；HTTP 慢工具 10s 才浮出异常，工具调用超时未强制 | 修复过程实测：HTTP `FAULT_SLOW` + 2s spec，异常 10s 后才浮出 | 已修复：改用非废弃入口 `streamable_http_client` + 自建 `httpx.AsyncClient(Timeout(connect=read=spec))`；契约测试 `test_slow_tool_over_http_enforces_timeout` |
| F-04 | MEDIUM | ToolResolver 策略覆盖缺口静默放行：`default_decision=ALLOW` 意味着任何未被 preflight 覆盖的 capability 在解析面自动 ALLOW | 代码审读 `resolver.py::resolve_capability`；运行探针确认 `ResolutionInput()` 空决策返回 bindings | 已修复：fail-closed——无显式 per-capability 决策按 DENY；单元测试 `test_no_explicit_allow_is_fail_closed` + 集成测试 `TestResolverFailClosed` |
| F-05 | MEDIUM | execution-time `REQUIRE_APPROVAL` 在 use case `execute_tool_call` 中被静默放行（与 OpenHands PolicyEnforcingAgent/PolicyWrappedToolExecutor 的阻塞语义不一致，四面对齐缺口） | 代码审读：仅 `DENY` 抛异常，`REQUIRE_APPROVAL` 继续执行 | 已修复：`REQUIRE_APPROVAL` → `APPROVAL_REJECTED` 阻塞；测试 `test_execution_time_requires_approval_blocks`；`TOOL_RUNTIME.md` §6 同步四面对齐语义 |
| F-06 | LOW | ToolPack 的 `credential.scope` 声明（LLM/TOOL/WORKSPACE/USER_OAUTH）在安装门禁未被强制：required 凭据可声明 LLM 域，与凭据域隔离边界（CAPABILITY_SECURITY.md §4）不一致 | 代码审读 `lifecycle.py::_verify_supply_chain` | 已修复：required 凭据强制 TOOL 域；测试 `TestLifecycleCredentialGate` 2 项 |

非阻断（记录为技术债，不阻塞 PASS）：

| ID | 发现 | 处置 |
| --- | --- | --- |
| D-01 | `execute_tool_call` 只查 capability 级策略，不查 tool_id/argument 级；`policy_check._CAPABILITY_SCOPE` 常量表与 `examples/config/policy.yaml` 手工同步 | 记录为技术债；scope 映射一致性有既有测试锁死；后续 approval 通道（M7 遗留）落地时统一 |
| D-02 | frozen tool set 与 ToolCatalog/健康状态无运行时组合门禁：`require_frozen_tool_set` 是显式纯函数，生产调用方未挂接 | M8 交付语义即显式强制（FakeAgentRuntime/OpenHands 装配均以 frozen 集合构造）；运行时组合门禁属后续编排强化 |
| D-03 | MCP `check_health` 的 `except Exception` 宽捕获吞掉超时语义（健康探测降级为 open circuit 可接受） | 可接受行为；慢 server 的 check_health 已由 initialize 硬超时约束 |
| D-04 | `McpToolProvider._resolved_spec` 属私有方法被契约测试直接访问（`test_credential_scope_is_tool_domain`） | 测试实现细节耦合，非产品缺陷 |

## 检查结果

修复后验证证据：

| Gate | 检查 | 结果 |
| --- | --- | --- |
| G-01 | 定向测试（M8 全量：contracts + application + integration + mcp_server） | 66 passed（含新增 5 项：stdio 慢工具超时、HTTP 慢工具超时、非法 timeout spec、resolver fail-closed、发现面不扩张） |
| G-02 | execution.py REQUIRE_APPROVAL 阻塞 + TestLifecycleCredentialGate | 49 passed（tool_plane + integration 定向） |
| G-03 | 全量 pytest | 1139 passed（基线 1134 + 5 新增；execution 修复后最终轮重跑确认） |
| G-04 | ruff check（product + engineering 按 CI 定义作用域） | 0 errors |
| G-05 | ruff format --check | 275 files already formatted |
| G-06 | mypy strict | Success: no issues found in 258 source files |
| G-07 | import-linter 架构边界 | python/dependency-boundaries 2 passed |
| G-08 | validate_bundle | 验证通过 |
| G-09 | governance validate | PASS: 0 warning(s) |
| G-10 | m0 profile | 18 deterministic checks PASS（最终轮，含全部修复） |

## M8 DoD 逐项复核（Roadmap MILESTONES.md M8 节）

| DoD | 结论 | 证据 |
| --- | --- | --- |
| MCP Streamable HTTP + stdio adapter 通过 ToolProvider contract suite | PASS | `tests/contracts/test_tool_provider_contract.py` 双 transport 21 项（含新增超时故障注入 3 项） |
| ToolPack install/update/revoke 单元 + 契约测试 | PASS | `test_tool_plane_execution.py::TestLifecycle` + `test_tool_pack_store_contract.py` + 新增凭据域门禁 2 项 |
| health/circuit breaker 故障注入测试 | PASS | `test_tool_plane.py::TestHealth` 5 次失败 OPEN / 非法迁移 / DISABLED / 4 次 CLOSED + MCP 真实 probe + schema 漂移 |
| tool credential 与 LLM credential 隔离测试 | PASS | `TestCredentialDomainSeparation` 3 项 + ToolPack 凭据域门禁 2 项 |
| 供应链 pin 验证 | PASS | digest 篡改拒绝 + pinned 满足 preflight（`TestSupplyChainPin`）+ mcp==1.29.0 uv.lock |
| 独立复审 PASS + m0 profile 全绿 | PASS | 本 recheck + 最终轮 m0 profile 18/18 |

## 复审范围外核查

- M8 未侵入 M9（ExecutionBackend/DockerWorkspace 未动）、M10（MemoryStore/Evidence 未动）、M11（eval harness 未动）；`ToolResultRecord` 不直接成为 Evidence（`result_handler.register_session_result` 将 Agent 结构化输出注册为 PROPOSED Claim，VERIFIED 需 AcceptanceCriteria 评估升级，非工具输出直通）。
- 未为跑通测试重复实现 M5/M6/M7 能力：circuit breaker 复用 `packages/domain/circuit_breaker.py` 纯状态机；Policy Wrapper（M6）未改写；M7 编排/frozen 语义未回退。
- mock/test provider 走正式 ToolProvider Port 路径：`FakeToolProvider` 与 `McpToolProvider` 均实现同一 Port；MCP contract suite 走真实 stdio/HTTP transport；测试 MCP server 仅注册 mock tool，无测试专用 bypass。

## 结论

- 结果：`PASS_WITH_WARNINGS`（复审发现 F-01..F-06 已修复并有回归测试
  锁死；D-01..D-04 非阻断技术债为 warning 来源；最终 M8 DoD 全部有
  可重复证据 → **M8 判定 PASS**）
- 剩余风险：D-01..D-04 非阻断技术债，不阻塞 M8；approval 通道落地前
  `REQUIRE_APPROVAL` 一律阻塞（安全侧默认）。
- 后续动作：M9/M10/M11 可并行启动；停在本阶段边界。