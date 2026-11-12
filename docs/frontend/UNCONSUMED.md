# 未消费的后端路由登记表

（**如实登记**那些后端有、前端没有消费者的路由。目的不是消灭这份表，而是让「暂不暴露」
成为一个**可审计的决定**，而不是一个没人查的空白。）

**判据**（`apps/web/tests/unit/backend-route-coverage.test.ts` +
`unconsumed-registry.test.ts`）：

1. `docs/api/openapi.m13.json` 里的每条路由**要么**在前端有请求形状同形的消费者，
   **要么**在本表里有一行；
2. 本表每行的**理由必须非空且非占位符**（`-` / `TODO` / `TBD` / `待补` 都算空）；
3. 本表每行的路径必须**真的**存在于 OpenAPI（写错路径 = 这条登记保护不到任何东西）；
4. 同一条路由不得登记两次。

**白名单不是刷覆盖率数字的工具**。往这里加一行之前，先确认它真的不该有 UI：
能接线的就接线（那是本文件存在的意义的反面）。本轮已经把 7 条接上了消费者，
剩下的每一条都写在下面并给出理由。

## 登记表

| 方法 | 路径 | 理由 |
| --- | --- | --- |
| GET | /health | 进程存活探针（`{"status": "ok"}`），供部署/编排系统与 CI 健康检查使用；控制台没有消费它的场景 —— 界面上的「系统可用性」读的是 `GET /llm-endpoints/{id}/health`（端点级，已接线），不是进程级探针。给它加 UI 等于把运维探针做成用户按钮。 |
| POST | /memory/{memory_id}/conflicts/{other_id}/resolve | **证据矛盾的人工裁决面**（GOAL-20261111-110 EC-02）：缺省返回 `REQUIRE_HUMAN` 判词、**不落账**；只有显式声明策略或带 `resolved_by` 时才写。控制台**故意不接**——「谁来裁决这条矛盾」是治理动作（当前没有审批工作流、也没有多主体身份），把按钮做进记忆页等于给「自动消解」开一个可点入口。GOAL 的 `U-2` 已登记：接前端时要与审批面一起设计。 |

## 已经接上消费者的（本轮的处置，留档）

这 7 条此前零消费者，**本轮接了线**，因此**不在**上表里：

| 路由 | 接法 |
| --- | --- |
| `GET /runs/{id}/reviews` | `inspectionClient.reviews()` + `ReviewPanelSection`（RunPanel）：逐条判词原文 + `reviewed_by` / `reviewer_model` / `reviewed_at`。**前端不做聚合** —— `aggregate_panel` 是领域逻辑。 |
| `PUT /projects/{id}/direction` | `projectsClient.setDirection()` + `ProjectDirectionEditor`（ProjectsPage 每行）：空输入 = 清除（发 `null`）。 |
| `POST` / `GET` `/projects/{id}/programs`、`GET /programs/{id}`、`POST /programs/{id}/advance` | 新 `programsClient.ts` + `ProgramsSection`（ProjectsPage）：列表 + 「推进一轮」按钮，按钮显示服务端返回的决定本身。**只做最小读面**，完整程序页不在本轮。 |

另有 3 条**只加了 client 方法但 UI 仍不消费** —— 它们是本轮新写的，等于「加了个方法然后
不住何地方调它」。这类**必须**登记，否则就是死代码：

| 方法 | 路径 | 理由 |
| --- | --- | --- |
| GET | /library/{resource_id} | 库页面用列表 + 行内字段已够（`libraryClient.list` 带全部展示字段），没有单独的详情页需求。`libraryClient.detail()` 已备好，等真的出现「打开单件资源」交互时直接用。 |
| GET | /projects/{project_id}/memory/validity | 时效读面要**调用方给时点**（`at`，不读挂钟）。记忆页目前只展示列表；「在某时点这条记忆是否还有效」是复核工作流的一部分，尚未有该交互。`memoryClient.validity(at)` 已备好。 |
| POST | /tasks/{task_id}/retry | 服务端能力，前端暂不暴露：现有 UI 只有 run 级 pause/resume/cancel。「挑单个 task 重试」需要先有任务级故障处置交互（哪个任务失败、为什么、重试会不会重复副作用），本轮不做。`runClient.retryTask()` 已备好。 |
