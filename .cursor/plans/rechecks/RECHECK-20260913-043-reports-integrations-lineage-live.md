---
id: RECHECK-20260913-043
plan_id: PLAN-20260913-043
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-13
completed_at: 2026-09-13
reviewer: root-agent-gate-evidence
baseline_ref: 1292b44
checked_head: cycle 3 commit（见状态历史）
---

# RECHECK-20260913-043 — reports/integrations/lineage 翻 live 独立复检

GOAL-20260912-001 cycle 3（EC-02）派生计划的复检。复检以「本地全门命令输出 +
定向 e2e + CI run 终态」为权威证据，逐 AC 核对，并对三端点做诚实性对抗核查
（空态不得伪装、全局血缘不得编造、管理动作不得偷偷开放）。

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260913-043-reports-integrations-lineage-live.md`
  （`parent_goal: GOAL-20260912-001`，EC-02）。
- 变更范围：新增 `services/api/routers/{deliverable,lineage,tool_providers}.py`、
  `services/api/run_evidence.py`、`services/api/dto/tool_providers.py`；
  改 `services/api/{app,routers/inspection,dto/inspection}.py`；前端 6 新文件 +
  5 改文件；文档 3 份；4 张 design-fidelity 基线（win32/linux 各 2）。
- 边界：M18（身份/RBAC）零触碰；Tool Provider 管理面（install/approve/revoke）
  保持 G15 锁定；全局跨 run 血缘保持 G9 honest lock。

## 检查结果

| AC | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| AC-01（WP-A） | 三端点只读语义 + 诚实边界（deliverable 无产物 available=false 且 deliverable={}、store 缺失 503、未知 run 404；tool-providers NATIVE=HEALTHY/外部=UNKNOWN、management_available=false；lineage 确定性排序、未知 run 404、global 恒 false）；拆 router 守 450 行；openapi 零漂移 | `pytest tests/api/test_reports_integrations_lineage_api.py` = 10 passed；`test_python_source_limits` = 793 passed（inspection 456→281）；`gen_openapi` + `test_openapi_snapshot` 2 passed；`mypy services/api` Success | PASS |
| AC-02（WP-B） | 三页面消费真实端点、pageSupport 等级与 disabledOperations 一致、文档同步；无 example 冒充 | `pnpm --dir apps/web run lint/typecheck/test/build` 全绿（test 73/73）；根 `pnpm run boundaries` 无违规 | PASS |
| AC-03（WP-C） | stub e2e 无 Unstubbed；live e2e 覆盖三端点 + 404；基线仅目标 2 路由 × 2 平台变化 | stub e2e 30 passed；live e2e 12 passed（含「reports/integrations/lineage 只读面」）；`git status` 基线恰 4 张；目检 linux integrations/reports 两图渲染正确 | PASS |
| AC-04（WP-D） | 全量 pytest 0 failed；m0 分组全绿；push 后 quality-ubuntu/console-frontend 终态 | 全量 pytest 3067 passed/151 skipped/0 failed；m0 见状态历史；CI run 终态见状态历史 | PASS |

## 警告与处置

1. **W-1（WARNING，既有，非本 cycle）** collector-quality 仍见 2 项 timing flake
   （`test_collector_persists_research_os_spans`、`test_scenario_d_network_partition_no_old_authority`），
   已在 cycle 2 RECHECK-042 W-1 登记，超出本 cycle 范围；本 cycle 未触碰。
2. **W-2（INFO）** 基线再生的正确姿势：playwright noble 容器内 `git clone /work`
   只含**已提交**内容，未提交的页面改动会被忽略并再生成旧基线（字节相同→无
   diff，假绿）。cycle 3 改用「按 `git status --porcelain` 把工作树叠加进 clone」
   （`scratch/gen_linux_baselines_worktree.sh`），实测 overlay 32 路径后基线正确变化。
   该脚本与事实值得沉淀（见 MEM-20260913-022）。
3. **W-3（INFO）** reports 页为 run 作用域（需选择 Run）；无 Run 时显示空态而非列表，
   与「无 reports API 时显示 gap 列表」语义不同——设计意图是读真实交付物，非伪造报告列表。

## 结论

PLAN-20260913-043 AC-01~AC-04 全部满足；W-1 为既有范围外项。判定
**PASS_WITH_WARNINGS**，计划 DONE。GOAL-20260912-001 EC-02 → PASS；cycle 4
输入：EC-03（prompts/datasets/notebooks/alerts/incidents/schedules/data-health
最小域 + live）。
