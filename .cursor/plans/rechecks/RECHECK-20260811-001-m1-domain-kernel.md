---
id: RECHECK-20260811-001
plan_id: PLAN-20260811-001
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-08-11
completed_at: 2026-08-11
reviewer: root-agent-independent-pass
baseline_ref: M0 DONE (BACKLOG)
checked_head: working-tree
---

# RECHECK-20260811-001 — M1 Domain Kernel 复检

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260811-001-m1-domain-kernel.md`
- 验收条件：BACKLOG M1/P0 的 7 项交付（bootstrap validation、Domain entities/enums/invariants、JSON/YAML schema loaders、Run/Phase/Task state machines、RunManifest+Revision+digest、append-only Usage Ledger、Artifact digest/verification）
- 变更范围：`packages/domain/`、`adapters/contracts/`、`schemas/model-profile.schema.json`、`docs/architecture/DETERMINISTIC_SERIALIZATION.md`、`docs/reliability/RUN_STATE_MACHINE.md`、`docs/INDEX.md`、`pyproject.toml`、`.importlinter.domain`、`.cursor/skills/system-spec-check/scripts/validate_bundle.py`（expected_schema_files + profiles strict 校验）、`tests/`
- 基线：M0 完成后（BACKLOG 前三项勾选，全部 68 测试通过）

## 检查结果

| Gate | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| G-01 | 范围与架构 | 变更全部位于批准范围（M1 Domain Kernel & Contract Assets），未扩大至 M2+；Domain 不 import jsonschema/yaml/fastapi 等（`.importlinter.domain` 0 broken） | PASS |
| G-02 | 验收条件 | 见下表 AC-01..AC-07 逐项独立证据 | PASS |
| G-03 | lint/typecheck/test | `uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going` → 18 deterministic checks PASS；178 pytest 通过 | PASS |
| G-04 | 安全与凭据 | 无新增凭据；loader 只读 schemas/examples（无网络）；domain 纯 stdlib | PASS |
| G-05 | 兼容性与迁移 | `validate_bundle.py` 通过（新增 model-profile.schema.json 已注册）；`governance validate.py` 通过；VERSION=0.4.0 单一版本源未变；uv.lock 未变（零新依赖） | PASS |
| G-06 | 计划、记忆、供应链 | 任务计划、复检、状态历史齐备；jsonschema/PyYAML 复用已 ADOPTED 登记项；无未 pin 依赖 | PASS |

## 验收条件逐项证据

| AC | 交付项 | 独立证据 | 结果 |
| --- | --- | --- | --- |
| AC-01 | bootstrap validation script in CI | `tests/domain/test_bootstrap.py`（domain 导入 + digest 确定性回归）+ `tests/architecture/python/test_domain_boundaries.py`（domain 可导入）被 `python/tests` 门禁收集并全绿 | PASS |
| AC-02 | Domain entities/enums/invariants | `packages/domain/` 13 个模块；`test_entities_invariants.py` 19 项覆盖枚举唯一、frozen 不变量、跨模块引用 | PASS |
| AC-03 | JSON/YAML schema loaders | `adapters/contracts/`（base + roles/models/tasks loaders）；`tests/loaders/test_contract_loaders.py` 12 项基于真实 examples（26 roles / 8 agents / 3 teams / 3 models / 2 contracts） | PASS |
| AC-04 | Run/Phase/Task state machines | `packages/domain/{run,phase,task,session}_state.py` + `state_base.py`；迁移表写入 `docs/reliability/RUN_STATE_MACHINE.md`；`test_state_machines.py` 25 项（合法/非法/terminal 不可回退/cancellation） | PASS |
| AC-05 | RunManifest + Revision + digest | `packages/domain/manifest.py` + `docs/architecture/DETERMINISTIC_SERIALIZATION.md`；`test_manifest.py` 10 项（digest 稳定性/不可变/Revision 语义） | PASS |
| AC-06 | append-only Usage Ledger | `packages/domain/budget.py` UsageLedger；`test_ledger.py` 7 项（append-only/重复拒绝/frozen/UNKNOWN 成本） | PASS |
| AC-07 | Artifact digest/verification | `packages/domain/artifacts.py`；`test_artifacts.py` 7 项（digest 匹配/篡改拒绝/sha256 前缀） | PASS |

## Findings

| ID | 严重度 | 发现 | 处置 |
| --- | --- | --- | --- |
| F-01 | INFO | 本地直接 `python run_all_checks.py` 会用系统解释器（缺 dev 依赖）；CI 通过 `uv run --frozen --no-sync` 提供 venv 解释器，本地须同样执行 | 已按 CI 等价方式验证，无代码改动 |
| F-02 | INFO | `AgentBinding`/`ModelBinding` 等 binding 值对象与 schema 的 `type` 键命名存在 mapper 翻译 | loader 内已显式映射，测试覆盖 |

## 结论

- 结果：`PASS`
- 理由：全部 7 项 M1/P0 验收条件均有独立测试证据；18 个 m0 确定性门禁全绿；两个契约 validator 全绿；零新增依赖、零 lockfile 变更、VERSION 未变。
- 后续动作：PLAN-20260811-001 已更新为 DONE 并登记 ALL_PLAN；建议下一步进入 M2（Protocol Compiler + Preflight）或按 BACKLOG 顺序继续。

## 2026-08-11 独立端到端复审（supplement）

本补充由独立复审执行，范围 = M1 完成度复审（含 upstream 源码级核对与修复后回归）。

| 项 | 证据 | 结果 |
| --- | --- | --- |
| 全量测试（复审基线） | `uv run pytest` → 180 passed（含 domain 19 + state machines 25 + manifest 10 + serialization 18 + ledger 7 + artifacts 7 + loaders 12 + value objects 15） | PASS |
| m0 全量门禁（复审基线与修复后各一次） | `run_all_checks.py --profile m0 --keep-going` → 18 deterministic checks PASS | PASS |
| 双契约 validator | validate_bundle.py + governance validate.py | PASS |
| Claim 不变量缺口 | RESEARCH_INTEGRITY Hard Rule 1 声明"VERIFIED Claim 必须有 Evidence"，但 `Claim.__post_init__` 未强制；已修复并新增测试（VERIFIED 无 evidence_relations 被拒） | FIXED |
| 非法契约拒绝 | agent-spec schema 对未知 binding type / 缺必填 抛 ContractLoadError | PASS |
| domain 纯度 | `.importlinter.domain` 0 broken；`tests/architecture/python` 4 passed | PASS |
| upstream 核对 | OpenHands SDK commit d66f10dc：`ConversationExecutionStatus` 含 PAUSED/STUCK/waiting_for_confirmation；`execute_tool` 文档明确绕过 confirmation/security；`AgentBase.verify` 要求 tool 只能增不能删；模型/LLM 配置可自由变更 | 与 M1 domain 设计一致 |
| 临时代码/技术债 | packages/adapters 无 TODO/FIXME/stub/NotImplemented/pragma 跳过 | PASS |