---
id: GOAL-20260915-002
slug: gap-registry-completion
title: 诚实缺口注册表收口：G9/G12/G8/G7/G15/G2 六项从「诚实禁用」转为「有真实消费者」
status: ACTIVE
created_at: 2026-09-15
updated_at: 2026-09-15
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
    status: PENDING
  - id: EC-05
    criterion: >-
      G15 tool-provider 管理写面：注册/更新/健康复核（当前只读投影 → 有真实写面与消费者）
    verify: >-
      OpenAPI 快照写方法存在；ops/integrations 的 disabledOperations 相应项消失；API + live e2e 绿
    status: PENDING
  - id: EC-06
    criterion: >-
      G2 项目删除/归档 + 治理收口：项目归档/删除语义落地（被引用返回 409，不静默级联）；
      每个 cycle 本地 m0 与 main 的 CI 全绿；收口 RECHECK + 安全扫描处置
    verify: >-
      OpenAPI 快照含 DELETE/PATCH 项目路径 + 409 用例；每 cycle CI run 六 job 结论；
      收口 RECHECK = PASS 或 PASS_WITH_WARNINGS
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
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
child_plans:
  - .cursor/plans/tasks/PLAN-20260915-054-netproxy-partition-heal.md
  - .cursor/plans/tasks/PLAN-20260915-055-project-scope-provenance-lineage.md
  - .cursor/plans/tasks/PLAN-20260915-056-blackhole-must-be-effective-on-return.md
  - .cursor/plans/tasks/PLAN-20260915-057-project-scope-cost-forecast.md
  - .cursor/plans/tasks/PLAN-20260915-058-workspace-snapshot-tree-and-file-diff.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-058-workspace-snapshot-tree-and-file-diff.md
memory_entries:
  - MEM-20260915-031-partition-injector-must-heal
  - MEM-20260915-032-project-lineage-merge-and-honest-unlinked-resources
  - MEM-20260915-033-series-projection-valued-days-only
  - MEM-20260915-034-digest-addressed-snapshot-read-surface
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
| EC-04 | G7 ops 写面（告警规则 CRUD + incident 处置） | OpenAPI 写方法 + pageSupport 收敛 | PENDING |
| EC-05 | G15 tool-provider 管理写面 | OpenAPI 写方法 + pageSupport 收敛 | PENDING |
| EC-06 | G2 项目归档/删除 + 每 cycle 门禁/CI 全绿 + 收口复检 | DELETE/PATCH + 409 用例 + CI run + RECHECK | PENDING |

**不变量（沿用 GOAL-001 与 AGENTS.md）**：不伪装实现（不注册没人消费的 scheduler/规则、
不让 fixture 冒充业务数据）；默认 deny 的安全姿态不变；观测隐私（不记录完整 Prompt）
不变；每一项写面必须走既有 policy/preflight 门链。**规模标注**：G8 为 L（控制面当前
没有 workspace 快照枚举面）、G7/G9/G12/G15 为 M、G2 为 S。

## 循环入口协议

按 README 的 7 步判定执行；当前续点：**cycle 4 已闭环（PLAN-20260915-058：
G8 工作区快照文件树与文件级 Diff 交付——按内容寻址 digest 只读，
`GET /workspace-snapshots/{digest}/files` 与 `/{left}/diff/{right}`，
EC-03 = PASS；RECHECK-058 = PASS_WITH_WARNINGS）**。
下一个动作 = ① derive：取 EC-04（G7 ops 写面：告警规则 CRUD + incident
declare/assign/close），子 PLAN 编号续全局序列（下一号 = **PLAN-20260915-059**）。
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

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20260915-054（CI 债：分区注入器真实性） | e6f09cb | 新语义用例 3 passed + 反证 `legacy: SWALLOWED / fixed: ECHOED`；Linux 容器 D 场景 5/5、`tests/distributed` 全量 25 passed / 4 skipped / 0 failed；本地 m0 23/23；RECHECK-054 = PASS_WITH_WARNINGS | run 34960364156（e6f09cb）：**六个 job 全 success**（quality-ubuntu-latest / quality-windows-latest / console-frontend / container-quality / eval-gate / collector-quality）——对照修复前 run 34957121713 的 collector-quality 失败 | 旧 `_stall` 消费并丢弃分区期间的字节且连接线程直接结束 ⇒ `restore()` 无法恢复在途请求，worker 阻塞到 30s 客户端超时、SIGTERM 打不断阻塞读 ⇒ D 场景 teardown `wait(10)` 超时（cycle 13 收口提交的 CI 红）；另修宿主 venv 被容器 `uv sync` 覆盖的事故（已重建并验证） | EC-01~06 全部 PENDING（本轮为 EC-06 的门禁债前置，已清零） | cycle 2 = ① derive EC-01（G9 全局跨 run 血缘），子 PLAN 编号 = PLAN-20260915-055 |
| 2 | PLAN-20260915-055（EC-01：G9 项目级来源血缘）+ PLAN-20260915-056（门禁轮：`blackhole()` 返回即生效） | 见本 cycle 提交 | API 6 passed；stub e2e **40 passed**、live e2e **20 passed**；根 eslint 0 error；web lint/typecheck 通过 + 单测 76 passed；设计基线（win32 本地 + linux pinned 容器）重生成（实测陈旧基线仅差 1.73% ⇒ 旧基线不会报警）；本地 m0 **23/23**（3411 passed / 6 skipped）；RECHECK-055/056 = PASS_WITH_WARNINGS | run **34969935719**（ecf0ebf）：**六个 job 全 success**（quality-ubuntu-latest / quality-windows-latest / console-frontend / container-quality / eval-gate / collector-quality） | ① 全页目检发现 `.cards` auto-fit 网格把 4 列节点表裁列 ⇒ 新增 `.stack` 整宽堆叠（先修复再重生成基线）；② 陈旧设计基线与新渲染只差 **15,933 px = 1.73%**，低于 2% 阈值 ⇒ 基线不会报警，必须主动重生成；③ m0 全量在 Windows 上暴露 `blackhole()` 竞态（泵已阻塞在 `recv` ⇒ 标志置了但仍转发）⇒ `blackhole()` 改为等分区生效（有界 2s），PLAN-056 单独记账 | EC-02~06 PENDING | cycle 3 = ① derive EC-02（G12 跨 run 时序成本预测），子 PLAN 编号 = PLAN-20260915-057 |
| 3 | PLAN-20260915-057（EC-02：G12 项目级成本预测） | 见本 cycle 提交 | 纯函数 7 passed + API 7 passed（项目隔离/unattributed/幽灵项目/422/503）；契约 **355 passed / 56 skipped**；stub e2e **41 passed**、live e2e **21 passed**；根 eslint 0 error + web lint/typecheck 通过 + 单测 76 passed；设计基线 `insights-cost-analytics` / `govern-budget` × win32/linux 重生成并目检；本地 m0 **首跑红**（命名门禁：`liveSpecs.ts` 违反测试文件 kebab-case + Playwright 生成目录 `test-results/<中文用例标题>/` 被判非法路径）→ 修复后 **23/23**；RECHECK-057 = PASS_WITH_WARNINGS | run **34978272057**（d350e8e）：**六个 job 全 success**（quality-ubuntu-latest / quality-windows-latest / console-frontend / container-quality / eval-gate / collector-quality） | ① 命名门禁同时抓出**新文件命名**与**生成产物误判**两类问题 ⇒ 前者改名 `live-specs.ts`，后者把 gitignored 的 `test-results` 加入 `IGNORED_DIRECTORIES` 并补回归用例；② `live-*.spec.ts` 清单原在两份 playwright 配置里各写一遍，漏同步会让 stub 套件去连真实后端 ⇒ 抽 `tests/e2e/live-specs.ts` 单一来源（`--list` 复核 41/11 与 21/5 未漂移）；③ 三处新工程债登记为 RECHECK-057 W-1/W-2/W-3（日均方法与窗口语义） | EC-03~06 PENDING；EC-02 已 PASS（范围注记见 EC 表） | cycle 4 = ① derive EC-03（G8 workspace 文件树 + 文件级快照 Diff，或产出 Accepted ADR 收敛标注），子 PLAN 编号 = PLAN-20260915-058 |
| 4 | PLAN-20260915-058（EC-03：G8 工作区快照文件树 + 文件级 Diff） | 见本 cycle 提交 | 纯函数 8 passed / 读取器 12 passed / API 11 passed；契约 **383 passed / 56 skipped**；stub e2e **45 passed**、live e2e **25 passed**；根 eslint 0 error + web lint/typecheck 通过 + 单测 76 passed；`run-workspace` 设计基线 win32/linux 重生成并目检、design-fidelity 33 路由绿；本地 m0 **首跑红**（ruff：新增测试两行 101/102 字符）→ 修复后 **23/23**；RECHECK-058 = PASS_WITH_WARNINGS | 待 CI（见状态历史） | ① 全量 stub 套件被严格替身守卫拦下（新面板必然调用 run 快照面）⇒ 默认路由进共享替身表 `stub-routes-workspace.ts`，不逐用例打补丁；② 控制面首次读宿主目录 ⇒ 收窄为只接受 `sha256:<64hex>` digest、只在 `<root>/.snapshots` 内解析、symlink 一律拒绝、未配置即 503；③ `ArtifactDiffDto.note` 与 `REPRODUCTION_NOTE` 里「控制面无快照 diff 面」的旧表述同步收敛（否则新能力被旧文案否认） | EC-04~06 PENDING；EC-03 已 PASS（范围注记见 EC 表） | cycle 5 = ① derive EC-04（G7 ops 写面：告警规则 CRUD + incident 处置），子 PLAN 编号 = PLAN-20260915-059 |

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
  真的产出过快照；W-4 `stub-routes.ts` 已 403 行、接近硬上限）。
