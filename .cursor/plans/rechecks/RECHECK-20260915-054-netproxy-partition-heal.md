---
id: RECHECK-20260915-054
plan_id: PLAN-20260915-054
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-15
completed_at: 2026-09-15
reviewer: root-agent-goal-002-cycle1
baseline_ref: 8d18c5e
checked_head: 8d18c5e+worktree
---

# RECHECK-20260915-054 — 分区注入器真实性修复（GOAL-002 cycle 1）

## 检查范围

PLAN-20260915-054 声称的交付面：`tests/distributed/net_proxy.py` 的分区语义
（`restore()` 真正恢复、字节不被吞）、新增 `tests/distributed/test_net_proxy_partition.py`、
以及在 Linux 上的复现证据。**产品代码不在范围内**（本轮零改动）。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 分区期间字节不被吞、恢复后送达 | `tests/distributed/test_net_proxy_partition.py::test_restore_delivers_bytes_sent_during_partition` 通过 | PASS |
| 分区语义对新连接同样成立 | 同文件 `test_partition_holds_new_connections_until_restore` 通过 | PASS |
| 分区期间客户端断开不滞留连接线程 | 同文件 `test_closed_client_does_not_strand_the_stall` 通过 | PASS |
| **反证**：旧语义下同一场景必须失败 | `python scratch/falsify_net_proxy.py`（子类复刻旧 `_stall`：recv 消费 + return）→ `legacy: SWALLOWED` / `fixed: ECHOED`；反证窗口与用例同口径（0.5s，短于上游 5s 读超时），排除"测到上游 EOF"的假象 | PASS |
| Linux 上 D 场景不再超时（teardown 10s 内退出） | Linux 容器（`python:3.12-slim`，`--network host`，`UV_PROJECT_ENVIRONMENT=/tmp/venv`，真实 host postgres）D 场景连跑 **5/5 passed** | PASS |
| 回归面（其它用 NetProxy 的用例） | Linux 容器 `tests/distributed` 全量 = **25 passed / 4 skipped / 0 failed**（4 skip 为 GPU 类） | PASS |
| Windows 侧无回归 | 本地 m0 = `profile=m0; 23 deterministic checks` | PASS |
| CI 复验（修复提交） | run **34960364156**（e6f09cb）：**六个 job 全 success**（quality-ubuntu-latest / quality-windows-latest / console-frontend / container-quality / eval-gate / collector-quality）；对照修复前 run 34957121713 的 collector-quality 失败（同一测试） | PASS |

## 结论

result: **PASS_WITH_WARNINGS**

根因链完整可复现：旧 `_stall` **消费并丢弃**分区期间的字节且连接线程直接结束，`restore()`
无法恢复该连接 ⇒ 调用方只能等自己的 HTTP 超时（worker client 30s），而 SIGTERM 的 handler
只能置标志（主线程阻塞在 socket 读，PEP 475 重启该系统调用）⇒ `partitioned.wait(timeout=10)`
超时。修复后分区期间字节留在内核缓冲、`restore()` 后回到泵循环送达。测试基础设施，非产品语义。

## 告警

- W-1（产品侧性质，登记给 GOAL-002 后续决策）：**worker 的 SIGTERM 不能打断阻塞中的 HTTP 读**，
  退出上界 = 客户端请求超时（`WorkerClientConfig.request_timeout_seconds = 30.0`）。生产上可接受
  （编排器 grace 过后 SIGKILL，租约由控制面回收并由 reaper 转 LOST），但若将来要求"停机必须在
  N 秒内生效"，需要让关停路径能中断在途请求（本次未改，属行为变更需单独 PLAN）。
- W-2（测试顺序依赖）：D 场景仍要求 `proxy.restore()` 先于 `terminate()`；这是测试自身的顺序，
  不是产品保证。若把 terminate 放在 restore 之前，worker 仍会被卡住——那是 W-1 的直接后果。
- W-3（注入器背压）：不再消费字节后，分区期间客户端发送的数据会积存在内核缓冲；当前用例都是
  小请求，不触发背压。若将来有分区期间的大流量用例，需要显式限流或丢弃策略。
- W-4（工具链事故，已修复并留痕）：Linux 复现脚本原先未设 `UV_PROJECT_ENVIRONMENT`，
  容器内 `uv sync` 会把宿主的 Windows `.venv` 覆盖成 Linux 布局；本轮实际发生一次，
  已用 `uv sync --frozen --dev` 在宿主重建并验证（3 项新用例 + m0 全绿），
  脚本与本记录同时留痕（`scratch/linux-verify-*.sh` 已加 `UV_PROJECT_ENVIRONMENT` 与注释）。

## 复现

```
# 语义用例 + 反证
python -m pytest tests/distributed/test_net_proxy_partition.py -q
python scratch/falsify_net_proxy.py            # legacy: SWALLOWED / fixed: ECHOED
# Linux 复现（Windows 的 terminate() 是 TerminateProcess，无法复现）
MSYS_NO_PATHCONV=1 docker run --rm --network host \
  -v /d/research-system:/work -v /d/research-system/scratch:/scratch \
  -e SCENARIO_D_RUNS=5 -w /work python:3.12-slim bash /scratch/linux-verify-scenario-d-fix.sh
# 本地门
sh scratch/run-m0-cycle12.sh                   # profile=m0; 23 deterministic checks
```
