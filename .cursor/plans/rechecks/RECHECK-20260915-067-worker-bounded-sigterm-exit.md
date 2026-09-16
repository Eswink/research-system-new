---
id: RECHECK-20260915-067
plan_id: PLAN-20260915-067
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-16
completed_at: 2026-09-16
reviewer: root-agent-goal-003-cycle5
baseline_ref: dca1f94
checked_head: dca1f94+worktree
---

# RECHECK-20260915-067 — worker SIGTERM 有界退出（GOAL-003 cycle 5 / EC-04）

## 检查范围

PLAN-20260915-067 声称的交付面：`adapters/worker/client.py` 的单一收口点
`_call` + `WorkerDrainAbort` + `WorkerClientConfig.drain_seconds`、
`services/worker/__main__.py` 的 `should_stop` 注入 / `WorkerDrainAbort` 捕获 /
`RESEARCHOS_WORKER_DRAIN_SECONDS` 开关、`tests/worker/test_worker_drain_bound.py`
（5 进程内 + 2 真实信号）、`docs/operations/OPERATIONS_RUNBOOK.md` 的停机段、
以及 `scratch/` 里的两个测量脚本（修复前/后对照与 Linux 容器复验）。

**未覆盖**（如实登记，见告警）：worker 侧的其他停机路径（在途**执行**的中断沿用既有
协作式 cancel 通道，本轮未动）、服务端 drain 语义、`tests/distributed` 场景在
win32 本机无法复现（需 PG）。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 出站调用有单一收口点（AC-01） | `grep -c "self._http\." adapters/worker/client.py` 只剩 `_call` 内部与 `close()`；8 个方法全部经 `_call(lambda: self._http.X(...))` | PASS |
| 停机后放弃在途调用（AC-01） | `test_blocked_read_is_abandoned_after_the_drain_window`：1.5s 阻塞读 + 0.1s 后置停机标志 + drain=0.3 ⇒ 抛 `WorkerDrainAbort`，耗时 < 1.5s，且 `transport.calls == 1`（请求确实发出，被放弃的是等待） | PASS |
| **未停机时语义不变**（AC-02，反证） | `test_no_shutdown_never_shortens_a_blocked_read`：drain=0.1 但从不置标志 ⇒ 1.5s 阻塞读**照常跑完**（断言 `elapsed >= 1.5`）；`test_client_without_should_stop_keeps_the_direct_semantics`：不注入 `should_stop` ⇒ 直接调用语义 | PASS |
| deadline 只 armed 一次 | `test_second_call_after_the_deadline_aborts_without_waiting`：停机后新调用 <1s 内放弃（不各等一个宽限期） | PASS |
| 真实 SIGTERM 有界退出（AC-03） | `test_sigterm_exits_within_the_drain_window_while_blocked_in_a_read`：黑洞网关（accept 后永不回包）+ 真子进程 + `SIGTERM`，drain=1 ⇒ 退出码 0、耗时 < 5s | PASS |
| 上界来自**配置**而不是写死的常数 | `test_drain_window_governs_the_bound_not_a_fixed_cap`：drain=30 时进程在 6s 后**仍在运行**（若实现里塞了固定短上界，这条会失败） | PASS |
| **修复前反证的数字**（AC-04） | `scratch/measure-worker-sigterm-exit.py` 同一脚本、同一参数、同一容器镜像，对两个工作树各跑一次：修复前（HEAD `dca1f94`）**29.64s**、修复后**1.12s**，退出码都是 0 | PASS |
| Linux 复验（AC-05） | `python:3.12-slim` 容器内跑整份用例：**6 passed**（含两条真实信号用例）；win32 上这两条 skip（`Popen.terminate()` 是 TerminateProcess） | PASS |
| env 开关的默认值与取值域（AC-06） | `test_drain_seconds_env_knob_has_a_default_and_a_range`：缺省 5.0、`"2.5"` ⇒ 2.5、`"0"` ⇒ ValueError("within")、`"soon"` ⇒ ValueError("must be a number")；runbook 写明默认与范围 | PASS |
| 全量门禁（AC-07） | `tests/worker` **33 passed / 2 skipped**；`tests/architecture+worker+contracts` **453 passed / 58 skipped**；m0 **PASS: profile=m0; 23 deterministic checks**（首轮红于 `python/product-lint`：两处 skipif 行 101 > 100 字符 ⇒ 收敛成一个模块级 marker，**未放宽任何断言**；第二轮撞上已知 Windows 文件占用 flake） | PASS |
| 安全扫描（sealed） | Mimosa deep scan `scan-2026-09-16T12-00-41.425Z-870fb6a2d27f`，seal `sha256:cbd2ba950115c60d76fa2a95722340864358e4b289ece1a049dc749cb17cfe02`：**36 findings（3 high / 28 medium / 5 low），182 packages**，计数与上一轮（cycle 4）完全一致。唯一落在本 cycle 改动文件上的命中是 `services/worker/__main__.py:135` 的 **advisory**（`疑似跨文件污点`：`RESEARCHOS_WORKER_GPU_IMAGE` 环境变量 → `probe_gpu(image=...)`）——**上一轮同一条**（当时报在第 107 行），本轮只是文件加了 28 行导致行号平移；`advisory: true` / `verdictEffect: none`。本轮新增的 `_drain_seconds` 解析带取值域校验，未引入新类别 | PASS |
| 记录（AC-07） | RECHECK-067 + MEM-20260915-042 + GOAL-003 的 EC 表/迭代日志/状态历史 + ALL_PLAN | PASS |

## 告警

- **W-1（范围）**：本轮只覆盖**网关读**的停机上界。在途**执行**的中断仍走既有协作式
  cancel 通道（`CancelProbe`），其"多久必须停"没有新增上界——一个不响应 cancel 的
  执行后端仍会让停机等到它自己结束。这不是本轮口径（EC-04 说的是"阻塞中的 HTTP 读"），
  但读者不应把它读成"worker 停机已完全有界"。
- **W-2（模糊性）**：放弃在途调用 ⇒ 被放弃的 `submit_result` / `upload_bundle`
  **可能已经到达服务端**。语义上 at-least-once + 幂等键 + 租约恢复能覆盖，但在
  "提交结果"这一具体动作上，worker 与 CP 的认知可能不一致（worker 以为没发）。
  runbook 已把这点写成明确口径（不得读成"一定没发生"）。
- **W-3（平台）**：真实信号的两条用例在 win32 上 skip，因此**本机**无法复验；
  本轮给出的 Linux 证据是容器里的一次实跑（6 passed）与 CI 的 quality-ubuntu-latest。
  这是 RECHECK-051 F-1 记录过的同一限制，不是新缺口。
- **W-4（线程模型）**：`_call` 在注入 `should_stop` 时每个出站请求起一个短命守护线程。
  worker 的调用频率低（心跳 10s 级、claim 轮询秒级），但这条改变了调用栈形状
  （异常 traceback 会跨线程）。既有用例全绿，未发现线程计数断言受影响。
- **W-5（未注入即无上界）**：`WorkerClient(config)`（不传 `should_stop`）**没有**停机上界——
  这是刻意的（测试与一次性脚本保持原语义），但意味着任何绕过 `__main__` 的用法
  需要自己注入 `should_stop` 才能得到 EC-04 的保证。

## 结论

result: **PASS_WITH_WARNINGS**

EC-04 的目标达成且**有对照数字**：同一条"连上了但读不到数据"的网关、同一个子进程、
同一份参数，修复前 29.64s（=客户端超时）退出、修复后 1.12s（=drain 宽限期 + ε）退出，
两次退出码都是 0（有序停机）。反证有两层：进程内（未停机 ⇒ 不缩短）与进程外
（把 drain 调大 ⇒ 进程不早退），因此"上界来自停机窗口而非写死的常数"是被证伪式覆盖的。

W-1~W-5 都是范围/语义登记：本轮把"网关读"这一条上界做掉了，没有宣称 worker 停机
在所有维度上都有界。
