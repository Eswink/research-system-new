---
id: PLAN-20260915-067
slug: worker-bounded-sigterm-exit
title: worker SIGTERM 有界退出（EC-04）
status: DONE
created_at: 2026-09-16
updated_at: 2026-09-16
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 5 = EC-04（worker 退出语义：SIGTERM 有界中断阻塞中的 HTTP 读）。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」；push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-067-worker-bounded-sigterm-exit.md
memory_entries:
  - MEM-20260915-042-sigterm-cannot-break-a-blocked-read
---

# PLAN-20260915-067 — worker SIGTERM 有界退出（GOAL-003 cycle 5 / EC-04）

## 目标

SIGTERM 之后，worker 进程必须在**有界时间**内退出——即使此刻正阻塞在一次网关 HTTP 读上。
今天这个上界等于客户端超时（30s）：信号处理器只置标志，主线程仍卡在 `recv`，
PEP 475 会在处理器返回后**重试**那次被中断的系统调用，于是进程要等
`httpx.ReadTimeout`（30s）才走到退出路径。

```text
今天：  SIGTERM → 置标志 → （阻塞读继续）→ 30s 后 ReadTimeout → 重连层看到 should_stop → 退出
本轮：  SIGTERM → 置标志 → 在途调用最多再等 drain_seconds → 放弃该调用 → 立即走退出路径
```

## 口径（这轮最容易做错的地方）

1. **有界 ≠ 立刻**：给在途调用一个明确的 drain 宽限期（默认 5s，可用
   `RESEARCHOS_WORKER_DRAIN_SECONDS` 覆盖），让"马上就能回来的"请求正常完成；
   超过宽限期才放弃。放弃是**幂等**语义可覆盖的（at-least-once + 幂等键；
   CP 侧按 LOST 恢复租约，与 worker 崩溃走同一条路）。
2. **不改变未停机时的语义**：没有停机请求时，调用照旧按客户端超时阻塞/抛错——
   本轮加的是"停机后的上界"，不是"给所有调用加一个更短的超时"。
   （反证用例必须能证伪这一点：不置停机标志时，同一条阻塞读仍然等满客户端超时。）
3. **单一收口点**：客户端里所有出站调用走同一个 `_call`，避免"修了 claim 忘了 upload"。
4. **不引入第二套停机机制**：仍由 `__main__` 的 `_STOP` 标志 + `_WAKE` 事件驱动；
   本轮只是让在途调用可以被放弃，**不新增进程看门狗、不 os._exit**。
5. **退出码不变**：SIGTERM 仍是有序停机（返回 0），放弃在途调用不改变退出码。

## 范围

- 新增：`services/worker/` 侧不新增模块（`loop.py` 已 445 行，逼近 450 硬上限，**本轮不改它**）；
  在途调用的放弃逻辑与异常类型放在 `adapters/worker/client.py`（269 行，有空间）。
- 修改：`adapters/worker/client.py`（`WorkerClientConfig.drain_seconds`、`WorkerClient`
  的 `should_stop` 注入、`_call` 收口、`WorkerDrainAbort`）、
  `services/worker/__main__.py`（把 `should_stop` 传给客户端、`main()` 捕获放弃异常 → 0、
  新增 env 开关）、`docs/operations/OPERATIONS_RUNBOOK.md`（停机语义补"在途调用有界放弃"）。
- 测试：`tests/worker/`（定向单测：阻塞读 + 停机 → 有界放弃；未停机 → 不放弃）、
  `tests/distributed/`（真实 SIGTERM 子进程用例，POSIX；Windows 上 skip 并在注释里写明理由）、
  `tests/distributed/worker_harness.py`（新 env 开关进 `worker_child_env` 白名单）。
- **不改**：`services/worker/loop.py`、`services/worker/reconnect.py` 的行为语义
  （放弃异常不是 `httpx.TransportError`，重连层不会重试它，直接冒泡到 `main()`）。

## 验收条件

- [x] AC-01：`WorkerClient` 的出站调用有**单一收口点**，停机后超过 drain 宽限期的在途调用
  被放弃并抛 `WorkerDrainAbort`（类型与位置写进模块 docstring）。
  ——`_call()` 收口 8 处调用（register / heartbeat / claim / submit_result / renew /
  cancel_requested / download_bundle / upload_bundle）；类型 `WorkerDrainAbort` 定义在同一模块。
- [x] AC-02：**未停机时语义不变**——同一条阻塞读仍然等满客户端超时（反证用例）。
  ——`test_no_shutdown_never_shortens_a_blocked_read`：drain=0.1s 但未停机 ⇒ 1.5s 的阻塞读
  照常跑完（断言 `elapsed >= 1.5`）；`test_client_without_should_stop_keeps_the_direct_semantics`
  证明不注入 `should_stop` 时逐字保持原语义。
- [x] AC-03：真实 SIGTERM 下进程退出时间有界：阻塞在网关读上的 worker 在
  `drain_seconds + ε` 内退出（定向子进程用例；POSIX）。
  ——`test_sigterm_exits_within_the_drain_window_while_blocked_in_a_read`（黑洞网关 +
  真子进程 + 真 SIGTERM，`drain=1` ⇒ 断言 <5s）。
- [x] AC-04：**修复前反证**——同一脚本在修复前的提交上测得的退出时间 ≈ 客户端超时。
  ——`scratch/measure-worker-sigterm-exit.py` 在容器里对两个工作树各跑一次：
  **修复前（HEAD `dca1f94`）`exit_after_sigterm_seconds=29.64`**、
  **修复后 `1.12`**（同一 `RESEARCHOS_WORKER_DRAIN_SECONDS=1`，退出码都是 0）。
- [x] AC-05：Linux 容器复验（Windows 的 `Popen.terminate()` 是 TerminateProcess，
  不能代表 SIGTERM 语义）——同一条子进程用例在 pinned Linux 镜像里跑绿。
  ——`python:3.12-slim` 容器内 `tests/worker/test_worker_drain_bound.py` **6 passed**
  （脚本 `scratch/verify-linux-worker-drain.sh`，只装 worker 导入链需要的最小依赖）。
- [x] AC-06：`RESEARCHOS_WORKER_DRAIN_SECONDS` 有默认值、有取值域校验、写进 runbook；
  未设置时不改变既有行为（默认 5s 只在停机后生效）。
  ——`_drain_seconds()`：默认 5.0、范围 `[0.1, 60]`、非数字与越界各自明确报错
  （`test_drain_seconds_env_knob_has_a_default_and_a_range`）；runbook 停机段已写明。
- [x] AC-07：全量门禁（m0 23 + 定向套件 + 契约/架构门禁不动）+ 记录（RECHECK-067 + GOAL 记账）。
  ——`tests/worker` 33 passed / 2 skipped、`tests/architecture+worker+contracts` 453 passed /
  58 skipped、`tests/distributed` 见 m0 全量、m0 **PASS: profile=m0; 23 deterministic checks**；
  RECHECK-20260915-067 + MEM-20260915-042 + GOAL 记账。

## 实施清单

- [x] WP-A 客户端收口与放弃原语（`_call` + `WorkerDrainAbort` + `drain_seconds`）
- [x] WP-B 入口接线（`should_stop` 注入、`main()` 捕获、env 开关）
- [x] WP-C 定向用例（阻塞读 + 停机 / 未停机反证 / 子进程 SIGTERM）
- [x] WP-D 修复前反证实测（干净工作树跑同一脚本，记录数字）
- [x] WP-E Linux 容器复验 + runbook 文档
- [x] WP-F 全量门禁 + 记录

## 证据

**WP-A/B（收口点与接线）**

```text
$ python -m pytest tests/worker -q
33 passed, 2 skipped in 4.68s          # 2 skipped = POSIX-only 的真实信号用例（win32）
$ python -m pytest tests/architecture tests/worker tests/contracts -q
453 passed, 58 skipped in 45.26s
$ python -m ruff check adapters/worker/client.py services/worker/__main__.py
All checks passed!   （ruff format --check、mypy 同步通过）
```

**WP-C（定向用例）**

```text
$ python -m pytest tests/worker/test_worker_drain_bound.py -q
5 passed, 2 skipped in 2.81s
# 进程内：停机后放弃在途调用 / 未停机不缩短 / 无 should_stop 保持原语义 /
#         deadline 只 armed 一次 / env 开关默认值与取值域
```

**WP-D（修复前 vs 修复后，同一脚本同一参数，容器内真实 SIGTERM）**

```text
$ docker run --rm --entrypoint sh -v "<repo>:/repo" -v "<pre-fix worktree>:/prefix" \
    -w /repo python:3.12-slim /repo/scratch/measure-drain-both.sh
=== baseline (pre-fix worktree: dca1f94) ===
repo=/prefix
drain_seconds=1
exit_code=0
exit_after_sigterm_seconds=29.64
=== fixed (working tree) ===
repo=/repo
drain_seconds=1
exit_code=0
exit_after_sigterm_seconds=1.12
```

**WP-E（Linux 容器复验）**

```text
$ docker run --rm -v "<repo>:/repo" -w /repo python:3.12-slim \
    sh /repo/scratch/verify-linux-worker-drain.sh
worker import ok
6 passed, 10 warnings in 13.23s      # 含两条真实 SIGTERM 用例
```

**WP-F（全量门禁）**

```text
$ sh scratch/run-m0-cycle12.sh      -> PASS: profile=m0; 23 deterministic checks
# 全量 pytest：3592 passed, 10 skipped（444s）
# 首轮红于 python/product-lint（两处 101 字符行，已修，未放宽断言）；
# 第二轮撞上已知 Windows 文件占用 flake（framework/run_cursor_framework_evals，
#   evolution_state.json.tmp 原子改名 PermissionError）——--profile framework 单独复跑 8/8 绿
# 收口提交 1f0c7d9 → CI run 35093603690：六个 job 全 success（无重跑）
```

## 状态历史

- 2026-09-16 创建（IN_PROGRESS）：cycle 4（EC-03 ops 调度写面）闭环后按 EC 表顺序取 EC-04。
  derive 时的关键判断：**上界必须来自"停机后的宽限期"，不能来自"给所有调用更短的超时"**——
  否则正常路径会被无谓地打断；证据必须包含反证（未停机时仍等满客户端超时）。
  另据 recon：`services/worker/loop.py` 已 445 行（硬上限 450），本轮**不改它**，
  收口点放在客户端；真实 SIGTERM 只能在 Linux 上验（Windows 的 terminate 是
  TerminateProcess，见 RECHECK-051 F-1）。
- 2026-09-16 WP-A/B 完成：`adapters/worker/client.py` 把 8 处出站调用收口到 `_call()`，
  注入 `should_stop` 后请求跑在守护线程、停机后超过 `drain_seconds` 抛 `WorkerDrainAbort`；
  `services/worker/__main__.py` 接线并新增 `RESEARCHOS_WORKER_DRAIN_SECONDS`（默认 5，
  取值域 0.1~60）。**刻意不做**：不加进程看门狗、不用 `os._exit`——沿用本仓"守护线程 +
  有界等待 + 放弃"的既有模式（`adapters/otel/sink.py::_run_bounded`、`renewer.join(timeout=5.0)`）。
- 2026-09-16 WP-C/D/E 完成：进程内五条用例（含两条反证）在 win32 全绿；两条真实 SIGTERM 用例
  在 win32 skip、在 `python:3.12-slim` 容器里跑绿（**6 passed**）。修复前/后对照用同一脚本、
  同一参数、同一镜像对两个工作树各跑一次：**29.64s → 1.12s**（drain=1，退出码都是 0）。
  runbook 写明在途读的独立上界与"被放弃的请求可能已到达服务端，也可能没有"。
- 2026-09-16 WP-F 完成：全量 m0 首轮红于 `python/product-lint`（两处 skipif 行 101 字符）
  ⇒ 收敛成模块级 marker（**未放宽断言**）；再跑又撞上**已知的 Windows 文件占用 flake**
  （`framework/run_cursor_framework_evals` 的 `evolution_state.json.tmp` 原子改名
  `PermissionError`，单独复跑 `--profile framework` **8/8 通过**）；第三次
  **m0 PASS: profile=m0; 23 deterministic checks**（全量 pytest **3592 passed / 10 skipped**）。

## 影响报告

- **Domain/API/schema**：无 Domain 变化、无 HTTP/OpenAPI 变化（本轮全在 worker 平面）。
  `WorkerClientConfig` 新增字段 `drain_seconds`（默认 5.0）与 `WorkerClient.__init__` 的
  关键字参数 `should_stop`（默认 None ⇒ 旧行为）；新异常类型
  `adapters.worker.client.WorkerDrainAbort`。
- **安全/凭据**：无凭据面变化。被放弃的请求语义已在 runbook 写明（"可能已到达服务端，
  也可能没有"），不宣称更强的一致性。
- **兼容性/迁移风险**：`should_stop` 未注入时逐字保持原语义（既有测试与一次性脚本不受影响）；
  Python 侧没有新增依赖（threading/time 是标准库），上游版本零变化。
- **可观测性**：退出路径新增一行 stdout（`worker: drain abort — ...`），与既有
  `worker: drain requested` / `worker: stopped completed=N` 同格式，供 harness 解析。
- **下一项任务**：EC-05（替身 harness 校验 Idempotency-Key）或 EC-02 剩余子句
  （provider 侧健康复核 schema digest 漂移 + 凭据绑定）。

## 已知风险

- **放弃在途请求的语义**：被放弃的 `submit_result`/`upload_bundle` 可能"服务端已收、
  worker 以为没发"。这是 at-least-once 允许的（幂等键 + 租约恢复），但必须写进 runbook，
  不能让读者以为"放弃 = 一定没发生"。
- **线程计数**：每个出站调用多一个短命守护线程；worker 的调用频率低（心跳 10s 级），
  但要确认不影响既有的并发/线程断言。
- **Windows 侧**：子进程用例在 Windows 上跳过，Linux 证据由容器与 CI 提供——
  本地 win32 只能证明"未停机语义不变"这一半。
