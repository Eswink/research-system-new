---
id: PLAN-20260915-056
slug: blackhole-must-be-effective-on-return
title: 分区注入器的第二个失真：blackhole() 返回时分区必须已经生效
status: DONE
created_at: 2026-09-15
updated_at: 2026-09-15
parent_goal: GOAL-20260915-002
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-002 cycle 2 的门禁轮（与 EC-01 同 cycle）：本地 m0 第 3 次全量运行在 Windows 上暴露 `tests/distributed/test_net_proxy_partition.py::test_restore_delivers_bytes_sent_during_partition` 失败（分区刚设就收到回显）。修门禁确定性属 EC-06「每 cycle 本地 m0 与 main 的 CI 全绿」的前置；授权口径同 GOAL-20260915-002。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-056-blackhole-must-be-effective-on-return.md
memory_entries:
  - MEM-20260915-031-partition-injector-must-heal
---

# PLAN-20260915-056 — blackhole() 返回时分区必须已生效（GOAL-002 cycle 2 门禁轮）

## 目标

让 `NetProxy.blackhole()` 的语义与它的名字一致：**返回时分区已经生效**（每条活连接的泵
线程都已进入 stall），而不是"标志已置、稍后某个时刻才生效"。

## 背景（本地 m0 第 3 次全量运行的失败）

```
FAILED tests/distributed/test_net_proxy_partition.py::test_restore_delivers_bytes_sent_during_partition
E  AssertionError: assert b'hello-during-partition' is None
   （分区刚 blackhole() 完，客户端发出的字节就被转发并回显了）
```

根因：泵循环**只在每一轮的顶部**检查 `_blackholed`。当客户端连接先建立、泵已经阻塞在
`client.recv()` 里时，随后调用的 `blackhole()` 只是置标志；下一次 `recv` 收到的正是测试
刚发出的字节，于是被正常转发 ⇒ 分区"稍后"才生效。该用例断言的是"分区期间字节不流动"的
**立即性质**，因此命中与否取决于当时的调度时序（cycle 1 在 Linux 上 5/5 绿，本轮 Windows
全量在负载下复现）。

第二轮同类失真：`restore()` 必须真的恢复（已由 PLAN-20260915-054 修复），
`blackhole()` 必须真的生效（本计划）——两者都属"注入器必须忠实于它声称的故障"。

## 范围

- `tests/distributed/net_proxy.py`：`blackhole(timeout=2.0)` 置标志后等待
  `stalled_connections >= live_connections`（有界等待）；`_pipe`/`_stall` 维护两个计数
  （锁保护，`_stall` 用 `try/finally` 保证退出时归还）。
- 不改任何断言/超时；不改产品代码。

## 验收条件

- [x] AC-01：修复后 `tests/distributed/test_net_proxy_partition.py` 连跑 8 次全绿（此前在
      全量负载下可复现失败）。
- [x] AC-02：`tests/distributed` 全量（含 D 场景等使用注入器的用例）本地通过，证明
      `blackhole()` 变为有界阻塞后没有破坏既有场景。
- [x] AC-03：本地 m0 = `profile=m0; 23 deterministic checks`。
- [x] AC-04：不改变"分区期间字节被保留、恢复后送达"的语义（PLAN-054 的用例仍绿）。

## 实施清单

- [x] WP-A 计数 + 有界等待 + 文档化契约
- [x] WP-B 定向重复运行 + distributed 全量 + m0 全量
- [x] WP-C RECHECK-056 + GOAL-002 记账（与 PLAN-055 同 cycle）

## 证据

| WP | 证据 | 结果 |
| --- | --- | --- |
| WP-A | `blackhole(timeout: float = 2.0)`：置标志后轮询 `stalled_connections >= live_connections`；`_pipe` 进入时 `live_connections += 1`（`finally` 归还），`_stall` 进入时 `stalled_connections += 1`（`try/finally` 归还） | PASS |
| WP-B | `for i in 1..8: pytest tests/distributed/test_net_proxy_partition.py -q` → 8/8 `3 passed` | PASS |
| WP-B | `pytest tests/distributed -q` → **32 passed**（0 failed；含 scenario D） | PASS |
| WP-B | 本地 m0 = `profile=m0; 23 deterministic checks`（`3411 passed, 6 skipped`） | PASS |
| WP-C | RECHECK-056 = PASS_WITH_WARNINGS | PASS |

## 已知风险

- `blackhole()` 现在最多阻塞 `timeout`（默认 2s）：连接泵在 `recv` 超时（0.2s）后才会
  看到标志，正常路径的额外等待 ≤ ~0.4s；上游不可达时 `_pipe` 直接结束、计数归还，
  调用立即返回。
- 计数只覆盖"泵线程存活"的连接：`blackhole()` 返回后**新建立**的连接仍由泵顶部检查
  （已由 `test_partition_holds_new_connections_until_restore` 锁定）。

## 状态历史

- 2026-09-15 创建（IN_PROGRESS）：GOAL-20260915-002 cycle 2 门禁轮，m0 第 3 次全量运行在
  Windows 上暴露分区即时性竞态。
- 2026-09-15 WP-A/WP-B 完成：计数 + 有界等待；定向用例 8/8、distributed 全量 32 passed、
  本地 m0 23/23。
- 2026-09-15 WP-C 完成：RECHECK-056 = PASS_WITH_WARNINGS ⇒ 本计划 DONE。

## 影响报告

- 改动：`tests/distributed/net_proxy.py`（`blackhole` 契约 + 两个连接计数）。**产品代码零改动**。
- lint/typecheck/test：定向用例 8/8；`tests/distributed` 32 passed；本地 m0 23/23。
- Domain/API/schema 变化：无。
- 安全/凭据变化：无。
- 兼容性/迁移风险：无（唯一调用方是测试与 scratch 反证脚本，均无参调用）。
- 上游版本影响：无。
- 下一项任务：GOAL-20260915-002 cycle 3 = EC-02（G12 跨 run 时序成本预测）。
