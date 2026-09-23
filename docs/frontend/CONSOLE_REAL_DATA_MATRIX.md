# CONSOLE_REAL_DATA_MATRIX — 逐页真实数据验收矩阵（GOAL-20260923-013 EC-01）

本表把 `apps/web/src/navigation/pageSupport.ts` 里 **19 条 `partial` + 1 条 `gap`** 共 **20 条**
路由逐条判定，每条给一个**终态二选一**：

- **收敛**——该页的**呈现读面**全部由已交付端点服务，且有**页面级 live e2e 用例**为证
  （用例必须 `goto` 该路由并对 DOM 断言，不只是 `page.request` 打读面），
  且 `pageSupport` 的降级注记按 `CONSOLE_PAGE_MAP.md` 自身的等级定义相应收敛。
- **保持**——该页**确有后端读面缺口**（点名缺哪条 API / 哪个字段 / 哪张读面），
  `pageSupport` 与 `CONSOLE_PAGE_MAP.md` 的注记与该缺口事实逐条一致，并写明**为什么现在不做**。

**零条待定**；**(a)/(b) 不混写**（同一条不会既记收敛又记缺口）。判据见
`apps/web/tests/unit/console-real-data-matrix.test.ts`（离线、零出网）。

## 缺口记法（机器可查）

每条**保持**行的「点名缺口」列必须至少含一个以下 token，且必须同时含一段
**「」引文**——该引文须**逐字**出现在 `apps/web/src/navigation/pageSupport.ts`
或 `docs/frontend/CONSOLE_PAGE_MAP.md` 里（矩阵不得自造缺口事实）：

| token | 含义 | 附加要求 |
| --- | --- | --- |
| `API:<以 / 开头的路径>` | 已存在的读面路径被限制/缺字段 | — |
| `FIELD:<字段名>` | 读面缺某个字段，页面因此只能降级呈现 | — |
| `SURFACE:<读面名>` | 读面整体尚不存在（无路径可点） | 须含 `不做的原因：` |
| `DESIGN:<slug>` | 该页按设计不接读面（仅 `ops/matrix` 允许，见 EC-04） | 须含 `不做的原因：` |

每条**收敛**行的「点名缺口」列必须含 `LIVE:<spec 文件名>`；该文件须存在，且其 suite 名
须在 `apps/web/tests/e2e/live-specs.ts` 的 `LIVE_SUITES` 白名单内。

## 逐页矩阵（20 条）

| # | 路由 | 原等级 | 终态 | 体现状（读面） | 点名缺口 / 证据 | 为什么现在不做 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `plan/overview` | partial | **收敛** | `GET /runs/{id}`、`/tasks`、`/claims`、`/usage` 四条读面全部已交付，页面呈现的每张指标卡都由读面取值（无禁用操作） | `LIVE:live-plan-overview.spec.ts`；收敛后 `pageSupport` 等级 = `full`（依 `CONSOLE_PAGE_MAP.md` 的等级定义：FULL＝数据与操作真实、无禁用操作） | —（已收敛；注记「无独立 overview API」是**聚合口径**、不构成缺口，故其**文字逐字未改**——设计基线 `design-outlines.json` 会渲染这段文字，改文字等于改设计基线，而本次是等级口径收敛、不是设计变更。page map 里「原型 manifest 摘要字段（objectives/autonomy）无对应 DTO」一行是**原型设计偏差**：实现的页面根本没有消费这两字段的代码路径 ⇒ 已就地改写为「已实现面的一部分」，不留假缺口） |
| 2 | `portfolio/projects` | partial | **保持** | `GET /projects` + `POST`/`PATCH`/`DELETE /projects/{id}` 均已交付；页面无伪造数据 | 「agents/memory/experiments 数据面仍单项目共享，租户隔离属 M18 deferred」；`SURFACE:多租户数据面隔离`（不做的原因：M18 已登记 deferred） | 租户隔离是 M18 里程碑范围，改它会动 Canonical State 边界 ⇒ 需拍板，本循环不做 |
| 3 | `portfolio/experiments` | partial | **保持** | `GET /runs/{id}/experiments`、`/projects/{id}/experiments`、`/experiment-plans`、`/projects/{id}/experiment-queue` 均已交付 | 「复现执行与日历/矩阵视图无 API，不伪装」；`SURFACE:复现执行与日历/矩阵视图`（不做的原因：G14 未交付面继续标注） | 复现执行需要新的执行路径与预算语义，属里程碑扩建，不在本目标范围 |
| 4 | `portfolio/compare` | partial | **保持** | `GET /projects/{id}/runs` + 每条 run 的 `/runs/{id}/usage`、`/runs/{id}/experiments` 均已交付 | 「仅比较已返回指标；不可比语义保留」；`FIELD:可比性（comparability）无后端承载` | 可比性是研究语义判定（模型漂移/协议差异），需先定契约再加工，不在本目标范围 |
| 5 | `run/timeline` | partial | **保持** | `GET /runs/{id}`、`/tasks`、`/events`（含 SSE）均已交付 | 「无抢占式中断；跨进程暂停上下文不持久化」；`FIELD:抢占式中断`；`FIELD:跨进程暂停上下文` | 抢占式中断与跨进程暂停上下文是运行时执行体能力，属里程碑扩建 |
| 6 | `library/prompts` | partial | **保持** | `GET /projects/{id}/library?kind=prompt` + `POST /projects/{id}/library` 已交付 | 「版本树与 A-B 无 API，不伪造」；`SURFACE:版本树与 A-B`（不做的原因：G7b 已交付面之外的目录能力） | 版本树/A-B 需要新的库模型，属里程碑扩建 |
| 7 | `library/datasets` | partial | **保持** | `GET /projects/{id}/library?kind=dataset` 已交付 | 「上传与字段 schema 无 API」；`SURFACE:上传与字段 schema`（不做的原因：G7b 已交付面之外的目录能力） | 上传与 schema 需要制品存储契约，属里程碑扩建 |
| 8 | `library/notebooks` | partial | **保持** | `GET /projects/{id}/library?kind=notebook` 已交付 | 「单元格编辑与执行无 API」；`SURFACE:单元格编辑与执行`（不做的原因：G7b 已交付面之外的目录能力） | 单元格执行需要新的执行体与沙箱面，属里程碑扩建 |
| 9 | `library/lineage` | partial | **保持** | `GET /projects/{id}/lineage` 已交付（合并图 + 未连边库资源清单） | 「数据集/提示词与 Run 的引用关系无记录面」；`API:/projects/{project_id}/lineage` 的 `reference_recording=NOT_RECORDED` | 引用记录面需要在写入侧记关系，会动 Canonical State 的写入路径 ⇒ 需拍板 |
| 10 | `insights/reports` | partial | **保持** | `GET /runs/{id}/deliverable`（M12 持久化交付物）已交付，只读视图完整 | 「报告生成/编辑/PDF/发布无 API——生成动作禁用」；`SURFACE:报告生成/编辑/PDF/发布`（不做的原因：G7a 只读视图已交付，写面无 API） | 报告生成需要新的产物管线与发布面，属里程碑扩建 |
| 11 | `insights/cost-analytics` | partial | **保持** | `GET /runs/{id}/cost`、`GET /cost/daily`、`GET /projects/{id}/cost-forecast` 均已交付 | 「无按资源维度分解的预测与置信区间」；`FIELD:按资源维度分解`；`FIELD:置信区间` | 资源维度分解需要按模型的计价归集口径，置信区间需要统计方法定案 ⇒ 需先定契约 |
| 12 | `ops/schedules` | partial | **保持** | `GET /ops/schedules` + `POST /ops/schedules`、`PATCH /ops/schedules/{name}`、`POST /ops/schedules/{name}/trigger` 已交付 | 「缺：不能新增执行路径（只能绑定既有 job 词表）、无删除/归档、无 cron 表达式与日历视图」；`FIELD:cron 表达式`；`SURFACE:删除/归档`（不做的原因：执行体仍是既有守护线程） | 新增执行路径会绕过既有调度执行体，需拍板 |
| 13 | `ops/integrations` | partial | **保持** | `GET /tool-providers`、`GET/POST /tool-provider-registrations`、`GET /tool-packs` + install/approve-update/revoke 均已交付 | 「缺：provider 凭据绑定、健康复核的 schema digest 漂移比对」；`FIELD:provider 凭据绑定`；`FIELD:schema digest 漂移比对` | 凭据绑定触及独立凭据域，schema 漂移比对需先定 schema 契约 ⇒ 需拍板 |
| 14 | `ops/data-health` | partial | **保持** | `GET /projects/{id}/ops/data-health` 已交付（端点健康计数 / dataset 计数 / artifact 抽样校验） | 「无聚合质量报告 API」；`SURFACE:聚合质量报告`（不做的原因：G7 只读投影已交付，聚合报告未建） | 聚合质量报告需要质量口径定案，属里程碑扩建 |
| 15 | `ops/matrix` | gap | **保持** | 该页**按设计不消费任何读面**——呈现加载/空/错误/权限/未知等 UI 组件状态 | 「界面状态说明页（非实时运维状态）」；`DESIGN:not-a-live-ops-surface`（不做的原因：它是界面状态说明页，不是实时运维状态面；实时运维状态各有读面与页面 —— `#/ops/observability`、`#/ops/compute` 均 FULL、`#/ops/data-health` 为 partial 但读面已交付，本页只陈述组件状态词表，见 `CONSOLE_PAGE_MAP.md` 同小节） | 这是**设计口径**而非待建功能：四处同源（`pageSupport.reason` / page map 小节 / 本行 / 页面可见文案），页面判据 `apps/web/tests/e2e/matrix-states.spec.ts`（EC-04 处置） |
| 16 | `govern/budget` | partial | **保持** | `GET /runs/{id}/usage`、`/runs/{id}/cost-forecast`、`/projects/{id}/cost-forecast` 均已交付；`POST /runs/{id}/interventions` 预算调整已交付 | 「预测只覆盖已预留额度（未预留开销不外推）」；`FIELD:未预留开销外推` | 未预留开销的外推需要改变预算账本的预留语义 ⇒ 需拍板 |
| 17 | `govern/audit` | partial | **保持** | `GET /runs/{id}/events`、`/runs/{id}/export`、`GET /policy/capabilities`、`GET/POST/DELETE /projects/{id}/memory`、`/memory/{id}` 均已交付 | 「无持久化 pending 提案，门链直提交」；`SURFACE:持久化 pending 提案与两阶段 decide`（不做的原因：§8 门链直提交是既定设计） | 两阶段 decide 与既定门链设计冲突，需拍板 |
| 18 | `settings/settings` | partial | **保持** | `GET /projects/{id}/settings`、`GET /team-templates`、`PUT /projects/{id}/settings` 已交付 | 「无账户/身份/Billing/平台 API Keys API」；`SURFACE:账户/身份/Billing/平台 API Keys`（不做的原因：M18/M19 已登记 deferred） | 账户与计费属 M18/M19 里程碑范围 |
| 19 | `notifications/notifications` | partial | **保持** | `GET /notifications` + `POST /notifications/{event_id}/read` 已交付（事件投影 + 已读持久化） | 「无实时推送，数量只来自当前页」；`SURFACE:实时推送通道`（不做的原因：G3 事件投影已交付，无推送通道） | 推送通道需要长连接与投递语义，属里程碑扩建 |
| 20 | `command-center/command-center` | partial | **保持** | `GET /projects/{id}/runs`、`GET /cluster/workers`、`GET /runs/{id}/telemetry`、`/claims`、`/usage`、`/experiments`、`/events` 均已交付 | 「复用真实查询；跨项目/预测/全球节点不可用」；`SURFACE:跨项目聚合与全球节点`（不做的原因：页面已把 `ALERTS FEED` 与 `MODEL ACTIVITY` 两段标注为 API GAP） | 跨项目聚合需要多租户读面（同第 2 条的 M18 前提），全球节点需要跨地域拓扑面 |

## 汇总

- **已收敛 1 / 保持 19 / 待定 0**（共 20）。
- 唯一收敛项是 `plan/overview`：四条读面全部已交付、页面无禁用操作、且已有页面级 live 用例
  （`live-plan-overview.spec.ts`，含成对反证）。它的 `partial` 在事实层面是**旧注记**
  （`CONSOLE_PAGE_MAP.md` 的等级定义下 `FULL`＝数据与操作真实、无禁用操作），故按注记与事实一致
  的要求收敛为 `full`。
- 其余 19 条的 `partial`/`gap` **不是旧注记**：每条的 `pageSupport.reason`（或 page map 的
  「剩余受限」段）都点名了一个仍然存在的后端读面缺口，逐条抄录在上表「点名缺口」列，
  并写明为什么现在不做。

## 与其它权威面的关系

- `apps/web/src/navigation/pageSupport.ts` —— 等级与注记的**代码**权威；本表收敛项落回该文件。
- `docs/frontend/CONSOLE_PAGE_MAP.md` —— 逐页设计与**缺口总登记**（G1…G16）；本表引文取自该文件与其
  「剩余受限」段。
- `apps/web/src/navigation/presentationPolicy.ts` —— 消费 `level`：`gap` ⇒ `example`，否则 `live`。
  第 15 条（`ops/matrix`）是当前唯一会落到 `example` 的页，其口径由 EC-04 单独处置。
