---
id: RECHECK-20260926-191
slug: principal-model-and-write-face-auth-recheck
title: PLAN-190 独立复检：认证三态 + 主体落 canonical + 三次按压 + m0 23/23 + `Idempotency-Key` 逐字节未动
plan_id: PLAN-20260926-190
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-26
completed_at: 2026-09-26
owners:
  - root-agent
---

# RECHECK-20260926-191 — PLAN-190 独立复检

## 检查结果

**复检口径**：不复用 PLAN 的结论叙述，直接读树 + 跑判据；每项给出**可复核的观察面**。
**未实跑的不记通过**。本复检**只覆盖 PLAN-190 的范围**（GOAL-019 的 EC-01 / EC-02 与
EC-03 的证据面）；**EC-04（四处文档）与 EC-05（收口）不在本轮**，见 W-2 / W-3。

### 一、认证三态（EC-02 硬判据）

| # | 检查 | 结果 |
| --- | --- | --- |
| 1.1 | **未设 token** ⇒ 认证关闭 + 写面放行 | `test_disabled_auth_lets_mutating_requests_through_without_principal` 实跑：POST → **200**，且端点回报的 `actor` 为 **None** ⇒ 证据**区分了**「无认证」与「已认证」（不是"放行即通过"） |
| 1.2 | **未设 token** ⇒ 启动**显式警告** | `auth_disabled_warning()` 文案含 `CONTROL PLANE AUTH IS DISABLED`、点名 `RESEARCHOS_CONTROL_PLANE_TOKEN`、含边界句 `NOT a statement that the project is secure`；`_lifespan` 在 `not auth.enabled` 时 `_log.warning` 发出 |
| 1.3 | 警告**不回显** token | `test_warning_never_echoes_a_token_value`：警告文案与主体串里**都不含**夹具 token 值 |
| 1.4 | **设了 token + 不带** ⇒ 401 且**点名** | `test_enabled_auth_rejects_missing_token_and_names_the_header`：**401**，`detail` 含 `Bearer` |
| 1.5 | **设了 token + 带错** ⇒ 401 且**点名** | `test_enabled_auth_rejects_wrong_token_and_names_the_mismatch`：**401**，`detail` 含 `does not match` |
| 1.6 | **设了 token + 带对** ⇒ 放行 | `test_enabled_auth_allows_correct_token_and_propagates_principal`：**200** |
| 1.7 | 非 Bearer 方案 ⇒ 401 | `test_enabled_auth_rejects_non_bearer_scheme`（`Basic …`） |
| 1.8 | **读面不受保护**（范围**只有写面**） | 受控面 `test_read_face_is_not_protected` + **真实 app** `test_read_face_of_the_real_app_stays_open_when_auth_is_enabled`（`GET /health` 与 `GET /runs/{id}` **不带 token** 均 **200**） |
| 1.9 | 保护分类**唯一**（不新造第二套） | 认证中间件**直接**判 `request.method not in _MUTATING_METHODS`（同一模块同一符号）；未新增第二套方法集合 |
| 1.10 | **不**按路径设例外 | 认证面**无**路径白名单；`/health` 因是 **GET** 自动豁免（`_ANALYSIS_ACTIONS` 是**幂等**面的例外，**未**被搬进认证面） |

### 二、主体落 canonical（EC-01 硬判据）

| # | 检查 | 结果 |
| --- | --- | --- |
| 2.1 | `Principal` 是**域值对象**且**只有** id + 类型 | `packages/domain/principal.py`：`Principal(id, kind)` + `PrincipalKind`（`USER`/`SERVICE`/`AGENT`/`SYSTEM`）；**无**租户 / 组织 / 角色 / 权限字段 |
| 2.2 | 有**真实用例**把主体写进 canonical | `test_authenticated_decision_records_the_configured_principal`：带 token 的 `POST /approvals/{id}/decide` → 读 `GET /runs/{id}/events` 的 `approval.decided` ⇒ `actor == service:fixture-principal` |
| 2.3 | **不再是占位** | 同一用例断言 `"user:console" not in actors` |
| 2.4 | **配对反证**：不带 token ⇒ 被拒**且不落 canonical** | `test_unauthenticated_decision_is_rejected_and_writes_nothing`：**401** + 决策事件**零条** + run **仍停在** `WAITING_FOR_APPROVAL`（不是"拒了但写了"） |
| 2.5 | 带错 token 同样不落 canonical | `test_wrong_token_decision_is_rejected_and_writes_nothing` |
| 2.6 | **向后兼容对照**：认证关闭时 actor **实测**等于历史常量 | `test_auth_disabled_keeps_the_baseline_actor_verbatim`：**200** 且 actors **== `["user:console"]`**（实测取值对照，**不是**「套件没红」推定） |
| 2.7 | 上下文真的传播到端点 | 1.6 与 2.2 都读的是**端点内**的 `current_principal()` ⇒ 中间件在 `call_next` 前设置、下游同任务可见（实测，非推理） |
| 2.8 | `default_actor` **零改动**且语义向后兼容 | `dependencies.py` / `service.py` 的 **`git diff` 为空**；`eventing.publish_event` 改为 `_event_actor(sink)`：主体为 `None` ⇒ **原样**返回 `sink._actor`（读点回退） |
| 2.9 | 其余 actor 字面量**未被误伤** | 产品侧 6 处 actor 字面量中**只**替换了审批路径（请求级动作）；`system:workflow-engine` / `console` / `system:policy-view` / `system:m12` **一字未动**（系统自身动作） |

### 三、非恒真（按压必须判红，且**复原后逐字节相同**）

| # | 按压面 | 结果 |
| --- | --- | --- |
| 3.1 | **PRESS-A**：把 token 校验改成自比（`verify(provided, provided)`） | **判红**：`2 failed`（`…rejects_wrong_token_and_names_the_mismatch` + `…wrong_token_decision_is_rejected_and_writes_nothing`）⇒ 「去掉校验 ⇒ 带错也放行」的反证成立 |
| 3.2 | **PRESS-B**：把审批主体强制回退常量（`principal = None`） | **判红**：`1 failed`，判词 `assert ['user:console'] == ['service:fixture-principal']` ⇒ 判据**绑行为**、不绑字面量 |
| 3.3 | **PRESS-C**：去掉方法过滤（读面也要求 token） | **判红**：`5 failed` ⇒ 「读面放行」不是恒真断言 |
| 3.4 | 复原 | 三次按压全部**逐字节复原**（`rg "PRESS-"` 零命中；复原后 **18 passed**） |
| 3.5 | 受保护符号**未被按压污染** | 见第五节：哈希对 HEAD 全等 |

### 四、`Idempotency-Key` 语义一字未动（EC-03 硬判据）

| # | 符号 | HEAD 哈希 | 当前哈希 | 结论 |
| --- | --- | --- | --- | --- |
| 4.1 | `IdempotencyMiddleware`（整类） | `78072fb10f633ffe` | `78072fb10f633ffe` | **IDENTICAL** |
| 4.2 | `IdempotencyMiddleware.dispatch` | `621b1605c11d18b7` | `621b1605c11d18b7` | **IDENTICAL** |
| 4.3 | `_is_analysis_post` | `7740b6009048f164` | `7740b6009048f164` | **IDENTICAL** |
| 4.4 | `_problem` | `9ddb50204466a888` | `9ddb50204466a888` | **IDENTICAL** |
| 4.5 | `_MUTATING_METHODS`（字面量） | — | — | **IDENTICAL** |
| 4.6 | `_ANALYSIS_ACTIONS`（字面量） | — | — | **IDENTICAL** |

复现：`ast.get_source_segment` 取各符号源码 + `sha256[:16]`；常量用正则取花括号内字面量逐字比较。
⇒ 认证面是**加性**改动：新增中间件 + 复用同一分类，**没有**改幂等的任何分支。

### 五、凭据纪律（EC-02 硬判据）

| # | 检查 | 结果 |
| --- | --- | --- |
| 5.1 | 变量名在**全工作树**（排除 `.git` / `.venv` / `node_modules`）出现次数 | **恰好 1 次**（`services/api/middleware.py:127` 的**名字常量**）；测试导入的是该**常量**，不重复字面量 |
| 5.2 | 是否存在**给该变量赋值 token 值**的地方 | `RESEARCHOS_CONTROL_PLANE_TOKEN\s*=` ⇒ **零命中**（值只在运行进程的环境变量里） |
| 5.3 | 比较是否常数时间 | 新代码唯一的比较是 `hmac.compare_digest`（`middleware.py:194`）；`token ==` / `== …token` 形态 ⇒ **零命中** |
| 5.4 | 空值语义 | `verify_control_plane_token` 对空 `provided` / 空 `expected` **都**返回 `False`（不把「未配置」当匹配）；`test_empty_never_matches` 实跑 |
| 5.5 | 不回显 / 不进日志 | 警告只打印**变量名**（1.3 实跑）；无任何 logger 调用传 token；未新增遥测字段 |
| 5.6 | `.env.example` **未加**该变量 | `git diff` 对 `.env.example` 为空 ⇒ 连占位值也不落盘 |

### 六、既有链路零回归（EC-03 证据面）

| # | 检查 | 结果 |
| --- | --- | --- |
| 6.1 | `tests/api` + `tests/contracts` | **924 passed / 73 skipped / 0 failed**（含 **OpenAPI 快照** ⇒ 中间件式认证**未**引起 schema 漂移，未触发重生成） |
| 6.2 | `tests/architecture/python`（canonical `uv run --frozen --no-sync`） | **175 passed**（含 runbook 同源族 / 依赖边界 / 出口守卫） |
| 6.3 | **全量 m0**（独占、仓库 `.venv`、DSN 固化、`--keep-going`） | 终态行 **`PASS: profile=m0; 23 deterministic checks`**；`PASS [` = **24**；`python/tests` = **4538 passed / 20 skipped**；`FAILED`/`ERROR` 零命中 |
| 6.4 | 前端面 | `apps/web/**` **零改动**（`git status` 无该路径）⇒ 前端行为不可能是本轮引入 |
| 6.5 | `stub e2e` / `live e2e`（认证关闭） | **98 passed** / **53 passed**、退出码均 0 —— 与 GOAL-018 基线**计数完全一致**（见 W-1：实施方同轮实跑，非独立复检证据） |
| 6.6 | 认证关闭 = 默认 | 环境变量未设时 `enabled=False`，中间件**直接透传**；CI / live 夹具不设该变量 ⇒ 默认链路不变 |

### 七、本轮内被 m0 抓到的两处真红（已修，非"一次通过"）

| # | 红面 | 根因 | 处置 |
| --- | --- | --- | --- |
| 7.1 | `python/format-check` | 新测试文件 `tests/api/test_principal_auth.py` **未**被纳入我先前的 `ruff format --check` 文件清单（3 处该折叠的签名/调用） | 按 ruff 输出逐处折叠；复跑 `ruff format --check services packages tests adapters` = **1032 files already formatted** |
| 7.2 | `python/tests::test_python_source_size_limits[services\api\app.py]` | 新增 6 行把 **`create_app` 从 47 行推到 53 行**，越过 **50 行函数门禁**（`app.py` 此前只剩 1 行余量） | 抽出 `_install_write_face_auth(app)`，`create_app` 回到 48 行；规模门禁 **1032 passed** |

⇒ 这两处**只有跑全量 m0 才会红**（定向套件当时全绿）——再次印证「本地不绿不得 push」的判据必须是**全量门**。

## 警告（W）

- **W-1｜`stub e2e` / `live e2e` 由实施方在同轮实跑，且与本复检的其余项**不同源**：**
  本复检正文（第三节）的结论来自单元/集成判据与全量 m0；两条 e2e 是在本复检起草**之后**
  跑完的（`scratch/goal019-c1-e2e-stub.log` = **98 passed (5.2m)**、`STUB_EXIT=0`；
  `scratch/goal019-c1-e2e-live.log` = **53 passed (1.1m)**、`LIVE_EXIT=0`）。
  计数与 GOAL-018 的基线**完全一致**（98 / 53），且 `apps/web/**` **零改动**
  ⇒ 支持 EC-03 的「认证关闭时行为不变」，但**它是实施方-run 证据**，不是独立复检证据。
- **W-2｜EC-04（四处文档同源）本轮未做**：`IDENTITY_AND_ACCESS.md` / `THREAT_MODEL.md` 第 6 节 /
  `CONTROL_PLANE_API.md` / `LIVE_MODEL_RUNBOOK.md` **仍是旧口径**（写面认证已在树上生效，
  但文档尚未登记）⇒ **文档与实现此刻有落差**；GOAL-019 的 EC-04 **仍未完成**。
- **W-3｜EC-05（收口）本轮未做**：两树复检 / CI 台账到终态 / 残余逐条**尚未**成文；
  GOAL-019 仍 **ACTIVE**。
- **W-4｜单一共享 token ⇒ 单一主体**：`kind` 固定 `SERVICE`，**不做**调用方自报。
  ⇒ 本轮的「主体」能回答「是不是经过认证的调用方」，**不能**回答「是哪一个调用方」。
  **不得**把它读成 per-caller 身份；逐调用方身份需要逐调用方凭据（未来工作 / M18 面）。
- **W-5｜主体只以字符串形态落在事件 envelope 里**：`outbox_events.envelope_json.actor`
  **没有**独立列 / 外键 / 约束 ⇒ 没有 schema 级力量阻止将来某处再写任意 actor 字符串。
  本轮的约束是**代码级**（读点回退 + 单元判据），**不是**数据库级。
- **W-6｜`eventing` 的读点回退是"就近"防线**：`_event_actor` 只覆盖经
  `publish_event` 的事件；直接构造 `EventEnvelope` 的其它路径（如 outbox relay 的
  `system:workflow-engine`）**不经过**它 —— 那是有意保留（系统自身动作）。
- **W-7｜`app.py` 余量紧张**：`create_app` 抽助手后才合规；该文件后续再加装配行会**再次**
  撞 50 行门禁（`app.py` 已 327 行，>300 软阈值）。
- **W-8｜未做真实部署面验证**：认证只在**进程内**生效；反代 / TLS / 多副本场景
  **未验证**（也不在本 GOAL 范围）。
- **W-9｜`R-M1` 未收口**：Mimosa 钩子在 commit/push 时报告 `scanner_enobufs` 未得完整结论
  ⇒ **不得**因本轮新增认证面而宣称项目安全。

## 结论

**PASS_WITH_WARNINGS**。PLAN-190 的两条主判据（**认证三态** / **主体落 canonical**）均有
**实跑证据 + 成对反证 + 三次按压**；`Idempotency-Key` **逐字节未动**；凭据纪律四条反证全零命中；
**全量 m0 = 23/23**；两条 e2e 与基线计数一致。本轮内 m0 抓到并修掉两处真红
（其中一处正是 50 行函数门禁）。
**EC-04 / EC-05 仍未做**（W-2 / W-3）⇒ GOAL-019 维持 **ACTIVE**。
