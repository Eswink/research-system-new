# M8 Completion Record — Research Capability Plane

Date: 2026-08-14
Plan: `PLAN-20260814-012`
Recheck: `RECHECK-20260814-012`（PASS）；独立复审 `RECHECK-20260814-013`
（PASS_WITH_WARNINGS：发现并修复 F-01..F-06，最终 M8 判定 PASS）
Milestone 权威定义：`docs/roadmap/MILESTONES.md` M8 节

## Git Evidence

- `4c2c16d`（2026-08-14）feat(m8): research capability plane with
  independent-recheck hardening（实现 + 独立复审修复落地）。
- 关联复审：`RECHECK-20260814-013`（独立复审，PASS_WITH_WARNINGS →
  M8 PASS）。

## 交付概要

M8 把 M1/M4 冻结的 Tool/Skill/Capability 骨架实现为可运行、可治理、
可测试的 Research Capability Plane。三个 work package 在同一 M8
Milestone 内完成：

1. **Tool Plane Core**：Domain 枚举补全（`ToolCallStatus` /
   `ToolResultStatus` / `CredentialScope` / `RiskClass` / `SkillStatus` /
   `ToolPackState`，位于 `packages/domain/tool_enums.py` 并 re-export）、
   `classify_risk` effect/risk 分层、`ToolProvider` Port 扩展
   （list_tools / check_health）、`packages/application/tool_plane/`
   （ToolCatalog / ToolResolver / ToolPack install-update-revoke 生命周期
   / ToolHealthMonitor 熔断驱动 / ExecuteToolCall execution-time 门禁 /
   大结果 Artifact spill）、`ToolPackStore` Port + Fake、preflight
   `TOOL_RISK_ELEVATED` 挂接。
2. **Skill Registry**：`SkillSpec` 增补 digest（内容确定性，不含
   status）与 status（ACTIVE→DEPRECATED→RETIRED）、
   `packages/application/skill_registry/`（registry 校验 / 纯声明能力路由
   / 生命周期）、preflight `SKILL_MISSING / SKILL_DIGEST_MISMATCH /
   SKILL_DEPRECATED / SKILL_RETIRED` + `check_role_skills` 集成。
3. **Capability Integration & MCP**：`adapters/mcp/`（`McpToolProvider`
   + `McpConnectionSpec`，stdio + Streamable HTTP 双 transport，凭据经
   CredentialResolver 注入禁止 passthrough，错误映射 transient/permanent）、
   本地测试 MCP server（双 transport + 故障注入开关）、MCP 专属 contract
   suite、capability plane 垂直集成与安全验证（双权限 / 凭据域隔离 /
   供应链 pin / frozen set / 大结果 / schema 漂移）。

## 关键交付物

| 交付物 | 位置 |
| --- | --- |
| Tool Plane use cases | `packages/application/tool_plane/` |
| Skill Registry | `packages/application/skill_registry/` |
| MCP adapter | `adapters/mcp/` |
| ToolPackStore Port | `packages/application/ports/tool_pack_store.py` |
| MCP upstream qualification | `docs/references/upstream/M8_MCP_QUALIFICATION.md` |
| Skill Registry 规格 | `docs/architecture/SKILL_REGISTRY.md` |
| MCP contract suite | `tests/contracts/test_tool_provider_contract.py` |
| 垂直集成 + 安全验证 | `tests/integration/test_capability_plane{,_security}.py` |
| 测试 MCP server | `tests/mcp_server/` |
| 新增 schema | `schemas/tool-spec.schema.json`、`schemas/capability.schema.json` |

## 上游版本影响

- **mcp==1.29.0 ADOPTED**（v1 stable line，MIT；`pyproject.toml`
  `mcp>=1.28,<2` + uv.lock + sdist digest）。mcp 2.0.0 被拒绝：
  openhands-sdk 1.42.0（M5R revision lock）经 fastmcp 3.x 硬依赖
  `mcp<2.0`。升级门禁：任何 mcp 版本变更必须重跑 ToolProvider contract
  suite（双 transport）。
- `openhands-sdk==1.42.0` revision lock 未动。

## DoD 证据（AC-01..AC-13 全部 PASS）

- MCP 双 transport contract：21 项（含独立复审新增 3 项超时故障注入）
- ToolPack 生命周期 + 供应链 pin：单元 + 契约 15 项（含凭据域门禁 2 项）
- health/circuit breaker 故障注入：4 项 + schema 漂移 2 项
- tool/LLM 凭据域隔离：3 项 + ToolPack 凭据域门禁 2 项
- 双权限检查：4 项（含 execution-time REQUIRE_APPROVAL 阻塞）；frozen set：2 项
- 大结果 artifact indirection：2 项（含真实 MCP stdio 链路）
- Skill Registry：16 项单元 + 集成；resolver fail-closed 2 项
- 垂直集成全链：`Role/Agent → Skill → Capability → ToolResolver → ToolProvider`
- 无真实第三方科研工具（仅 mock provider + 本地测试 MCP server）
- 全量回归：pytest **1139 passed**（基线 1134）；ruff 0 errors；format
  275 files；mypy strict 258 files Success；validate_bundle 通过；
  governance validate 通过；architecture tests 2 passed；
  **m0 profile PASS（18 deterministic checks）**
- 独立复审：`RECHECK-20260814-013` = **PASS_WITH_WARNINGS → M8 PASS**

### 独立复审修复记录（2026-08-14）

RECHECK-20260814-013 独立复审不默认开发窗口结论，实测发现并修复：

1. **stdio 超时缺失**（F-01/F-02）：`McpConnectionSpec.timeout_seconds`
   对 stdio call_tool 不生效（10s 慢工具按 1s spec 返回 SUCCEEDED）；
   超时取消触发 SDK TaskGroup `ExceptionGroup` 掩盖 `TimeoutError`
   致误分类为 `TOOL_UNAVAILABLE`。修复：`call_tool_with_timeout` /
   initialize / list_tools 硬超时 + transport 层超时异常链归一化。
2. **HTTP 超时不强制**（F-03）：v1 废弃入口 `streamablehttp_client`
   的 `timeout` 只约束 connect，读超时默认 300s。修复：改用非废弃入口
   `streamable_http_client` + 自建 `httpx.AsyncClient`（connect=read=
   spec 超时）。
3. **resolver 静默放行**（F-04）：`default_decision=ALLOW` 使策略覆盖
   缺口自动放行。修复：fail-closed——无显式 per-capability 决策按
   DENY。
4. **execution-time REQUIRE_APPROVAL 静默放行**（F-05）：use case 与
   OpenHands Policy Wrapper 阻塞语义不一致。修复：
   `APPROVAL_REJECTED` 阻塞，四面对齐（`TOOL_RUNTIME.md` §6 同步）。
5. **ToolPack 凭据域未强制**（F-06）：required 凭据可声明 LLM 域。
   修复：安装门禁强制 TOOL 域。

新增回归测试 6 项：`test_slow_tool_enforces_spec_timeout`、
`test_slow_tool_over_http_enforces_timeout`、
`test_invalid_timeout_spec_rejected`、`test_no_explicit_allow_is_fail_closed`、
`TestResolverFailClosed`、`TestLifecycleCredentialGate`（2 项）。

## 风险登记

- MCP 生态多样性导致 adapter 抽象泄漏：以 contract suite（双 transport
  21 项）+ 独立复审超时故障注入实测收敛（F-01..F-03）；非废弃入口
  `streamable_http_client` 采纳，废弃入口不再使用。
- 工具风险分级不足造成安全漏洞：execution-time 门禁 fail-closed
  （F-04/F-05：无显式 per-capability 决策按 DENY；REQUIRE_APPROVAL
  四面对齐）与 ToolPack 凭据域强制（F-06）双重收敛。
- ToolPack 供应链治理复杂度：mcp==1.29.0 ADOPTED + sdist digest + 升级
  门禁（任何 mcp 版本变更必须重跑 ToolProvider contract suite）。

## M9 / M10 / M11 Readiness

- **M9 Real Experiment Runtime**：READY——M8 未触碰 ExecutionBackend /
  WorkspaceBackend / DockerWorkspace；M7 遗留 P1 债（容器执行）仍按
  BACKLOG 归属 M9，无新阻塞。
- **M10 Evidence / Memory / Provenance**：READY——M8 未触碰 MemoryStore /
  SourceRecord / MemoryWriteProposal；ToolResultRecord 的
  output_digest/reference 结构可直接作为 M10 证据链的数据输入。
- **M11 Evaluation Plane**：READY——M8 的 ToolSpec/SkillSpec 版本+digest
  与 ToolPack 生命周期为 M11「Tool 变更 before/after regression」提供
  了可评测对象与 pin 数据面；M11 按路线可并行启动。
- IG-1（M12 Entry）前置：M8 完成，剩 M9/M10/M11。