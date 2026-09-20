# LLM Endpoint Integration v0.4.0

## 1. MVP 用户输入

```text
Base URL
API Key
Model ID(s)
```

协议取值为（域枚举 `LLMProtocol`，唯一词表）：

```text
OPENAI_COMPATIBLE | ANTHROPIC
```

Research OS 不要求用户选择真实厂商；协议标识指**线协议族**，不是模型厂商绑定。
默认 `OPENAI_COMPATIBLE`（API DTO 默认值）。

**执行侧按协议选路**（`adapters/relay/protocols.py` 是唯一分派点）：

| protocol | 线上形态 | 鉴权头 | 备注 |
| --- | --- | --- | --- |
| `OPENAI_COMPATIBLE` | `POST {base_url}/chat/completions`，或按 `api_style=responses` 走 `POST {base_url}/responses` | `Authorization: Bearer` | 既有行为，未变 |
| `ANTHROPIC` | `POST {base_url}/messages`（Messages 形态） | `x-api-key` + `anthropic-version`（**不**发 `Authorization`） | 见下方缺口 |

**未知协议 fail-closed**：`select_wire_shape` 抛分类错误（`MODEL_INCOMPATIBLE`）且
**不发起任何出站请求**——静默回退会让「配了某种协议」与「实际跑的是另一种形态」不可区分。

**Messages 形态的已知缺口（如实登记，不伪造能力）**：

- **流式未实现**：`stream=True` 点名拒绝（不降级成非流式、不套用 OpenAI SSE 解析）；
  probe 的 `streaming` 步因此记为 capability failure，**不写 SUPPORTED 断言**；
- **`response_format` 无对应参数**：非空即点名拒绝（静默丢弃等于声称支持了没支持的能力）；
- **`max_tokens` 必填**：该形态要求该字段，缺失即点名拒绝；probe 层对它显式给出
  `PROBE_ANTHROPIC_MAX_TOKENS`（256），**产品流量必须自带自己的值**；
- **无 `system_fingerprint` 等价字段**：该槽位保持 `None`（不拿别的字段顶替）；
- **usage** 用 `input_tokens` / `output_tokens`；`total_tokens` 仅在两者都存在时给出。

OpenHands 侧的 runtime model identifier 同样按协议取前缀（`adapters/openhands/llm_factory.py`）：
`ANTHROPIC` ⇒ `anthropic/`，`OPENAI_COMPATIBLE` ⇒ 既有探测失败后 `openai/` 前缀。

## 2. LLMEndpoint

```yaml
id: main_relay
name: Main Relay
protocol: OPENAI_COMPATIBLE   # OPENAI_COMPATIBLE | ANTHROPIC
api_style: chat_completions   # 仅对 OPENAI_COMPATIBLE 生效：chat_completions | responses
base_url: https://xxx.com/api/v1
credential_ref: cred_main
request_timeout_seconds: 120
max_retries: 2
concurrency_limit: 8
enabled: true
# 可选块（契约 schema 支持；API PATCH 目前不回传，见 API 文档）
discovery: { enabled: false }
circuit_breaker: { failure_threshold: 5, open_timeout_seconds: 60, half_open_max_probes: 1 }
```

## 3. URL 处理

- 保存用户原始 URL；
- runtime 层做 syntax/TLS validation；
- 不偷偷拼 `/v1`；
- Test Connection 以真实行为为准；
- **默认拒绝** localhost / 环回（`127.0.0.0/8`、`::1`）/ 私有 / 链路本地 / **保留类**
  （多播、未指定、保留段、CGNAT `100.64.0.0/10`、非全局单播），除非部署策略允许；
- 每一类有**自己的**开关：`allow_localhost` / `allow_private` / `allow_link_local`；
  保留类**没有**开关，只能靠 `allowed_hosts` 点名豁免（唯一判据
  `packages/application/model_relay/endpoint_policy.py::_host_kind`）；
- host 是域名时不做 DNS 解析（判定在 adapter 层），因此「放行域名」不等于「可达」。

## 4. ModelDefinition

```yaml
id: model_alpha
endpoint_id: main_relay
model_name: alpha-2026
display_name: Research Alpha
```

`model_name` 原样传给中转站。

## 5. Discovery

```text
Manual                # 永远可用
Optional /models      # 兼容时使用
```

Discovery 结果不能自动启用，需用户确认。

Endpoint 可选配置（`llm-endpoint.schema.json`）：

```yaml
discovery:
  enabled: true
  allow_models: [model-alpha]   # 允许加入候选的模型白名单
```

## 6. Probe

```text
connectivity
authentication
basic chat
streaming
tool calling
structured output
vision（可选）
usage metadata
```

Probe 使用无敏感信息的固定 fixture。

## 7. Health

EndpointHealth：

```text
UNKNOWN
HEALTHY
DEGRADED
OPEN_CIRCUIT
DISABLED
```

记录 latency/error rate/rate-limit/circuit 状态。

Circuit breaker 配置（`llm-endpoint.schema.json`，迁移表见 `docs/reliability/CIRCUIT_BREAKER.md`）：

```yaml
circuit_breaker:
  failure_threshold: 5
  open_timeout_seconds: 60
  half_open_max_probes: 1
```

## 8. Drift Fingerprint

中转站可能在相同 Model ID 后改变底层模型。

运行时尽可能记录：

- returned model field；
- system fingerprint；
- selected safe headers；
- probe suite hash；
- calibration result digest；
- observed capabilities。

**对比结论必须进读面**（每次 probe 都算一次，三态语义见 `docs/integration/MODEL_PROBE.md`
§「漂移判定」）：

- **一致**：登记声明值与返回标识精确相符；
- **漂移**：不符，且**点名两个原值**——只差大小写也算漂移（不折叠，见该节的严格口径）；
- **未知**：未探到（没探测 / provider 没回标识 / 探测失败）。**未知不等于无漂移**，
  读面文案必须自带这句反义。

漂移是**可见性**不是熔断：不自动禁用模型、不改 eligibility。

不能获取真实底模时，不宣称“模型完全可复现”。

## 9. Credentials

**凭据值现在存在哪里**（如实声明；历史声明与本节的差异见
`.cursor/plans/rechecks/RECHECK-20260920-116-*.md`）：

| 层 | 事实 | 落点 |
| --- | --- | --- |
| Domain | 只保存 `credential_ref`（形如 `endpoint:<id>`），**永不保存密钥值** | `LLMEndpoint.credential_ref` |
| 进程内注册表 | `POST /llm-endpoints` 的 `api_key` 进 `register()`，只活在**内存**里 | `adapters/relay/registry_credential_resolver.py` |
| 环境变量 | `resolve()` 先查注册表，未命中再按 `credential_ref` **同名**环境变量回退 | 同上 |

由此得到三条必须写进读面的边界：

- 凭据值**只存在于环境变量或进程内注册表**；注册表随进程消失，**重启后需重新注入**
  （UI 显示 `credential=missing`，由向导重新输入）。**不伪装 Secret Manager**：
  没有加密存储层，也**不落盘**、不进数据库/配置面 JSON、不进 CI；
- 读面只回答存在性：`GET /llm-endpoints*` 回 `credential: configured | missing`，
  任何响应/日志/错误消息都不回显密钥（映射集中在 `services/api/mappers/endpoints.py`）；
- 明文凭据不进仓库/记录/日志：判据是 `tools/credential_audit.py`（四面扫描；
  放行项按**值**白名单逐条给理由，新串仍判红）+ `tests/tooling/test_credential_audit.py`。

其余既有约定不变：

- 不进入 Agent context；
- 不进入 Tool Provider；
- 不进入 telemetry/log；
- Test Connection 错误必须 redacted。

## 10. 多 Endpoint

产品默认一个 Endpoint，但 Domain 支持多个，便于：

- 备用 relay；
- confidential self-hosted relay；
- organization/project override。

不要在 MVP 引入复杂智能路由。

## 11. 首次真实 run（live-gated）

真实端点上的第一次 run 是**门控**动作，不是默认路径（AGENTS.md §11：Fake 仍是默认 runtime）。

**开门条件**（`packages/application/model_relay/live_run_gate.py`，两条都要满足）：

1. runtime **显式配置**：`RESEARCHOS_AGENT_RUNTIME=openhands`（默认空串 = 保持 Fake；
   配别的值也关门——Fake 跑出来的不是真实 run）；
2. 登记端点的凭据**可解析**：用 `CredentialResolver.has()`——只问「能不能」，
   **不物化明文**（`resolve` 才要值）。

**怎么跑**（凭据由操作者注入，只经环境变量或 Credential boundary）：

```bash
RESEARCHOS_AGENT_RUNTIME=openhands LLM_MAIN_KEY=… \
  pytest tests/e2e/test_ec04_live_first_run.py
```

**跑成什么样才算数**：run 到**终态**、运行时**指纹**可判（endpoint 配置摘要 / 返回的模型标识 /
白名单响应头 / probe 套件版本）、usage **真归账**（`BudgetLedger` 的 `MODEL_TOKENS` 正向）、
制品与证据落 canonical 且**可读**。

**结论口径**（AGENTS.md §4）：只能停在「**可重复配置**」——端点、模型与配置被真实运行
确认，但底层模型是否完全一致**不可证明**（provider 不给证据时尤其如此）。本仓不宣称
「模型完全可复现」；这句话本身也由判据把守
（`tests/architecture/python/test_reproducibility_wording.py`：口径面必须出现「可重复配置」，
**肯定式**的越级宣称判红）。

**门关着时**（无凭据 / runtime 未配置）：**不发起任何真实调用**，产出结构化的
`NOT_VERIFIED` 记录（`live_run_record.py`）并点名缺哪一个 `credential_ref`。
**skip 不是 PASS**：它是「没有证据」，不是「证据支持」。

**落地实现**：`apps/web` 的模型详情页对 probe 指纹显示
`Configuration reproducible / provider fingerprint unavailable`（无指纹时），
即同一口径的读面落实。

**已知边界**（如实登记）：目录里所有模型当前都绑定 `main`（OPENAI_COMPATIBLE 面），
登记进目录的 **ANTHROPIC 端点**（`agnes-anthropic`）由 live 用例的 probe 段单独驱动
——让**一次 run 自身**消费 anthropic 面需要改模型→端点绑定。**这条边界的口径、改绑步骤、
实测影响面与判据草案见 §12**（由 `tests/architecture/python/test_anthropic_surface_boundary.py`
把守：口径一变就红）。

---

## 12. run 腿与 probe 腿：现在走哪一面

一次 live 判据（`tests/e2e/test_ec04_live_first_run.py`）里有**两条腿**，它们走的**不是**同一条面。
这一节把口径写成**可判事实**，判据见 `tests/architecture/python/test_anthropic_surface_boundary.py`。

### 12.1 现在走哪一面

| 腿 | 谁在跑 | 端点 | 协议 |
| --- | --- | --- | --- |
| **run 腿** | `POST /projects/{id}/runs` 起的那次真实 run | `main` | `OPENAI_COMPATIBLE` |
| **probe 腿** | 判据里的 probe 段（取运行时指纹） | `agnes-anthropic` | `ANTHROPIC` |

**run 腿为什么是 `main`**：解析链是
协议 phase 的 `required_roles` → `examples/config/agents.yaml` 的 agent → 该 agent 的
`AgentBinding.value` → `examples/config/models.yaml` 的模型 → 该模型的 `endpoint_id` → 端点协议。
示例协议 `console_demo_research_v1.yaml` 只要 `domain_researcher` 与 `scientific_reviewer`
两个角色，它们解析到 `domain_a` 与 `reviewer_a`，绑的是 `research_alpha` 与 `reviewer_gamma`
——两者都在 `main` 上。**注意 `agnes_flash` 不在 run 腿里**：它只被 probe 腿用到，
所以「把 `agnes_flash` 改绑到 anthropic」**不会**让 run 走 anthropic。

**边界本来就可读**（读面已经暴露，不需要新增字段）：

- 每个模型走哪个端点：`ModelReadDto.endpoint_id`（`services/api/dto/models.py`）；
- 每个端点是什么协议：`LlmEndpointReadDto.protocol`（`services/api/dto/endpoints.py`）。

### 12.2 改绑步骤

目标：让 **run 腿**走 `ANTHROPIC`。按解析链改，改的是 **run 腿真的会读到的那些模型**：

1. 在 `examples/config/models.yaml` 里，把 run 腿解析到的模型（当前是 `research_alpha` 与
   `reviewer_gamma`）的 `endpoint` 从 `main` 改成 `agnes-anthropic`；
2. 在 `examples/config/llm_endpoints.yaml` 确认 `agnes-anthropic` 的 `enabled: true`
   且 `credential_ref` 可解析（`LLM_MAIN_KEY`）；
3. **同步更新判据与断言**（这是有意设计成必撞门的，见 §12.3）：
   `tests/architecture/python/test_anthropic_surface_boundary.py` 与
   `tests/loaders/test_contract_loaders.py`；
4. 关闭前先离线核对：`make validate-all` 应绿（跑之前确认环境与 CI 同形，
   见 `.cursor/plans/rechecks/RECHECK-20260920-121-first-live-sampling-run.md` 的 W-7）；
5. 需要实证时按 §11 开一次 live run（**显式** `RESEARCHOS_AGENT_RUNTIME=openhands`，
   次数取最小必要），并核对 run 的端点协议确为 `ANTHROPIC`。

### 12.3 影响面（实测）

下面每一条都是**在仓库里核对过的**耦合点，不是「可能会有影响」：

- **`tests/loaders/test_contract_loaders.py`**——`test_load_models_from_fixture` 断言
  `models["research_alpha"].endpoint_id == "main"`。改绑必须同步改这条断言，
  否则它会把**有意的**配置变更报成失败。
- **`tests/e2e/test_ec03_real_runtime_offline_chain.py`**——它的 `_MockRelayHandler` 自称
  「最小 **OpenAI-compatible** 端点」（只提供 `GET /models` 与 `POST /v1/chat/completions`），
  而 `tests/e2e/live_run_support.py` 的 `point_catalog_at` **只换 `base_url`、保留 `protocol`**。
  ⇒ 改绑到 `ANTHROPIC` 会让这条既有门禁把 **Messages 形态**请求打到 OpenAI 形态的 mock 上。
  **这是改绑最重的一处影响**：修它需要让 mock 讲 Messages 形态、或让该用例显式指定端点，
  两件都落在「测试与门禁」的射程内。
- **读面 DTO**——`services/api/dto/endpoints.py` 的 `LlmEndpointReadDto.protocol` 是断言的
  来源字段；若哪天它被改名或移除，§12.1 的「边界可读」就不再成立（本判据会红）。
- **前端读面**——`ModelCatalogTable` / `ModelDetails` / `ModelInspector` 都渲染
  `endpoint_id`（`apps/web/src/features/models/`）⇒ 改绑会改**读面文案**，可能牵动设计基线。
- **该路径从未真跑**——`ANTHROPIC` 的**执行**路径（`adapters/openhands/llm_factory.py` 加
  `anthropic/` 前缀 → OpenHands SDK → litellm）在 live 上**从未被 run 消费过**。
  已实测的是 `OpenAIChatGateway` 的 **probe** 段（走 ANTHROPIC 形态成功），**不是** run 的 LLM 路径。
- **本判据自身**——`tests/architecture/python/test_anthropic_surface_boundary.py` 会把
  run 腿走在非 OpenAI 兼容面报成红。**这是有意的**：改绑是架构决策，应该撞门。

### 12.4 改绑后的判据草案

改绑**之后**，「一次 run 消费哪一面」要用下面两条**一起**判（缺一条都只是半句话）：

- **(A) 配置面**：run 腿解析链上的模型，其端点的 `protocol == "ANTHROPIC"`
  （把 §12.1 的解析链反过来断言）；
- **(B) 运行面**：一次 live run 的记录里，run 所用端点的协议为 `ANTHROPIC`，
  **且** run 到终态（`FAILED` 也算终态，见 §11 与
  `docs/integration/LIVE_MODEL_RUNBOOK.md` §6 的判据）、**且** usage 真归账。

只满足 (A) 是「配置改了但没跑过」；只满足 (B) 而 (A) 不成立说明解析链没被真的改到
（例如只改了 `agnes_flash`——它**不在** run 腿上）。
