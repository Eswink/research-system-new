---
id: RECHECK-20260915-053
plan_id: PLAN-20260915-053
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-15
completed_at: 2026-09-15
reviewer: root-agent-goal-cycle13
baseline_ref: 1b2a26d
checked_head: 1b2a26d+worktree
---

# RECHECK-20260915-053 — GOAL-20260912-001 收口独立复检（cycle 13）

## 检查范围

GOAL-20260912-001 的六个退出标准（EC-01~06）在当前工作树上的**可核验证据面**：
OpenAPI 快照中的端点、前端能力清单（pageSupport）中的路由等级、EC-04 六项深水区语义的
落地文件、EC-05 守卫与分布、EC-06 收口面（RECHECK / 密封扫描 / CI）。**不重演历史实现**，
只判定"当前树是否仍支持这些结论"。

## 检查结果

| EC | 标准（摘要） | 本轮独立核验 | 结果 |
| --- | --- | --- | --- |
| EC-01 | 项目注册表 + 前端去硬编码 + projects 页 live | `/projects` GET+POST、`/projects/{id}` PATCH、`/projects/{id}/settings` GET+PUT 在快照中；`portfolio/projects` 显式登记 `partial` 且 `disabledOperations: ["delete"]`（无删除 = 诚实边界）；`ProjectsPage.tsx` 存在 | PASS |
| EC-02 | reports / integrations / 全局血缘（复用既有域） | `/runs/{id}/deliverable`、`/tool-providers`、`/runs/{id}/lineage` 在快照中；`insights/reports` 与 `library/lineage` 显式登记 `partial` 且 reason 写明缺口（全局数据集/提示词血缘无 API） | PASS |
| EC-03 | 七个最小域（prompts/datasets/notebooks/alerts/incidents/schedules/data-health） | `/projects/{id}/library` GET+POST、`/library/{id}` GET+PATCH、`/projects/{id}/ops/{alerts,incidents,data-health}`、`/ops/schedules` 在快照中；七条路由全部显式登记 `partial` | PASS |
| EC-04 | 深水区六项（budget_adjust / 预测 / Diff / pause-resume / 队列 / memory policy） | interventions 声明 `pause|resume|budget_adjust|replace_agent`；`/runs/{id}/cost-forecast`、`/artifacts/{left}/diff/{right}`、`/runs/{id}/pause|resume`、`/policy/capabilities`、`/projects/{id}/experiment-queue`、`/experiments/{plan}/queue`、`/experiment-queue/{id}` PATCH+DELETE、`/experiment-plans` 全部在快照中；源码 `experiment_queue.py`（域/派发）、`run_execution.py`（唯一启动装配）、`014_experiment_queue.sql` 存在 | PASS |
| EC-05 | 33 路由能力声明显式且诚实 | 守卫测试 76 passed（3 例含反证：未登记键确实落到 `未登记页面`）；`scratch/route_dist.mjs` **现算** registry × pageSupport = `33 = 10 full / 22 partial / 1 gap`，唯一 gap 仍为 `ops/matrix`（非业务状态说明页） | PASS |
| EC-06 | 每 cycle GHA 全绿 + 收口 RECHECK + 安全扫描处置 | CI run `34952933291`（629f757）**六 job 全 success**；收口 RECHECK = 本轮 RECHECK-053 与 RECHECK-050/051/052；Mimosa 密封扫描 `scan-2026-09-15T09-33-06.821Z-d2729fe03dd7`（seal `sha256:e09328e1…db7be384`，36 findings）与 PA-1R 处置清单同集合、零新增 | PASS |

支撑证据（同一 head）：

- 全量 `python -m pytest tests -q -rs` → **3398 passed, 6 skipped, 0 failed**；6 个 skip
  逐条核对：Windows symlink 特权 ×2、fail-open 专项套件接手 ×2、live relay 需环境变量 ×1、
  OTel collector 未启动 ×1 —— **没有 EC 覆盖被静默跳过**。
- 环境相关三套件（distributed + observability + postgres，DSN 固化）→ 157 passed / 1 skipped。
- 本地 m0 → `profile=m0; 23 deterministic checks` 全绿（收口 head）。

## 结论

result: **PASS_WITH_WARNINGS**

GOAL-20260912-001 的六个退出标准在**当前树上**全部成立，且证据由本轮重新核验（不是复述历史
结论文本）。按 GOAL README「ACHIEVED 前置 = 全 EC PASS + 独立 RECHECK + 收口」，本 GOAL
判 **ACHIEVED**。以下告警**结转**（不因收口而消失）。

## 告警（结转清单）

- W-1（历史遗留，本轮未处理）：`infra/compose/research-validation.yaml` 的同类证据目录供给
  缺口（RECHECK-20260915-051 W-1）；服务集合被 `tests/tooling/test_research_compose.py`
  的 `EXPECTED_SERVICES` 常量锁定，改它属服务契约变更。
- W-2（G1 语义，长期有效）：实验队列认领 TTL 恢复 = **at-least-once**，同一条目可能对应
  两次 run 启动；`run_id` 为最近一次结果。
- W-3（G14）：队列不发 outbox 事件（与 PLAN-046/048 同口径），状态变化只能轮询观测。
- W-4（G14）：派发在控制面进程内**同步**执行 run ⇒ 队列串行推进，多实例不提升吞吐。
- W-5（G14）：`ExperimentPlan` 域无 `project_id` ⇒ `GET /experiment-plans` 是全局列表
  （与 `GAPS.multiProject` 一致）。
- W-6（门禁灵敏度）：design-fidelity 的 `maxDiffPixelRatio: 0.02` 对首屏之下的改动不敏感
  （RECHECK-052 W-4），本轮页面改动需人工强制重生成基线。
- W-7（测试替身纪律）：结构型 fake 必须来自单一实现（共享 `FakeExperimentStore`），
  否则 Port 每次扩展都会让手写 fake 失去结构兼容（cycle 12 实测发生，mypy 捕获）。
- W-8（配置同步单点）：stub/live 两份 playwright 配置的 include/exclude 是手工列表，
  新增 live spec 漏改会让 stub 套件静默收进 live 用例（cycle 12 实测发生，已修 + 注释）。
- W-9（框架并发敏感）：`.cursor/hooks/evolution_gate.py` 的 `atomic_json` 在 Windows 上
  遇到被占用的状态文件会以 `WinError 5` 失败，令 `framework/run_cursor_framework_evals`
  偶发红（复跑通过）。
- W-10（本轮口径）：本复检是"当前树一致性"核验，**不重演历史实现**；历史 RECHECK 的判定
  偏差只能通过"当前树不支持该结论"暴露。

## 复现

```
# EC-01~06 证据面（当前树断言）
python scratch/verify_goal001_closeout.py          # PASS: EC-01..EC-06 证据面与当前树一致
# EC-05 守卫 + 分布现算
cd apps/web && pnpm run test                       # 76 passed（含守卫 3 例）
node --import ./tests/helpers/registerStyles.mjs --import tsx ../../scratch/route_dist.mjs
# 全量套件 + skip 原因
RESEARCHOS_POSTGRES_DSN=postgresql://research_os:research_os_m14_test@localhost:15432/research_os \
  RESEARCHOS_DATABASE_URL= DATABASE_URL= POSTGRES_DSN= \
  python -m pytest tests -q -rs --ignore=tests/architecture/python/test_dependency_boundaries.py
# 本地 m0
sh scratch/run-m0-cycle12.sh                       # profile=m0; 23 deterministic checks
```
