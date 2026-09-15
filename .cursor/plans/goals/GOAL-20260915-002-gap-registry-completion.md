---
id: GOAL-20260915-002
slug: gap-registry-completion
title: 诚实缺口注册表收口：G9/G12/G8/G7/G15/G2 六项从「诚实禁用」转为「有真实消费者」
status: ACHIEVED
created_at: 2026-09-15
updated_at: 2026-09-16
owners:
  - root-agent
authorization:
  source: user-request
  ref: "2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」——GOAL-20260912-001 收口（ACHIEVED）后，本 GOAL 承接其长程迭代余量：候选缺口表（G9 全局血缘 / G12 跨 run 时序预测 / G8 workspace 文件树 / G7 ops 余项 / G15 tool-provider 写面 / G2 项目删除）由 GOAL-001「终止与收口 · cycle 12 长程排期」立项。push-to-main-for-CI 授权沿用 GOAL-001 的批准口径（只推 main、不 force、不推旁支触发 CI）。"
objective: >
  把前端的六个诚实缺口（pageSupport 中已如实标注的 partial/gap 项）逐个变成
  有真实后端消费者与真实页面的能力：G9 全局跨 run 血缘、G12 跨 run 时序成本预测、
  G8 workspace 文件树与文件级快照 Diff、G7 ops 写面（告警规则/incident 处置/
  用户级 schedule/聚合报表）、G15 tool-provider 管理写面、G2 项目删除/归档；
  每一项要么交付并翻 live，要么产出 Accepted ADR 并在 pageSupport / CONSOLE_PAGE_MAP
  同步收敛（不留死端点、不用 fixture 冒充业务数据）。
exit_criteria:
  - id: EC-01
    criterion: >-
      G9 全局跨 run 血缘：项目作用域血缘投影（run/dataset/prompt 节点与边）落地并翻 live
    verify: >-
      OpenAPI 快照含项目级 lineage 路径；library/lineage 的 pageSupport reason 收敛；live e2e 用例绿
    status: PASS
  - id: EC-02
    criterion: >-
      G12 跨 run 时序成本预测：由 cost/daily 序列给出跨 run 预测（口径与计量完备状态如实标注）
    verify: >-
      OpenAPI 快照含预测路径；insights/cost-analytics 与 govern/budget 的 reason 收敛；API + live e2e 用例绿
    status: PASS
  - id: EC-03
    criterion: >-
      G8 workspace 文件树 + 文件级快照 Diff：只读文件树 API 与文件级 diff 接入页面；
      若判定不可行则产出 Accepted ADR 并同步收敛页面标注，且不留死端点
    verify: >-
      OpenAPI 快照路径 + live e2e 绿，或 ADR 文件（Accepted）+ pageSupport 文案一致
    status: PASS
  - id: EC-04
    criterion: >-
      G7 ops 写面：告警规则 CRUD 与 incident 处置（declare/assign/close）落地，页面去掉对应 disabledOperations
    verify: >-
      OpenAPI 快照写方法存在；ops/alerts 与 ops/incidents 的 disabledOperations 相应项消失；API + live e2e 绿
    status: PASS
  - id: EC-05
    criterion: >-
      G15 tool-provider 管理写面：注册/更新/健康复核（当前只读投影 → 有真实写面与消费者）
    verify: >-
      OpenAPI 快照写方法存在；ops/integrations 的 disabledOperations 相应项消失；API + live e2e 绿
    status: PASS
  - id: EC-06
    criterion: >-
      G2 项目删除/归档 + 治理收口：项目归档/删除语义落地（被引用返回 409，不静默级联）；
      每个 cycle 本地 m0 与 main 的 CI 全绿；收口 RECHECK + 安全扫描处置
    verify: >-
      OpenAPI 快照含 DELETE/PATCH 项目路径 + 409 用例；每 cycle CI run 六 job 结论；
      收口 RECHECK = PASS 或 PASS_WITH_WARNINGS
    status: PASS
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
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
child_plans:
  - .cursor/plans/tasks/PLAN-20260915-054-netproxy-partition-heal.md
  - .cursor/plans/tasks/PLAN-20260915-055-project-scope-provenance-lineage.md
  - .cursor/plans/tasks/PLAN-20260915-056-blackhole-must-be-effective-on-return.md
  - .cursor/plans/tasks/PLAN-20260915-057-project-scope-cost-forecast.md
  - .cursor/plans/tasks/PLAN-20260915-058-workspace-snapshot-tree-and-file-diff.md
  - .cursor/plans/tasks/PLAN-20260915-059-ops-write-surface-rules-and-incidents.md
  - .cursor/plans/tasks/PLAN-20260915-060-tool-provider-registration-and-governance-write-surface.md
  - .cursor/plans/tasks/PLAN-20260915-061-project-delete-and-archive-semantics.md
  - .cursor/plans/tasks/PLAN-20260915-062-goal-002-closeout-recheck.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-062-goal-002-closeout.md
memory_entries:
  - MEM-20260915-031-partition-injector-must-heal
  - MEM-20260915-032-project-lineage-merge-and-honest-unlinked-resources
  - MEM-20260915-033-series-projection-valued-days-only
  - MEM-20260915-034-digest-addressed-snapshot-read-surface
  - MEM-20260915-035-write-surface-must-be-consumed-by-read-surface
  - MEM-20260915-036-registration-state-derives-trust
  - MEM-20260915-037-delete-must-refuse-when-referenced
  - MEM-20260915-030-goal-closeout-verification-recipe
---

# GOAL-20260915-002 — 诚实缺口注册表收口（自迭代循环）

## 目标与退出标准

格式规范与循环 SOP 见 [README.md](README.md)。本 GOAL 是 GOAL-20260912-001
（ACHIEVED，2026-09-15）的长程承接：GOAL-001 把 33 条规范路由全部变成「live-capable 且
**诚实标注缺失面**」；本 GOAL 的目标是把其中**仍然缺失的六个能力**做成真实能力，
而不是把标注改小。

| EC | 标准（摘要） | 验证 | 状态 |
| --- | --- | --- | --- |
| EC-01 | G9 全局跨 run 血缘（项目作用域节点/边） | OpenAPI + pageSupport + live e2e | PASS（2026-09-15 cycle 2；范围注记：跨 run 关系由**共享节点**表达，库资源以未连边清单交付——资源↔run 边无记录面，见 RECHECK-055 W-1） |
| EC-02 | G12 跨 run 时序成本预测 | OpenAPI + API/live e2e + 计量口径 | PASS（2026-09-15 cycle 3；范围注记：外推只吃**已计价的天**（`MEAN_OF_VALUED_DAYS`），排除项逐日给原因、跨币种不给金额；无趋势/置信区间，见 RECHECK-057 W-1/W-2） |
| EC-03 | G8 workspace 文件树 + 文件级 diff（或 Accepted ADR 收敛） | OpenAPI/ADR + live e2e | PASS（2026-09-15 cycle 4；范围注记：按 digest 只读、需配置 `RESEARCHOS_WORKSPACE_SNAPSHOT_ROOT`；无 run→工作区绑定记录面 ⇒ run 面只回答"记录过哪些快照"，见 RECHECK-058 W-1/W-2） |
| EC-04 | G7 ops 写面（告警规则 CRUD + incident 处置） | OpenAPI 写方法 + pageSupport 收敛 | PASS（2026-09-16 cycle 5；范围注记：静音只打 `muted/muted_by` 标记**不隐藏**告警、候选不会自动变事故、已关闭再处置 409；`assignee` 无成员校验，见 RECHECK-059 W-2/W-3） |
| EC-05 | G15 tool-provider 管理写面 | OpenAPI 写方法 + pageSupport 收敛 | PASS（2026-09-16 cycle 6；范围注记：信任级别由注册状态推导（PENDING→UNTRUSTED/ACTIVE→USER_APPROVED），注册方不能声明 BUILT_IN/VERIFIED；pin 必须是 `sha256:<hex>` 且作为 `tool_pack_digests` 被 preflight 消费；REVOKED 为终态（再处置 409）；capabilities 取值域与 digest 真实性未校验、健康复核无 schema 漂移比对，见 RECHECK-060 W-2/W-3/W-4） |
| EC-06 | G2 项目归档/删除 + 每 cycle 门禁/CI 全绿 + 收口复检 | DELETE/PATCH + 409 用例 + CI run + RECHECK | PASS（2026-09-16 cycle 7；范围注记：删除只对**无引用**项目可用——被 runs/草稿/实验队列/库资源/ops 记录引用即 409 并列出引用、**不级联**；`example-project` 为合成基线 409；删除活动项目后的上下文回退是**前端行为**，后端无"当前项目"概念；草稿引用计数有 200 上限，见 RECHECK-061 W-3/W-4/W-5） |

**不变量（沿用 GOAL-001 与 AGENTS.md）**：不伪装实现（不注册没人消费的 scheduler/规则、
不让 fixture 冒充业务数据）；默认 deny 的安全姿态不变；观测隐私（不记录完整 Prompt）
不变；每一项写面必须走既有 policy/preflight 门链。**规模标注**：G8 为 L（控制面当前
没有 workspace 快照枚举面）、G7/G9/G12/G15 为 M、G2 为 S。

## 循环入口协议

按 README 的 7 步判定执行；**循环已收口（status=ACHIEVED，2026-09-16 cycle 8）**：
六个 EC 全 PASS（EC-01 G9 项目级血缘 / EC-02 G12 项目级成本预测 / EC-03 G8 工作区快照
文件树与文件级 Diff / EC-04 G7 ops 写面 / EC-05 G15 tool-provider 注册治理写面 /
EC-06 G2 项目删除语义），独立复检 `RECHECK-20260915-062` = PASS_WITH_WARNINGS
（`scratch/verify_goal002_closeout.py` 59 条证据面断言 + 8 个 CI run 逐 job 现读全绿）。
**本文件不再接受新的 cycle**：长程剩余项见「终止与收口 · 收口结论」表，后继工作另立
GOAL（入口建议：① 设计门禁容差盲区 ② ToolPack install/approve ③ M18 租户/RBAC）。
driver=session-goal，owner=root-agent（已停止推进）。

## 驱动

驱动无关（README「驱动适配」）：默认会话驱动；需要无人值守时挂定时自动化，指令模板见
README（仅当 status=ACTIVE 时推进）。进入 cycle 时在迭代日志声明 driver/owner；
同一时刻仅一个驱动推进。

## 单 cycle SOP

按 README ①~⑦ 执行。本实例附加约定：

- ① derive 的主题顺序默认取 EC 表首个 PENDING；若上一 cycle 部分交付，则以其「下一轮输入」为准。
- 子 PLAN 必须独立可验收、独立 RECHECK；GOAL 只在 EC 层面记账。
- ③ 本地验证：m0 全量（23 项）+ 受影响定向套件 + web 门（lint/typecheck/unit/build/stub e2e/live e2e）
  + 设计基线（页面改动时按既有流程强制重生成并目检）。
- ⑤ push 前 `git pull --ff-only origin main`（并发历史先 rebase，不 force）。
- 每个 EC 允许拆到多个 cycle；部分交付记 `PARTIAL`，不得预置 PASS。

## CI 失败分类与纠错

按 README 分类表执行；本仓已知 flake/env 签名（重跑不修）：observability OTLP teardown race、
m0 全量单跑在负载下的 timing 用例（隔离复跑对照）、DSN 注入（需固化配方）、
`framework/run_cursor_framework_evals` 在 Windows 上偶发文件占用（复跑对照）。
`.github/workflows/m0-quality.yml` 属治理面：循环内不修改；需要改动即 BLOCKED 提请人工。

## 终止与收口

- **ACHIEVED** 前置：六个 EC 全 PASS（或经 Accepted ADR 收敛）+ 独立 RECHECK
  PASS/PASS_WITH_WARNINGS + 本文件收口（`latest_recheck` 指向该 RECHECK）。
- **BLOCKED**：预算触顶（`max_cycles` 或 `no_progress_stop_cycles`）、命中 escalation_triggers、
  或同一失败签名超过 `fix_policy` 上限；恢复条件必须写清（哪些 EC 未达成、需要谁决定什么）。
- **收口动作**：更新 EC 状态表、迭代日志、child_plans、memory_entries；把长程剩余项
  写入「终止与收口」供后继 GOAL 承接（不在本文件内隐藏缺口）。

### 收口结论（2026-09-16，cycle 8）

**status = ACHIEVED**。六个 EC 全 PASS 且经独立复检（RECHECK-20260915-062 =
PASS_WITH_WARNINGS）在**当前树**上重新验证：`scratch/verify_goal002_closeout.py`
的 59 条证据面断言全过；cycle 1~7 的 8 个 CI run 经 GitHub API 逐 job 重读，
**每个 run 六个 job 全 success**（含收口前的 cycle 7 run 35018256116）。

收口后**仍然开放**的长程项（后继 GOAL 承接，不在本文件内隐藏）：

| # | 长程项 | 来源 |
| --- | --- | --- |
| 1 | **设计门禁容差盲区**：整块新增内容后旧基线只差 0.48%~1.73%，低于 `maxDiffPixelRatio: 0.02` ⇒ 门禁不报警；页面改动必须主动重生成基线并目检 | RECHECK-055/057/059/060/061 W-1 |
| 2 | **替身不校验 `Idempotency-Key`**：stub harness 只匹配 method+path，mutating 约束只有 live/中间件能守 | RECHECK-061 W-2 |
| 3 | **worker SIGTERM 打不断阻塞中的 HTTP 读**（退出上界 = 客户端 30s 超时） | RECHECK-054 W-1（结转） |
| 4 | **供应链面**：capabilities 取值域不是授权边界；`pinned_revision` 只校验形态；健康复核无 schema 漂移比对；ToolPack install/approve 面仍未提供 | RECHECK-060 W-2/W-3/W-4 |
| 5 | **删除面边界**：草稿引用计数上限 200；不做跨项目引用检查；活动项目回退是前端行为 | RECHECK-061 W-3/W-4/W-5 |
| 6 | **平台面**：成员/RBAC/租户隔离（M18 deferred）、`ops/schedules` 无用户可见创建/启停、聚合报表仍禁、Memory 之外的身份/Billing 面未提供 | GOAL-001 结转 + `pageSupport` |
| 7 | **环境供给**：`infra/compose/research-validation.yaml` 的 evidence 目录缺口 | GOAL-001 结转 |
| 8 | **安全声明**：`scanner_enobufs` 期间 hook 扫描无结论，循环内以独立 Mimosa 密封扫描替代（cycle 7 = 36 findings / 3 high，本轮改动文件命中 0 条）；**不主张项目整体安全** | 各 cycle 状态历史 |

后继 GOAL 的入口 = 从本表任选主题（建议优先级：① 门禁盲区 → 用更强的像素/结构判据替代
纯比率阈值；② 供应链面 ToolPack install/approve；③ 平台面 M18 租户与 RBAC）。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20260915-054（CI 债：分区注入器真实性） | e6f09cb | 新语义用例 3 passed + 反证 `legacy: SWALLOWED / fixed: ECHOED`；Linux 容器 D 场景 5/5、`tests/distributed` 全量 25 passed / 4 skipped / 0 failed；本地 m0 23/23；RECHECK-054 = PASS_WITH_WARNINGS | run 34960364156（e6f09cb）：**六个 job 全 success**（quality-ubuntu-latest / quality-windows-latest / console-frontend / container-quality / eval-gate / collector-quality）——对照修复前 run 34957121713 的 collector-quality 失败 | 旧 `_stall` 消费并丢弃分区期间的字节且连接线程直接结束 ⇒ `restore()` 无法恢复在途请求，worker 阻塞到 30s 客户端超时、SIGTERM 打不断阻塞读 ⇒ D 场景 teardown `wait(10)` 超时（cycle 13 收口提交的 CI 红）；另修宿主 venv 被容器 `uv sync` 覆盖的事故（已重建并验证） | EC-01~06 全部 PENDING（本轮为 EC-06 的门禁债前置，已清零） | cycle 2 = ① derive EC-01（G9 全局跨 run 血缘），子 PLAN 编号 = PLAN-20260915-055 |
| 2 | PLAN-20260915-055（EC-01：G9 项目级来源血缘）+ PLAN-20260915-056（门禁轮：`blackhole()` 返回即生效） | 见本 cycle 提交 | API 6 passed；stub e2e **40 passed**、live e2e **20 passed**；根 eslint 0 error；web lint/typecheck 通过 + 单测 76 passed；设计基线（win32 本地 + linux pinned 容器）重生成（实测陈旧基线仅差 1.73% ⇒ 旧基线不会报警）；本地 m0 **23/23**（3411 passed / 6 skipped）；RECHECK-055/056 = PASS_WITH_WARNINGS | run **34969935719**（ecf0ebf）：**六个 job 全 success**（quality-ubuntu-latest / quality-windows-latest / console-frontend / container-quality / eval-gate / collector-quality） | ① 全页目检发现 `.cards` auto-fit 网格把 4 列节点表裁列 ⇒ 新增 `.stack` 整宽堆叠（先修复再重生成基线）；② 陈旧设计基线与新渲染只差 **15,933 px = 1.73%**，低于 2% 阈值 ⇒ 基线不会报警，必须主动重生成；③ m0 全量在 Windows 上暴露 `blackhole()` 竞态（泵已阻塞在 `recv` ⇒ 标志置了但仍转发）⇒ `blackhole()` 改为等分区生效（有界 2s），PLAN-056 单独记账 | EC-02~06 PENDING | cycle 3 = ① derive EC-02（G12 跨 run 时序成本预测），子 PLAN 编号 = PLAN-20260915-057 |
| 3 | PLAN-20260915-057（EC-02：G12 项目级成本预测） | 见本 cycle 提交 | 纯函数 7 passed + API 7 passed（项目隔离/unattributed/幽灵项目/422/503）；契约 **355 passed / 56 skipped**；stub e2e **41 passed**、live e2e **21 passed**；根 eslint 0 error + web lint/typecheck 通过 + 单测 76 passed；设计基线 `insights-cost-analytics` / `govern-budget` × win32/linux 重生成并目检；本地 m0 **首跑红**（命名门禁：`liveSpecs.ts` 违反测试文件 kebab-case + Playwright 生成目录 `test-results/<中文用例标题>/` 被判非法路径）→ 修复后 **23/23**；RECHECK-057 = PASS_WITH_WARNINGS | run **34978272057**（d350e8e）：**六个 job 全 success**（quality-ubuntu-latest / quality-windows-latest / console-frontend / container-quality / eval-gate / collector-quality） | ① 命名门禁同时抓出**新文件命名**与**生成产物误判**两类问题 ⇒ 前者改名 `live-specs.ts`，后者把 gitignored 的 `test-results` 加入 `IGNORED_DIRECTORIES` 并补回归用例；② `live-*.spec.ts` 清单原在两份 playwright 配置里各写一遍，漏同步会让 stub 套件去连真实后端 ⇒ 抽 `tests/e2e/live-specs.ts` 单一来源（`--list` 复核 41/11 与 21/5 未漂移）；③ 三处新工程债登记为 RECHECK-057 W-1/W-2/W-3（日均方法与窗口语义） | EC-03~06 PENDING；EC-02 已 PASS（范围注记见 EC 表） | cycle 4 = ① derive EC-03（G8 workspace 文件树 + 文件级快照 Diff，或产出 Accepted ADR 收敛标注），子 PLAN 编号 = PLAN-20260915-058 |
| 4 | PLAN-20260915-058（EC-03：G8 工作区快照文件树 + 文件级 Diff） | 见本 cycle 提交 | 纯函数 8 passed / 读取器 12 passed / API 11 passed；契约 **383 passed / 56 skipped**；stub e2e **45 passed**、live e2e **25 passed**；根 eslint 0 error + web lint/typecheck 通过 + 单测 76 passed；`run-workspace` 设计基线 win32/linux 重生成并目检、design-fidelity 33 路由绿；本地 m0 **首跑红**（ruff：新增测试两行 101/102 字符）→ 修复后 **23/23**；RECHECK-058 = PASS_WITH_WARNINGS | run **34984686466**（05bcf04）：**六个 job 全 success**（quality-ubuntu-latest / quality-windows-latest / console-frontend / container-quality / eval-gate / collector-quality） | ① 全量 stub 套件被严格替身守卫拦下（新面板必然调用 run 快照面）⇒ 默认路由进共享替身表 `stub-routes-workspace.ts`，不逐用例打补丁；② 控制面首次读宿主目录 ⇒ 收窄为只接受 `sha256:<64hex>` digest、只在 `<root>/.snapshots` 内解析、symlink 一律拒绝、未配置即 503；③ `ArtifactDiffDto.note` 与 `REPRODUCTION_NOTE` 里「控制面无快照 diff 面」的旧表述同步收敛（否则新能力被旧文案否认） | EC-04~06 PENDING；EC-03 已 PASS（范围注记见 EC 表） | cycle 5 = ① derive EC-04（G7 ops 写面：告警规则 CRUD + incident 处置），子 PLAN 编号 = PLAN-20260915-059 |
| 5 | PLAN-20260915-059（EC-04：G7 ops 写面） | 见本 cycle 提交 | 控制面 10 passed + 读面口径 5 passed、全量 API **336 passed**；契约 3 passed（路径 + 写方法断言）；stub e2e **50 passed**、live e2e **28 passed**（含 3 条真实 HTTP 写链）；根 eslint 0 error + web `tsc --noEmit` 通过 + 单测 76 passed；`ops-alerts` / `ops-incidents` 设计基线 win32+linux 重生成并目检；本地 m0 **连续红了 4 次**（格式 / 50 行函数 / 循环依赖 / 命名，逐条修复）→ **23/23**；RECHECK-059 = PASS_WITH_WARNINGS | run **35002027768**（8148df4）：**六个 job 全 success**（quality-ubuntu-latest 17:43:08Z / quality-windows-latest 17:45:36Z / console-frontend / container-quality / eval-gate / collector-quality，无重跑） | ① 写面必须**被读面消费**：规则只打 `muted/muted_by` 标记不隐藏告警、登记事故回链来源 run 的告警、已登记 run 从候选移出；② 本地 m0 连红 **4 次**（格式 → 50 行函数 → 模块循环依赖 → 文件命名），逐条修复后才绿，全部如实记录；③ 本轮量化了**设计门禁的容差盲区**：整块新增面板后旧基线只差 **1.02% / 0.93%**（阈值 2%）⇒ 门禁不会报警，必须主动删基线强制重生成 + 目检（脚本 `scratch/cycle5-baseline-drift/measure.py`）；早期用"任一通道像素差 ≠ 0"得到的 ~40% 是误导性指标 | EC-05~06 PENDING；EC-04 已 PASS（范围注记见 EC 表） | cycle 6 = ① derive EC-05（G15 tool-provider 管理写面：注册/更新/健康复核），子 PLAN 编号 = PLAN-20260915-060 |
| 6 | PLAN-20260915-060（EC-05：G15 tool-provider 注册治理写面） | 见本 cycle 提交 | 控制面 **18 passed**（状态机/409/422/404/503 + 三态 preflight 消费证明 + 健康同源）、全量 API **354 passed**；契约 **358 passed / 56 skipped**（+648 行 OpenAPI 快照）；stub e2e **55 passed / 14 files**、live e2e **30 passed / 8 files**（含 2 条真实 HTTP 注册链）；根 eslint 0 error + web `tsc --noEmit` 通过 + 单测 76 passed；`ops-integrations` 基线 win32+linux 重生成并目检；本地 m0 **红了 3 次**（行宽 / 格式 / 类型，逐条修复）→ **23/23**；RECHECK-060 = PASS_WITH_WARNINGS | run **35011288950**（5714179）：**六个 job 全 success**（eval-gate 19:03:36Z / collector-quality 19:05:32Z / container-quality 19:06:51Z / console-frontend 19:11:18Z / quality-ubuntu-latest 19:12:35Z / quality-windows-latest 19:16:12Z，无重跑） | ① 消费证明必须由**同一输入在不同状态下结论不同**给出：`dataset.read`（examples 三 provider 都不声明）在 PENDING → `TOOL_UNAVAILABLE`、ACTIVE → 消失且无 `SUPPLY_CHAIN_UNPINNED`（pin 来自注册）、REVOKED → 回归；② 供应链写面的三条硬门：信任级别由状态推导（DTO 无该字段）、pin 必须 `sha256:<hex>`、内置 id 不影子覆盖；③ 健康复核与读面共用 `probe_provider_spec()`，杜绝"复核说健康、目录说不可证明"；④ 顺带清两处跨 feature 重复（`useOpsAction`→`hooks/useAsyncAction`、`OpsFields`→`components/InlineFields`）；⑤ 复现门禁容差盲区：0.79% / 0.66% ⇒ 不报警 | EC-06 PENDING；EC-05 已 PASS（范围注记见 EC 表） | cycle 7 = ① derive EC-06（G2 项目归档/删除语义 + `DELETE/PATCH /projects/{id}` + 409 用例 + 每 cycle 门禁/CI 全绿 + GOAL 收口复检），子 PLAN 编号 = PLAN-20260915-061 |
| 7 | PLAN-20260915-061（EC-06：G2 项目删除语义） | 见本 cycle 提交 | 删除语义 **7 passed**（无引用 204 / 被 runs·持久化 run·草稿·ops 引用各 409 且数据仍在 / 默认项目 409 / 未装配 503）、全量 API **361 passed**；契约 **359 passed / 56 skipped**（OpenAPI +34 行，仅新增 delete 操作）；stub e2e `project-delete.spec.ts` **4 passed**、全量 stub **59 passed / 15 files**；live e2e `live-project-registry.spec.ts` **2 passed**、全量 live **31 passed / 9 files**；根 eslint 0 error + web `tsc --noEmit` 通过 + 单测 76 passed；`portfolio-projects` 基线 win32+linux 重生成并目检；本地 m0 **首跑红**（治理校验：`MEM-20260915-037` 的来源 PLAN/RECHECK 尚未落盘——本轮先写记忆、后写计划所致）→ 补齐后 **23/23**；RECHECK-061 = PASS_WITH_WARNINGS | run **35018256116**（bc4a9aa）：**六个 job 全 success**（eval-gate 20:13:18Z / collector-quality 20:15:11Z / container-quality 20:16:35Z / console-frontend 20:21:05Z / quality-ubuntu-latest 20:22:10Z / quality-windows-latest 20:23:54Z，无重跑） | ① 删除的默认答案是**拒绝**：控制面能删的是注册行，删不掉用户的研究数据 ⇒ `_references()` 只枚举能证实的项目作用域存储并逐项计数（`runs=2, drafts=1`），存储层不级联、原因在路由层；② 合成行（`example-project`）**必须显式 409**——返回 204 会变成"删除成功但列表里还有"的静默陷阱，404 也不对（它确实存在）；③ **替身守不住 `Idempotency-Key`**（反证：去掉该头后 stub 4 用例仍全绿，随后还原）⇒ mutating 调用的该约束只有 live 套件能守；④ `ProjectDeleteAction` 首版 60 行超 50 上限 ⇒ 抽出 `useProjectDeletion.ts`（hook 文件名与导出同名）；⑤ 复现门禁容差盲区第三次：0.48% / 0.47% ⇒ 不报警 | 六个 EC 全部 PASS；剩余 = GOAL 收口复检（`PLAN-20260915-062`）+ 终止条款判定 | GOAL 收口：① derive 收口复检 PLAN（`PLAN-20260915-062`），逐条复核 EC-01~06 的判定标准与范围注记；② 通过后按 README 终止条款置 status=ACHIEVED 并写收口状态历史 |
| 8 | PLAN-20260915-062（收口复检：EC-01~06 × 当前树 + CI 逐 job 复核） | 见本 cycle 提交 | `scratch/verify_goal002_closeout.py` **59 条断言全 PASS**（EC-01 5 / EC-02 7 / EC-03 6 / EC-04 12 / EC-05 12 / EC-06 12 / 路由与基线 5）；CI 逐 run 现读：cycle 1~7 的 **8 个 run × 6 job 全 success**；治理 validate 绿；本地 m0 **23/23**；RECHECK-062 = PASS_WITH_WARNINGS | run **35021162088**（e879768）：**六个 job 全 success**（eval-gate 20:41:36Z / collector-quality 20:43:40Z / container-quality 20:44:57Z / quality-ubuntu-latest 20:49:08Z / console-frontend 20:49:09Z / quality-windows-latest 20:54:59Z，无重跑） | 无失败；结转告警 8 类原样保留（见「收口结论」表） | **GOAL 收口**：六个 EC 全 PASS ⇒ status=ACHIEVED、`latest_recheck` 指向 RECHECK-20260915-062；长程剩余项交给后继 GOAL | 本 GOAL 无下一轮。后继 GOAL 建议入口 =「收口结论」表优先级 ① 门禁盲区 ② ToolPack install/approve ③ M18 租户/RBAC |

## 状态历史

- 2026-09-15 创建（ACTIVE）：GOAL-20260912-001 收口（ACHIEVED，RECHECK-20260915-053）后，
  按用户「循环迭代 10-20 次」的授权承接长程迭代；范围 = GOAL-001「终止与收口 · cycle 12
  长程排期」的候选缺口表（G9/G12/G8/G7/G15/G2），六项各立一个 EC。
- 2026-09-15 cycle 1（CI 债，非 EC 交付）：GOAL-001 cycle 13 的收口提交 `8d18c5e`（只改
  `.cursor/**` 记录）在 CI run `34957121713` 上 collector-quality 失败
  ——`test_scenario_d_network_partition_no_old_authority` teardown `subprocess.TimeoutExpired
  (d-partitioned, 10s)`。根因定位到**故障注入器语义缺陷**：`NetProxy._stall` 用 `recv()`
  消费并丢弃分区期间的字节、且连接线程随即结束，`restore()` 无法恢复在途请求；调用方只能
  等自己的 HTTP 超时（worker client 30s），而 SIGTERM 的 handler 只能置标志（主线程阻塞在
  socket 读，PEP 475 重启该系统调用）⇒ 进程 10s 内不退出。修法：`_stall` 改 `MSG_PEEK`
  观测、分区解除后回到泵循环（字节留在内核缓冲，恢复后送达）。新增 3 条 loopback 语义用例
  + 反证脚本（旧语义 `SWALLOWED`／修复后 `ECHOED`）；Linux 容器内 D 场景 5/5、
  `tests/distributed` 全量 25 passed / 0 failed；本地 m0 23/23。RECHECK-054 =
  PASS_WITH_WARNINGS（W-1 = worker 的 SIGTERM 打不断阻塞中的 HTTP 读、退出上界 = 客户端
  30s 超时，登记给后续 EC 决策）。六个 EC 仍全部 PENDING。
- 2026-09-15 cycle 2（EC-01 = G9 项目级来源血缘，**PASS**）：`GET /projects/{project_id}/lineage`
  把 run 级投影规则（`services/api/lineage_projection.py`，run 级与项目级共用）作用到项目内
  每个 run 并按节点 id 合并 ⇒ **共享节点即跨 run 关系**（`shared = len(run_ids) > 1`）；
  库资源（dataset/prompt/notebook）以**未连边清单**交付，响应带
  `reference_recording=NOT_RECORDED` + 原因（协议定义只有 `id/version/phases`、`RunManifest`
  只有 `evaluation_dataset_digest` 摘要、evidence 的 `source_ref` 不支持资源 id ⇒ 资源↔run
  的边**当前不可证**，不猜边）。前端 `library/lineage` 新增 `ProjectLineagePanel`
  （摘要 + 节点/边/未连边资源三表 + 诚实说明），`pageSupport` 的 G9 reason 收敛为
  「已接入 + 记录面边界」。验证：API 6 passed；stub e2e 40 passed、live e2e 20 passed；
  根 eslint 0 error；web 单测 76 passed；`library-lineage` 设计基线 win32/linux 重生成；
  本地 m0 23/23。RECHECK-055 = PASS_WITH_WARNINGS（W-1 记录资源↔run 边的不可交付边界）。
  同 cycle 门禁轮另立 **PLAN-20260915-056**：本地 m0 全量在 Windows 上暴露
  `NetProxy.blackhole()` 的"标志已置但分区未生效"竞态（泵已阻塞在 `recv`，置标志后的下一批
  字节仍被转发）⇒ 改为等 `stalled_connections >= live_connections`（有界 2s）；定向用例
  8/8、`tests/distributed` 32 passed、m0 23/23；RECHECK-056 = PASS_WITH_WARNINGS。
  本轮提交 `ecf0ebf` 的 CI run **34969935719 六个 job 全 success**。安全面：Mimosa 密封扫描
  （36 findings / 3 high，`verdictEffect: none`）对账后**本轮改动文件命中 0 条**；3 条 high 为
  ① `protocol_authoring/service.py` 的 `yaml.load(_StrictLoader)`——已知误报（`SafeLoader`
  子类 + `# noqa: S506`，与 `yaml.safe_load` 同安全级）、② 与本产品无关的
  `artifacts/钻孔官方API_v12/` 第三方产物目录两条路径穿越。**不主张项目整体安全**。
- 2026-09-15 cycle 3（EC-02 = G12 项目级成本预测，**PASS**）：新增纯函数
  `packages/application/cost/series_projection.py`（口径 `MEAN_OF_VALUED_DAYS`）与
  `GET /projects/{project_id}/cost-forecast`——把项目 runs 的已记录用量按 UTC 日投影成序列，
  **只对已计价的天**（`ACTUAL`/`ESTIMATED`/`ZERO` 且金额非空）取日均再外推，视野 1~90 天；
  每个未进样本的天都随响应返回 `exclusion_reason`（`USAGE_UNKNOWN`/`MONETARY_UNAVAILABLE`/
  `NO_DATA`/`CURRENCY_CONFLICT`/`PARTIALLY_METERED`/`MIXED_PRICING`），样本跨币种时
  `projected_minor=null` + `CURRENCY_CONFLICT`（不做隐式换算、不插值、缺失不当 0）。
  项目归属按 run 解析：其它项目的已知 run 明确排除，归属不明的条目只计数
  （`unattributed_entries` + `attribution_note`）不猜项目。前端新增
  `ProjectCostForecastPanel`（成本分析页 + 预算页共用），`pageSupport` 的
  `GAPS.costSeries`/`budgetForecast` 两条 reason 由"不绘制预测"收敛为"已接入 + 口径边界"；
  `insights-cost-analytics` 与 `govern-budget` 的 win32/linux 设计基线重生成并目检。
  验证：纯函数 7 passed、API 7 passed、契约 355 passed、stub e2e **41 passed**、
  live e2e **21 passed**、根 eslint 0 error、web 单测 76 passed。
  本轮顺带清两处工程债：① `live-*.spec.ts` 清单原在两份 playwright 配置里各写一遍（漏同步会让
  stub 套件连真实后端）⇒ 抽 `apps/web/tests/e2e/live-specs.ts` 单一来源；② **本地 m0 首跑红**
  ——命名门禁拦下新文件 `liveSpecs.ts`（测试/夹具须 kebab-case）与 Playwright 生成目录
  `apps/web/test-results/<中文用例标题>/`（`.gitignore` 已忽略但仍被扫描）⇒ 改名
  `live-specs.ts`、把 gitignored 的 `test-results` 加入 `IGNORED_DIRECTORIES` 并补回归用例，
  复跑 m0 **23/23**（该失败如实记入 RECHECK-057，未掩盖）。RECHECK-057 =
  PASS_WITH_WARNINGS（W-1 日均方法无趋势/置信区间；W-2 窗口无默认值；W-3 归属不明的条目
  使序列偏小；W-5 生成目录与命名门禁的边界）。本轮提交 `d350e8e` 的 CI run
  **34978272057 六个 job 全 success**。安全面：Mimosa 密封扫描（`scan-2026-09-15T13-43-39.799Z-
  1c3d6ade595d`，seal `sha256:03ad88a1…`，36 findings / 3 high，`verdictEffect: none`）对账后
  **本轮改动文件命中 0 条**；3 条 high 仍是既有两条路径穿越（`artifacts/钻孔官方API_v12/`）与
  `protocol_authoring/service.py` 的已知误报。注：提交/推送时 Cursor hook 自带的扫描未取得结论
  （`scanner_enobufs`），上面的密封结论来自独立重跑的完整审计。**不主张项目整体安全**。
- 2026-09-15 cycle 4（EC-03 = G8 工作区快照文件树与文件级 Diff，**PASS**）：新增应用层纯函数
  `packages/application/workspace/snapshot_tree.py`（树枚举 + 文件级 diff）、独立能力协议
  `packages/application/ports/workspace_snapshot.py`（`WorkspaceSnapshotReader`，不改既有
  `WorkspaceBackend` 契约）、适配器 `adapters/workspace/snapshot_reader.py`（只读
  `<root>/.snapshots/<digest hex>/`）与四条只读端点：`GET /workspace-snapshots`（能力面）、
  `/workspace-snapshots/{digest}/files`（文件树：路径/大小/sha256）、
  `/workspace-snapshots/{left}/diff/{right}`（文件级 diff：ADDED/REMOVED/CHANGED + unchanged，
  只比元数据）与 `GET /runs/{run_id}/workspace-snapshots`（该 run 记录过的 digest + `retained`）。
  **安全收窄**：控制面首次读宿主目录 ⇒ 只接受 `sha256:<64hex>` digest（调用方无法表达路径）、
  只在 `<root>/.snapshots` 内解析、快照内 symlink 一律 `POLICY_DENIED`、未配置
  `RESEARCHOS_WORKSPACE_SNAPSHOT_ROOT` 即 503（不猜默认路径、不用空树冒充）。前端
  `WorkspaceSnapshotPanel` 接入 `run/workspace`（记录清单 + 文件树 + 文件级 diff + 逐项原因），
  `pageSupport.GAPS.fileBrowse` 收敛、`run/workspace` 的 `disabledOperations` 清空，
  `CONSOLE_PAGE_MAP` 页面级与 G8 行同步；旧文案「控制面无快照 diff 面」
  （`ArtifactDiffDto.note`、`REPRODUCTION_NOTE`）同步改写——新能力不能被旧否认句留着。
  验证：纯函数 8 passed、读取器 12 passed、API 11 passed、契约 383 passed、
  stub e2e **45 passed**、live e2e **25 passed**（live 侧由 `console_api_app` 建临时快照根 +
  受控 run，真实 HTTP 走通"digest → 文件树 → 文件级 diff"）、根 eslint 0 error、web 单测 76 passed、
  `run-workspace` win32/linux 基线重生成并目检。本轮两处失败如实记录：m0 首跑红于 ruff 行长
  （新增测试两行 101/102 字符）、全量 stub 套件红于严格替身守卫（新面板必然请求 run 快照面）
  ⇒ 后者按既有惯例把默认路由补进共享替身表 `stub-routes-workspace.ts`。RECHECK-058 =
  PASS_WITH_WARNINGS（W-1 无 run→工作区绑定记录面；W-2 快照无 retention；W-3 digest 依赖执行链
  真的产出过快照；W-4 `stub-routes.ts` 已 403 行、接近硬上限）。本轮提交 `05bcf04` 的
  CI run **34984686466 六个 job 全 success**（quality-windows-latest 15:06:31Z 收尾）。

- 2026-09-16 cycle 5（EC-04 = G7 ops 写面，**PASS**）：把 `ops/alerts` 与 `ops/incidents` 的
  "规则 CRUD 无 API""无处置工作流"两处诚实缺口做成真实写面——域
  `packages/domain/ops_control.py`（`AlertRule` + `Incident` + `IncidentStatus` 状态机，
  OPEN→ASSIGNED→CLOSED、可重复指派、OPEN 可直接关闭）、Port
  `packages/application/ports/ops_store.py`、适配器 `adapters/sqlite/ops_store.py`
  （`ops_alert_rules` / `ops_incidents` 两表 + 项目索引）、写面 7 端点
  （`GET/POST /projects/{id}/ops/alert-rules`、`PATCH/DELETE /ops/alert-rules/{rule_id}`、
  `POST /projects/{id}/ops/incidents`、`/ops/incidents/{id}/assign`、`/close`）。
  **写面被读面消费**是本轮的核心口径：命中规则的告警在读面带 `muted=true` + `muted_by`
  但**不从列表消失**（静音不是隐藏）+ `muted_count`；登记事故后来源 run 的告警带
  `incident_id`，`GET .../ops/incidents` 拆成 `incidents`（已登记）与 `candidates`
  （派生自 FAILED run，不会自动变事故，已登记者移出候选）；关闭后标记消失、再处置
  **409**（域状态机拒绝而非静默 no-op）；store 缺失时读面 `*_available=false` + 原因、
  写面 503。前端新增 `OpsAlertRulesPanel`（新建/启停/删除）与事故处置列
  （指派/关闭/候选一键登记），`pageSupport` 的 `GAPS.alerts` / `GAPS.incidents` 收敛、
  两条 `disabledOperations` 清空、`level` 升为 `full`。验证：控制面 10 passed、
  全量 API **336 passed**、契约 3 passed（含写方法集合断言）、stub e2e **50 passed**、
  live e2e **28 passed**（新增 3 条真实 HTTP 写链）、根 eslint 0 error、web 单测 76 passed、
  `ops-alerts` / `ops-incidents` 基线 win32+linux 重生成并目检；本地 m0 **连续红了 4 次**
  （`python/format-check` 手工改过的测试文件未跑 `ruff format` → `python/tests` 的 50 行/函数上限
  → `typescript/boundaries` 的面板↔列定义循环依赖 → 命名门禁的"模块名须与唯一组件导出同名"），
  逐条修复后 **23/23**；四次失败全部如实记录，未跳过任何一道门。
  本轮另有一项重要的**门禁事实**被量化：ops 两页整块新增面板后，旧设计基线按 Playwright
  判据（pixelmatch / YIQ 阈值 0.2）只差 **1.02% / 0.93%**，低于 `maxDiffPixelRatio: 0.02`
  ⇒ 门禁**不会报警**（与 cycle 3 记录的 1.73% 同类）；据此改为主动删除基线强制重生成并目检，
  量化脚本留在 `scratch/cycle5-baseline-drift/`（并纠正了"任一通道像素差 ≠ 0 ⇒ ~40%"这一
  误导性指标）。RECHECK-059 = PASS_WITH_WARNINGS（W-1 门禁容差盲区；W-2 静音不抑制来源；
  W-3 `assignee` 无成员校验；W-4 `IncidentsViewDto.incidents` 元素形状变更需消费者升级；
  W-5 四道门禁的教训）。本轮提交 `8148df4` 的 CI run **35002027768 六个 job 全 success**（无重跑）。安全面：Mimosa 密封扫描
  （`scan-2026-09-15T16-54-15.771Z-ee27361c7e9a`，seal `sha256:070346dd…`，36 findings / 3 high，
  `verdictEffect: none`）对账后**本轮改动文件命中 0 条**；3 条 high 仍是既有两条路径穿越
  （`artifacts/钻孔官方API_v12/`）与 `protocol_authoring/service.py` 的已知误报
  （`yaml.load(_StrictLoader)`，与 `yaml.safe_load` 同安全级）。**不主张项目整体安全**。
- 2026-09-16 cycle 6（EC-05 = G15 tool-provider 注册治理写面，**PASS**）：把 `ops/integrations`
  的"install/approve/revoke 属供应链治理面，不提供"做成真实写面——域
  `packages/domain/tool_registry.py`（`ProviderRegistration`：PENDING → ACTIVE → REVOKED，
  REVOKED 终态）、Port `ToolProviderRegistry`、适配器
  `adapters/sqlite/tool_provider_registry.py`（`tool_provider_registrations` 单表）、
  6 端点（`GET/POST /tool-provider-registrations`、`PATCH /{id}`、`/{id}/approve`、
  `/{id}/revoke`、`/{id}/health-check`）。
  **三条硬门**是本轮的口径：① 信任级别由注册状态推导（PENDING→UNTRUSTED、ACTIVE→USER_APPROVED、
  REVOKED→REVOKED），请求 DTO 里没有该字段，注册方无法自我声明 BUILT_IN/VERIFIED；
  ② pin 必须是内容寻址 digest（`sha256:<64hex>`），可漂移的 tag/分支名 422
  （AGENTS.md §9「默认 deny：unpinned plugin」），且该 pin 作为 `tool_pack_digests[provider_id]`
  合入目录 ⇒ `preflight._is_pinned_digest` 通过 = "用户 pin 的那份就是 preflight 看到的那份"；
  ③ 内置目录已占用的 id 拒绝注册（不影子覆盖平台自己的 provider），重复登记 409 且不改写既有行。
  **消费证明**用"同一份输入在不同状态下结论不同"给出：`dataset.read` 是 examples 三个 provider
  都不声明的能力，对同一份草稿协议跑 `POST /projects/{id}/preflight`——未注册/PENDING →
  `TOOL_UNAVAILABLE`；ACTIVE → 该 finding 消失、`SUPPLY_CHAIN_UNPINNED` 不出现、
  `TOOL_HEALTH_UNPROVEN` 出现（警示不阻断）；REVOKED → `TOOL_UNAVAILABLE` 回归。
  健康复核与读面共用 `preflight_support.probe_provider_spec()`（一条探测路径，不做两套真相）：
  注入 Fake ToolProvider 后 health-check 写入 HEALTHY/OPEN_CIRCUIT 与 `GET /tool-providers`
  完全一致，无实例时 UNKNOWN + 原因。前端新增 `RegistryPanel`（登记/批准/吊销/健康复核、
  "是否已进入目录"列、终态行不再有处置动作），`pageSupport` 的
  `disabledOperations: ["install","approve","revoke"]` 删除、`GAPS.integrations` 改写为收敛后口径；
  `GET /tool-providers` 的 `management_available` 由恒 false 变为"注册表是否装配"（连带
  `live-api-workflow.spec.ts` 与 API 用例的旧断言同步改写，不是删断言）。验证：控制面
  **18 passed**、全量 API **354 passed**、契约 **358 passed / 56 skipped**（OpenAPI +648 行）、
  stub e2e **55 passed**、live e2e **30 passed**（含 2 条真实 HTTP 注册链）、根 eslint 0 error、
  web 单测 76 passed、`ops-integrations` 基线 win32+linux 重生成并目检；本地 m0 **红了 3 次**
  （`python/product-lint` 行宽 104 → `python/format-check` 未格式化 → `python/typecheck` 与
  `typescript/typecheck` 的 Any/可空返回），逐条修复后 **23/23**，全部如实记录。
  本轮复现了 cycle 5 的门禁容差盲区：新增整块注册面板后旧基线按 Playwright 判据只差
  **0.79%（win32）/ 0.66%（linux）**，低于 `maxDiffPixelRatio: 0.02` ⇒ 门禁不会报警；
  量化脚本 `scratch/cycle6-baseline-drift/measure.py`（从 `git show HEAD:` 取旧基线，
  不往仓库堆 PNG）。顺带清两处跨 feature 重复：`useOpsAction` → `hooks/useAsyncAction`、
  `OpsFields` → `components/InlineFields`（否则会复制第二份），ops-view 三处调用点同步。
  另修正一处文档漂移：`docs/api/CONTROL_PLANE_API.md` 的 Ops 段仍写着"只读/no workflow"，
  本轮补齐 cycle 5 的 7 条写面。RECHECK-060 = PASS_WITH_WARNINGS（W-1 门禁容差盲区复现；
  W-2 capabilities 取值域不是授权边界；W-3 pin 只校验形态；W-4 健康复核无 schema 漂移比对；
  W-5 跨 feature 重构需随计划登记）。
- 2026-09-16 cycle 7（EC-06 = G2 项目删除语义，**PASS**）：`DELETE /projects/{project_id}`
  把 `#/portfolio/projects` 的"不提供删除（归档即终态）"缺口变成真实能力，且**删除的默认
  答案是拒绝**：判定顺序为 `example-project` → 409 `Project Reserved`（合成行不做静默
  no-op：返回 204 会变成"删除成功但列表里还有"的陷阱，404 也不对——它确实存在）、未知 id
  → 404、未装配 store → 503、仍被 runs / 协议草稿 / 实验队列 / 库资源 / ops 规则或事故引用
  → 409 `Project In Use` 且 detail 逐项计数（`runs=2, drafts=1`）、无引用 → 204（注册行与
  随项目创建的设置行一起删，设置行与项目注册同生、不是研究数据）。`_references()` 只枚举
  **能证实**的项目作用域存储，run 的从属事实（approvals/budget/evidence/eval report）由
  `runs=N` 代表、不重复计数；存储层 `delete_project` 只删被要求删的那一行（rowcount 0 →
  `KeyError` → 404），"是否允许删"的决策与原因留在路由层。前端每行一个删除动作（默认项目
  按钮禁用 + title 说明），被引用的 409 detail 原样呈现在行内且行保留，删除活动项目后
  `activeProject` 回退默认项目（副作用在 `useProjectDeletion` 里，不在组件里）；
  `pageSupport` 的 `disabledOperations: ["delete"]` 删除、`GAPS.multiProject` / `GAPS.delete`
  收敛。替身改为**状态可变**（`stub-routes-projects.ts` 接管 `/projects` 四个方法：创建真的
  进列表、归档真的改状态、删除真的移出、引用/默认项目真的 409），否则"删除后列表变了"无法
  在 stub 套件里被验证。验证：删除语义 7 passed、全量 API 361 passed、契约 359 passed /
  56 skipped（OpenAPI +34 行，仅新增 delete 操作 + `test_openapi_contains_project_delete_method`
  把 409/不级联口径锁进契约）、stub e2e 4 passed（全量 59 passed / 15 files）、live e2e
  2 passed（全量 31 passed / 9 files）、根 eslint 0 error、web `tsc --noEmit` 通过、单测
  76 passed；`portfolio-projects` 基线 win32+linux 重生成并目检（漂移 **0.48% / 0.47%**，
  容差盲区第三次复现）。三处本轮暴露的问题如实记录：① `ProjectDeleteAction` 首版 60 行超
  `max-lines-per-function` 50 上限 ⇒ 抽 `useProjectDeletion.ts`（hook 文件名须与导出同名）；
  ② `live-api-workflow.spec.ts` 逼近 450 行硬上限 ⇒ 项目链拆到 `live-project-registry.spec.ts`
  并在 `live-specs.ts` 登记一处；③ **替身守不住 `Idempotency-Key`**——本轮做了反证：
  去掉 `projectsClient.remove` 的该头后 stub 4 用例仍全绿（随后还原并复跑），说明 mutating
  调用的这条约束只有 live 套件（真中间件）能守。本地 m0 **首跑红**：治理校验报
  `工程记忆来源不存在: MEM-20260915-037`——本轮先把记忆条目写进树、计划与复检文件在其后
  落盘；补齐 `PLAN-20260915-061` + `RECHECK-20260915-061` 后复跑 = `profile=m0; 23 deterministic
  checks`（失败如实记入 RECHECK-061，未掩盖）。RECHECK-061 = PASS_WITH_WARNINGS（W-1 门禁
  容差盲区第三次实测；W-2 替身守不住 Idempotency-Key（含反证）；W-3 草稿引用计数有 200 上限；
  W-4 不做跨项目引用检查；W-5 活动项目回退是前端行为；W-6 继承 RECHECK-054 W-1、
  RECHECK-060 W-2/W-3/W-4；W-7 live 套件文件规模需拆）。本轮提交 `bc4a9aa` 的 CI run
  **35018256116 六个 job 全 success**（无重跑）。安全面：Mimosa 密封扫描对账后
  **本轮改动文件命中 0 条**；提交/推送时 Cursor hook 自带的扫描未取得结论
  （`scanner_enobufs`），上述结论来自独立重跑的完整审计。**不主张项目整体安全**。
- 2026-09-16 cycle 8（收口复检，**ACHIEVED**）：立 `PLAN-20260915-062` 做 ACHIEVED 前置
  复检——**不依赖历史结论文本**，只读当前树判定六个 EC。复检脚本
  `scratch/verify_goal002_closeout.py` 现算 **59 条证据面断言**：EC-01 项目级血缘路径 +
  `GAPS.globalLineage` 收敛 + 未连边清单的诚实边界标记仍在；EC-02 成本预测两条路径 +
  「不绘制预测」表述消失 + `MEAN_OF_VALUED_DAYS` 口径仍在；EC-03 三条工作区快照路径 +
  `RESEARCHOS_WORKSPACE_SNAPSHOT_ROOT` 边界仍在；EC-04 五条 ops 写路径与写方法 +
  告警/事故 reason 记录写路径 + 两页 `level: "full"`；EC-05 五条注册面路径与写方法 +
  `ops/integrations` 不再禁写 + `trust_for()` 仍在；EC-06 `/projects/{project_id}` 的
  `patch|delete` + `portfolio/projects` 不再禁删 + 「归档即终态」表述消失 + 契约描述含
  `409`/`级联`；以及 33 条规范路由仍在、`portfolio-projects` 双平台基线存在。
  EC-06 的另一半（每 cycle CI 六 job 全绿）改为**从 GitHub API 逐 job 现读**：
  cycle 1 `34960364156`、cycle 2 `34969935719`、cycle 3 `34978272057`、cycle 4 `34984686466`、
  cycle 5 `35002027768`、cycle 6 `35011288950`、记录提交 `35013114804`、cycle 7 `35018256116`
  —— **8 个 run × 6 job 全 success**，无重跑。治理 validate 绿、本地 m0 **23/23**。
  RECHECK-062 = PASS_WITH_WARNINGS（8 类结转告警原样保留，见「收口结论」表）。
  本 cycle 的收口提交 `e879768` 单独跑 run **35021162088 六个 job 全 success**（无重跑，
  记录提交同样触发六 job——cycle 1 已证明这一点）。
  **判定：GOAL-20260915-002 = ACHIEVED**（六个 EC 全 PASS + 独立复检 + 本文件收口，
  `latest_recheck` 指向 RECHECK-20260915-062）。收口语义：六个诚实缺口已变成**有真实
  消费者**的能力，且每一项仍带范围注记（能力边界，不是待办占位）；长程剩余项已按主题
  列入「终止与收口 · 收口结论」表，交后继 GOAL 承接。
