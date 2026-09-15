---
id: GOAL-20260912-001
slug: backend-frontend-full-integration
title: 后端补全与前端完整对接（预留接口/fixture 全消，33 路由 live-capable）
status: BLOCKED
created_at: 2026-09-12
updated_at: 2026-09-12
owners:
  - root-agent
authorization:
  source: user-request
  ref: "2026-09-12 用户要求设计并启用 goal 循环文件以自动迭代完成后端补全与完整对接；GOAL 格式与 push-to-main-for-CI 授权随该计划批准（循环不得推非 main、不得 force）。"
objective: >
  前端所有 live 页面均消费真实后端能力（无预留接口/fixture 冒充业务数据），
  9 个 GAP 域与项目/深水区语义按已批准 PLAN-041/042 落地，main 的本地门与
  GitHub Actions m0-quality 全绿。
exit_criteria:
  - id: EC-01
    criterion: 项目注册表落地：ProjectDefinition 域 + store + GET/POST/PATCH /projects；
      前端 ProjectContext 替换 6 处 example-project 硬编码；#/portfolio/projects 翻 live
    verify: rg -n "example-project" apps/web/src/api/*.ts 仅剩测试/默认值；live e2e 项目链用例绿
    status: PASS
  - id: EC-02
    criterion: reports/integrations/全局血缘 经既有应用层（deliverable builder、
      tool_plane、跨 run 投影）HTTP 面 + 对应页面翻 live
    verify: tests/api 新端点套件绿；stub e2e 无 Unstubbed；design-fidelity 基线按批准更新
    status: PASS
  - id: EC-03
    criterion: prompts/datasets/notebooks/alerts/incidents/schedules/data-health 各建
      最小域（domain 实体 + SQLite/PG store + API + client + 页面 live）
    verify: 每域 API 测试 + live e2e 断言；presentationPolicy 不再把该路由强制 example
    status: PASS
  - id: EC-04
    criterion: 深水区语义收口：budget_adjust 走 BudgetLedger、成本预测投影、
      pause/resume 真执行（lease+worker 协调）、实验队列、artifact 文件 diff、
      memory capability policy（G16）；未落地项必须在 GAPS 保持诚实标注（不得默认绿）。
      （收口判定）6 项中 5 项已交付（046/047/048/049）；实验队列 G14 未交付且保持禁用
      标注 ⇒ 本 EC 记 BLOCKED（预算用尽，需人工决定是否续做）
    verify: tests/api 对应用例 + CONSOLE_PAGE_MAP G 表逐行与代码一致
    status: BLOCKED
  - id: EC-05
    criterion: example fixture 仅作设计参照：33 路由 live-capable（身份/billing/members
      类除外，保持 M18/M19 诚实锁定）；example-isolation 与 live e2e 全链绿
    verify: pnpm run test:e2e + test:e2e:live；pageSupport 无 gap 级业务页残留（EC-04 授权延期项除外）
    status: PASS
  - id: EC-06
    criterion: 每 cycle main 推送后 GitHub Actions m0-quality 全 job 成功；
      最终收口 RECHECK=PASS/PASS_WITH_WARNINGS 且密封安全扫描有处置记录
      （收口判定）后半满足（RECHECK-050 PASS_WITH_WARNINGS；sealed scan
      sha256:bfeaf946…c5f2db31 逐条处置入 docs/audits/PA1_MIMOSA_REVIEW.md）；
      前半未达成：collector-quality 在 run 61-68 每次失败且失败测试恒为同 2 项
      （持续失败，非 flake；根因见 RECHECK-050 F-1）⇒ 本 EC 记 BLOCKED
    verify: gh run list --branch main --workflow m0-quality.yml 最新 run conclusion=success；
      docs/audits/PA1_MIMOSA_REVIEW.md 含收口时间戳节
    status: BLOCKED
budget:
  max_cycles: 10  # 用户于 cycle 6 后给出更新授权「持续循环迭代，迭代10次」；原值 8（见状态历史）
  per_cycle_minutes: 240
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 5
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
  - .cursor/plans/tasks/PLAN-20260912-041-project-registry-and-switcher.md
  - .cursor/plans/tasks/PLAN-20260912-042-ci-debt-remediation.md
  - .cursor/plans/tasks/PLAN-20260913-043-reports-integrations-lineage-live.md
  - .cursor/plans/tasks/PLAN-20260914-044-library-catalog-domains-live.md
  - .cursor/plans/tasks/PLAN-20260914-045-ops-observability-projections-live.md
  - .cursor/plans/tasks/PLAN-20260914-046-budget-adjust-ledger-and-forecast.md
  - .cursor/plans/tasks/PLAN-20260914-047-artifact-content-diff.md
  - .cursor/plans/tasks/PLAN-20260914-048-pause-resume-dispatch-coordination.md
  - .cursor/plans/tasks/PLAN-20260914-049-memory-capability-policy.md
  - .cursor/plans/tasks/PLAN-20260914-050-ec05-ec06-closeout.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-050-ec05-ec06-closeout.md
memory_entries:
  - MEM-20260914-023-budget-ledger-sharing-and-reservation-attribution
  - MEM-20260914-024-live-console-artifact-fixtures-and-api-prefix
  - MEM-20260915-025-pause-dispatch-coordination
  - MEM-20260915-026-policy-capability-mirror-scopes
---

# GOAL-20260912-001 — 后端补全与前端完整对接（自迭代循环）

## 目标与退出标准

格式规范与循环 SOP 见 [README.md](README.md)（本文件为首个实例）。

| EC | 标准（摘要） | 验证 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 项目注册表 + 前端去硬编码 + projects 页 live | rg + live e2e | PASS |
| EC-02 | reports/integrations/全局血缘 复用既有域 + live | API/e2e/基线 | PASS |
| EC-03 | 9 GAP 域中 prompts/datasets/notebooks/alerts/incidents/schedules/data-health 最小域 + live | API/e2e/policy | PASS |
| EC-04 | 深水区语义（budget_adjust/预测/真 pause-resume/队列/Diff/memory policy），未落地保持诚实标注 | API + G 表一致性 | **BLOCKED**（6 项中 5 项交付：budget_adjust + 成本预测 + 制品内容 Diff + pause/resume + memory capability policy；实验队列 G14 未交付，pageSupport / CONSOLE_PAGE_MAP 保持诚实禁用） |
| EC-05 | 33 路由 live-capable（M18/M19 诚实锁定除外）；example 仅设计参照 | stub+live e2e + pageSupport | **PASS**（33 路由 = 10 full / 22 partial / 1 gap；gap 仅 ops/matrix 非业务页；守卫测试锁死：显式登记 + 非 full 必有 reason + gap 仅非业务页） |
| EC-06 | 每 cycle GHA 全绿；收口 RECHECK + 安全扫描处置 | gh run + audits | **BLOCKED**（收口 RECHECK-050 + 密封扫描处置已交付；GHA 全绿未达成——collector-quality 在 run #61–#68 持续失败同 2 项） |

前置输入（cycle 前已完成，不占 cycle 预算）：PLAN-20260912-040（后端组成浮现、
接缝闭合、DELETE/custom/clone/approvals-history/参考协议）已 DONE，
RECHECK-20260912-040 = PASS_WITH_WARNINGS；密封扫描 scan-2026-09-12 已处置
（PLAN-040 文件零命中）。

## 循环入口协议

按 README 的 7 步判定执行；当前续点：**cycle 10 已闭环（PLAN-050：EC-05 路由能力声明守卫 + EC-06 密封扫描处置 + 最终复检）；预算（10 cycle）用尽，status=BLOCKED；driver=session-goal，owner=root-agent。**

人工决策点（恢复本 GOAL 前必须逐条处理，详见「终止与收口」）：
1. `collector-quality` 持续失败（worker 关闭语义 / OTel 证据链）——修产品行为，还是改判该 job 的验收口径；
2. 实验队列 G14（queue/schedule）是否续做；
3. 是否提高 `max_cycles` 并恢复 ACTIVE。

## 驱动

本 GOAL 驱动无关（README「驱动适配」）：默认**会话驱动**（用户指令进入下一 cycle）；
需要无人值守时挂**定时自动化**（指令模板见 README，仅当 status=ACTIVE 时推进）；
若运行环境提供客户端 goal/auto 持续模式，其每轮触发等价为一次入口协议进入，
限额与停止条件以本文件 frontmatter 为准。进入 cycle 时在迭代日志声明 driver 与
owner；同一时刻仅一个驱动推进。

## 单 cycle SOP

按 README ①~⑦ 执行。本实例附加约定：

- ① derive 的主题顺序默认取 EC 表首个 PENDING（EC-01→EC-02→EC-03→EC-04→EC-05），
  除非迭代日志「下一轮输入」给出更强约束（如上一 cycle 的部分交付）。
- 子 PLAN 必须独立可验收、独立 RECHECK；GOAL 只在 EC 层面记账。
- ⑤ push 前：`git pull --ff-only origin main`（并发历史则先 rebase 解决，不 force）。
- EC-04 允许部分延期：任一子项若触发 escalation，记 BLOCKED 并继续其余 EC；
  全部可选项收口后再统一判定 EC-04。

## CI 失败分类与纠错

按 README 分类表执行；本仓已知 flake/env 签名（重跑不修）：observability OTLP
teardown race、m12 容器 e2e/pg_crash_restart 混合顺序失败（DSN 固化配方）、
m0 全量单跑截断（分组复跑）。工作流文件 `.github/workflows/m0-quality.yml`
属治理面：循环内不修改；需要改动即 BLOCKED 提请人工。

## 终止与收口

**2026-09-15 收口判定（cycle 10，预算用尽）**：

| EC | 判定 | 证据 |
| --- | --- | --- |
| EC-01 | PASS | RECHECK-041（项目注册表 + 前端去硬编码 + projects 页 live） |
| EC-02 | PASS | RECHECK-043（deliverable / tool-providers / lineage 三端点 + 三页 live） |
| EC-03 | PASS | RECHECK-044 + RECHECK-045（7 域最小域 + ops 只读投影，全部 live） |
| EC-04 | **BLOCKED** | 5/6 交付（046 预算调整+预测、047 制品内容 Diff、048 pause/resume、049 memory capability policy）；实验队列 G14 未交付，pageSupport `disabledOperations: ["queue","schedule"]` 与 CONSOLE_PAGE_MAP 保持诚实标注 |
| EC-05 | PASS | 33 路由 = 10 full / 22 partial / 1 gap（gap 仅 ops/matrix 非业务页）；守卫测试 `apps/web/tests/unit/page-support-coverage.test.ts` 3 例；stub e2e 36/36（含 example-isolation）、live e2e 17/17 |
| EC-06 | **BLOCKED** | 收口面满足：RECHECK-050 = PASS_WITH_WARNINGS、sealed scan sha256:bfeaf946…c5f2db31 逐条处置；**未达成面**：collector-quality 在 run #61–#68 每次失败且失败测试恒为同 2 项（持续失败，非 flake） |

**所需人工决策**（三者任一处理后本 GOAL 方可恢复 ACTIVE 或转 ACHIEVED）：

1. `collector-quality`：修 worker 关闭语义（SIGTERM drain 不打断在途执行 ⇒ teardown 超时）
   与 OTel 证据链（collector file exporter 未落盘 marker span），**或**明确该 job 的验收
   口径（workflow 属治理面，循环内不改）。
2. 实验队列 G14：是否续做（需新 cycle 预算）。
3. 预算：`max_cycles` 是否提高。

**可恢复点**：本文件迭代日志最后一行（cycle 10）+ 工作树/远端 = main 上的收口提交；
`latest_recheck` 指向 RECHECK-20260915-050。


- ACHIEVED：EC-01~06 全 PASS（含证据）→ 跑一次整体独立复检（RECHECK-*，
  result=PASS*）→ 沉淀 MEM-* → 本文件 status=ACHIEVED。
- BLOCKED：命中 escalation/fix_policy 上限/no-progress 停止 → 记录阻塞事实、
  所需人工决策、可恢复点；等待人工后转 ACTIVE 或 PAUSED。
- ABORTED：用户撤回目标/授权 → 冻结迭代日志并归档说明。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| (0) | PLAN-20260912-040（cycle 前完成） | 6d844e3, 2022b02, d5abf18, af5df14, b86c693, 54a6360 | m0 分组全绿；stub 30/30；live 10/10 | 未 push（cycle 1 ⑤ 一并推） | — | EC-01~06 | cycle 1 = PLAN-041（EC-01） |
| 1 | PLAN-20260912-041 | b55df92, 9ba606e, 57feb37 + 收口批 | 全量 pytest exit 0/0 failed；ts 9/9；fw 8/8；stub 30/30；live 11/11；RECHECK-041 PASS_WITH_WARNINGS | run #50/收口 run（见状态历史） | F-2 AC 文案、F-3 docstring、F-1 收口时序 | EC-02~06 | cycle 2 = PLAN-042（EC-02：reports/integrations/lineage 经既有域 HTTP 面） |
| 2 | PLAN-20260912-042 | 4de2282 | 全量 pytest 2997 passed/205 skipped/0 failed；m0 23/23 PASS；typescript 9/9；framework 8/8；mypy 767 files（默认+linux）Success；docs_consistency 6 PASS | run #53: quality-ubuntu/console-frontend/quality-windows/container-quality/eval-gate 全 SUCCESS；collector-quality FAIL（2 项既有 timing flake，52→53 由 5→2） | project_store 时序、symlink 惰性目录、pinned 镜像引用、docs 检查器大小写 | EC-02~06 | cycle 3 = EC-02（reports/integrations/lineage 经既有域 HTTP 面 + 页面翻 live） |
| 3 | PLAN-20260913-043 | 94570f6 | 全量 pytest 3067 passed/151 skipped/0 failed；api 新套件 10 passed；stub e2e 30/30；live e2e 12/12；m0 23/23 PASS；web lint/typecheck/test/build+boundaries 全绿；基线 win32+linux 各 2 张 | run #55: quality-ubuntu/console-frontend/quality-windows/container-quality/eval-gate 全 SUCCESS；collector-quality FAIL（同 2 项既有 flake） | linux 基线 clone 只见已提交内容（改叠加工作树）；inspection.py 超 450 行→拆 router | EC-03~06 | cycle 4 = EC-03（prompts/datasets/notebooks/alerts/incidents/schedules/data-health 最小域 + live） |
| 4 | PLAN-20260914-044 | e0cb3ca | 全量 pytest 3094 passed/151 skipped/0 failed；store 13/api 7 passed；stub e2e 30/30；live e2e 13/13；m0 23/23 PASS；web 73/73；基线 3 路由 × win32/linux | run #57: quality-ubuntu/console-frontend/container-quality/eval-gate SUCCESS；quality-windows FAIL=单个既有 MCP stdio flake；collector-quality FAIL（同 2 项既有 flake） | 基线 `--update-snapshots` 只写差异（改强制重写+还原无关漂移）；两测试随等级提升同步 | EC-03 第二批 + EC-04~06 | cycle 5 = EC-03 第二批（alerts/incidents/schedules/data-health 最小域 + live） |
| 5 | PLAN-20260914-045 | a19f616, caf7fbb | 全量 pytest 3103 passed/151 skipped/0 failed；api 5 passed；stub 30/30；live 14/14；ts 9/9（stub-api 拆分后复跑）；web 73/73；基线 4 路由 × win32/linux | run #58 quality-ubuntu FAIL（新拆 stub helper 文件名 camelCase，Linux naming gate 红而 Windows 本地绿）→ caf7fbb 修正；run #59: quality-ubuntu/console-frontend/container-quality/eval-gate SUCCESS；collector-quality FAIL（同 2 项既有 flake） | stub-api.ts 超 450 行→拆 stub-routes/stub-fixtures（kebab！）；console-shell/unit 断言随等级提升换 gap 锚点 | EC-04~06 | cycle 6 = EC-04（深水区语义：budget_adjust/预测/真 pause-resume/队列/Diff/memory policy） |
| 6 | PLAN-20260914-046 | 837f730 | 全量 pytest 3132 passed/151 skipped/0 failed；api 14 + domain 11 passed；stub e2e 32/32；live e2e 15/15；m0 23/23 PASS；web lint/typecheck/unit/build 全绿；RECHECK-046 PASS_WITH_WARNINGS | run #61（34838516562，文字曾记作 #60，ID 为准）: quality-ubuntu-latest/quality-windows-latest/console-frontend/container-quality/eval-gate 全 SUCCESS；collector-quality FAIL（同 2 项既有 flake，日志实测确认）；收口 run #62（34840236341）同结论 | `_budget_adjust` 55 行 → 拆 `_budget_policy`/`_adjustment_lines`；`test_semantic_intervention_is_501` 断言随 budget_adjust 交付改锚 replace_agent；run_fixtures 预算账本三实例 → 共享同一实例（生产同侧） | EC-04 余项 + EC-05/06 | cycle 7 = EC-04 剩余（真 pause-resume 执行协调 / 实验队列 / artifact 文件 diff / memory capability policy G16） |
| 7 | PLAN-20260914-047 | 7eece2f | 全量 pytest 3297 passed/6 skipped/0 failed（DSN 固化后 postgres 用例实跑）；应用层 10 + API 4（合计 21 passed）；stub e2e 34/34；live e2e 17/17；m0 23/23 PASS；web lint/typecheck/unit(73) 绿；ruff/mypy 绿；RECHECK-047 PASS_WITH_WARNINGS | run #63（34846151640）: quality-ubuntu-latest / quality-windows-latest / console-frontend / container-quality / eval-gate 全 SUCCESS；collector-quality FAIL（同 2 项既有 flake，日志实测确认：`test_collector_persists_research_os_spans`、`test_scenario_d_network_partition_no_old_authority`） | live 正向链无制品可用（m12 参考链在 live 装配下终态 FAILED、artifact 列表 0 条）→ 改为 test-only 装配注入受控制品；ruff format 2 处；stub e2e 用用例内路由覆盖以免搅动 design-fidelity 基线 | EC-04 余 3 项 + EC-05/06 | cycle 8 = EC-04 剩余（真 pause-resume 执行协调 / 实验队列 / memory capability policy G16） |
| 8 | PLAN-20260914-048 | a5d83dc | 全量 pytest 3319 passed/6 skipped/0 failed（DSN 固化；一次未复现失败见 RECHECK-048 W-5）；应用层 5 + 契约 9（Fake/SQLite/PG）+ API 5 = 19 新增；m0 23/23 PASS；web lint/typecheck/unit(73) 绿；stub e2e 34/34；live e2e 17/17；ruff/mypy 绿；RECHECK-048 PASS_WITH_WARNINGS | run #65（34881096941）: quality-ubuntu-latest / quality-windows-latest / console-frontend / container-quality / eval-gate 全 SUCCESS；collector-quality FAIL（同 2 项既有 flake，日志实测确认） | `_claim_next_impl` 53 行 → 抽 `_claim_candidates`（50 行函数上限）；夹具补 `runs_store`（否则派发断言是空的）；SQLite runs DDL 收敛到 `db.RUNS_SCHEMA_SQL` 单一来源 | EC-04 余 2 项 + EC-05/06 | cycle 9 = EC-04 剩余（memory capability policy G16 优先，实验队列次之） |
| 9 | PLAN-20260914-049 | 14e6c4f | 全量 pytest 3333 passed/6 skipped/0 failed（DSN 固化）；应用层 8（`test_policy_wiring.py`）+ API 4 + stub e2e 2 = 14 新增；m0 23/23 PASS；ruff check/format + mypy（294 files）绿；eslint 0 error；stub e2e 36/36；RECHECK-049 PASS_WITH_WARNINGS | run #67（34928371669）: quality-ubuntu-latest / quality-windows-latest / console-frontend / container-quality / eval-gate 全 SUCCESS；collector-quality FAIL（同 2 项既有 flake，日志实测确认：2 failed / 85 passed） | m0 首跑 `test_scenario_f_scheduler_restart_keeps_state`（负载 timing，隔离复跑 10 passed）；mypy 两个测试助手缺返回注解；run_fixtures 超 300 行软阈值 → 抽 `assembly.policy_bindings()` 三处共用；stub-routes.ts 逼近 450 行 → 路由拆到 `stub-routes-policy.ts` | EC-04 余 1 项（实验队列 G14）+ EC-05/06 | cycle 10 = EC-06 收口（最终 RECHECK + 安全扫描处置 + 残留缺口诚实登记） |
| 10 | PLAN-20260914-050 | (见收口提交) | 路由能力声明守卫 3 例（web unit 76/76；tsc/eslint 绿）；反序列化防线 4 例（authoring 套件 13 passed）；m0 23/23 PASS（复跑口径见 RECHECK-050 W-2）；全量 pytest 3336 passed/6 skipped（首跑 1 例负载敏感失败，隔离复跑 10 passed）；sealed scan 36 findings 逐条处置；RECHECK-050 PASS_WITH_WARNINGS | run #68（34929500205，cycle 9 收口提交）: 5 job SUCCESS + collector-quality FAIL（同 2 项）；cycle 10 自身 run #69（34933817161，1f7f4db）: console-frontend/quality-ubuntu/container-quality/eval-gate SUCCESS，collector-quality FAIL（同 2 项），quality-windows-latest FAIL（telemetry RSS 135.0 vs 阈值 128.0 MiB，series 首次，flake 类，见 RECHECK-050 W-2）；跨 run 取证 #61–#68 该 job 每次失败、失败测试恒为同 2 项 ⇒ 纠正口径：持续失败，非 flake | ruff format 1 处（新增测试字符串引号）；test_scenario_g_drain_stops_claims 首跑 check-then-act 竞态（隔离复跑通过，未改断言）；test_scenario_f_scheduler_restart_keeps_state（cycle 9 首跑）同属负载敏感类 | EC-04 实验队列 + EC-06 GHA 全绿（人工决策点） | 无（预算用尽，status=BLOCKED；恢复条件见「终止与收口」） |

## 状态历史

- 2026-09-13 cycle 1 收口：EC-01 → PASS（本地全绿 + RECHECK-20260912-041 PASS_WITH_WARNINGS）；收口 commit（openapi/docs/PLAN/GOAL/MEM）与代码同 push，CI 终态以收口 run 为准。
- 2026-09-13 cycle 2 = PLAN-20260912-042（CI 既有债修复）：WP-A 类型/链接、WP-B docs 检查器大小写 bug、WP-C 环境守卫 + 3 处测试缺陷、WP-D 本地全门全绿并 push。本地证据：m0 23/23 PASS；全量 pytest 2997 passed/205 skipped/0 failed；mypy（默认 + linux）767 files Success。commit `4de2282`。CI run #53 终态：quality-ubuntu-latest ✅、console-frontend ✅、quality-windows-latest ✅、container-quality ✅、eval-gate ✅；collector-quality ❌（仅剩 2 项**既有** timing flake：`test_collector_persists_research_os_spans` 文件导出轮询超时、`test_scenario_d_network_partition_no_old_authority` 子进程退出超时——run #52 同两项 + 3 项 GPU 失败共 5，cycle 2 守卫降至 2）。AC-04（quality-ubuntu + console-frontend 全绿）满足。
- 2026-09-13 cycle 3 = PLAN-20260913-043（EC-02：reports/integrations/全局血缘）：新增三个只读端点（`GET /runs/{id}/deliverable` 读 M12 persisted 交付物、`GET /tool-providers` catalog 投影 + 三态健康、`GET /runs/{id}/lineage` typed nodes/edges），三页翻 live，文档与 pageSupport 同步。本地证据：全量 pytest 3067 passed/0 failed；api 新套件 10 passed；RECHECK-043 PASS_WITH_WARNINGS；MEM-20260913-022（linux 基线需叠加工作树）。commit `94570f6`。CI run #55 终态：quality-ubuntu-latest ✅、console-frontend ✅、quality-windows-latest ✅、container-quality ✅、eval-gate ✅；collector-quality ❌（仍是 RECHECK-042 W-1 登记的**同两项**既有 flake：`test_collector_persists_research_os_spans`、`test_scenario_d_network_partition_no_old_authority`，非本 cycle 引入）。EC-02 满足。
- 2026-09-14 cycle 4 = PLAN-20260914-044（EC-03 第一批：prompts/datasets/notebooks 库目录）：新增 LibraryResource 域 + LibraryStore Port + SQLite store（配置面同侧，不新增 PG 表）+ 4 端点，三页翻 live。本地证据：全量 pytest 3094 passed/0 failed；store 13/api 7；stub 30/30；live 13/13；m0 23/23；web 73/73；基线 3 路由 × win32/linux。commit `e0cb3ca`。CI run #57 终态：quality-ubuntu-latest ✅（EC 验收所需）、console-frontend ✅、container-quality ✅、eval-gate ✅；collector-quality ❌（同两项既有 flake）；quality-windows-latest ❌ 为**单个既有 timing flake** `test_tool_provider_contract.py::TestStdioTransport::test_slow_tool_enforces_spec_timeout`（stdio 子进程连接在 2s 超时前 BrokenResourceError → TransientPortError 而非 PortTimeoutError；本地单跑 5.3s 通过；与 library 域无关）。按 fix_policy 不放宽断言、不 skip，记为 flake 待复跑。EC-03 第一批满足。
- 2026-09-14 cycle 5 = PLAN-20260914-045（EC-03 第二批：ops 四页只读投影）：**不做持久域**（避免"注册了却不被消费的假 scheduler/规则"），改只读派生——`ops_view` 视图域 + 4 端点（alerts 失败 Run∪非健康端点∪离线 worker、incidents 失败 Run 候选、schedules 进程内 4 scheduler 配置事实、data-health 端点/dataset/artifact 计数与抽样 verify），能力缺口随响应回传锁定标记。本地证据：全量 pytest 3103 passed/0 failed；api 5；stub 30/30；live 14/14；ts 9/9；web 73/73；基线 4 路由 × win32/linux。commit `a19f616` + `caf7fbb`（run #58 暴露新拆 helper 文件名 camelCase 在 Linux naming gate 红——Windows 大小写不敏感本地全绿；kebab 修正）。CI run #59 终态：quality-ubuntu-latest ✅、console-frontend ✅、container-quality ✅、eval-gate ✅；collector-quality ❌（同 2 项既有 flake）。EC-03 全部满足（7/7 域）。
- 2026-09-14 cycle 6 = PLAN-20260914-046（EC-04 第一批：budget_adjust 走账本 + 预留-消耗预测）：**调整 = reservation 生命周期**（release 既有引用 + reserve 新额度；append-only 无原地改数），**预测只覆盖已预留额度**（不外推未预留开销）。新增 `domain/cost_forecast` 纯投影（三态计量 KNOWN/UNKNOWN/NO_DATA + 金额完备状态 + 不跨币种求和 + 剩余可为负）与 `LedgerSnapshot.reservations_by_ref`（run 预留归属的权威来源——正式 preflight 预留作用域是 `phase:<id>`，只有冻结 manifest 的 ref 能证明归属；ref 不可解析时退化作用域匹配并如实标注 attribution，preflight 预留计入 unattributed_reserved 而非伪装为零）。replace_agent 语义变更保持诚实 501。本地证据：全量 pytest 3132 passed/0 failed；api 14 + domain 11；stub 32/32；live 15/15；m0 23/23 PASS；web lint/typecheck/unit/build 全绿。commit `837f730`。附带修复：run_fixtures 预算账本三实例 → 共享同一实例（生产 composition 同一实例，夹具分离使预算读链恒空）。CI run #60（34838516562）终态：quality-ubuntu-latest ✅、quality-windows-latest ✅、console-frontend ✅、container-quality ✅、eval-gate ✅；collector-quality ❌（**日志实测确认**仍是 RECHECK-042 起登记的同 2 项既有 flake）。RECHECK-20260914-046 = PASS_WITH_WARNINGS（新增 W-2 调整不发 outbox 事件、W-3 归属依赖进程内 ref，均已在响应/文档标注）。EC-04 → PARTIAL（本批 2 项交付，余 4 项 PENDING）。
- 2026-09-15 cycle 7 = PLAN-20260914-047（EC-04 第二批：制品内容 Diff）：把 workspace 页"文件 Diff 未接入"的占位换成**真实制品内容 diff**——`GET /artifacts/{left}/diff/{right}`（两侧都是 persisted content-addressed 制品；行级 unified hunks + 统计；`comparison=ARTIFACT_CONTENT` 明示口径）。**"不可比"是一等事实**：二进制/非 UTF-8 → `available=false` + `BINARY_CONTENT|NOT_TEXT`；单侧 > 2 MiB → `TOO_LARGE`；行数 > 2000 → 保留头部 + `truncated=true`；两侧 digest 相同 → `identical=true` + 空 lines（是"无差异"的事实，不是空实现）。诚实边界：控制面没有 workspace 快照枚举面（`WorkspaceBackend` 只在 CLI 参考链装配），因此做的是"制品内容 vs 制品内容"，文件树/文件级快照 diff 无 API（pageSupport G8 与文档均写明）。前端 `ArtifactDiffPanel` 与 `ArtifactBrowser` 共享同一份产物列表（不重复请求）。本地证据：全量 pytest 3297 passed/6 skipped/0 failed（DSN 固化后 postgres 用例实跑，skip 从 151 降到 6）；应用层 10 + API 4（合计 21 passed）；stub e2e 34/34（含 design-fidelity 33 路由与 example-isolation 未受影响）；live e2e 17/17（新增 `live-artifact-diff.spec.ts` 2 例：真实 HTTP 返回 1 added/1 removed/3 context、同制品 identical、未知制品 404 `Artifact Not Found`）；m0 23/23 PASS；web lint/typecheck/unit(73) 绿；ruff/mypy 绿。commit `7eece2f`。实现与计划文字的差异（如实记录）：`diff_texts(...)` → `diff_artifacts(DiffSide, DiffSide)`（规避 ruff PLR0913）；live 正向链改由 `tests/api/console_api_app.py` 注入受控制品——实测 live 装配的 m12 参考链终态 FAILED 且 artifact 列表 0 条（无后台 worker），记入 MEM-20260914-024。CI run #63（34846151640）终态：quality-ubuntu-latest ✅、quality-windows-latest ✅、console-frontend ✅、container-quality ✅、eval-gate ✅；collector-quality ❌（**日志实测确认**仍是 RECHECK-042 起登记的同 2 项既有 flake）。RECHECK-20260914-047 = PASS_WITH_WARNINGS（W-2 live 正向链依赖受控 fixture、W-3 内容级而非文件级口径、W-6 stub 用例内覆盖避免基线漂移）。EC-04 → 仍 PARTIAL（本批交付 1 项；真 pause-resume 执行协调 / 实验队列 / memory capability policy G16 余 3 项）。
- 2026-09-15 cycle 8 = PLAN-20260914-048（EC-04 第三批：pause/resume 真执行协调）：**暂停事实只存一份**——`runs` 行的 canonical state 即暂停信号，派发面（`claim_next` 三实现，SQLite `json_extract` / PostgreSQL `->>` / Fake 状态视图）与执行器谓词都读它，不引入第二个标志位。派发暂停：PAUSED run 的 QUEUED 任务不再被认领，**已持租约不撤销**（无抢占、无孤儿）；执行器观测：组边界读到暂停即**零任务执行**返回 PAUSED，剩余 specs 经 `on_pause` 交回暂存；API：pause/resume 与 interventions 同实现，响应带 `dispatch`/`execution_context`/`continuation`（无暂停上下文时 `continuation=NONE`，只解除暂停，不伪造续跑）。诚实边界（RECHECK-048 W-2/W-3）：进程内 run 是同步执行（`POST /runs` 阻塞式），HTTP 层无法在运行中途插入 pause，因此不存在"抢占式物理暂停"；暂停也不发新的 outbox 事件类型。本地证据：全量 pytest 3319 passed/6 skipped/0 failed；应用层 5 + 契约 9（Fake/SQLite/PG）+ API 5 = 19 新增；m0 23/23 PASS；web lint/typecheck/unit(73) 绿；stub e2e 34/34；live e2e 17/17。commit `a5d83dc`。附带修正：夹具补 `runs_store`（与生产 composition 同侧，否则派发面读不到 run 行、断言是空的）；SQLite `runs` DDL 收敛到 `db.RUNS_SCHEMA_SQL` 单一来源。CI run #65（34881096941）终态：quality-ubuntu-latest ✅、quality-windows-latest ✅、console-frontend ✅、container-quality ✅、eval-gate ✅；collector-quality ❌（**日志实测确认**仍是 RECHECK-042 起登记的同 2 项既有 flake）。RECHECK-20260915-048 = PASS_WITH_WARNINGS。EC-04 → 仍 PARTIAL（本批交付 1 项，余 2 项）。
- 2026-09-15 cycle 9 = PLAN-20260914-049（EC-04 第四批：memory capability policy G16）：**能力策略不新增第二套判定**——记忆门链的 policy 阶段复用控制面运行期的同一个 `PolicyEvaluator`（`NativePolicyEvaluator` + `examples/config/policy.yaml`），`memory.write` 成为一等 capability：policy.yaml 显式声明四个 tier 的 allow（**默认行为与接线前一致**，避免 default DENY 把既有写入打回 422）、capabilities.yaml 注册、preflight 镜像新增**多 scope 门链能力**常量 `_GATE_CAPABILITY_SCOPES`（镜像测试由单值相等改为**并集相等**，同样严格、未放宽为子集）。运行时：SQLite/PG 两套组成与 e2e 夹具共用 `services/api/assembly.py::policy_bindings()` 注入真实求值器，门链拒绝 reason 从常量文案改为求值器理由（如 `policy deny: matched deny rule`）；policy 未加载时 evaluator 为 None（端点诚实 503、门链退回 provenance + curator 兜底，不伪造默认策略）。可见性：新增只读 `GET /policy/capabilities`（声明规则 + 逐 scope **有效判决**，由运行期同一求值器计算，不做第二套判定），console govern/audit Memory Tab 新增策略面板，G16 标记**已交付**。本地证据：全量 pytest 3333 passed/6 skipped/0 failed；应用层 8 + API 4 + stub e2e 2 = 14 新增；m0 23/23 PASS；ruff/mypy/eslint 绿；stub e2e 36/36。commit `14e6c4f`。CI run #67（34928371669）终态：quality-ubuntu-latest ✅、quality-windows-latest ✅、console-frontend ✅、container-quality ✅、eval-gate ✅；collector-quality ❌（**日志实测确认**仍是 RECHECK-042 起登记的同 2 项既有 flake）。RECHECK-20260915-049 = PASS_WITH_WARNINGS。EC-04 → 仍 PARTIAL（本批交付 1 项，余实验队列 G14 queue/schedule）。
- 2026-09-15 cycle 10 = PLAN-20260914-050（末轮：EC-05 判定 + EC-06 处置/诚实登记）：**EC-05 → PASS**：33 条规范路由的能力声明从人工清点变为机检锁死——新增 `apps/web/tests/unit/page-support-coverage.test.ts` 三例（每条规范路由必须有显式支持条目、非 full 必有可读 reason、gap 级只允许非业务页），并带反证断言（未登记键确实落到默认 gap，证明断言非空）；实测分布 10 full / 22 partial / 1 gap（gap 仅 `ops/matrix` 界面状态说明页）。**EC-06 → 收口面交付 + 判定 BLOCKED**：收口面 = RECHECK-050 PASS_WITH_WARNINGS；Mimosa 密封深扫 `scan-2026-09-15T04-43-03.726Z-4bad20180460`，seal `sha256:bfeaf946…c5f2db31`，36 findings / 2504 parsed files / 182 packages，coverage partial、runStatus inconclusive、verdictEffect none，逐条处置入 `docs/audits/PA1_MIMOSA_REVIEW.md`（**不宣称安全**）；HIGH `yaml.load` 误报由新增 4 例可证伪测试锁定（三个 `!!python/*` 标签载荷必须解析失败 + loader 源码去注释后必须含 SafeLoader 子类且无 FullLoader/UnsafeLoader）。未达成面：`collector-quality` 在 run #61–#68 每次失败且失败测试恒为同 2 项——`test_collector_persists_research_os_spans`（collector 可达但 file exporter 45s 内未落盘 marker）与 `test_scenario_d_network_partition_no_old_authority`（teardown wait(10)：worker 的 SIGTERM 只置 drain 标志、不打断 25s 在途执行；Windows 本地 terminate=TerminateProcess 故永不复现）。**这纠正了此前 8 个 cycle 把该 job 记作 timing flake 的口径：它是持续失败，不是抖动**；按 fix_policy 不调超时、不让断言让步，登记为人工决策点（修 worker 关闭语义 / OTel 证据链，或改判该 job 验收口径；workflow 属治理面循环内不改）。本地证据：web unit 76/76（+3）、tsc/eslint 绿、authoring 套件 13 passed（+4）、全量 pytest 3336 passed / 6 skipped（首跑 1 例负载敏感失败，隔离复跑通过）、m0 23/23 PASS。预算：frontmatter max_cycles 由 8 依据用户更新授权（持续循环迭代，迭代10次）记为 10——变更来源在此登记；本轮用尽 ⇒ GOAL status=BLOCKED（非失败，而是预算用尽 + 存在需人工决策的阻塞项），恢复条件三条列在「终止与收口」。
- 2026-09-15 cycle 7 收口 run #64（34869444294，docs-only 提交 10dc459）终态：quality-ubuntu-latest ✅、quality-windows-latest ✅、console-frontend ✅、container-quality ✅、eval-gate ✅；collector-quality ❌（同 2 项既有 flake）——与 run #63 结论一致。
- 2026-09-14 cycle 1 CI 纠错循环：run #50 failure = openapi 快照未同批（F-1 时序，收口批 899c1fb 已修）；run #51 failure 暴露两层既有 CI 债——(a) example-console 设计 fixture 被根 data/ 规则误忽略致 fresh-checkout 类型解析失败（899c1fb 已修并验证 web lint/build 过）；(b) design-fidelity 基线仅 win32 33 张，console-frontend job 在 ubuntu runner 上必然缺 linux 基线。处置（不 skip、不降断言、不动 workflow）：playwright 官方 noble 容器（与 ubuntu-24.04 runner 同发行版）生成 linux 基线 33 张，目检 projects/run-timeline 两张抽检通过后入库。
- 2026-09-13 cycle 1 CI 债清单（run #51 quality-ubuntu 等暴露，全部既有、非本 cycle 引入）：(1) `.cursor/plans/*.plan.md` 历史散装文件含 `d:/research-system/...` 绝对链接 → Linux 上 validate_bundle/validate 失败，修：改 repo 相对链接；(2) `docs/roadmap/MILESTONES.md` 链接指向 gitignored scratch 记录，修：去链接化；(3) docs_consistency 报 M13/M14 无 COMPLETION_RECORD（本地靠 gitignored 文件通过），修：补记录或对齐检查；(4) tests/postgres 若干用例在 CI 无 15432 时直接失败而非 skip（skip guard 缺失）+ python/typecheck 仅 CI 失败，修：skip 守卫 + 定位 mypy 差异；(5) container-quality（runner 无 compose 镜像）与 collector-quality（cancelled）涉 workflow/服务配置，属治理面 → BLOCKED 待人工决策。(1)-(4) 为 cycle 2 修复范围。

- 2026-09-12 创建（ACTIVE）：GOAL 格式定稿（README），PLAN-040 作为前置输入；
  授权含 push-to-main-for-CI；等待「执行 GOAL-001 下一 cycle」指令进入 cycle 1。
- 2026-09-13 驱动适配定稿：GOAL 契约驱动无关（会话/cron/客户端 goal 模式三选一，
  限额以 frontmatter 为准，单驱动推进）；经查证当前 ZCode 安装无 agent 侧 goal
  模式工具面（可见能力为 plan mode、定时自动化、子代理），故不绑定客户端模式，
  无人值守路径由定时自动化承担。
