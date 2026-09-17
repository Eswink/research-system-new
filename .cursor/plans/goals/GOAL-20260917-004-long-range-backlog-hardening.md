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
    status: PENDING
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
    status: PENDING
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
    status: PENDING
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
    status: PENDING
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
child_plans: []
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
| EC-01 | 第 2 项 | 重建的来源自足（协议正文冻结进 run 行或 CAS） | e2e：删文件后仍能重建续跑 + 篡改反证 + 持久化往返 | PENDING |
| EC-02 | 第 3 项 | 读面区分两种 `PAUSED`（重排停车 vs 用户暂停） | 读面用例（注入时钟）+ PG parity + 文档同源 | PENDING |
| EC-03 | 第 4 项 | `failure_policy` 有真实消费者 | 反向搜索 + fail-fast/重试对照用例 + 回归对照 | PENDING |
| EC-04 | 第 5 项 | 失败 run 与 `manifest.frozen` 事件的语义 digest（W-1/W-2） | API/事件/重放一致性用例 + 反证 | PENDING |
| EC-05 | 第 6 项 | 锁粒度（每线程连接）+ 两个派发方的统一读面 | 并发反证场景 + 三态读面用例 + PG parity | PENDING |
| EC-06 | 第 7 项 | `resume_paused` 失败补偿（不留悬空 RUNNING） | 失败注入 + 重入用例 + 反证 | PENDING |
| EC-07 | 第 1 项 | 完整安全审计的可复核终态（二选一） | 终态文档 + 封印标识/findings 处置 或 根因+配方+人工清单 | PENDING |

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

当前续点：**建档完成**（本文件 + GOAL-003 事实更正行已提交并推送，CI 结论见迭代日志
第 0 行）；下一条工程 cycle = cycle 1 = EC-01（来源自足续跑）。

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
| 0 | 建档（本文件 + GOAL-003 事实更正行；driver=client-goal / owner=root-agent） | 见状态历史 | `.cursor/skills/governance-check/scripts/validate.py` 绿（本机实跑） | 见状态历史（建档提交 run 结论） | — | EC-01…EC-07 全 PENDING | cycle 1 = EC-01（来源自足续跑：协议正文冻结进 run 行或 CAS） |

## 状态历史

- 2026-09-17 建档：由 GOAL-003 恢复条件①建立（用户 goal 模式指令）；`status: ACTIVE`；
  EC-01…EC-07 全 PENDING；GOAL-003 保持 BLOCKED，仅按只追加原则补一行事实更正
  （其 BLOCKED 记录写「W-1…W-6」，RECHECK-083 实为 W-1…W-7）。
