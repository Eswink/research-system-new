---
id: MEM-20260814-012
title: M8 Research Capability Plane 实施事实（Tool Plane + Skill Registry + MCP）
status: ACTIVE
created_at: 2026-08-14
updated_at: 2026-08-14
scope: repository
confidence: 0.9
review_after: 2026-11-14
source_plans:
  - .cursor/plans/tasks/PLAN-20260814-012-m8-research-capability-plane.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260814-012-m8-research-capability-plane.md
supersedes: []
tags: [m8, tool-plane, skill-registry, mcp, capability]
---

# MEM-20260814-012 — M8 Research Capability Plane 实施事实

## 做了什么

M8 把 M1/M4 Tool/Skill/Capability 骨架落地为可运行、可治理、可测试的
Research Capability Plane（三个 work package，同一 Milestone 内）：

1. Tool Plane Core：`packages/application/tool_plane/`（ToolCatalog /
   ToolResolver / ToolPack install-update-revoke / ToolHealthMonitor /
   ExecuteToolCall / 大结果 Artifact spill）；`ToolProvider` Port 扩展
   list_tools/check_health；新增 `ToolPackStore` Port；
   `ToolCallStatus`/`ToolResultStatus`/`CredentialScope`/`RiskClass`/
   `SkillStatus`/`ToolPackState` 枚举在 `packages/domain/tool_enums.py`
   （`enums.py` re-export 保持既有 import 路径）。
2. Skill Registry：`packages/application/skill_registry/`（registry
   校验 / 纯声明能力路由 / ACTIVE→DEPRECATED→RETIRED 生命周期）；
   preflight 新增 `SKILL_*` findings + `check_role_skills`。
3. MCP：`adapters/mcp/`（McpToolProvider，stdio + Streamable HTTP 双
   transport，凭据经 CredentialResolver 注入，错误映射
   transient/permanent）；测试 MCP server 在 `tests/mcp_server/`。

## 为什么这样做

- **mcp 依赖选 1.29.0（v1 stable line），拒绝 2.0.0**：`uv add
  "mcp==2.0.0"` 确定性解析失败——openhands-sdk==1.42.0（M5R revision
  lock）经 fastmcp 3.x 硬依赖 `mcp>=1.24,<2`。官方 PyPI 明确 v1.x
  分支持续收安全补丁并推荐 `mcp>=1.28,<2` 作为未迁移前 pin。
- M8 新增枚举放独立模块并 re-export：`enums.py` 超 300 行硬阈值。
- skill 检查从 `role_checks.py` 拆出：超 300 行硬阈值 + 单一职责。
- 大结果按 TOOL_RUNTIME.md §7 走 ArtifactStore 阈值分流，不进
  Domain JSON / 模型上下文。
- Skill 路由纯声明（不产生 CapabilityGrant）：授权面由 Role/Policy
  裁决（ADR-0005）。

## 怎么做与复现

1. 依赖检查：`uv.lock` 中 mcp==1.29.0；`UPSTREAM_COMPONENTS.yaml` mcp
   条目 ADOPTED + sdist digest `52d01f...`。
2. 全量回归（UTF-8 环境）：`pytest tests -q`（1134 passed）+
   `ruff check packages adapters tests` + `ruff format --check` +
   `mypy`（258 files Success）+ `validate_bundle.py` +
   `governance validate` + `run_all_checks.py --profile m0`（18 checks）。
3. MCP 双 transport 验证：
   `tests/contracts/test_tool_provider_contract.py`（15 项，stdio 子进程
   `python -B -m tests.mcp_server.run_stdio <fault>` + 进程内 uvicorn
   Streamable HTTP）。
4. 架构边界：`.importlinter.mcp`（mcp SDK 仅限 adapters/mcp）+
   `.importlinter.application`/`.importlinter.domain` 增补 mcp 禁令。

## 适用边界

- 适用于：M8 之后的 Tool/Skill/MCP 演进、M9-M12 的工具消费、
  mcp/openhands-sdk 依赖升级决策。
- 不适用于：真实第三方科研工具（M8 明确不引入；M12 才接入真实工具）。

## 失效与复核触发器

- 到达 `review_after`（2026-11-14）。
- openhands-sdk 升级解除 `mcp<2.0` 约束时：重新 qualification mcp 2.x。
- ToolProvider Port 契约再演化（新增方法）时：contract registry 与
  FakeToolProvider/McpToolProvider 同步升级。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20260814-012-m8-research-capability-plane.md` | 范围、AC、决策与偏差 |
| recheck | `.cursor/plans/rechecks/RECHECK-20260814-012-m8-research-capability-plane.md` | AC-01..AC-13 全部 PASS |
| repository | `docs/references/upstream/M8_MCP_QUALIFICATION.md` | mcp 1.29.0 决策与冲突证据 |
| repository | `uv.lock`（mcp 1.29.0 sdist digest） | 依赖 pin 事实 |
| repository | `packages/application/tool_plane/`、`packages/application/skill_registry/`、`adapters/mcp/` | 实现位置与边界 |