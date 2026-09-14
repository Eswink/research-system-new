---
id: RECHECK-20260914-045
plan_id: PLAN-20260914-045
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-14
completed_at: 2026-09-14
reviewer: root-agent-gate-evidence
baseline_ref: e0cb3ca
checked_head: cycle 5 commit（见状态历史）
---

# RECHECK-20260914-045 — ops 只读投影独立复检

GOAL-20260912-001 cycle 5（EC-03 第二批）派生计划的复检。本 cycle 的关键设计决定
是**不做持久域**（避免"注册了却不被消费的假 scheduler/规则"），改用只读派生投影。
复检以「本地全门命令输出 + 定向 e2e + CI run 终态」为权威证据，并重点对抗核查
诚实性：能力锁定标记、缺失依赖降级、失败 Run 不自动登记为事故。

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260914-045-ops-observability-projections-live.md`
  （`parent_goal: GOAL-20260912-001`，EC-03 第二批）。
- 变更范围：新增 `packages/domain/ops_view.py`、`services/api/{routers,dto}/ops_view.py`、
  前端 `ops-view/` 目录与四页改写；改 pageSupport、docs 2 份、基线 4 路由 × 2 平台。
- 边界：无新表/迁移（纯视图，无持久化）；规则 CRUD/事故处置/用户调度/聚合报告
  全部保持禁用；M18 零触碰。

## 检查结果

| AC | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| AC-01（WP-A） | 四类视图有界校验；无持久化 | 逐行核对 ops_view.py（subject/detail 长度、枚举、interval>0）；无任何 store/migration | PASS |
| AC-02（WP-B） | 四端点真实派生 + 能力锁定 + 404/503；openapi 零漂移 | `pytest tests/api/test_ops_view_api.py` = 5 passed；`test_openapi_snapshot` 2 passed | PASS |
| AC-03（WP-C） | 四页消费真实端点；pageSupport/文档一致 | `pnpm --dir apps/web run lint/typecheck/test/build` 全绿（73/73）；`pnpm run boundaries` 无违规 | PASS |
| AC-04（WP-D） | stub/live e2e、全量 pytest、m0、CI 终态 | stub e2e 30/30；live e2e 14/14；全量 pytest 3103 passed/0 failed；m0 见状态历史；CI run 见状态历史 | PASS |

## 警告与处置

1. **W-1（WARNING，既有，非本 cycle）** collector-quality 仍见 2 项 timing flake
   （RECHECK-042/043 已登记）；quality-windows-latest 在 cycle 4 的 run #57 见
   `test_slow_tool_enforces_spec_timeout` 单个 stdio 子进程连接 flake（本地单跑通过）。
   本 cycle 未触碰二者；按 fix_policy 不放宽断言、不 skip。
2. **W-2（INFO）** 只读投影的 alerts 视图含 worker LOST/DRAINING 分支，但生产
   worker_registry 在多数装配中为空——该来源诚实缺省，非"无告警"伪装（端点/Run
   来源仍会出告警）。data-health 的 artifact 抽样 verify 对全量 refs 线性扫描，
   当前规模可接受，量大时应改分页/采样（已记为后续项）。
3. **W-3（INFO）** 基线再生沿用「强制删目标 linux 基线 + 还原无关漂移」流程
   （MEM-20260913-022）；本 cycle 4 路由 × 2 平台，无关 6 张已 checkout 还原。

## 结论

PLAN-20260914-045 AC-01~AC-04 全部满足；W-1 为既有范围外项。判定
**PASS_WITH_WARNINGS**，计划 DONE。GOAL-20260912-001 EC-03 → PASS（7 域全部交付）；
cycle 6 输入：EC-04（深水区语义：budget_adjust/成本预测/真 pause-resume/实验队列/
artifact diff/memory capability policy，未落地项保持诚实标注）。
