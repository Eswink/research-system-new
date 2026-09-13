---
id: RECHECK-20260913-042
plan_id: PLAN-20260912-042
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-13
completed_at: 2026-09-13
reviewer: root-agent-gate-evidence
baseline_ref: c3c2811
checked_head: cycle 2 commit（见状态历史）
---

# RECHECK-20260913-042 — CI 既有债修复独立复检

GOAL-20260912-001 cycle 2 派生计划的复检。本 cycle 的产物全部是测试守卫、
检查器缺陷修复与历史记录链接修复——不引入产品行为变更，因此复检以「本地全门
命令输出 + CI run 终态」为权威证据，逐 AC 核对。判定 PASS_WITH_WARNINGS
（WARNING = collector-quality 仅剩 2 项既有 timing flake，超出本 cycle 范围，
见 W-1）。

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260912-042-ci-debt-remediation.md`
  （`parent_goal: GOAL-20260912-001`）。
- 变更范围：`tests/conftest.py`（新增）、`tests/postgres/test_workflow_engine_parity.py`、
  `tests/adapters/execution/test_docker_backend_e2e.py`、
  `tests/adapters/sqlite/test_project_store.py`、
  `tests/adapters/workspace/test_file_backend.py`、
  `tests/observability/test_telemetry_overhead.py`、
  `tools/docs_consistency_check.py`、两个 `.cursor/plans/*.plan.md` 历史文件、
  `docs/roadmap/MILESTONES.md`。
- 边界：零改动 `.github/workflows/*`；零改动产品代码（packages/adapters/services/apps）。

## 检查结果

| AC | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| AC-01（WP-A） | WinDLL/windll Linux 属性缺失修复不改语义；历史绝对链接改 repo 相对；MILESTONES 去链接化 | `mypy tests/observability/test_telemetry_overhead.py` 与 `--platform linux` 均 Success；`validate_bundle.py` 通过；`governance validate.py` 通过 | PASS |
| AC-02（WP-B） | docs_consistency 大小写 bug 修复不放松规则（仍要求 DONE milestone 有 COMPLETION_RECORD 或 recheck） | `python tools/docs_consistency_check.py` = PASS（6 checks）；`pytest tests/tooling/test_docs_consistency_check.py` = 10 passed | PASS |
| AC-03（WP-C） | 无环境时 skip 而非 fail；`-m requires_docker` 仍 fail-closed；PG parity 标记；3 处测试缺陷修复 | `pytest tests/adapters/execution` = 58 passed/31 skipped/0 failed；`-m requires_docker` = 硬失败；`pytest tests/postgres/test_workflow_engine_parity.py` = 5 skipped；`test_project_store` 7 passed；file_backend 语义断言两平台安全 | PASS |
| AC-04（WP-D） | 全量本地门全绿；push 后 quality-ubuntu/console-frontend 终态 | `run_all_checks.py --profile m0` = 23/23 PASS（全量 pytest 2997 passed/205 skipped/0 failed）；CI run 终态见状态历史 | PASS |

## 警告与处置

1. **W-1（WARNING，范围外 BLOCKED）** run #53 终态：quality-ubuntu-latest ✅、
   console-frontend ✅、quality-windows-latest ✅、container-quality ✅、eval-gate ✅；
   collector-quality ❌——失败为 2 项**既有** timing flake：
   `test_collector_persists_research_os_spans`（file exporter 轮询 45s 未落盘 marker）、
   `test_scenario_d_network_partition_no_old_authority`（partitioned worker
   `subprocess.wait` 10s 超时）。run #52 同两项 + 3 项 GPU 失败 = 5，cycle 2 的
   GPU/docker 守卫将其降至 2，说明尾 2 项与本 cycle 无关、属 CI 负载下既有
   timing/环境 flake。collector-quality 的通过性**不在本 cycle 验收内**；
   待人工判定是否为其补重试/探针（非本 cycle 授权范围）。
2. **W-2（INFO）** 全量 pytest 在本机有 205 skipped（docker/GPU/PG/collector 在
   无对应环境时诚实跳过）；GHA 的 collector-quality 作业设
   `RESEARCHOS_REQUIRE_POSTGRES/COLLECTOR=1` 时这些用例仍 fail-closed，不被本
   守卫削弱。
3. **W-3（INFO）** `tests/conftest.py` 的 docker 探测要求 Linux-capable daemon；
   若将来在 windows-latest 上以 Linux 容器模式跑，探测会放行，行为符合预期。

## 结论

PLAN-20260912-042 AC-01~AC-04 全部满足，W-1 为已登记范围外 BLOCKED。判定
**PASS_WITH_WARNINGS**，计划 DONE。GOAL-20260912-001 EC-01 → PASS；cycle 3
输入：EC-02（reports/integrations/全局血缘经既有 deliverable/tool_plane/跨 run
投影的 HTTP 面 + 页面翻 live）。
