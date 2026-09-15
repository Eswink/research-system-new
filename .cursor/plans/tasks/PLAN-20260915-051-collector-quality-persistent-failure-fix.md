---
id: PLAN-20260915-051
slug: collector-quality-persistent-failure-fix
title: collector-quality 持续失败修复：worker 关闭语义 + OTel 证据链目录供给
status: DONE
created_at: 2026-09-15
updated_at: 2026-09-15
parent_goal: GOAL-20260912-001
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260912-001 cycle 11：用户 2026-09-15 会话确认 collector-quality 是持续失败（非 flake）且 D 场景根因已定位，要求继续 goal 循环；处置方向取「修产品行为」而非改判验收口径。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-051-collector-quality-persistent-failure-fix.md
memory_entries:
  - MEM-20260915-028
---

# PLAN-20260915-051 — collector-quality 两项持续失败的根因修复（cycle 11）

## 目标

`collector-quality` 在 run #61–#69 每次失败、失败集合恒定（2 failed / 85 passed）。
本轮把两项从"持续失败 + 人工决策点"推进到**根因已定位并修复**：

1. `test_scenario_d_network_partition_no_old_authority` —— 失败在**断言之后的 teardown**：
   worker 的 SIGTERM 处理器只置 drain 标志，主循环只在迭代之间读它，25s 在途执行
   无法在 `wait(timeout=10)` 内退出（Windows `terminate()` 走 TerminateProcess
   立即结束，故本地永不复现）。
2. `test_collector_persists_research_os_spans` —— 根因本轮**定位**：collector 容器以
   uid 10001 运行，而 fresh checkout 没有 `data/otel/`，bind mount 源目录由 Docker
   以 root:root 创建 ⇒ file exporter 打不开证据文件（`permission denied`），45s
   轮询窗口内文件始终不存在。

## 诚实边界

- **不改超时、不放宽/删除断言、不改 workflow**（`.github/workflows/*` 属治理面）。
  两项修复都落在产品/基础设施侧：worker 关闭语义 + 证据目录供给。
- 本地 Windows 无法复现 SIGTERM 语义（`terminate()` 即 TerminateProcess）；修复的
  端到端证据必须来自 Linux 侧（本轮用 Linux 容器实测），不接受"本地绿"作为证据。
- 证据文件落盘后仍由 collector 进程（uid 10001）持有，**读侧可见性**是断言成立
  的必要条件（0600 会让 runner 用户读不到），修复必须同时覆盖写与读。
- 两个本地栈（`personal-production.yaml`、`research-validation.yaml`）存在同类
  目录供给缺口，但 `research-validation.yaml` 的服务集合由
  `tests/tooling/test_research_compose.py` 契约锁定，本轮**不动**，如实登记为遗留项。

## 范围

- WP-A（worker 关闭语义）：`services/worker/loop.py` +
  `services/worker/__main__.py` —— SIGTERM 期间在途执行经**既有协作式 cancel 通道**
  中断；关停中断的作业**不提交**结果（租约由控制面回收，at-least-once 语义不变）；
  空闲心跳睡眠可被打断。含 `tests/worker/test_worker_loop.py` 新用例。
- WP-B（OTel 证据链目录供给）：`infra/compose/otel-evidence.yaml` 增加一次性初始化
  服务（mkdir + touch + chown/chmod），collector `depends_on:
  service_completed_successfully` 后启动。
- WP-C：Linux 容器端到端复验（D 场景 + collector 证据套件）+ 本地 m0 分组 +
  RECHECK-051 + GOAL 记账。

## 验收条件

- [x] AC-01（WP-A）：新增单测证明"关停在途作业 → 协作式中断 → 不提交结果"；
  SIGTERM 语义在 Linux 容器中实测（D 场景 teardown 在 10s 内完成）。
- [x] AC-02（WP-B）：在"fresh checkout ⇒ Docker 创建 root-owned 目录"条件下，
  collector 能写入证据文件，且**非属主 uid（runner 1001）可读**并检索到 marker。
- [x] AC-03（WP-C）：本地 m0 分组全绿；RECHECK-051 覆盖两项根因与证据；
  GOAL 迭代日志/状态历史与实况一致；CI run 终态记账（不预设绿）。

## 实施清单

- [x] WP-A worker 关闭语义（含单测）
- [x] WP-B 证据目录供给（compose）
- [x] WP-C Linux 容器复验 + 本地门 + 复检 + 记账

## 证据

| WP | 证据 | 结果 |
| --- | --- | --- |
| WP-A | 单测 29 passed（含 5 新例）；mypy 801 files Success；Linux 容器实测 CI job 选择 87 passed / 4 skipped / 0 failed；**反证**：移除 shutdown 分支即复现 CI 原文 `TimeoutExpired ... after 10 seconds` | PASS |
| WP-B | 命名卷复现 root:root 条件的 `permission denied`；修复后真实 compose 下文件 0644/10001 且 `--user 1001:1001` 可读并检索到 marker；`up --wait` 退出码 0 | PASS |
| WP-C | full m0 的 python/typescript 组全绿（`python/tests` 3339 passed / 5 skipped，420s；web lint/test/typecheck/build 4 项 PASS）；治理 `framework/validate` 记录补齐后复跑绿；CI 复验结论回写 GOAL | PASS |

## 已知风险

- 关停即中断在途执行会放弃该次尝试的提交；这是**有意**语义（控制面租约回收
  at-least-once），但必须写进 loop 文档字符串，避免被误读为"丢任务"。
- 若 CI 仍失败，按 GOAL「CI 失败分类」处置；同一签名超过 fix_policy 上限即 BLOCKED。
- Windows 本地无法复现 SIGTERM 语义，验证证据只能来自 Linux（容器）；最终以 CI 为准。

## 状态历史

- 2026-09-15 创建（IN_PROGRESS）：GOAL-20260912-001 cycle 11，方向 = 修产品行为。
- 2026-09-15 WP-A 完成：`CancelProbe` 抽出 `services/worker/cancellation.py`（450 行硬
  阈值推动的拆分，行为等价），SIGTERM 经既有协作式 cancel 通道中断在途执行且不提交；
  心跳睡眠/重连退避可打断。
- 2026-09-15 WP-B 完成：`otel-evidence.yaml` / `personal-production.yaml` 增加一次性
  `evidence-dir` 供给服务（mkdir+touch+chown 10001+chmod 0644），collector 等其完成。
- 2026-09-15 WP-C 完成：Linux 容器复验（CI 同一 job 选择 87 passed / 0 failed；预修复
  反证复现 CI 原文）、本地 m0 python/typescript 组全绿、RECHECK-051 判定
  PASS_WITH_WARNINGS ⇒ 本计划 DONE。
- 2026-09-15 CI 复验：run 34939068977（commit 2f688a9）六 job 全 success，
  collector-quality 自 run #61 起首次转绿 ⇒ GOAL EC-06 记 PASS。

## 影响报告

- 改动：`services/worker/cancellation.py`（新，CancelProbe）、`services/worker/loop.py`
  （关停中断 + 不提交 + 抽出探针，445 行）、`services/worker/__main__.py`（可打断的
  睡眠 + 关停唤醒事件）、`tests/worker/test_worker_cancellation.py`（新 3 例）、
  `tests/worker/test_worker_loop.py`（+2 例）、`infra/compose/otel-evidence.yaml`、
  `infra/compose/personal-production.yaml`（证据目录供给）、`infra/compose/README.md`、
  `docs/operations/OPERATIONS_RUNBOOK.md`（Worker Fleet 关停语义）+ 治理记录
  （GOAL/ALL_PLAN/PLAN/RECHECK/MEM-20260915-028）。
- lint/typecheck/test：ruff check/format 绿；mypy 801 files Success；`tests/worker`
  29 passed；`python/tests` 3339 passed / 5 skipped；web lint/test/typecheck/build 绿；
  `tests/tooling/test_python_source_limits.py` 811 passed。
- Domain/API/schema：无 Domain/API/schema 变更（worker 内部语义 + compose 供给服务）。
- 安全/凭据：无凭据面变更；未引入新上游镜像（init 复用同一次 CI 调用已有的
  `postgres:16-alpine`，仅 shell + chown，且一次性退出）；collector 仍以非 root
  （uid 10001）运行，未放宽其权限；证据文件 0644 属有意选择（sanitized 闭集词汇 + 位于
  gitignored `data/`）。
- 兼容性/迁移风险：**行为变更** = SIGTERM 现在中断在途执行且不提交该次尝试（控制面
  按租约回收，at-least-once 不变）；服务端 drain 与 Control-Plane cancel 两条路径不变。
  无数据迁移。
- 上游版本影响：无新增依赖、无 pin 变更。
- 下一项任务：CI run 复验（→ EC-06 判定）；遗留 W-1（`research-validation.yaml` 同类
  目录供给缺口，需同步其服务集合契约常量）。
