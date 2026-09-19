---
id: RECHECK-20260919-108
plan_id: PLAN-20260919-108
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-19
completed_at: 2026-09-19
reviewer: root-agent-goal-007-cycle2
baseline_ref: f3e388a
checked_head: WORKTREE
---

# RECHECK-20260919-108 — 受控出网门链（GOAL-20260919-007 cycle 2 = EC-02）

## 检查范围

EC-02 的四条可判事实逐条对表（每条都要**实跑**证据）：

| EC-02 要求 | 交付 | 判据（可复核） |
| --- | --- | --- |
| **复用**既有 `EndpointUrlPolicy` / `validate_endpoint_url` 与 `RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS` 语义 | 新增 `endpoint_url_refusal`（同一模块内的薄包装）+ `build_endpoint_url_denials`（服务层只搬裁决结果） | `::test_a_single_host_judgement_exists_in_the_repo`（全仓 `ipaddress` 只出现在 `endpoint_policy.py`）+ `::test_the_env_flag_is_the_single_source_for_the_policy` |
| 缺 endpoint / 缺凭据 / 端点不健康 / 能力不匹配**逐项点名** | `core` 四环：`ENDPOINT_URL_DENIED`（新）/ `CREDENTIAL_MISSING` / `ENDPOINT_UNHEALTHY` / `MODEL_ELIGIBILITY` | `::test_each_remaining_link_names_its_own_fact` + `::test_preflight_names_the_url_denial_and_stops_the_chain` |
| 「一次都不发起出站调用」必须是**可观测的出站计数 == 0** | 记录型 `httpx.BaseTransport` 注入真实 `OpenAIChatGateway`；端口级用 `FakeBase.calls` | `::test_denied_url_makes_zero_outbound_calls`、`::test_missing_credential_stops_before_any_outbound_call`、`::test_run_is_refused_with_zero_probes_when_policy_denies` |
| 默认姿态**不得放松**（未配置 ⇒ deny；url 策略默认 fail-closed） | `PreflightContext.endpoint_url_denials` 缺失时服务层按 `EndpointUrlPolicy()` 默认裁决；`_probe_endpoint` 同 | `::test_the_env_flag_is_the_single_source_for_the_policy`（默认 `False`）+ 上述三条零出站用例 |
| **反证**（拆掉任一环 ⇒ 判据红） | 三处注入各跑一次 | 见「反证与实测」 |

## 检查结果

### 门链的真实形状

```text
URL 策略（endpoint_url_refusal ← validate_endpoint_url）
  → 凭据存在性（CredentialResolver.resolve）
  → 端点健康（gateway.probe_connectivity）
  → 模型能力匹配（decide_eligibility）
```

- **第一环是在触网之前生效的**：`services/api/preflight_support.py::_probe_endpoint` 在
  **解析凭据之前**先做 URL 裁决；被拒 ⇒ 返回 `EndpointHealth.UNKNOWN` 且**不出网**。
  这不是「顺手加一个 if」：`_probe_endpoint` 原本对目录里**每个** endpoint 都发
  `GET /models`，即使用户把 `http://127.0.0.1:8080/v1` 写进目录、即使用户随后会被拒——
  受控出网以前只在两个**手动**操作（`/llm-endpoints/{id}/test`、`/models/{id}/probe`）
  上有门禁，run 路径上没有。
- **短路是刻意的**：URL 被拒时同 endpoint 上**不派生** `ENDPOINT_UNHEALTHY`。探测没有
  发生，`UNKNOWN` 是**派生噪声**；把它一起报出来会让人以为「端点不健康」，而真实阻塞
  事实是「策略没放行」。对照用例同时证明这两个 finding **本来都会报**（去掉裁决注入 +
  清空 health/凭据面 ⇒ 两者同时出现），所以短路不是巧合。
- **`CREDENTIAL_MISSING` 消息顺手补上了 `credential_ref`**：原文只说
  「credential for endpoint main cannot be resolved」——运维能看出哪条链断了，但不知道
  要配**哪一条**凭据。EC-02 要求「点名缺哪条事实」，因此消息改为
  `credential {ref} for endpoint {id} cannot be resolved`（ref 是键名，不是秘密值）。
  这是一处**真实缺陷修复**，不是为了让断言变绿。
- **门链无条件、不按基质分叉**：Fake 与真实执行体走同一条链，因此不可能出现「真实
  runtime 比 demo 更松」的缝隙。副作用是目录里写 `localhost` 默认即被拒——这正是
  `RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS=1` 的用途。既有夹具不受影响：`localtest.me`
  不是 `localhost` 字面量也不是可解析 IP，`_host_kind` 判 `domain` ⇒ 放行。

### 端口形态的选择（为什么不是把策略对象塞进 `PreflightContext`）

`ports` **不能** import `model_relay`：`model_relay/__init__.py` 反向 `from
packages.application.ports import (...)`，而 `packages/application/__init__.py` 又在
`ports` 之前执行——任何 `ports → model_relay` 的导入都会落在**部分初始化**的模块上
（软失败点随导入顺序漂移）。因此 URL 裁决在服务层**求值**，以中性
`Mapping[str, str]`（endpoint_id → 拒绝理由）注入，与同一 dataclass 里既有的
`provider_health` 同口径（注解写明：未注入 key = 注入方未声明该面）。

## 反证与实测

| # | 注入 | 结果 |
| --- | --- | --- |
| F1 | 删掉 `_probe_endpoint` 的 URL 短路 | **红**：`test_denied_url_makes_zero_outbound_calls` + `test_run_is_refused_with_zero_probes_when_policy_denies`（2 failed）⇒「零出站」不是空断言 |
| F2 | 删掉 `_check_endpoint` 的 URL 环 | **红**：`test_preflight_names_the_url_denial_and_stops_the_chain` + 端到端用例（2 failed），且失败形态降级为**不点名**的 `ENDPOINT_UNHEALTHY` ⇒ 点名与短路都靠这一环 |
| F3 | 删掉 `run_execution` 的 `endpoint_url_denials=` 注入 | **红**：`test_run_is_refused_with_zero_probes_when_policy_denies`（1 failed）⇒ 生产路径真的读这条裁决 |

三次注入均已复原，`git status --short` 只剩预期改动。

## Warnings（不阻断，如实登记）

- **W-1**：门链覆盖的是 **LLM endpoint** 这一条出网口。tool provider（MCP/REST/远端
  worker）的出网仍各自为政（`adapters/mcp/transport.py` 等），不在本 EC 射程。
- **W-2**：`endpoint_url_denials` 按「未注入 = 未声明该面」处理（沿用 `provider_health`
  口径）。对**手写** `PreflightContext` 的调用方（单测/fixture）而言这是 fail-open；
  两条生产控制面路径都注入，且探针侧的短路是无条件 fail-closed，因此生产面没有这个口子。
  若将来出现第三条构造 `PreflightContext` 的生产路径，必须同步注入。
- **W-3**：本 EC 没有把「运行时选择的基质」与「门链」耦合：门链对 Fake 与真实 runtime
  一视同仁。这样更严，但也意味着**不能**用「跑的是 demo」来豁免一条写得不好的
  localhost endpoint——用户要放行只能显式设环境变量。
- **W-4**：`_probe_endpoint` 仍会探测目录里**未被任何模型引用**的 endpoint。
  策略拒绝时已不触网，但「全目录探测」这个行为本身没变（不在本 EC 射程）。
- **W-5**：`AgentSessionSpec` 仍不携带 endpoint / model / 凭据，因此 session 期 LLM 装配
  仍是 EC-03 的事；本 EC 只保证「只要出网口被使用，它已经过门链」。
- **W-6**：`ENDPOINT_URL_DENIED` 是新 finding code，不进 OpenAPI / web types（findings
  不是 DTO 字段），因此读面暂只有 `run.failed` 的 codes 串；前端若要展示完整消息需另开。

## 结论

EC-02 **PASS_WITH_WARNINGS**：门链四环齐备且逐项点名；URL 环在**触网之前**生效，
「出站 0」由传输层替身与端口计数器两处独立可观测，并有反向（策略放行 ⇒ 确实出站）
与三处注入反证。默认姿态未放松（`0` = deny）。W-1…W-6 为如实登记的射程边界，不阻断。

## 门禁

| 门 | 结果 |
| --- | --- |
| `tests/api/test_runtime_egress_gate.py` | **9 passed** |
| 尺寸门（450 行 / 50 行函数） | **945 passed** |
| 受影响套件（tests/api + tests/application + tests/contracts + tests/architecture/python） | **1519 passed / 70 skipped / 3 failed** — 3 条为 `@pytest.mark.postgres` 的环境依赖（靶向运行未加载 `tests/postgres/conftest.py`，见 MEM-20260919-080），m0 全量运行下通过 |
| `ruff check` / `ruff format --check` | 绿 |
| `mypy` | **935 source files, no issues** |
| m0（23 项） | **PASS: profile=m0; 23 deterministic checks**（4003 passed / 10 skipped，582.31s）。首跑 `framework/validate` 红（`PLAN-20260919-108` 缺 `## 影响报告` 章节，即本 PLAN 自身不合规），补齐后全量复跑绿——**首跑红如实记录，不当作绿** |
