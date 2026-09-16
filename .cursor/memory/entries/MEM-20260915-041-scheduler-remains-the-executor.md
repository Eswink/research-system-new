---
id: MEM-20260915-041
title: 让守护线程"可管理"时，执行体必须还是它自己；记账失败不得杀死自愈循环
status: ACTIVE
created_at: 2026-09-16
updated_at: 2026-09-16
scope: repository
confidence: 0.9
review_after: 2027-09-16
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-066-ops-schedules-write-surface.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-066-ops-schedules-write-surface.md
supersedes: []
tags:
  - scheduler
  - daemon
  - write-surface-consumed
  - fail-open
  - contract-registry
---

# 调度写面：定义可写、执行体不变；`trigger` 与定时 pass 同函数

## 做了什么

把"进程内 4 个守护 scheduler 的只读事实"变成**可写定义 + 运行事实**（GOAL-003 cycle 4 / EC-03）：

```text
定义（可写，持久化）   ScheduleStore（schedules 表：name/job/interval/enabled/builtin/note）
执行体（进程内）       services/api/scheduler.py 的 PeriodicDaemon 子类 —— 每轮问 due(job)
手动触发               POST /ops/schedules/{name}/trigger → ScheduleRegistry.trigger → 注册的同一个 pass
运行事实（本进程）     run_count / last_run_at / last_outcome / next_due_at（重启归零）
```

## 为什么这样做

1. **写面必须被执行体的读面消费**：`enabled=false` 不是响应里的一个字段——守护线程每轮
   调 `ScheduleRegistry.due(job)`，停用的定义不再被授予，所以 `run_count` **冻结**。
   这条断言是可证伪的（真实线程 + 可控时钟：停用 0.5s 内计数不动，重新启用后继续涨），
   比"响应体说自己停用了"强得多。
2. **`trigger` 不许是第二条执行路径**：守护线程 `start()` 时把自己的 `_execute_pass`
   注册进 registry，`trigger(name)` 调的就是**这个函数对象**（用例用计数器证明）。
   换一套"手动执行"逻辑会让定时与手动两条路径缓慢分叉。
3. **记账失败不得杀死自愈线程**：`_record` / `_due_names` / `_next_wait` 全部 fail-open
   （各自 try/except 退化到"本轮不跑/用自身 interval"）。取舍是事实可能滞后一轮——但读面
   可见（`last_outcome` 停在旧值），而"线程死了"不可见。本仓的守护线程存在的理由就是
   自愈（M14 lease recovery 起），任何新增的记账调用都可能成为新的杀死路径。
4. **定义名与 job 是两个维度**：job 是受控词表（新增定义只能绑定既有词表——不新造执行路径），
   同一个 job 可以挂多条定义（守护线程每轮会对该 job 跑多次）。同名 job ≠ 同名定义。

## 怎么做与复现

```bash
# 语义（registry：due 的 reserve、record、trigger 共用 pass、停用被消费）
python -m pytest tests/application/ops/test_schedule_registry.py -q
# 执行体（真实线程：节奏随定义、停用被消费、失败记账仍存活、trigger 同一函数）
python -m pytest tests/application/ops/test_periodic_daemon.py -q
# HTTP 边界（读面诚实事实 / 取值域 / 冲突 / 未装配 store 的 503）
python -m pytest tests/api/test_ops_schedules_api.py -q
# console 链（stub 状态机 + live 真实 SQLite）
pnpm --dir apps/web exec playwright test schedules-write
pnpm --dir apps/web exec playwright test --config playwrightLive.config.ts schedules-write
```

装配要点：`ApiDeps.schedule_store` + `schedule_registry` 由**两组成同侧**装配
（`composition._sqlite_config_stores` / `pg_composition._pg_config_stores` / `run_fixtures` /
`conftest`），lifespan 把**同一个 registry 实例**作为 `control` 交给四个守护线程——
两个实例会让 `trigger` 找不到执行体（注册进 A、路由读 B）。

## 适用边界（踩过的坑）

- **校验只能有一份实现**：首版 registry 的 `_validate`（只查首字母小写）比域正则
  （`^[a-z][a-z0-9_]{2,40}$`）弱，`"ab"` 会穿过写面直达 dataclass 抛 `ValueError` ⇒ 500。
  改成 `validate_schedule_name()` 由域与 registry 共用后，控制面稳定返回 422。
- **取值域校验不能放在 DTO**：`services/api/dto/**` 不得 import `packages`（架构门禁
  `api-dto-purity`，配置在 `.importlinter.api`）。把 `job: ScheduleJob` 写进 Pydantic
  会在**全量 m0** 里判红——定向套件（contracts/api/ops）看不到 `tests/architecture`。
  正确形态：DTO 收字符串，域边界（`ScheduleRegistry._coerce_job`）收敛成枚举并点名合法值；
  代价是 OpenAPI 里没有 enum 列表，补偿是在字段 description 指向词表的权威读面
  （`GET /ops/schedules` 的 `jobs`），**而不是在 DTO 里再抄一份词表**（重复即漂移）。
- **新端口要进 contract registry**：`ScheduleStore` 需同时登记 `_FAKE_FACTORIES` /
  `_PORT_PROTOCOL_NAMES` / `_PORT_PROBES` / `_PORT_PROBE_METHODS` 与矩阵期望集；
  Fake 必须用 `FakeBase._enter(method, args)`（用 `_ensure_open()` 会让故障注入用例失效）。
- **守护线程的等待下界是它自己的 interval**：定义只回答"这一轮跑不跑"（`due()` 授予与否），
  不回答"多久醒一次"。首版把"尚未预约的定义"当成 0.1s 候选 ⇒ `min(fallback, 0.1)` = 0.1 ⇒
  四个守护线程在 `create_app` 后约 100ms **同时**执行首个 pass（它们原本各自要等 5s/15s/30s），
  于是和启动期初始化写在共享连接上并发，把请求线程的显式 Postgres 事务打断
  （`tests/postgres/test_m13_pg_run_e2e.py` 在干净 HEAD 上 6/6 绿、带该行为 6/6 红；
  `OutOfOrderTransactionNesting`）。"定义下一轮生效"要按字面实现——**未预约 ⇒ 不参与候选**。
- **进程内观测 ≠ 持久事实**：`run_count` 重启归零是诚实的（它不是配置）。要跨重启历史就是
  另一个存储面，不要偷偷把内存计数写进 read DTO 冒充"历史"。
- **调度写面不过 policy**：它等价于启停既有守护线程，无外部副作用面；如果将来要求
  "调度变更也走审批"，需要新增 `schedule.*` 能力并接 policy（RECHECK-066 W-6）。

## 来源

- PLAN-20260915-066 / RECHECK-20260915-066（GOAL-20260915-003 cycle 4 / EC-03）。
- 相关：[[MEM-20260915-040]]（写面能力要与平台策略词表对齐——本记忆的 W-6 是同一族问题）、
  [[MEM-20260915-038]]（结构签名与像素判据互补：本轮 ops-schedules 结构 +90 节点判红、
  像素仅 1.64%）。
