---
id: RECHECK-20260911-039
plan_id: PLAN-20260910-037
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-11
completed_at: 2026-09-11
reviewer: independent-review-agent + root-agent-gate-evidence
baseline_ref: 9c3e34d
checked_head: 5b2388f
---

# RECHECK-20260911-039 — 前端预留接口 ↔ 后端对接独立复检

独立复检代理逐 AC 对抗性核查（不采信实现阶段完成声明；实跑定向测试与门禁），
根级收口门禁由主代理以实际命令输出补全。AC-01 至 AC-09 全部 PASS。
复检实跑工作树 = 5b2388f（git status clean；其内容与复检时评估的树一致：
cfdf84d/5b2388f 仅格式与文件归位，无逻辑差异）。

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260910-037-frontend-backend-api-integration.md`。
- 变更范围：WP-A~H 九个提交（9fa1641、7fd0aba、77a9f40、02c236a、8d9587e、
  ba1fea6、3d4efc2、4358b5c、3e0db85）+ 收口 cfdf84d、5b2388f；
  控制面新增 13 端点、前端 5 域接线、文档/spec 同步。
- 边界：③类（多项目、身份/billing、tool-packs 供应链、prompts/datasets/
  notebooks/reports/alerts/incidents/schedules/data-health、budget_adjust、
  forecast、DELETE 面）零扩建；pageSupport/CONSOLE_PAGE_MAP 保持诚实标注；
  example 树零 `/api`（example-isolation 实跑证明）。

## 检查结果

| AC | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| AC-01 | 10 个原预留 client 函数逐一有 UI 调用方；全量扫描 57 个 facade 函数无死预留 | 复检 grep 行号 + api 面穷举扫描；stub e2e 29/29；plan-team/notifications 基线按批准重录 | PASS |
| AC-02 | protocol_source 共享 loader；DTO 双来源；四端点同源；旧 path 兼容 | pytest test_protocol_source_draft + test_team_protocol_api = 19 passed；T14 baseline 更新 | PASS |
| AC-03 | artifacts 三端点 + 503/404/410/413 + nosniff/ETag；composition 双实例修复（根因注释在位） | pytest test_artifacts_api = 7 passed；PG 路径复用 PostgresArtifactStore | PASS |
| AC-04 | provider_health 三态枚举；checks 判定（default HEALTHY=注入方契约、OPEN_CIRCUIT/DISABLED 出局、UNKNOWN/DEGRADED 警示）；无 `{pid: True}` 残留（全局 grep）；日序列混合定价不求和 | pytest provider_preflight(8)+cost_daily(6)+cost_daily_api(3) = 17 passed | PASS |
| AC-05 | 项目视图/预注册/归档；experiment_store 槽位 PG-only、SQLite 503；queue/schedule 保持禁用；cancel→archive 偏差如实登记 | pytest test_experiments_api = 6 passed；pageSupport 文案一致 | PASS |
| AC-06 | 完整 §8 门链（sanitize→schema→provenance→contradiction→curator→commit→事件）；两阶段 decide 不提供（docstring 明示）；policy 槽位显式 None 有理由（_CAPABILITY_SCOPE 镜像约束 → follow-up G16） | pytest test_memory_api + tests/application/memory = 58 passed | PASS |
| AC-07 | recent_events port + 双 adapter（SQL DESC / sink 尾部反转）；白名单排除 task.*；读状态 view-state 持久化 | pytest test_notifications_api = 4 passed；live e2e 断言 manifest.frozen 投影与 ghost 404 | PASS |
| AC-08 | human-gate 注册→WAITING→approve 续跑→终态；重启 503 不消费审批（无 fake resume）；HUMAN_GATE WARNING→INFO 有据（否则 freeze 阻断，审批门不可达）；demo 协议存在 | pytest test_approval_registration + test_approvals_api = 14 passed；INFO 降级断言在 test_m2 | PASS |
| AC-09 | 门禁全绿：ruff check（product roots + .cursor 全量）；format --check；mypy 750 files 0 错；source-limits/naming/arch-ts = 789；node 边界测试 5/5；tsc/eslint/unit 70/70；stub e2e 30/30；live e2e 7/7；openapi 再生零漂移 + contract 2/2；framework/hook/learning evals、system-spec、docs_consistency 全 PASS；Docker/PG 依赖测试在 DSN gating 环境全绿（此前失败确认为 litellm dotenv 注入操作员 DSN 的环境问题，非代码回归） | 各命令实际输出见计划"证据"节；recheck 代理独立复跑定向套件 | PASS |

## 警告（不影响判定）

1. m0 runner 单次全量运行受后台任务时限截断：按其 job 定义分组（python 6、
   typescript 9、framework 8）逐一实跑复现全绿，等效完成。
2. Docker/PG 环境依赖测试（m12 容器 e2e、pg_crash_restart）在未钉 DSN 的
   混合顺序下会因 litellm dotenv 注入操作员 DSN 失败；按既有 gating 配方
   （RESEARCHOS_POSTGRES_DSN 钉测试 DSN + 其余 DSN 键清空）复跑全绿。
3. 本 session 内 Mimosa PreToolUse 多次返回 scanner_enobufs/library_source
   未完整扫描结论（Write/Edit 检查以兼容策略放行）；项目级密封深度扫描未
   完成，不得宣称"项目安全已审计"——遗留项：另跑 /mimosa-security-scan
   深度审计并处置其对本批新文件的结论。
4. 语义偏差（cancel→archive、无两阶段 decide、HUMAN_GATE INFO、
   memory capability policy follow-up=G16）均已登记于计划"偏差记录"与
   CONSOLE_PAGE_MAP G 表，非隐瞒。

## 结论

PASS_WITH_WARNINGS。计划可标记 DONE；警告 3（深度扫描）作为独立后续任务跟踪。
