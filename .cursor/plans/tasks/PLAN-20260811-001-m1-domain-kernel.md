---
id: PLAN-20260811-001
slug: m1-domain-kernel
title: M1 Domain Kernel & Contract Assets 实施
status: DONE
created_at: 2026-08-11
updated_at: 2026-08-11
cursor_plan_uri: m1_domain_kernel_实施_f7341045
owners:
  - root-agent
authorization:
  source: cursor-plan
  ref: M1 — Domain Kernel & Contract Assets 实施（用户批准）
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260811-001-m1-domain-kernel.md
memory_entries:
  - .cursor/memory/entries/MEM-20260811-001-m1-domain-kernel-wiring.md
---

# PLAN-20260811-001 — M1 Domain Kernel & Contract Assets 实施

## 目标

实现 BACKLOG M1/P0 全部 7 项交付：bootstrap validation、Domain entities/enums/invariants、JSON/YAML schema loaders、Run/Phase/Task state machines、RunManifest+Revision+digest、append-only Usage Ledger、Artifact digest/verification，并接入既有 m0 质量门禁。

## 范围

- 包含：`packages/domain/` 域内核、`adapters/contracts/` schema loaders、`schemas/model-profile.schema.json`、确定性序列化规格、状态机迁移表、依赖边界门禁、测试与验证。
- 不包含：M2 Protocol Compiler 执行、M3 probe/eligibility 运行、M4 26 Role fixtures、M5 Ports+Fakes、M6 OpenHands、M7 lease/outbox/PostgreSQL、P1 Memory/Evidence/Artifact Store 生命周期。

## 架构与数据流

```text
adapters/contracts (infrastructure, jsonschema+PyYAML)
    → packages/domain (纯 stdlib 域内核，零第三方依赖)
    → tests/loaders + tests/domain (pytest)
```

Canonical digest 规则：`docs/architecture/DETERMINISTIC_SERIALIZATION.md`（key 排序、RFC3339 UTC、Decimal normalize、UUID 小写、拒绝 float）。状态机迁移表：`docs/reliability/RUN_STATE_MACHINE.md`。依赖门禁：`.importlinter.domain`（domain 禁止 import jsonschema/yaml/fastapi/sqlalchemy/temporalio/openhands 等）。

## 验收条件

- [x] AC-01：bootstrap validation（domain 导入冒烟 + digest 确定性回归）在 CI 门禁内全绿
- [x] AC-02：Domain entities/enums/invariants 定义层 + invariant 测试
- [x] AC-03：基于已批准 jsonschema/PyYAML 的 JSON/YAML schema loaders 覆盖真实 examples
- [x] AC-04：Run/Phase/Task/AgentSession + Cancellation 状态机，迁移表文档化，非法迁移/terminal 不可回退测试
- [x] AC-05：RunManifest 不可变快照 + Revision（approval/audit）+ sha256 确定性 digest
- [x] AC-06：append-only UsageLedger（重复拒绝、frozen、未知成本不伪造）
- [x] AC-07：Artifact sha256 内容寻址 digest/verify

## 实施清单

- [x] STEP-01：工程接线（mypy files + pytest pythonpath + packages/__init__.py）
- [x] STEP-02：core 值对象（ID/Timestamp/Digest/Version/Money）+ canonical serialization
- [x] STEP-03：跨领域稳定枚举（FailureCategory/ModelCapability/PolicyDecision 等 24 类）
- [x] STEP-04：四个状态机（run/phase/task/session + cancellation）+ 迁移表文档
- [x] STEP-05：实体模块（protocols/roles/tasks/models/tools/workspace/memory/evidence/budget/artifacts）
- [x] STEP-06：RunManifest/Revision/digest + UsageLedger + Artifact verify
- [x] STEP-07：adapters/contracts loaders（base/roles/models/tasks）+ 真实 examples 测试
- [x] STEP-08：model-profile.schema.json 新增并同步 validate_bundle.py 注册表与 strict 校验
- [x] STEP-09：.importlinter.domain 真实代码依赖门禁 + test_domain_boundaries.py
- [x] STEP-10：m0 全量门禁 + 双 validator + recheck

## 子代理使用

M1 计划制定阶段使用 3 个并行 explore 子代理调查域规格、契约资产与测试基础设施；实施阶段未委派。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | ---: | --- | --- | --- |
| 1 | 域内核规格 / 契约资产现状 / 测试与 CI 门禁 | 3 | 完成 | 调查结论已并入本计划 |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | 全部门禁 | check | `uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going` | 18 checks PASS |
| EV-02 | 单元测试 | test | `uv run pytest` | 178 passed |
| EV-03 | 系统契约 | check | `python -B .cursor/skills/system-spec-check/scripts/validate_bundle.py` | 验证通过 |
| EV-04 | 治理契约 | check | `python -B .cursor/skills/governance-check/scripts/validate.py` | 验证通过 |
| EV-05 | 依赖边界 | check | `uv run pytest tests/architecture/python` | 4 passed（含 domain purity） |
| EV-06 | 复检 | recheck | `RECHECK-20260811-001` | PASS |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-11 | canonical digest 规则写入新文档 DETERMINISTIC_SERIALIZATION.md | 仓库原无确定性序列化规格 | 唯一 digest 规则来源 |
| 2026-08-11 | 状态机迁移表显式化并写入 RUN_STATE_MACHINE.md | 原文档仅有状态集合与 5 条规则 | 迁移表成为可测试契约 |
| 2026-08-11 | 新增 schemas/model-profile.schema.json 并同步 validator 注册表 | ModelProfile 被 4 处 schema 引用但无 schema 文件 | 契约资产补齐 |
| 2026-08-11 | loader 采用"嵌套 map + 扁平化 id"结构与 validator 一致 | examples 实际结构为嵌套 map | 避免结构假设偏差 |
| 2026-08-11 | 新增 .importlinter.domain 配置文件（不修改既有 fixture 配置） | 真实代码依赖门禁与 fixture 门禁分离 | 两套门禁并行 |
| 2026-08-11 | 复审修复：Claim VERIFIED 不变量强制要求 evidence_relations | RESEARCH_INTEGRITY.md Hard Rule 1（复审前仅文档声明，domain 未强制） | 不变量由测试固化；新增 test_entities_invariants 用例 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-11 | — | APPROVED | 用户批准 Cursor Plan | m1_domain_kernel_实施_f7341045 |
| 2026-08-11 | APPROVED | IN_PROGRESS | 开始实施 | Stage 1 开始 |
| 2026-08-11 | IN_PROGRESS | VERIFYING | 全部实现与门禁完成 | m0 18 checks PASS |
| 2026-08-11 | VERIFYING | DONE | 复检 PASS | RECHECK-20260811-001 |
| 2026-08-11 | DONE | VERIFYING | M1 完成度端到端复审（独立执行） | 复审发现 Claim 不变量缺口，已修复 |
| 2026-08-11 | VERIFYING | DONE | 复审修复后全量回归 PASS | 180 pytest + 18 m0 checks PASS |

## 影响报告

- Domain/API/schema：新增 `packages/domain`（13 模块）、`adapters/contracts`、`schemas/model-profile.schema.json`；`validate_bundle.py` 注册表与 profiles strict 校验同步。
- 安全/凭据：无新增凭据；domain 零第三方依赖；loader 只读契约资产。
- 兼容性/迁移：VERSION=0.4.0 未变；uv.lock 未变（零新依赖）；既有 fixture 门禁与 TS 门禁全部保持 PASS。
- 上游版本：复用已 ADOPTED 的 jsonschema 4.26.0 / PyYAML 6.0.3，无新增上游。
- 下一项任务：M2 — Protocol Compiler + Preflight（BACKLOG M2/P0）。