# Identity & Access v0.4.0

## 1. MVP 与未来

MVP 可以单用户运行，但 Domain/API 不把“当前用户”写死为全局管理员。

预留：

```text
Organization
User
ServicePrincipal
AgentPrincipal
ProjectMembership
AccessGrant
```

## 2. Human Roles

```text
SYSTEM_ADMIN
ORG_ADMIN
PROJECT_OWNER
RESEARCHER
REVIEWER
OBSERVER
```

Reviewer 的人类权限与 ScientificReviewer Agent 的 RoleDefinition 是不同概念。

## 3. Agent Principal

AgentSession 获得临时 Principal：

```text
agent_session_id
run/task scope
capabilities
workspace lease
credential bindings
expiry
```

Agent 不继承发起用户的全部权限。

## 4. Service-to-Service

API、Worker、Tool Gateway、Agent Server 使用独立 service identity 和最小权限。

## 5. Authorization

```text
Human/Service identity
+ Project membership
+ Task/Agent capability
+ Resource scope
→ Policy Decision
```

## 6. Audit

所有变更记录：

```text
actor_type
actor_id
impersonation/delegation chain
resource
action
policy decision
trace
```

## 7. Multi-tenancy

生产多租户需要：

- tenant-scoped queries；
- artifact namespace；
- secret namespace；
- worker/sandbox isolation；
- quota；
- cross-tenant test。

在这些完成前，不宣称支持不可信多租户。

## Worker Identity (M16)

- 入网：预共享 enrollment secret 经 `CredentialResolver`（WORKER 凭据域，
  与 TOOL/MODEL 隔离），`hmac.compare_digest` 常量时间比较。
- 会话：注册成功签发 256-bit session token（仅返回一次；服务端只存
  sha256 + `registration_generation`）；`Authorization: Bearer` 按 hash 查表。
- 反冒充/反重放：请求体 worker_id 必须与 token 身份一致；generation 单调，
  重新注册作废旧 token，旧 session fail closed。
- 传输：默认要求 TLS（`RESEARCHOS_WORKER_GATEWAY_REQUIRE_TLS=1`）；
  绑定非 loopback 且未启用 TLS 拒绝启动。
- Worker 不持有 Control Plane 数据库凭据；Console 只经只读 API 观察集群。

## Control Plane 写面认证（GOAL-019）

本节登记 **2026-09-26（GOAL-20260926-019）落地**的最小认证面。它**只**是「谁在调用」这一层的
最小实现，**不是**授权模型，也**不是**多租户。

**认证覆盖**：写面（POST / PATCH / PUT / DELETE）已认证；读面（GET / HEAD）未认证；多租户与 RBAC 未实现。

- **保护范围 = 只保护写面**：分类**复用**幂等中间件的 `_MUTATING_METHODS`
  （`services/api/middleware.py`，**不新造第二套**）。读面（GET/HEAD）**一律放行**；
  `GET /health` 因是 GET 自动豁免，**没有**路径白名单。
- **凭据**：token 只从环境变量 `RESEARCHOS_CONTROL_PLANE_TOKEN` 读取（可选
  `RESEARCHOS_CONTROL_PLANE_PRINCIPAL_ID` 声明主体标识，缺省 `control-plane`）。
  **不落盘、不进日志 / 事件 / 遥测**；比较用 `hmac.compare_digest`（**常数时间**，
  空值永不匹配）。仓库内**只登记变量名**，任何地方都不出现 token 值。
- **可关**：变量留空 ⇒ **认证关闭**，并在**启动时打印显式警告**（文案明确说
  「无认证，任何能连上本进程的调用方都能写」并声明未覆盖范围）。**CI 与本仓 live 夹具
  不设该变量** ⇒ 默认链路行为不变。
- **主体（`Principal`）**：域值对象 `packages/domain/principal.py`，只含**主体 id + 类型**
  （`user` / `service` / `agent` / `system`），**不含**租户 / 角色 / 权限矩阵字段
  （那属 M18）。认证通过后，请求级主体落 **canonical**（事件 envelope 的 `actor`，
  经 `outbox_events.envelope_json` 持久化）并在读面可见（`GET /runs/{id}/events`）。
  无请求主体时**沿用**调用方既有的常量（如 `system:orchestration` / `user:console`）
  ⇒ 未启用认证时行为与基线**逐字相同**。
- **诚实边界（不得读成更强结论）**：**单一共享 token ⇒ 单一主体**。本面能回答
  「是不是**经过认证的**调用方」，**不能**回答「是**哪一个**调用方」——本实现
  **不接受**调用方自报身份（无逐调用方凭据时那只可被伪造，会比不做更坏）。
  逐调用方身份需要**逐调用方凭据**，属未来工作。

#### 运维面：开启 / 轮换 / 关闭 / 验证 401

**开启**：把 `RESEARCHOS_CONTROL_PLANE_TOKEN` 设为一段**操作者自选的长随机串**
（可选 `RESEARCHOS_CONTROL_PLANE_PRINCIPAL_ID` 声明主体标识，缺省 `control-plane`），
然后**重启 API** 进程。变量只在进程启动时读一次 ⇒ **改值必须重启才生效**。

**轮换**：换掉环境变量值 → **重启**。没有别处要改，也**没有**持久化副本要清理
（本面不伪装 Secret Manager）。

**关闭**：`unset` 该变量 → 重启 ⇒ **认证关闭**，并打印**显式警告**（警告不是安全结论）。

**验证 401 是否正常（四步，可照抄）**——判据是**状态码 + `detail`**，不是「看起来通了」：

| 步骤 | 请求 | 期望 | 不是期望值说明什么 |
| --- | --- | --- | --- |
| ① | `GET /health`，**不带** token | **200** | 读面被拦 ⇒ 与口径不符（**不是**认证问题） |
| ② | `POST /projects`，**不带** token | **401** + 点名缺 `Authorization: Bearer` 头 | 写面未被保护 ⇒ 确认进程读到了变量（须重启） |
| ③ | `POST /projects`，**带错** token | **401** + 点名 token 不匹配 | 同上 |
| ④ | `POST /projects`，**带对** token | **2xx** | 认证已放行、请求被**别的**规则拒（如 422）⇒ 改请求不改认证 |

命令与读法见 `docs/integration/LIVE_MODEL_RUNBOOK.md` §2.2（含可复核实测：关闭态
**200 / 201 / 警告在场**；开启态 **200 / 401 / 401 / 201**，两个 401 各自点名成因）。

**部署面注意事项（前两条是硬要求，后两条是**本机不可验证**的检查项）**：

1. **反代必须透传 `Authorization` 头**（不得剥离 / 覆盖）。反代若自己也用
   `Authorization` 做上游认证，两个信任域会**互相顶替** ⇒ 不要共用同一个头。
2. **TLS 必须在反代终止**：bearer 凭据在明文 HTTP 上等于公开。开发脚本绑 `127.0.0.1`、
   容器发布端口为回环 ⇒ **跨主机暴露前必须上 TLS**。
3. **多副本：每个副本都要同一个变量值**。本实现**没有**共享会话 / 密钥协调面 ⇒
   副本间不一致会表现为**间歇 401**。此条**未在本机验证**（本机单进程）——登记为**未验证**。
4. **反代 / TLS / 多副本下的认证行为未验证**：上面只给**检查项**，**不产生**验证结论；
   要变成已验证需要真实部署拓扑（本机没有）。

### 未覆盖范围（明确不覆盖什么）

1. **读面未认证**：任一能连上控制面端口的调用方仍可**读**全部对象。
2. **多租户 / organization scope / RBAC / 角色与权限矩阵**：**未实现**（M18 `DEFERRED`
   状态不变，**不得**标记部分完成）。
3. **对象级授权（BOLA / BFLA）**：**未做**。主体存在**不等于**授权存在——
   没有「哪个主体能碰哪个对象」的判定点，也没有专项测试面。
4. **逐调用方身份**：见上「诚实边界」。
5. **部署面**：反代 / TLS / 多副本下的认证行为**未验证**（GOAL-020 已给出**检查项**与
   **本机不可验证**的原因，**未**产生验证结论——见上「部署面注意事项」第 3、4 条）。
6. **持久化约束**：主体只以字符串落在事件 envelope，**没有**独立列 / 外键 / 约束
   ⇒ 本面是**代码级**约束，不是数据库级。
7. **`R-M1`**：Mimosa 钩子侧结论仍未取得 ⇒ **不得**因本节新增而宣称项目安全。
