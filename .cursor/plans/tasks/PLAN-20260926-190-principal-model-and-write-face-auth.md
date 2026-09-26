---
id: PLAN-20260926-190
slug: principal-model-and-write-face-auth
title: GOAL-019 cycle 1（EC-01 + EC-02）：`Principal` 域值对象 + 写面 token 认证 + 请求主体归因落 canonical
status: DONE
created_at: 2026-09-26
updated_at: 2026-09-26
parent_goal: GOAL-20260926-019
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260926-019 的 **EC-01**（主体模型 + 请求级主体归因落 canonical）与
    **EC-02**（认证面：写面 token 保护 / 三态 / 凭据纪律）。授权沿用该 GOAL 的
    `authorization.ref`：**只保护写面**（复用 `_MUTATING_METHODS` 同一分类）、
    **认证可关**（环境变量留空 ⇒ 关闭 + 启动显式警告）、**主体归因落 canonical**
    （**向后兼容**：缺主体时既有行为**逐字不变**）、push-to-main-for-CI 口径
    （**只推 main、不 force、不重写历史、不推旁支**）、默认 runtime 保持 **Fake**、
    默认 CI **离线**。**明文不做**：多租户 / organization scope / RBAC / 角色权限矩阵 /
    M18 任何内容；**不给读面加认证**；**不改 `Idempotency-Key` 语义**；
    **不把 token 写进任何文件 / CI / 记录 / 日志 / 遥测 / 测试输出**；
    **不新增依赖**（token 校验必须用标准库 `hmac.compare_digest`，**不得**用 `==`）；
    **不做** D-12 的 (a) 面（BOLA / BFLA 专项测试与门）。
    本 PLAN **不放宽任何判据 / 阈值 / 放行面**，**不新增策略面 allow**，
    **不改 Canonical State 边界**，**不得宣称项目安全**。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260926-191-principal-model-and-write-face-auth-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260926-143-auth-face-reuses-the-one-classification.md
---

# PLAN-20260926-190 — `Principal` 域值对象 + 写面 token 认证 + 请求主体归因落 canonical

## 目标

把 GOAL-019 的 **EC-01** 与 **EC-02** 一次做完（二者是**同一层**的两半：
EC-02 落在 HTTP 边界，EC-01 落在 canonical 与读面）：

1. **EC-02 认证面**：新增一个**写面**认证中间件——只对
   `_MUTATING_METHODS`（`services/api/middleware.py:23`，**复用同一分类，不新造第二套**）
   要求的请求校验 `Authorization: Bearer <token>`；token **从环境变量读取**、
   **常数时间比较**（`hmac.compare_digest`）、**不落盘 / 不进日志 / 事件 / 遥测**；
   **读面（GET/HEAD）放行**；**环境变量留空 ⇒ 认证关闭**并在**启动时打印显式警告**
   （文案必须**明确说「无认证」**）。
2. **EC-01 主体模型**：新增 `Principal` **域值对象**（**主体 id + 类型**两要素；
   **不含**租户 / 角色字段）+ **请求级主体归因**：认证通过后，真实主体**落 canonical**
   （`EventEnvelope.actor` → `outbox_events.envelope_json`）并在**读面可见**
   （`GET /runs/{id}/events`），**替换**今天硬编码的占位。

**验收主路径（实测已定）**：`POST /approvals/{approval_id}/decide` 是
**唯一**在请求内同步发布 canonical 事件（`deps.events.publish(event)`）的写路径
（`services/api/routers/approvals.py:125`，其上一行 `:124` 硬编码 `actor="user:console"`）
⇒ 端到端链路 = **带 token 的 decide 请求 → outbox 的 `approval.decided` 事件 actor
== 配置的主体 → `GET /runs/{run_id}/events` 读得到**。

## 关键设计决定（建档当日侦察所得，实施时须逐条留证）

### D-1｜主体是**一个**配置的服务主体，**不是**「每个调用方一个身份」

单 token 场景下，**token 即身份**。⇒ 本 PLAN 的 `Principal` 是**唯一**的、
**配置而来**的服务主体；**不做**「调用方自报 id」——那在无逐调用方凭据时
**可被伪造**，会形成「看起来有归因、其实可冒充」的假象（比不做更坏）。
**诚实边界（必须写进文档与判据面）**：**单一共享 token ⇒ 单一主体**；
「每个调用方各自身份」需要**逐调用方凭据**，**不在本 GOAL 范围**。⇒ 判据里的
「主体是请求带的那个」= 「canonical 里的主体是**配置的**那个，而**不是**占位常量」。

### D-2｜`default_actor` 的处置 = **读点回退**，不删字段、不改缺省值

`OrchestrationDependencies.default_actor`（`dependencies.py:53`）今天**没有任何装配方
显式传值**（`composition.py:307` 的构造不传它）⇒ 生效值恒为 `"system:orchestration"`。
**设计**：在事件**发布读点**（`packages/application/run_orchestration/eventing.py:34`
`publish_event` 里读 `sink._actor`）改成「**请求级主体优先，缺则回退 `sink._actor`**」。
⇒ **缺主体（= 认证关闭）时行为逐字不变**（仍产出 `system:orchestration`）；
**字段与缺省值一字不改**（`dependencies.py` 与 `service.py` **零改动**，
避开两个 450 行零余量文件）。**反证**：认证关闭时同一路径的 `actor` 取值须与基线**逐字相同**。

### D-3｜审批路径的处置 = **回退到现有字面量**，不是换成新常量

`routers/approvals.py:124` 的 `actor="user:console"` 是**请求级主体**（谁处置了审批），
⇒ 改成「**有请求主体用请求主体，否则沿用 `"user:console"`**」。
⇒ 认证关闭时 `actor` **仍是 `"user:console"`**（离线基线逐字不变），
认证开启时变成配置的主体。**不得**把回退值改写成别的字符串。

### D-4｜其余 4 处 actor 字面量**本次不动**（逐条判定留证）

`adapters/sqlite/outbox.py:38` / `adapters/postgres/outbox.py:43`
（`system:workflow-engine`）、`services/api/routers/tool_packs.py:50`（`console`）、
`services/api/routers/policy.py:75`（`system:policy-view`）、
`packages/application/m12_reference/clean_run_stages.py:113`（`system:m12`）——
**均为「系统自身动作」而非「某次请求」**（workflow engine 的 relay、只读快照视图、
参考实现内部步骤）⇒ **保持常量**是**正确**语义，**不在**本 GOAL 的替换面。
**判定须逐条写进本 PLAN 的证据节**（不是"没管"）。

### D-5｜中间件顺序 = 认证**在**幂等**之外**（先认证再进幂等）

实测 Starlette 1.6.0 `build_middleware_stack`：`reversed(middleware)` 逐层包裹 ⇒
**`user_middleware` 里靠前者在外层**；`add_middleware` 插入到**表头** ⇒
**后 `add_middleware` 的在外层**。而 `create_app()` 先加
`IdempotencyMiddleware`（`services/api/app.py:277`）⇒ **认证中间件必须在它之后添加**
才会**先执行**，从而让未认证的写请求**不消耗 `Idempotency-Key` 槽位、不写响应缓存**。

### D-6｜`/health` 不需要特例

`/health` 是 **GET**（`_register_health_route`，`services/api/app.py:52`）⇒
按「读面放行」自动豁免；compose 的 api healthcheck 也正是
`urlopen('http://127.0.0.1:8000/health')`（`infra/compose/research-validation.yaml:96`）。
⇒ **不加路径白名单**（少一处可漂移的特例）；**判据**：设了 token 时
`GET /health` **不带** token 仍 **200**（这是「保护范围只有写面」的正面反证）。
**注意**：不引入 `_ANALYSIS_ACTIONS`（`middleware.py:27`）式的按路径例外——
那是**幂等**面的例外，**不**自动成为认证面的例外；认证面**只按方法分类**。

### D-7｜token 的配置面与形态

- 变量名沿用 `RESEARCHOS_*`：**`RESEARCHOS_CONTROL_PLANE_TOKEN`**（凭据类命名与
  `RESEARCHOS_WORKER_ENROLLMENT_SECRET` 同侧）。**只登记名字，绝不留值**；
  **`.env.example` 也不加**（避免任何占位值落盘）。
- 读取点 = `create_app()` 装配期（**构造期快照**，与 worker 网关的凭据姿态一致；
  `services/api/settings.py` 提供 `from_env` 解析面）。
- **不得**把 token 放进 `ApiDeps`：`services/api/composition.py` = **450 行零余量**，
  动它**必须先搬代码** ⇒ 取「`create_app` 读配置 → 作为参数传给中间件」的形态。
- 主体 id 的来源**必须**与 token 同源（配置），**不得**由请求头自报（见 D-1）。

### D-8｜新增文件优先，避免碰零余量文件

- **新增** `packages/domain/principal.py`（`Principal` 值对象 + 类型枚举）。
- **新增** `services/api/principal_auth.py`（token 读取 / 常数时间校验 /
  `Principal` 解析 / 请求上下文存取）。**或者**放进既有的
  `services/api/middleware.py`（101 行，余量充足）——**但** `IdempotencyMiddleware`
  的类体、`_MUTATING_METHODS`、`_ANALYSIS_ACTIONS`、`_is_analysis_post`、`_problem`
  **须逐字节不变**（EC-03 的取证面）。
- **零改动目标**：`packages/application/run_orchestration/dependencies.py`、
  `packages/application/run_orchestration/service.py`、
  `services/api/composition.py`（三个零余量文件）。
- `packages/application/run_orchestration/eventing.py`（86 行）**允许改**（D-2 的读点）。

## 验收条件

- **AC-1（EC-02 三态）**：**未设 token** ⇒ 认证关闭 + **启动显式警告**（文案明确说
  「无认证」/「任何人可写」）+ 写面放行（2xx）；**设了 token + 不带 / 带错** ⇒
  **401 且点名**（响应体给出缺失/不匹配的具体原因）；**设了 token + 带对** ⇒ 放行。
- **AC-2（EC-02 范围）**：保护范围**只有写面**——`GET /health` 与至少一条普通 `GET`
  在**设了 token 且不带 token**时仍 **2xx**（正面反证）。
- **AC-3（EC-02 纪律）**：比较走 `hmac.compare_digest`（**反证**：改成 `==` ⇒
  判据判红）；token **值**在全仓（排除 `.git`）**零命中**，且**不在**日志 / 事件 /
  遥测 / 测试输出里。
- **AC-4（EC-01 主体）**：带 token 的 `POST /approvals/{id}/decide` ⇒ canonical
  （outbox 的 `approval.decided`）的 `actor` == **配置的主体**（**不是** `"user:console"`）；
  且 `GET /runs/{run_id}/events` **读得到**该主体。**配对反证**：不带 token 的同一请求
  ⇒ 被拒、且 canonical 里**不留**该主体（不能「拒了但写了」）。
- **AC-5（EC-01 兼容）**：认证**关闭**时，审批路径的 `actor` 仍是 **`"user:console"`**、
  run 链事件的 `actor` 仍是 **`"system:orchestration"`**——**实测取值逐字对照**基线
  （不是「套件没红」）。
- **AC-6（EC-03 零回归）**：`tests/api` / `tests/contracts`（含 **OpenAPI 快照**）/
  `tests/e2e` / `tests/architecture/python`（含 runbook 同源族）/ `tests/worker` 全绿；
  `IdempotencyMiddleware` 的 `dispatch` 体与 `_MUTATING_METHODS` **逐字节未改**
  （`git diff` 取证）。
- **AC-7**：`ruff check` / `ruff format --check` / `mypy` 绿；规模门禁（450 行 / 50 行）
  绿且**未新增触线**；治理 `validate.py` + `DOCS-CHECK` 绿。
- **AC-8**：本 PLAN 的判据**可被按压**——逐条「临时破坏 ⇒ 判红 ⇒ 逐字节复原」。

## 实施清单

- [x] **WP1｜`Principal` 域值对象**：新增 `packages/domain/principal.py`
      （`Principal` + `PrincipalKind`；**无**租户 / 角色字段）；域纯度门禁绿。
- [x] **WP2｜认证中间件（写面）**：`ControlPlaneAuth` / `control_plane_auth_from_env` /
      `auth_disabled_warning` / `verify_control_plane_token` / `_bearer_token` /
      `PrincipalAuthMiddleware` **并入 `services/api/middleware.py`**（D-8 的「并入」支——
      该文件**已在** `.importlinter.api` 的 `source_modules` 里 ⇒ **不必改门禁**即被边界覆盖）；
      `create_app()` 经 **`_install_write_face_auth(app)`**（新助手）在 `IdempotencyMiddleware`
      **之后**注册；`_lifespan` 在认证关闭时打印显式警告。
- [x] **WP3｜主体归因落 canonical**：`packages/application/principal_context.py`（请求级主体
      上下文）+ `eventing.publish_event` 读点回退（D-2）+ `routers/approvals.py` 用请求主体
      （回退 `"user:console"`，D-3）。**`dependencies.py` / `service.py` / `composition.py`
      三个零余量文件零改动**。
- [x] **WP4｜判据（成对可按压）**：`tests/api/test_principal_auth.py` **18 passed**；
      三次按压（A 去校验 / B 强制回退 / C 读面也拦）分别 **2 / 1 / 5 failed**，
      全部逐字节复原。
- [x] **WP5｜本地验证**：`tests/api` + `tests/contracts` **924 passed / 73 skipped**（含
      OpenAPI 快照绿）；`tests/architecture/python`（canonical `uv run`）**175 passed**；
      `ruff check` / `ruff format --check`（1032 files）绿；规模门禁 **1032 passed**；
      **m0 全量 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = 24、
      `python/tests` = **4538 passed / 20 skipped**）；治理 `validate.py` 绿 + `DOCS-CHECK PASS`。
- [x] **WP6｜记录**：本 PLAN + `RECHECK-20260926-191` + GOAL-019 回写 + ALL_PLAN 投影
      （**本提交**）。**EC-04（四处文档）与 EC-05（收口）留给后续 cycle**（见 W-2 / W-3）。
- **前端 e2e（认证关闭，同轮实跑）**：`pnpm --dir apps/web test:e2e` = **98 passed (5.2m)**、
  `test:e2e:live` = **53 passed (1.1m)**，退出码均 0 —— 与 GOAL-018 基线**计数完全一致**
  （`scratch/goal019-c1-e2e-stub.log` / `…-live.log`）。

## 证据

（全部**实跑**；判定见 `RECHECK-20260926-191`。）

- **D-9（实施期新增决定）｜**不**复用 worker 网关的 `extract_bearer`**：实测
  `services/api/worker_gateway/__init__.py` **急切**导入 `create_worker_app` /
  `WorkerGatewayDeps` / `WorkerGatewaySettings`，且其 docstring 明写「Kept separate from
  the Control Plane API so the worker trust domain has its own auth dependency and DTOs」
  ⇒ 复用会把 **worker 信任域**整体拉进控制面的导入图。改为在 `services/api/middleware.py`
  内**自带 7 行** `_bearer_token`，只**沿用同一原语与同一不变量**
  （`hmac.compare_digest`；空值永不匹配）。
- **主体模型**：`packages/domain/principal.py` — `Principal(id, kind)` + `PrincipalKind`；
  `actor` 属性 = `"<kind>:<id>"`；`from_actor` 对**形态不合法 / 类型未知**返回 `None`
  （不猜测）。不变量：id 非空、无首尾空白、**不含 `":"`**。
- **实测取值（金标）**：`Principal(id="console", kind=USER).actor == "user:console"`、
  `Principal(id="orchestration", kind=SYSTEM).actor == "system:orchestration"`
  ⇒ 既有占位常量**可被同一值对象表达**（不是硬编码字符串）。
- **认证三态**（`tests/api/test_principal_auth.py`，**18 passed**）：
  未设 token ⇒ POST **200** 且端点回报 `actor=None`（**无认证**，非"已认证"）；
  设 token + 不带 ⇒ **401** + `detail` 含 `Bearer`；带错 ⇒ **401** + `detail` 含
  `does not match`；带对 ⇒ **200** 且端点内 `current_principal().actor ==
  "service:fixture-principal"`（**上下文传播实测**）。
- **读面反证**：受控面 `GET` + **真实 app** 的 `GET /health` 与 `GET /runs/{id}`
  在「设了 token 但不带 token」下均 **200** ⇒ 保护范围**只有写面**。
- **主体落 canonical**：带 token 的 `POST /approvals/{id}/decide` ⇒ 读
  `GET /runs/{id}/events` 的 `approval.decided` ⇒ `actor == service:fixture-principal`，
  且 `"user:console" not in actors`。
- **配对反证（不落 canonical）**：不带 token / 带错 token ⇒ **401** + 决策事件**零条** +
  run **仍为 `WAITING_FOR_APPROVAL`**（不是"拒了但写了"）。
- **向后兼容对照（实测取值）**：认证关闭时同一路径 `actors == ["user:console"]`
  （**逐字**与基线一致，**不是**「套件没红」推定）。
- **按压（非恒真）**：PRESS-A 去掉校验 ⇒ **2 failed**；PRESS-B 强制回退常量 ⇒ **1 failed**
  （判词 `assert ['user:console'] == ['service:fixture-principal']`）；PRESS-C 读面也拦 ⇒
  **5 failed**；三次均**逐字节复原**（`rg "PRESS-"` 零命中，复原后 18 passed）。
- **`Idempotency-Key` 一字未动**：`ast.get_source_segment` + `sha256[:16]` 对 HEAD 比较 —
  `IdempotencyMiddleware` `78072fb10f633ffe`、`.dispatch` `621b1605c11d18b7`、
  `_is_analysis_post` `7740b6009048f164`、`_problem` `9ddb50204466a888` **全部 IDENTICAL**；
  `_MUTATING_METHODS` / `_ANALYSIS_ACTIONS` 字面量**逐字相同**。
- **凭据纪律（四条反证）**：变量名在全工作树**恰好出现 1 次**（`middleware.py:127` 的名字常量）；
  `RESEARCHOS_CONTROL_PLANE_TOKEN\s*=` **零命中**（从不赋值）；新代码唯一比较是
  `hmac.compare_digest`；`token ==` / `== …token` **零命中**；`.env.example` **未改**。
- **零改动面**：`packages/application/run_orchestration/dependencies.py` 与
  `service.py`、`services/api/composition.py`（三个 450 行零余量文件）`git diff` **为空**；
  `apps/web/**` **零改动**。
- **定向套件**：`tests/api` + `tests/contracts` = **924 passed / 73 skipped / 0 failed**
  （含 **OpenAPI 快照** ⇒ 无漂移）；`tests/architecture/python`（canonical `uv run --frozen
  --no-sync`）= **175 passed**。
- **全量 m0**（独占、仓库 `.venv`、DSN 固化、`--keep-going`）：终态行
  **`PASS: profile=m0; 23 deterministic checks`**；`PASS [` = **24**；
  `python/tests` = **4538 passed / 20 skipped**；`FAILED`/`ERROR` 零命中；
  日志 `scratch/goal019-c1-m0-rerun.log`。
- **m0 抓到的两处真红（本轮内已修）**：① `python/format-check` —— 新测试文件未纳入
  先前的 `ruff format --check` 清单；② `python/tests::…[services\api\app.py]` ——
  新增 6 行把 **`create_app` 从 47 行推到 53 行**、越过 **50 行函数门禁**（该文件此前只剩
  1 行余量）⇒ 抽 `_install_write_face_auth(app)` 后回到 48 行。**两处只有全量 m0 才会红**
  （定向套件当时全绿）。
- **`ruff`**：`ruff check` = `All checks passed!`；`ruff format --check services packages tests
  adapters` = **1032 files already formatted**；规模门禁 **1032 passed**。
- **治理**：`.cursor/skills/governance-check/scripts/validate.py` 绿；`tools/docs_consistency_check.py`
  = `DOCS-CHECK PASS: 6 deterministic checks`。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-26 | IN_PROGRESS | 派生自 GOAL-20260926-019（cycle 1）：EC-01 + EC-02 合并为一个可独立验收的主题面。侦察完成并落 8 条关键设计决定（D-1…D-8），其中 D-1（单 token ⇒ 单主体，不做调用方自报）与 D-4（其余 4 处 actor 字面量逐条判定为「系统自身动作」）是**诚实边界**的核心。**尚未开始改代码**。|
| 2026-09-26 | VERIFYING | WP1…WP5 落地：`Principal` 值对象 + 请求级主体上下文 + 写面认证中间件（复用 `_MUTATING_METHODS`）+ 读点回退 + 审批路径归因；18 条判据全绿，三次按压判红并逐字节复原；`tests/api`+`tests/contracts` 924 passed、`tests/architecture/python` 175 passed；首次全量 m0 **2 红**（format-check / 50 行函数门禁）⇒ 当场修；复跑 **m0 23/23**。实施期新增 **D-9**（不复用 worker 网关的 `extract_bearer`，避免把 worker 信任域拉进控制面导入图）。|
| 2026-09-26 | DONE | 独立复检 `RECHECK-20260926-191` = `PASS_WITH_WARNINGS`（W-1…W-9；其中 **W-2 / W-3** 明写 EC-04（四处文档）与 EC-05（收口）**本轮未做**）。|

## 影响报告

- **改动面（计划）**：新增 `packages/domain/principal.py`、
  `services/api/principal_auth.py`（或并入 `middleware.py`）；改
  `services/api/app.py`（注册中间件 + 启动警告）、
  `packages/application/run_orchestration/eventing.py`（读点回退）、
  `services/api/routers/approvals.py`（主体归因）；新增判据与文档（EC-04 在后续 cycle）。
- **Domain / API / schema**：新增 `Principal` **域值对象**（**不**入 canonical schema、
  **不**改 DTO、**不**改路由签名）；OpenAPI 快照**预期不漂移**（纯中间件式认证，
  无 `responses` / `securitySchemes` 声明）——若漂移则按既有流程重生成并说明。
- **安全 / 凭据**：新增**读环境变量的 token 校验**（不落盘、不进日志/遥测）；
  **零新依赖**（标准库 `hmac`）；**零**策略面 allow；**不给读面加认证**。
- **兼容性 / 迁移风险**：认证**默认关闭** ⇒ 离线基线行为**逐字不变**（AC-5）；
  `default_actor` / `Idempotency-Key` 语义**一字不动**。
- **上游版本影响**：无（零依赖变化）。
- **下一项任务**：本 PLAN 完成后 => EC-03（零回归对照）/ EC-04（四处文档同源）/
  EC-05（收口复检）。
