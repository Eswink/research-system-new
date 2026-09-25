# Threat Model v0.4.0

## 1. 保护资产

- LLM/Tool/Compute credentials；
- 用户代码、数据和未公开研究；
- Workspace/Artifact；
- Domain canonical state；
- Evidence/Claim integrity；
- 预算和计算资源；
- 审计轨迹。

## 2. 主要信任边界

```text
Browser/User
Control Plane
Agent Runtime
LLM Relay
MCP/Tool Providers
Sandbox/Compute
Artifact Store
External Web/PDF/Data
```

## 3. 威胁与控制

### Prompt Injection

来源：Web/PDF/MCP Tool output。

控制：trust label、上下文隔离、不可修改系统策略、敏感 Tool 二次检查。

### Tool Poisoning / Schema Change

控制：ToolPack digest、版本 pin、schema diff、安装审批、canary。

### Confused Deputy / Token Passthrough

控制：CredentialBinding、audience/scope、禁止把 LLM key 给 Tool、禁止通用 bearer token 透传。

### Rogue / Stolen Worker（M16）

来源：被入侵的 worker 主机、被盗 session token、伪造注册。

控制（ADR-0027）：enrollment secret 常量时间比较 + session token 仅存
sha256（generation 单调，重注册作废旧 token）；worker_id 与 token 身份一致性
校验；`fence` 单调拒绝迟到结果；worker 不持有 PostgreSQL/ArtifactStore
凭据；非 loopback 绑定无 TLS 拒绝启动；作业级最小凭据 scope；秘密枚举面为零。

### Partition / Split-brain（M16）

来源：网络分区、重复投递、scheduler 重启。

控制：分区仅为 claim 过滤（所有权权威是 leases 行，结构上无双重所有权）；
服务端时间判定 LOST；`recover_expired_leases` 单一恢复权威；迟到结果被
fence 拒绝；重连不恢复旧权威。

### SSRF / Data Exfiltration

控制：egress proxy、domain allowlist、DNS/IP 检查、下载大小上限、private-network deny。

### Workspace Escape

控制：sandbox、readonly mount、无 Docker socket、无 privileged、path guard、resource limit。

### Supply Chain

控制：pin commit/digest、license/manifest、dependency scan、quarantine、可撤销安装。

### Resource Exhaustion

控制：budget/quota、timeout、max turns、process/memory/GPU limits、circuit breaker。

### Model Relay Drift / Malicious Relay

控制：TLS、endpoint health、runtime fingerprint、敏感项目提示、数据分类策略、可选 self-hosted relay。

### Evidence Tampering

控制：content digest、append-only provenance、artifact verification、separation of duties。

## 4. Data Classification

```text
PUBLIC
INTERNAL
CONFIDENTIAL
RESTRICTED
```

Project 分类影响：

- 是否允许外部 LLM Relay；
- 是否允许公网 Tool；
- telemetry 内容；
- artifact retention/export。

## 5. Security Invariants

- Agent 永远看不到明文 Secret；
- MCP Roots 不是安全边界；
- Reviewer 不可修改实验结果；
- Writer 不可创建 Verified Claim；
- 高风险 Tool 不能仅依赖模型自觉；
- 所有外部内容默认不可信。

## 6. 授权面威胁建模（BOLA / BFLA）—— 文档级草案

本节是 **D-12「取 (b)」** 的交付物：先出**文档级**威胁模型草案，**不改代码、不改门禁、
不加判据**。它的用途是让「授权面缺什么」从口头印象变成**可引用的实况清单**，并据此
判断下一步 (a)（专项威胁建模 + 授权面判据）的范围与代价。

**本节不是安全结论**：它只描述**今天树上的事实**与**明确的空白**，不对系统作安全背书。

### 6.1 术语

- **BOLA**（Broken Object Level Authorization，越权访问对象）：调用方拿到**别人的**
  对象（run / artifact / memory / endpoint…）。典型成因是「按 ID 取对象但不校验归属」。
- **BFLA**（Broken Function Level Authorization，越权访问功能）：调用方调用了**不该它调**
  的功能或动作（跨租户、跨角色的写 / 删 / 审批 / 安装）。

### 6.2 覆盖了什么（本节实际论证到的范围）

本节只覆盖**一个**问题：**「当前树上的授权面，在 BOLA / BFLA 两类问题上的实况是什么」**。
具体论证到的事实（逐条可在树上复核）：

1. **控制面 HTTP 面 = 124 条路由，逐条零授权依赖**。应用由 `services/api/app.py:261`
   的 `create_app()` 组装（`:266` 建 FastAPI、`:276` 只挂 `IdempotencyMiddleware`、
   `:277` 起 `include_router`）；全仓 `Depends(` / `Security(` / `current_user` /
   `HTTPBearer` / `APIKeyHeader` **零命中** ⇒ **没有任何路由声明授权依赖**。
2. **控制面无调用方认证**（不只是「授权粒度粗」）。无 API key / bearer / session /
   cookie / tenant 头。唯一与请求相关的强制项是 `Idempotency-Key`
   （`services/api/middleware.py:40`），那是**幂等**要求，**不是身份**。
   `api_key` 只出现在**出站** LLM 端点的凭据面（`services/api/dto/endpoints.py:3`）。
3. **策略是「能力级」而非「对象级」**。`PolicyRule.matches()` 只比
   capability / action / scope（`packages/domain/policy.py:29`）；
   `PolicyRequest` 虽声明 `actor` / `resource` / `context`
   （`packages/application/ports/policy_evaluator.py:21`），但
   `NativePolicyEvaluator` **不读**这三者，未命中即落 `default_effect`
   （`packages/application/policy/native.py:17`、`:47`）。树上自己就写着
   「actor 不参与规则匹配」（`services/api/routers/policy.py:11`）。
   `examples/config/policy.yaml:2` 是 `default_effect: DENY`，规则只讲能力与 scope，
   **从不讲资源 id**。评估点是 **preflight / 执行点**（`packages/application/preflight/policy_check.py:70`、
   `packages/application/tool_plane/execution.py:43`），**不是 HTTP 边界**。
4. **域实体与 DTO 上不存在「归属」概念**。`ResearchRun` 只有
   `id` / `project_id` / `protocol_id` / `state` / digests / 时间戳
   （`packages/domain/run.py:37`）；`ProjectDefinition` 无 owner，且模块注释明说它
   **不是**租户边界（`packages/domain/projects.py:5`）。全 `services/api/dto/` 里唯一
   身份味的字段是 `Artifact.created_by`（`packages/domain/artifacts.py:90`），它是
   **溯源字符串**（写入方是 `export_bundle`、`experiment_executor`、`tool:<id>` 等内部
   生产者），**没有任何路由按它过滤**。`EventEnvelope.actor` 是**必填**但取值是
   调用点硬编码的字面量（如 `"user:console"`），**不是**认证身份。
5. **路径 id 只用于选对象，不用于判归属**。`GET /runs/{run_id}`
   （`services/api/routers/runs.py:141`）按 id 取任意 run；
   `GET /artifacts/{artifact_id}/content`（`services/api/routers/artifacts.py:165`）
   流式返回任意 artifact。`project_id` 只做**列表过滤**（`services/api/routers/runs.py:117`）。
6. **仓库里唯一有认证的面是 worker 网关，且它不属于本节的空白**。
   enrollment secret 常量时间比较（`services/api/worker_gateway/security.py:31`）+
   `Authorization: Bearer` 会话 token 仅以 sha256 存储
   （`services/api/worker_gateway/auth.py:21`）；非 loopback 绑定无 TLS 拒绝启动
   （`services/api/worker_gateway/auth.py:58`）。
7. **「默认 DENY」成立，但它是能力策略而非 HTTP 拒绝**——两者**不可互相顶替**：
   即使某能力被 DENY，控制面的读路由仍然返回数据（见 6.3 第 1 条）。

### 6.3 未覆盖范围（明确不覆盖什么）

以下**都不在本节的射程内**，本文档**不**对它们作任何判断，也**不**因写了本节而变成已覆盖：

1. **不覆盖「控制面无认证」这一事实的处置**。6.2 第 2 条把它记成事实；**要不要**、**何时**
   补认证与逐路由授权，属 **M18**（见 6.4）与 D-12(a) 的范围，本文档**只登记不决定**。
   注意其直接后果：**任一能连上控制面 TCP 端口的调用方，即可读写全部对象**——
   BOLA 与 BFLA 在**无认证**的前提下不是「某处校验写错了」，而是**整面尚无校验点**。
2. **不覆盖渲染层可达范围**。控制面绑定的实际暴露面由部署决定：开发脚本绑
   `127.0.0.1`（`tools/dev_backend.mjs:249`），容器内 `uvicorn` 监听 `0.0.0.0`
   （`infra/docker/research/Dockerfile.python:38`）而**发布端口**是回环
   （`infra/compose/research-validation.yaml:192`）。⇒ **不得**把本节读成「控制面只可能
   被本机访问」；本节没有验证任何部署拓扑。
3. **不覆盖前端**。`apps/web` 的按钮可见性 / 路由可见性**不是**访问控制；本节未审计前端，
   也不接受「前端藏起来了」作为控制。
4. **不覆盖业务逻辑越权**（同一对象上「能读是否就能撤」这类动作级语义）、
   **不覆盖竞态型越权**（TOCTOU）、**不覆盖**「同一 principal 内的权限提升」。
5. **不覆盖 worker 网关的既有实现**（它在 6.2 第 6 条只作为事实引用）；worker 面的
   threat 覆盖见第 3 节「Rogue / Stolen Worker（M16）」。
6. **不产生任何机器判据，也不改变任何门禁**。本节的 diff **只含文档**；
   没有新增测试、没有新增 allow、没有改阈值。⇒ **本节的结论会随树漂移而过期**，
   它没有「自动发现回归」的能力（这正是 (a) 与 (b) 的区别，见 6.5）。
7. **不覆盖** Prompt Injection / SSRF / 供应链等其余威胁面——它们在第 3 节，
   本节**不**重复论证，也**不**因本节新增而重新论证。
8. **不覆盖** `R-M1`（hook 面安全结论）与 `R-D1`（依赖告警未清部分）；它们是各自
   登记项，本节无权收口。**特别地**：依赖告警（`undici` / `yaml`）与本节的授权面
   是**两个不同**的缺口，**不得**互相顶替。

### 6.4 与 M18 边界的关系

**本节的存在不等于 M18 被启动。** M18 = 「Multi-user / Organization / RBAC」
（定义在 `docs/roadmap/MILESTONES.md:971`），状态 **DEFERRED**
——`:973` 写明「当前不实现 Tenant / Organization / cross-tenant data isolation /
multi-user RBAC / tenant quota / tenant billing 的任何能力，**不标记部分完成**」，
正式触发条件是「出现真实第二用户、team、organization、shared service、RBAC 或
tenant isolation 需求」（`docs/roadmap/MILESTONES.md:980`，另见
`docs/adr/ADR-0028-personal-scale-rebaseline.md:44`）。

因此本节的授权面空白应被读成**「按 M18 deferral 有意未做」**，而不是「本可以立刻补好的
疏漏」：

- **树的代码里**已把这条边界写成注释：`packages/domain/projects.py:4`
  （「多用户/RBAC/成员管理属 M18 deferred，本模块不表达授权语义」）、
  `services/api/routers/projects.py:7`、`services/api/routers/memory.py:12`、
  `docs/api/CONTROL_PLANE_API.md:520`（「Identity / Governance（未提供；M18 deferred）」）。
- **已有的预留面**在 `docs/security/IDENTITY_AND_ACCESS.md`：预留实体
  （`Organization` / `User` / `ServicePrincipal` / `AgentPrincipal` /
  `ProjectMembership` / `AccessGrant`）、授权式「身份 + Project 成员 + 能力 + 资源 scope
  ⇒ Policy 决策」、以及「在完成这些之前不宣称支持不可信多租户」的口径。
  **本节不重写该文档**，只把它标为**唯一**的未来落点。
- **启动 M18 之前**，本节的空白是**已知且被接受**的；它必须继续以「单用户、本机 /
  受信网络」为**部署前提**。⇒ 任何把控制面**暴露到不可信网络**的部署，
  都**先**撞上本节 6.3 第 1 条，**而不是**先撞上 M18。
- 与 **M16**（分布式执行）的边界不要混淆：M16 补的是 **worker 面**的认证与
  fence / lease 语义，并已在 `PLAN-20260831-025-m16-distributed-execution.md:46`
  明写「认证缺口：Control Plane API 完全无认证（M18/M19 债务）」。

### 6.5 若取 (a)：范围与代价

(a) = 专项威胁建模 + 授权面**测试**（把本节的事实变成机器判据）。它的**最小**范围与代价：

- **前置**：必须先有**主体模型**——没有 principal 就没有「越权」可言。这一步
  **不能**靠加测试解决，它落在 M18（或 D-12(a) 明文授权的等价子集）。
- **若只做「防回归」而非「补能力」**（即：先把**今天的空白**钉成判据，防止它在无人
  察觉时变多），范围 = 逐路由授权面清单 + 「控制面无认证」的显式声明判据
  + 新路由必须登记授权状态的机械判据。**代价**：一轮专项 cycle、一套新判据的
  维护面，且**会立刻全红**（今天 124 条路由都没有授权依赖）⇒ 要么先改产品、
  要么把判据写成「白名单式现状快照」（后者只防漂移、不提供安全性，且**本身就是
  一份待还的债**）。
- **若做完整 (a)**（BOLA/BFLA 负面测试套件 + 跨主体隔离取证），前置是 M18 的数据模型
  与 schema 级隔离；**在 M18 之前做完整 (a) 会撞上「没有第二个主体可测」**。
- **判据成本**：无论是哪种，都要求先定「授权失败的**响应语义**」（403 还是 404、
  是否泄露对象存在性）。今天树上**没有**任何控制面 401/403 断言
  （现有 401 断言全在 worker 网关测试里）⇒ 语义先定，测试才有意义。
- **不做 (a) 的代价**（即维持 (b)）：本节结论会**过期**且**无自动发现**；
  授权面缺口靠人工面在每轮 GOAL 里「原样承继」。这正是 D-12 台账里
  「授权面覆盖继续缺一项系统性论证」的含义，也是 `R-M1` 无法据此收口的原因。

### 6.6 引用约束（写作纪律）

- 本节所有事实以**当前树**为准；`file:line` 用于复核，**行号会随后续改动漂移**，
  复核时以**符号名**为准。
- 本节**不得**被引用为「已做威胁建模」「授权面已覆盖」或任何形式的安全结论。
  可引用的口径只有：**「授权面的实况与空白已登记在
  `docs/security/THREAT_MODEL.md` 第 6 节（D-12(b) 草案）」**。
- 外部审计记录沿用同一口径：`docs/audits/MIMOSA_POST_CLOSURE_AUDIT_20260918.md:75`
  已写明 threatModel 阶段仍为 `partial`（0 入口 / 0 主体 / 0 授权面）。
