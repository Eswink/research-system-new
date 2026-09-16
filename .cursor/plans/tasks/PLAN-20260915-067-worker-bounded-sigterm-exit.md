---
id: PLAN-20260915-067
slug: worker-bounded-sigterm-exit
title: worker SIGTERM 有界退出（EC-04）
status: IN_PROGRESS
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
latest_recheck: null
memory_entries: []
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

- [ ] AC-01：`WorkerClient` 的出站调用有**单一收口点**，停机后超过 drain 宽限期的在途调用
  被放弃并抛 `WorkerDrainAbort`（类型与位置写进模块 docstring）。
- [ ] AC-02：**未停机时语义不变**——同一条阻塞读仍然等满客户端超时（反证用例）。
- [ ] AC-03：真实 SIGTERM 下进程退出时间有界：阻塞在网关读上的 worker 在
  `drain_seconds + ε` 内退出（定向子进程用例；POSIX）。
- [ ] AC-04：**修复前反证**——同一脚本在修复前的提交上测得的退出时间 ≈ 客户端超时
  （把两次实测数字都写进证据段，不是只写"应该更快"）。
- [ ] AC-05：Linux 容器复验（Windows 的 `Popen.terminate()` 是 TerminateProcess，
  不能代表 SIGTERM 语义）——同一条子进程用例在 pinned Linux 镜像里跑绿。
- [ ] AC-06：`RESEARCHOS_WORKER_DRAIN_SECONDS` 有默认值、有取值域校验、写进 runbook；
  未设置时不改变既有行为（默认 5s 只在停机后生效）。
- [ ] AC-07：全量门禁（m0 23 + 定向套件 + 契约/架构门禁不动）+ 记录（RECHECK-067 + GOAL 记账）。

## 实施清单

- [ ] WP-A 客户端收口与放弃原语（`_call` + `WorkerDrainAbort` + `drain_seconds`）
- [ ] WP-B 入口接线（`should_stop` 注入、`main()` 捕获、env 开关）
- [ ] WP-C 定向用例（阻塞读 + 停机 / 未停机反证 / 子进程 SIGTERM）
- [ ] WP-D 修复前反证实测（干净工作树跑同一脚本，记录数字）
- [ ] WP-E Linux 容器复验 + runbook 文档
- [ ] WP-F 全量门禁 + 记录

## 证据

（实施中逐项填写）

## 状态历史

- 2026-09-16 创建（IN_PROGRESS）：cycle 4（EC-03 ops 调度写面）闭环后按 EC 表顺序取 EC-04。
  derive 时的关键判断：**上界必须来自"停机后的宽限期"，不能来自"给所有调用更短的超时"**——
  否则正常路径会被无谓地打断；证据必须包含反证（未停机时仍等满客户端超时）。
  另据 recon：`services/worker/loop.py` 已 445 行（硬上限 450），本轮**不改它**，
  收口点放在客户端；真实 SIGTERM 只能在 Linux 上验（Windows 的 terminate 是
  TerminateProcess，见 RECHECK-051 F-1）。

## 影响报告

（收口时填写）

## 已知风险

- **放弃在途请求的语义**：被放弃的 `submit_result`/`upload_bundle` 可能"服务端已收、
  worker 以为没发"。这是 at-least-once 允许的（幂等键 + 租约恢复），但必须写进 runbook，
  不能让读者以为"放弃 = 一定没发生"。
- **线程计数**：每个出站调用多一个短命守护线程；worker 的调用频率低（心跳 10s 级），
  但要确认不影响既有的并发/线程断言。
- **Windows 侧**：子进程用例在 Windows 上跳过，Linux 证据由容器与 CI 提供——
  本地 win32 只能证明"未停机语义不变"这一半。
