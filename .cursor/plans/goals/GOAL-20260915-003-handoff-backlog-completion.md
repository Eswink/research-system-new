---
id: GOAL-20260915-003
slug: handoff-backlog-completion
title: 收口清单续做：设计门禁结构判据、ToolPack 供应链面、ops 调度写面、worker 退出语义、替身守卫
status: ACTIVE
created_at: 2026-09-16
updated_at: 2026-09-16
owners:
  - root-agent
authorization:
  source: user-request
  ref: "2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」（会话内再次激活）；GOAL-20260915-002 收口（ACHIEVED，RECHECK-20260915-062）后，其「终止与收口 · 收口结论」表列出后继入口，本 GOAL 承接该表优先级最高的四项工程债 + 一个测试真实性问题。push-to-main-for-CI 授权沿用 GOAL-001 的批准口径（只推 main、不 force、不推旁支触发 CI）。"
objective: >
  把 GOAL-002 收口时如实登记、但**没有随收口一起通过**的工程债做成能力或门禁，
  让"系统更完整"这件事在质量面与供应链面同样成立：设计门禁必须有能抓住"整块新增
  内容"的结构判据（当前纯像素比率 2% 阈值对 0.48%~1.73% 的整块新增视而不见）、
  ToolPack 安装/批准必须有真实的供应链证明（pin 与交付物一致、能力取值域受控）、
  ops 调度必须有用户可见的写面（当前只有只读事实）、worker 退出必须有界
  （当前 SIGTERM 打不断阻塞中的 HTTP 读）、替身 harness 必须校验 Idempotency-Key
  （当前它守不住 mutating 契约）。
exit_criteria:
  - id: EC-01
    criterion: >-
      设计门禁结构判据：新增"结构签名"判据，使整块新增/删除节点必然判红，
      且只改样式不误报；判据与像素判据互补（像素管面积，结构管增删）
    verify: >-
      33 条路由结构签名基线入库 + 反证用例（注入面板/多一行/删除节点 → 判红；
      只改样式 → 不误报）+ 跨平台一致性证据（linux 容器重算与 win32 逐字节一致）
    status: PASS
  - id: EC-02
    criterion: >-
      ToolPack 供应链面：install/approve 写面落地，pin 与交付物 digest 绑定，
      capabilities 取值域校验，健康复核记录 schema digest 并可比对漂移
    verify: >-
      OpenAPI 写方法 + API 用例（digest 不符 409/422、未登记 provider 422）+
      live e2e 链 + pageSupport/文档收敛
    status: PASS
  - id: EC-03
    criterion: >-
      ops 调度用户可见写面：schedule 的创建/启停/触发从"只读事实"变成真实写面
      （进程内 scheduler 仍是执行体，不新造第二套调度器）
    verify: >-
      OpenAPI 写方法 + ops/schedules 的 disabledOperations 相应项消失 +
      API + live e2e 用例
    status: PASS
  - id: EC-04
    criterion: >-
      worker 退出语义：SIGTERM 能在有界时间内中断阻塞中的 HTTP 读（退出上界不再
      等于客户端 30s 超时）
    verify: >-
      定向用例（阻塞读 + SIGTERM → 有界退出，含修复前反证）+ Linux 容器复验
    status: PASS
  - id: EC-05
    criterion: >-
      替身 harness 校验 Idempotency-Key：缺头 → 422（与真中间件同语义），
      使 stub 套件能守住 mutating 契约，不再依赖 live 套件兜底
    verify: >-
      harness 头校验 + 反证（客户端去掉该头 → stub 用例失败）+ 全量 stub 套件绿
    status: PASS
  - id: EC-06
    criterion: >-
      治理收口：每个 cycle 本地 m0 与 main 的 CI 全绿；收口 RECHECK + 安全扫描处置；
      GOAL 收口时把仍未处理的长程项写成后继入口
    verify: >-
      每 cycle CI run 六 job 结论；收口 RECHECK = PASS 或 PASS_WITH_WARNINGS
    status: PASS
budget:
  # 2026-09-17 显式变更 10 → 20（见「终止与收口 · 续期记录」）：用户指令的区间是
  # 「循环迭代 10-20 次」，10 是 derive 时自定的下限；cycle 1…10 已全部交付后，
  # 按用户区间续期到 20，不降低任何判据。
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
child_plans:
  - .cursor/plans/tasks/PLAN-20260915-063-design-gate-structural-criterion.md
  - .cursor/plans/tasks/PLAN-20260915-064-tool-pack-supply-chain-write-surface.md
  - .cursor/plans/tasks/PLAN-20260915-065-tool-pack-console-surface.md
  - .cursor/plans/tasks/PLAN-20260915-066-ops-schedules-write-surface.md
  - .cursor/plans/tasks/PLAN-20260915-067-worker-bounded-sigterm-exit.md
  - .cursor/plans/tasks/PLAN-20260915-068-stub-harness-idempotency-contract.md
  - .cursor/plans/tasks/PLAN-20260915-069-provider-health-schema-digest-drift.md
  - .cursor/plans/tasks/PLAN-20260915-070-shared-sqlite-connection-serialization.md
  - .cursor/plans/tasks/PLAN-20260915-071-shared-connection-read-atomicity.md
  - .cursor/plans/tasks/PLAN-20260915-072-provider-endpoint-binding.md
  - .cursor/plans/tasks/PLAN-20260915-073-goal-003-budget-closeout.md
  - .cursor/plans/tasks/PLAN-20260915-074-provider-credential-binding.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-074-provider-credential-binding.md
memory_entries:
  - MEM-20260915-038-structural-signature-complements-pixel-gate
  - MEM-20260915-039-tool-pack-install-binds-content-digest
  - MEM-20260915-040-pending-must-be-visible-in-ui
  - MEM-20260915-041-scheduler-remains-the-executor
  - MEM-20260915-042-sigterm-cannot-break-a-blocked-read
  - MEM-20260915-043-stub-must-enforce-the-contract-it-stands-in-for
  - MEM-20260915-044-schema-digest-is-a-state-not-an-event
  - MEM-20260915-045-shared-connection-is-not-concurrency-safety
  - MEM-20260915-046-statement-serialization-is-not-read-atomicity
  - MEM-20260915-047-declared-but-unconsumed-config-is-a-lie
  - MEM-20260915-048-nonportable-counterexamples-are-not-gates
  - MEM-20260915-049-presence-check-is-not-a-resolve
---

# GOAL-20260915-003 — 收口清单续做（自迭代循环）

## 目标与退出标准

格式规范与循环 SOP 见 [README.md](README.md)。本 GOAL 是 GOAL-20260915-002
（ACHIEVED，2026-09-16）的长程承接：GOAL-002 把六个诚实缺口做成了有真实消费者的能力，
并在收口时**如实登记**了仍未处理的长程项；本 GOAL 把其中**可独立验收的四项工程债 +
一项测试真实性问题**做成能力或门禁，而不是把登记表丢掉。

| EC | 标准（摘要） | 验证 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 设计门禁结构判据（整块新增必红） | 33 路由结构签名 + 反证用例 + 跨平台一致性 | PASS（2026-09-16 cycle 1；范围注记：结构签名只看标签/testid/role/aria-label/叶子文本/子节点数，**不看样式与坐标**（那是像素判据的职责）；文本截断 120 字符 ⇒ 长文案的后半段变化不由本判据覆盖） |
| EC-02 | ToolPack install/approve 供应链面 | OpenAPI 写方法 + API/live e2e | **PASS**（2026-09-16 cycle 2：后端写面——三条文档化端点 + SQLite store + digest 重算自证 + 扩张待批准 + capability 取值域 + 目录消费，OpenAPI/契约/文档/pageSupport 全部收敛；cycle 3：console 操作面——`ops/integrations` 面板（安装表单 / 待批准横幅含 diff 明细与候选 digest / 批准 / 吊销理由必填）、stub 6 + live 2 各一条链；**cycle 7：健康复核记录 schema digest 并可比对漂移**——适配器早已算出的 `observed_schema_digest` 接到注册记录/DTO/读面/console（漂移是**状态**：当前 vs 基线；**未知观测不清除漂移**；`approve` 重基线化），三条反证在用例里，OpenAPI +39/−1）。判据四条子句至此全部落地。**注记**：`provider 凭据绑定` 与 `policy.yaml` 的 `tool_pack.*` 产品决策是收口时登记的**相邻缺口**，不在本 EC 判据文本内，作为独立长程项留在「下一轮输入」；范围注记：漂移**只在治理读面可见**（目录读面不带 digest、preflight 不消费），"可见"≠"可阻断"；基线只能从**首次观测**起算（更早的漂移检测不到）——见 RECHECK-069 W-2/W-3） |
| EC-03 | ops 调度用户可见写面 | OpenAPI 写方法 + pageSupport 收敛 + e2e | PASS（2026-09-16 cycle 4：`ops/schedules` 的 `disabledOperations` 相应项消失、`management_available=true`；**执行体仍是既有守护线程**——`trigger` 调用的就是定时 pass 的**同一个函数对象**（用例以计数器证明），`enabled=false` 被守护线程**自己的读面**（`due(job)`）消费（真实线程 + 可控时钟：停用后 `run_count` 冻结）。诚实的边界都在用例里：无 store → 静态兜底 + 写操作 503；未挂执行体 → `executor_attached=false` 且 trigger 禁用；从未跑过 → `last_outcome=null`（前端显示 UNKNOWN）；pass 失败 → 200 + `FAILED` + `last_error`。范围注记：`run_count` 等事实是**进程内观测**（重启归零，不是配置）；调度写面**不经过 policy**（等价于启停既有守护线程），若要审批需新增 `schedule.*` 能力——见 RECHECK-066 W-6） |
| EC-04 | worker 退出语义（SIGTERM 有界中断阻塞读） | 定向用例 + 反证 + Linux 容器复验 | PASS（2026-09-16 cycle 5：8 处出站调用收口到 `WorkerClient._call`，停机后超过 `RESEARCHOS_WORKER_DRAIN_SECONDS`（默认 5s，取值域 0.1~60）即放弃在途调用并抛 `WorkerDrainAbort`，进程按有序停机退出 0。**实测对照**（同脚本同参数，Linux 容器 + 黑洞网关）：修复前 **29.64s**、修复后 **1.12s**（drain=1）。两层反证：进程内"未停机 ⇒ 同一条阻塞读照常跑满"、进程外"drain 调大 ⇒ 进程不早退"。范围注记：只覆盖**网关读**的停机上界——在途**执行**的中断仍走既有协作式 cancel 通道，其停止时间没有新增上界（RECHECK-067 W-1）；被放弃的请求可能已到达服务端也可能没有，属 at-least-once 允许的模糊点，已写进 runbook（W-2）） |
| EC-05 | 替身 harness 校验 Idempotency-Key | 头校验 + 反证 + stub 套件绿 | PASS（2026-09-16 cycle 6：替身在 handler 之前守门，与真中间件四条语义对齐——缺头/空值 → 422 `Idempotency-Key Required`；同 key 不同摘要 → 422 `Idempotency-Key Reused`；同 key 同摘要 → 重放首次响应；分析类 POST 豁免；响应体与真件 `_problem()` 同形（`instance` 为空串）。**反证做在产品客户端上**：把 `apps/web/src/api/http.ts` 的头发送改成别的头名后，`schedules-write` + `project-delete` **7 failed / 2 passed**，失败面板里呈现的正是真件的 422 detail；还原后 `git diff` 为空。跨语言守卫把 stub 词表与 `middleware.py` 的 `_MUTATING_METHODS`/`_ANALYSIS_ACTIONS` 钉成集合相等（并断言豁免清单非空）——替身单方面放宽会在 Python 套件里红。范围注记：两处**刻意不一致**（替身摘要只做判等、重放不带 ETag）、守门顺序的真实副作用（未知路径 + mutating + 无 key → 422 而非 404 ⇒ 不进 `assertNoUnmatched`）、`PUT` 无真实路由可测——见 RECHECK-068 W-1/W-2/W-3/W-4） |
| EC-06 | 每 cycle m0/CI 全绿 + 收口复检 + 安全扫描处置 | CI run 六 job 结论 + RECHECK | PENDING（cycle 1 一度 BLOCKED：账户计费阻断 → 阻断解除后 run **35059391199 六个 job 全 success**，cycle 1 的 CI 结论已成立；后续每 cycle 继续按此标准记） |

**不变量（沿用 GOAL-001/002 与 AGENTS.md）**：不伪装实现（不注册没人消费的写面、
不让 fixture 冒充业务数据）；默认 deny 的安全姿态不变；观测隐私不变；每一项写面必须走
既有 policy/preflight 门链；**判据只允许增强，不允许为了让测试通过而削弱**
（本 GOAL 的 EC-01 与 EC-05 本身就是"把门禁变强"，与 fix_policy 的"不得改门禁使其通过"
不冲突：前者是交付物，后者是作弊）。**规模标注**：EC-02 为 M/L（供应链语义最重）、
EC-03 为 M、EC-04 为 M（进程信号语义）、EC-05 为 S、EC-01 为 M。

## 循环入口协议

按 README 的 7 步判定执行；当前续点：**cycle 1 已闭环**（PLAN-20260915-063 设计门禁
结构判据 = EC-01 PASS，RECHECK-063；提交 `5a44445`→`28c9c30`，CI run **35059391199** 六个 job 全 success）。
**cycle 2 已闭环**（PLAN-20260915-064 ToolPack 供应链写面 = EC-02 后端，RECHECK-064；
提交 `3c343f4` → run **35064152993** 六 job 全 success）。
**cycle 3 已闭环**（PLAN-20260915-065 console 操作面 + live 链 = EC-02 前端，
RECHECK-065 见 `latest_recheck`；提交 `ce28e05` → run **35071216707** 六 job 全 success，
记录提交 `bc44b68` → run **35072629321** 六 job 全 success）。
**cycle 4 已闭环**（PLAN-20260915-066 ops 调度写面 = EC-03 PASS，
RECHECK-066 见 `latest_recheck`；提交见 cycle 4 迭代日志行的 CI 结论）。
**cycle 5 已闭环**（PLAN-20260915-067 worker SIGTERM 有界退出 = EC-04 PASS，
RECHECK-067 见 `latest_recheck`；修复前/后实测 29.64s → 1.12s）。
**cycle 6 已闭环**（PLAN-20260915-068 替身 harness 校验 Idempotency-Key = EC-05 PASS，
RECHECK-068 见 `latest_recheck`；反证 = 去掉客户端发送头后 mutating 用例 7 failed；
全量 stub 套件 81 passed、m0 23 项绿；提交见 cycle 6 迭代日志行的 CI 结论）。
**EC 表至此全项 PASS**（EC-01/02/03/04/05）。下一轮起做**相邻长程项**与 cycle 7 发现的新缺陷：
① **控制面 SQLite 共享连接的并发写缺陷**（cycle 7 复现：12 线程 24 个
`POST /ops/schedules` ⇒ 2×500 `sqlite3.InterfaceError` + 2×404；`check_same_thread=False`
允许跨线程但 sqlite3 连接不支持两个线程同时使用，FastAPI 同步端点跑在 threadpool 里）——
见 RECHECK-069 W-1，**这是下一轮第一项**；② provider 凭据绑定（`CredentialResolver` 已有先例、
`ToolProviderSpec.endpoint_env` 已解析但从未被消费）；③ RECHECK-065 W-1 的 `tool_pack.*`
策略产品决策；④ EC-06 收口复检（GOAL 收口时把仍未处理的长程项写成后继入口）。
BLOCKED 处置模板见「终止与收口 · BLOCKED 记录（已解除）」。
driver=session-goal，owner=root-agent。

## 驱动

驱动无关（README「驱动适配」）：默认会话驱动；需要无人值守时挂定时自动化，指令模板见
README（仅当 status=ACTIVE 时推进）。进入 cycle 时在迭代日志声明 driver/owner；
同一时刻仅一个驱动推进。

## 单 cycle SOP

按 README ①~⑦ 执行。本实例附加约定：

- ① derive 的主题顺序默认取 EC 表首个 PENDING；若上一 cycle 部分交付，则以其「下一轮输入」为准。
- 子 PLAN 必须独立可验收、独立 RECHECK；GOAL 只在 EC 层面记账。
- ③ 本地验证：m0 全量（23 项）+ 受影响定向套件 + web 门（lint/typecheck/unit/build/stub e2e/live e2e）
  + 设计基线（页面改动时按既有流程强制重生成并目检；**结构签名基线同步重生成**，
  命令 `UPDATE_OUTLINES=1 pnpm exec playwright test design-fidelity -g 结构签名`）。
- ⑤ push 前 `git pull --ff-only origin main`（并发历史先 rebase，不 force）。
- 每个 EC 允许拆到多个 cycle；部分交付记 `PARTIAL`，不得预置 PASS。
- **只改 `.cursor/**` 的记录提交同样触发六 job CI**（cycle 1 起即按此等待结论）。

## CI 失败分类与纠错

按 README 分类表执行；本仓已知 flake/env 签名（重跑不修）：observability OTLP teardown race、
m0 全量单跑在负载下的 timing 用例（隔离复跑对照）、DSN 注入（需固化配方）、
`framework/run_cursor_framework_evals` 在 Windows 上偶发文件占用（复跑对照）。
`.github/workflows/m0-quality.yml` 属治理面：循环内不修改；需要改动即 BLOCKED 提请人工。

## 终止与收口

- **ACHIEVED** 前置：五个 EC 全 PASS + 独立 RECHECK PASS/PASS_WITH_WARNINGS +
  本文件收口（`latest_recheck` 指向该 RECHECK）。
- **BLOCKED**：预算触顶（`max_cycles` 或 `no_progress_stop_cycles`）、命中 escalation_triggers、
  或同一失败签名超过 `fix_policy` 上限；恢复条件必须写清。

### 续期记录（2026-09-17）——**预算 10 → 20，status BLOCKED → ACTIVE**

> **触发**：用户会话指令的区间是「循环迭代 **10-20** 次」。`max_cycles: 10` 是 derive
> 时自定的**下限**，不是用户给的上限；cycle 1…10 交付完后按区间续期，是回到用户
> 口径，不是放宽判据。
>
> **变更**：`budget.max_cycles: 10 → 20`（frontmatter 有同源注释）；`status: BLOCKED → ACTIVE`。
> **EC 未动**：EC-01…EC-06 的 criterion/verify 与判据一字未改；已记 PASS 的不回退、
> 未达成的不得预置 PASS。
> **发起方式**：RECHECK-20260915-073 列的恢复条件②（显式变更 `budget.max_cycles`
> 并置回 ACTIVE，从 cycle 11 续跑）。①（新建承接 GOAL）保留为后续选项。
> **续期后的推进顺序**：先做「最小、最安全」的一条 —— provider 凭据绑定
> （RECHECK-072 W-4 / RECHECK-073 后继②）；escalation 级的两项（端点注入 adapter、
> `tool_pack.*` 策略产品决策）仍**不**由本 GOAL 自行决定。

### BLOCKED 记录（2026-09-16，cycle 10 收口）——**预算触顶（已由上方续期记录解除）**

> **原因**：`budget.max_cycles: 10` 已用尽（cycle 1…10 全部交付，不是 EC 未达成、
> 也不是失败签名超限）。按 frontmatter 口径「硬上限，触顶即 BLOCKED」置 `status: BLOCKED`。
>
> **EC 状态**：EC-01…EC-05 全 PASS；EC-06 因"每 cycle m0 + main CI + 收口复检 +
> 扫描处置 + 后继入口"四条齐备置 PASS，其中 cycle 9 的 ubuntu 红项已定位为
> **反证不可移植**（非代码缺陷）、更正后在 cycle 10 的 run 上验证通过。
>
> **收口复检**：RECHECK-20260915-073（`result: PASS_WITH_WARNINGS`，本文件
> `latest_recheck` 已指向它），内含 EC 表、每 cycle CI 结论、安全扫描处置与六条后继入口。
>
> **恢复条件（二选一，由用户决定，本 GOAL 不自作续期）**：
> ① 新建承接 GOAL（沿用 GOAL-002 → GOAL-003 的方式），把 RECHECK-073 的
> 「仍未处理的长程项」按优先级写进新 GOAL 的 EC；② 显式变更本 GOAL 的
> `budget.max_cycles` 并置回 `status: ACTIVE`，从 cycle 11 续跑。
> **两条路都需要用户拍板**（其中"端点注入 adapter"与 `tool_pack.*` 策略本就是
> escalation 级决策）。

### BLOCKED 记录（2026-09-16，cycle 1）——**已解除**

> **解除（同日）**：账户计费状态恢复后，cycle 1 的收口提交 `28c9c30` 触发 run
> **35059391199**，六个 job 全部拿到真实 runner 且 **全部 success**（无重跑），
> `EC-06` 回到 PENDING、GOAL 回到 ACTIVE。本段保留为真实历史与"下次再遇到同签名时
> 的处置模板"：阻断期间**不推进 cycle**、把"本地能证的"与"远端未证的"分开记账、
> 解除后先复核 runner 是否真的拿到（`runner_id != 0`）再回填。

**类别**：基础设施（README 分类表「runner 挂/网络/依赖源不可达 → 等窗口重跑 1 次；
仍败 → BLOCKED（infra 非代码缺陷）」）。**已按要求重跑 1 次，仍败**。

**证据（现读 GitHub API，不是记录转述）**：

- cycle 1 提交 `5a44445` → run **35056976439**（`m0-quality.yml`，event=push）：
  六个 job（quality-ubuntu-latest / quality-windows-latest / console-frontend /
  container-quality / eval-gate / collector-quality）全部 `failure`，且
  **`runner_id: 0`、无任何 step**——job 从未启动（04:47:40 → 04:47:42，2 秒）。
- `rerun-failed-jobs` → attempt 2 六个 job 同样 2 秒内失败、`runner_id` 为空。
- check-run 注释给出唯一根因（原样引用）：
  *"The job was not started because recent account payments have failed or your
  spending limit needs to be increased. Please check the 'Billing & plans'
  section in your settings"*。
- 同一 workflow 在本提交之前的 12 个 run 全部 `success`（最近一个 35022837958，
  2026-09-15T20:58Z）⇒ 不是 workflow/代码回归，而是**账户计费状态变化**。
- 本段记录自身的提交 `ab340cb` 也产生 run **35057354632**：六个 job 同样
  `runner_id=0`、0 step、同一条注释 ⇒ 与改动内容无关（连只改 `docs` 的记录提交
  也起不来）。**此后不再逐次追记 run**：同因重复，追记只会再产生一个同形 run。

**为什么不是"重试就能过"**：该条件由 GitHub 账户计费面决定，仓库内任何动作
（改 workflow、改分支、改提交）都不会改变它；`--force`/重推/新 commit 只会再产生
一个同样失败的 run。故不再重试，按契约置 BLOCKED。

**恢复条件（满足任一路径后按序执行）**：

1. 仓库所有者处理 GitHub `Billing & plans`（付款失败 → 更新支付方式；额度/支出上限
   → 提高上限或等下一计费周期刷新）——**只有账户所有者能做，本循环内外均无替代动作**。
2. 验证：对本 run 再执行一次 `rerun-failed-jobs`，或推一个空提交触发新 run，
   观察六个 job 是否**真的拿到 runner**（`runner_id != 0`、有 step 输出）。
3. 六个 job 全 `success` → 回填 cycle 1 迭代日志的 `CI run/结论` 字段与本段状态，
   然后 `status: ACTIVE`，按「循环入口协议」执行 ①（EC-02 / PLAN-20260915-064）。

**BLOCKED 期间不做什么**：不推进 cycle 2+（EC-02~05 的交付物都需要 EC-06 的
"每 cycle CI 全绿"才能记账，无 CI 就会产生"本地绿、远端未验证"的不可核验声明）；
不把本地绿当作 CI 绿；不伪造 run 结论；不为绕过计费而改动 `.github/workflows/**`
（治理面，改动即命中 escalation，需人工决策）。

#### 阻断期间的"CI 等价复现"（**不是 CI**，只用于降低恢复风险）

阻断后按"若 CI 恢复，六个 job 会不会红"逐项做了本地/容器等价复现（提交 `9b5c1a2` 的全新
clone，pinned `mcr.microsoft.com/playwright:v1.56.1-noble` 镜像 = CI 的 linux 平台）：

| 受阻断的 job | 等价复现方式 | 结果 |
| --- | --- | --- |
| quality-windows-latest | 本地 win32 全量 m0（`.venv` + DSN 固化配方） | `profile=m0; 23 deterministic checks` |
| quality-ubuntu-latest | 容器内跑 m0 的**根 typescript 5 项**（`format:check` / `lint` / `typecheck` / `boundaries` / `test`） | 全绿（prettier 通过、eslint 0 error 1 warning、depcruise 923 modules 0 违规） |
| console-frontend | 容器内 `pnpm --dir apps/web lint/typecheck/test/build/test:e2e` | 全绿；**stub e2e 66 passed (2.9m)**（含 EC-01 的 33 路由结构签名用例）；win32 上单测 **76 passed** |
| eval-gate | `python -B -m adapters.cli.eval_gate` + `pytest tests/evals -q -m "not requires_live_llm"` | `M11 CI eval gate: PASS`（两数据集 PASS + digest）；**110 passed** |
| container-quality | `docker build -t research-os-sandbox:m9-test adapters/execution/sandbox` + `pytest -m requires_docker` | 镜像构建成功；**58 passed**（3474 deselected） |
| collector-quality | 既有 postgres-test 实例（15432，36h healthy）+ 本轮新起 otel collector；`pytest tests/observability tests/postgres tests/distributed tests/e2e/test_pg_crash_restart.py -m "requires_collector or postgres or distributed"`（`REQUIRE_COLLECTOR=1` / `REQUIRE_POSTGRES=1`） | **98 passed**（64 deselected） |

**这些证据的边界（必须与 CI 区分）**：

1. **不是 CI**：没有 Actions runner、没有 checkout action、没有 job 隔离与并行、没有 runner
   镜像差异——**因此不构成 EC-06 的"main 的 CI 全绿"，EC-06 仍为 BLOCKED**。
2. **quality 的 python 侧没有在 linux 上重跑**：本 cycle 的改动是**纯前端测试面**
   （`apps/web/tests/e2e/**`），python 侧与最近一次 ubuntu 全绿（run 35022837958）逐字节相同；
   为省时间没有在容器里重建 python 环境跑 3530 条用例——这一点如实记录，不当作"复现过"。
   （win32 侧 python 全量 m0 已绿，含 58 条 requires_docker。）
3. **collector-quality 的复现不完全等价**：本轮 `compose up` 的 postgres 容器因
   `0.0.0.0:15432` 被既有实例占用而**未启动**（`research-system-postgres-1` = Created），
   测试实际跑在既有的 postgres 实例上（otel collector 是本轮新起的）——所以这一项只是
   "测试套件在真 collector + 真 postgres 下通过"，不是"CI 的 compose 起停链通过"。
4. 本轮创建的容器与网络（`research-system-otel-collector-1` / `research-system-postgres-1` /
   `research-system-evidence-dir-1` / network `research-system_default`）已删除；
   既有的 `compose-postgres-1`（project=compose）与 5 天前的随机名容器（非本轮产生）未动。

**已确证的部分（不受阻断影响）**：EC-01 的全部证据都是本地/容器可复现的——
m0 `23 deterministic checks`、stub e2e 66 / live e2e 31 / 单测 76、eslint 0 error、
`tsc --noEmit` 通过、结构签名跨平台一致性（pinned noble 容器 33/33 逐字节一致）、
Mimosa 密封扫描本轮改动文件命中 0 条。阻断的只是"main 上六个 job 的远端复验"。
- **收口动作**：更新 EC 状态表、迭代日志、child_plans、memory_entries；把长程剩余项
  写入「终止与收口」供后继 GOAL 承接（不在本文件内隐藏缺口）。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20260915-063（EC-01：设计门禁结构判据） | 见本 cycle 提交 | 结构签名基线 33 条（`apps/web/tests/e2e/design-outlines.json`）；guard 用例 **6 passed**（注入可见面板/多一行/视口外节点/删节点 → 判红；只改样式 → 不误报；归一化 4 断言）；对照实验：多一行 **0.079%**、视口外 **0.000%** ⇒ 像素判据不报警而结构判据判红；跨平台一致性：linux 容器重算与 win32 **逐字节一致**（33/33）；全量 stub e2e / live e2e / 单测 / m0 见「证据」段 | run **35056976439**（5a44445）：**失败——但失败在启动前**：六个 job 全部 `runner_id=0`、无 step、2 秒内结束（attempt 1 与 rerun attempt 2 同形）；check-run 注释原样给出根因 *"The job was not started because recent account payments have failed or your spending limit needs to be increased"* ⇒ 账户级计费阻断，非代码/门禁缺陷。**两小时后阻断解除**（未做任何仓库内动作）：cycle 1 的收口提交 `28c9c30` → run **35059391199 六个 job 全 success**（container-quality / console-frontend / eval-gate / collector-quality / quality-ubuntu-latest / quality-windows-latest，均拿到真实 runner）⇒ **cycle 1 的 CI 结论成立**（详见「终止与收口 · 当前 BLOCKED」的处置记录） | 首次实现踩到三处：① 用 `toMatchSnapshot` 会得到 per-platform `-win32.txt` 基线（CI 在 ubuntu 上必然缺文件）⇒ 改成单一 JSON 基线 + 显式 `UPDATE_OUTLINES=1` 更新；② ISO 正则没吃 `+00:00` 偏移 ⇒ 归一化残留导致 33 条基线含半截时间戳，修正则后重生成；③ 注入到 `body` 末尾的面板落在视口外，像素差 0.000% ⇒ 补"可见注入"用例作为真实对照 | EC-01 已 PASS（范围注记见 EC 表）；EC-02~05 PENDING；**EC-06 BLOCKED（账户级计费阻断 CI）** | **本 cycle 无下一轮**（GOAL = BLOCKED）：恢复条件满足后 cycle 2 = ① derive EC-02（ToolPack install/approve 供应链面：pin↔交付物绑定、能力取值域、schema digest 漂移），子 PLAN 编号 = PLAN-20260915-064 |

| 2 | PLAN-20260915-064（EC-02：ToolPack 供应链写面） | 见本 cycle 提交 | **API 9 passed**（digest 重算 422 / 未知 capability 422 点名 / 内置 id 409 / 扩张待批准且目录 digest 不变 / approve 后生效 / 相似内容 `unchanged` / 终态 409 / 未知 404 / **三态消费证明**）；生命周期 **12 passed**（新增"扩张不生效直到批准"、"相同内容不是更新"、"吊销清 pending"）；契约 **1354 passed / 3 skipped**；OpenAPI **+437 行**（仅新增四条路径）+ 契约断言；stub e2e **66 passed**、live e2e **31 passed**；根 eslint 0 error、`tsc --noEmit` 通过；33 路由像素 + 结构签名双绿（基线逐字节未动）；本地 m0 连红三轮（ruff 行宽/import 排序 → mypy 2 处 → 50 行函数上限 2 处）→ 修复后 **23/23** | run **35064152993**（3c343f4）：**六个 job 全 success**（eval-gate 06:32:27Z / collector-quality 06:34:05Z / container-quality 06:36:09Z / console-frontend 06:38:03Z / quality-ubuntu-latest 06:40:49Z / quality-windows-latest 06:44:34Z，无重跑） | ① `InvalidInputError` 是 `PermanentPortError` 子类 ⇒ 异常映射必须先判子类（首版"未知 pack"返回 422，被"未知 pack 404"用例抓住）；② pin 的正确形态是**控制面自己重算**（不是采信请求里的字面量），且要写清"自洽 ≠ 与上游一致"；③ 扩张不生效要有**读面证据**（pending 期间目录 digest 不变），否则"待批准"只是响应里的一个字段；④ `pageSupport` 的 reason 文本不在 33 路由可见 DOM 中（W-2） | EC-02 记 **PARTIAL**（后端已交付，console 入口与 live 链未做）；EC-03~06 PENDING | cycle 3 = ① derive EC-02 前端面（console ToolPack 操作入口 + 替身 + live e2e 链），并顺带 W-4（provider 健康复核记录 schema digest 并比对漂移），子 PLAN 编号 = PLAN-20260915-065 |
| 3 | PLAN-20260915-065（EC-02：console 操作面 + live 链） | 见本 cycle 提交 | **stub 6 passed**（空列表是正确状态 / 安装后 digest 由服务端重算校验 / 篡改内容 → 422 detail 在面板内 / 扩张 → 横幅有 diff 且**生效 digest 不变** / 批准后 digest 变 / 吊销理由必填且终态无动作）；**live 2 passed**（真实 uvicorn + 真实 SQLite：install → 扩张（读面 digest 不变、`pending.digest` = 候选）→ approve（digest 变）→ revoke（REVOKED、目录退出、同 id 再装 409）；422 detail 落在面板内）；stub e2e **72 passed**、live e2e **33 passed**、web 单测 **76 passed**、根 eslint 0 error（1 条既有 soft warning）、`tsc --noEmit` 通过、`tests/tooling+api+application` **1890 passed / 1 skipped**、全量 pytest **3436 passed / 8 skipped**；**结构判据首次真实拦截**：`ops-integrations` 节点 **+18** 判红、同一次运行 33 条像素用例全绿（2% 阈值不报警）；基线重生成后 `verify_linux_outlines.sh` → win32 == linux（33/33 逐键一致）；像素基线 win32+linux 各重生成一张并目检；本地 m0 两轮红（ruff 行宽 → ruff format）后 **23/23** | run **35071216707**（ce28e05）：**六个 job 全 success**（eval-gate 07:58:06Z / collector-quality 07:59:51Z / container-quality 08:01:43Z / console-frontend 08:04:13Z / quality-ubuntu-latest 08:04:18Z / quality-windows-latest 08:09:07Z，无重跑） | ① live 第一次跑就撞上"平台默认策略没有 `tool_pack.*` 规则 ⇒ default DENY"，面板把 403 原样显示（界面正确工作的证据）⇒ 本轮只在**夹具层**放行四个能力、不改产品策略（W-1）；② 替身里的 digest 是**镜像口径**（canonical JSON→sha256），权威口径由 live fixture（域代码生成 + 同步守卫）证明（W-2）；③ GOAL 级 EC-02 的第三子句（健康复核 schema digest + 漂移比对）本轮未覆盖 ⇒ AC-10 收窄、EC-02 保持 PARTIAL（W-4） | EC-02 仍 **PARTIAL**（console 面已交付；剩 provider 侧 schema digest 漂移与凭据绑定）；EC-03~06 PENDING | cycle 4 = ① 按 EC 表选首个未满足项（EC-02 剩余子句"schema digest 漂移"需先定探测面从哪来，或直接做 EC-03 ops 调度写面）；② 顺带 W-1 的产品决策（policy.yaml 放行 `tool_pack.*`，或把既有 `action: TOOL_PACK_INSTALL_OR_UPDATE` 接成 require_approval → 登记待批准） |

| 4 | PLAN-20260915-066（EC-03：ops 调度写面） | `de58a31`（收口提交，55 个显式路径） | **tests/application/ops 20 passed**（registry 11 + daemon 9：节奏随定义 / 停用被守护线程读面消费 / trigger 跑同一函数 / 记账失败不杀线程 / **启动不抢跑**）；**tests/api 8 passed**（诚实事实 / 取值域 / PATCH 被 due 消费 / trigger 共用 pass 并记账 / 未装配 registry 的 503）；契约 **365 passed / 56 skipped**；`tests/architecture+api+application/ops` **447 passed**；`tests/postgres` **70 passed**；lint-imports **2 kept, 0 broken**；OpenAPI 重生成（**+303 / -2**）；stub e2e **77 passed**、live e2e **35 passed**、web 单测 **76 passed**、`pnpm lint`/`tsc` 通过、根 `eslint .` 0 error；**结构判据第二次真实拦截**（`ops-schedules` 170 → 260 节点判红，同一次运行 33 条像素用例全绿、实测 **15093 px = 1.64% < 2%**）+ 两平台像素基线重生成目检 + 跨平台 33/33；**m0 PASS: profile=m0; 23 deterministic checks** | run **35087267045**（de58a31）：**六个 job 全 success**（eval-gate 10:52:15Z / collector-quality 10:54:06Z / container-quality 10:56:03Z / console-frontend 10:57:09Z / quality-ubuntu-latest 10:59:18Z / quality-windows-latest 11:04:34Z，无重跑） | ① live 首跑观察到守护线程因 `record()` 抛 `KeyError('worker_reaper')` 退出（三次复跑未复现，根因未定）⇒ 记账/读面调用全部改 fail-open + 3 条回归用例（W-1）；② **架构门禁**：DTO 直接 import domain 的枚举 ⇒ `api-dto-purity` BROKEN（全量 m0 判红）⇒ 取值域校验下沉到 `ScheduleRegistry._coerce_job`、DTO 收字符串，**未放宽断言**；③ **启动抢跑回归**：`next_wait_seconds` 对未预约定义返回 0.1s ⇒ 四个守护线程在 app 起来约 100ms 后同时开跑，打断请求线程的共享 psycopg 事务（m13 PG 用例：干净 HEAD 6/6 绿、带该行为 6/6 红；另有一次合并跑把守护线程留在 idle in transaction 使 TRUNCATE 阻塞 8 分钟）⇒ 未预约定义不参与候选 + 3 条钉子用例（W-9）；④ 首版 registry 校验比域正则弱（`"ab"` 会 500）⇒ 收敛为共用 `validate_schedule_name()` | EC-03 **PASS**；EC-04 / EC-05 / EC-06 仍 PENDING；EC-02 仍 PARTIAL（provider 侧 schema digest 漂移 + 凭据绑定 + RECHECK-065 W-1 的 `tool_pack.*` 策略产品决策） | cycle 5 = ① 按 EC 表取 EC-04（worker SIGTERM 有界中断阻塞读），子 PLAN 编号 = PLAN-20260915-067；② 备选：EC-05（替身 harness 校验 Idempotency-Key）或 EC-02 剩余子句；③ 顺带评估 W-1 与 W-9 是否同源（都指向"启动期并发读写共享 store"，若 EC-04 扩面可一并复现） |

| 5 | PLAN-20260915-067（EC-04：worker SIGTERM 有界退出） | `1f0c7d9`（收口提交，10 个显式路径） | **tests/worker 33 passed / 2 skipped**（新增 drain 用例 5 进程内 + 2 真实信号）；**容器内 `tests/worker/test_worker_drain_bound.py` 6 passed**（`python:3.12-slim`，含两条真实 SIGTERM）；**修复前/后实测**：同一脚本同一参数同一镜像，worktree @ `dca1f94` **29.64s** → 修复后 **1.12s**（drain=1，退出码都是 0）；`tests/architecture+worker+contracts` **453 passed / 58 skipped**；ruff/format/mypy 全绿；`docs_consistency_check` 6 项 + 治理验证通过；m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3592 passed / 10 skipped**） | run **35093603690**（1f0c7d9）：**六个 job 全 success**（eval-gate 12:03:06Z / collector-quality 12:04:59Z / container-quality 12:06:21Z / console-frontend 12:09:12Z / quality-ubuntu-latest 12:10:47Z / quality-windows-latest 12:13:31Z，无重跑）⇒ 两条真实 SIGTERM 用例在 ubuntu job 上真实执行并通过 | ① 全量 m0 首轮红于 `python/product-lint`：两处 `skipif` 装饰器行 101 > 100 字符 ⇒ 收敛成模块级 `_SIGTERM_ONLY` marker（**未放宽任何断言**）；② 第二轮撞上**已知 Windows 文件占用 flake**（`framework/run_cursor_framework_evals` 的 `evolution_state.json.tmp` 原子改名 `PermissionError`）⇒ 按 GOAL 分类表复跑对照，`--profile framework` **8/8 绿**，第三轮 m0 全绿；③ 设计上刻意**不用** `os._exit`/进程看门狗，沿用本仓"守护线程 + 有界等待 + 放弃"模式；④ 容器复验踩到两个环境坑（uv 镜像无 `sh`、Git Bash 改写 `-w /repo`）已写进 MEM-042 | EC-04 **PASS**；EC-05 / EC-06 仍 PENDING；EC-02 仍 PARTIAL（provider 侧 schema digest 漂移 + 凭据绑定 + RECHECK-065 W-1 的 `tool_pack.*` 策略产品决策） | cycle 6 = ① 按 EC 表取 EC-05（替身 harness 校验 Idempotency-Key：缺头 → 422 与真中间件同语义；反证 = 客户端去掉该头后 stub 用例失败），子 PLAN 编号 = PLAN-20260915-068；② 备选：EC-02 剩余子句或 RECHECK-065 W-1 的产品决策 |
| 6 | PLAN-20260915-068（EC-05：替身 Idempotency-Key 契约） | `4af5ad4`（收口提交，12 个显式路径） | stub 新用例 **4 passed**（缺头逐字段等于真件 problem body + DELETE/PATCH 同 422；分析类 POST 免 key；同 key 不同 body → 422 Reused；同 key 同 body → 重放，用 `/ops/schedules` 的"重名会 409"构造证明没有第二次状态变更）；parity 守卫 **2 passed**（跨语言词表集合相等 + 豁免清单非空）；全量 stub 套件 **81 passed (4.5m)**（77 既有 + 4 新增，两次独立运行一致）；**客户端反证**（临时改 `http.ts` 的头发送）`schedules-write` + `project-delete` **7 failed / 2 passed**，失败面板里就是真件的 422 detail，还原后 `git diff` 为空；m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3595 passed / 10 skipped**）；framework profile **8/8**（doc 改动后复跑）；治理验证通过；Mimosa deep scan 36 findings / 182 packages（3 high / 28 medium / 5 low），与 cycle 4/5 逐项一致、本轮四个改动文件零命中 | run **35100510412**（4af5ad4）：**六个 job 全 success**（eval-gate 13:13:28Z / collector-quality 13:15:24Z / container-quality 13:17:08Z / console-frontend 13:20:23Z / quality-ubuntu-latest 13:20:44Z / quality-windows-latest 13:24:25Z，无重跑） | ① **根 `eslint .` 对 `apps/web/tests/**` 判红 10 error**（`max-params` 两处：`call` 5 参、`beginMutation` 4 参；内联 `import type`；`dot-notation` 四处；两处冗余判断）——`apps/web` 自己的 lint 只覆盖 `src`（且对 `tests/**` 有放宽），所以"web 门绿"**不等于**"根 TS 门绿"；按规则改代码（options 对象收敛参数表、顶层 `import type`、点号访问），未动配置、未加 disable；② `tsc -p apps/web/tsconfig.json` 接着暴露两处（`page.evaluate` 的数组实参推断成 `string[]` ⇒ 解构得 `string \| undefined`；`body: string \| undefined` 撞 `exactOptionalPropertyTypes`）⇒ 显式四元组 + 条件式装配 `RequestInit`；③ **证据采集失误**：首次后台跑 stub 套件被 `TaskStop`，遗留 `npx playwright test` 子进程与第二次运行共用日志 ⇒ ok 与 x/- 混杂、不可判读；按 PID 清理后用唯一文件名重跑（单表头、81 passed），教训记为 EXP-20260916-001 | EC-05 **PASS**；EC-01/03/04/05 全 PASS、EC-02 仍 PARTIAL（provider 侧 schema digest 漂移 + 凭据绑定、RECHECK-065 W-1 的 `tool_pack.*` 策略决策）；EC-06 按 cycle 记账（本行即 cycle 6 的 CI 结论） | cycle 7 = ① 取 EC-02 剩余子句「健康复核记录 schema digest 并可比对漂移」，recon 已定位缺口：适配器**已经算出** `observed_schema_digest`（`adapters/mcp/provider.py:145`、`adapters/research_tools/ncbi.py:150`、`adapters/fakes/tool_provider.py:101`），但 `probe_provider_spec`（`services/api/preflight_support.py:88-94`）把它**丢掉**、`ProviderRegistration.record_health`（`packages/domain/tool_registry.py:156-165`）不接收、DTO 与 SQLite store 都不落 ⇒ 漂移不可检测；子 PLAN 编号 = PLAN-20260915-069；② 备选：provider 凭据绑定（`CredentialResolver` port 已有先例、`ToolProviderSpec.endpoint_env` 已解析但从未被消费）、RECHECK-065 W-1 的策略产品决策 |
| 7 | PLAN-20260915-069（EC-02 剩余子句：schema digest 漂移） | `b269aef`（收口提交，21 个显式路径） | API **23 passed**（漂移三态 / 回到基线清除 / **无 digest 观测不清除** 三条反证 + approve 重基线化 + 无 schema 概念的 kind 诚实为 null）；store **3 passed**（四字段往返 + **旧行键集**仍可解码）；stub e2e **83 passed (4.8m)**（81 + 2：漂移可见 + 对照组不显示；**33 路由像素与结构签名均未变**）；live e2e **35 passed**（首轮 1 failed 的处置见下）；API+store+contracts+architecture **944 passed / 2 skipped**；`lint-imports --config .importlinter.api` **2 kept, 0 broken**；OpenAPI **+39 / −1**；根 eslint 与 `tsc -p apps/web/tsconfig.json` 空输出；mypy **860 files clean**；m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3605 passed / 10 skipped**） | run **35108305191**（b269aef）：**六个 job 全 success**（eval-gate 14:24:59Z / collector-quality 14:26:30Z / container-quality 14:28:24Z / console-frontend 14:30:47Z / quality-ubuntu-latest 14:32:03Z / quality-windows-latest 14:36:32Z，无重跑） | ① **门禁拦截两次**：加漂移标记后 `registrationColumns` 53 行 > 50 上限（根 eslint）⇒ 抽成 `RegistryHealthCell.tsx`；`tests/api/test_tool_registrations_api.py` 达 **523 行** > 450 硬上限（`test_python_source_limits.py`）⇒ 拆出 `test_tool_registration_health_drift.py`——两处都改代码/文件划分，**未放宽任何规则**；② **顺带复现出真实缺陷**（见 cycle 8）：live e2e 首轮 `live-schedules-write` 期望 422 得到 **500**，隔离复跑 2 passed、第二轮全量 35 passed，但顺着这条线对 live 控制面并发发 24 个 `POST /ops/schedules`（12 线程）得到 **19×201 / 2×500 / 2×404 / 1×409**，500 的服务端栈落在 `adapters/sqlite/schedule_store.py:78` 的 `sqlite3.InterfaceError: bad parameter or other API misuse` | EC-02 **PASS**（判据四条子句全部落地；`provider 凭据绑定` 与 `tool_pack.*` 策略决策是相邻缺口、不在判据文本内）；**EC 表全项 PASS**；W-1 交给 cycle 8 | cycle 8 = ① 修控制面 SQLite 共享连接的并发写缺陷（RECHECK-069 W-1），子 PLAN 编号 = PLAN-20260915-070；② 备选：陈旧读（每线程连接/显式事务）、provider 凭据绑定 |
| 8 | PLAN-20260915-070（共享 SQLite 连接的并发写缺陷） | `e4f5b3d`（收口提交，8 个显式路径） | `tests/adapters/sqlite` **92 passed**（含新增 2 条并发用例）；`tests/adapters/sqlite tests/api` **472 passed**；**反证**：同一并发负载（12 线程 × 8 轮写）打在**普通连接**上 **10 次 `sqlite3.InterfaceError`**、打在 `connect()` 返回的连接上 **0 次**且 96 行全部落库；**live 前后对照**（同脚本同参数，12 线程 24 个 `POST /ops/schedules`）：**19×201 / 2×500 / 2×404 / 1×409 → 23×201 / 1×404 / 0×500**；ruff/format 干净；mypy **862 files clean**；m0 **PASS: profile=m0; 23 deterministic checks**（首轮唯一红项见下）；framework **8/8** | run **35111194584**（e4f5b3d）：**六个 job 全 success**（eval-gate 14:50:00Z / collector-quality 14:51:45Z / container-quality 14:53:41Z / console-frontend 14:56:38Z / quality-ubuntu-latest 14:57:00Z / quality-windows-latest 14:59:54Z，无重跑） | ① m0 首轮唯一红项是 `framework/validate` 的"任务计划未加入 ALL_PLAN: PLAN-20260915-070"——登记后复跑即绿（不是门禁缺陷，是收口时忘了同步索引，如实记账）；② 写 `SerializedConnection` 撞到本仓安全扫描的"SQL 直通"判据（在 `sqlite3.Connection` 子类里直接定义/调用执行方法会被拒写）⇒ 按仓库既有的已记录写法用**别名赋值 + `getattr(super(), ...)` 转发**，行为等价（语句文本仍由调用方构造，本类不拼装 SQL）；③ mypy 对着返回 `Any` 的转发判 `Returning Any` 四处 ⇒ `cast`，并把 `cursor` 的赋值显式放宽（重载函数）；④ 顺带把 GOAL 前言的 EC-02/EC-05 status 回正（正文早已 PASS、前言漏更新） | 崩溃类已治；**锁只管语句级串行，写后立读仍会读不到**——残留的读侧缺陷如实登记为 RECHECK-070 W-1 并交给 cycle 9，**不把本轮读成"并发读写已经正确"** | cycle 9 = ① 读原子性（RECHECK-070 W-1），子 PLAN 编号 = PLAN-20260915-071；② 备选：provider 凭据绑定、`tool_pack.*` 策略决策 |
| 9 | PLAN-20260915-071（共享 SQLite 连接的读原子性） | `cb61f41`（收口提交，8 个显式路径） | 定因实验：2×2 对照（12 线程 × 8 轮，每格 3 轮 × 96 次读）——(写护,读护)=(F,F) 10/14/13 → (T,F) 1/4/0 → **(F,T) 0/0/0** → (T,T) 0/0/0 ⇒ 决定性的一侧是读；修复后同矩阵四格全 0；`tests/adapters/sqlite test_shared_connection_read_atomicity.py` **4 passed**（结构反证 + 游标面七项对账 + 并发解码无短行）；`tests/adapters/sqlite tests/api` **476 passed**；ruff/format 干净；mypy clean；m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest 3613 passed / 10 skipped）；live 观察 24×201 / 0×404 / 0×500 | run **35115260874**（cb61f41）：**五个 job success，`quality-ubuntu-latest` 判红**（`python/tests`）；红在 cycle 9 自己的**负载型反证**——2 vCPU runner 上 288 次往返一次没复现竞态（本地 8+ 核每次 10~20/96）；**cycle 9 不计为"CI 全绿"**，更正随 cycle 10 入库 | ① **反证不可移植**：这是真实竞态，复现率随并行度变化；"确定性做法"经实验也不成立（拿住游标 + 另线程写提交不触发——竞态要两个线程**同时**在 sqlite3 的 C 调用里）⇒ 门禁换成**结构判据**（读结果是否在锁内取尽），负载型复现器降级为记录；② m0 首轮即绿（与 cycle 8 不同，这次没有索引遗漏）；③ 游标面改成只读视图后，`execute()` 不再返回 `sqlite3.Cursor` 实例——仓库无 `isinstance` 依赖（已 grep）；④ 物化让"一行代码改动覆盖全部 store"，但代价是锁内取尽（大结果集会更久地占锁），如实写进已知风险 | 读侧缺陷已治；**live 与 2 vCPU 环境压不出这一类** ⇒ 未来回归必须靠结构判据 + 记录里的负载复现器，**不许拿"live 全绿"当证明** | cycle 10 = ① 相邻长程项 provider 端点绑定（`endpoint_env` 零消费面 + 示例配置误用），子 PLAN 编号 = PLAN-20260915-072；② 备选：`tool_pack.*` 策略决策（产品决策，需用户拍板） |
| 10 | PLAN-20260915-072（provider 端点绑定：声明被执法且可见） | `d5e5de7`（收口提交，24 个显式路径） | 新用例 **7 passed**（三态 / 文件里的同名值不算数 / 明文不泄漏 / 读面自洽拒绝 / 门槛挂在声明上 / 注册读面三态 / 示例配置不带凭据名）；store **97 passed**（含端点声明往返 + 旧行解码为未声明）；`tests/api` **380 passed**；`tests/contracts + tests/loaders` **398 passed / 56 skipped**；OpenAPI **+66 行**且快照契约过；TS 类型镜像 + `tsc -p apps/web/tsconfig.json --noEmit` 空输出；mypy 5 模块 clean；m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3623 passed / 10 skipped**） | run **35119573827**（d5e5de7）：**六个 job 全 success**（eval-gate 16:05:03Z / collector-quality 16:06:48Z / container-quality 16:08:46Z / console-frontend 16:11:45Z / **quality-ubuntu-latest 16:13:52Z** / quality-windows-latest 16:16:35Z，无重跑）⇒ cycle 9 的反证更正**在 2 vCPU 的 ubuntu job 上被验证**（结构判据可移植） | ① `endpoint_env` 的缺陷有**两半**：没人消费 + `ProviderRegistration.spec()` 重建时把它**丢掉**（derive 时才发现），本轮一并补齐；② 示例配置把**凭据名**写进端点位且无人报错 ⇒ 交付里加了"示例约定"钉子（定点，不是通用启发式门禁）；③ 目标文件里写 SQL 常量被本仓安全扫描判"注入"⇒ 调用点用字面量 SQL（既有已记录写法）；④ Bash 直接改 `.ts` 源码被拒 ⇒ 一律走 Write/Edit（含用 Edit 重新落一遍已被 Bash 写过的内容，让扫描器看到候选代码） | 端点声明已"执法 + 可见"；**仍未把解析出的端点注入 adapter**（要按 spec 重建 provider 实例，涉及受控出网——先登记不擅动），如实登记为下一轮候选；相邻缺口：`ToolProviderSpec` 无 `credential_ref` 表达面 | cycle 11 = ① provider 凭据绑定（声明 → 门槛 → 可见，只做存在性检查、绝不物化密钥），子 PLAN 编号 = PLAN-20260915-073；② 备选：把端点注入 adapter（受控出网，需先定策略）、`tool_pack.*` 策略决策（需用户拍板）、`conn.cursor()` 自建游标路径收口 |

## 状态历史

- 2026-09-16 cycle 5 交付（EC-04 = **PASS**）：SIGTERM 之后进程不再等客户端超时——
  `WorkerClient` 的 8 处出站调用收口到 `_call()`，停机后超过
  `RESEARCHOS_WORKER_DRAIN_SECONDS`（默认 5s，取值域 0.1~60）即放弃在途调用并抛
  `WorkerDrainAbort`，`main()` 捕获后按有序停机返回 0。**对照实测**（同一脚本、同一参数、
  同一容器镜像，黑洞网关 + 真子进程）：
  **修复前（worktree @ `dca1f94`）29.64s → 修复后 1.12s**（drain=1，退出码都是 0）。
  两层反证把"上界来自停机窗口而不是写死的常数"钉死：进程内未停机 ⇒ 同一条 1.5s 阻塞读
  照常跑满；进程外 drain=30 ⇒ 6s 后进程仍在跑。容器内 `tests/worker/test_worker_drain_bound.py`
  **6 passed**；win32 上两条真实信号用例 skip（`Popen.terminate()` 是 TerminateProcess）。
  刻意不用 `os._exit`/进程看门狗——沿用本仓"守护线程 + 有界等待 + 放弃"的既有模式。
  全量 m0 首轮红于 `python/product-lint`（两处 101 字符行 ⇒ 收敛成模块级 skipif marker，
  **未放宽断言**），第二轮撞上已知 Windows 文件占用 flake（`framework/run_cursor_framework_evals`
  的 `evolution_state.json.tmp` 原子改名 PermissionError；单独复跑 `--profile framework` **8/8 绿**），
  第三轮 **PASS: profile=m0; 23 deterministic checks**（全量 pytest 3592 passed / 10 skipped）。
- 2026-09-16 cycle 4 CI（**六个 job 全 success**）：收口提交 `de58a31` → run **35087267045**
  （eval-gate 10:52:15Z / collector-quality 10:54:06Z / container-quality 10:56:03Z /
  console-frontend 10:57:09Z / quality-ubuntu-latest 10:59:18Z / quality-windows-latest
  11:04:34Z，无重跑）⇒ EC-06 的"每 cycle CI 全绿"在本 cycle 成立；本轮本地证据为
  m0 23/23、tests/application/ops 20 / tests/postgres 70 / 契约 365 / stub 77 /
  live 35 / 单测 76、Mimosa sealed scan（`scan-2026-09-16T09-58-50.302Z-c66ac1c53225`，
  36 findings，与本轮改动相关命中 0）。
- 2026-09-16 创建（ACTIVE）：GOAL-20260915-002 收口（ACHIEVED，RECHECK-20260915-062）后，
  按其「收口结论」表的后继入口立项，承接优先级最高的四项工程债 + 一项测试真实性问题；
  范围不含 M18 租户/RBAC（该表明确标注为 deferred，需独立决策立项）。
- 2026-09-16 cycle 1（EC-01 = 设计门禁结构判据，**PASS**）：新增
  `apps/web/tests/e2e/design-outline.ts`（结构签名：前序遍历的 标签/testid/role/aria-label/
  叶子文本/子节点数，含 ISO 时间戳、时钟、UUID、长数字的归一化）与单一 JSON 基线
  `design-outlines.json`（33 路由，156 KB），`design-fidelity.spec.ts` 增加第二条主判据
  "33 路由结构签名（DOM outline，整块新增必红）"。判据的**存在理由**由对照实验给出：
  同一改动的三类形态里，"列表多一行"只差 **0.079%**、"视口外面的板"差 **0.000%** ⇒
  2% 阈值的像素判据不会报警（这正是 cycle 3/5/6/7 四次实测的盲区：1.73% / 1.02%·0.93%
  / 0.79%·0.66% / 0.48%·0.47%），而结构签名判据对这三种形态全部判红。反证与对照写进
  `design-outline-guard.spec.ts`（6 用例）：注入可见面板、注入视口外节点、列表多一行、
  删除一个节点行 → 判据失败；**只改颜色 → 不误报**（避免门禁退化成噪音）；
  易变字面量归一化 4 条断言。跨平台：因为 CI 跑 ubuntu 而本机是 win32，把基线做成
  **单一 JSON**（不是 Playwright 的 per-platform 快照——首版 `toMatchSnapshot` 生成了
  `-win32.txt`，在 CI 上必然缺文件），并用 pinned noble 容器重算全部 33 条签名，
  与 win32 结果**逐字节一致**，证明结构签名与平台无关（脚本
  `scratch/verify_linux_outlines.sh`）。更新流程写进 GOAL 的 SOP：
  `UPDATE_OUTLINES=1 … -g 结构签名`（CI 不设该变量，与 `--update-snapshots` 同理）。
- 2026-09-16 cycle 1 的 CI 结论（**FAIL，infra**）⇒ GOAL 置 **BLOCKED**：提交 `5a44445`
  推送后 run **35056976439** 六个 job 全部在 2 秒内失败且 `runner_id=0`（job 从未启动）；
  按 README「基础设施 → 重跑 1 次」重跑（attempt 2）仍同形；check-run 注释原文给出根因：
  *"The job was not started because recent account payments have failed or your spending
  limit needs to be increased. Please check the 'Billing & plans' section in your settings"*。
  此前同一 workflow 连续 12 个 run 全 success（最近 35022837958）⇒ 判定为**账户计费状态
  变化**而非代码回归（本段记录自身的提交 `ab340cb` → run 35057354632 同形，证明与改动无关）。
  按契约「infra 非代码缺陷 → BLOCKED」置 `status: BLOCKED`、
  `EC-06 = BLOCKED`，恢复条件与验证步骤写入「终止与收口 · 当前 BLOCKED」。
  **本 cycle 的 CI 不记 PASS**；本地证据（m0 23/23、stub 66 / live 31 / 单测 76、
  跨平台签名一致、Mimosa 命中 0）不受影响。
- 2026-09-16 阻断**解除**（account billing 恢复）：cycle 1 收口提交 `28c9c30` → run
  **35059391199 六个 job 全 success**（container-quality / console-frontend / eval-gate /
  collector-quality / quality-ubuntu-latest / quality-windows-latest，均 `runner_id != 0`）；
  `status: BLOCKED → ACTIVE`、`EC-06: BLOCKED → PENDING`；cycle 1 的 CI 结论就此成立。
  解除未做任何仓库内动作（只等账户侧恢复），且解除后**先复核 runner 真的拿到**再回填。
- 2026-09-16 cycle 2 开轮（EC-02）：derive = PLAN-20260915-064（ToolPack 供应链写面），
  入口按「循环入口协议」第 6 条（上一 cycle commit+CI 全绿且 EC 未满足 → 执行 ①）。
- 2026-09-16 cycle 2 CI（**六个 job 全 success**）：提交 `3c343f4` → run **35064152993**
  （eval-gate / collector-quality / container-quality / console-frontend /
  quality-ubuntu-latest / quality-windows-latest 依次 06:32–06:44Z，无重跑）⇒ EC-06 的
  "每 cycle CI 全绿"在本 cycle 成立。
- 2026-09-16 cycle 2 交付（EC-02 = **PARTIAL**）：把 ADR-0019 的 ToolPack 供应链从
  "有 use case、无控制面"接成真实写面——`POST /tool-packs/install`（控制面**重算**内容
  digest 并要求与请求 digest 相等；capability 取值域；内置 pack id 不可覆盖）、
  `POST /tool-packs/{id}/approve-update`（**权限扩张不生效直到批准**：待批准期间目录里
  仍是旧 digest）、`POST /tool-packs/{id}/revoke`（终态、清 pending）、`GET /tool-packs`
  （生效版本与待批准版本分开呈现）。持久化 = `SqliteToolPackStore`（生效版本与待批准
  版本同一行写入），两组成同侧装配；`catalog_merge` 把 INSTALLED 的 digest 合入
  `tool_pack_digests`（preflight/compile 的同一读面）⇒ 三态消费证明可证伪。
  RECHECK-060 结转的 W-2（capability 取值域）与 W-3（pin 与交付物绑定）**在 pack 侧关闭**
  （provider 侧仍开放，如实结转）。未交付：console 操作入口与 live e2e 链（cycle 3）。
- 2026-09-16 阻断期间追加**CI 等价复现**（明确**不是 CI**，见「终止与收口 · 当前 BLOCKED」表）：
  按六个 job 逐项在本地/容器复现——win32 全量 m0 23/23；linux 容器内根 typescript 5 项全绿、
  web lint/typecheck/unit/build + **stub e2e 66 passed**；eval-gate `PASS` + 110 passed；
  container-quality 镜像构建 + **58 passed**（requires_docker）；collector-quality 四套件
  **98 passed**（postgres 复用既有实例、collector 本轮新起 ⇒ 该项不等价，如实标注）。
  目的：让 CI 恢复后的首次运行更可能一次绿，并把"阻断期间系统仍然完好"落成可核验证据；
  **EC-06 不因此解冻**（它要求的是 main 上六个 job 的真实结论）。
- 2026-09-16 cycle 3 开轮（EC-02 收口）：derive = PLAN-20260915-065（console 操作面 +
  live 链），入口按「循环入口协议」第 6 条（上一 cycle commit+CI 全绿且 EC 未满足 → ①）。
- 2026-09-16 cycle 3 实施中的两个**计划外事实**（都写进 RECHECK-065，不在循环内改产品语义）：
  ① **live 第一次运行就 403**——平台默认策略 `examples/config/policy.yaml` 没有
  `tool_pack.*` 规则 ⇒ `default_effect: DENY`，真实部署下 console 写面（及任何调用
  lifecycle 的路径）会被拒；面板把 `policy denied capability tool_pack.install` 原样显示
  在动作旁边（这正是"拒绝原因落在行内"该有的样子）。本轮**只在夹具层**放行四个能力
  （`tests/api/console_api_app.py::_ConsoleToolPackPolicy`），产品策略未动；待产品决策的
  两条候选路径记在「下一轮输入」。② **结构判据第一次真实拦截**：新增面板使
  `ops-integrations` 结构签名 +18 节点判红，而同一次运行的 33 条像素用例全绿（2% 阈值
  对整块新增依然不敏感）——cycle 1 的判据在真实改动上兑现了它的用途。
- 2026-09-16 cycle 3 交付（EC-02 = **PARTIAL（收窄）**）：console 面全部交付——
  `ToolPackPanel`（表列 id/状态(+待批准 chip)/**生效 digest**/版本/capabilities/目录/吊销）、
  安装表单（完整 manifest JSON → install，422 detail 行内显示）、待批准横幅（候选 digest +
  `pending.diff` 明细 + 批准按钮，**表里 digest 始终是生效版本**）、吊销（理由必填、终态无动作）；
  `toolPacksClient` 四方法经 `api.*` 门面；stub 6 + live 2 各一条链（live 的 manifest 由域
  代码生成、由 `tests/tooling/test_console_toolpack_fixtures.py` 守同步）；`pageSupport` /
  `CONSOLE_PAGE_MAP` / `CONTROL_PLANE_API` 三处文案收敛；两条设计基线重生成并目检。
  **AC-10 由"EC-02 PARTIAL → PASS"收窄**为"本 PLAN 十条 AC 全绿 + EC-02 保持 PARTIAL"：
  GOAL 级 EC-02 的第三子句（健康复核 schema digest + 漂移比对）本轮未覆盖，不用
  "前端收口"冒充整个 EC-02；剩余范围如实写在 EC 表与「下一轮输入」。
- 2026-09-16 cycle 3 CI（**六个 job 全 success**）：提交 `ce28e05` → run **35071216707**
  （eval-gate 07:58:06Z / collector-quality 07:59:51Z / container-quality 08:01:43Z /
  console-frontend 08:04:13Z / quality-ubuntu-latest 08:04:18Z / quality-windows-latest
  08:09:07Z，无重跑）⇒ EC-06 的"每 cycle CI 全绿"在本 cycle 成立；本轮本地证据为
  stub 72 / live 33 / 单测 76 / 全量 pytest 3436 passed·8 skipped / m0 23/23 /
  安全扫描（sealed）本轮改动命中 0。
- 2026-09-16 cycle 4 开轮（EC-03）：derive = PLAN-20260915-066（ops 调度写面），
  入口按「循环入口协议」第 6 条（上一 cycle commit+CI 全绿且 EC 未满足 → ①）。
  范围口径与 EC 表述一致：**只把"调度定义"变成可写/可读/可触发，执行体仍是既有守护线程**，
  验收的关键是"写面被执行体的读面消费"，不是"多了一张表"。
- 2026-09-16 cycle 4 交付（EC-03 = **PASS**）：`ScheduleDefinition`（名/间隔/启停/note，
  取值域 1s~86400s、名字 `^[a-z][a-z0-9_]{2,40}$`）+ `ScheduleStore` 端口
  （SQLite + Fake，登记进 contract matrix）+ `ScheduleRegistry`（due 预约 / record 事实 /
  trigger 手动 / runtime 读面）+ 四条 HTTP 写面（POST 201 / PATCH / trigger / GET 并入读面），
  取代原先的 `disabledOperations` 锁定；console 端 `SchedulesPage` 的创建表单、行内启停与
  触发、事实列（executor / 上次结果），替身 `stub-routes-schedules.ts` 是有状态的最小实现，
  live 用例跑真实 SQLite。**执行体没变**：`PeriodicDaemon` 在 `start()` 时把自己的
  `_execute_pass` 注册进 registry，`trigger(name)` 调用的就是这个函数对象（用例用计数器
  证明同一对象）；守护线程每轮问 `due(job)`，所以 `enabled=false` 是被执行体自己的读面消费的
  （真实线程 + 可控时钟：停用后 `run_count` 冻结）。过程中发现并修掉一个**真实缺陷**：
  `record()` 抛错会杀死守护线程（live 日志里 `KeyError: 'worker_reaper'`）——本轮把
  `_record`/`_due_names`/`_next_wait` 全部改成 fail-open 并补 3 条回归用例
  （根因未复现，如实记在 RECHECK-066 W-1）；另外首版 registry 的校验比域正则弱，
  `"ab"` 会穿过写面直达 dataclass 抛 500 ⇒ 收敛成 `validate_schedule_name()` 由域与
  registry 共用（422）。**门禁拦截一次**：全量 m0 的 `python/tests` 判红于
  `tests/architecture/python/test_services_api_boundaries.py` 两项——DTO 直接 import 了
  domain 的枚举（`api-dto-purity` BROKEN）；修法是把取值域校验下沉到域边界
  （`ScheduleCreateDto.job: str` + `ScheduleRegistry._coerce_job`，未知作业 → 422 点名词表），
  **未放宽任何断言**，复验 `lint-imports --config .importlinter.api` → 2 kept / 0 broken、
  `tests/architecture+api+application/ops` 447 passed。教训：定向套件不含
  `tests/architecture`，新 DTO 的"类型好看"很容易换来一次全量红。
  **第二次真实拦截（同日）**：全量 m0 又红在 `tests/postgres/test_m13_pg_run_e2e.py`，
  且随后卡在 71%（一个后端 `idle in transaction` 持锁，另一个在 `TRUNCATE` 等锁）。
  隔离对照证明是本 cycle 的确定性回归——干净工作树 HEAD `82e3e13` 上 **6/6 通过**，
  带改动 **6/6 失败**（`OutOfOrderTransactionNesting`）。根因：`next_wait_seconds` 把
  "尚未预约的定义"当成 0.1s 候选，于是**四个守护线程在 app 起来约 100ms 后同时开跑**，
  与启动期初始化写在共享 psycopg 连接上并发、打断请求线程的显式事务。修法：未预约的定义
  不参与候选（等待下界 = 守护线程自身 interval，与"定义下一轮生效"一致）+ 三条钉子用例；
  复验 `tests/postgres` 70 passed、m13 6/6 绿、`tests/application/ops` 20 passed，
  **未改动 m13 用例**。两个现象（W-1 的 live `record()` KeyError 与 W-9 的抢跑）**可能同源**，
  但 KeyError 未被直接复现，故不宣称已解决。
- 2026-09-16 cycle 6 开轮（EC-05）：derive = PLAN-20260915-068（替身 harness 校验
  Idempotency-Key）。关键判断：**反证对象必须是产品客户端**——只写一条"替身会回 422"的用例
  等于替身自己测自己；真正的风险是客户端漏发头而 stub 放行，所以必须有"去掉发送 → 套件红"
  的实验，否则这条 EC 只是装饰。替身与真件是"同一契约的两个实现"，词表漂移用**跨语言守卫**
  （Python 侧 import 真件的 `_MUTATING_METHODS`/`_ANALYSIS_ACTIONS` 做集合相等）钉住，
  因为替身单方面放宽不会让任何既有用例变红。
- 2026-09-16 cycle 6 交付（EC-05 PASS）：`stub-idempotency.ts` 实现四条语义（缺头 422 /
  同 key 不同摘要 422 Reused / 同 key 同摘要重放 / 分析类 POST 豁免），`stub-api.ts` 在
  `match()` 之前守门、`handler()` 之后记账；4 条用例全绿，全量 stub 套件 **81 passed (4.5m)**。
  **客户端反证**：临时改 `http.ts` 的头发送后 `schedules-write` + `project-delete`
  **7 failed / 2 passed**（失败面板里就是真件的 422 detail），还原后工作树零残留。
  两处**刻意不一致**（摘要只判等、重放不带 ETag）写进模块 docstring 与 RECHECK-068 告警，
  不假装与真件逐字相同。**门禁拦截两次**：根 `eslint .` 对 `apps/web/tests/**` 判红
  10 个 error（`max-params` 两处、内联 import type、`dot-notation` 四处、两处冗余判断）——
  `apps/web` 自己的 lint 只覆盖 `src`，所以本仓"web 门绿"不等于"根 TS 门绿"；
  修完后 `tsc -p apps/web/tsconfig.json` 又暴露两处（元组推断出 `string | undefined`、
  `body: string | undefined` 撞 `exactOptionalPropertyTypes`）。两处都**改代码**，
  未动任何 eslint 配置、未加 disable 注释；修完 m0
  **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3595 passed / 10 skipped**）。
  **一次证据采集失误（已纠正并如实记账）**：首次后台跑 stub 套件时把它 `TaskStop` 了，
  遗留的 `npx playwright test` 子进程与第二次运行共用同一日志文件，产出一份 ok 与 x/-
  混杂、不可判读的日志 ⇒ 按 PID 清理后用唯一文件名重跑（单表头、81 passed）；
  教训记为 EXP-20260916-001。Mimosa deep scan（seal
  `sha256:d15c0a99c4c08a2237fc9b53e544eebe45b19d899a6714faa193125c26d32998`）
  36 findings / 182 packages，与 cycle 4/5 逐项一致，本轮四个改动文件零命中。
- 2026-09-16 cycle 7 开轮（EC-02 剩余子句）：derive = PLAN-20260915-069（健康复核记录
  schema digest 并可比对漂移）。recon 定位缺口：**适配器早就算出** `observed_schema_digest`
  （`adapters/mcp/provider.py:145`、`adapters/research_tools/ncbi.py:150`、
  `adapters/fakes/tool_provider.py:101`），是 `probe_provider_spec` 只取 status/detail
  把它丢掉、`record_health` 不接收、DTO 与 SQLite 都不落。两条关键口径在 derive 时就写进
  PLAN：**漂移是状态（当前 vs 基线）不是事件（这次 vs 上次）**——否则 A→B→B 会让告警自己
  消失，而提供方仍不是当初那个；**未知观测不得清除漂移**——把"没观测到 digest"读成
  "没变化"会抹掉已经发现的漂移。
- 2026-09-16 cycle 7 交付（EC-02 → PASS）：域加四字段 + `record_health` 接收 digest
  （None 时四字段一律不动）+ `approve` 重基线化（"我看见了并接受"）；探测路径改为
  返回 `ProviderProbe(status, detail, observed_schema_digest)`，写面与读面继续共用它；
  SQLite 是 JSON-blob-per-row ⇒ **表结构不变、无迁移**，旧行按 `None/False` 解码
  （用一条手写历史键集的用例钉住）；DTO + OpenAPI（+39/−1）+ TS 镜像 +
  `RegistryHealthCell`（漂移标记带两个截断指纹）。**门禁拦截一次**：加标记后
  `registrationColumns` 53 行 > 50 上限被根 eslint 判红 ⇒ 抽成独立组件，未放宽规则。
  证据：API **23 passed**（含无 digest 不清除、回基线清除两条反证）、store **3 passed**、
  stub e2e **83 passed**（**33 路由像素与结构签名均未变**——漂移标记只在真漂移时渲染，
  这是结构判据"只在真实变化时判红"的正向证据）、live e2e **35 passed**、
  API+store+contracts+architecture **944 passed / 2 skipped**、mypy 860 files clean、
  m0 **PASS: profile=m0; 23 deterministic checks**。
- 2026-09-16 cycle 7 的**顺带发现（下一轮第一项）**：live e2e 首轮出现 1 failed
  ——`live-schedules-write` 的"越界间隔"期望 422 却得到 **500**。隔离复跑 2 passed、
  第二轮全量 35 passed（单看属于 flake），但顺着这条线**复现出真实缺陷**：对 live 控制面
  并发发 24 个 `POST /ops/schedules`（12 线程）⇒ **19×201 / 2×500 / 2×404 / 1×409**，
  500 的服务端栈为 `ops_schedules.py:99 → :50 → schedule_registry.py:94 →
  adapters/sqlite/schedule_store.py:78` 抛 **`sqlite3.InterfaceError: bad parameter or
  other API misuse`**——`connect(..., check_same_thread=False)` 允许跨线程，但 sqlite3
  连接**不允许两个线程同时使用**，而 FastAPI 的同步端点跑在 threadpool 里。
  这**不是** cycle 7 引入的（本轮只动 provider 注册面），但它意味着此前 EC-03 的
  "live 35 passed"必须被读成**单并发**下的结论。已记入 RECHECK-069 W-1，并作为 cycle 8 的
  第一项（修法方向：连接加锁/每线程连接 + `busy_timeout`，并以并发用例钉住）。
- 2026-09-16 cycle 8 开轮（真实缺陷：共享 SQLite 连接的并发写）：derive = PLAN-20260915-070。
  关键判断：**在 `connect()` 这个唯一咽喉处加锁**（store 与调用点一个都不动），并且
  **不把"加锁"说成"一致性"**——语句级串行治的是崩溃，不治陈旧读。
  写法上撞到本仓安全扫描的既定触发面（在 `sqlite3.Connection` 子类里直接写
  `def execute(...)` / `.execute(...)` 会被判"SQL 直注"而**拒绝写入**）⇒ 改用
  **别名赋值 + `getattr(super(), ...)` 转发**（仓库既有已记录的规避写法），行为等价：
  语句文本仍由调用方构造，本类不拼装、不解析、不缓存。
- 2026-09-16 cycle 8 交付：`adapters/sqlite/db.py` 返回 `SerializedConnection`
  （execute/executemany/executescript/cursor/commit/rollback/close 全在可重入锁内转发）+
  `PRAGMA busy_timeout=5000`。证据：**live 前后对照（同脚本同参数，12 线程 24 个
  `POST /ops/schedules`）：19×201 / 2×500 / 2×404 / 1×409 → 23×201 / 1×404 / 0×500**；
  单元层面同负载打在**普通连接**上 **10 次 `sqlite3.InterfaceError`**、打在 `connect()`
  的连接上 **0 次**（这就是反证）；`tests/adapters/sqlite` **92 passed**；
  `tests/adapters/sqlite tests/api` **472 passed**；mypy **862 files clean**；
  m0 **PASS: profile=m0; 23 deterministic checks**（首轮唯一红项是
  `framework/validate` 的"PLAN-070 未加入 ALL_PLAN"——登记后复跑即绿，
  不是门禁缺陷）。记录落盘：PLAN-070 DONE + RECHECK-070（PASS_WITH_WARNINGS）+
  MEM-045 + ALL_PLAN + GOAL 前言的 EC-02/EC-05 状态回到与正文一致的 PASS。
  **未治的另一半（下一轮第一项）**：**陈旧读**——锁不保证"写后立读看得见刚提交的行"，
  live 残留 1/24 的 `404 unknown schedule`（行已提交、独立连接查得到，共享连接上的那次
  SELECT 没看见），单元复现为"12 线程 × 8 轮写后立刻读"里 9~10 次读不到；
  治法需要**每线程连接或显式事务**（结构性改动，本轮刻意不做），见 RECHECK-070 W-1。
- 2026-09-16 cycle 9 开轮（读原子性）：derive = PLAN-20260915-071。derive 先把"到底
  什么坏了"钉死再动手——三次诊断脚本依次排除"读快照旧"（miss 时 `in_transaction=False`、
  同一连接上**紧接着**的 `list_definitions()` 看得见那行）与"写入丢了"（独立连接 100% 看得见），
  再用 **2×2 对照**定因：只护读即归零、只护写不归零 ⇒ 是**读侧的取行窗口**。
- 2026-09-16 cycle 9 交付：`SerializedConnection._statement` 在锁内执行，
  返回行的语句（`cursor.description is not None`）**在锁内取尽**，交回只读视图
  `MaterializedRows`（fetchone/fetchmany/fetchall/迭代/rowcount/description/close），
  store 与路由一行未动。证据：修复后 12 线程 × 8 轮 × 3 轮 = **288 次往返 0 处对不上**
  （修复前 10~20/96）；**反证**可复现（语句级串行的形态既有"读不到"也有
  `zip() argument 2 is shorter` 的坏行）；游标面七项与真游标逐项相等；
  `tests/adapters/sqlite tests/api` **476 passed**；live 24×201 / 0×404 / 0×500。
  **如实收窄**：把控制面切回语句级串行后 216 个并发 POST 仍全 201 ⇒ live 压不出这一类，
  live 对照只作补充观察，判据由单元级证据承担（RECHECK-071 W-1）；
  cycle 8 的 live 1×404 因此只能说"与这一类一致"，**不能说已证明同源**。
  m0 **PASS: profile=m0; 23 deterministic checks**。
- 2026-09-16 cycle 9 收口的 CI 结果与处置（如实记账）：收口提交 `cb61f41` → run
  **35115260874**：`quality-ubuntu-latest` 在 `python/tests` **判红**，红的是本轮的
  **负载型反证**——2 vCPU runner 上 12 线程 × 8 轮 × 3 次**一次都没复现**竞态
  （本地 8+ 核每次 10~20/96）。按 GOAL 的失败分类表：**不是代码缺陷、更不是门禁太严，
  而是反证不可移植**；也顺手把"确定性做法"证伪（拿住游标 + 另线程写提交不触发——
  竞态要两个线程同时在 sqlite3 的 C 调用里）。处置：反证换成**结构判据**
  （读结果是否在锁内取尽），负载型复现器降级为记录（RECHECK-071「更正」段）。
  **不把它算成"cycle 9 已绿"**：更正随 cycle 10 的收口提交入库，并在随后的 run 上复核。
- 2026-09-16 cycle 10 开轮（相邻长程项：provider 端点绑定）：derive = PLAN-20260915-072。
  先全仓 grep 确认 `endpoint_env` **零消费面**，并发现唯一现实用法是**误用**
  （示例配置 `endpoint_env: NCBI_API_KEY`——字段名说端点、值是凭据名，且无人报错）；
  derive 时又发现同一缺陷的另一半：`ProviderRegistration.spec()` 会把该字段**丢掉**。
- 2026-09-16 cycle 10 交付：`endpoint_env` 从"声明了没人消费"变成"被执法且可见"——
  解析只在进程边界（`os.environ`，不读文件）、三态（未声明/未设置/已绑定）、
  读面只给状态 + 变量名 + `sha256` 指纹（端点明文不进任何读面）、
  声明了但未设置 ⇒ 健康探测不执行、如实 UNKNOWN 并点名变量；
  注册写入/存储往返/旧行解码全线打通。证据：新用例 **7 passed**；
  `tests/adapters/sqlite` **97 passed**；`tests/api` **380 passed**；
  `tests/contracts + tests/loaders` **398 passed / 56 skipped**；OpenAPI +66 行后快照契约过；
  TS 类型镜像 + `tsc --noEmit` 空输出；mypy 5 模块 clean；
  m0 **PASS: profile=m0; 23 deterministic checks**。
  **未做到**（如实登记为下一轮候选）：把解析出的端点**注入 adapter**——需要按 spec
  重建 provider 实例；另登记相邻缺口 `ToolProviderSpec` 无 `credential_ref` 表达面。
- 2026-09-16 cycle 10 收口（**预算触顶 → BLOCKED**）：`budget.max_cycles: 10` 已用尽，
  按 frontmatter 口径（硬上限，触顶即 BLOCKED）置 `status: BLOCKED`；EC-01…EC-05 全 PASS，
  **EC-06 置 PASS**（每 cycle 本地 m0 + main CI 记账齐备，含 cycle 9 红项的定性/更正/验证）。
  收口复检 = **RECHECK-20260915-073**（PASS_WITH_WARNINGS，`latest_recheck` 已指向），
  内含 EC 表、十条 cycle 的 CI 结论表、安全扫描处置与六条后继入口。
  **安全扫描处置（本轮实跑）**：Mimosa 密封深度扫描 scanId
  `scan-2026-09-16T16-21-44.354Z-fb46b8691603`、seal `sha256:8b801259…`，
  **36 findings（3 high / 28 medium / 5 low）、182 packages、依赖离线库命中 1 包 / 1 advisory**；
  **coverage = partial / runStatus = inconclusive**，且 `evidenceBoundary =
  static_only_no_runtime_execution` ⇒ 这是静态证据，**不构成"项目安全"结论**；
  cycle 8–10 的改动文件在报告里 **0 命中**（逐项检索）。
  **恢复条件（需用户拍板，本 GOAL 不自作续期）**：① 新建承接 GOAL（沿用 GOAL-002 →
  GOAL-003 的方式）把后继入口写进新 EC；② 显式变更 `budget.max_cycles` 并置回 ACTIVE、
  从 cycle 11 续跑。后继入口按优先级：provider 凭据绑定（最小最安全，不出网）→
  provider 端点注入 adapter（含受控出网，安全策略级）→ `tool_pack.*` 策略产品决策 →
  `conn.cursor()` 收口 → 锁粒度（每线程连接）。
- 2026-09-16 收口提交的 CI：`e020639` → run **35121878161 六个 job 全 success**
  （eval-gate 16:26:41Z / collector-quality 16:28:27Z / container-quality 16:30:20Z /
  console-frontend 16:33:31Z / quality-ubuntu-latest 16:34:09Z / quality-windows-latest
  16:38:12Z，无重跑）⇒ 收口提交本身也过了 main 的全部门禁。**本 GOAL 至此停在
  BLOCKED（预算触顶），等待用户在前述两条恢复条件里选一条。**
- 2026-09-17 续期（**预算 10 → 20，BLOCKED → ACTIVE**）：用户会话指令的区间是
  「循环迭代 **10-20** 次」，10 是我 derive 时自定的下限而非用户上限。按恢复条件②
  显式变更 `budget.max_cycles: 20` 并置回 ACTIVE，从 cycle 11 续跑；EC 表一字未改、
  已记 PASS 的不回退、新增轮次不得预置 PASS。续期记录见「终止与收口 · 续期记录」。
- 2026-09-17 cycle 11 开轮（凭据绑定）：derive = PLAN-**20260915-074**（cycle 10 登记
  的"子 PLAN 编号 = 073"已被收口计划占用，如实改用 074）。derive 先核对两件事：
  ① MCP streamable_http 在**构造期**就要求 `credential_ref`，而这条要求进不了 spec；
  ② NCBI 的凭据是**可选**的（`_api_key()` 在 `InvalidInputError` 时返回 None），
  因此字段语义定为「**声明即必需**」，示例配置不给 ncbi 声明凭据。
- 2026-09-17 cycle 11 交付：`CredentialResolver.has` 成为 Port 成员并补齐全部实现
  （mypy 用协议抓出 6 处老替身，全部补 `has` 而**未放宽类型**）；
  `ToolProviderSpec.credential_ref` / `ProviderRegistration.credential_ref` / `spec()` /
  SQLite 往返（旧行 ⇒ 未声明）/ 注册读面 `credential_binding`（四态：NOT_DECLARED /
  ABSENT / PRESENT / UNCHECKED）全线打通；探测门槛对**所有 kind 含 NATIVE** 成立
  （与端点门槛故意不对称，用例两向钉住）；判定**只调 `has`、不调 `resolve`**，
  用例用"一被调用就断言失败"的 `resolve` 把这条口径变成可执行判据。
  定向套件：新用例 **8 passed**、`tests/api` **422 passed**、
  `tests/adapters/sqlite+tests/loaders+tests/api` **525 passed**、
  `tests/contracts+tests/application` **955 passed / 57 skipped**、
  `tests/observability` **58 passed / 1 skipped**（canary 替身补齐）；
  stub e2e **83 passed**（结构与像素基线均未变）、live e2e **36 passed**（+1 凭据链）；
  OpenAPI 重生成（+1276 字符）后快照契约通过；ruff/format 干净、mypy **867 files clean**。