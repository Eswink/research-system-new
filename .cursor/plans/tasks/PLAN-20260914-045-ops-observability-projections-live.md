---
id: PLAN-20260914-045
slug: ops-observability-projections-live
title: alerts/incidents/schedules/data-health 只读运维投影 + 页面 live（GOAL-001 cycle 5：EC-03 第二批）
status: DONE
created_at: 2026-09-14
updated_at: 2026-09-14
parent_goal: GOAL-20260912-001
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260912-001 cycle 5（/goal 持续循环迭代指令）；范围=EC-03 第二批 alerts/incidents/schedules/data-health"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260914-045-ops-observability-projections-live.md
memory_entries: []
---

<!-- 无可复用事实：只读投影模式与基线再生的坑均已记录于 MEM-20260913-022
     （worktree overlay + 强制重写），本 cycle 无新增机械门禁事实。 -->

# PLAN-20260914-045 — 运维只读投影（alerts/incidents/schedules/data-health）翻 live（cycle 5）

## 目标

为 `#/ops/alerts`、`#/ops/incidents`、`#/ops/schedules`、`#/ops/data-health` 四页
建立**只读运维投影**，数据全部来自既有真实状态（RunStore / worker registry /
endpoint health / artifact verify / 进程内 scheduler 配置）：

- **alerts**：由真实信号派生告警项（FAILED run、端点 DEGRADED/OPEN_CIRCUIT、
  worker 离线）。只读收件箱；规则 CRUD 仍禁用。
- **incidents**：FAILED run 的事故候选列表 + 诚实标注「无 declare/assign/close
  处置工作流」（失败 Run **不**自动变成已登记事故）。
- **schedules**：进程内 4 个守护 scheduler（LeaseRecovery/OutboxRelay/Retention/
  WorkerReaper）的**配置事实**（interval/purpose/enabled）+ 诚实标注
  「无用户可见调度 API」。
- **data-health**：聚合公开事实（端点健康计数 + dataset 目录条目数 + 抽样 artifact
  digest 校验结果）+ 诚实标注「无聚合质量报告 API」。

## 为什么不做「最小持久域」

EC-03 原文写「最小域（domain 实体 + store + API）」。对前三个库目录页（PLAN-044）
该式成立（用户自有的目录元数据）。但这四页若照搬，会造出一个**不被消费的持久
实体**——例如「已注册的定时任务」在进程内 scheduler 并不读取，启用后永不触发，
正是本仓明令禁止的「伪装实现」。故本 cycle 采用**派生只读投影**：domain 模块只放
视图类型（无持久化），数据来自既有真实状态，能力边界逐条如实标注。这不降低
EC-03 的验收（四页均 consume 真实后端能力、不再强制 example），且不产生假真相。

## 范围

- 包含：
  - WP-A 视图域：`packages/domain/ops_view.py`（AlertItem/IncidentItem/
    ScheduleEntry/DataHealthMetric 冻结 dataclass + 有界校验）。
  - WP-B API：`services/api/routers/ops_view.py`
    （`GET /ops/alerts`、`GET /ops/incidents`、`GET /ops/schedules`、
    `GET /ops/data-health`；项目作用域过滤；store 缺失诚实降级）；
    DTO + app 注册。
  - WP-C 前端：`opsViewClient` + 四页消费真实端点；pageSupport 等级与
    disabledOperations、CONSOLE_PAGE_MAP/CONTROL_PLANE_API 同步。
  - WP-D 测试与收口：domain/api 单测；stub e2e 替身；live e2e；基线按需再生；
    m0 全绿；RECHECK + MEM。
- 不包含：告警规则 CRUD、事故处置工作流、用户调度 CRUD/触发、质量报告生成；
  `.github/workflows/*`。

## 架构与数据流

```
GET /ops/alerts        ← RunStore(FAILED) ∪ endpoint_health(≠HEALTHY) ∪ workers(离线)
GET /ops/incidents     ← RunStore(FAILED)（候选；无处置流）
GET /ops/schedules     ← 进程内 scheduler 配置常量（只读事实）
GET /ops/data-health   ← endpoint_health 计数 + library(dataset) 计数 + artifact 抽样 verify
```

全部只读、确定性排序；无副作用；缺失依赖（worker_registry/artifacts=None）时该项
诚实降级为 `available=false` + reason，不伪造空成功。

## 验收条件

- [x] AC-01（WP-A）：四类视图有界校验；无持久化（纯视图类型）。
- [x] AC-02（WP-B）：四端点返回真实派生数据；失败 Run/降级端点/离线 worker 可见；
  未知项目 404；缺失依赖诚实降级；openapi 再生零漂移。
- [x] AC-03（WP-C）：四页消费真实端点；pageSupport（gap→partial）+ 文档一致；
  web lint/typecheck/test/build 绿。
- [x] AC-04（WP-D）：m0 全绿 + stub/live e2e 绿；push 后 quality-ubuntu 与
  console-frontend 全绿；RECHECK-045 回填。

## 实施清单

- [x] WP-A 视图域 ops_view.py
- [x] WP-B API + DTO + 注册
- [x] WP-C 前端 client + 四页 live + 文档
- [x] WP-D 测试 + 本地门 + 收口

## 证据

- **WP-A 视图域**（`packages/domain/ops_view.py`）：AlertItem/IncidentItem/
  ScheduleEntry/DataHealthMetric 冻结 dataclass + 有界校验（subject/detail 长度、
  kind/severity 枚举、interval>0）。无持久化（纯视图类型）。
- **WP-B API**（`services/api/routers/ops_view.py`、`services/api/dto/ops_view.py`、
  app 注册）：`GET /projects/{id}/ops/alerts`（失败 run ∪ 非健康端点 ∪ LOST/DRAINING
  worker，确定性排序）、`.../ops/incidents`（FAILED run 候选）、`GET /ops/schedules`
  （4 个进程内 scheduler 配置事实，interval 与 app.py 构造默认值一致）、
  `.../ops/data-health`（端点健康计数 + dataset 计数 + artifact 抽样 verify）。
  每视图回传能力锁定标记（rules/workflow/management/aggregate_available=false +
  reason）；未注册项目 404；run store 缺失 503。
  证据：`pytest tests/api/test_ops_view_api.py` = **5 passed**；
  `gen_openapi.py` 再生 + `test_openapi_snapshot` 2 passed。
- **WP-C 前端**：`opsViewClient` + 共享 `OpsViewPage` 骨架 + opsViewColumns；
  alerts/incidents/schedules/data-health 四页翻 live；pageSupport 等级（gap→partial）
  + disabledOperations、CONSOLE_PAGE_MAP（4 节 + G7 表）、CONTROL_PLANE_API 同步。
  console-shell 的 example 用例改用仍为 gap 的 `ops/matrix`；unit resolveDataSource
  断言同步（alerts→live、matrix→example）。
  证据：`pnpm --dir apps/web run lint/typecheck/test/build` 全绿（test 73/73）。
- **WP-D 测试与收口**：stub-api 补 4 ops 替身；design-fidelity testid 改 live；
  新增 live e2e「ops 只读投影」。基线 4 路由 × win32 + linux（强制重写 + 还原
  无关漂移，见 MEM-20260913-022）。证据：stub e2e 30/30、live e2e、全量 pytest、
  m0 见「状态历史」。

## 已知风险

- worker_registry/artifacts 在测试装配中可能为 None；降级路径须有测试覆盖，
  不得以空列表冒充「无告警」。
- 端点健康依赖 catalog（examples + 用户 override）；无端点时诚实为空。

## 状态历史

- 2026-09-14 由 GOAL cycle 5 派生，进入执行。
- 2026-09-14 WP-A~WP-D 完成并本地验证（api 5 / web 73 / stub 30 / live 14 /
  全量 pytest 3103 passed 0 failed / m0 分组全绿；收口期 stub-api.ts 超 450 行
  硬上限，拆 stubRoutes.ts/stubFixtures.ts 后 ts 9/9 与 stub 30/30 复跑通过）；
  提交并 push，CI 终态回填。

## 影响报告

- Domain/API/schema：新增 `ops_view` 视图域（无持久化）+ 4 个只读端点；
  openapi 快照再生；无破坏性变更。
- 安全/凭据：只读派生；无凭据回显；端点健康仅连通性。
- 兼容性/迁移：无数据迁移；无新表。
- 上游版本：无。
- 下一项：EC-04（深水区语义：budget_adjust/成本预测/真 pause-resume/实验队列/
  artifact diff/memory capability policy），cycle 6。
