# Control Plane API Sketch v0.4.0

所有 mutating request 支持：

```text
Idempotency-Key
If-Match / resource version
```

## Models

```text
POST   /llm-endpoints
GET    /llm-endpoints
GET    /llm-endpoints/{id}
PATCH  /llm-endpoints/{id}
DELETE /llm-endpoints/{id}               （WP-B G10；被用户模型引用 → 409）
POST   /llm-endpoints/{id}/test
POST   /llm-endpoints/{id}/discover-models
GET    /llm-endpoints/{id}/health

POST   /models
GET    /models
GET    /models/{id}
PATCH  /models/{id}
DELETE /models/{id}                      （WP-B G10；被 agent 显式绑定 → 409）
POST   /models/{id}/probe
GET    /models/{id}/compatibility        （hard_capability_requirements 为
                                          合并目录投影：role all_of/any_of +
                                          profile hard_capabilities；WP-B）
```

不返回明文 Key。

## Projects（注册表，PLAN-20260912-041 WP-A）

```text
GET    /projects                                 （默认 example-project 恒在首位；用户项目按 store 合并）
POST   /projects                                 （name 必填；id 服务端生成；自动落默认设置行）
PATCH  /projects/{id}                            （rename 和/或 status: ACTIVE|ARCHIVED；归档 ≠ 删除）
DELETE /projects/{id}                            （PLAN-061：被引用 → 409 且列出引用，不级联；默认项目 409）
```

- `DELETE` 的判定顺序与语义：`example-project` 由 examples 契约合成 → 409
  `Project Reserved`（删了也还在，属静默 no-op 陷阱）；未知 id → 404；未装配 store → 503；
  仍被 runs / 协议草稿 / 实验队列 / 库资源 / ops 规则或事故引用 → 409 `Project In Use`
  且 detail 给出逐项计数（`runs=2, drafts=1` 形式）——**控制面不做级联删除**，用户须先
  自行处置研究数据；无引用 → 204，注册行与随项目创建的设置行一并删除（设置行与项目注册
  同生，不是研究数据）。删除对活动与已归档项目同样适用。
- 单用户项目注册表；不表达租户/授权（M18 deferred）。数据面归属真实生效：
  runs 列表按项目过滤、`GET /projects/{id}/settings` 按项目精确（仅默认项目
  允许 examples 回退）、协议草稿按路径项目创建/列表；agents/memory/experiments
  数据面暂为单项目共享（G2 标注，不伪装隔离）。未注册项目访问项目面 → 404。

## Library（库目录，PLAN-20260914-044 WP-B）

```text
GET    /projects/{id}/library                    （可选 ?kind=prompt|dataset|notebook 过滤）
POST   /projects/{id}/library                    （kind/name 必填；id 服务端生成；201）
GET    /library/{resource_id}                    （未知 404）
PATCH  /library/{resource_id}                    （rename 和/或 status: ACTIVE|ARCHIVED；无 DELETE）
```

- prompts/datasets/notebooks 三页共享的目录事实：元数据 + 不透明 content_ref
  （不解析/不下载）。配置面存储（与 projects/settings/agents 同侧，两组成均为
  SQLite），不新增 PG 表。datasets 的评测输入仍由 eval spec 承载，不与之耦合。
  未注册项目写入 → 404；store 未配置 → 503。

## Ops

读面（PLAN-20260914-045 WP-B，只读运维投影）：

```text
GET    /projects/{id}/ops/alerts                  （派生：失败 Run ∪ 非健康端点 ∪ 离线 worker）
GET    /projects/{id}/ops/incidents               （已登记事故 + FAILED run 候选）
GET    /ops/schedules                             （调度定义 + 每项运行事实；见下"调度"）
GET    /projects/{id}/ops/data-health             （端点健康计数 + dataset 计数 + artifact 抽样校验）
```

写面（PLAN-20260915-059，G7）：

```text
GET    /projects/{id}/ops/alert-rules             （项目内静音规则；store 未配置 → rules_available=false + 原因）
POST   /projects/{id}/ops/alert-rules             （新建规则；kind/max_severity 为空 = 不限来源/级别）
PATCH  /ops/alert-rules/{id}                      （改名/启停/改范围；clear_kind / clear_max_severity 显式清空）
DELETE /ops/alert-rules/{id}                      （删除规则；读面即时反映）
POST   /projects/{id}/ops/incidents               （显式登记事故，可关联来源 run）
POST   /ops/incidents/{id}/assign                 （指派处理人；已关闭 → 409）
POST   /ops/incidents/{id}/close                  （关闭并留处理结论；已关闭 → 409）
```

- 读面全部**只读派生**，无持久化、无副作用；缺失依赖（worker_registry/
  artifacts=None）时该项诚实缺省。能力缺口随响应回传：alerts 的 rules_available、
  incidents 的 workflow_available、schedules 的 management_available、
  data-health 的 aggregate_available 均为 false + 原因说明。未注册项目 → 404。
- 写面是**被消费**的：规则命中只给告警打 `muted`/`muted_by` 标记（不隐藏），
  已登记事故回链来源 run 的告警并在候选列表中去重，关闭后不再有处置动作。

### 调度（PLAN-20260915-066 / GOAL-003 EC-03）

```text
GET    /ops/schedules                   （定义 + 每项运行事实；无 store → 静态回落 + management_available=false）
POST   /ops/schedules                   （登记定义：name/job/interval_seconds/enabled/note）
PATCH  /ops/schedules/{name}            （启停 / 改 interval）
POST   /ops/schedules/{name}/trigger    （手动触发一次 pass）
```

- **执行体不新增**：仍是 `services/api/scheduler.py` 的进程内守护线程。定义只决定
  `enabled`/`interval_seconds`（守护线程每轮经 `ScheduleRegistry.due` 读取，下一轮生效）；
  新增定义只能绑定既有 `job` 词表（lease_recovery / outbox_relay / retention /
  worker_reaper / retry_dispatch），否则 422 并点名合法值。`retry_dispatch` 是 cycle 19
  起的新执行体：把重排已到期、停在 `PAUSED` 的 run 自动续跑（此前只能人工 resume）。
- **trigger 复用同一条 pass**：`ScheduleRegistry.trigger` 调用守护线程注册的同一个函数
  对象，并写下与定时 pass 相同的运行事实（`run_count`/`last_run_at`/`last_outcome`）。
  pass 自身失败仍返回 200，但 `last_outcome=FAILED` + `last_error` 如实留痕。
- **写面被读面消费**（可证伪）：`enabled=false` 后该定义不再出现在 `due()` 里，
  `run_count` 停止增长；`next_due_at` 为 null。无执行体的作业 `executor_attached=false`。
- 事实口径：`run_count`/`last_run_at`/`last_outcome` 是**本进程观测**（重启归零），
  未跑过就是 null/UNKNOWN——不伪造成功。配置（name/job/interval/enabled/note）持久化在
  ScheduleStore（SQLite 配置面，两组成同侧）。
- 错误：未知 name → 404；名字重复/占用内置名 → 409；已停用或无执行体触发 → 409；
  name 形状、interval 越界（1~86400 秒）、job 不在词表 → 422；未装配 store → 503
  （读面同时回落静态事实并给出 `management_reason`）。

## Roles / Teams / Agents

```text
GET    /roles                            （合并视图：examples 基底 + SQLite 用户覆盖）
POST   /roles/custom                     （WP-B：examples 同 schema/domain 校验；id 冲突 409）
GET    /team-templates
POST   /team-templates/custom            （WP-B：同上）
GET    /projects/{id}/agents
POST   /projects/{id}/agents
PATCH  /agents/{id}
POST   /agents/{id}/clone                （WP-B；new_id 缺省服务端生成）
DELETE /agents/{id}                      （WP-B G10；仅用户 store 记录，契约基线 404）
```

## Protocol / Preflight

```text
POST   /protocols/validate                 （path 或 {draft_id,draft_revision} 二选一）
POST   /projects/{id}/compile              （同上双来源；WP-B 已交付）
POST   /projects/{id}/preflight            （同上双来源）
POST   /projects/{id}/dry-run              （同上双来源）
GET    /compiled-plans/{id}                （未提供：编译产物暂无独立寻址）
POST   /compiled-plans/{id}/preflight      （未提供：见上双来源预检）
```

## Protocol Drafts（PLAN-20260908-033）

```text
GET    /protocol-templates
GET    /protocol-templates/{template_id}
POST   /protocol-drafts/validate          （零副作用；分析类 POST）
POST   /projects/{id}/protocol-drafts     （创建草稿；Idempotency-Key）
GET    /projects/{id}/protocol-drafts
GET    /protocol-drafts/{draft_id}
PUT    /protocol-drafts/{draft_id}        （保存新修订；If-Match + expected_revision；冲突 412）
DELETE /protocol-drafts/{draft_id}        （WP-B G10；物理删除草稿与修订；未知 404）
GET    /protocol-drafts/{draft_id}/revisions
GET    /protocol-drafts/{draft_id}/revisions/{revision}
POST   /projects/{id}/runs                （扩展：{draft_id, draft_revision} 引用，与 path 二选一）
```

- 修订 append-only、不可变；修订号是草稿内部版本（非工程版本、非 RunManifest Revision）。
- 启动使用已保存修订时，服务端加载该不可变修订并重新 Compile → Preflight → Freeze；
  草稿后续变化不改写已冻结运行。
- 旧 `protocol_path` 请求保持兼容。
- WP-B（PLAN-20260910-037）：validate/compile/preflight/dry-run 与 runs 启动共用
  同一 `protocol_source` loader（互斥来源、缺失 422、未知修订 404）。
- GOAL-004 cycle 1：启动时把**被解析的那份正文**连同 sha256 冻结进 run 行
  （`protocol_body`），重启后的重建只认这份字节——外部文件/草稿修订消失都不再阻断
  续跑；`GET /runs/{id}` 的 `protocol_body_digest` 为空表示该 run 早于正文冻结，
  其重启续跑仍依赖来源可解析。冻结不改变漂移判据：重建仍要过语义 digest 校验。
- `GET /runs/{id}`（与列表）的 `paused_dispatch` 是**停车语义读面**（GOAL-004 cycle 2）：
  仅当 `state == "PAUSED"` 时非空，`kind` 取三值之一——
  - `RETRY_SCHEDULED`：任务面有重排在等时钟（`due_now=false`，`next_retry_at` 是该
    期限）或已经到期（`due_now=true`）⇒ 派发守护到期会自己把它续起来；
  - `USER_PAUSED`：任务面没有任何重排 ⇒ 只有人工 `resume`/`cancel` 会动它；
  - `UNKNOWN`：控制面没有 workflow 读面（或读面读不到）⇒ 不猜。
  判据只有两件 canonical 事实（run 行状态 + 任务行 `RETRY_SCHEDULED`/`retry_at`），
  不是"停车原因"字段；"现在"在 adapter 内用权威时钟取（与调度器同一处），读面不自己
  比墙钟。**诚实边界**：重建被拒后放回的停车在任务面表现为"重排已到期但没动"
  （`RETRY_SCHEDULED` + `due_now=true`），**拒绝原因不在读面**（只在本进程遥测/日志）。
- `GET /runs/{id}`（与列表）的 `manifest_semantic_digest` 是**冻结的语义 digest**
  （GOAL-004 cycle 4 = EC-04）：排除 `frozen_at`（`manifest_digest` 覆盖它），是
  resume/重建的漂移校验输入。成功路径与**执行期失败收敛的 `FAILED` run** 都带它——
  收敛路径没有 `RunOutcome`，从 `manifest.frozen` 事件 payload 的 `semantic_digest`
  补回，落行走与成功路径同一个 `ResearchRun.with_manifest(...)`。**诚实边界**：
  非空只表示"这条 run 冻结过一次 manifest 且事件里有这项"，不保证重建成功
  （目录/契约漂移仍被 `assert_semantics_frozen` 拒绝）；`None` = 未冻结、preflight
  被拒，或事件早于本轮（不回填、不猜测）。
- `GET /runs/{id}`（与列表）的 `dispatch` 是**统一派发读面**（GOAL-004 cycle 6 = EC-05 ②）：
  **任何状态**都给，回答"这条 run 现在有没有活的派发方、是哪一个"。两个派发方此前各持
  一半事实（retry dispatch 只看 `PAUSED` 的重排到期；worker plane 的租约不在读面），
  现在由**一个** port 读（`WorkflowEngine.dispatch_ownership`）同时给出：
  - `kind=WORKER_CLAIM`：有**活着**的租约持有者（`holders[]` 逐条给 `task_id`/
    `worker_id`/`fence`/`expires_at`；`worker_id` 为 `null` = 控制面自己持有，即 agent
    session 投递，不是 worker plane claim）；
  - `kind=RETRY_DISPATCH`：任务面有重排（`retry.scheduled`/`retry.due`/`retry.next_retry_at`）
    ⇒ 派发守护会（或马上会）续跑；
  - `kind=BOTH`：两件事实同时存在；`kind=NONE`：都没有；
  - `kind=UNKNOWN`：控制面没有 workflow 读面（或读面读不到）⇒ 不猜。

  "活"的判据是**回收判据的补集**（未过期且持有者不是 LOST worker），在 adapter 内用
  权威时钟取（生产：DB 时钟；测试：注入时钟）——读面与 `recover_expired_leases` 不会
  各说各话。**诚实边界**：`dispatch` 不回答执行健康度（心跳新鲜度、进度、卡死与否都不在
  这里）；不暴露 `lease_id`（那是作业面结果提交的凭据，控制面读面不复制能力）。
  `paused_dispatch` 与 `dispatch` 出自**同一次读**（`paused_dispatch` 是它的 `PAUSED`
  投影），不会互相漂移。

  **列表路径**（`GET /projects/{id}/runs`）走**一次批量读**
  （`WorkflowEngine.dispatch_ownership_many`，GOAL-005 cycle 5 = EC-05 ①）：单 run 读就是
  批量读的一条（同一段装配）⇒ 逐行判定与 `GET /runs/{id}` 逐字相同，而查询数不再随 run
  数增长。没有 workflow 读面时逐行 `UNKNOWN`（与详情同口径）；空页不读派发面。
  `kind` 的两件事实出自**同一条语句**（GOAL-20260918-006 cycle 1 = EC-01）⇒ 它们来自
  **同一个快照**：并发写不会让响应出现"重排面已前移、租约面仍是旧值"的混合态。

  批量读**有显式上限**（GOAL-20260918-006 cycle 5 = EC-05 ①）：上限是 port 常量
  `MAX_DISPATCH_OWNERSHIP_BATCH`（= 500 条，唯一事实源）；单次调用超限 ⇒
  `InvalidInputError`（调用方 bug、可判定拒绝，**不静默截断**），恰好等于上限合法。
  页大于上限时**由控制面服务层按该常量分块**（`services/api/run_dispatch_view.py`）、
  合并后回答整页 —— 代价是一条**显式边界**：此时整批可能**跨多个快照**（块内仍确定是
  一个快照），同一页里两条 run 的 `kind` 因此可能来自相隔一次提交的两个时刻。任一块读不到
  ⇒ 整批 `UNKNOWN`（不给半份答案：半份会让"没读的部分"看着像 `NONE`）。

  **两条容易读错的事实**（同源登记，EC-05 文档面）：① **Fake 实现没有租约过期语义** ——
  它的"活"= 仍在租约表里，过期与 LOST worker 两种情形由 SQLite 注入时钟单测与 PG parity
  覆盖（Fake 不假装实现回收）；② `kind=WORKER_CLAIM` **也覆盖控制面自持的租约** ——
  `worker_id` 为 `null` 的持有者是 agent session 投递路径，不是 worker plane claim，
  `kind` 不区分这两种持有者（要区分只能看 `holders[].worker_id`）。
  这两条只是"逐条点名"清单里的两条：可同判轴与不可同判轴的完整清单写在 port docstring 里，
  由 `tests/contracts/test_dispatch_ownership_weak_equivalence.py` 机器校验（可同判轴与契约
  套件里的三实现用例双向一一对应；不可同判轴的判据不许声称三实现）。
- `GET /runs/{id}`（与列表）的 `rebuild` 是**重建能力读面**（GOAL-005 cycle 6 = EC-06）：
  **任何状态**都给，正面回答"这份**记录**够不够重建、缺哪条事实"——历史上这里只有两个
  含糊的 `None`（`manifest_semantic_digest` / `protocol_body_digest`），分不清"功能前的
  历史行"与"起步时冻结失败 / 还没冻结"：
  - `status=SELF_CONTAINED`：冻结正文（`protocol_body_digest` 非空）+ 两个 digest 齐
    ⇒ 重建只用行上的字节，外部来源消失/漂移都不影响；
  - `status=SOURCE_DEPENDENT`：两个 digest 齐、**没有**冻结正文 ⇒ 重建依赖来源仍可解析
    （模板路径还在 / 草稿修订还在）；
  - `status=REFUSED`：缺阻塞事实 ⇒ 重建会被拒绝，`missing` **点名**缺的是哪条：
    `manifest_digest`（无法校验重建）、`manifest_semantic_digest`（**旧 `manifest.frozen`
    事件形态**：事件早于语义 digest 那一轮，漂移校验没有输入）、
    `protocol_body` + `protocol_source`（**旧 run 形态**：没有任何装配输入）；出路是
    fork run 或 revision（与 `/resume` 拒绝文案同一口径）。

  **同源**：`missing` 与 `/resume` 拒绝文案由**同一个分类器**给出
  （`packages/application/run_orchestration/rebuild_readiness.py`），不会各说各话；
  `missing` 里的名字就是 canonical run 行的**字段名**。**控制台**（GOAL-006 cycle 3 =
  EC-03）：`#/run/timeline` 的「重建就绪（读面）」面板直接渲染这份 `status`/`missing`
  （`apps/web/src/features/runs/RebuildReadiness.tsx`），文案与本节同口径——`SELF_CONTAINED`
  写成"记录自足"（不是"重建必过"）、`REFUSED` 写成"读面拒绝给出结论"（不是"不可回填"）、
  `missing` 以行字段名逐个点名；stub 与 live 两条 e2e 都断言"页面值 == 读面返回值"。
  **诚实边界**：`rebuild` 只回答
  "输入齐不齐"，不回答"该不该重建"（状态机/策略/预算不在这里），也不承诺"重建必过"
  ——漂移校验与 preflight 仍在 `/resume` 真跑时判。`REFUSED` **不是**"不可回填"的裁决：
  运营侧仍可用 `tools/snapshot_migrate.py`（显式 opt-in）对个别 run 做 re-freeze / fork。
- **`execution`（执行体读面，GOAL-007 cycle 4 = EC-04）**：`GET /runs/{id}` 给出
  `execution.execution_backend`（这条 run 是哪个执行体跑的：`fake` = 受控 demo 执行体、
  `openhands` = 真实 adapter）与 `execution.runtime_fingerprint`（AGENTS.md §4 指纹槽位的
  **状态**：`status` + `substrate` + `reason`）。**两个 `null` 不是一回事**：
  `execution` 为 `null` = 这条 run **尚未冻结**；`execution_backend` 为 `null` =
  **冻结时未声明**（M7 不伪填充口径）——都不代表某个具体执行体。
  **同源**：事实取自冻结的 `manifest.frozen` 事件 payload（`services/api/run_execution_view.py`
  回读，不另存副本），与 `GET /runs/{id}/events` 上看到的是同一份值。指纹只报状态：
  `NOT_VERIFIED` 时连同 `reason` 一起给出（默认受控 demo 执行体不发起模型调用，§4 的七件
  事实一件也不存在），**不得**被读作"已验证的指纹"。**边界**：列表路径
  （`GET /projects/{id}/runs`）**不带**这两个字段——避免逐 run 回读冻结事件形成 N+1；
  列表要披露时另开批量读面。**控制台**：`#/run/timeline` 的「运行身份」面板渲染这两项
  （`run-execution-backend` / `run-runtime-fingerprint`），stub 与 live 两条 e2e 断言
  "页面值 == 读面返回值"且**两种执行体在页面上可区分**。

## Runs

```text
GET    /projects/{id}/runs
POST   /projects/{id}/runs
GET    /projects/{id}/settings
PUT    /projects/{id}/settings
GET    /runs/{id}
POST   /runs/{id}/pause                   （PLAN-048 协作式暂停：派发面停止认领）
POST   /runs/{id}/resume                  （恢复派发；无进程内上下文时按 run 的冻结正文重建续跑）
POST   /runs/{id}/cancel
POST   /runs/{id}/fork                     （未提供：Fork/Manifest Revision 属后续能力）
GET    /runs/{id}/events
GET    /runs/{id}/usage
GET    /runs/{id}/telemetry
GET    /runs/{id}/cost
GET    /runs/{id}/artifacts                （WP-C 只读列表）
GET    /artifacts/{artifact_id}            （WP-C 元数据 + 内容级 verify）
GET    /artifacts/{artifact_id}/content    （WP-C 下载/白名单内联预览）
GET    /artifacts/{left}/diff/{right}      （PLAN-047 制品内容 diff：行级 hunks + 统计）
GET    /cost/daily                         （WP-D 跨 run 日序列，五状态盖章）
GET    /evaluations/trend
GET    /cluster/workers
GET    /runs/{id}/placement
```

M15 Operations（只读投影）：

- `GET /runs/{id}/telemetry` — canonical state + sink 计数器组成的
  telemetry summary(任务状态计数、outbox pending、exporter drop/last_error);
  不含任何 telemetry vendor 数据。
- `GET /runs/{id}/cost` — UsageLedger × 版本化定价快照的五状态成本视图
  (ACTUAL/ESTIMATED/MONETARY_UNAVAILABLE/USAGE_UNKNOWN/ZERO +
  pricing_version/digest 盖章)。
- `GET /evaluations/trend` — 分段可比趋势 + 回归标记(判定来自
  `compare_reports`)+ 缺失评测第三态;可选 `dataset_id` 过滤。
- `GET /cost/daily`（WP-D）— UsageLedger 全扫描按 UTC 日投影；每天按
  (pricing_version, digest) 分组，混合定价的日不求和（PARTIALLY_METERED +
  分组小计）；只含有数据的日期，无预测无插值。
- `GET /artifacts/*`（WP-C）— store 缺失 503；未知 404；tombstone/缺 blob
  410；超限 413；非白名单 media 一律 attachment + nosniff。
- `POST /runs/{id}/pause`（PLAN-048）— canonical 状态即暂停事实：PAUSED 后
  派发面（`claim_next`）不再认领该 run 的任务，**已持租约不撤销**；本进程若正
  持有该 run 的执行上下文，执行器在下一次 phase 组边界读到 PAUSED 后零任务
  执行并返回 PAUSED（剩余 specs 暂存）。响应带 `dispatch=HELD` /
  `execution_context`（`NONE` 或 `PAUSED_IN_PROCESS`）。只有 RUNNING 可暂停（否则 409）。
- `POST /runs/{id}/resume`（PLAN-048；cycle 20 扩展）— 恢复派发；**继续执行**优先用
  本进程持有的暂停上下文（`continuation=RESUMED`），没有上下文时（进程重启过）按 run 行
  记下的**协议来源**重建执行上下文再续跑（`continuation=REBUILT`，重建的装配链与
  `POST /runs` 同一条：来源解析 → 目录/项目合并 → preflight → 冻结语义校验，漂移一律拒绝）；
  重建被拒或没有来源可重建时 `continuation=NONE` 并在 `note` 里点名原因（只解除暂停，
  不伪造续跑）。只有 PAUSED 可恢复（否则 409）。
  无抢占式中断：暂停不撤销在途租约，也不物理停止已派发的 worker 任务。
- `GET /artifacts/{left}/diff/{right}`（PLAN-047）— 两侧都是 persisted 制品
  （口径：制品内容 vs 制品内容；控制面**没有**文件系统快照 diff 面）。相同内容
  → `identical=true` 且 lines 空；二进制/非 UTF-8 → `available=false` +
  `reason=BINARY_CONTENT|NOT_TEXT`；单侧超过 2 MiB → `reason=TOO_LARGE`；
  行数超过 2000 → 保留头部 + `truncated=true`。不可比一律 200 + 显式原因，
  不返回空 diff 冒充"无差异"；diff 不落库。

## Inspection（只读投影；WP-A 对齐 run gate）

```text
GET    /runs/{id}/evidence                 （未知 run 404；ledger 缺失 503）
GET    /runs/{id}/claims                   （同上；degraded 标志显式）
GET    /runs/{id}/usage                    （run 级隔离；UNKNOWN ≠ 0）
GET    /runs/{id}/cost-forecast            （PLAN-046：预留-消耗-剩余；只覆盖已预留
                                            额度，不外推；UNKNOWN/跨币种不降级为 0；
                                            attribution=RESERVATION_REF/RUN_SCOPE/NONE）
GET    /runs/{id}/export                   （persisted-state 重算，非 UI 内存）
GET    /runs/{id}/deliverable              （PLAN-043：M12 持久化交付物；无产物 available=false）
GET    /runs/{id}/lineage                  （PLAN-043：Run 级 nodes/edges typed 投影；全局血缘恒 false）
```

## Health（WP-A）

```text
GET    /health                             （status/version/composition/pricing_degraded；
                                           无秘密、无内容采样）
```

## Tasks / Approvals

```text
GET    /runs/{id}/tasks
GET    /tasks/{id}                         （未提供：任务详情走 /runs/{id}/tasks 投影）
POST   /tasks/{id}/retry                   （未提供：retry 属 WorkflowEngine 内部策略）
POST   /tasks/{id}/fork                    （未提供：同 runs fork）
GET    /approvals
POST   /approvals/{id}/decide
GET    /runs/{id}/approvals               （WP-B：run 审批历史，含已裁决；未知 run 404）
POST   /runs/{id}/interventions           （pause/resume 状态迁移已接线 WP-H；
                                          budget_adjust 走 BudgetLedger release+reserve
                                          （PLAN-046：200 调整摘要 / 无调整行 422 /
                                          预算面缺失 503）；replace_agent 仍 501）
```

WP-H（PLAN-20260910-037）审批注册点：协议 phase 声明
`gate: HUMAN_GATE`（preflight 呈现为 INFO 声明 + unresolved_risks，不阻断
freeze）；执行循环在该 phase 前注册 ApprovalRecord 并 emit
`approval.requested`，run 进入 WAITING_FOR_APPROVAL。decide approve 后续跑
剩余 specs 并持久化终态；进程重启导致执行上下文丢失时 approve 诚实返回
503 且不消费审批（绝不伪造恢复）。deny → APPROVAL_REJECTED → FAILED。

approve 的**续跑失败**（GOAL-005 cycle 2 = EC-02）：裁决已落库（响应仍是 200 +
`APPROVED`），但续跑执行失败时 canonical **不放任在悬空 `RUNNING`**——与
`POST /runs/{id}/resume` 的补偿同形：run 放回 `PAUSED`，失败原因写进事件链
（`run.resume_failed`：`failure_type` / `message` / `compensated_to`）。响应体不新增
字段，**结局以 canonical 状态 + 事件链判别**（与 `/resume` 的 `continuation` 口径一致：
失败不是终态，运营可再从停车态续）。本入口只有一处驱动（本端点），`resume_paused`
的另一条驱动是守护线程，两者的补偿共用同一实现（`compensate_failed_resume`）。
竞态（上下文已被取走 ⇒ `InvalidInputError`）保持既有 no-op——那种情况下另一个入口
正在跑这个 run，`RUNNING` 是正确状态。

**补偿失败本身也是可读事实**（GOAL-20260918-006 cycle 6 = EC-06 (b)）：守护线程面补偿
失败（store 不可用等）时，run 仍停在原 canonical 状态、下一轮重新评估，**并**在事件链里
记一条 `run.resume_compensation_failed`（payload：`run_id` / `failure_type` / `message` /
`canonical_state`；`canonical_state` 是补偿失败时 run 仍停在的状态，**没有**被伪造成
`PAUSED`）⇒ 用 `GET /runs/{id}/events` 就能判"这次补偿没做成"，不必翻遥测/log。
**地板**：连这条事件也发不出去时只剩遥测（本轮如实登记，不宣称"必然留痕"）。

**两条一等边界**（同源登记，EC-06）：① `run.resume_failed` /
`run.resume_compensation_failed` 的 payload **不含任务级归因**——"哪一步（哪个 task/phase）
炸的"要读该 run 的事件链上下文（本读面不承诺任务级归因）；② `/resume` 的续跑失败响应仍是
`200` + `continuation=FAILED`（与 `NONE` / `REBUILT` 同形状），**结局必须看 `continuation`
与 canonical 状态**；换成 5xx 之类的传输层信号属产品决策，本轮只如实登记、不改。

## Tools

```text
GET    /tool-providers                     （PLAN-043：目录只读投影 + 三态健康；只含已批准注册）
GET    /tool-provider-registrations        （PLAN-060：全部注册；注册表未装配 → 200 + 不可用原因）
POST   /tool-provider-registrations        （登记 PENDING；pin 必须 sha256:<hex>；id 已存在/被内置目录占用 → 409）
PATCH  /tool-provider-registrations/{id}   （re-pin/能力等可变字段；REVOKED 终态 → 409）
POST   /tool-provider-registrations/{id}/approve       （PENDING → ACTIVE：进入目录，preflight/compile 立即可见）
POST   /tool-provider-registrations/{id}/revoke        （任意非终态 → REVOKED；理由必填并留痕）
POST   /tool-provider-registrations/{id}/health-check  （写入一次健康事实；读面随后呈现同一结论）
GET    /tool-packs                         （PLAN-064：全部已安装 pack；生效版本与待批准版本分开呈现）
POST   /tool-packs/install                 （PLAN-064：安装/提交更新；控制面重算内容 digest 并要求与请求 digest 相等）
POST   /tool-packs/{id}/approve-update     （PLAN-064：批准权限扩张；此前新版本不生效）
POST   /tool-packs/{id}/revoke             （PLAN-064：终态吊销；digest 退出目录、待批准更新清空）
```

- **ToolPack 供应链（PLAN-064 / EC-02）**：`install` 由控制面自己重算 manifest 内容
  digest 并要求与请求里的 `digest` 相等（内容与 pin 不符 → 422；这不是采信调用方写的
  字面量）；`requested_capabilities` 与各 tool 的 capabilities 必须都在平台词表
  （`examples/config/capabilities.yaml`，与离线 bundle validator 同源），否则 422 并点名；
  平台自带 pack id（`examples/contracts/toolpack_*.yaml`）不可影子覆盖 → 409。
- **权限扩张不立即生效**：同 id 提交的 manifest 若新增 capability / network domain /
  credential（`permission_diff` 非空），登记为**待批准更新**并返回该 pack 的旧 digest——
  `approve-update` 通过 policy（`tool_pack.update.expanded`）后才替换；无扩张的更新直接生效；
  内容完全相同的提交返回 `unchanged`（不改写任何东西）。**"已提交"不等于"已生效"**。
- **被消费**：state=INSTALLED 的 pack 把 digest 合入 `tool_pack_digests`（键 = pack id 去掉
  `_vN` 后缀，与 examples 契约同口径），preflight 的 `SUPPLY_CHAIN_UNPINNED` 与 compile 的
  `tool_pack_digests` 随之改变；REVOKED 是终态退出（吊销后 pin 消失）。
- **console 操作入口（PLAN-065）**：`ops/integrations` 的 ToolPack 面板消费上述四条路由
  （表单提交完整 manifest、待批准横幅给出候选 digest 与 diff 明细、批准/吊销行内动作），
  stub 与 live e2e 各有一条链。注意：生命周期按能力名 `tool_pack.install/update/revoke`
  求值策略，而平台默认策略（`examples/config/policy.yaml`）没有这些规则 ⇒ default DENY，
  真实部署下需运维显式放行；**live 夹具层**（`tests/api/console_api_app.py`）只放行这四个
  能力以便跑通写链，未放宽产品策略。
- 控制面重算 digest 证明的是"提交内容与声明的 pin 自洽"，**不是**"pin 与上游实际交付物一致"
  （后者需要远端取证，不在控制面职责内）。

- 信任级别由注册状态推导（PENDING→UNTRUSTED、ACTIVE→USER_APPROVED、REVOKED→
  REVOKED），注册方不能声明 BUILT_IN/VERIFIED；pin 强制内容寻址 digest（AGENTS.md §9
  「默认 deny：unpinned plugin」），并可漂移的 tag/分支名一律 422。
- 批准后该 provider 与其 pin digest 合入 `tool_providers`/`tool_pack_digests`：
  compile 的 `provider_ids`、preflight 的工具可用性与供应链 pin 检查都随之改变；
  PENDING/REVOKED 不进入目录（未批准不可用、吊销即退出）。
- provider 凭据绑定无写面（凭据域独立，不经控制面转发）。

## Experiments（WP-E；WP-A 起 SQLite 开发路径与 PG 双支持）

```text
GET    /runs/{id}/experiments              （run 级 evidence 聚合视图）
GET    /projects/{id}/experiments          （项目级跨 run 视图；双路径可用）
POST   /projects/{id}/experiments          （计划预注册 DRAFT→PREREGISTERED）
POST   /experiments/{plan_id}/archive      （归档裁决 409/404；无 queued 状态，不伪造队列）
```

## Notifications（WP-G）

```text
GET    /notifications?limit=               （outbox 事件白名单投影；无 payload 内容）
POST   /notifications/{event_id}/read      （已读 view-state 持久化；幂等）
```

- 事件流是真相；已读是 per-event view-state（控制面 SQLite，非 canonical 研究事实）。

## Memory（WP-A 起 SQLite 开发路径与 PG canonical 双支持）

```text
GET    /projects/{id}/memory               （WP-F；store 缺失 503 + scope_note）
POST   /memory/proposals                   （WP-F；完整 §8 门链直提交）
POST   /memory/proposals/{id}/decide       （未提供：域内无持久化 pending 提案）
DELETE /memory/{id}                        （WP-F；lifecycle 用例 + 幂等键）
```

- WP-F 语义修正：MemoryWriteProposal 是瞬态值对象，没有可裁决的持久化
  pending 状态；两阶段 decide 需要 proposal store + 迁移（未实现，避免伪
  造第二套事实源）。`curator_approved` 作为提案参数进入门链：
  schema → provenance（ledger.has_source 验证）→ contradiction →
  policy → tier/curator 门 → sanitize-before-commit →
  commit + MEMORY_PROPOSED/MEMORY_COMMITTED 事件。
- PLAN-20260914-049：policy 槽位注入 composition 装配的真实 PolicyEvaluator
  （NativePolicyEvaluator + `examples/config/policy.yaml`）。`memory.write`
  按 tier 声明（`_GATE_CAPABILITY_SCOPES` 多 scope 门链能力）：默认四个 tier
  都是 allow（行为与接线前一致），运维可在 policy.yaml 对某 tier 收紧为
  deny / require_approval —— 收紧后提案在 policy 阶段被 422 拒绝，reason
  可读（如 `policy deny: matched deny rule`）。policy.yaml 缺失/不可解析时
  evaluator 为 None，门链不伪造默认策略（退回 provenance + curator 兜底）。

## Policy（只读快照，PLAN-20260914-049 WP-C）

```text
GET    /policy/capabilities                （声明规则 + 门链能力逐 scope 有效判决）
```

- 判决由控制面运行期实际使用的同一 PolicyEvaluator 计算（同代码路径，不做
  第二套判定）；actor 不参与规则匹配（仅 capability/action/scope），响应 note
  显式说明。
- 只读：无规则 CRUD（策略变更是 policy.yaml 的版本化改动 + 重启）；policy
  未加载 → 503（不伪造快照）。

## Event Stream

```text
GET /runs/{id}/stream       # 未提供：SSE 实为 GET /runs/{id}/events
WS  /runs/{id}/ws           # 未提供：无交互通道；投影轮询即 events SSE
```

事件支持 cursor/resume，客户端按 event_id 去重。SSE 与 JSON replay 共用
`GET /runs/{id}/events`（Accept 分流；Last-Event-ID / ?cursor= 续传）。

## Identity / Governance（未提供；M18 deferred）

```text
GET  /me                                   （未提供：单用户控制面无 principal 概念）
GET  /organizations/{id}/members           （未提供）
POST /projects/{id}/memberships            （未提供）
GET  /projects/{id}/data-policy            （未提供）
PUT  /projects/{id}/data-policy            （未提供）
POST /projects/{id}/export                 （未提供：run 级走 GET /runs/{id}/export）
POST /projects/{id}/delete-request         （未提供）
```

所有资源查询必须按 principal/scope 授权，不依赖前端隐藏按钮。

### M16 Cluster（只读投影）

- `GET /cluster/workers` — worker 集群视图：`worker_ref`（worker_id 的
  sha256 短 digest，原始 id/凭据不出控制面）、state（WorkerState）、
  protocol/runtime 版本、generation、drain 标记、服务端时间的心跳。
- `GET /runs/{id}/placement` — run 的 EXECUTION 任务与其 worker placement。
- registry 未配置 → 503（不伪装空集群）。Console（useCluster/ClusterPanel）
  只消费这两个端点，不直连 Worker。
