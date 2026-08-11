---
id: RECHECK-20260811-002
plan_id: PLAN-20260811-002
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-08-11
completed_at: 2026-08-11
reviewer: root-agent-independent-pass
baseline_ref: M1 DONE + 复审 PASS（BACKLOG M1/P0 全勾选，RECHECK-20260811-001 PASS）
checked_head: working-tree
---

# RECHECK-20260811-002 — M3 Model Relay 复检

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260811-002-m3-model-relay.md`
- 验收条件：AC-01..AC-11（见下）
- 变更范围：`packages/domain/{circuit_breaker,redaction}.py`、`packages/domain/models.py` 扩展、`packages/application/model_relay/`、`adapters/relay/`、4 个新 schema、`llm-endpoint.schema.json` 扩展、`examples/contracts/` 4 个 fixture、`validate_bundle.py` 同步、`pyproject.toml`/`uv.lock`/`UPSTREAM_COMPONENTS.yaml`/`LICENSE_MATRIX.md`/`SOURCE_SNAPSHOT.md`/`UPSTREAM_FINDINGS_V0_4_0.md`、`.importlinter.application`/`.importlinter.relay`/`.importlinter.domain`、`docs/reliability/CIRCUIT_BREAKER.md`、`docs/integration/MODEL_PROBE.md`、`docs/INDEX.md`、`BACKLOG.md`、`CHANGELOG.md`、`tests/`
- 基线：M1 完成后（HEAD 185a752、180 pytest、18 m0 checks）

## 检查结果

| Gate | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| G-01 | 范围与架构 | 变更全部位于 M3 批准范围；application 只依赖 domain（`.importlinter.application` 0 broken），relay 无厂商 SDK（`.importlinter.relay` 0 broken），domain 纯度保持（`.importlinter.domain` 0 broken） | PASS |
| G-02 | 验收条件 | 见下表 AC-01..AC-11 逐项独立证据 | PASS |
| G-03 | lint/typecheck/test | `run_all_checks.py --profile m0 --keep-going` → 18 deterministic checks PASS；`uv run pytest` → 339 passed | PASS |
| G-04 | 安全与凭据 | secret 仅经 EnvCredentialResolver 密封解析；`test_redaction.py` 断言 Authorization/api-key 永不进入输出；config repr 不暴露 credential_ref；供应链 httpx/tenacity 已 ADOPTED 登记（sdist sha256 与 uv.lock 一致） | PASS |
| G-05 | 兼容性与迁移 | `validate_bundle.py` 通过（4 个新 schema + fixtures 已注册）；governance `validate.py` 通过；VERSION=0.4.0 单一版本源未变；uv.lock 与 pyproject 一致（`uv lock --check` 语义） | PASS |
| G-06 | 计划、记忆、供应链 | 任务计划 + 复检 + 状态历史齐备；httpx/tenacity 复用成熟开源并 pin + license evidence + upgrade gate；无未 pin 依赖 | PASS |

## 验收条件逐项证据

| AC | 交付项 | 独立证据 | 结果 |
| --- | --- | --- | --- |
| AC-01 | EndpointStore CRUD + credential ref | `tests/adapters/relay/test_endpoint_store.py` 12 项（内存/YAML CRUD、持久化、不变量拒绝）；`test_credential_resolver.py` 4 项（env 解析、缺失/空拒绝、SecretValue repr 脱敏） | PASS |
| AC-02 | manual ModelDefinition 进入 eligibility | 复用 M1 `load_models`；`tests/application/test_model_eligibility.py` 10 项对 ModelDefinition 硬能力判定 | PASS |
| AC-03 | endpoint test 机器可读 + redacted | `tests/application/test_probe_use_cases.py`（auth 失败 MODEL_AUTH、异常消息 redacted）；`tests/adapters/relay/test_gateway.py`（401/403/429/400/422/500 分类、错误消息 redacted） | PASS |
| AC-04 | discovery DISCOVERED 不自动启用 | `tests/application/test_probe_use_cases.py::TestDiscoveredModels`（source 强制 DISCOVERED，PROBED 被拒）；gateway `list_models` MockTransport 解析 | PASS |
| AC-05 | capability probe 五类能力 | `test_probe_use_cases.py::TestRunProbe`（CHAT/STREAMING/TOOL_CALLING_NATIVE/STRUCTURED_OUTPUT_NATIVE/SYSTEM_FINGERPRINT/USAGE_REPORTING + PROBED 断言 probe_version） | PASS |
| AC-06 | ModelEligibilityPolicy | `test_model_eligibility.py`（全满足 ALLOW、缺失/UNKNOWN/DEGRADED 拒绝、EMULATED 默认拒绝/批准放行） | PASS |
| AC-07 | circuit breaker 迁移表 + EndpointHealth | `tests/domain/test_circuit_breaker.py` 19 项（阈值打开、超时半开、半开成功/失败、非法迁移、HEALTHY/DEGRADED/OPEN_CIRCUIT/DISABLED 映射）；`docs/reliability/CIRCUIT_BREAKER.md` 迁移表 | PASS |
| AC-08 | ModelRuntimeFingerprint 采集 | `tests/application/test_fingerprint.py` 8 项（config digest 稳定/漂移、probe suite digest、fingerprint 字段、calibration digest 确定性） | PASS |
| AC-09 | fallback 决策 + audit | `tests/application/test_fallback.py` 6 项（合格候选选择、不合格跳过+audit、primary 排除、无候选、task/policy 引用、session_switch 标志） | PASS |
| AC-10 | secret redaction 四类路径 | `tests/domain/test_redaction.py` 12 项（bearer/api-key/URL 凭据、异常、header 白名单、config repr、telemetry） | PASS |
| AC-11 | 契约资产 + 全部门禁 | `validate_bundle.py` 验证通过（4 新 schema + fixtures 注册 + llm-endpoint 扩展）；governance validate.py 通过；m0 18 checks PASS；339 pytest；架构边界 7 passed | PASS |

## Findings

| ID | 严重度 | 发现 | 处置 |
| --- | --- | --- | --- |
| F-01 | INFO | 本地直接 `python run_all_checks.py` 会用系统解释器；须用 `uv run --frozen --no-sync`（与 M1 F-01 相同） | 已按 CI 等价方式验证 |
| F-02 | INFO | gateway `_join_url` 不再拼 `/v1`；base_url 原样作为 API 根（LLM_ENDPOINTS.md §3） | 测试断言与文档一致 |
| F-03 | INFO | `packages/application` 与 `adapters` 新增 `__init__.py` 以解决 mypy package-bases 歧义 | 已修复，mypy 88 files 无问题 |

## 结论

- 结果：`PASS`
- 理由：全部 11 项 AC 均有独立测试/校验证据；m0 18 个确定性门禁全绿；339 pytest 通过；双契约 validator 全绿；新增依赖 pin + 供应链登记完整；无真实 LLM/网络/凭据进入 CI。
- 后续动作：PLAN-20260811-002 标记 DONE 并登记 ALL_PLAN；建议下一项进入 M2（Protocol Compiler + Preflight）。