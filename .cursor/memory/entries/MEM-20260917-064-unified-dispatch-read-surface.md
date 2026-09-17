---
id: MEM-20260917-064
title: "派发读面：一个 port 读答谁在派发、活租约 = 回收判据的补集、读面不外泄 lease_id"
status: ACTIVE
created_at: 2026-09-17
updated_at: 2026-09-17
scope: repository
confidence: 0.9
review_after: 2027-09-17
source_plans:
  - .cursor/plans/tasks/PLAN-20260917-089-unified-dispatch-ownership-read-surface.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260917-089-unified-dispatch-ownership-read-surface.md
supersedes: []
tags:
  - workflow-engine
  - dispatch
  - leases
  - read-surface
  - postgres
  - sqlite
---

# 统一派发读面：谁在派发这条 run

## 做了什么

`WorkflowEngine` 新增 `dispatch_ownership(run_id) -> DispatchOwnership`：**一个调用**同时
给出两件 canonical 事实——重排读面（`RetrySchedule`）与**活**租约持有者
（`LeaseHolder`：`task_id`/`worker_id`/`fence`/`expires_at`）——并组合成
`kind ∈ {NONE, RETRY_DISPATCH, WORKER_CLAIM, BOTH}`。控制面 `GET /runs/{id}`（与列表）
新增 `dispatch` 字段；`paused_dispatch` 改为消费**同一次读**的 `PAUSED` 投影（取值不变）。

```text
dispatch_ownership(run_id)                  # adapter 内用权威时钟
  ├─ retry  : 与 retry_schedule 同一列同一判据（同一 now）
  └─ leases : 未过期 且 持有者不是 LOST worker = recover_expired_leases 回收集合的补集
kind = NONE / RETRY_DISPATCH / WORKER_CLAIM / BOTH    # 事实的组合，不是第二份真相
```

## 为什么这样做

1. **两个派发方各持一半事实**：retry dispatch 守护线程只看 `PAUSED` 的重排到期（EC-02 的
   `paused_dispatch`），worker plane 的租约**完全不在读面**——一条 `RUNNING` 且任务正被 worker
   持租约跑的 run，从控制面看不出"有人在派发它"。运维要的正是"有没有、是哪一个"这一个答案。
2. **"活"必须与回收同判**：读面若自己拿墙钟比 `expires_at`，就会与 `recover_expired_leases`
   各说各话（读面说"有人在跑"、回收方同时说"这租约该收回了"）。判据取**回收的补集**后，
   两个持久化实现的用例可以在同一个测试里同时断言两侧（"读面说不活的，回收就该动手"）。
3. **能力面不复制**：`lease_id` 是作业面提交结果的凭据，控制面读面只给身份与到期。读面最小暴露
   是安全姿态（同 AGENTS.md §9 口径），用例里用负向断言钉住。

## 怎么做与复现

```bash
python -m pytest tests/contracts/test_dispatch_ownership_contract.py -q      # 三实现契约
python -m pytest tests/adapters/sqlite/test_dispatch_ownership.py -q        # 注入时钟：过期/LOST/边界秒
RESEARCHOS_POSTGRES_DSN=postgresql://research_os:research_os_m14_test@localhost:15432/research_os \
  python -m pytest tests/postgres/test_dispatch_ownership_pg.py -q          # PG parity
python -m pytest tests/api/test_run_dispatch_view_api.py -q                 # HTTP 三态 + BOTH + UNKNOWN
```

## 适用边界（踩过的坑）

- **`ClaimRequest.lease_ttl_seconds` 目前无人消费**：三个实现的取租路径都只用**引擎构造时**的
  `lease_ttl_seconds`。写用例时给请求传 TTL 不生效——要"租约比退避活得久"，得把**引擎** TTL
  调大（本轮的 BOTH 用例就这么写）。
- **LOST 判据要写成 `(worker_id IS NULL OR worker_id NOT IN (SELECT … state='LOST'))`**：
  SQL 的 `NULL NOT IN (...)` 结果是 NULL（行被过滤），漏了 `IS NULL` 分支就永远看不到控制面
  自持的租约。
- **Fake 没有过期语义**：它的"活" = 仍在租约表里；契约里"过期/LOST ⇒ 不活"两条只在两个
  持久化实现上钉，另有一条用例显式钉住 Fake 的限制（看到"持有"≠"租约新鲜"）。
- **PG 两读不构成快照**：重排与租约是同连接上的两次查询，并发写期间可能前移；读面是观测，
  不是事务保证（要强一致读属新增能力）。
- **`WORKER_CLAIM` 也覆盖 `worker_id=None` 的租约**（agent session 投递）：词表沿用 EC 的
  "worker claim / retry dispatch"；区分靠 `holder.worker_id`，文档已点名。
- **"两侧相等"式断言会假绿**：列表同判、只读性两条用例都拿同一个字段两次读比较，
  `dispatch=None` 时相等仍成立。修法是先钉住"读面真的答了"（`kind == WORKER_CLAIM`）再比。
- **450 行硬上限的收口姿势是搬代码**：PG 引擎加方法后 479 行 ⇒ 把 `due_retries`、
  `dispatch_ownership` 组合搬进 `projections.py`（与 SQLite 侧同形）、连接装配
  `resolve_connection` 上移 `db.py`；**不动门禁**。
- 相关：[[MEM-20260917-063]]（每线程连接）、[[MEM-20260917-062]]（事实从事件链接回）、
  [[MEM-20260917-060]]（停车语义读面）。

## 来源

- PLAN-20260917-089 / RECHECK-20260917-089（GOAL-20260917-004 cycle 6 = EC-05 第②半）。
