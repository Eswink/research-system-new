---
id: GOAL-20260915-003
slug: handoff-backlog-completion
title: 收口清单续做：设计门禁结构判据、ToolPack 供应链面、ops 调度写面、worker 退出语义、替身守卫
status: BLOCKED
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
    status: PENDING
  - id: EC-03
    criterion: >-
      ops 调度用户可见写面：schedule 的创建/启停/触发从"只读事实"变成真实写面
      （进程内 scheduler 仍是执行体，不新造第二套调度器）
    verify: >-
      OpenAPI 写方法 + ops/schedules 的 disabledOperations 相应项消失 +
      API + live e2e 用例
    status: PENDING
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
    status: BLOCKED
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
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-063-design-gate-structural-criterion.md
memory_entries:
  - MEM-20260915-038-structural-signature-complements-pixel-gate
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
| EC-02 | ToolPack install/approve 供应链面 | OpenAPI 写方法 + API/live e2e | PENDING |
| EC-03 | ops 调度用户可见写面 | OpenAPI 写方法 + pageSupport 收敛 + e2e | PENDING |
| EC-04 | worker 退出语义（SIGTERM 有界中断阻塞读） | 定向用例 + 反证 + Linux 容器复验 | PENDING |
| EC-05 | 替身 harness 校验 Idempotency-Key | 头校验 + 反证 + stub 套件绿 | PENDING |
| EC-06 | 每 cycle m0/CI 全绿 + 收口复检 + 安全扫描处置 | CI run 六 job 结论 + RECHECK | **BLOCKED**（2026-09-16 cycle 1：GitHub Actions 账户级计费阻断，六个 job 均未启动，详见「终止与收口」；本地 m0 = 23/23 已绿，CI 不可验证） |

**不变量（沿用 GOAL-001/002 与 AGENTS.md）**：不伪装实现（不注册没人消费的写面、
不让 fixture 冒充业务数据）；默认 deny 的安全姿态不变；观测隐私不变；每一项写面必须走
既有 policy/preflight 门链；**判据只允许增强，不允许为了让测试通过而削弱**
（本 GOAL 的 EC-01 与 EC-05 本身就是"把门禁变强"，与 fix_policy 的"不得改门禁使其通过"
不冲突：前者是交付物，后者是作弊）。**规模标注**：EC-02 为 M/L（供应链语义最重）、
EC-03 为 M、EC-04 为 M（进程信号语义）、EC-05 为 S、EC-01 为 M。

## 循环入口协议

按 README 的 7 步判定执行；当前续点：**cycle 1 已交付（PLAN-20260915-063：
设计门禁结构判据——33 条路由结构签名 + 反证用例 + 跨平台一致性，EC-01 = PASS；
RECHECK-063 见 `latest_recheck`），但 CI 因账户级计费阻断 ⇒ 本 GOAL = BLOCKED
（状态与恢复条件见「终止与收口」）**。
BLOCKED 期间的入口判定（README 第 7 条 + 驱动适配）：驱动进入时若 `status != ACTIVE`
即直接结束，不推进 cycle；只有恢复条件满足（CI 恢复可用、六 job 全 success 回填）后
才置回 ACTIVE 并执行 ①。
恢复后的下一个动作 = ① derive：取 EC-02（ToolPack install/approve 供应链面），
子 PLAN 编号续全局序列（下一号 = **PLAN-20260915-064**）。
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

### 当前 BLOCKED（2026-09-16，cycle 1）

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

**已确证的部分（不受阻断影响）**：EC-01 的全部证据都是本地/容器可复现的——
m0 `23 deterministic checks`、stub e2e 66 / live e2e 31 / 单测 76、eslint 0 error、
`tsc --noEmit` 通过、结构签名跨平台一致性（pinned noble 容器 33/33 逐字节一致）、
Mimosa 密封扫描本轮改动文件命中 0 条。阻断的只是"main 上六个 job 的远端复验"。
- **收口动作**：更新 EC 状态表、迭代日志、child_plans、memory_entries；把长程剩余项
  写入「终止与收口」供后继 GOAL 承接（不在本文件内隐藏缺口）。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20260915-063（EC-01：设计门禁结构判据） | 见本 cycle 提交 | 结构签名基线 33 条（`apps/web/tests/e2e/design-outlines.json`）；guard 用例 **6 passed**（注入可见面板/多一行/视口外节点/删节点 → 判红；只改样式 → 不误报；归一化 4 断言）；对照实验：多一行 **0.079%**、视口外 **0.000%** ⇒ 像素判据不报警而结构判据判红；跨平台一致性：linux 容器重算与 win32 **逐字节一致**（33/33）；全量 stub e2e / live e2e / 单测 / m0 见「证据」段 | run **35056976439**（5a44445）：**失败——但失败在启动前**：六个 job 全部 `runner_id=0`、无 step、2 秒内结束（attempt 1 与 rerun attempt 2 同形）；check-run 注释原样给出根因 *"The job was not started because recent account payments have failed or your spending limit needs to be increased"* ⇒ 账户级计费阻断，非代码/门禁缺陷（详见「终止与收口 · 当前 BLOCKED」）。**本 cycle 的 CI 结论记 FAIL（infra），不记 PASS** | 首次实现踩到三处：① 用 `toMatchSnapshot` 会得到 per-platform `-win32.txt` 基线（CI 在 ubuntu 上必然缺文件）⇒ 改成单一 JSON 基线 + 显式 `UPDATE_OUTLINES=1` 更新；② ISO 正则没吃 `+00:00` 偏移 ⇒ 归一化残留导致 33 条基线含半截时间戳，修正则后重生成；③ 注入到 `body` 末尾的面板落在视口外，像素差 0.000% ⇒ 补"可见注入"用例作为真实对照 | EC-01 已 PASS（范围注记见 EC 表）；EC-02~05 PENDING；**EC-06 BLOCKED（账户级计费阻断 CI）** | **本 cycle 无下一轮**（GOAL = BLOCKED）：恢复条件满足后 cycle 2 = ① derive EC-02（ToolPack install/approve 供应链面：pin↔交付物绑定、能力取值域、schema digest 漂移），子 PLAN 编号 = PLAN-20260915-064 |

## 状态历史

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