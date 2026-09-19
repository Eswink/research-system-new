---
id: RECHECK-20260919-110
plan_id: PLAN-20260919-110
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-19
completed_at: 2026-09-19
reviewer: root-agent-goal-007-cycle4
baseline_ref: 7039424
checked_head: WORKTREE
---

# RECHECK-20260919-110 — 诚实披露：执行体性质与运行时指纹（GOAL-20260919-007 cycle 4 = EC-04）

## 检查范围

EC-04 的可判事实逐条对表（每条都要**实跑**证据，不采信"代码里看着对"）：

| EC-04 要求 | 交付 | 判据（可复核） |
| --- | --- | --- |
| 披露 = **读面字段 + 页面渲染分支**（只在 `types.ts` 里存在不算） | `services/api/run_execution_view.py`（新）+ `RunDetailDto.execution` + `RunPanel` 的 `run-execution-backend` / `run-runtime-fingerprint` 两行 | stub e2e 四态用例 + live e2e 同值用例，**都断言 DOM**（不是断言 JSON） |
| 事实来源只有一个（canonical 事件，不另存一份） | 读面经 `RunProjection.events(run_id)` 筛 `manifest.frozen`，与 `GET /runs/{id}/events` **同一端口同一实现** | 反证 F-B：把 payload 读成空 ⇒ live 用例在**读面**就红 |
| 未冻结 ≠ 未声明 ≠ 具体执行体 | 四态（openhands / fake / 已冻结未声明 / 未冻结）在页面上互不相同 | stub 用例的 `new Set(seen).size == CASES.length` |
| 指纹只报**状态**，不冒充指纹值 | `status` + `reason` 同显；`NOT_VERIFIED · <reason>` | stub 用例的 `toHaveText(/^NOT_VERIFIED · /)` + live 用例的 `NOT_VERIFIED` |
| 反证：去掉渲染分支 ⇒ 对应 e2e 红 | 摘掉两行后跑同一套 | 见「反证与实测」F-A |
| 页面改动走既有设计基线流程，且**如实记录覆盖结论** | 第 34 条基线条目 + win32/linux 两张像素 + 跨平台结构签名 | 见「覆盖结论：基线原本看不见这条分支」 |
| 过时/不实的披露声明按事实收敛 | 6 份文档 + 1 处代码注释 + 1 处测试 docstring | 逐处列出（见「文案收敛清单」） |
| 默认门离线可跑 | 全部断言都在本机 Fake/SQLite 路径上；live 套件是本机 uvicorn+fake ports | 无网络、无凭据 |

## 检查结果

### 断点原本在哪：披露声明存在，承载它的**页面分支**不存在

`M13_R1_COMPLETION_RECORD.md:164` 声称 "Run Control 含
`Agent 研究执行体为受控 Fake Runtime（非真实 LLM 推理）` 披露"。实测：该字符串只出现在
协议注释与 `demo_session_output()` 的 payload 文案里，`apps/web/src` **零引用**——
运行页没有任何分支承载它。也就是说，这是一条**声称已披露、实际不可见**的声明
（GOAL AGENTS.md §4 要消灭的正是这种漂移）。本 PLAN 的靶子因此不是"再加一句文案"，
而是让"哪个执行体跑的"成为**读面字段 + 页面分支**。

### 两条读面同源（不是第二份真相）

```text
冻结的 manifest.frozen（canonical outbox 事件，含 execution_backend / runtime_fingerprint）
  → RunProjection.events(run_id)（既有端口，与 GET /runs/{id}/events 同一条实现）
  → services/api/run_execution_view.run_execution_dto
  → RunDetailDto.execution
  → RunPanel 的两行
```

manifest 实体不落库（run 行只有 digest）是本仓库的既有事实，因此读面**只能**回读事件；
本 PLAN 没有新增迁移、没有新增存储字段、没有第二条取数路径。SQLite 与 PG 两个
`RunProjection` 实现的 `events()` 都经 publisher 的 `published` 取 **outbox 表**内容
（`@property published` 查 `outbox_events`），所以冻结事件在进程重启后仍可读到——
这一点本轮**读代码确认**，不是假设。

### 覆盖结论：基线原本看不见这条分支（实测，不是推断）

`#/run/timeline` 的既有设计基线**不选 run**（`runs-empty`），而披露行只在选中 run 时
渲染 ⇒ 加行后**结构签名不变**（实测：先只加行、跑结构签名，结果与旧基线逐字节相同）。
若就此收工，"披露行是否被渲染"这件事在像素/结构门上是**不可见**的——门是绿的，但它
没在看你。处置：新增第 34 条基线条目 `run-timeline-substrate`
（`#/run/timeline?run=substrate-openhands`），并生成 win32 与 linux 两张像素基线；
跨平台结构签名复核 34/34、零漂移（`bash scratch/verify_linux_outlines.sh`）。
规范路由仍是 `registry.ts` 的 33 条，多出来的是**同页的选中 run 变体**——这一区分已写进
`docs/frontend/CONSOLE_DELIVERY.md` 的更正说明（`design-fidelity.spec.ts` 头注释同步）。

### 四态语义（页面必须分得开的四件事）

| 读面取值 | 页面（中文 / 英文） | 含义 |
| --- | --- | --- |
| `execution.execution_backend = "openhands"` | `openhands` | 冻结时选择面给出的真实执行体 |
| `execution.execution_backend = "fake"` | `fake` | 受控 demo 执行体 |
| `execution_backend = null`（冻结了但没声明） | 未声明 / UNDECLARED | 冻结时**没声明**，不得读成某个执行体 |
| `execution = null`（未冻结） | 未冻结 / NOT FROZEN | 这次运行还没有冻结快照 |

指纹同理：冻结 payload 里的**空 dict**（`{}`）是"冻结时未声明该面"⇒ 读面给 `None` ⇒
页面 `未声明`；不把 `{}` 当成一条记录（否则读面要么崩、要么编出一个空状态）。

### 事实纠正：live 夹具的 run id 撞了别人的"不存在的 run"

live 套件首跑 1 红：`live-workspace-snapshots.spec.ts:108` 断言
`/api/runs/22222222-…/workspace-snapshots` 返回 404（"未知 run 如实 404"），而本轮
夹具恰好把**同一个 UUID** 声明成了自己的受控 run ⇒ 404 变 200。这不是既有用例的错，
是**新夹具占用了别人当哨兵的取值**。已改用全仓库未被使用的 UUID
（`44444444-4444-4444-8444-444444444444`），并在 Python 常量与 TS 常量两处写明约束；
复跑 live 套件 39 passed。

## 反证与实测

| # | 注入 | 结果 |
| --- | --- | --- |
| F-A | 摘掉 `RunPanel` 的两行渲染（保留 DTO 与 fixtures） | **红**：stub 两条用例都失败（`run-execution-backend` / `run-runtime-fingerprint` "element(s) not found"）⇒ 用例真的钉在**页面分支**上，不是钉在 DTO 上 |
| F-B | `run_execution_view._frozen_payload` 恒返回 `{}`（假装没读到冻结事件） | **红**：live 用例在读面即失败（`declared.execution.execution_backend` 是 `undefined`，期望 `"openhands"`）⇒ 读面**真的**从冻结事件取值，不是返回常量 |
| F-C | （非注入，实测发现）夹具 UUID 与既有"未知 run"哨兵相同 | **红**：`live-workspace-snapshots` 404 断言变 200；已修并复跑绿 |

F-A / F-B 的注入均已复原；`git status --short` 只剩预期改动。

## Warnings（不阻断，如实登记）

- **W-1**：执行体读面**只在详情路径**（`GET /runs/{id}` 与启动/取消后的详情返回）。
  列表路径（`GET /projects/{id}/runs`）不带该字段：逐 run 回读冻结事件会变成 N+1。
  这是**显式边界**（`_detail_dto` 的 `with_execution` 参数 + 文档写明），不是静默省略；
  代价是运行历史列表上无法一眼分辨执行体。
- **W-2**：今天可以披露的指纹事实只有 `NOT_VERIFIED`（判据是"这次 run 没收集到 probe
  事实"）。`VERIFIED` 分支的**渲染路径未被任何用例走过**——没有真实 probe 事实可造。
  读面因此只报 `status` + `reason`，不变量冒充指纹值；等真实 probe 接线进冻结 payload
  时才可能有用例覆盖。
- **W-3**：live e2e 的"第二种执行体"是夹具**声明**的（经生产自己的 `frozen_payload` +
  `publish_event` 发布），不是真跑过一次 openhands 会话。live 用例判的是"页面 == 读面"，
  不是"真的跑过真实执行体"——后者的离线全链在 EC-03 的
  `tests/e2e/test_ec03_real_runtime_offline_chain.py`，两者互补，不能互相顶替。
- **W-4**：`RunProjection.events(run_id)` 的实现是"取 outbox 全量再按 run 过滤"
  （SQLite 的 `published` 属性 `SELECT … FROM outbox_events` 无 run_id 谓词）。
  详情路径每个 run 一次全表扫描；事件表很大时这是可测量的开销。既有 events 读面
  （SSE/replay）是同一形态，本 PLAN 没有引入新形状，但也没有改善它。
- **W-5**：`_frozen_payload` 取**第一条** `manifest.frozen`。运行中换 manifest 的路径
  （Manifest Revision / Fork）在今日实现里不重复发布该事件类型，所以当前唯一；若将来
  允许重复发布，这里必须改成"按 revision 取最新"，否则读面会停在第一次冻结。
- **W-6**：`docs/frontend/CONSOLE_DELIVERY.md` 与
  `docs/frontend/CONSOLE_REFERENCE_RECONSTRUCTION_DELIVERY.md` 里的 "33 路由基线"
  是**历史交付记录**的原文。前者已加日期化更正说明（覆盖面变更）；后者按历史记录保留
  不改（它描述的是当轮交付时的状态）。两处都不是当前事实的唯一来源——当前事实在
  `design-fidelity.spec.ts` 与 `design-outlines.json`。
- **W-7**：夹具的 UUID 约束（不得与别处"不存在的 run"哨兵撞车）只写在注释里，**没有**
  机械门禁。本轮的碰撞是被 live 套件抓到的（这算门在起作用），但它依赖用例恰好跑了那条
  404 断言。

## 文案收敛清单（WP-E）

| 位置 | 原口径 | 现口径 |
| --- | --- | --- |
| `docs/roadmap/M13_R1_COMPLETION_RECORD.md` | "Run Control 含 …披露" | 追加日期化**更正**：该字符串当时只存在于协议注释与 Fake 输出文案，页面无渲染分支；EC-04 起改走读面字段 + 页面分支 |
| `docs/architecture/AGENT_RUNTIME.md` | "读面只有事件 payload" | 两条读面可判 + 列表路径 N+1 边界 |
| `docs/architecture/EVENT_MODEL.md` | payload "带三项冻结引用" | 补齐 payload 实际键（含 `execution_backend` / `runtime_fingerprint`） |
| `docs/architecture/DOMAIN_MODEL.md` | `execution_backend` "保持 None/不伪填充" | 与 `manifest.py` 现状一致：有来源（preflight context → 冻结），未声明仍有其语义 |
| `docs/api/CONTROL_PLANE_API.md` | 无 `execution` 说明 | 新增 `execution` 读面（两个 `null` 的区分、同源规则、列表路径边界、console 渲染位置） |
| `docs/frontend/CONSOLE_PAGE_MAP.md` | 运行时间线只写重建就绪面板 | 增补执行基质两行（未声明 vs 未冻结分开说；指纹只报状态） |
| `packages/application/run_orchestration/eventing.py` | 注释称 "零 DTO/路由/OpenAPI 变化" | 改为：EC-01 加键不动 DTO；EC-04 的读面回读的仍是这份 payload |
| `tests/api/test_runtime_selection_surface.py` | 同上（docstring） | 同上（并点名 `run_execution_view.py`） |

## 结论

EC-04 **PASS_WITH_WARNINGS**：披露从"声称存在"变成"读面字段 + 页面分支"，四态在页面上
互不相同，stub 与 live 各一条用例钉在 DOM 上，两处反证各自可复现；事实来源仍是唯一的
canonical 事件；基线覆盖缺口（不选 run ⇒ 看不见新分支）被实测发现并以第 34 条基线条目
补上；6 份文档 + 代码注释 + 测试 docstring 的口径按事实收敛（含一条**更正**：M13 记录里
那条披露当时并不存在）。W-1…W-7 是如实登记的射程边界与残余风险，不阻断。

## 门禁

| 门 | 结果 |
| --- | --- |
| 尺寸门（450 行 / 50 行函数） | **948 passed**（首跑红两处，均已拆分：`console_api_app.py::_with_substrate_disclosure` 62 行 → `_bind_disclosure_selection` + `_declare_substrate_run`；`RunPanel.tsx::RunIdentity` 57 行 → `RunIdentityFacts`。**首跑红如实记录**） |
| `ruff check` / `ruff format --check` | 绿（948 files already formatted） |
| `mypy` | **938 source files, no issues**（首跑红 1 处：`deps.projection` 可空未判 → 加守卫） |
| 受影响套件 | `tests/api` + `tests/contracts` + `tests/architecture` + `tests/tooling` **2049 passed / 2 skipped** |
| web 六门 | lint 0 problems；typecheck 绿；unit **76 passed**；build 绿；stub e2e **87 passed**；live e2e **39 passed** |
| 设计基线 | `design-fidelity` **2 passed**（34 条）；win32 像素本机生成；linux 像素容器生成；跨平台结构签名 **34/34 零漂移** |
| 根 eslint（覆盖 `apps/web/tests`） | 0 error（1 条既有 soft-limit warning，非本轮文件） |
| m0（23 项） | **23/23 PASS** |
