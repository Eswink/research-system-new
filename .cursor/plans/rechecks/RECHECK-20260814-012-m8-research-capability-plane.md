---
id: RECHECK-20260814-012
plan_id: PLAN-20260814-012
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-08-14
completed_at: 2026-08-14
reviewer: root-agent-independent-pass
baseline_ref: M7 DONE（pytest 989 baseline；m0 profile 全绿）
checked_head: working-tree
---

# RECHECK-20260814-012 — M8 Research Capability Plane 复检

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260814-012-m8-research-capability-plane.md`
- 验收条件：AC-01..AC-13（与 MILESTONES.md M8 DoD 对齐）
- 变更范围：`packages/domain/`（tools/enums/tool_enums/events/protocols）、
  `packages/application/ports/`（tool_provider/tool_pack_store）、
  `packages/application/tool_plane/`（新）、
  `packages/application/skill_registry/`（新）、
  `packages/application/preflight/`（checks/role_checks/skill_checks）、
  `adapters/mcp/`（新）、`adapters/fakes/`、`schemas/`、`examples/`、
  `tests/`（contracts/integration/mcp_server/tooling）、`docs/`、
  `UPSTREAM_COMPONENTS.yaml`、`pyproject.toml`/`uv.lock`、
  `.importlinter.*`、`validate_bundle.py`
- 基线：M7 DONE；M8 批准 Cursor Plan `m8_research_capability_plane_59f777c0.plan.md`

## 检查结果

| Gate | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| G-01 | 范围与架构 | git status 变更全部落在 M8 批准范围内；`packages/` 无 mcp/openhands/litellm 引用；`.importlinter.application`（含 mcp 禁令）+ `.importlinter.domain`（含 mcp）+ `.importlinter.mcp`（新）全部 0 broken；`tests/architecture/python` 10 passed | PASS |
| G-02 | AC-01 MCP 双 transport 过 ToolProvider contract | `tests/contracts/test_tool_provider_contract.py` 15 passed（stdio execute/list_tools/health/schema 漂移/大结果/未注册工具/关闭语义 + Streamable HTTP 4 项 + 凭据失败） | PASS |
| G-03 | AC-02/AC-05 ToolPack 生命周期 + 供应链 pin | `tests/application/test_tool_plane_execution.py::TestLifecycle` 6 passed + `tests/contracts/test_tool_pack_store_contract.py` 7 passed + `TestSupplyChainPin`（digest 篡改拒绝 + pinned 满足 preflight） | PASS |
| G-04 | AC-03 health/circuit breaker 故障注入 | `tests/application/test_tool_plane.py::TestHealth`（5 次失败 OPEN / 非法迁移 / DISABLED / 4 次仍 CLOSED）+ `TestSchemaHashDrift`（baseline vs drifted digest 不同） | PASS |
| G-05 | AC-04 凭据域隔离 | `TestCredentialDomainSeparation`（TOOL/LLM 域枚举分离 + http 必声明 credential_ref + deny 不泄漏 LLM secret） | PASS |
| G-06 | AC-06 双重权限检查 | `TestDoubleEnforcement` 3 项（exposure DENY 阻断 preflight / execution DENY 阻断 execute / policy truth 仅来自 PolicyEvaluator） | PASS |
| G-07 | AC-07 frozen tool set + M7 回归 | `TestFrozenToolSet` 2 项；全量 pytest 1134 passed（含 M7 全部 e2e/contract 回归，989 基线之上） | PASS |
| G-08 | AC-08 大结果 artifact indirection | `TestLargeResultIndirection` 2 项（spill roundtrip 不进 Domain JSON + 真实 MCP stdio 大结果溢出） | PASS |
| G-09 | AC-09/AC-10 Skill Registry + 垂直集成 | `tests/application/test_skill_registry.py` 16 passed + `TestVerticalSlice` 全链 + `TestSkillCannotGrantPermissions` 2 项 | PASS |
| G-10 | AC-11 无真实第三方科研工具 | `tests/mcp_server/server.py` 仅 mock tool（literature_search/citation_inspect 无真实数据）；无 OpenAlex/SemanticScholar/PaperQA 依赖 | PASS |
| G-11 | AC-12 质量门禁 | ruff check 0 errors；ruff format --check 268 files；mypy strict 258 files Success；validate_bundle 通过；governance validate 通过；m0 profile PASS（18 deterministic checks） | PASS |
| G-12 | 安全与供应链 | UPSTREAM_COMPONENTS mcp ADOPTED（sdist digest 与 uv.lock 一致）；LICENSE_MATRIX 增补；`examples/contracts/toolpack_manifest.yaml` scope 改用 TOOL 枚举；governance validate "未发现明显凭据材料" | PASS |
| G-13 | 兼容性 | `ToolResultRecord.status` 迁移为枚举（fixtures/fake/tests 同步迁移，全部通过）；`RunManifest` digest 语义未动（M7 resume 测试全绿）；新增 enum re-export 保持 `packages.domain.enums` 导入路径不变 | PASS |

## Findings

| ID | 严重度 | 发现 | 处置 |
| --- | --- | --- | --- |
| — | — | 无 | — |

## 结论

- 结果：`PASS`
- 理由：AC-01..AC-13 逐条有独立可复现证据；全部 hard gate（架构边界、
  lint/typecheck/test、validators、m0 profile、供应链 pin）通过；无
  未处置 finding。M8 范围内未引入真实第三方科研工具，未扩大
  Milestone 范围。
- 后续动作：PLAN-20260814-012 置 DONE；`MILESTONES.md` 索引 M8 行更新；
  `M8_COMPLETION_RECORD.md` 落地；停在阶段边界，不自动进入 M9。