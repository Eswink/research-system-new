---
id: PLAN-20260814-012
slug: m8-research-capability-plane
title: M8 Research Capability Plane（Tool Plane + Skill Registry）
status: DONE
created_at: 2026-08-14
updated_at: 2026-08-14
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: cursor-plan
  ref: "用户批准 Cursor Plan『M8 — Research Capability Plane 实施计划』；范围以 docs/roadmap/MILESTONES.md M8 节为唯一权威"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260814-012-m8-research-capability-plane.md
memory_entries:
  - MEM-20260814-012
---

# PLAN-20260814-012 — M8 Research Capability Plane

## 目标

把 M1/M4 已冻结的 Tool/Skill/Capability 骨架（`SkillSpec / Capability /
ToolSpec / ToolProviderSpec / ToolPackManifest`）与 M5 `ToolProvider` Port
实现为可运行、可治理、可测试的 Research Capability Plane：ToolCatalog /
ToolResolver、ToolProvider lifecycle、ToolPack install/update/revoke、
health/circuit breaker、effect/risk、tool credential separation、
large-result Artifact indirection、正式 Skill Registry、MCP Streamable
HTTP + stdio adapter。全部验证走 mock provider 与本地测试 MCP server，
不引入真实第三方科研工具。

## 范围

- 包含（三个 work package，同一 M8 Milestone 内）：
  1. Tool Plane Core：Domain 枚举补全（ToolCallStatus/ToolResultStatus/
     CredentialScope/RiskClass + classify_risk）、ToolProvider Port 扩展
     （list_tools/check_health）、`packages/application/tool_plane/`
     （catalog/resolver/lifecycle/health/execution/results）、
     compile/preflight/session 挂接。
  2. Skill Registry：`SkillSpec` 扩展（digest/status）、
     `packages/application/skill_registry/`（registry/routing/lifecycle）、
     Role/Agent 集成。
  3. Capability Integration & MCP：`adapters/mcp/`（stdio + Streamable
     HTTP + McpToolProvider）、本地测试 MCP server、contract tests、
     fault injection、policy/credential/supply-chain 安全验证。
- 不包含：真实第三方科研工具库（OpenAlex/Semantic Scholar/PaperQA 等）、
  UI、分布式工具执行、ToolPack 市场/发布平台、M9-M12 内容；不新建
  Milestone 编号；不改 `RunManifest` digest 语义。

## 架构与数据流

```text
Protocol（Role: skills/capabilities）
→ Protocol Compile（capability requirements）
→ ToolResolver（catalog + health + trust + policy ∩）
→ ResolvedToolBindings → Freeze（frozen tool set）
→ AgentSession（冻结）
→ ExecuteToolCall（execution-time PolicyEvaluator 门禁）
→ ToolProvider Port
→ adapters/mcp（stdio / Streamable HTTP，凭据经 CredentialResolver TOOL 域）
→ 大结果经 ArtifactStore reference 回传
```

架构边界：Role/Skill/Capability/Tool 不混合；Skill 只声明所需
Capability 不授权限；ToolProvider 不拥有 Policy truth；exposure-time 与
execution-time 双重检查保留；LLM Relay 与 Tool Provider 独立凭据域；
AgentSession Effective Tool Set 冻结；大结果 Artifact indirection；
OpenHands direct tool execution 经 Policy Wrapper（M6 语义不变）。

## 验收条件

- [x] AC-01：MCP Streamable HTTP + stdio adapter 通过 ToolProvider contract suite。
- [x] AC-02：ToolPack install/update/revoke 单元 + 契约测试。
- [x] AC-03：health/circuit breaker 故障注入测试。
- [x] AC-04：tool credential 与 LLM credential 隔离测试。
- [x] AC-05：供应链 pin（digest）验证测试。
- [x] AC-06：exposure-time + execution-time 双重权限检查保留（测试证据）。
- [x] AC-07：AgentSession Effective Tool Set 冻结语义保留（M7 回归全绿）。
- [x] AC-08：大型 Tool Result 走 Artifact/reference（不塞 Domain JSON/模型上下文）。
- [x] AC-09：Skill Registry 稳定加载、版本/digest、生命周期、capability 路由、复用、Role/Agent 集成。
- [x] AC-10：Role/Agent → Skill → Capability → ToolResolver → ToolProvider 集成测试。
- [x] AC-11：无真实第三方科研工具（仅 mock provider + 本地测试 MCP server）。
- [x] AC-12：m0 profile 全绿 + validate_bundle + governance validate + ruff/mypy/import-linter 全过。
- [x] AC-13：独立复审（recheck）PASS。

## 实施清单

- [x] STEP-01：all-plan 立项（本文件）+ MCP upstream qualification + mcp SDK pin。
- [x] STEP-02：WP1a Domain 枚举补全 + status 迁移 + Port 扩展 + Fake 升级 + contract suite 扩展。
- [x] STEP-03：WP1b `packages/application/tool_plane/` 六模块 + compile/preflight/session 挂接 + 测试。
- [x] STEP-04：WP2 SkillSpec 扩展 + `packages/application/skill_registry/` + Role/Agent 集成 + 负面测试。
- [x] STEP-05：WP3a `adapters/mcp/` + 本地测试 MCP server + contract tests。
- [x] STEP-06：WP3b 垂直集成 + 安全验证（双权限/凭据隔离/pin/frozen/大结果/schema 漂移）。
- [x] STEP-07：收口 docs（SKILL_REGISTRY.md + M8_MCP_QUALIFICATION.md + INDEX）+ validate_bundle 交叉引用 + 全量回归。
- [x] STEP-08：recheck + M8_COMPLETION_RECORD.md + MILESTONES.md 索引更新 + DoD 报告 + readiness 评估。

## 子代理使用

Subagent 默认不启用。需要并行时，每个 wave 最多 3 个；多 wave 必须在前一波
完成并整合后才可开始。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| — | 未使用 | 0 | — | — |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | STEP-01 | doc | docs/references/upstream/M8_MCP_QUALIFICATION.md + uv.lock mcp 1.29.0 | PASS |
| EV-02 | STEP-02 | test | tests/domain/test_tool_plane_domain.py + tests/contracts/test_ports_semantics.py | PASS（26+ 项） |
| EV-03 | STEP-03 | test | tests/application/test_tool_plane.py + test_tool_plane_execution.py | PASS（35 项） |
| EV-04 | STEP-04 | test | tests/application/test_skill_registry.py | PASS（16 项） |
| EV-05 | STEP-05 | test | tests/contracts/test_tool_provider_contract.py | PASS（15 项，双 transport） |
| EV-06 | STEP-06 | test | tests/integration/test_capability_plane.py + _security.py | PASS（16 项） |
| EV-07 | STEP-07 | check | pytest 1134 passed；ruff 0 errors；format 268 files；mypy 258 files Success；validate_bundle/governance PASS；architecture 10 passed；m0 profile 18 checks PASS | PASS |
| EV-08 | STEP-08 | recheck | .cursor/plans/rechecks/RECHECK-20260814-012-m8-research-capability-plane.md | PASS |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-14 | 初始化 | 用户批准的 Cursor Plan | 无 |
| 2026-08-14 | 采用 mcp>=1.28,<2（uv.lock 解析 1.29.0），拒绝 2.0.0 | mcp 2.0.0 与 openhands-sdk 1.42.0（M5R revision lock）经 fastmcp 3.x 硬依赖 mcp<2.0 冲突；官方 v1.x 分支持续收安全补丁 | 仅 adapter 层；升级门禁=ToolProvider contract suite |
| 2026-08-14 | M8 新增枚举移至 packages/domain/tool_enums.py 并由 enums.py re-export | enums.py 超过 300 行硬阈值（311） | 既有 import 路径不变，mypy 显式 re-export |
| 2026-08-14 | skill 检查拆到 packages/application/preflight/skill_checks.py | role_checks.py 超过 300 行硬阈值（324） | 职责更清晰：role/agent 检查与 skill registry 检查分离 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-14 | — | APPROVED | 用户批准 Cursor Plan（M8 实施） | Cursor Plan `m8_research_capability_plane_59f777c0.plan.md` |
| 2026-08-14 | APPROVED | IN_PROGRESS | 开始 WP1a | 无 |
| 2026-08-14 | IN_PROGRESS | VERIFYING | 全量回归 + m0 profile 全绿 | EV-07 |
| 2026-08-14 | VERIFYING | DONE | 复检 PASS | RECHECK-20260814-012 |
| 2026-08-14 | DONE | VERIFYING | 用户要求独立端到端复审（不默认开发窗口结论） | 本会话独立复审启动 |
| 2026-08-14 | VERIFYING | DONE | 独立复审发现 F-01..F-06 并修复（超时强制/超时归一化/resolver fail-closed/REQUIRE_APPROVAL 阻塞/凭据域门禁），补充 6 项契约+故障测试，最终 m0 profile 18/18 | RECHECK-20260814-013 |

## 影响报告

- Domain/API/schema：`ToolCallRecord.status`/`ToolResultRecord.status` 裸字符串→稳定枚举（fixtures/fake/测试同步迁移）；`SkillSpec` 增补 digest/status（向后兼容默认值）；新增 `tool-spec.schema.json`、`capability.schema.json`；`skill.schema.json`/`toolpack-manifest.schema.json` 扩展（scope 枚举化）；ToolProvider Port 增补 list_tools/check_health；新增 ToolPackStore Port；新增 EventType `tool_pack.updated`/`tool_pack.revoked`；新增 PreflightFindingCode `TOOL_RISK_ELEVATED` + `SKILL_*` 4 项。
- 安全/凭据：CredentialScope 四域枚举（LLM/TOOL/WORKSPACE/USER_OAUTH）；MCP streamable_http 强制 TOOL 域 credential_ref；禁止 token passthrough；双权限检查保留；大结果不进入模型上下文。
- 兼容性/迁移：`packages.domain.enums` 导入路径不变（tool_enums re-export）；RunManifest digest 语义未动；M7 全量回归 1134 passed（基线 989）。
- 上游版本：mcp==1.29.0 ADOPTED（MIT）；openhands-sdk 1.42.0 未动。
- 下一项任务：M9 Real Experiment Runtime / M10 Evidence-Memory / M11 Evaluation Plane 可并行（均 READY，IG-1 前置剩 M9/M10/M11）。