---
id: MEM-20260915-028
title: collector-quality 两项持续失败的根因与修复（SIGTERM 中断在途执行 / 证据目录供给）
status: ACTIVE
created_at: 2026-09-15
updated_at: 2026-09-15
scope: repository
confidence: 0.95
review_after: 2026-12-15
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-051-collector-quality-persistent-failure-fix.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-051-collector-quality-persistent-failure-fix.md
supersedes: []
tags:
  - ci
  - worker-shutdown
  - otel
  - evidence-discipline
  - local-green-ci-red
---

# MEM-20260915-028 — 两项"CI 红 / 本地绿"的根因都是**平台语义差**，不是抖动

## 做了什么

`collector-quality` 的两项持续失败（run #61–#69 恒定 2 failed / 85 passed）在
cycle 11 定位并修复：

1. `tests/distributed/test_scenarios.py::test_scenario_d_network_partition_no_old_authority`
   —— 失败在**断言之后的 teardown**（`partitioned.wait(timeout=10)`）。worker 的
   SIGTERM 处理器只置 drain 标志，主循环只在迭代之间读它；该 worker 用
   `RESEARCHOS_WORKER_EXECUTE_DELAY_SECONDS=25` 跑在途作业 ⇒ 25s 内不会退出，
   10s 必然超时。修复：**SIGTERM 也走协作式 cancel 通道**（在途执行 ≤0.25s 内中断），
   关停中断的尝试**不提交结果**（租约由控制面按 LOST 路径回收，与硬杀一致），
   心跳睡眠与重连退避改为可打断（`threading.Event`）。
2. `tests/observability/test_collector_evidence.py::test_collector_persists_research_os_spans`
   —— collector 容器以 **uid 10001** 运行，而 fresh checkout 没有 `data/otel/`，
   bind mount 源目录由 Docker 以 **root:root** 创建 ⇒ file exporter
   `can't open new logfile ... permission denied`，证据文件在 45s 轮询窗口内
   始终不存在。修复：compose 增加一次性 `evidence-dir` 服务
   （`mkdir + touch + chown 10001:10001 + chmod 0644`），collector
   `depends_on: service_completed_successfully`。**chmod 0644 是必要的一环**：
   collector 自己创建的文件是 0600，宿主 runner 用户读不到。

## 为什么这样做

- 两项都是**平台语义差**：Windows `Popen.terminate()` = `TerminateProcess`（立即），
  Linux = SIGTERM（协作式）；Windows bind mount 权限宽松，Linux 严格按 uid。
  "本地绿"在这里**不构成任何证据**。
- 按 fix_policy 不调超时、不放宽断言、不改 workflow：改的是产品行为（worker 关停语义）
  与栈的目录供给，不是验收口径。
- 关停中断后**不提交**是刻意的：worker 已不再代表该次尝试，提交反而会与控制面的
  租约权威竞争；放弃提交让 at-least-once + 租约回收这条既有路径承担，与崩溃/硬杀
  完全同构。

## 怎么做与复现

- Linux 侧复现/验证（Windows 无法复现 SIGTERM 语义）——用容器跑真实套件：

  ```text
  docker run --rm --network host -v <repo>:/repo -w /repo \
    -e UV_PROJECT_ENVIRONMENT=/tmp/venv -e UV_LINK_MODE=copy -e UV_PYTHON_DOWNLOADS=never \
    -e RESEARCHOS_POSTGRES_DSN=postgresql://research_os:research_os_m14_test@localhost:15432/research_os \
    -e RESEARCHOS_OTEL_COLLECTOR_ENDPOINT=http://localhost:4318 -e RESEARCHOS_REQUIRE_COLLECTOR=1 \
    python:3.12-slim sh <repo>/scratch/linux-verify-collector-quality.sh
  ```

  （容器内 `pip install uv==0.11.18 && uv sync --frozen --dev`，再用
  `/tmp/venv/bin/python -m pytest`；`--network host` 让容器直连宿主 loopback 的
  postgres:15432 与 collector:4318。）
- 反证（证明是修复带来的绿）：临时移除 `_cancel_probe` 里的 shutdown 分支后，
  同一 Linux 运行必然复现 CI 原文
  `subprocess.TimeoutExpired ... 'd-partitioned' ... after 10 seconds`。
- 证据目录供给的 CI 条件复现：用命名卷替代 bind mount（命名卷与 Docker 新建的
  bind 源目录同属 root:root 0755），跑真实 `infra/compose/otel-evidence.yaml`，
  再用 `docker run --user 1001:1001 ... grep <marker>` 验证**读侧**可见。
- 本地 m0：`scratch/run-m0-cycle11.sh`（要点：`.venv/Scripts` 必须在 PATH，否则
  `python/dependency-boundaries` 因 `shutil.which("lint-imports")` 找不到而假红；
  DSN 按 [[m0-gating-dsn-pinning]] 固化）。

## 适用边界

- 适用于"CI 红 / 本地绿"的判读：先问**平台语义差**（信号、权限、大小写、路径规则），
  再问时序抖动；只有"同一签名时红时绿"才配叫 flake（对照 [[MEM-20260915-027]]）。
- worker 关停语义的这次改动**不覆盖**控制面 `drain`（仍为"不再认领 + 在途作业正常
  收尾"）与 `POST /runs/{id}/cancel`（仍提交 CANCELLED）；三者语义不同，见
  `docs/operations/OPERATIONS_RUNBOOK.md` 的 Worker Fleet 节。
- `infra/compose/research-validation.yaml` 存在同类目录供给缺口，但其服务集合由
  `tests/tooling/test_research_compose.py` 的常量锁定，未在本轮修改（见 RECHECK-051 W-3）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260915-051-collector-quality-persistent-failure-fix.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260915-051-collector-quality-persistent-failure-fix.md`
- 代码：`services/worker/loop.py`、`services/worker/__main__.py`、
  `infra/compose/otel-evidence.yaml`、`infra/compose/personal-production.yaml`
- CI 取证：run #61–#69 的 collector-quality job 日志（`FAILED` 两行恒定）
- 相关：MEM-20260915-027（持续失败 vs flake 的口径）、MEM-20260913-021（linux-only 检查器）
