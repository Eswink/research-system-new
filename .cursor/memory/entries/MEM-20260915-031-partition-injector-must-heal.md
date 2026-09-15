---
id: MEM-20260915-031
title: 分区注入器必须"恢复即恢复"：吞字节的 stall 会把间歇缺陷伪装成超时
status: ACTIVE
created_at: 2026-09-15
updated_at: 2026-09-15
scope: repository
confidence: 0.90
review_after: 2027-09-15
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-054-netproxy-partition-heal.md
  - .cursor/plans/tasks/PLAN-20260915-056-blackhole-must-be-effective-on-return.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-054-netproxy-partition-heal.md
  - .cursor/plans/rechecks/RECHECK-20260915-056-blackhole-must-be-effective-on-return.md
supersedes: []
tags:
  - distributed
  - fault-injection
  - worker
---

# 分区注入器必须"恢复即恢复"

## 做了什么

把 `tests/distributed/net_proxy.py` 的 `_stall` 从「`recv()` 消费并丢弃字节 + 连接线程
直接结束」改成「`MSG_PEEK` 观测 + 分区解除后回到泵循环」；新增
`tests/distributed/test_net_proxy_partition.py` 三条 loopback 语义用例，并写了反证脚本。

## 为什么这样做

`test_scenario_d_network_partition_no_old_authority` 的 teardown
（`restore(); terminate(); wait(10)`）在 CI 上间歇失败，报
`subprocess.TimeoutExpired: [... --worker-id d-partitioned] timed out after 10 seconds`。
根因不是"负载抖动"：

1. 分区期间 worker 在心跳/认领/提交循环里发 HTTP 请求 → 命中注入器的 `_stall`；
2. 旧 `_stall` **消费**了这些字节又让连接线程 `return`，所以 `restore()` 之后那次请求
   永远不会有响应：调用方只能等自己的 HTTP 超时（worker client 默认 `request_timeout_seconds=30.0`）；
3. SIGTERM 的 Python handler 只置标志，主线程阻塞在 socket 读里（PEP 475 会重启该系统调用）
   ⇒ 进程 30s 内不退出 ⇒ 10s 的 `wait()` 超时。

也就是说：**注入器的失真把"连接永远不通"伪装成了"停机超时"**。是否命中取决于测试前面的
步骤是否慢到让 worker 越过 25s 执行窗口，所以同一用例在相邻 run 有绿有红。

## 怎么做与复现

```
python -m pytest tests/distributed/test_net_proxy_partition.py -q     # 3 passed
python scratch/falsify_net_proxy.py   # legacy: SWALLOWED / fixed: ECHOED（反证）
# Linux 复现（Windows 的 Popen.terminate() 是 TerminateProcess，无法复现）
MSYS_NO_PATHCONV=1 docker run --rm --network host \
  -v /d/research-system:/work -v /d/research-system/scratch:/scratch \
  -e SCENARIO_D_RUNS=5 -w /work python:3.12-slim bash /scratch/linux-verify-scenario-d-fix.sh
```

## 适用边界

- 修的是**注入器**：模拟"包不流动"就该保住字节；若模拟目标是"数据被丢弃"（重置连接），
  应该另写一个显式故障类型，不要混在分区里。
- **注入器的每个动作都必须在返回时已经生效**（PLAN-20260915-056 补上的另一半）：
  泵循环只在每轮顶部检查标志，所以连接已阻塞在 `recv` 时，`blackhole()` 置标志后
  下一批字节仍会被转发。`blackhole()` 现在等到 `stalled_connections >= live_connections`
  （有界 2s）才返回——否则"分区立即生效"的断言在负载下会偶发失败（本地 m0 第 3 次全量
  运行在 Windows 上复现过）。同类要求适用于任何新增的注入动作：**返回即生效**。
- 不消费字节后，分区期间的数据会积存在内核缓冲（当前用例都是小请求，不触发背压）。
- 产品侧性质（**未修**）：worker 的 SIGTERM 打不断阻塞中的 HTTP 读，退出上界 = 客户端请求
  超时 30s。要"停机 N 秒内生效"必须让关停路径能中断在途请求，属独立 PLAN。
- 容器内跑 `uv sync` 前必须设 `UV_PROJECT_ENVIRONMENT=/tmp/venv`，否则会把宿主的
  Windows `.venv` 覆盖成 Linux 布局（本轮实际发生一次，用 `uv sync --frozen --dev` 重建）。

## 来源

- PLAN-20260915-054 / RECHECK-20260915-054（GOAL-20260915-002 cycle 1），
  起因 = CI run 34957121713（head 8d18c5e，docs-only 提交）。
- PLAN-20260915-056 / RECHECK-20260915-056（GOAL-20260915-002 cycle 2 门禁轮），
  起因 = 本地 m0 第 3 次全量运行的 `test_restore_delivers_bytes_sent_during_partition` 失败。
- 相关：[[collector-quality-root-causes-and-fix]]（同一场景 teardown 的执行中断那一半已由
  `services/worker/cancellation.py` 修好；本次是 HTTP 阻塞那一半）。
