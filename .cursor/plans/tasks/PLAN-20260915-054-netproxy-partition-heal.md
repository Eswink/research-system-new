---
id: PLAN-20260915-054
slug: netproxy-partition-heal
title: 分区注入器真实性修复：restore() 必须真的恢复（D 场景 teardown 超时根因）
status: DONE
created_at: 2026-09-15
updated_at: 2026-09-15
parent_goal: GOAL-20260915-002
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-002 cycle 1（CI 债轮）：cycle 13 收口提交 8d18c5e 的 CI run 34957121713 上 collector-quality 失败（test_scenario_d_network_partition_no_old_authority teardown TimeoutExpired 10s），而该提交只改 .cursor 记录 —— 属既有的间歇性门禁缺陷。用户 2026-09-15 授权「继续循环迭代 10-20 次让系统更完整」，修门禁债属 GOAL-002 EC-06「每 cycle 本地 m0 与 main 的 CI 全绿」的前置。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-054-netproxy-partition-heal.md
memory_entries:
  - MEM-20260915-031-partition-injector-must-heal
---

# PLAN-20260915-054 — 分区注入器真实性修复（GOAL-002 cycle 1）

## 目标

让 `tests/distributed/net_proxy.py` 的故障注入**忠实于它声称模拟的故障**：网络分区是
「包不流动」，不是「字节被丢弃」。修复后 `restore()` 真正恢复——分区期间已发出、仍留在
socket 缓冲里的字节在分区解除后照常送达，请求得以完成。

## 背景（CI 证据 → 根因）

cycle 13 收口提交 `8d18c5e`（**只改 `.cursor/plans/**` 记录**）的 CI run `34957121713`：

```
FAILED tests/distributed/test_scenarios.py::test_scenario_d_network_partition_no_old_authority
       - subprocess.TimeoutExpired: Command '[... -m services.worker --worker-id d-partitioned]'
         timed out after 10 seconds
1 failed, 93 passed, 4 skipped
```

该测试第 222~223 行是 teardown：`proxy.restore(); partitioned.terminate(); partitioned.wait(timeout=10)`。
worker 收到 SIGTERM 后**必须在 10s 内退出**。根因链：

1. D 场景先 `proxy.blackhole()` 制造分区；worker（25s 长作业）在分区窗口内可能已经跑完
   进入心跳/认领/提交循环 → 期间的 HTTP 请求命中注入器的 `_stall`。
2. 旧 `_stall` 用 `client.recv()` **消费并丢弃**客户端字节，随后 `_pipe` 直接 `return`
   （连接线程结束）。于是：分区解除后，那次请求的字节已经没了，连接也不会再泵 →
   调用方只能等自己的 HTTP 超时（worker client `request_timeout_seconds=30.0`）。
3. SIGTERM 的 Python handler 只能置标志：主线程阻塞在 socket 读里，PEP 475 会自动重启
   该系统调用 → 30s 内进程不退出 ⇒ `wait(timeout=10)` 超时。
4. 是否命中取决于「测试前面的步骤是否慢到让 worker 越过 25s 执行窗口」——所以同一测试
   在 run 34939068977 / 34952933291 绿、在本轮红：**间歇但不是随机抖动**，是一次语义缺陷。

## 诚实边界

- 修的是**故障注入器**（测试基础设施），不是产品行为：控制面/worker 的生产语义未改。
- **产品侧特性如实登记**（见 RECHECK 的 W）：worker 的 SIGTERM 不能打断阻塞中的 HTTP 读，
  退出的上界是客户端请求超时（默认 30s）。这在生产上可接受（编排器的 grace 过后 SIGKILL，
  租约由控制面回收），但**不是**本轮修复目标，登记给 GOAL-002 后续 EC 决策。
- 不调整任何超时/断言：`wait(timeout=10)`、25s 延迟、断言全部原样。

## 范围

- `tests/distributed/net_proxy.py`：`_pipe` 在 `_stall` 返回后回到泵循环（不再 `return`）；
  `_stall` 改为分区期间**只在恢复/停止/对端关闭时返回**，且用 `MSG_PEEK` 观测而非消费。
- 新增 `tests/distributed/test_net_proxy_partition.py`：三条 loopback 用例锁住语义
  （分区期间字节不流动 → 恢复后送达；新连接同语义；分区期间客户端断开不滞留）。
- 反证脚本（scratch，gitignored）：用子类复刻旧 `_stall` 语义跑同一场景，必须失败。

## 验收条件

- [x] AC-01：新用例在修复后通过，在旧语义下失败（反证 `legacy: SWALLOWED` / `fixed: ECHOED`）。
- [x] AC-02：Linux 容器内 `tests/distributed` 全量 = 25 passed / 4 skipped / 0 failed。
- [x] AC-03：Linux 容器内 D 场景连跑 5 次全绿（teardown 10s 内退出）。
- [x] AC-04：本地 m0 23/23（Windows 侧回归面）与 CI 复验（收口提交后的 run）。

## 实施清单

- [x] WP-A 注入器语义修复 + 新测试 + 反证脚本
- [x] WP-B Linux 复现（D 场景 ×5 + distributed 全量）
- [x] WP-C 本地 m0 + RECHECK-054 + GOAL-002 记账

## 证据

| WP | 证据 | 结果 |
| --- | --- | --- |
| WP-A | `pytest tests/distributed/test_net_proxy_partition.py` 3 passed；反证 `python scratch/falsify_net_proxy.py` → `legacy: SWALLOWED` / `fixed: ECHOED` | PASS |
| WP-B | Linux（`python:3.12-slim`，`--network host`，uv frozen）：D 场景 ×5 = 5/5 passed；`tests/distributed` 全量 = **25 passed / 4 skipped / 0 failed** | PASS |
| WP-C | 本地 m0 23/23；RECHECK-054 = PASS_WITH_WARNINGS | PASS |

## 已知风险

- 注入器停止吞字节后，分区期间的字节会积存在内核缓冲：测试里都是几十~几百字节的小请求，
  不会触发背压（若将来有用例在分区期间发大流量，需要显式限流）。
- 控制面侧「worker 退出上界 = 请求超时」的性质未变（W-1），D 场景因此仍依赖
  `restore()` 先于 `terminate()`——这是测试自己的顺序，不是产品保证。

## 状态历史

- 2026-09-15 创建（IN_PROGRESS）：GOAL-20260915-002 cycle 1，起因 = cycle 13 收口提交的 CI 红。
- 2026-09-15 WP-A 完成：`_stall` 改 MSG_PEEK + 恢复后回泵；新增 3 条 loopback 语义用例；
  反证脚本实测旧语义 `SWALLOWED`、修复后 `ECHOED`。
- 2026-09-15 WP-B 完成：Linux 容器内 D 场景 5/5、distributed 全量 25 passed / 0 failed。
- 2026-09-15 WP-C 完成：本地 m0 23/23；RECHECK-054 = PASS_WITH_WARNINGS ⇒ 本计划 DONE。

## 影响报告

- 改动：`tests/distributed/net_proxy.py`（`_pipe`/`_stall` 语义）、新增
  `tests/distributed/test_net_proxy_partition.py`。**产品代码零改动**。
- lint/typecheck/test：新增用例 3 passed；Linux distributed 全量 25 passed / 4 skipped；
  本地 m0 23/23。
- Domain/API/schema 变化：无。
- 安全/凭据变化：无。
- 兼容性/迁移风险：无（测试基础设施；其它使用 NetProxy 的用例在 Linux 全量中一并通过）。
- 上游版本影响：无。
- 下一项任务：GOAL-20260915-002 cycle 2 = EC-01（G9 全局跨 run 血缘）。
