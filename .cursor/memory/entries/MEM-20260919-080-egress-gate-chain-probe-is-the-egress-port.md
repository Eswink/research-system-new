---
id: MEM-20260919-080
title: "受控出网门链：探针本身就是出网口（策略必须在触网前生效）；ports 不能 import model_relay（__init__ 反向导入）"
status: ACTIVE
created_at: 2026-09-19
updated_at: 2026-09-19
scope: repository
confidence: 0.9
review_after: 2027-09-19
source_plans:
  - .cursor/plans/tasks/PLAN-20260919-108-egress-gate-chain.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260919-108-egress-gate-chain.md
supersedes: []
tags:
  - egress-control
  - endpoint-url-policy
  - dependency-boundaries
  - preflight
  - falsification
---

# 受控出网门链（GOAL-20260919-007 / EC-02）

## 做了什么

给「执行体 → LLM endpoint」这条唯一出网口装了一条**有序门链**，并让它**在触网之前**生效：

```text
URL 策略（endpoint_url_refusal ← validate_endpoint_url）
  → 凭据存在性 → 端点健康 → 模型能力匹配
```

- `packages/application/model_relay/endpoint_policy.py`：新增薄包装 `endpoint_url_refusal(base_url, policy) -> str | None`。
- `packages/domain/protocols.py`：`PreflightFindingCode.ENDPOINT_URL_DENIED`。
- `packages/application/ports/resource_catalog.py`：`PreflightContext.endpoint_url_denials: Mapping[str, str]`。
- `packages/application/preflight/checks.py`：`_check_endpoint` 在 health 之前插入 URL 环，**被拒即短路**。
- `services/api/preflight_support.py`：`build_endpoint_url_denials`；`_probe_endpoint` 在解析凭据**之前**做 URL 裁决，被拒 ⇒ `UNKNOWN` 且**不出网**。
- `services/api/run_execution.py`（新 `_live_preflight`）/ `team_support.py`：两条生产控制面路径注入裁决。

## 为什么这样做

1. **探针本身就是出网口**。此前 `validate_endpoint_url` 只被两个**手动**操作调用
   （`/llm-endpoints/{id}/test`、`/models/{id}/probe`）；`start_run` 路径上的
   `build_endpoint_health` 对目录内**每个** endpoint 直接 `gateway.probe_connectivity`。
   也就是说：把 `http://127.0.0.1:8080/v1` 写进目录，run **会先对它发起真实 HTTP 请求**，
   然后才在 preflight 里被判不健康。策略加在「拒绝」上而不加在「触网」上，等于没加。
2. **链要短路，不能报派生事实**。URL 被拒时探测没有发生，此时把 health 报成
   `ENDPOINT_UNHEALTHY: health is unknown` 是**派生噪声**：它指向「端点不健康」，
   而真实阻塞事实是「策略没放行」。门链语义 = 停在第一环并只报那一环。
3. **`ports` 不能 import `model_relay`**。`model_relay/__init__.py` 反向
   `from packages.application.ports import (...)`，而 `packages/application/__init__.py`
   又在 `ports` 之前执行；`from packages.application.model_relay.endpoint_policy import X`
   会先执行 `model_relay/__init__.py`，落在**部分初始化**的 `ports` 上（是否真的报错取决于
   导入顺序，属软失败点）。因此策略对象不进 `PreflightContext`，只把**裁决结果**
   （`Mapping[str, str]`）注入，与同 dataclass 里的 `provider_health` 同口径。

## 怎么做与复现

- 门链判据：`uv run --frozen --no-sync python -B -m pytest tests/api/test_runtime_egress_gate.py -q` ⇒ **9 passed**。
  - 「出站 0」用**两个独立可观测面**：记录型 `httpx.BaseTransport` 注入真实
    `OpenAIChatGateway`（传输层计数），以及 `FakeBase.calls` / `method_calls`
    （端口层计数）。两者都不是「没抛异常」。
  - **反面必须同跑**（同一 URL、只把策略放开 ⇒ 替身确实收到请求），否则「0 次」可能是恒真。
- **反证三条**（改红再复原，记录在 RECHECK-20260919-108）：
  1. 删 `_probe_endpoint` 的 URL 短路 ⇒ 2 failed（传输层零出站 + 端到端零探测同时红）；
  2. 删 `_check_endpoint` 的 URL 环 ⇒ 2 failed，且失败形态降级为**不点名**的 `ENDPOINT_UNHEALTHY`；
  3. 删 `run_execution` 的 `endpoint_url_denials=` 注入 ⇒ 1 failed。
- 结构判据：全仓 `ipaddress` 只出现在 `packages/application/model_relay/endpoint_policy.py`
  （`::test_a_single_host_judgement_exists_in_the_repo`）——「新造第二份 host 判据」可判负。

## 适用边界（踩过的坑）

- **未注入 = 未声明该面**（沿用 `provider_health` 口径）：手写 `PreflightContext` 的调用方
  不会因缺 `endpoint_url_denials` 而失败（fail-open）。生产两条路径都注入，且探针侧短路是
  **无条件** fail-closed，因此生产面没有这个口子；将来若出现第三条生产构造路径必须同步注入。
- **门链不按基质分叉**：Fake 与真实 runtime 走同一条链，所以不可能出现「真实 runtime 比
  demo 更松」。副作用是目录里写 `localhost` 默认即被拒（要放行只能显式
  `RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS=1`）。
- **既有夹具为什么不受影响**：`host` 判据认的是 `localhost` / `127.0.0.1` / `::1` 字面量与
  可解析 IP；`http://localtest.me:9999` 两条都不是 ⇒ 判 `domain` ⇒ 放行。改判据前先看这条。
- **射程只到 LLM endpoint**：tool provider（MCP / REST / 远端 worker）的出网仍各自为政。
- `endpoint_url_denials` 的 value 只承载 URL 策略理由；health / 凭据仍是既有 finding，
  不要为了「统一」把四环合并成一个 code——那会丢掉「点名缺哪条事实」的可判性。

## 来源

- `.cursor/plans/tasks/PLAN-20260919-108-egress-gate-chain.md`
- `.cursor/plans/rechecks/RECHECK-20260919-108-egress-gate-chain.md`
- 代码：`packages/application/model_relay/endpoint_policy.py`、
  `packages/application/preflight/checks.py`、`services/api/preflight_support.py`、
  `services/api/run_execution.py`
- 判据：`tests/api/test_runtime_egress_gate.py`
