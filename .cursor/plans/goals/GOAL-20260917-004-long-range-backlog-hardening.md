---
id: GOAL-20260917-004
slug: long-range-backlog-hardening
title: 长程项加固：来源自足续跑、停车语义读面、失败策略消费者、失败语义 digest、派发读面与补偿、完整安全审计
status: ACHIEVED
created_at: 2026-09-17
updated_at: 2026-09-17
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-17 用户会话指令（goal 模式）：进入 goal 模式并**新建承接 GOAL-004**，把
    GOAL-20260915-003 收口时如实登记、但未随收口通过的长程项按优先级做成可独立验收的
    EC，之后由本驱动**自动化循环推进、无需逐轮确认**。承接关系 = GOAL-003
    「终止与收口 · BLOCKED 记录（2026-09-18）」的**恢复条件①**（新建承接 GOAL，把
    「仍未处理的长程项」8 项按优先级写进新 GOAL 的 EC）；GOAL-003 保持 BLOCKED 不动。
    push-to-main-for-CI 授权沿用 GOAL-001/002/003 的批准口径：只推 main、不 force、
    不重写历史、不推旁支触发 CI；push 前 `git pull --ff-only origin main`（必要时
    --rebase，始终不 force）。循环预算与纪律以本文件 frontmatter 为准（客户端自带的
    迭代/重试/超时上限一律让位于此）。
objective: >
  把 GOAL-003 收口登记的长程项从「登记表」变成「有真实消费者、可独立验收的能力」：
  重启续跑不再依赖外部协议文件仍在（来源自足）、运维读面能区分两种停车语义、
  `failure_policy` 有真实消费者、失败 run 与 `manifest.frozen` 事件同样带语义 digest、
  派发方锁粒度与统一读面可判定、`resume_paused` 失败不留悬空 RUNNING，并给完整安全
  审计一个可复核终态（扫描跑通 ⇒ 逐条处置；环境不可用 ⇒ 根因 + 配方 + 人工清单）。
exit_criteria:
  - id: EC-01
    criterion: >-
      重建的来源自足（后继入口第 2 项 / RECHECK-083 W-3）：run 启动时把协议正文
      （路径来源的受控模板内容；草稿来源的不可变修订内容）冻结进 run 行或内容寻址
      存储，使重启续跑**不再因为那份外部文件消失而拒绝**；同时不放宽既有漂移判据——
      冻结正文与记录 digest 不符（被篡改 / 被改写）仍必须拒绝且一次都不执行，
      外部文件被改动不得静默替换冻结正文。
    verify: >-
      e2e（真 SQLite + 真 run store + 注入时钟）：启动 run ⇒ 断点停车 ⇒ **移走/删除
      外部协议文件** ⇒ 换新 service 按来源重建 ⇒ 续跑至 `SUCCEEDED`、runtime 执行次数
      符合断点语义；反证：篡改冻结正文 ⇒ 拒绝且一次都不执行；持久化用例（SQLite 往返 +
      PG parity）证明冻结正文随 run 行落 canonical（或 CAS 引用可解析）；重建被拒时
      拒绝原因点名缺的是哪条事实（不笼统报缺文件）。
    status: PASS
  - id: EC-02
    criterion: >-
      读面区分两种 `PAUSED`（后继入口第 3 项）：运维读面能判定一个停车中的 run 是
      「重排停车（到期会自己走）」还是「用户暂停（不会自己走）」——判据来自 canonical
      事实（持久化的停车原因/到期事实），不是守护线程的进程内暂存；重建失败被放回
      `PAUSED` 的第三种来源要么可区分、要么明确归入其一并写进文档。
    verify: >-
      读面用例（SQLite 注入时钟）：重排停车 → 读面给出 reschedule 判定与下一到期事实；
      用户暂停 → 读面给出 user-paused 且无到期；PG parity 用例；读面在无 store / 未知
      取值时如实回答 UNKNOWN（不猜）；OpenAPI/文档与读面同源收敛。
    status: PASS
  - id: EC-03
    criterion: >-
      `failure_policy` 从「声明了没人消费」变成有真实消费者（后继入口第 4 项）：
      run 执行期的失败分支按 TaskContract 声明的策略取值行事（至少让 fail-fast 与
      重试/继续两类可判定），且「这一次消费了哪条策略」在 run/任务事实里可见；
      未声明策略时回落既有默认行为且行为不变。
    verify: >-
      反向搜索证据：`failure_policy` 至少一处**非解析**消费者（当前只有
      `packages/domain/tasks.py` 的字段声明）；用例：声明 fail-fast 的 run 在任务失败后
      不重发后续任务、声明重试的走既有重试链、未声明时行为与基线一致（回归对照）；
      策略归属在 run 事实/读面可见；受影响套件 + m0 绿。
    status: PASS
  - id: EC-04
    criterion: >-
      失败 run 与 `manifest.frozen` 事件的语义 digest（后继入口第 5 项 /
      RECHECK-083 W-1+W-2）：终态 `FAILED` 的 run 行与成功路径同判据地带上
      `manifest_semantic_digest`（当前 `run_from_execution` 的 `ValueError` 收敛分支
      只恢复 manifest digest 与定价引用）；`manifest.frozen` 事件 payload 也带该语义
      digest，使「从事件链重放 run 行」能补齐这项。
    verify: >-
      API 用例：收敛 `FAILED` 的 run 行语义 digest 非空、且与同协议成功 run 的判据一致；
      事件用例：`manifest.frozen` payload 含语义 digest 且与 run 行相等；重放一致性用例：
      由事件重建 run 行 ⇒ 语义 digest 相同；反证：去掉该字段 ⇒ 对应用例失败
      （避免「从不开火的守卫」）。
    status: PASS
  - id: EC-05
    criterion: >-
      锁粒度与统一派发读面（后继入口第 6 项）：① 控制面 SQLite 共享连接的锁粒度落到
      **每线程连接**（或等价机制），共享连接不再被跨线程并发使用；② worker claim 与
      retry dispatch 两个派发方有**统一读面**，能回答「这个 run 现在有没有活的派发方、
      是哪一个」（当前两处各管一半，没有一处答得出来）。
    verify: >-
      并发用例（真 SQLite，多线程写）：复现 cycle 7 的 12 线程 24 次 `POST /ops/schedules`
      场景 ⇒ 无 `InterfaceError`/404 类失败（反证：修复前该场景 2×500 + 2×404）；
      统一读面用例：worker claim 持有、retry dispatch 持有、两者皆无三种情形各有可判定
      答案；PG parity；文档 + 读面收敛。
    status: PASS
  - id: EC-06
    criterion: >-
      `resume_paused` 失败后的补偿（后继入口第 7 项 / RECHECK-082 W-3）：续跑失败路径
      不留悬空的 `RUNNING`——失败即补偿到可判定状态（放回 `PAUSED` 或等价），补偿本身
      可观测（原因可见）、可重入（补偿后再次续跑能成功），且不静默吞掉失败。
    verify: >-
      用例：注入 `resume_paused` 失败 ⇒ run 不停在 `RUNNING`，状态与失败原因可从 canonical
      事实读到；重入用例：补偿后再次续跑成功；反证：去掉补偿 ⇒ 用例失败（run 留 `RUNNING`）；
      API/读面与守护线程两条入口的补偿语义一致（或在文档中写明有意差异）。
    status: PASS
  - id: EC-07
    criterion: >-
      完整安全审计的可复核终态（后继入口第 1 项）：Mimosa 全量扫描（或等价的密封扫描）
      二选一终态——a) 扫描完整跑通 ⇒ findings **逐条处置**（修复或登记误报）并给出
      结论文本；b) 环境仍返回 `scanner_enobufs` ⇒ 先定位**根因**、给出**可复现配方**与
      **人工步骤清单**。两种终态都**禁止**宣称「项目安全」；未覆盖范围必须写明。
    verify: >-
      a) 扫描封印标识（scanId/seal）+ findings 处置表（每条：结论/依据/处置）+ 结论段；
      b) 根因定位证据（复现命令、原始日志、影响面）、可复现配方、人工步骤清单；
      两种终态都把「未覆盖范围」写进记录；本 EC 的 PASS 以其终态文档 + 证据为准，
      不以「扫描没报问题」为 PASS 依据。
    status: PASS
budget:
  max_cycles: 20
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更（含为判据引入新的图像/解析库——优先用现有依赖实现）
  - 同一失败签名超过 fix_policy 上限
  - 「按声明给 adapter 接线」与 `tool_pack.*`/脚本策略（后继入口第 8 项）——受控出网与产品决策，需用户或 ADR 拍板
child_plans:
  - .cursor/plans/tasks/PLAN-20260917-084-freeze-protocol-body-into-run.md
  - .cursor/plans/tasks/PLAN-20260917-085-parked-run-read-surface.md
  - .cursor/plans/tasks/PLAN-20260917-086-failure-policy-gets-a-consumer.md
  - .cursor/plans/tasks/PLAN-20260917-087-failed-run-semantic-digest.md
  - .cursor/plans/tasks/PLAN-20260917-088-per-thread-sqlite-connection.md
  - .cursor/plans/tasks/PLAN-20260917-089-unified-dispatch-ownership-read-surface.md
  - .cursor/plans/tasks/PLAN-20260917-090-resume-failure-compensation.md
  - .cursor/plans/tasks/PLAN-20260917-091-security-audit-terminal-state.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20260917-092-goal-004-closeout-recheck.md
memory_entries:
  - MEM-20260917-059
  - MEM-20260917-060
  - MEM-20260917-061
  - MEM-20260917-062
  - MEM-20260917-063
  - MEM-20260917-064
  - MEM-20260917-065
  - MEM-20260917-066
---

# GOAL-20260917-004 — 长程项加固（自迭代循环）

## 目标与退出标准

格式规范与循环 SOP 见 [README.md](README.md)。本 GOAL 是 GOAL-20260915-003
（BLOCKED，预算触顶 20/20）的**承接 GOAL**：按 GOAL-003「终止与收口 · BLOCKED 记录
（2026-09-18）」的恢复条件①建立，把该记录「仍未处理的长程项」8 项按优先级做成
可独立验收的 EC（第 8 项为 escalation 级，见「不进入循环 / 需人工拍板」）。

| EC | 后继入口 | 标准（摘要） | 验证 | 状态 |
| --- | --- | --- | --- | --- |
| EC-01 | 第 2 项 | 重建的来源自足（协议正文冻结进 run 行或 CAS） | e2e：删文件后仍能重建续跑 + 篡改反证 + 持久化往返 | **PASS**（cycle 1：PLAN-20260917-084 / RECHECK-084；详见下方 EC-01 注记） |
| EC-02 | 第 3 项 | 读面区分两种 `PAUSED`（重排停车 vs 用户暂停） | 读面用例（注入时钟）+ PG parity + 文档同源 | **PASS**（cycle 2：PLAN-20260917-085 / RECHECK-085；详见下方 EC-02 注记） |
| EC-03 | 第 4 项 | `failure_policy` 有真实消费者 | 反向搜索 + fail-fast/重试对照用例 + 回归对照 | **PASS**（cycle 3：PLAN-20260917-086 / RECHECK-086；详见下方 EC-03 注记） |
| EC-04 | 第 5 项 | 失败 run 与 `manifest.frozen` 事件的语义 digest（W-1/W-2） | API/事件/重放一致性用例 + 反证 | **PASS**（cycle 4：PLAN-20260917-087 / RECHECK-087；详见下方 EC-04 注记） |
| EC-05 | 第 6 项 | 锁粒度（每线程连接）+ 两个派发方的统一读面 | 并发反证场景 + 三态读面用例 + PG parity | **PASS**（① cycle 5：PLAN-20260917-088 / RECHECK-088；② cycle 6：PLAN-20260917-089 / RECHECK-089；详见下方注记） |
| EC-06 | 第 7 项 | `resume_paused` 失败补偿（不留悬空 RUNNING） | 失败注入 + 重入用例 + 反证 | **PASS**（cycle 7：PLAN-20260917-090 / RECHECK-090；详见下方注记） |
| EC-07 | 第 1 项 | 完整安全审计的可复核终态（二选一） | 终态文档 + 封印标识/findings 处置 或 根因+配方+人工清单 | PASS |

**EC-01 注记（2026-09-17 cycle 1）**：`ProtocolBody`（正文 + sha256，构造即校验）随启动
落 canonical；重建优先用冻结正文，外部文件/草稿修订消失不再阻断（API 面实测：
删除模板后 `continuation=REBUILT`，修复前为 `NONE` + `protocol file not found`）；
漂移判据未放宽（换一份自洽正文 ⇒ 语义漂移拒绝、一次都不执行）；拒绝原因点名两条事实。
范围注记（RECHECK-084 W-2/W-4）：旧 run（早于正文冻结）没有正文，重启续跑仍依赖来源
可解析；`protocol_body_digest` 非空不保证重建成功（目录/契约漂移仍拒绝）。

**EC-02 注记（2026-09-17 cycle 2）**：`WorkflowEngine.retry_schedule(run_id)` 把守护线程
的判据（`due_retry_task_ids`）升级成读面可用的同一句读（`scheduled`/`due`/`next_retry_at`，
分类在 adapter 内用权威时钟——与写 deadline、与调度器同一处）；控制面 `GET /runs/{id}` 与
列表新增 `paused_dispatch`：仅 `PAUSED` 非空，`kind ∈ {RETRY_SCHEDULED, USER_PAUSED,
UNKNOWN}`，`RETRY_SCHEDULED` 带 `next_retry_at` 与 `due_now`。判据只读 canonical 事实
（run 行状态 + 任务行 `RETRY_SCHEDULED`/`retry_at`），**没有新增"停车原因"字段**；读面
零时钟调用、不写任何状态。第三种来源（重建被拒后放回）**有意**归入
`RETRY_SCHEDULED + due_now=true`，拒绝原因不在读面——已写进 `docs/api/CONTROL_PLANE_API.md`
并登记为后继入口（RECHECK-085 W-1）。其余口径登记：读面按 run 聚合不回答"是哪条任务"
（W-3）、`next_retry_at` 不表达"迟到多久"（W-4）、`paused_dispatch` 不进事件流（W-5）、
Fake 无写 `RETRY_SCHEDULED` 路径故其读面恒空（W-2，已显式钉成用例）。

**EC-03 注记（2026-09-17 cycle 3）**：`failure_policy` 从"只有解析面"变成**有消费者 + 可点名**：
`TaskContract.failure_policy_view()` 返回冻结视图（`on_task_failure ∈ {FAIL_RUN(缺省), CONTINUE}`
+ `declared`/`unhonored`），取值非法 ⇒ `ValueError`；消费点在 `phase_runner.failure_step`——
三处失败（任务失败 / 结果畸形 / 验收门拒收）**唯一分叉**：缺省 = 既有隐式 fail-fast（逐字不变），
`CONTINUE` = 失败被容忍（`task.failed` 事件 + `TaskOutcome.failure_policy`）且剩余工作照跑，
跑完收敛 `DEGRADED`（此前无生产者的状态）并发 `run.degraded`（点名策略与失败清单）。
**未消费的键被点名**：`on_validation_failure`/`allow_partial_evidence` 在 `unhonored` 里，用例钉住
"声明它们不改行为"（消费 `on_validation_failure` 需要"完成后二次写任务行"，登记为后继入口）。
范围注记（RECHECK-086 W-2/W-3/W-4）：`DEGRADED` 的 HTTP 落库走既有 `state=outcome.state`
映射、未单独 e2e；被容忍失败不进 run 行（读清单走事件链）；`DEGRADED` 没有自动后续推进。

**EC-04 注记（2026-09-17 cycle 4）**：冻结语义在**失败收敛路径**上补齐。`manifest.frozen`
payload 增 `semantic_digest`（排除 `frozen_at`；与 `digest` 同一 producer
`RunManifest.semantic_digest()`）；执行期 `ValueError` 收敛分支不再自己拼字段——改为唯一的
payload→引用映射 `FrozenManifestRefs.from_payload(...).apply(run)`，`apply` 内部走
**成功路径同一个** `ResearchRun.with_manifest(...)`（"同判据" = 同一 producer + 同一域方法）。
读面 `GET /runs/{id}`（与列表）新增 `manifest_semantic_digest`。**判据落地为四件可复核事实**：
① 收敛 FAILED 的行与成功路径共用同一个断言函数（非空、`sha256:` 前缀、`!= manifest_digest`）；
② 事件 payload 的语义 digest 与行相等；③ 只凭事件链能把行的四项冻结引用（快照/语义/定价版本/
定价 digest）原样重建；④ 漂移守卫真的消费它——带对的值 ⇒ 不再被 `lacks a semantic digest`
挡住并一路走到执行，换成别的值 ⇒ `drifted` 拒绝。**反证双跑**：去掉事件 payload 键 ⇒ 7 红、
去掉收敛分支的语义 digest 参数 ⇒ 3 红（失败文本正是改动前的
`frozen manifest lacks a semantic digest`）。反证还暴露一处**假绿**（重放用例在"两侧同为
None"时相等成立）——已把"重放出来的值非空"钉进断言，判据只增强。
范围注记（RECHECK-087 W-1/W-2）：旧 `manifest.frozen` 事件没有该键 ⇒ 那些 run 读回 None
且**不回填**（重建仍被守卫拒绝，与今天一致）；"重建后续跑在执行期再失败"的结局仍属 EC-06。

**EC-05 注记①（2026-09-17 cycle 5，部分交付）**：控制面**文件库**路径的连接粒度换成
**每线程一条**（`adapters/sqlite/pool.py::ThreadLocalConnection`）：store 拿到的仍是同一个
句柄，但一切连接入口转发到本线程自己的连接（懒创建，WAL + `busy_timeout` 同 `db.connect`），
`with conn:` = 本线程事务块，`ApiDeps.close()` 走 `close_all()`；`:memory:` 仍共用一条
（SQLite 语义：内存库属于连接）并在用例里显式钉住。证据：池单测 5 条、12 线程 24 次
`POST /ops/schedules` 在**内存/文件两路径**都 24×201 无 5xx/404、`tests/api` 全量 420 例
（夹具统一走池 ⇒ ~30 个 store 的代理面兼容回归）、定向复跑 1371 passed、live e2e 36 绿。
**诚实边界（RECHECK-088 W-1…W-4）**：cycle 7 的 1×404 在 hermetic harness **不可复现**，
本轮不宣称"404 已修"；代理面是鸭子类型（mypy 在装配边界 cast，覆盖靠套件）；池不做线程
死亡回收；**统一派发读面（②）仍未做**——EC-05 因此保持 PENDING。

**EC-05 注记②（2026-09-17 cycle 6，交付完成）**：`WorkflowEngine.dispatch_ownership(run_id)`
成为**统一派发读面**——一个调用同时给出重排读面（`RetrySchedule`，与 `retry_schedule` 同一列
同一判据、同一个 `now`）与**活**租约持有者（`LeaseHolder`：`task_id`/`worker_id`/`fence`/
`expires_at`，**不含 `lease_id`**），并组合成 `kind ∈ {NONE, RETRY_DISPATCH, WORKER_CLAIM,
BOTH}`；三实现（Fake/SQLite/PG）同判据，控制面 `GET /runs/{id}`（与列表）新增 `dispatch`
字段（读不到 ⇒ `UNKNOWN`，不猜 `NONE`）。**"活"= 回收判据的补集**（未过期且持有者不是 LOST
worker），由 adapter 用权威时钟判定，两个持久化实现的用例都在**同一个测试里**同时断言
"读面说不活的，回收就该动手"。`paused_dispatch`（EC-02）改为消费**同一次读**的 `PAUSED`
投影——取值与语义逐字不变，两个字段不再可能各说各话。证据：契约套件（3 实现）、SQLite
注入时钟 7 条（过期/边界秒/LOST/控制面自持/重排/BOTH）、PG parity 4 条、API 7 条
（三态 + BOTH + UNKNOWN + 列表同判 + 只读性）、**反证三跑**（过期判据/LOST 判据/路由器装配，
分别 2/2/7 红）。**诚实边界（RECHECK-089 W-1…W-6）**：`ClaimRequest.lease_ttl_seconds` 三个
实现都未消费（既有 port 漂移，实测撞到）；列表路径每 run 一次读（N+1）；读面不回答持有者
健康度（心跳/进度/卡死不在读面）；Fake 无过期语义（"活"= 仍在租约表里）；PG 两读不构成
跨表快照；`WORKER_CLAIM` 词表也覆盖 `worker_id=None` 的控制面自持租约（靠 `holder.worker_id`
区分，已写进文档）。EC-05 两半（① 每线程连接 cycle 5、② 统一读面 cycle 6）由此**全部交付**。

**EC-06 注记（2026-09-17 cycle 7）**：`resume_paused` 失败不再留悬空 `RUNNING`。反向搜索
确认的机制：`service.resume_paused` **先 pop 上下文再执行** ⇒ 执行抛错后上下文已丢；API 面异常
外冒（run 留 `RUNNING`，而 `PAUSED → RUNNING` 迁移会 409 ⇒ 除人工改库外无入口能再推进它），
守护线程面 `except Exception: return 0`（如实注释但同样不补偿）。**补偿只有一处**
（`run_terminals.compensate_failed_resume`）：走既有域迁移 `PAUSE` 放回停车，并发
`run.resume_failed`（payload：`failure_type`/`message`/`compensated_to`）——事件链是原因的
canonical 记录，**读面不新增"停车原因"字段**（与 EC-02 口径一致）。两条入口共用它，差别只在
由谁落库：API 面多一种如实结局（`continuation=FAILED` + 原因 + `dispatch=HELD`），守护线程面
补偿后继续服务本轮其余 run。**补偿不是终局**：撤掉故障后同一入口能真的把它续起来（用例里跑到
`RUNNING`）。证据：API 4 条（补偿 + 事件 payload + 可重入 + 既有重建/竞态回答不变）、调度器
2 条新增（补偿写回序列 `[RUNNING, PAUSED]`、下一轮 pass 真的续跑成功）、**反证两跑**（各 2 红）。
**诚实边界（RECHECK-090 W-1…W-5）**：`resume_after_approval` 是同形未修入口（停在
`WAITING_FOR_APPROVAL`，不在本 EC 判据内）；进程内上下文不复活（重入走 durable 重建，没有冻结
正文的旧 run 会被诚实拒绝）；失败原因无任务级归因（只有异常类型/文本）；守护线程补偿失败静默
降级（既有"不拖垮整轮"约定）；API 响应仍是 200（以 `continuation` 判别结局）。

**EC-07 注记（2026-09-17 cycle 8）**：走**终态 a**——独立密封深扫首次跑通（hook 侧
`scanner_enobufs` 依旧，两条通道不互相抵消）。扫描标识：`scan-2026-09-17T20-05-18.700Z-663d0976701f`，
seal `sha256:b2af673997a765567d519bc4aee226c861deac1a6c6ec7dc76e87f69a0610347`，
depth=deep，`runStatus=inconclusive` / `completeness=partial`（**该扫描器在本仓库的常态**：
同 projectId 连续 6 次深扫剖面逐次相同 3/28/5，与 `docs/audits/PA1_MIMOSA_REVIEW.md`
两次记录同口径），36 findings = high 3 / medium 28 / low 5。**逐条处置**（每条：结论/依据/处置）
落在 `docs/audits/MIMOSA_DEEP_SCAN_20260917.md`：1 条产品代码 HIGH（`yaml.load`）经代码行 +
3 个已执行用例判**误报**（加载器是 `yaml.SafeLoader` 子类，且「危险 tag 不执行」被用例钉住）；
2 条 HIGH 落在**未跟踪**的第三方转储目录（`git ls-files artifacts/` = 0、`.gitignore:36`、
`git log --all` 为空）；27 条 MEDIUM 是同一静态污点启发式（把 env→**连接目标**读成
env→**SQL 文本**），判误报的依据是产品树全量动态 SQL 形态检索**零命中 + 反证**（同一模式对
四种蓄意形态命中、对参数化写法不命中）+ 汇点逐行核对；1 条 MEDIUM（worker GPU 镜像 env）
污点汇实为 `tempfile.mkdtemp`，另有已执行用例断言该 env 不进沙箱子进程；5 条 LOW 是 M12
参考实验的固定 seed。**证据可复核性**：三件产物逐件 sha256 与 `seal.json.artifacts` 全部一致
（聚合 `digest` 的合成属扫描器内部，明确**不宣称**可复算）；可复跑配方与未覆盖范围
（静态-only、threatModel 0 入口/0 主体/0 授权面、业务逻辑候选 0、validation investigated 0、
依赖 advisory 命中 1 条**未署名**未决、扫描输入含 gitignored 目录）同文记录。
**本 EC 的 PASS 不以「扫描没报问题」为依据，也不主张项目安全。**

**后继入口 ↔ EC 映射与取舍**：第 1 项（完整安全审计）在 GOAL-003 记录里就被标注为
「运维动作，不在循环内可完成」——本 GOAL 把它**单列**为 EC-07，判据容纳两种合格终态，
不做成循环主线（derive 顺序取 EC 表首个 PENDING，故 EC-07 只在循环空档或有新证据时
推进）。第 2…7 项各成一条 EC，编码顺序按 GOAL-003 的建设优先级（第 2 项优先）。

**基线继承**：GOAL-003 的 RECHECK-083（PASS_WITH_WARNINGS）告警 W-1/W-2 → EC-04、
W-3 → EC-01；本 GOAL 不重新解释告警，只把「已量成事实的缺口」做成判据。

**不变量（沿用 GOAL-001/002/003 与 AGENTS.md）**：不伪装实现（不注册没人消费的写面、
不让 fixture 冒充业务数据）；默认 deny 的安全姿态不变；观测隐私不变（不记录完整
Prompt/模型输入输出）；每一项写面走既有 policy/preflight 门链；**判据只允许增强，
不允许为了让测试通过而削弱**；Canonical State 边界不变（PostgreSQL Domain Entity 是
业务真相，CAS/索引只能是可重建的派生面或**明示**的 run 事实）。

**规模标注**：EC-01 为 L（跨 domain/adapters/API + 迁移语义）、EC-05 为 M/L
（并发正确性 + 读面收敛）、EC-03 为 M（策略语义 + 回归面）、EC-04 为 S/M、
EC-02 为 M、EC-06 为 S、EC-07 为 M（运维/审计，进度不由本循环独占）。

## 循环入口协议

按 README 的 7 步判定执行，一切状态以「文件 + 工作树 + 远端实况」为准：

1. 本文件 `status != ACTIVE` → 只输出终止摘要（ACHIEVED/BLOCKED/ABORTED + 依据），本轮不做改动。
2. 迭代日志最后一行判定续点：无记录 → 开 cycle 1（执行 ①）；有子 PLAN 在
   IN_PROGRESS → 继续 ②；本地验证已过、有未推送 commit → ④⑤；CI 未记录结论 →
   ⑤（等待/判定，禁止猜测绿）；CI 有失败且未达上限 → ⑥。
3. 每 cycle 收口必须：CI 终态已记录 + 本文件（迭代日志/EC 状态/child_plans/
   latest_recheck/状态历史）已回写；未收口不得开新 cycle。
4. 进入 cycle 时在迭代日志声明 `driver=client-goal` / `owner=root-agent`；另一驱动
   持有未收口 ACTIVE cycle 时等待，不并发双写。

当前续点：**本 GOAL 已收口（ACHIEVED）**——七个 EC 全 PASS + 收口复检 `RECHECK-20260917-092`
（PASS_WITH_WARNINGS）+「终止与收口」已写。按循环入口协议第 1 条，后续触发只输出终止摘要、
不再做改动；仍未处理的长程项见「收口结论」表，由后继 GOAL 承接。

## 驱动

驱动无关（README「驱动适配」）：本实例由客户端 goal 模式驱动（每轮触发 = 一次入口
协议），亦可换会话/定时驱动；仅当 `status=ACTIVE` 时推进。同一时刻仅一个驱动推进。

## 单 cycle SOP

按 README ①~⑦ 执行。本实例附加约定：

- ① derive 主题顺序：EC 表首个 PENDING；若上一 cycle 部分交付，以其「下一轮输入」为准。
  子 PLAN 必须独立可验收、独立 RECHECK（`.cursor/plans/rechecks/`），frontmatter 带
  `parent_goal: GOAL-20260917-004` 并投影 ALL_PLAN。
- ② 按子 PLAN 的 WP 推进，**每 WP 独立 commit**（显式路径；并发工作树，禁 `git add -A`）。
- ③ 本地验证：`make validate-all` 全量 23 项（DSN 固化配方）+ 受影响定向套件 + web 门
  （lint/typecheck/unit/build/stub e2e/live e2e）；页面改动时按既有流程重生成设计基线
  与结构签名（`UPDATE_OUTLINES=1 pnpm exec playwright test design-fidelity -g 结构签名`，
  跨平台一致性用既有容器配方复核）。本地不绿不得 push。
- ④ 子 PLAN 收口（RECHECK DONE）后 GOAL 记录 commit 列表。
- ⑤ `git pull --ff-only origin main`（必要时 --rebase，不 force）→ `git push origin main`
  → 按本机口径查 m0-quality 最新 run（无 gh CLI：`git credential fill` 取已存令牌走
  GitHub REST API，按 head_sha 匹配 + `/jobs` 读六个 job 结论）→ 轮询到终态并记录
  run 链接与结论。只改 `.cursor/**` 的记录提交同样触发六 job CI，按同口径等待。
- ⑥ 按「CI 失败分类与纠错」处置；修复以独立 commit 落 main 并回到 ⑤。
- ⑦ 回写本文件：迭代日志（含 driver/owner 声明行）、EC 状态、child_plans、
  latest_recheck、状态历史；未达终态且未触顶 → 直接进入下一 cycle ①。
- **未实跑不得记 PASS**；本机无法验证记 PENDING 并停止推进，不猜测绿。

## CI 失败分类与纠错

按 README 分类表执行；本仓已知 flake/env 签名（重跑不修，先排除环境干扰）：
observability OTLP teardown race（stopped receiver 端口）、m0 全量单跑在负载下的 timing
用例（隔离复跑对照）、DSN 注入（需固化配方：`RESEARCHOS_POSTGRES_DSN` 指向 test DSN、
其余 DSN 键清空，防 litellm `load_dotenv` 注入 operator `.env`）、
`framework/run_cursor_framework_evals` 在 Windows 上偶发文件占用（复跑对照）、
**kill 后台 m0 会留孤儿 pytest**（复跑前先确认无残留进程/容器，否则污染下一轮）。

`.github/workflows/m0-quality.yml` 属治理面：循环内不修改；需要改动即 BLOCKED 提请人工。
账户级计费阻断（runner_id=0、无 step、2 秒结束）非代码缺陷：不推进 cycle，恢复后先复核
`runner_id != 0` 再回填结论（GOAL-003 cycle 1 的处置模板）。

## 终止与收口

- **ACHIEVED**：EC-01…EC-07 全 PASS 且有实跑证据 + 收口 RECHECK（独立复检，
  `result: PASS` 或 `PASS_WITH_WARNINGS`）+ 本文件 `latest_recheck` 指向该 RECHECK +
  「终止与收口」写明收口结论（含仍未处理项，如有）。
- **BLOCKED**：`budget.max_cycles` 触顶、或 `no_progress_stop_cycles` 连续命中、
  或命中 `escalation_triggers`（含后继入口第 8 项）。写 BLOCKED 记录（原因/EC 状态表/
  收口复检/安全扫描处置/恢复条件/仍未处理的长程项），恢复条件由用户拍板。
- **ABORTED**：用户显式终止本目标。

收口时必须把「仍未处理的长程项」如实登记为后继入口（不隐藏缺口），并给出恢复条件
（新建承接 GOAL 或显式变更 budget 并置回 ACTIVE）。

### 收口结论（2026-09-17，cycle 9）

**status = ACHIEVED**。七个 EC 全 PASS 且经独立复检（`RECHECK-20260917-092` =
PASS_WITH_WARNINGS）在**当前树**上重新验证：`scratch/verify_goal004_closeout.py` 的 **46 条
断言全 PASS**（含 15 个定向套件**真跑**：域/SQLite/API/e2e/application/postgres）；
本 GOAL 的 **44 个 commit → 16 个 CI run 逐 job 重读**：#134…#147 每个 run 六个 job 全 success，
唯一失败 **#133**（建档 run，`collector-quality`）是**测试墙钟依赖**，同 cycle 内以「改夹具、
不改断言」修复（`5607992` → #134 全绿）；#137 此前未进台账，本轮**补记**。

收口后**仍然开放**的长程项（后继 GOAL 承接，不在本文件内隐藏）：

| # | 长程项 | 来源 |
| --- | --- | --- |
| 1 | **安全审计残留**：依赖 advisory 1 条**未署名未决**（需联网复核）；hook 侧 `scanner_enobufs` 未被消除（独立密封深扫是替代通道）；扫描输入含 gitignored 内容（19/36 条落在 `scratch/`+`artifacts/`）；`artifacts/` 内含**未跟踪**明文 token 文件（从未提交）；威胁建模/授权面/业务逻辑**零覆盖**（越权、BOLA/BFLA 不在射程） | EC-07 / RECHECK-091 W-1…W-5 |
| 2 | **同形未修入口**：`resume_after_approval` 也是「先 pop 后执行」，失败同样不补偿（只是停在 `WAITING_FOR_APPROVAL`） | RECHECK-090 W-1 |
| 3 | **策略面仍有未消费项**：`on_validation_failure` 声明了没有消费者；`ClaimRequest.lease_ttl_seconds` 声明了无人读 | RECHECK-086 W-1 / RECHECK-089 W-1 |
| 4 | **读面语义边界**：`dispatch_ownership` 不回答持有者健康度；PG 两读不构成快照；Fake 无过期语义；`WORKER_CLAIM` 也覆盖控制面自持租约；列表路径每 run 一次读（N+1） | RECHECK-089 W-2…W-6 |
| 5 | **失败 run 的重建执行期结局**：判据停在冻结语义守卫，`FAILED → 重建` 之后仍可能再次失败 | RECHECK-087 W-2 |
| 6 | **历史行不可追溯**：正文冻结只在启动路径产生（旧 run 无正文、需重建被拒）；旧 `manifest.frozen` 事件无 `semantic_digest` 键，不回填 | RECHECK-084 W-2 / RECHECK-087 W-1 |
| 7 | **补偿的诚实边界**：守护线程补偿失败静默降级（不拖垮整轮）；API 失败仍 200（以 `continuation` 判别）；失败原因只有异常类型/文本，无任务级归因；进程内暂停上下文不复活 | RECHECK-090 W-2…W-5 |
| 8 | **450 行硬上限持续贴线**：`run_orchestration/service.py` 450/450——后续任何改动都要**先搬代码**（本 GOAL 已两次以搬代码收口） | RECHECK-086 W-5 |
| 9 | **同类时钟/时序风险只做了 grep 排查**（12 个注入时钟的 PG 用例文件里只改了 1 个，其余按「未观测到失败」保留） | RECHECK-084 W-5 |

**后继 GOAL 的入口** = 从本表任选主题（建议优先级：① 安全审计残留的**联网复核**与
干净 checkout 上的重扫；② 同形未修入口 `resume_after_approval`；③ 声明未消费项清账
（`on_validation_failure` / `lease_ttl_seconds`））。

**不进入循环 / 需人工拍板（原样保留）**：见下一节。

## 不进入循环 / 需人工拍板

**后继入口第 8 项（escalation 级，不在本 GOAL 的 EC 内）**：
「按声明给 adapter 接线」（组合根仍注入 FakeAgentRuntime；OpenHands adapter 已建未接线，
方向是 runtime 可配置而非删 Fake）与 `tool_pack.*`/脚本策略（受控出网、产品决策、可能
触及 Accepted ADR 与核心安全策略）。本循环**不得自行决定**：一旦发现 EC-01…EC-07 的
实现必须改动这两项才能继续，按 `escalation_triggers` 立即置 `status: BLOCKED` 并留
人工决策；可选动作只限「如实登记 + 给出选项与影响面」，不含实现。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 建档（本文件 + GOAL-003 事实更正行；driver=client-goal / owner=root-agent） | `7c0d9f2` | `.cursor/skills/governance-check/scripts/validate.py` 绿（本机实跑） | run **35203036505**（7c0d9f2）：**failure**——仅 `collector-quality` 红，2 条 PG 退避用例断言失败（其余五 job success） | 定位为**测试墙钟依赖**（非本提交缺陷）：夹具注入固定引擎时钟却用 SQL `now()` 挪 deadline，CI 墙钟越过 `START` 后必红；修复提交 `5607992`（夹具改用引擎时钟，断言未改）→ run **35204710864 六个 job 全 success** | EC-01…EC-07 全 PENDING | cycle 1 = EC-01（来源自足续跑：协议正文冻结进 run 行或 CAS） |
| 1 | PLAN-20260917-084（来源自足续跑：`ProtocolBody` 冻结进 run 行 + 重建只认它） | `3d9cc73`（WP-A 域/装配/两个 store）、`87c2d86`（WP-B 重建/读面/用例）、`5141e06`（WP-C 记录 + 契约快照 + 文档） | 定向：api **9** / e2e **5** / domain **4+13** / sqlite **4** / pg **3** 全 passed；契约 `test_openapi_snapshot.py` **8 passed**（DTO 新增字段后重生成快照 +11 行）；web 门（lint/typecheck/unit/build/web-*）全绿；m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3773 passed / 10 skipped**，497.96s；首轮 m0 红 2 处——契约快照漂移 + web 夹具缺字段——均为本改动引入、已修后复跑全绿） | **CI**：记录提交 `5141e06` → run **35211094454 六个 job 全 success**（collector-quality / eval-gate / console-frontend / container-quality / quality-ubuntu-latest / quality-windows-latest，无重跑）；另：WP-A/WP-B 提交经 `5141e06` 的同一棵树覆盖验证（CI 只跑 head） | 首轮 m0 红 2 处（契约快照漂移 + web 夹具缺字段），均为本改动引入、已修 | EC-01 **PASS**（RECHECK-084）；新发现 W-1：重建"没有剩余工作"的 run 会退化成重跑全部并收敛 `FAILED`；EC-02…EC-07 PENDING | cycle 2 = EC-02（停车语义读面：PLAN-20260917-085 已建档） |
| 2 | PLAN-20260917-085（停车语义读面：`retry_schedule` 读面 + `paused_dispatch`；driver=client-goal / owner=root-agent） | `9b163cf`（WP-A：port `RetrySchedule` + SQLite/PG/Fake + 单测/PG parity/契约）、`fd8654f`（WP-B：`run_pause_view` + DTO/OpenAPI/web 类型 + 文档）、`98569c1`（PG 分类挪进 projections：450 行硬上限）、`c2cdc98`（WP-C：API 用例）、`f62bda4`（格式）、`8da4b13`（RECHECK-085 + MEM-060 + GOAL/ALL_PLAN） | 定向：sqlite **6** / pg parity **5**（pinned DSN，实跑非 skip）/ 契约 **8** / API **7** / OpenAPI 快照 **8** 全 passed；受影响广度复跑 **1137 passed / 2 skipped**；web 门全绿（unit **76** / stub e2e **83** / live e2e **36**）；m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3804 passed / 10 skipped**，485.85s）。首跑 10 红经隔离复跑判定为**环境并发污染**（被 kill 的上一轮留下孙子 pytest 进程共享 test DB/容器），清理后 23/23 | **CI**：head `7316d1d`（`2dbf3c7` 记录提交 + WP 提交 + `8da4b13` 记录提交，同一棵树）→ run **35219834215 六个 job 全 success**（collector-quality / eval-gate / console-frontend / container-quality / quality-ubuntu-latest / quality-windows-latest，runner_id 非 0，无重跑） | 首跑 m0 红 10 处 = 环境并发污染（非本改动；隔离复跑该 PG 文件 5 passed 为判据）；`python/format-check`/`python/typecheck`/450 行硬上限三处为本改动引入、已修 | EC-02 **PASS**（RECHECK-085，W-1…W-5）；EC-03…EC-07 PENDING；候选下一 cycle：EC-03（`failure_policy` 消费者）或 RECHECK-084 W-1（"没有剩余工作"的重建语义） | cycle 3：derive 取 EC 表首个 PENDING（EC-03 = `failure_policy` 真实消费者），先做反向搜索确认真实缺口 |
| 3 | PLAN-20260917-086（失败策略的消费者：`on_task_failure` 消费 + DEGRADED 落点 + 未消费键点名；driver=client-goal / owner=root-agent） | `2a014ad`（WP-A 域视图）、`7896525`（WP-B 消费/事件/e2e/文档 + 词表门禁同步）、`652e712`（450 行/50 行硬上限的搬移重构）、`1c280b2`（RECHECK-086 + MEM-061 + GOAL/ALL_PLAN） | 定向：domain **5** / application **6** / e2e **2**（新增）+ 受影响套件复跑 **977 passed**；事件词表门禁 **14 passed**；mypy 906 files 绿；m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3823 passed / 10 skipped**，511.99s）。首跑 m0 红 2 处 = `phase_runner.py` 456 行 + `_execute_group` 61 行、`service.py` 483 行（均为本改动引入、已搬代码修复） | **CI**：head `186963c`（`2a014ad`/`7896525`/`652e712` 三个 WP 提交 + `1c280b2` 记录提交 + `186963c` 迭代日志回填，同一棵树）→ run **35227784813 六个 job 全 success**（collector-quality / eval-gate / console-frontend / container-quality / quality-ubuntu-latest / quality-windows-latest，runner_id 1000006747…1000006752，无重跑） | 事件词表门禁先红（新增 2 个事件类型）⇒ 补词表与清单，断言未改；组合复跑的 3 条 PG 假红 = 手工顺序把 `tests/api` 排到 `test_pg_crash_restart` 之后（非产品缺陷，隔离复跑 + m0 全量为判据） | EC-03 **PASS**（RECHECK-086，W-1…W-5）；EC-04…EC-07 PENDING | cycle 4：derive 取 EC 表首个 PENDING（EC-04 = 失败 run 与 `manifest.frozen` 事件的语义 digest），先反向搜索确认 `run_from_execution` 的 ValueError 收敛分支与事件 payload 现状 |
| 4 | PLAN-20260917-087（失败 run 的冻结语义 digest：事件 payload 带语义 digest + 收敛分支走同一个 `with_manifest`；driver=client-goal / owner=root-agent） | `1831841`（WP-A 事件 payload + EVENT_MODEL）、`028abf3`（WP-B 收敛路径 + `FrozenManifestRefs` + DTO/OpenAPI/web 类型与夹具 + CONTROL_PLANE_API）、`65d1ebd`（WP-C API 用例 7 条）、`a3ccc66`（复跑抓到的类型收窄修复） | 定向：`tests/api` **418 passed**（新增 7）+ 新增应用用例 **3 passed**；`tests/domain tests/application tests/contracts tests/postgres tests/e2e` 复跑 **1629 passed / 4 skipped**（197.19s）；web 门全绿（lint 0 error / typecheck / unit **76** / build / stub e2e **83** / live e2e **36**）；**反证双跑**：去掉事件 payload 键 ⇒ **7 failed / 3 passed**、去掉收敛分支的语义 digest 参数 ⇒ **3 failed / 4 passed**（失败文本 = 改动前的 `frozen manifest lacks a semantic digest`）；m0 首跑 24/25（唯一红项 = MEM-062 引用的 RECHECK-087 尚未写入的记录顺序问题，非产品缺陷）⇒ 补齐记录后复跑又暴露 `python/typecheck` 的 `str | None` 收窄问题（`Digest.parse` 收到 `str | None`，已恢复显式判空并删掉未被消费的 `frozen` 属性）⇒ 第三次实跑 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3835 passed / 10 skipped**，477.88s） | **CI**：head `13054a8`（`1831841`/`028abf3`/`65d1ebd`/`a3ccc66` 四个 WP/修复提交 + `13054a8` 记录提交，同一棵树）→ run **35238057745 六个 job 全 success**（collector-quality / eval-gate / console-frontend / container-quality / quality-ubuntu-latest / quality-windows-latest，runner_id 1000006862…1000006867，无重跑） | 反证暴露一处**假绿**：重放一致性用例在"两侧同为 None"时相等成立 ⇒ 已把"重放值非空"钉进断言（判据只增强）；首跑"守卫放行"用例报 `drifted`，用临时探针定位为**用例替身** `_park` 漏复制定价引用（守卫正常工作），修替身而非改产品/断言 | EC-04 **PASS**（RECHECK-087，W-1…W-5）；EC-05…EC-07 PENDING | cycle 5：derive 取 EC 表首个 PENDING（EC-05 = 锁粒度每线程连接 + worker claim/retry dispatch 的统一派发读面），先反向搜索确认控制面 SQLite 共享连接的当前用法与两个派发方各自读到的事实 |
| 5 | PLAN-20260917-088（EC-05 第①半：控制面每线程一条 SQLite 连接；driver=client-goal / owner=root-agent） | `64d668a`（`ThreadLocalConnection` + `_open_sqlite`/`close_all` 装配 + 夹具统一走池 + 池单测 5 + 负载用例 2） | 定向：池单测 **5 passed** / 负载用例 **2 passed**（内存 + 文件两路径）/ `tests/api` **420 passed** / `adapters-sqlite+application+contracts+e2e+postgres` 复跑 **1371 passed / 4 skipped**（213.47s）；mypy **911 files** 绿；live e2e **36 passed**（真 app + 文件库）；m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3846 passed / 10 skipped**，510.93s；首跑红 1 处 = `conftest.make_base_deps` 54 行撞 50 行/函数硬上限 ⇒ 拆出 `tests/api/base_fixtures.py`（`121246c`）后复跑全绿） | **CI**：head `d8c9377`（`64d668a` 池/装配/用例 + `121246c` 夹具拆分 + `d8c9377` 记录提交，同一棵树）→ run **35245282964 六个 job 全 success**（collector-quality / eval-gate / console-frontend / container-quality / quality-ubuntu-latest / quality-windows-latest，runner_id 1000006994…1000006999，无重跑） | Mimosa 把 `__getattr__` 之前的显式转发方法（`execute(self, sql, ...)`）误报成 SQL 注入 ⇒ 改成委托式代理面（少写 N 个转发方法，也把误报消除）；夹具默认 `:memory:` 不覆盖每线程连接 ⇒ 另加文件库夹具的负载用例；池不是 `sqlite3.Connection` 子类 ⇒ 装配边界 cast（mypy 看不到鸭子类型） | EC-05 **部分交付**（① 交付并验收，② 统一派发读面待做）⇒ EC-05 保持 PENDING；cycle 7 的 1×404 在 hermetic harness 不可复现（不宣称已修） | cycle 6 = PLAN-089（EC-05 ②：worker claim 与 retry dispatch 的统一派发读面 + 三态用例 + PG parity），先反向搜索两家当前各自能读到什么、lease 事实在哪些表里 |
| 6 | PLAN-20260917-089（EC-05 第②半：统一派发读面 `dispatch_ownership` + `dispatch` 字段；driver=client-goal / owner=root-agent） | `07213ee`（WP-A：port `DispatchOwnership`/`LeaseHolder` + SQLite/PG/Fake 三实现 + 契约套件 + SQLite 注入时钟单测 + PG parity）、`48fe31d`（WP-B：DTO/视图/路由器 + OpenAPI 快照 + web 类型与夹具 + CONTROL_PLANE_API/PORTS + 7 条 API 用例）、`925ac6c`（修复：PG 引擎 479 行 ⇒ 搬 `projections.py`/`db.py`；3 处 mypy；两条断言按反证增强） | 定向（DSN 固化配方，PG 实跑）`api+contracts+adapters+application+e2e+postgres` **2108 passed / 7 skipped**（347.66s）；`test_python_source_limits` **927 passed**；mypy **917 files** 绿；web 门全绿（lint / typecheck / unit **76** / build / stub e2e **83** / live e2e **36**）；**反证三跑**：① 去掉过期判据 ⇒ SQLite/PG 各 1 红、② 去掉 LOST 判据 ⇒ 各 1 红、③ 去掉路由器装配 ⇒ 新 API 用例 **7 红**（首跑 5 红 ⇒ 两条“两侧相等”用例假绿 ⇒ 补“先钉住读面真的答了”后复跑 7 红）；m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3887 passed / 10 skipped**，521.87s；首跑 2 红 = 3 处 mypy + PG 引擎 450 行硬上限，均本改动引入 ⇒ 修类型 + 搬代码；第二次复跑唯一红项 = MEM-064 frontmatter 的 YAML 引号 ⇒ 修复后第三次实跑全绿） | 首跑 m0 红 2 处（类型/行数，均本改动引入）；反证暴露一处**假绿**（列表同判与只读性用例在 `dispatch=None` 时两侧同为空仍相等）⇒ 断言只增强；PG 引擎撞 450 行上限 ⇒ 搬代码而非改门禁 | EC-05 **PASS**（① RECHECK-088 + ② RECHECK-089，W-1…W-6：`ClaimRequest.lease_ttl_seconds` 无人消费、列表 N+1、读面不含健康度、Fake 无过期语义、PG 两读无快照、`kind` 词表张力）；EC-06/EC-07 仍 PENDING | cycle 7：derive 取 EC 表首个 PENDING（EC-06 = `resume_paused` 失败补偿，RECHECK-082 W-3），先反向搜索确认失败路径当前把 run 留在什么状态、两条入口（API / 守护线程）各自怎么收敛 |
| 7 | PLAN-20260917-090（EC-06：续跑失败补偿 `compensate_failed_resume` + `run.resume_failed`；driver=client-goal / owner=root-agent） | `56a93e8`（事件类型 + 词表同步 + 共享补偿 + 两条入口 + API/调度器用例 + `human_gates.py`/`lease_recovery.py` 两处 450 行搬迁） | 定向（DSN pin）`api+application+e2e+domain+contracts` **1993 passed / 4 skipped**（233.21s）；调度器 **11 passed**、补偿 API **4 passed**；mypy **920 files** 绿；`test_python_source_limits` **930 passed**；web 门全绿（lint / typecheck / unit **76** / build / stub e2e **83** / live e2e **36**）；**反证两跑**：去掉 API 补偿 ⇒ 2 红、去掉守护线程补偿 ⇒ 2 红（失败文本 = 旧行为 `RUNNING != PAUSED`）；m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3896 passed / 10 skipped**，509.48s；首跑 22/23，红项 = MEM-065 引用尚未写入的 RECHECK-090（记录顺序）⇒ 补齐后复跑全绿） | 两处 450 行硬上限（`service.py`/`scheduler.py`）以**搬代码**收口（`human_gates.py` / `lease_recovery.py`），未改门禁；未 pin DSN 的组合跑出现 3 条假红 ⇒ 隔离 + pin 复跑判定为环境 | EC-06 **PASS**（RECHECK-090，W-1…W-5：`resume_after_approval` 同形未修、上下文不复活、失败无任务级归因、守护线程补偿失败静默降级、响应仍 200）；EC-07 仍 PENDING | cycle 8：derive 取 EC 表首个 PENDING（EC-07 = 完整安全审计的可复核终态，二选一；`scanner_enobufs` 证据见 `scratch/goal4-mimosa-enobufs.md`） |
| 8 | PLAN-20260917-091（EC-07：完整安全审计的可复核终态；driver=client-goal / owner=root-agent） | 见本 cycle 提交（终态文档 `docs/audits/MIMOSA_DEEP_SCAN_20260917.md` + PLAN/RECHECK/MEM/ALL_PLAN/GOAL 回写） | MCP 独立密封深扫 **completed**（`scan-2026-09-17T20-05-18.700Z-663d0976701f`，seal `sha256:b2af6739…`，36 = high 3 / medium 28 / low 5；三件产物逐件 sha256 与 `seal.json.artifacts` **全 ok**；同 projectId 连续 6 次深扫剖面逐次相同）；定向：`tests/application/protocol_authoring/test_draft_service.py` **13 passed**（含危险 tag 不执行 / 钩子继承 SafeLoader）、`tests/distributed/test_security_distributed.py` 凭据隔离 2 条 **2 passed**；动态 SQL 形态检索产品树**零命中 + 反证**（蓄意四形态命中、参数化写法不命中）；治理 validate 绿；m0 见「状态历史」 | run **35272745779**（`b6e14d4`，run_number 147）：**六个 job 全 success**（container-quality / quality-ubuntu-latest / collector-quality / eval-gate / quality-windows-latest / console-frontend，无重跑） | **无产品代码变更**：36 条逐条处置 = 1 条产品代码 HIGH 误报（SafeLoader 子类）+ 2 条 HIGH 仓库外（未跟踪转储）+ 27 条 MEDIUM 同签名误报（env→DSN 被读成 env→SQL 文本）+ 1 条 MEDIUM 误报（汇点为 `tempfile.mkdtemp`）+ 5 条 LOW 误报（M12 固定 seed） | EC-07 **PASS**（终态 a；RECHECK-091 W-1…W-5 = 依赖 advisory 未署名未决 / hook 侧 enobufs 仍存 / 扫描输入含 gitignored 内容 / `artifacts/` 内明文 token 未跟踪 / 威胁建模与授权面零覆盖）；**EC-01…EC-07 全 PASS** | GOAL 收口：cycle 9 = 收口复检（独立 RECHECK 复核七个 EC 在当前树上的证据 + CI 逐 job 现状），通过后按 README 终止条款置 `ACHIEVED` 并写「终止与收口」 |
| 9 | PLAN-20260917-092（收口复检：EC-01…07 × 当前树 + CI 台账逐 job） | 见本 cycle 提交 | `scratch/verify_goal004_closeout.py` **46 条断言全 PASS**（含 15 个定向套件真跑；首跑抓出 EC-07 处置表「合并行只有 7 行 < 36」⇒ 按封印产物逐条生成 36 行后复绿）；CI 台账 **16 个 run 逐 job 重读**（#134…#147 全 success；#133 失败已同 cycle 修复；#137 补记）；治理 validate 绿；m0 见「状态历史」 | 见「状态历史」（push 后回填） | 唯一失败项是复检脚本自己抓出的处置表缺项（**判据有效性的正面证据**，非产品缺陷）；无产品代码变更 | 七个 EC 全 PASS + 独立复检通过 ⇒ **ACHIEVED**；长程剩余 9 类见「收口结论」表 | 无（本 GOAL 终止）；后继入口 = 收口结论表优先级 ① 安全审计联网复核 ② `resume_after_approval` ③ 声明未消费项清账 |


## 状态历史

- 2026-09-17 建档：由 GOAL-003 恢复条件①建立（用户 goal 模式指令）；`status: ACTIVE`；
  EC-01…EC-07 全 PENDING；GOAL-003 保持 BLOCKED，仅按只追加原则补一行事实更正
  （其 BLOCKED 记录写「W-1…W-6」，RECHECK-083 实为 W-1…W-7）。
- 2026-09-17 cycle 1 收口：EC-01 **PASS**（PLAN-20260917-084 / RECHECK-084，
  PASS_WITH_WARNINGS）；记录提交 `5141e06` → CI run **35211094454 六个 job 全 success**；
  建档提交的 CI 红项（PG 退避用例的墙钟依赖）已定位并修复（`5607992` → run
  **35204710864 六个 job 全 success**，非本 GOAL 代码缺陷）；新发现 W-1（重建"没有剩余
  工作"会重跑全部并收敛 `FAILED`）登记为 cycle 2 的候选；cycle 2 已建档
  PLAN-20260917-085（EC-02 停车语义读面）。
- 2026-09-17 cycle 2 收口：EC-02 **PASS**（PLAN-20260917-085 / RECHECK-085，
  PASS_WITH_WARNINGS，W-1…W-5）；`retry_schedule` 成为三个 adapter 的读面、`paused_dispatch`
  落到 `GET /runs/{id}` 与列表（`RETRY_SCHEDULED`/`USER_PAUSED`/`UNKNOWN`，无新增原因字段）；
  m0 23/23（全量 pytest 3804 passed / 10 skipped）；首跑 10 红定位为环境并发污染（kill 后台
  m0 留下的孙子 pytest 进程），清理后复跑全绿——判据是隔离复跑而非"重试就绿"；
  cycle 3 的 derive 取 EC 表首个 PENDING（EC-03）。
- 2026-09-17 cycle 2 CI 记录：head `7316d1d` → run **35219834215 六个 job 全 success**
  （runner_id 非 0，无重跑）；记录提交 `2dbf3c7`/`8da4b13` 与 WP 提交同一棵树被该 run 覆盖
  （CI 只跑 head）。
- 2026-09-17 cycle 3 收口：EC-03 **PASS**（PLAN-20260917-086 / RECHECK-086，
  PASS_WITH_WARNINGS，W-1…W-5）；`failure_policy` 有了真实消费者（`on_task_failure`）与
  "未消费键点名"（`unhonored`），容忍失败收敛 `DEGRADED`（此前无生产者）并发 `run.degraded`；
  m0 23/23（全量 pytest 3823 passed / 10 skipped）；首跑红 2 处 = 两个文件撞 450 行硬上限，
  以"搬代码"而非改门禁收口。
- 2026-09-17 cycle 3 CI 记录：head `186963c` → run **35227784813 六个 job 全 success**
  （runner_id 1000006747…1000006752，无重跑）；首次轮询脚本因 API 响应截断 JSON 解析失败
  （`goal4-ci-watch.sh` 的重试分支未覆盖解析异常），重跑同一脚本即取得终态——按"重跑脚本
  而非猜结论"处置，未记录任何未观察到的结论。
- 2026-09-17 cycle 4 建档：EC-04 **IN_PROGRESS**（PLAN-20260917-087，`parent_goal` 已投影
  ALL_PLAN；driver=client-goal / owner=root-agent）；反向搜索确认缺口 =
  `eventing.frozen_payload` 无 `semantic_digest`（`eventing.py:57-64`）+ 收敛分支
   `frozen_manifest_refs_of` 只读三项（`run_execution.py:65-82`）⇒ FAILED run 的语义 digest
  缺失，`assert_semantics_frozen` 直接拒绝（`convergence.py:29`）。
- 2026-09-17 cycle 4 收口：EC-04 **PASS**（PLAN-20260917-087 / RECHECK-087，
  PASS_WITH_WARNINGS，W-1…W-5）；`manifest.frozen` payload 带 `semantic_digest`，
  失败收敛分支经唯一的 payload→引用映射（`FrozenManifestRefs.from_payload(...).apply`）
  走**与成功路径同一个** `with_manifest` 落行，读面新增 `manifest_semantic_digest`；
  重放用例证明"只凭事件链"能把四项冻结引用原样重建；**反证双跑**（拆 payload 键 ⇒ 7 红、
  拆收敛参数 ⇒ 3 红，失败文本 = 改动前的 `lacks a semantic digest`）；反证暴露并修掉一处
  假绿（重放用例在"两侧同为 None"时相等成立 ⇒ 断言补"非空"）；定向 `tests/api` 418 passed、
  `domain/application/contracts/postgres/e2e` 复跑 1629 passed / 4 skipped、web 门全绿；
  m0 见迭代日志第 4 行（首跑唯一红项 = MEM 先于 RECHECK 写入的记录顺序，补齐后复跑）。
  EC-01…EC-04 的 exit_criteria `status` 一并按既有表格口径校准为 PASS（此前只在表格里
  记录，列表字段留在 PENDING——本次不改变任何判据事实，只消除同一文件内两处口径不一致）。
- 2026-09-17 cycle 4 CI 记录：head `13054a8` → run **35238057745 六个 job 全 success**
  （runner_id 1000006862…1000006867，无重跑）；WP/修复提交与记录提交同一棵树，被该 run 覆盖
  （CI 只跑 head）。
- 2026-09-17 cycle 4 收口提交 CI 记录：head `8f0b91e` → run **35239932808 六个 job 全 success**
  （记录提交只改 `.cursor/**` 同样触发六 job，按同口径等待到终态）。
- 2026-09-17 cycle 5 部分交付收口：EC-05 **① 交付**（PLAN-20260917-088 / RECHECK-088，
  PASS_WITH_WARNINGS，W-1…W-4）——控制面文件库路径改为**每线程一条连接**（代理面转发，
  store 零改动），`:memory:` 共用一条被显式钉住；池单测 5 + 负载用例 2（内存/文件两路径
  24×201 无 5xx/404）+ `tests/api` 420 + 定向 1371 + live e2e 36 全绿；m0 见迭代日志第 5 行。
  **EC-05 仍 PENDING**（② 统一派发读面未做 ⇒ 下一 cycle 的 PLAN-089）。
- 2026-09-17 cycle 5 CI 记录：head `d8c9377` → run **35245282964 六个 job 全 success**
  （runner_id 1000006994…1000006999，无重跑）；池/夹具/记录提交同一棵树被该 run 覆盖
  （CI 只跑 head）。

- 2026-09-17 cycle 5 收口提交 CI 记录：head `2a979e2` → run **35246943135 六个 job 全 success**
  （run_number 142；collector-quality / eval-gate / console-frontend / container-quality /
  quality-ubuntu-latest / quality-windows-latest 全 success，无重跑）——记录提交只改
  `.cursor/**`（RECHECK-088 / MEM-063 / GOAL 回写）同样触发六 job，按同口径等待到终态。
- 2026-09-17 cycle 6 建档：EC-05 ② **IN_PROGRESS**（PLAN-20260917-089，`parent_goal` 已投影
  ALL_PLAN；driver=client-goal / owner=root-agent）；反向搜索确认缺口 = `leases` 表没有任何
  run 级读口（PG 只有进程内 `claimed_by(task_id)`）、`paused_dispatch` 只覆盖 `PAUSED`，
  且"活"的判据必须与 `recover_expired_leases`（`expires_at < now` 或 worker LOST）互补。
- 2026-09-17 cycle 6 收口：EC-05 **PASS（① + ② 全部交付）**（PLAN-20260917-089 /
  RECHECK-089，PASS_WITH_WARNINGS，W-1…W-6）；`dispatch_ownership` 成为统一派发读面
  （重排 + 活租约 ⇒ `NONE`/`RETRY_DISPATCH`/`WORKER_CLAIM`/`BOTH`），控制面新增 `dispatch`
  字段、`paused_dispatch` 改为消费同一次读；三实现契约 + SQLite 注入时钟（过期/边界秒/LOST）
  + PG parity + API 三态全绿；定向 2108 passed / 7 skipped；web 门全绿；**反证三跑**有效
  （含一处假绿修复：列表同判与只读性用例在 `dispatch=None` 时两侧同为空仍相等 ⇒ 补"先钉住
  读面真的答了"）；m0 见迭代日志第 6 行（首跑 2 红均本改动引入 ⇒ 修类型 + 搬代码，未改门禁）。
  EC-06/EC-07 仍 PENDING ⇒ 下一条工程 cycle = cycle 7 = EC-06（`resume_paused` 失败补偿，
  RECHECK-082 W-3）。
- 2026-09-17 cycle 6 CI 记录：head `e6656be` → run **35258463258 六个 job 全 success**
  （collector-quality / container-quality / console-frontend / quality-ubuntu-latest /
  quality-windows-latest / eval-gate，run_number 143，无重跑）；本 cycle 的代码提交
  `07213ee`/`48fe31d`/`925ac6c` 与记录提交 `e6656be` 同一棵树，被该 run 覆盖（CI 只跑 head）。
- 2026-09-17 cycle 6 收口提交 CI 记录：head `ce06be2` → run **35259814746 六个 job 全 success**
  （run_number 144；collector-quality / eval-gate / console-frontend / container-quality /
  quality-windows-latest / quality-ubuntu-latest 全 success）——记录提交只改 `.cursor/**`
  （RECHECK-089 / MEM-064 / GOAL 回写）同样触发六 job，按同口径等到终态。
- 2026-09-17 cycle 7 建档：EC-06 **IN_PROGRESS**（PLAN-20260917-090，`parent_goal` 已投影
  ALL_PLAN；driver=client-goal / owner=root-agent）；反向搜索确认 = `resume_paused` 先 pop
  后执行 + API 面异常外冒 + 守护线程面 `except Exception: return 0`，两条路径都不补偿。
- 2026-09-17 cycle 7 收口：EC-06 **PASS**（PLAN-20260917-090 / RECHECK-090，
  PASS_WITH_WARNINGS，W-1…W-5）；补偿落在 `run_terminals.compensate_failed_resume`（一处，
  两条入口共用），`EventType` 36 → 37（`run.resume_failed`，词表门禁与 `EVENT_MODEL.md`
  同步）；API 4 条 + 调度器 11 条用例、**反证两跑**（各 2 红）；定向 1993 passed / 4 skipped；
  web 门全绿；两处 450 行硬上限以搬代码收口（`human_gates.py` / `lease_recovery.py`）。
  EC-07 仍 PENDING ⇒ 下一条工程 cycle = cycle 8 = EC-07（完整安全审计的可复核终态；
  `scanner_enobufs` 证据在 `scratch/goal4-mimosa-enobufs.md`）。
- 2026-09-17 cycle 7 CI 记录：head `0a58b6d` → run **35266572576 六个 job 全 success**
  （collector-quality / quality-windows-latest / eval-gate / quality-ubuntu-latest /
  container-quality / console-frontend，无重跑）；本 cycle 的代码提交 `56a93e8`、记录提交
  `3a324ee` 与 m0 结果回填 `0a58b6d` 同一棵树，被该 run 覆盖（CI 只跑 head）。
- 2026-09-17 cycle 8 建档：EC-07 **IN_PROGRESS**（PLAN-20260917-091，`parent_goal` 已投影
  ALL_PLAN；driver=client-goal / owner=root-agent）；通道判定 = commit hook 侧**仍**
  `scanner_enobufs`，改用 MCP 独立密封深扫并**首次跑通**（deep / completed / 36 findings /
  seal `sha256:b2af6739…`）；同 projectId 连续 6 次深扫剖面逐次相同（3 / 28 / 5）⇒
  `inconclusive` + `partial` 是本扫描器在本仓库的常态，不是本轮回归。
- 2026-09-17 cycle 8 收口：EC-07 **PASS**（终态 a）——36 条 findings 逐条处置，**全部**为误报
  （1 条产品代码 HIGH = `SafeLoader` 子类；27 条 MEDIUM = env→DSN 被启发式读成 env→SQL 文本；
  1 条 MEDIUM = 污点汇实为 `tempfile.mkdtemp`；5 条 LOW = M12 固定 seed）或**仓库外**
  （2 条 HIGH 落在未跟踪的 `artifacts/` 转储：`git ls-files artifacts/` = 0、`.gitignore:36`、
  `git log --all` 为空）⇒ **无产品代码变更**；终态文档 `docs/audits/MIMOSA_DEEP_SCAN_20260917.md`
  + `docs/INDEX.md` 登记；**本地 m0 首跑 22/23**（红项 = `framework/validate`：PLAN-091 缺注册章节
  `## 验收条件 / ## 实施清单 / ## 证据 / ## 状态历史 / ## 影响报告`；**补章节，未改 validator**）
  ⇒ 复跑 **23/23 全绿**（全量 pytest **3896 passed / 10 skipped**，493.96s）；定向 =
  `test_draft_service` **13 passed**（含危险 tag 不执行）+ `tests/distributed` 凭据隔离 **2 passed**；
  反证 = 动态 SQL 形态检索对四种蓄意形态命中、对参数化写法不命中（产品树零命中因此有意义）；
  RECHECK-091 = PASS_WITH_WARNINGS（W-1…W-5：依赖 advisory 未署名未决 / hook 侧 enobufs 仍存 /
  扫描输入含 gitignored 内容 / `artifacts/` 内明文 token 未跟踪 / 威胁建模与授权面零覆盖）；
  **EC-01…EC-07 全 PASS** ⇒ 下一条工程 cycle = cycle 9 = GOAL 收口复检。
- 2026-09-17 cycle 7 记录提交 CI 记录：head `3a9b86c` → run **35268496008 六个 job 全 success**
  （run_number 146）——记录提交只改 `.cursor/**`（cycle 7 CI 回填）同样触发六 job，按同口径等到终态。
- 2026-09-17 cycle 8 CI 记录：head `b6e14d4` → run **35272745779 六个 job 全 success**
  （run_number 147；container-quality / quality-ubuntu-latest / collector-quality / eval-gate /
  quality-windows-latest / console-frontend 全 success，无重跑）——本 cycle 只有记录/文档提交
  （终态文档 + PLAN/RECHECK/MEM/ALL_PLAN/GOAL 回写），六 job 仍全绿。
- 2026-09-17 cycle 9 建档：GOAL 进入收口阶段（PLAN-20260917-092「收口复检」，
  driver=client-goal / owner=root-agent）；复检方式 = 只读当前树 + **真跑** 15 个定向套件
  （不读历史 RECHECK 结论）。
- 2026-09-17 cycle 9 收口：**ACHIEVED**。`scratch/verify_goal004_closeout.py` **46 条断言全 PASS**
  （首跑抓出 EC-07 处置表「合并行只有 7 行 < 36」⇒ 改为**按封印产物逐条生成 36 行**后复绿——
  这是判据有效性的正面证据，不是产品缺陷）；CI 台账 **44 个 GOAL-004 commit → 16 个 run 逐 job
  重读**（#136 之前含 cycle 2 的 `7316d1d`、#139 `13054a8` 等；#134…#147 全 success；
  #137 `ffa272c` **补记**；唯一失败 #133 为测试墙钟依赖，已同 cycle 修复）；本地 m0 **23/23 全绿**
  （全量 pytest **3896 passed / 10 skipped**，497.25s）；「终止与收口」写入**收口结论**
  （含 9 类仍开放长程项 + 后继入口建议）与「不进入循环 / 需人工拍板」原样保留；
  `latest_recheck` = RECHECK-20260917-092，`memory_entries` = MEM-059…066。
- 2026-09-17 cycle 8 收口提交 CI 记录：head `d00dec6` → run **35274491507 六个 job 全 success**
  （run_number 148；container-quality / quality-ubuntu-latest / collector-quality / eval-gate /
  quality-windows-latest / console-frontend 全 success）——记录提交只改 `.cursor/**` 同样触发六 job，
  按同口径等到终态（收口复检时读回）。

