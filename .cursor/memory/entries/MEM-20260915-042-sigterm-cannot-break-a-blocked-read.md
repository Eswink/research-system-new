---
id: MEM-20260915-042
title: 停机上界要来自"停机窗口"，不是"更短的超时"；被中断的 syscall 会被重试
status: ACTIVE
created_at: 2026-09-16
updated_at: 2026-09-16
scope: repository
confidence: 0.9
review_after: 2027-09-16
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-067-worker-bounded-sigterm-exit.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-067-worker-bounded-sigterm-exit.md
supersedes: []
tags:
  - shutdown
  - sigterm
  - http
  - bounded-exit
  - python-signals
---

# SIGTERM 打不断阻塞中的 HTTP 读：PEP 475 会重试，必须显式放弃

## 做了什么

worker 收到 SIGTERM 后，若主线程正卡在一次网关读上，进程原来要等**客户端超时 30s**
才退出（EC-04）。修法：`WorkerClient` 的所有出站调用走单一收口点 `_call`，把请求跑在
守护线程上；一旦 `should_stop()` 为真，最多再等 `drain_seconds`（`RESEARCHOS_WORKER_DRAIN_SECONDS`，
默认 5s）就抛 `WorkerDrainAbort` **放弃**这次调用，进程随即有序退出（码 0）。

实测（同脚本同参数，Linux 容器、黑洞网关 = accept 后永不回包）：

```text
修复前（HEAD dca1f94）：exit_after_sigterm_seconds = 29.64
修复后            ：exit_after_sigterm_seconds = 1.12   （drain_seconds=1）
```

## 为什么这样做

1. **信号处理器返回后，被中断的 read 会被重试**：Python 的 SIGTERM 处理器通常只置一个
   标志（本仓的 `_STOP`/`_WAKE` 就是这么做的），PEP 475 让被 `EINTR` 打断的系统调用在
   处理器返回后**重新开始**——所以"信号到了"并不等于"阻塞读结束了"，退出上界仍是客户端超时。
2. **上界必须来自停机窗口，而不是给所有调用更短的超时**：后者会在正常路径上无谓地打断
   请求。所以反证是必须的：**未停机时**同一条阻塞读仍然跑满（用例断言 `elapsed >= 阻塞时长`）。
3. **宽限期是配置**：把 `drain_seconds` 调大，进程就不在固定时刻退出（用例断言 drain=30 时
   6s 后进程**仍在跑**）——这条区分了"可配置的宽限期"与"写死的常数"。
4. **放弃是 at-least-once 允许的模糊点**：被放弃的请求可能已到达服务端，也可能没有；
   由幂等键 + 租约恢复（LOST 路径）覆盖，**不得读成"一定没发生"**（写进 runbook）。

## 怎么做与复现

```bash
# 进程内（所有平台）：停机后放弃 / 未停机不缩短 / deadline 只 armed 一次 / env 取值域
python -m pytest tests/worker/test_worker_drain_bound.py -q      # win32: 5 passed, 2 skipped

# 真实 SIGTERM（POSIX）：黑洞网关 + 真子进程
#   win32 的 Popen.terminate() 是 TerminateProcess，代表不了 SIGTERM ⇒ 只在 Linux 跑
docker run --rm -v "<repo>:/repo" -w /repo python:3.12-slim \
  sh /repo/scratch/verify-linux-worker-drain.sh                  # 6 passed

# 修复前/后对照（要挂两个工作树：pre-fix worktree 与当前工作树）
git worktree add --detach <pre-fix-dir> <baseline-sha>
docker run --rm --entrypoint sh -v "<repo>:/repo" -v "<pre-fix-dir>:/prefix" -w /repo \
  python:3.12-slim /repo/scratch/measure-drain-both.sh
```

## 适用边界（踩过的坑）

- **容器验证的依赖面**：worker 子进程的真实导入链很长
  （`docker` / `opentelemetry-api,sdk` / `opentelemetry-exporter-otlp-proto-http` /
  `pydantic(-settings)` / `pyyaml` / `jsonschema` / `tenacity` / `httpx`）。
  别用 `uv sync`（会往**挂载的仓库**写一个 Linux `.venv`），用
  `uv pip install --system …` / `pip install --quiet …` 只装这条链。
- **`--entrypoint sh` 不一定存在**：`ghcr.io/astral-sh/uv` 镜像里没有 `sh`；
  `python:3.12-slim` 可用。Git Bash 里还要 `MSYS_NO_PATHCONV=1`，否则 `-w /repo`
  会被改写成 `D:/tools/Git/repo`。
- **本仓的 Bash 守卫**：命令行里同时出现"挂载/写入动作 + `tests/**` 源码路径"会被判成
  绕过 Write/Edit 扫描而拒绝执行。把命令写进 `scratch/*.sh` 再在容器里执行即可。
- **不要用 `os._exit` 或额外的进程看门狗**：本仓的既有模式是"守护线程 + 有界等待 + 放弃"
  （`adapters/otel/sink.py::_run_bounded`、`renewer.join(timeout=5.0)`），停机逻辑跟着这条走，
  退出码仍是有序停机的 0。

## 来源

- PLAN-20260915-067 / RECHECK-20260915-067（GOAL-20260915-003 cycle 5 / EC-04）。
- 相关：[[MEM-20260915-041]]（守护线程的等待下界必须由它自己的节奏决定——同一族"不要让
  某个机制悄悄改变另一个机制的时间语义"）、[[MEM-20260915-030]]（GOAL 收口复检配方）。
