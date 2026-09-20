---
id: PLAN-20260920-116
slug: supply-chain-registration-and-credential-discipline
title: 供应链登记与凭据纪律：URL 策略补严 / 明文凭据审计 / 真实端点入库与重启失效边界（EC-03）
status: IN_PROGRESS
created_at: 2026-09-20
updated_at: 2026-09-20
parent_goal: GOAL-20260920-008
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260920-008 cycle 3 = EC-03（供应链登记与凭据纪律）。授权来源：2026-09-20 用户 goal 模式指令 frontmatter `authorization.ref` 第 (1)(3) 条——登记一个真实端点（anthropic 兼容型，base_url = https://apihub.agnes-ai.com，模型 agnes-2.5-flash）；凭据只从环境变量或 Credential boundary 读取（由用户注入），**不得**写入仓库/数据库/CI/记录/日志，不得回显，本循环**不索取明文**。本 PLAN 遵守：不新造第二套 host 判据、不改 Policy/eligibility、不引入依赖、默认门保持离线、真实端点调用**最小必要次数**。"
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260920-116 — 供应链登记与凭据纪律（GOAL-008 cycle 3 = EC-03）

## 目标

把「用户授权接入一个真实端点」这件事做成**可判事实**而不是叙述：

1. **URL 策略语义保持且补严**：https 公网放行；localhost / 环回 / 私有 / 链路本地 /
   **保留（含多播、未指定、TEST-NET、CGNAT）**地址一律拒绝；**复用唯一裁决点**
   `validate_endpoint_url`，不新造第二套；
2. **端点与模型登记入库**：配置面（`llm_endpoints` / `models` 两表）里有行、可读回，
   **凭据不出现在任何一行**（只存 ref 名）；
3. **明文凭据审计**：仓库跟踪文件 + `.cursor/plans/**` 记录 + 配置面 DB 文件 + 日志
   **逐面扫描**并给出命中数（0 = 通过），口径写清射程，不用「没扫到」冒充 PASS；
4. **重启失效边界同源**：代码 / 文档 / UI 三面同一口径——凭据只在进程内存或环境变量里，
   **不是** Secret Manager，重启后需重新注入；
5. **无凭据时的诚实行为**：健康探针在无凭据环境**点名失败**（不记 PASS、不伪造指纹、
   **出站 0**），并把这一事实登记进记录。

## 先探明再动手（建档时只读勘察已确认的事实）

1. **URL 策略是唯一 host 裁决点**：`packages/application/model_relay/endpoint_policy.py:40`
   `validate_endpoint_url`（全仓 `ipaddress` 只出现在这一处）；调用面 = probe
   （`packages/application/model_relay/probe.py:128,262`）、运行期
   （`services/api/runtime_support.py:136`）、preflight（`services/api/preflight_support.py:80,89`）。
   **注册面不校验**：`services/api/routers/llm_endpoints.py:94-116` 直接落库。
2. **既有分类有洞（实测）**：`_host_kind` 把 `224.0.0.1`（多播）与 `100.64.0.1`（CGNAT）
   判成 `public` ⇒ `EndpointUrlPolicy()` 默认**放行**；`0.0.0.0` 与 TEST-NET 段恰好落在
   CPython 的 `is_private` 表里 ⇒ 被拒。既有用例
   （`tests/application/test_endpoint_policy.py`，11 条）只覆盖 localhost / private /
   link-local / scheme / allowed_hosts，**没有**多播、CGNAT、IPv6 多播的判据。
3. **凭据两面**：`adapters/relay/credential_resolver.py`（env 名即 `credential_ref`，值密封为
   `SecretValue`）与 `adapters/relay/registry_credential_resolver.py`（内存注册表 + env 回退，
   docstring 已写「服务重启后注册表清空…诚实声明，不伪装 Secret Manager」）；
   `routers/llm_endpoints.py:52-70` 只在 `api_key` 非空时把它送进 boundary，失败回滚端点。
4. **文档口径不诚实**：`docs/integration/LLM_ENDPOINTS.md` §9 写「API Key 加密/Secret Store」——
   实现既**不加密**也**没有** Secret Store（只有进程内注册表 + 环境变量）。§3 只写「默认拒绝
   localhost/private IP」，未提保留地址。
5. **运行期防泄漏测试已存在**：`tests/api/test_security_scan.py`（DTO / SSE / Export /
   localStorage 四面）；**缺**面向「仓库 + 记录 + DB + 日志」的明文凭据审计。
6. **无凭据时的行为**：`probe.py:113-137` `run_endpoint_test` 先过 URL 策略，
   再 `_resolve_credential`；凭据缺失 ⇒ `configuration_failure`（分类 CONFIGURATION，
   消息 redacted），**不发起任何出站请求**。
7. **配置面位置**：默认 DB = `data/research-os-control.db`（`services/api/settings.py:8`），
   `data/` 在 `.gitignore:21`（gitignored，且该规则匹配任意深度）。
8. **真实端点授权**：`base_url = https://apihub.agnes-ai.com`（协议 = `ANTHROPIC`，
   EC-01 已实现该线协议族）、模型 `agnes-2.5-flash`；**凭据由用户注入**，
   本机当前无该端点凭据（cycle 1 的 W-1）。

## 口径（先写死，避免实施时漂移）

- **「保留地址」的判据**：在 `_host_kind` 里用 `ipaddress` 谓词把
  `is_multicast` / `is_reserved` / `is_unspecified` / CGNAT（`100.64.0.0/10`）/
  `not is_global` 归入**拒绝**类；新增类别名（如 `reserved`）并在异常消息里**点名**。
  **唯一裁决点不变**——只改 `endpoint_policy.py` 内部，不新增第二处判据。
- **拒绝必须可观测**：新增用例用**记录型 transport** 证明被拒时 `seen == []`（出站 0），
  与 EC-01 的 fail-closed 判据同构。
- **注册面是否加校验**：本轮**不加**（改成注册即拒会改变既有 API 语义，属行为决策）；
  改为在**读面**（endpoint 详情/健康）继续按既有策略诚实呈现，并在记录里点名
  「注册存疑 URL 仍可入库，但一跑就被拒」这一边界。
- **凭据审计的射程逐面写清**：① `git ls-files` 的全部跟踪文件；② `.cursor/plans/**`
  （记录，已在跟踪集内，单列以示强调）；③ 配置面 DB 文件（二进制，按字节扫）；
  ④ `data/**/*.log` 与 `scratch/*.log`。每面报告「扫描文件数 + 命中数」；
  文件不存在时**如实记为 not-present**（不写成 PASS）。
- **模式表**（与治理 `validate.py:98-105` 同源，另加本仓用到的形态）：
  OpenAI 式 `sk-` 长串、Google 式 `AIza`、私钥头、`api_key/token/password/secret = <非空值>`；
  **模式自身不得构成可用凭据字面量**（用拼接构造，避免把示例键写进源码）。
- **登记口径**：登记是**本机配置面**的动作（gitignored DB）；记录里只写 redacted 事实
  （端点 id / base_url / 协议 / 模型名 / `credential_ref` 名 / `has_credential=false`），
  **不写任何键值**。凭据**不注入**、不索取明文。
- **不做**：不新增登记面、不改 Policy/eligibility/探测语义、不引入依赖、不改门禁强度、
  不对真实端点发起任何调用（无凭据；健康探针如实失败并登记）。

## 验收条件

- **AC-01 URL 策略补严**：`validate_endpoint_url` 对 localhost / 环回（`127.0.0.2`、`::1`）/
  私有 / 链路本地 / **保留（多播 `224.0.0.1`、IPv6 多播、未指定 `0.0.0.0`、TEST-NET-3 /
  CGNAT `100.64.0.1`）**逐个拒绝且消息点名类别；https/http 公网继续放行；
  `allowed_hosts` 豁免语义不变；**反证**：把 `_host_kind` 改回旧分类 ⇒ 新用例红。
- **AC-02 出站 0**：被 URL 策略拒绝时，endpoint test / probe **不发起任何请求**
  （记录型 transport 证明 `seen == []`）。
- **AC-03 登记入库**：配置面 DB 里端点行 + 模型行存在且可读回（只读查询），
  端点 `protocol = ANTHROPIC`、`base_url` 为该公网地址、`credential_ref` 指向**名字**、
   模型名 `agnes-2.5-flash`；**DB 行里不含任何键值**（审计面另判）。
- **AC-04 明文凭据审计**：四面扫描（跟踪文件 / 记录 / DB / 日志）逐面报告文件数与命中数，
  命中即红；**反证**：往跟踪文件里写一个**测试用假键**（跑完删除）⇒ 审计红。
- **AC-05 重启失效边界同源**：代码 docstring / `docs/integration/LLM_ENDPOINTS.md` §9 /
  UI 文案三面都写明「凭据只在进程内存或环境变量；不是 Secret Manager；重启后需重新注入」，
  并逐面给出 `文件:行` 证据；文档里「加密 / Secret Store」这类不实口径必须改掉。
- **AC-06 无凭据如实失败**：对已登记端点跑健康探针 ⇒ `ok=false` +
  `error_category=CONFIGURATION` + **无出站**；记录里写明「未记 PASS、未伪造指纹、未跳过成绿」。
- **AC-07 门禁**：受影响定向套件 + 规模门 + `ruff`/`format`/`mypy` + **m0 全量 23 项** +
  治理 `validate.py` 绿。

## 实施清单

### WP-A — URL 策略补严（保留 / 多播 / 未指定 / CGNAT）

- `packages/application/model_relay/endpoint_policy.py`：`_host_kind` 增加 `reserved` 类别
  （`is_multicast` / `is_reserved` / `is_unspecified` / CGNAT / `not is_global`），
  `validate_endpoint_url` 默认拒绝并点名。
- 用例：逐个拒绝 + 公网放行 + 豁免不变 + **反证**。
- 提交：`fix(relay): refuse reserved and multicast endpoint hosts by default`

### WP-B — 出站 0 与探针语义

- 用例：被拒 URL / 缺凭据两条路径各用记录型 transport 证明 `seen == []`。
- 提交：`test(relay): prove refused endpoints and missing credentials cause zero outbound`

### WP-C — 明文凭据审计

- 新增审计脚本（`tools/credential_audit.py`，可复跑、逐面报告）**或**定向测试；
  决定：**测试 + 脚本双形态不重复**——实现为 `tools/credential_audit.py`（可被判据调用），
  测试 `tests/tooling/test_credential_audit.py` 断言「干净树上 0 命中」并**注入假键反证**。
- 提交：`test(tooling): audit plaintext credentials across tree, records, DB and logs`

### WP-D — 真实端点登记（本机配置面）

- 脚本（scratch，gitignored）：经**真实 API**（`POST /llm-endpoints` + `POST /models`）
  把端点与模型写进配置面 DB；凭据**不注入**。
- 只读读回：端点行 / 模型行字段（redacted）记入 RECHECK。
- 提交：无（gitignored）；**证据落记录**。

### WP-E — 重启失效边界同源

- `docs/integration/LLM_ENDPOINTS.md` §9 改写（去掉「加密 / Secret Store」）；§3 增补保留地址。
- UI：端点面（录入/详情）文案与代码/文档同口径。
- 提交：`docs(integration): state the credential boundary honestly (no secret manager)`

### WP-F — 反证、记录与收口

- 逐条反证（先红后复原）并登记前后对照；子 PLAN 收口 + RECHECK；GOAL 回写。
- 提交：`docs(goals): close GOAL-008 cycle 3 -- EC-03 ...`

## 证据

（实施中登记：每条 AC 的命令 + 实测输出摘要 + 反证前后对照。）

## 状态历史

- 2026-09-20 建档（GOAL-008 cycle 3 = EC-03）：`status: IN_PROGRESS`。
  只读勘察确认 8 条事实（URL 策略唯一裁决点且注册面不校验 → `_host_kind` 对多播/CGNAT 判 public
  → 凭据两面 + 记录「重启清空」→ 文档 §9 口径不实 → 运行期防泄漏测试已存在但缺仓库/DB/日志审计
  → 无凭据时 configuration_failure → 配置面 DB 位置与 gitignore → 真实端点授权与「无凭据」现状）。

## 影响报告

- **Domain/API/schema 变化**：无 Domain 改动；**行为变化** = URL 策略对**保留类地址**从「放行」
  改为「拒绝」（原判定把多播/CGNAT 当公网）——这是**收紧**，可能让既有「用多播/保留地址做端点」
  的配置从可用变为被拒；仓库内无用例依赖该行为（勘察第 2 条已列出）。
- **安全/凭据变化**：凭据面**无写入**（不注入、不落盘、不回显）；新增审计面把「明文凭据是否
  出现在仓库/记录/DB/日志」变成可复跑判据。
- **兼容性/迁移风险**：注册面仍不校验 URL（本轮不改语义，只登记边界）；已登记的存疑 URL
  仍可入库，但 probe/run 时会被拒——已在口径与记录里点名。
- **上游版本影响**：无（不引入依赖、不改 pin）。
- **下一项任务**：按 EC 表序，EC-03 收口后取 **EC-05（漂移可见性）**；EC-04（首次真实 run）
  仍受**无凭据**限制，届时按「如实 skip」处置。
