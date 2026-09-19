---
id: PLAN-20260919-108
slug: egress-gate-chain
title: 受控出网门链：URL 策略 → 凭据存在性 → 端点健康 → 能力匹配（每项点名拒绝、policy 不允许时出站 0）（EC-02）
status: DONE
created_at: 2026-09-19
updated_at: 2026-09-19
parent_goal: GOAL-20260919-007
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260919-007 cycle 2 = EC-02。授权来源：2026-09-19 用户 goal 模式指令（自动化循环推进、无需逐轮确认）；受控出网边界与 push-to-main-for-CI 授权见 GOAL-20260919-007 frontmatter `authorization.ref`。本 PLAN 遵守：默认 runtime 保持 Fake、不引入新依赖、凭据只从环境变量读、真实端点调用永不进默认 CI、默认 deny 姿态不得放松。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260919-108-egress-gate-chain.md
memory_entries:
  - MEM-20260919-080
---

# PLAN-20260919-108 — 受控出网门链（GOAL-007 cycle 2 = EC-02）

## 目标

真实执行体一旦被选中，它**唯一**的出网口是 LLM endpoint。今天这条口子上**只有三条
判据中的两条**在半途，且第一条完全缺失：

| 事实 | 今天的状态 |
| --- | --- |
| endpoint URL 策略 | **完全缺失**：`validate_endpoint_url` 只被 `/llm-endpoints/{id}/test` 与 `/models/{id}/probe` 两个手动操作调用；run 路径与 runtime 路径从不调用 |
| 凭据存在性 | 有（`_credential_findings` → `CREDENTIAL_MISSING`） |
| 端点健康 | 有（`_check_endpoint` → `ENDPOINT_UNHEALTHY`） |
| 模型能力匹配 | 有（`_check_record_eligibility` → `MODEL_ELIGIBILITY`） |

而**探针本身是无门禁的出站**：`services/api/preflight_support.py::_probe_endpoint` 直接
`deps.gateway.probe_connectivity(endpoint, credential)`，不看 URL 策略——即使用户把
`https://127.0.0.1:8080/v1` 写进目录，`start_run` 也会先对它发起一次真实 HTTP 请求
（在"被拒绝"之前）。

本 PLAN 把这条口子收敛成**一条有序门链**，且**受控出网边界在探针之前**：

```text
URL 策略（复用 EndpointUrlPolicy / validate_endpoint_url）
  → 凭据存在性
  → 端点健康
  → 模型能力匹配
```

每一项**点名**拒绝（哪一个 endpoint / 哪一条事实 / 怎么修），并且 **URL 被拒时出站调用数为 0**
（在传输层替身上可观测，不是"没抛异常"）。

本 PLAN **只做 EC-02**：离线全链（EC-03）、诚实披露（EC-04）、工具面边界（EC-05）、
`tool_pack.*`（EC-06）各自独立成 cycle。

## 先探明再动手（本轮只读勘察已确认的事实）

1. **`validate_endpoint_url` 只有两个调用点**，都在 `packages/application/model_relay/probe.py`
   （`run_endpoint_test:117-124`、`run_probe:242-249`），由两个**手动**路由传入
   `deps.endpoint_url_policy`。run 路径（`run_execution.py` / `team_support.py`）不传。
2. **探针无门禁**：`_probe_endpoint`（`services/api/preflight_support.py:66-75`）先解析凭据、
   再探测，**没有 URL 策略判断**；凭据缺失时返回 `UNKNOWN` 且**不出网**（既有行为，可复用）。
3. **`EndpointUrlPolicy` 是纯值对象**（`model_relay/endpoint_policy.py`，仅依赖
   `ipaddress` / `urlparse` / `dataclasses`）；`RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS`
   唯一读取点在 `services/api/settings.py:127-130`，默认 `"0"` ⇒ **默认 deny**。
4. **`ports` 不能 import `model_relay`**：`model_relay/__init__.py` 反向 `from
   packages.application.ports import (...)`，而 `packages/application/__init__.py` 也在
   `ports` 之前执行——任何 `ports → model_relay` 的导入都会落在**部分初始化**的模块上。
   因此门链的 URL 裁决**不把策略对象塞进 `PreflightContext`**，而是由服务层先裁决、
   以中性 `Mapping[str, str]`（endpoint_id → 拒绝理由）注入，与同处一处的
   `provider_health`（第 88-91 行注释：未注入 key 视为注入方未声明该面）**同口径**。
5. **host 判据全仓只有一份**：`rg ipaddress` 的非测试命中只有
   `packages/application/model_relay/endpoint_policy.py` 两行（`import ipaddress`、
   `ipaddress.ip_address(host)`）⇒「新造第二份 host 判据」可用**结构判据**判负。
6. **findings 不进 OpenAPI / web types**：`ENDPOINT_UNHEALTHY` 只在
   `packages/domain/protocols.py`、`packages/application/preflight/checks.py`、
   `services/api/preflight_support.py`、两个测试、一份 web 数据夹具里出现；新增枚举成员
   不牵动 OpenAPI 快照、`types.ts`、e2e 夹具。
7. **既有的 `localtest.me` 用法不受影响**：`tests/api/test_catalog_merge.py` 与
   `tests/api/test_api_restart_recovery.py` 用 `http://localtest.me:9999`，该主机名不是
   `localhost` 字面量、也不是可解析 IP ⇒ `_host_kind` 判 `domain` ⇒ 策略放行（与被拒的
   `tests/api/test_secret_redaction.py` 的 `http://localhost:9999/v1` 形成对照）。
8. **拒绝语义已可被调用方读到**：`compile_and_preflight` 的 ERROR finding 会让 run 在冻结前
   `FAILED`（`packages/application/run_orchestration/service.py:145-147`），因此门链的每项
   只要产出 ERROR finding 就同时满足「拒绝」与「点名」。

## 口径

- **「链」是有序的**：URL 策略先于凭据/健康——URL 被拒时该 endpoint 的探测**根本不该发生**，
  健康事实在那一刻**不可知**，把它报成 `ENDPOINT_UNHEALTHY: health is unknown` 是**派生噪声**。
  因此 URL 被拒时 `_check_endpoint` **在该 endpoint 上短路**，只报 `ENDPOINT_URL_DENIED`。
- **门链不按基质分叉**：门链是**无条件**的（对 Fake 与真实 runtime 同一条），因此不可能
  出现「真实 runtime 比 Fake 更松」的缝隙；代价是默认路径里写 `localhost` 也会被拒——
  这正是 `RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS=1` 存在的意义，默认 deny 不放松。
- **「出站调用 0」的判据是传输层替身计数**：注入 `OpenAIChatGateway(transport=...)` 的
  记录型 transport，断言 `transport.calls == 0`；**反面同样要证**（策略允许时计数 > 0），
  否则断言可能是恒真。
- **一条 host 判据**：新增的裁决函数只是 `validate_endpoint_url` 的**薄包装**（返回 `str | None`
  以便同时用于「探测前短路」与「findings」两处），**不得**出现第二份 `ipaddress` / 主机名集合。

## 验收条件

- **AC-01**：`RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS` 未设（默认 deny）+ 目录内 `localhost`
  endpoint ⇒ run 在 preflight 被拒，finding code = `ENDPOINT_URL_DENIED`，消息**点名**
  endpoint id、base_url 与修法（该环境变量）；且注入的记录型 transport **`calls == 0`**。
- **AC-02**：同一目录 + `allow_localhost_endpoints=True` ⇒ 同一路径下**无** `ENDPOINT_URL_DENIED`，
  且记录型 transport **`calls > 0`**（反证不空转）。
- **AC-03**：门链四项各自的点名事实可判——`ENDPOINT_URL_DENIED` / `CREDENTIAL_MISSING`
  （点名 credential_ref）/ `ENDPOINT_UNHEALTHY`（点名 health 取值）/ `MODEL_ELIGIBILITY`
  （点名 missing capabilities）；缺 endpoint / 缺 model 亦点名。
- **AC-04**：URL 被拒时 `build_endpoint_health` 对该 endpoint 返回 `UNKNOWN` **且不触网**；
  该 endpoint 上不产出 `ENDPOINT_UNHEALTHY`（链短路，无派生噪声）。
- **AC-05**：`RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS` 语义仍**单一来源**：默认 `"0"` ⇒ deny；
  `"1"/"true"/"yes"/"on"` ⇒ allow；由 `ApiSettings.from_env()` 读、`assembly.py` 构造策略。
- **AC-06**：结构判据——全仓非测试代码里 `ipaddress` 只出现在
  `packages/application/model_relay/endpoint_policy.py`；`services/` 下不出现第二份主机名集合
  / 私有网段判断。
- **AC-07**：默认路径**回归对照**：公共域名 endpoint（`examples/config/llm_endpoints.yaml`
  的 `https://apihub.agnes-ai.com/v1` 与既有 `localtest.me` 夹具）行为逐项不变——无新 finding、
  探针仍发生。
- **AC-08**：现有套件全绿（`tests/api`、`tests/application`、`tests/contracts`、
  `tests/architecture/python`）、尺寸门（450 行/文件、50 行/函数）、`ruff`、`mypy`、m0 23 项绿。

## 实施清单

- [x] **WP-A 门链的 URL 层**
  - `endpoint_policy.py::endpoint_url_refusal`（薄包装，不新造判据）。
  - `PreflightFindingCode.ENDPOINT_URL_DENIED`（+ docstring 一行）。
  - `PreflightContext.endpoint_url_denials: Mapping[str, str]`（中性键值，注释写明
    与 `provider_health` 同口径、以及为何不塞策略对象——import 环）。
- [x] **WP-B 门链接进 preflight**
  - `_check_endpoint` 在 health 之前插入 URL 环，被拒即**短路**，只报 `ENDPOINT_URL_DENIED`。
- [x] **WP-C 受控出网：探针前短路 + 注入面**
  - `build_endpoint_url_denials`；`_probe_endpoint` 在解析凭据**之前**做 URL 裁决。
  - `run_execution.py::_live_preflight`（新，兼解 50 行函数门禁）/ `team_support.py` 注入。
- [x] **WP-D 反证与点名测试**
  - `tests/api/test_runtime_egress_gate.py`（9 条）：记录型传输替身 + 端口计数器、
    策略放行的反面、四环点名、短路对照、环境变量语义、结构判据。
- [x] **WP-E 文档与记录**
  - `docs/architecture/AGENT_RUNTIME.md` §3.2（门链表 + 短路语义 + 不宣称的部分）。

## 证据

| 判据 | 命令 / 位置 | 结果 |
| --- | --- | --- |
| 门链用例 | `pytest tests/api/test_runtime_egress_gate.py -q` | **9 passed** |
| 反证 F1（删探针短路） | 改红再复原 | 2 failed（传输层零出站 + 端到端零探测同时红） |
| 反证 F2（删 URL 环） | 改红再复原 | 2 failed，失败形态降级为不点名的 `ENDPOINT_UNHEALTHY` |
| 反证 F3（删注入） | 改红再复原 | 1 failed |
| 尺寸门（450/50） | `pytest tests/tooling/test_python_source_limits.py -q` | **945 passed**（含新文件） |
| 受影响套件 | `pytest tests/api tests/application tests/contracts tests/architecture/python -q` | **1519 passed / 70 skipped / 3 failed**（3 条为 `@pytest.mark.postgres` 环境依赖，靶向运行未加载 `tests/postgres/conftest.py`；m0 全量下通过） |
| `ruff check` / `format --check` | `uv run ruff …` | 绿 |
| `mypy` | `uv run mypy` | **935 source files, no issues** |
| m0（23 项） | `.cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going` | **PASS: profile=m0; 23 deterministic checks**（4003 passed / 10 skipped，582.31s）。首跑 `framework/validate` 红是**本 PLAN 自身**缺 `## 影响报告`，补齐后全量复跑绿 |

## 影响报告

- **改动**：门链第一环（URL 策略）新增；`_probe_endpoint` 由「无条件探测」变为
  「策略裁决先于触网」；`CREDENTIAL_MISSING` 消息补上 `credential_ref`（真实缺陷修复）；
  `run_execution.py` 抽出 `_live_preflight`（兼解 50 行函数门禁）。
- **lint/typecheck/test**：见上表（全部实跑）。
- **Domain/API/schema 变化**：`PreflightFindingCode` 新增成员 `ENDPOINT_URL_DENIED`
  （StrEnum；findings 不进 DTO，因此 **OpenAPI 快照 / `types.ts` / e2e 夹具零变化**）。
  `PreflightContext` 新增字段（加性，带默认值，关键字构造不受影响）。
- **安全/凭据变化**：默认 deny **未放松**；门链是一条**新增的收紧**——目录里写
  `localhost` / 私有 IP 的 endpoint 现在会在触网前被拒（放行方式只有
  `RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS=1`）。凭据仍只从解析器读取，不写日志/事件。
- **兼容性/迁移风险**：无迁移。行为变化仅对「目录里有非公网 endpoint」的部署可见，
  且是 fail-closed 方向；`localtest.me` 类夹具不受影响（判 `domain` ⇒ 放行）。
- **上游版本影响**：无新增依赖、无 pin 变更。
- **下一项任务**：cycle 3 = EC-03（离线全链进默认门：mock 端点 → 会话创建/事件映射 →
  预算归账 → 制品/证据落 canonical；含 `requires_live_llm` 门控的真端点 E2E）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-19 | IN_PROGRESS | cycle 2 建档（EC-02） |
| 2026-09-19 | DONE | WP-A…WP-E 完成；反证三条改红复原；9 条判据绿；尺寸/ruff/mypy/m0 绿；RECHECK-20260919-108 = PASS_WITH_WARNINGS（W-1…W-6） |
