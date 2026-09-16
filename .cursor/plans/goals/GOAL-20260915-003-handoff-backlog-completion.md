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
    status: PARTIAL
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
    status: PENDING
  - id: EC-05
    criterion: >-
      替身 harness 校验 Idempotency-Key：缺头 → 422（与真中间件同语义），
      使 stub 套件能守住 mutating 契约，不再依赖 live 套件兜底
    verify: >-
      harness 头校验 + 反证（客户端去掉该头 → stub 用例失败）+ 全量 stub 套件绿
    status: PENDING
  - id: EC-06
    criterion: >-
      治理收口：每个 cycle 本地 m0 与 main 的 CI 全绿；收口 RECHECK + 安全扫描处置；
      GOAL 收口时把仍未处理的长程项写成后继入口
    verify: >-
      每 cycle CI run 六 job 结论；收口 RECHECK = PASS 或 PASS_WITH_WARNINGS
    status: PENDING
budget:
  max_cycles: 10
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
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-066-ops-schedules-write-surface.md
memory_entries:
  - MEM-20260915-038-structural-signature-complements-pixel-gate
  - MEM-20260915-039-tool-pack-install-binds-content-digest
  - MEM-20260915-040-pending-must-be-visible-in-ui
  - MEM-20260915-041-scheduler-remains-the-executor
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
| EC-02 | ToolPack install/approve 供应链面 | OpenAPI 写方法 + API/live e2e | **PARTIAL**（2026-09-16 cycle 2：后端写面已交付——三条文档化端点 + SQLite store + digest 重算自证 + 扩张待批准 + capability 取值域 + 目录消费，OpenAPI/契约/文档/pageSupport 全部收敛；2026-09-16 cycle 3：**console 操作面已交付**——`ops/integrations` 面板（安装表单 / 待批准横幅含 diff 明细与候选 digest / 批准 / 吊销理由必填）、stub 6 + live 2 各一条链、两条设计基线重生成；**仍未交付**：健康复核记录 schema digest 并可比对漂移（provider 侧，需先定探测面），以及 provider 凭据绑定；另发现平台默认策略未放行 `tool_pack.*`（default DENY，见 RECHECK-065 W-1）——三项都记在「下一轮输入」） |
| EC-03 | ops 调度用户可见写面 | OpenAPI 写方法 + pageSupport 收敛 + e2e | PASS（2026-09-16 cycle 4：`ops/schedules` 的 `disabledOperations` 相应项消失、`management_available=true`；**执行体仍是既有守护线程**——`trigger` 调用的就是定时 pass 的**同一个函数对象**（用例以计数器证明），`enabled=false` 被守护线程**自己的读面**（`due(job)`）消费（真实线程 + 可控时钟：停用后 `run_count` 冻结）。诚实的边界都在用例里：无 store → 静态兜底 + 写操作 503；未挂执行体 → `executor_attached=false` 且 trigger 禁用；从未跑过 → `last_outcome=null`（前端显示 UNKNOWN）；pass 失败 → 200 + `FAILED` + `last_error`。范围注记：`run_count` 等事实是**进程内观测**（重启归零，不是配置）；调度写面**不经过 policy**（等价于启停既有守护线程），若要审批需新增 `schedule.*` 能力——见 RECHECK-066 W-6） |
| EC-04 | worker 退出语义（SIGTERM 有界中断阻塞读） | 定向用例 + 反证 + Linux 容器复验 | PENDING |
| EC-05 | 替身 harness 校验 Idempotency-Key | 头校验 + 反证 + stub 套件绿 | PENDING |
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
**cycle 5 待开轮**：EC 表首个未满足项是 EC-04（worker 退出语义：SIGTERM 有界中断
阻塞中的 HTTP 读）；EC-02 仍有未交付子句（provider 侧健康复核 schema digest 漂移 +
凭据绑定）与 RECHECK-065 W-1（`policy.yaml` 未放行 `tool_pack.*` 的产品决策），
已在「下一轮输入」备选。BLOCKED 处置模板见「终止与收口 · BLOCKED 记录（已解除）」。
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

## 状态历史

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