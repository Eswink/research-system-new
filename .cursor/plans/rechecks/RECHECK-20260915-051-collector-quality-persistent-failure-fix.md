---
id: RECHECK-20260915-051
plan_id: PLAN-20260915-051
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-15
completed_at: 2026-09-15
reviewer: root-agent-goal-cycle11
baseline_ref: 692ef19
checked_head: 692ef19+worktree
---

# RECHECK-20260915-051 — collector-quality 两项持续失败的根因修复（GOAL-20260912-001 cycle 11）

GOAL-20260912-001 的第 11 个 cycle。上一轮把 `collector-quality` 的 2 项失败登记为人工
决策点（口径：持续失败，非 flake，见 RECHECK-050 F-1 与 MEM-20260915-027）。用户在
2026-09-15 会话确认该口径并要求继续循环；本轮按「修产品行为」处置——**不调超时、不放宽
断言、不改 workflow**，两项根因均已定位并修复，且在 Linux 侧取得正反双向证据。

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260915-051-collector-quality-persistent-failure-fix.md`
  （`parent_goal: GOAL-20260912-001`）。
- 变更范围：`services/worker/loop.py`、`services/worker/cancellation.py`（新）、
  `services/worker/__main__.py`、`tests/worker/test_worker_loop.py`、
  `tests/worker/test_worker_cancellation.py`（新）、`infra/compose/otel-evidence.yaml`、
  `infra/compose/personal-production.yaml`、`infra/compose/README.md`、
  `docs/operations/OPERATIONS_RUNBOOK.md` + GOAL/ALL_PLAN/PLAN/RECHECK/MEM 治理记录。
- 边界：`.github/workflows/*` 不改（治理面）；断言与超时不动；实验队列 G14 不在本轮；
  `infra/compose/research-validation.yaml` 不在本轮（见 W-1）。

## 检查结果

| AC | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| AC-01（WP-A：worker 关停中断在途执行） | 关停时在途作业被协作式中断、**不提交**结果；SIGTERM 语义在 Linux 实测 | 单测 `tests/worker`（含新增 5 例：`test_shutdown_interrupts_inflight_job_without_submitting`、`test_shutdown_before_claim_stops_immediately` + 3 例 `CancelProbe`）= 29 passed；mypy 801 files Success；ruff check/format 绿。**Linux 实测**（`python:3.12-slim` 容器 + `--network host`，复刻 CI job 命令 `pytest tests/observability tests/postgres tests/distributed tests/e2e/test_pg_crash_restart.py -m "requires_collector or postgres or distributed"`）：**87 passed / 4 skipped / 0 failed（102s）**，对照修复前 CI 的 `2 failed / 85 passed` | PASS |
| AC-02（WP-B：OTel 证据目录供给） | fresh checkout ⇒ Docker 建 root:root 目录时，collector 能落盘、且**非属主 uid 可读** | 根因实测：把 collector 指向新建命名卷（与 Docker 新建 bind 源目录同为 root:root 0755）→ 日志 `can't open new logfile ... permission denied`、45s 内无文件。修复后实测（真实 `infra/compose/otel-evidence.yaml` + CI 条件覆写）：evidence 目录 10001:10001、`research_os_signals.json` 0644 且含 marker，`docker run --user 1001:1001 ... grep marker` = `1` / `READ_OK`，collector 日志 0 条 permission/error；`docker compose up -d --build --wait` 退出码 0（一次性服务 Exited 0 不阻塞 --wait）。本机 Linux 复刻同一 job 命令亦绿（见 AC-01 行） | PASS |
| AC-03（WP-C：本地门 + 记录 + 记账） | 本地 m0 全绿；复检与 GOAL 记账一致 | full m0：`python/tests` PASS（3339 passed / 5 skipped，420s）、`typescript/web-*` 4 项 PASS、`python/{engineering,product}-lint`+`format-check`+`typecheck`(801 files)+`dependency-boundaries` PASS；治理 `framework/validate` 在修复记录结构后复跑绿（见 W-4）。CI 复验结论在本文件冻结后回写 GOAL | PASS_WITH_WARNINGS |

## 关键发现（两项根因，均为平台语义差而非抖动）

**F-1 `test_scenario_d_network_partition_no_old_authority`（teardown 超时）**
失败发生在断言之后的 teardown：`partitioned.wait(timeout=10)`。该 worker 用
`RESEARCHOS_WORKER_EXECUTE_DELAY_SECONDS=25` 跑在途作业，而 SIGTERM 处理器只置 drain
标志、主循环只在迭代之间读它 ⇒ 25s 内不可能退出。Windows 本地 `terminate()` 走
`TerminateProcess` 立即结束，故本地永不复现（"本地绿"在此不构成证据）。
修复：`services/worker/cancellation.py::CancelProbe` 把**本地关停**接进既有的协作式
cancel 通道（不节流；网关轮询仍按 `cancel_poll_interval_seconds` 节流），关停中断的
尝试**不提交**结果（租约由控制面按 LOST 路径回收，与硬杀同构），心跳睡眠与重连退避
改为可打断。
**反证**：临时移除 `_probe` 里的 shutdown 分支后，同一 Linux 运行必然复现 CI 原文
`subprocess.TimeoutExpired ... 'd-partitioned' ... after 10 seconds`（1 failed，
9 deselected）。修复后同一命令 10 passed。

**F-2 `test_collector_persists_research_os_spans`（证据文件从未出现）**
collector 容器以 **uid 10001** 运行；fresh checkout 没有 `data/otel/`，Docker 会把
bind mount 源目录创建为 **root:root 0755** ⇒ file exporter
`can't open new logfile: /var/lib/otelcol/research_os_signals.json: permission denied`
⇒ 45s 轮询窗口内 `_COLLECTOR_FILE.exists()` 恒为 False（CI 断言输出 `... in ''`）。
修复：`infra/compose/otel-evidence.yaml`（及同缺口的 `personal-production.yaml`）
增加一次性 `evidence-dir` 服务 `mkdir + touch + chown 10001:10001 + chmod 0644`，
collector `depends_on: {condition: service_completed_successfully}`。
**chmod 0644 是必要环节**：collector 自行创建的文件是 0600，宿主 runner 用户
（uid 1001）读不到——只修目录属主会把"文件不存在"变成"权限错误"。

## 警告与处置

1. **W-1（WARNING，遗留，未修）** `infra/compose/research-validation.yaml` 存在同类
   目录供给缺口（同一 image + 同类 bind mount），但其服务集合由
   `tests/tooling/test_research_compose.py::EXPECTED_SERVICES` 精确锁定；新增服务需要
   同步改该契约常量，超出本轮"不动测试"的边界 ⇒ 单独变更处理，登记为已知遗留。
2. **W-2（INFO，口径）** Linux 证据来自 Docker Desktop 的 WSL2 容器（Linux 内核），
   与 `ubuntu-24.04` runner 同为 Linux/SIGTERM 语义，但发行版与内核版本不同；最终
   验收仍以 CI run 结论为准（本文件不预设绿）。
3. **W-3（INFO，语义变更）** 关停中断后不提交是刻意设计：worker 已不代表该次尝试，
   提交会与控制面的租约权威竞争；放弃提交复用既有的 at-least-once 回收路径。控制面
   `drain`（照常收尾）与 `POST /runs/{id}/cancel`（提交 CANCELLED）两条路径**未变**，
   三者区别已写入 `services/worker/loop.py` 文档字符串与
   `docs/operations/OPERATIONS_RUNBOOK.md`。
4. **W-4（INFO，验证口径）** 本地 m0 分两次跑：`python/tests` 首跑因
   `python/dependency-boundaries` 需要 `.venv/Scripts` 在 PATH（`shutil.which`）而假红，
   修 invocation 后 full m0 的 python/typescript 组全绿；治理 `framework/validate` 在
   本轮记录（PLAN 缺 `## 状态历史`/`## 影响报告`、MEM 指向未创建的 RECHECK）补齐后
   复跑绿。两次运行之间代码未变。
5. **W-5（INFO，范围）** compose 的 init 服务复用同一次 CI 调用里已存在的
   `postgres:16-alpine`（仅需 shell + chown），**未引入新的上游镜像**；证据文件为
   0644（世界可读）——内容是闭集词汇的 sanitized signals，且位于 gitignored
   `data/` 目录，属有意选择。
6. **W-6（INFO，回归面）** `services/worker/loop.py` 触及 450 行硬阈值 ⇒ 本轮把
   cancel 探针抽成 `services/worker/cancellation.py`（445 行 + 54 行）；这是阈值门禁
   推动的拆分，行为等价（同一节流/短路/失败安全语义）。

## 结论

PLAN-20260915-051 AC-01~AC-03 满足，判定 **PASS_WITH_WARNINGS**：

- `collector-quality` 两项持续失败**根因均定位并修复**，Linux 侧以 CI 同一 job 选择
  实测 87 passed / 0 failed，且 D 场景有预修复反证复现 CI 原文；
- 未调超时、未放宽/删除断言、未改 workflow、未引入新上游镜像；
- 剩余 CI 复验（run 结论）在本文件冻结后回写 GOAL 迭代日志与 EC-06 判定；
- 遗留项见 W-1（research-validation.yaml 同类缺口）。
