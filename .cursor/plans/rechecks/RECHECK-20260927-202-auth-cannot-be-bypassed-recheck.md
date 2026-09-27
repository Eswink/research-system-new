---
id: RECHECK-20260927-202
slug: auth-cannot-be-bypassed-recheck
title: GOAL-021 cycle 1（EC-01）独立复检：枚举来自代码 + 三轮按压矩阵（3/3 红）+ 逐字节复原 + 既有判据零改动
plan_id: PLAN-20260927-201
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-27
completed_at: 2026-09-27
owners:
  - root-agent
---

# RECHECK-20260927-202 — 认证不可绕过（GOAL-021 EC-01）

## 检查结果

**复检口径**：不复用 PLAN / GOAL 的结论叙述；每一项给出**可复核观察面**（命令、文件、
行号、日志、sha256）。**未实跑的不记通过**。

### 一、枚举面：来自代码，且两口径互证

**复检动作**：不采信「枚举来自代码」这一叙述，直接跑两个**独立**口径并对账。

| # | 观察 | 结果 |
| --- | --- | --- |
| 1.1 | AST 口径（扫 `services/api/routers/*.py` 的 `@router.<m>` 装饰器，含 `async def`） | **60 处**，分布在 **17** 个 router 文件 |
| 1.2 | OpenAPI 口径（构建 app 后读 `paths` 的 mutating 操作） | **60** |
| 1.3 | 两口径一致 | **是**（`scratch/goal021-ec01-probe-enumeration.py` 输出 `两口径一致: True`） |
| 1.4 | 有 mutating 端点的 router 文件 | **17**（`team_protocol.py` 7 / `ops_control.py` 6 / `llm_endpoints.py` 5 / `tool_registrations.py` 5 / `approvals.py` 4 / …）；`services/api/routers/` 下共 **29** 个 router 模块（其余 12 个只有读面） |
| 1.5 | 与用户任务书的表述差异（**如实登记**） | 任务书写「约 62 处、29 个 router」。实测 **60 处**；**29 是 router 模块总数**，**有写面端点的 router 是 17 个**。⇒ 判据**不得**采用任务书的数字作为断言，只采用**代码枚举**的结果 |
| 1.6 | 判据内是否手写清单 | **否**——判据调用 `create_app()` 读 OpenAPI；`_MEASURED_MUTATING_COUNT = 60` 是**漂移告警线**，不是保护面定义（判据注释明写） |

### 二、行为面：全部写面端点无 token / 错 token 一律 401

**复检动作**：跑新判据文件，看**逐个端点**的结果。

| # | 观察 | 结果 |
| --- | --- | --- |
| 2.1 | `test_every_mutating_endpoint_rejects_a_missing_token` | **通过**（60 个端点逐个无 token ⇒ 全 401，`leaked == []`） |
| 2.2 | `test_every_mutating_endpoint_rejects_a_wrong_token` | **通过**（带不匹配 token 同样全 401） |
| 2.3 | 认证**先于路由**（建档期实测） | 对**不存在**的路径 `POST` 无 token ⇒ **401**（不是 404）⇒ 未知路径不构成绕过面；带 token 时同一请求得 **422**（缺 `Idempotency-Key`） |
| 2.4 | 判据规模 | **285 行**（≤ 450 硬上限）；**无** > 40 行的函数；`ruff check` + `ruff format --check` + `mypy` 全过 |
| 2.5 | **本轮被全量门抓到并修掉的一处真红** | `python/typecheck` 判红 **7 处**——`TestClient.app` 的静态类型是 ASGI callable（**不是** `FastAPI`），直接 `.openapi()` / `.state` 被 mypy 判错。**修法**：收敛一处 `_app_of(client) -> FastAPI`（内部按本仓既有约定 `cast(FastAPI, cast(Any, client.app))`，同 `test_memory_api.py`），**不是**散落 7 个 `cast` 或加 `# type: ignore` 抑制。修后定向 `mypy` **Success** + 判据 18 passed。**⇒ 定向套件绿 ≠ 全量门绿**（该 check 只有全量门跑到） |

### 三、按压矩阵：3/3 红，逐轮报**实际判红集合**，全部逐字节复原

**复检动作**：对 `services/api/middleware.py` 施加三种**破坏**，每次跑新判据并记录
**具体哪些用例红了**；每次用 `sha256` + `git diff` 证明复原。

**按压前 sha256**（也是复原后、且等于 HEAD 的值）：
`ca03dac36982d5509e34ae719e352fbc84cd70189a526bd3389621597c82691a`

| # | 按压 | 破坏内容 | 期望 | **实际判红集合** |
| --- | --- | --- | --- | --- |
| 3.1 | **PRESS-1** | `_MUTATING_METHODS` 去掉 `DELETE` | 枚举行为面红 | **3 failed**：`test_every_mutating_endpoint_rejects_a_missing_token`、`test_every_mutating_endpoint_rejects_a_wrong_token`、`test_the_protected_set_is_exactly_the_mutating_classification` |
| 3.2 | **PRESS-2** | `_MUTATING_METHODS` 加入 `GET` | 读面设计面红 | **4 failed**：`test_the_protected_set_is_exactly_...`、`test_health_and_read_endpoints_are_reachable_without_a_token`、`test_the_read_face_is_open_because_it_is_not_in_the_write_classification`、`test_a_read_request_is_never_challenged_even_on_a_mutating_route` |
| 3.3 | **PRESS-3** | 认证面对 `_is_analysis_post` 放行（继承幂等豁免） | 豁免行为面红 | **10 failed**：2 条枚举行为面 + **8 条** `test_analysis_endpoints_still_require_a_token[…]`（`/protocol-drafts/validate`、`/protocols/validate`、`/projects/example-project/compile`、`/preflight`、`/dry-run`、`/llm-endpoints/probe-id/test`、`/discover-models`、`/models/probe-id/probe` **逐个**红）。**在判据最终版（285 行）上复跑，红集合逐条相同** |
| 3.4 | 复原复核 | `sha256sum services/api/middleware.py` | 等于按压前 | **相等**；`git diff --quiet services/api/middleware.py` ⇒ **IDENTICAL TO HEAD** |
| 3.5 | 复原后复跑 | 定向套件 | 绿 | **53 passed**（`test_write_face_cannot_be_bypassed` + `test_principal_auth` + `test_control_plane_auth_same_source` + `test_security_scan`） |

**按压形态的可证伪性（先于判据、建档期实测）**：写判据之前先用
`scratch/goal021-ec01-probe-press-shape.py` 证明两个按压形态**真的会红**——
按压①（删 `DELETE`）使端点得 **404**、按压②（继承豁免）使端点得 **422**，
基线 **401**、复原 **401**。⇒ 本 EC 的按压条款**不是空话**。

### 四、与既有判据的分工（不重复、不顶替）

| # | 观察 | 结果 |
| --- | --- | --- |
| 4.1 | EC-01(b) 的**结构**面 | 由 `test_control_plane_auth_same_source.py::test_auth_face_does_not_inherit_the_idempotency_exception_set` 判（AST 断言不引用 `_ANALYSIS_ACTIONS`）——**本 PLAN 未改该文件** |
| 4.2 | EC-01(c) 的**顺序**面 | 由同一文件 AC-5 `test_auth_middleware_is_registered_after_idempotency` 判（注册顺序）——**本 PLAN 未改该文件** |
| 4.3 | 本 PLAN 的**新增**面 | 枚举行为全覆盖 / 豁免的**行为**面 / 读面「**这是设计**」的机制断言 —— **不复制** 4.1 / 4.2 的断言 |
| 4.4 | 四个受保护判据文件零改动 | `git diff --quiet` 对 `test_control_plane_auth_same_source.py` / `test_reproducibility_wording.py` / `test_record_face_is_covered_by_the_gate.py` / `test_security_scan.py` **全部 UNCHANGED** |

### 五、凭据纪律

| # | 观察 | 结果 |
| --- | --- | --- |
| 5.1 | 判据中的 token | 本文件内构造的**合成假值**（`fixture-` + 重复字符），**非**真实凭据；**不**从环境读取、**不**落盘、**不**进日志 |
| 5.2 | 仓库 token **值**命中 | **零**（只出现**变量名**如 `CONTROL_PLANE_TOKEN_ENV`） |
| 5.3 | `tools/credential_audit.py` | 四面 `offenders=0`：tracked `hits=96 allowed=96` / records `hits=3 allowed=3` / config_db `0` / logs `0` |

### 六、零产品代码改动（本 EC 的自检结论）

**复检动作**：确认自检**是否证明了任何缺陷**（是 ⇒ 需修产品代码）。

| # | 观察 | 结果 |
| --- | --- | --- |
| 6.1 | 判据证明了写面有漏网吗 | **没有**——60/60 端点全 401，`leaked == []` |
| 6.2 | 判据证明了豁免被继承吗 | **没有**——8 个分析类端点无 token 全 401 |
| 6.3 | 判据证明了读面被误拦吗 | **没有**——读面与 `/health` 均放行 |
| 6.4 | ⇒ 产品代码改动 | **零**（`services/api/middleware.py` 三轮按压后 `git diff` 为空） |
| 6.5 | 自检结论 | **边界成立**（不是「修好了」——本轮**没修任何东西**，是**证明它们本来就成立**） |
| 6.6 | 但本轮**确有一处真红**（非产品缺陷） | `python/typecheck`（见 2.5）：**判据自身**的类型写法被 mypy 判错 ⇒ **修的是判据**，不是产品。**如实登记**为「本轮修掉的缺陷 = 判据类型面 1 处」，**不**把它说成产品缺陷 |

## 结论

**`PASS_WITH_WARNINGS`**。GOAL-021 **EC-01** 的四条（a)(b)(c)(d）**全部成立且有实跑证据**：
枚举来自代码（两口径互证 60）、写面全覆盖 401（含错 token）、豁免面**结构 + 行为**双证不继承、
读面放行**按分类机制**断言（PRESS-2 证明该机制可判红）。按压 **3/3 红**、逐字节复原、
既有判据**零改动**、**零**产品缺陷。

**警告（如实登记，不构成 PASS 的例外）**：

- **`W-1`**：`_MEASURED_MUTATING_COUNT = 60` 是一条**会随时间失效**的告警线——树里增删写面端点
  时判据会**红**（这是设计意图：提示复核），但需要人工确认「是有意增删还是漂移」。
  它**不是**保护面的定义（定义来自枚举），所以**不会**造成漏保护，只会造成**误报式提醒**。
- **`W-2`**：本轮的「全覆盖」是**控制面 app** 的范围；**worker 网关是独立 app**
  （`create_worker_app`，未挂载到控制面 ⇒ 建档期实测 `app.routes` 无 worker 挂载），
  它有自己的信任域与认证面（`worker_gateway/auth.py` 的 `verify_enrollment`）。
  本 EC **不**宣称覆盖 worker 面。
- **`W-3`**：ENS（枚举）覆盖的是**app 声明过的**端点。若某个写操作**绕过 FastAPI 路由**
  （如 SSE 长连接内的副作用、后台调度器触发的写），它**不**在枚举面内 ⇒ 本判据**不覆盖**
  这类路径。**这是范围的诚实边界**，不是缺陷（这类路径的凭据面另属 worker/调度器信任域）。
- **`W-4`**：按压是**内存态**破坏（改模块属性 / 临时改一行再复原），**不是**改 tracked 文件后跑 CI。
  ⇒ 它证明的是「判据对这类破坏敏感」，**不**证明「CI 会在有人提交这类改动时拦住」——
  后者由 CI 跑本判据本身覆盖（判据在 CI 里，破坏会被判红）。
- **`W-5`**：本轮的 token 是合成假值 ⇒ **不**验证真实 token 的熵 / 长度 / 轮换行为
  （那属 `IDENTITY_AND_ACCESS.md` 的运维面，GOAL-020 EC-03 已给检查项）。

**未覆盖范围（承 GOAL-021 的边界，原样保留）**：读面未认证 / 多租户与 RBAC 未做 /
BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口（**不得**宣称项目安全）。
**本 RECHECK 证明的是「已声明的写面边界成立」，不能证明「不存在未声明的缺口」。**

### 七、全量门（记录写完之后）

| # | 观察 | 结果 |
| --- | --- | --- |
| 7.1 | `uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going` | 终态行 **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、**4577 passed / 21 skipped**、零 `FAILED`/`ERROR`；日志 `scratch/goal021-c1-m0-final.log`） |
| 7.2 | 运行时刻 vs 记录写入 | 记录 mtime **15:05**（PLAN / RECHECK / GOAL）< 门日志 mtime **15:16** ⇒ **门跑在记录之后**（承 MEM-145 的顺序） |
| 7.3 | 首跑与本轮的差异 | 首跑 `python/typecheck` 判红（见 2.5）⇒ **修判据**（非产品）⇒ 复跑全绿 |
| 7.4 | m0 条数 | 仍为 **23** ⇒ 新增判据**未**新增 check（落在既有 `python/tests` 收集面内） |
| 7.5 | 记录面判据 | `tests/architecture/python/` + `tests/tooling/` ⇒ **1369 passed**（记录面在受判集合内） |
