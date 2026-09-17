---
id: GOAL-20260917-004
slug: long-range-backlog-hardening
title: 长程项加固：来源自足续跑、停车语义读面、失败策略消费者、失败语义 digest、派发读面与补偿、完整安全审计
status: ACTIVE
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
    status: PENDING
  - id: EC-06
    criterion: >-
      `resume_paused` 失败后的补偿（后继入口第 7 项 / RECHECK-082 W-3）：续跑失败路径
      不留悬空的 `RUNNING`——失败即补偿到可判定状态（放回 `PAUSED` 或等价），补偿本身
      可观测（原因可见）、可重入（补偿后再次续跑能成功），且不静默吞掉失败。
    verify: >-
      用例：注入 `resume_paused` 失败 ⇒ run 不停在 `RUNNING`，状态与失败原因可从 canonical
      事实读到；重入用例：补偿后再次续跑成功；反证：去掉补偿 ⇒ 用例失败（run 留 `RUNNING`）；
      API/读面与守护线程两条入口的补偿语义一致（或在文档中写明有意差异）。
    status: PENDING
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
    status: PENDING
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
latest_recheck: null
memory_entries: []
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
| EC-05 | 第 6 项 | 锁粒度（每线程连接）+ 两个派发方的统一读面 | 并发反证场景 + 三态读面用例 + PG parity | PENDING |
| EC-06 | 第 7 项 | `resume_paused` 失败补偿（不留悬空 RUNNING） | 失败注入 + 重入用例 + 反证 | PENDING |
| EC-07 | 第 1 项 | 完整安全审计的可复核终态（二选一） | 终态文档 + 封印标识/findings 处置 或 根因+配方+人工清单 | PENDING |

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

当前续点：**cycle 4 已收口**（EC-04 PASS，RECHECK-087；CI 结论见迭代日志第 4 行）；
下一条工程 cycle = cycle 5 = EC-05（锁粒度每线程连接 + 两个派发方的统一读面）。

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
