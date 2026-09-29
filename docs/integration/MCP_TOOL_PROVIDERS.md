# MCP Tool Provider Integration v0.4.0

## 1. 位置

```text
Research Tool Service
→ MCP Provider Adapter
→ OpenHands MCP integration
→ Agent
```

Research OS 保存自己的 ToolSpec/Capability/Policy。

## 2. Transport

```text
stdio              # local trusted process
Streamable HTTP    # remote
```

旧 SSE 仅兼容，不作为新部署默认。

## 3. Authorization

Remote MCP：

- 独立 OAuth/credential；
- resource/audience scope；
- 禁止 token passthrough；
- server state handle 不视为 authorization；
- credentials 不进入模型上下文。

## 4. Roots

MCP Roots/工作目录提示只用于上下文，不是访问控制。

真正边界由 Workspace/Sandbox/Policy 执行。

## 5. Registration

```text
server identity
protocol/capabilities
transport
schema hash
Tool list
risk/effect class
auth mode
health
```

## 6. Health

- initialize/capability probe；
- tool schema diff；
- timeout/error rate；
- circuit breaker；
- canary after update。

### 6.1 端点绑定（`endpoint_env`）

provider 可以用 `endpoint_env` 声明**它的端点来自哪个环境变量**：

```yaml
some_rest_provider:
  kind: REST
  transport: rest
  endpoint_env: SOME_REST_ENDPOINT   # 变量名；其值是端点 URL
```

- **env-only**：只读进程环境（`os.environ`），不读文件、不落盘；
- **凭据不走这里**：凭据仍只经 `CredentialResolver`（`credential_ref`），
  把 `NCBI_API_KEY` 这类**凭据名**写进 `endpoint_env` 是配置错误；
- **未设置即不可用**：声明了 `endpoint_env` 而变量未设置 ⇒ 健康探测**不探测**、
  如实 UNKNOWN 并点名变量（不伪装健康）；
- **读面只有指纹**：注册表读面暴露状态（`NOT_DECLARED` / `ENV_UNSET` / `BOUND`）、
  变量名与端点 `sha256` 指纹，**没有端点明文**（端点可能含内网主机名或带 token 的查询串）。

### 6.2 凭据绑定（`credential_ref`）

provider 可以用 `credential_ref` 声明**没有它这个 provider 不可用**的那个凭据引用：

```yaml
docs_mcp:
  kind: MCP
  transport: streamable_http
  credential_ref: DOCS_MCP_TOKEN   # 引用名；值由 CredentialResolver 提供
```

- **声明即必需**：写了就表示"凭据不在 ⇒ 这个 provider 不可用"，因此**可选**凭据不要声明
  ——NCBI E-utilities 无 key 也能用（只是限速更严），它的 `credential_ref` 是适配器
  构造参数，不出现在 spec 里；
- **只查存在性，不碰明文**：判定走 `CredentialResolver.has`，**不调用 `resolve`**、
  不物化 `SecretValue`、不落盘、不进日志/异常/repr；
- **不在即不可用**：声明了 `credential_ref` 而凭据当前解析不到 ⇒ 健康探测**不探测**、
  如实 UNKNOWN 并点名引用（不伪装健康）。这条门槛对**所有 kind 含 NATIVE** 成立
  ——凭据是凭据事实，与传输形态无关（`endpoint_env` 门槛则跳过 NATIVE，因为
  NATIVE 没有外部端点）；
- **读面只有三样**：状态（`NOT_DECLARED` / `ABSENT` / `PRESENT` / `UNCHECKED`）、
  引用名、是否在场，**没有值**；凭据从不在于在（`register()`/`unregister()` 或环境
  变化）时读面立刻反映。

### 6.3 出站 URL 策略在触网之前（REST provider）

**实测边界**（GOAL-20260929-027 EC-01 建档勘察）：`network_domains` 此前**没有运行时
出口执法** —— `endpoint_url_refusal` 只被 LLM 端点与探针调用，没有任何调用方校验某个
tool provider 的出站 host 是否落在它自己声明的 `network_domains` 内。第一个真实 REST
文献源（Europe PMC，`adapters/research_tools/europe_pmc.py`）因此**自己**在发请求前判三件事：

1. **仅 http/https** —— 其它 scheme 一律拒；
2. **保留类地址** —— 复用 `packages/application/model_relay/endpoint_policy.py` 的
   `endpoint_url_refusal` 作**唯一**判据（拒绝 localhost / 环回 / 私有 / 链路本地 /
   保留地址 / CGNAT），**不新造第二个 host 谓词**；
3. **声明式白名单** —— host 必须落在 `ToolProviderSpec.network_domains` 内
   （即 provider 的登记声明本身，不是另一个副本；声明为空 ⇒ 一律拒，fail closed）。

任一条不过 ⇒ **抛错且零请求**（判据断言 transport 请求计数 == 0，而不是「请求后被拒」）。
同一 `network_domains` 也是 pin 契约（`examples/contracts/toolpack_europe_pmc.yaml`）与
登记条目（`examples/config/tool_providers.yaml`）的**同集合**声明，两份漂移会被判据抓住。

这条策略是**适配器自带的**，不是运行时的全局出口网关：默认门依旧离线，
`tests/egress_guard.py` 未放宽，真实出网只在显式开关下按既有 `requires_live_llm` 口径放行。

### 6.4 新增文献源的最低装配清单（以 Europe PMC 为例）

登记一个**复用既有能力名**（`literature.search` / `literature.read`）的 provider，
需要同时落四件事——漏掉第 4 条会让**既有** run 链判红：

1. **适配器**：`adapters/research_tools/europe_pmc*.py`，形态与 `ncbi.py` 同族
   （同步 `ToolProvider` Port、`httpx`、transient/permanent 分类、大结果 spill、
   内容寻址 digest、参数经 `tool-args:{task_id}:{operation_key}` 且校验 `argument_digest`）；
2. **pin 契约**：`examples/contracts/toolpack_<provider>.yaml`（`digest` /
   `resolved_revision` / `license` / `network_domains` / `tools` / `requested_capabilities`
   / `credentials` / `compatibility`）。注意 `digest` 是**声明值**：全仓无人重算它
   （`services/api/catalog.py::_load_tool_pack_digests` 只读、preflight 只做形状校验；
   内容重算只发生在 install 生命周期），**不要**用「内容寻址」描述它；
3. **登记**：`examples/config/tool_providers.yaml` 加条目（`kind` / `trust_level` /
   `transport` / `protocol_version` / `capabilities` / `effect_class` / `network_domains`
   / `health_check`）；**不要**声明可选凭据（「声明即必需」）；
4. **夹具 pin 源同轮扩表**：`tests/api/run_fixtures.py` 的 `_PROVIDERS` 是**整表替换**的
   pin 源。编译期按 capability 反查 provider（`protocol_compile/requirements.py`）⇒
   新 provider 会同时进入**所有**声明了该能力的协议的 `provider_ids` ⇒ preflight 的
   `_provider_trust_findings` 为每个非 `NATIVE` provider 查 `plan.tool_pack_digests`；
   表里没有它 ⇒ `SUPPLY_CHAIN_UNPINNED`（ERROR）⇒ 预检 FAIL ⇒ `freeze_manifest` 拒冻。
   实测影响面：`ai_ml_research_v0_4_0` / `human_gate_demo_v1` / `m12_reference_research_v1`
   / `real_experiment_research_v1` / `real_retrieval_research_v1` 五份协议的 `provider_ids`
   从 `('ncbi_eutils',)` 变成 `('europe_pmc','ncbi_eutils')`。该覆盖由
   `tests/contracts/test_europe_pmc_pin_and_registration.py` 的**下界断言**钉住。

**复用既有能力名 ⇒ 三处零改动**：`examples/config/capabilities.yaml` 词表、
`packages/application/preflight/policy_check.py` 的 `_CAPABILITY_SCOPE` 镜像表、
`examples/config/policy.yaml` —— 三者的并集由既有判据锁死
（`tests/application/test_m2_audit.py::test_policy_scope_mapping_matches_policy_yaml`），
新文献源不得为新名字改它们。

