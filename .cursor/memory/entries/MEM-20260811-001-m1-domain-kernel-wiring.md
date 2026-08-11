---
id: MEM-20260811-001
title: M1 Domain Kernel 接线与契约资产落地事实
status: ACTIVE
created_at: 2026-08-11
updated_at: 2026-08-11
scope: repository
confidence: 0.95
review_after: 2026-11-11
source_plans:
  - .cursor/plans/tasks/PLAN-20260811-001-m1-domain-kernel.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260811-001-m1-domain-kernel.md
supersedes: []
tags: [m1, domain-kernel, contract-assets, engineering-wiring]
---

# MEM-20260811-001 — M1 Domain Kernel 接线与契约资产落地事实

## 做了什么

M1 完成，验证结果：18 个 m0 确定性门禁 PASS、180 pytest 通过、两个契约 validator 通过、零新增依赖（uv.lock 不变）。落地事实：

1. `packages/domain/` 为纯 stdlib 域内核（13 模块），零第三方依赖；`adapters/contracts/` 基于已 ADOPTED 的 jsonschema 4.26.0 / PyYAML 6.0.3。
2. canonical digest 规则唯一来源：`docs/architecture/DETERMINISTIC_SERIALIZATION.md`；状态机迁移表：`docs/reliability/RUN_STATE_MACHINE.md`。
3. 新增 `schemas/model-profile.schema.json`（ModelProfile 之前被 4 处 schema 语义引用但无 schema 文件），`validate_bundle.py` 的 `expected_schema_files` 与 profiles strict 校验已同步。
4. 新增 `.importlinter.domain`（真实代码依赖门禁）+ `tests/architecture/python/test_domain_boundaries.py`。

## 为什么这样做

- mypy 对命名空间包会有 `domain.core` 与 `packages.domain.core` 双重解析：在 `packages/` 下加 `__init__.py` 即可消除；`mypy_path = "."` 反而会引入双重模块名，不要设置。
- pytest 无法 import `packages.*`：`[tool.pytest.ini_options] pythonpath = ["."]` 后解决（仓库无 editable install）。
- ruff format / 源码规模阈值（≤300 行、函数 ≤50 行、CCN ≤10、max-args 5）对 `packages/`、`adapters/` 自动生效：`state_machines.py` 363 行被拆分，loader 317 行被拆为 base/roles/models/tasks 四个模块。
- `run_all_checks.py` 用 `sys.executable` 运行各检查：本地必须 `uv run --frozen --no-sync python -B .../run_all_checks.py`（等价 CI），直接系统 `python` 会因缺 dev 依赖误报失败。
- examples 契约文件是“嵌套 map + 扁平化 id”结构（`models: {research_alpha: {...}}`），与 system-spec validator 的加载方式一致；loader 须先构造 `{"id": key, ...}` 再校验 schema。
- `ContractLoadError` 不能做成 frozen dataclass（`pytest.raises` 无参构造会触发 `TypeError: super(type, obj)`）。
- `AgentBinding`/`ModelBinding` 用枚举 `mode`，schema 用 `type` 键，loader 内显式翻译。

## 怎么做与复现

1. 全量门禁：`uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going` → 18 checks PASS。
2. 单元测试：`uv run pytest` → 178 passed。
3. 契约 validator：`python -B .cursor/skills/system-spec-check/scripts/validate_bundle.py`、`python -B .cursor/skills/governance-check/scripts/validate.py`。
4. 依赖边界：`uv run pytest tests/architecture/python` → 4 passed（含 domain purity）。

## 适用边界

- 适用于：M2+ 在 `packages/`、`adapters/` 继续扩展的接线方式；新增 schema 的同步流程（注册表 + strict 校验 + examples）。
- 不适用于：M0 之前的工具链历史（MEM-20260810-001 已 RETIRED）；未来若改为 uv workspace member + editable install，接线方式会变化。

## 失效与复核触发器

- 到达 `review_after`（2026-11-11）。
- pyproject 的 mypy/pytest/ruff 配置或 uv 工程模式变化（如启用 workspace member）。
- `validate_bundle.py` 的 `expected_schema_files` 注册表机制变化。

## 复审补充（2026-08-11）

- 独立 M1 完成度复审发现：`Claim` 的 VERIFIED 不变量（RESEARCH_INTEGRITY Hard Rule 1 "VERIFIED Claim 必须有 Evidence"）仅存在于文档，`Claim.__post_init__` 未强制。已修复：VERIFIED 状态无 `evidence_relations` 时抛 ValueError，并新增测试用例。
- 复审全量回归：180 pytest + 18 m0 checks PASS；OpenHands SDK（commit d66f10dc）源码级核对确认 M1 domain 对 AgentSession 状态（PAUSED/STUCK/waiting_for_confirmation）、resume 工具集兼容、`execute_tool` 绕过确认/安全的边界设计与其真实 API 一致。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20260811-001-m1-domain-kernel.md` | M1 范围与验收 |
| recheck | `.cursor/plans/rechecks/RECHECK-20260811-001-m1-domain-kernel.md` | PASS 结论 |
| repository | `pyproject.toml`（mypy files / pytest pythonpath） | 接线配置 |
| repository | `.importlinter.domain` | 依赖纯度门禁 |
| repository | `packages/domain/__init__.py` 等 | 包结构 |