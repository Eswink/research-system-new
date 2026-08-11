---
id: PLAN-20260811-002
slug: m3-model-relay
title: M3 Model Relay Compatibility 实施
status: DONE
created_at: 2026-08-11
updated_at: 2026-08-11
cursor_plan_uri: m3_model_relay_compatibility_31fcadc9
owners:
  - root-agent
authorization:
  source: cursor-plan
  ref: M3 Model Relay Compatibility（用户批准）
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260811-002-m3-model-relay.md
memory_entries:
  - .cursor/memory/entries/MEM-20260811-002-m3-model-relay-wiring.md
---

# PLAN-20260811-002 — M3 Model Relay Compatibility 实施

## 目标

实现 BACKLOG M3/P0 全部 10 项交付：LLMEndpoint CRUD + encrypted credential ref、manual ModelDefinition、endpoint test、optional `/models` discovery、capability probe、ModelEligibilityPolicy、endpoint health/circuit breaker、ModelRuntimeFingerprint、fallback audit、secret redaction。全部离线确定性测试，不引入真实 LLM 到 CI。

## 范围

- 包含：`packages/domain` 新增 circuit breaker / redaction / 扩展值对象；`packages/application/model_relay`（Ports + use cases）；`adapters/relay`（httpx gateway + SSE + env resolver + YAML/内存 store）；4 个新 schema + 4 个契约 fixture + validator 同步；httpx/tenacity 依赖与供应链登记；`docs/reliability/CIRCUIT_BREAKER.md` 与 `docs/integration/MODEL_PROBE.md`；application/relay 依赖边界契约。
- 不包含：M2 Preflight 编排、M4 Roles/Team、M5 全量 Ports+Fakes、M6 OpenHands 映射、M7 数据库/lease/outbox、真实 LLM 进 CI、Session 中途实际切换模型。

## 架构与数据流

```text
adapters/relay (httpx + MockTransport)
    → packages/application/model_relay (use cases + inward-owned Ports)
    → packages/domain (纯决策，零第三方依赖)
```

- EndpointStore / CredentialResolver / ModelRelayGateway 为 application 内层 Port；adapter 实现。
- circuit breaker 为 domain 纯函数状态机（CLOSED/OPEN/HALF_OPEN → EndpointHealth 映射）。
- fingerprint digest 用 canonical serialization（AGENTS.md §4 漂移可见性）。
- 错误在 use case 内转换为机器可读 ModelProbeResult，消息 redacted。

## 验收条件

- [x] AC-01：EndpointStore CRUD 复用 LLMEndpoint 不变量；credential_ref 走 CredentialResolver，明文 key 不落 Domain/log/audit。
- [x] AC-02：manual ModelDefinition 经 M1 loader 加载并可进入 eligibility 判定。
- [x] AC-03：endpoint test 返回机器可读 ModelProbeResult，错误消息 redacted。
- [x] AC-04：`/models` discovery 解析为候选列表（DISCOVERED 来源），默认不启用。
- [x] AC-05：capability probe 覆盖 chat/streaming/tool calling/structured output/usage，输出 ModelProbeResult + PROBED 断言。
- [x] AC-06：ModelEligibilityPolicy 纯决策；NATIVE 或经批准的 EMULATED；UNKNOWN/DEGRADED 视为不满足。
- [x] AC-07：circuit breaker 状态机迁移表映射 EndpointHealth，文档化。
- [x] AC-08：ModelRuntimeFingerprint 采集（requested/returned model、system fingerprint、safe headers、probe suite digest、observed capabilities）。
- [x] AC-09：fallback 决策仅当硬能力满足 + FallbackAuditRecord；Session 中途默认不切换。
- [x] AC-10：secret redaction 覆盖异常/header/config repr/telemetry 四类路径；Authorization 永不出现。
- [x] AC-11：契约资产变更后 validate_bundle.py + governance validate.py 全绿；m0 18 checks + 全部 pytest 通过；新增 import-linter 边界 0 broken。

## 实施清单

- [x] STEP-01：契约资产（4 个新 schema + llm-endpoint.schema 扩展 + fixtures + validator 同步 + 新文档入 INDEX）
- [x] STEP-02：依赖与工程接线（httpx/tenacity 落地 + 供应链登记 + mypy files + import-linter 边界）
- [x] STEP-03：domain 层（circuit breaker / redaction / ProbeSuiteSpec / FallbackAuditRecord / EndpointProbeSnapshot + 测试）
- [x] STEP-04：application 层（Ports + eligibility + endpoint policy + probe/discovery/fingerprint/fallback + 测试）
- [x] STEP-05：adapters/relay（httpx gateway + SSE + 错误分类 + env resolver + YAML/内存 store + MockTransport 离线测试）
- [x] STEP-06：回归与复审（m0 18 checks + 双 validator + recheck）

## 子代理使用

计划制定阶段使用 3 个并行 explore 子代理调查契约资产、运行时能力与上游、测试与 CI 门禁；实施阶段未委派。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | ---: | --- | --- | --- |
| 1 | 契约资产规格 / 运行时能力与上游 / 测试与 CI 门禁 | 3 | 完成 | 调查结论已并入 Cursor Plan |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | 全部门禁 | check | `run_all_checks.py --profile m0 --keep-going` | PASS: 18 deterministic checks |
| EV-02 | 全量测试 | test | `uv run pytest` | 339 passed |
| EV-03 | 系统契约 | check | `validate_bundle.py` | 验证通过 |
| EV-04 | 治理契约 | check | `governance validate.py` | 验证通过 |
| EV-05 | 依赖边界 | check | `pytest tests/architecture/python` | 7 passed（含 domain/application/relay） |
| EV-06 | 复检 | recheck | `RECHECK-20260811-002` | 待复检 |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-11 | `_join_url` 不拼 `/v1`，base_url 原样作为 API 根 | LLM_ENDPOINTS.md §3 明确"不偷偷拼 /v1" | gateway URL 与示例一致 |
| 2026-08-11 | SSE 解析、circuit breaker、redaction 自实现 | 避免 beta 依赖（httpx-sse）与对象内部状态（pybreaker） | domain 零依赖可穷尽测试 |
| 2026-08-11 | plan_fallback 改为 FallbackContext 参数对象 | ruff PLR0913 参数上限 5 | 决策上下文集中，可测试 |
| 2026-08-11 | ModelProbeResult 增加 error_message（redacted）字段 | AC-03 要求错误消息 redacted 后可读 | schema 与 domain 同步 |
| 2026-08-11 | build_fingerprint 移除 captured_at 外部注入 | 参数上限 + fingerprint 时间由内部生成 | 签名收敛 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-11 | — | APPROVED | 用户批准 Cursor Plan | m3_model_relay_compatibility_31fcadc9 |
| 2026-08-11 | APPROVED | IN_PROGRESS | 开始实施 | Stage A 开始 |
| 2026-08-11 | IN_PROGRESS | VERIFYING | 全部实现与门禁完成 | m0 18 checks PASS + 339 pytest |
| 2026-08-11 | VERIFYING | DONE | 复检 PASS | RECHECK-20260811-002 |

## 影响报告

- Domain/API/schema：新增 `packages/application/model_relay`、`adapters/relay`、`packages/domain/{circuit_breaker,redaction}.py`；`models.py` 扩展 4 个值对象；4 个新 schema + llm-endpoint.schema 扩展。
- 安全/凭据：secret 仅经 EnvCredentialResolver 密封解析；Authorization 永不落日志/audit/telemetry；redaction 覆盖四类路径。
- 兼容性/迁移：VERSION=0.4.0 未变；uv.lock 新增 7 包（httpx/tenacity 及传递依赖）；既有门禁全绿。
- 上游版本：httpx 0.28.1（BSD-3-Clause）、tenacity 9.1.4（Apache-2.0）已 ADOPTED 登记。
- 下一项任务：M2 — Protocol Compiler + Preflight（BACKLOG M2/P0）。