---
id: RECHECK-20260915-056
plan_id: PLAN-20260915-056
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-15
completed_at: 2026-09-15
reviewer: root-agent-goal-002-cycle2
baseline_ref: e6f09cb
checked_head: e6f09cb+worktree
---

# RECHECK-20260915-056 — blackhole() 返回时分区必须已生效（GOAL-002 cycle 2）

## 检查范围

PLAN-20260915-056 声称的交付面：`tests/distributed/net_proxy.py` 的 `blackhole()` 语义
（返回时分区生效）与由此带来的计数记账，以及"不破坏既有分区语义"的证据。
产品代码、其它 EC 不在范围内。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 修复前确有该失败（不是凭空记录） | m0 第 3 次全量运行日志 `scratch/m0-goal002-cycle2-run3.log`：`test_restore_delivers_bytes_sent_during_partition` 断言 `_recv_within(client, 0.5) is None` 得到 `b'hello-during-partition'` | PASS |
| `blackhole()` 返回时分区已生效 | 读实现：置标志后轮询 `stalled_connections >= live_connections`（`_lock` 保护，2s 上界）；`_stall` 用 `try/finally` 归还计数 | PASS |
| 定向用例不再间歇 | `tests/distributed/test_net_proxy_partition.py` 连跑 **8/8**（每轮 `3 passed`）；同文件在全量 m0 内亦绿 | PASS |
| 既有分区语义未被削弱 | `tests/distributed` 全量 **32 passed**（含 `test_scenario_d_network_partition_no_old_authority`）；PLAN-054 的"字节被保留、恢复后送达"用例仍绿 | PASS |
| 计数器不泄漏（连接结束后归还） | `_pipe` 的 `finally` 归还 `live_connections`；`_stall` 的 `finally` 归还 `stalled_connections`；上游不可达用例 `test_closed_client_does_not_strand_the_stall` 通过 | PASS |
| 本地门禁 | m0 = `profile=m0; 23 deterministic checks`（`3411 passed, 6 skipped`） | PASS |

## 结论

result: **PASS_WITH_WARNINGS**

注入器的第二条失真已闭环：`restore()` 必须真的恢复（PLAN-054）、`blackhole()` 必须真的
生效（本计划）。两条合起来才使"网络分区"这一故障在同 cycle 内可被判据化断言。
修复只动测试基础设施，产品语义不变。

## 告警

- W-1（有界等待）：`blackhole()` 现在最多阻塞 2s。正常路径 ≤ ~0.4s（泵的 0.2s recv 超时
  后才会看到标志）；若将来有连接长期卡在 `sendall`（对端不读），调用方会等到上界后返回
  ——此时分区仍会生效，只是"返回即生效"的保证退化为"上界内生效"。
- W-2（覆盖范围）：计数只覆盖**已建立**的泵线程；`blackhole()` 返回后新建的连接由泵顶部
  检查标志（已由既有用例锁定），不属竞态。
- W-3（继承）：RECHECK-054 W-1（worker SIGTERM 打不断阻塞中的 HTTP 读）仍未处理。

## 复现

```
python -m pytest tests/distributed/test_net_proxy_partition.py -q      # 3 passed（连跑 8 次）
python -m pytest tests/distributed -q                                  # 32 passed
sh scratch/run-m0-cycle12.sh                                           # profile=m0; 23 deterministic checks
```
