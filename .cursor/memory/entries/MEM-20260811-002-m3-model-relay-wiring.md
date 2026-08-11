---
id: MEM-20260811-002
title: M3 Model Relay 运行层接线与契约资产落地事实
status: ACTIVE
created_at: 2026-08-11
updated_at: 2026-08-11
scope: repository
confidence: 0.95
review_after: 2026-11-11
source_plans:
  - .cursor/plans/tasks/PLAN-20260811-002-m3-model-relay.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260811-002-m3-model-relay.md
supersedes: []
tags: [m3, model-relay, openai-compatible, httpx, contract-assets]
---

# MEM-20260811-002 — M3 Model Relay 运行层接线与契约资产落地事实

## 做了什么

M3 完成，验证结果：18 个 m0 确定性门禁 PASS、339 pytest 通过、两个契约 validator 通过。落地事实：

1. `packages/application/model_relay/`（inward-owned Ports + eligibility + probe/discovery/fingerprint/fallback use cases）与 `adapters/relay/`（httpx gateway + SSE 解析 + env resolver + YAML/内存 store）为第一批 application/adapter 产品代码，遵循 `adapters → application → domain` 边界。
2. 新增依赖 httpx 0.28.1（BSD-3-Clause）、tenacity 9.1.4（Apache-2.0），pin + sdist sha256 登记到 `UPSTREAM_COMPONENTS.yaml` / `LICENSE_MATRIX.md` / `SOURCE_SNAPSHOT.md` / `UPSTREAM_FINDINGS_V0_4_0.md`。
3. 新增 4 个契约 schema（probe-result / endpoint-health / model-runtime-fingerprint / fallback-audit-record）+ 4 个 fixture，`llm-endpoint.schema.json` 扩展 discovery/circuit_breaker；`validate_bundle.py` 的 `expected_schema_files` 与 `check_yaml_and_references` 已同步。
4. circuit breaker 为 domain 纯函数状态机（CLOSED/OPEN/HALF_OPEN → EndpointHealth），迁移表 `docs/reliability/CIRCUIT_BREAKER.md`；probe suite 规格 `docs/integration/MODEL_PROBE.md`。

## 为什么这样做

- **URL 拼接不拼 `/v1`**：`LLMEndpoint.base_url` 原样作为 API 根（如 `/api/v1`），gateway 只追加 `/models` 或 `/chat/completions`；LLM_ENDPOINTS.md §3 明确"不偷偷拼 /v1"。用户配置的中转站 URL 常已含版本前缀。
- **不用 openai-python SDK / pybreaker / httpx-sse**：协议层是 OPENAI_COMPATIBLE，httpx 提供原语级控制（header 白名单采集、fingerprint、SSE 原始流）；pybreaker 状态在对象内部不易穷尽测试；httpx-sse 是 beta。SSE 行解析（约 40 行）、circuit breaker、redaction 均自实现，domain 零依赖可单测。
- **离线确定性测试**：`httpx.MockTransport(handler)` 返回预置 Response（可带 `text/event-stream`），`tests/adapters/relay/test_gateway.py` 完全不联网；错误分类 401/403→MODEL_AUTH、429→MODEL_RATE_LIMIT、400/422→MODEL_INCOMPATIBLE。
- **供应链门禁**：ADOPTED 组件必须同时在 `[project] dependencies` 与 dev group，且 sdist sha256 与 `uv.lock` 一致（`validate_bundle.py check_supply_chain`）。
- **mypy package-bases**：新增 `adapters/` 到 mypy files 后，`adapters/contracts/base.py` 出现 `contracts.base` / `adapters.contracts.base` 双重解析；在 `adapters/__init__.py`、`packages/application/__init__.py` 补齐后消除。
- **PLR0913（max-args 5）对函数参数是硬约束**：`plan_fallback`/`build_fingerprint` 参数超限，用 `FallbackContext` 参数对象与移除可选参数收敛签名。
- **redaction 原则**：config repr 不输出 credential_ref 名称（用 `<configured>` 掩码）；响应头只采集白名单 `SAFE_RESPONSE_HEADERS`，Authorization/api-key 永不进入结果。

## 怎么做与复现

1. 全量门禁：`uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going` → 18 checks PASS。
2. 单元测试：`uv run pytest` → 339 passed。
3. 契约 validator：`python -B .cursor/skills/system-spec-check/scripts/validate_bundle.py`、`python -B .cursor/skills/governance-check/scripts/validate.py`。
4. 依赖边界：`uv run pytest tests/architecture/python` → 7 passed（domain / application / relay 三层）。

## 适用边界

- 适用于：M2/M6+ 复用 model_relay Ports 与 gateway（Protocol Compiler 的 model resolution、OpenHands LLM 配置映射）；新增 schema 的同步流程；任何新增 OpenAI-compatible 集成。
- 不适用于：M6 OpenHands 的 provider naming（由 OpenHandsAdapter→litellm 层负责）；M7 数据库化存储（当前 EndpointStore 为文件/内存）；真实 LLM 集成测试（默认离线）。

## 失效与复核触发器

- 到达 `review_after`（2026-11-11）。
- OpenAI Chat Completions 规范大幅变更（当前基线 openapi.yaml v2.3.0）。
- httpx/tenacity 版本升级或 `uv.lock` 结构变化。
- `validate_bundle.py` 注册表机制变化。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20260811-002-m3-model-relay.md` | M3 范围与验收 |
| recheck | `.cursor/plans/rechecks/RECHECK-20260811-002-m3-model-relay.md` | PASS 结论 |
| repository | `adapters/relay/gateway.py`（`_join_url`） | URL 拼接规范 |
| repository | `UPSTREAM_COMPONENTS.yaml` | httpx/tenacity 供应链登记 |
| repository | `packages/domain/circuit_breaker.py` | 熔断状态机 |
| repository | `pyproject.toml`（mypy files / dependencies） | 接线配置 |