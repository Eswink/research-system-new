---
id: MEM-20260915-027
title: collector-quality 的两项失败是持续失败（非 flake）；口径纠正与根因
status: ACTIVE
created_at: 2026-09-15
updated_at: 2026-09-15
scope: repository
confidence: 0.9
review_after: 2026-12-15
source_plans:
  - .cursor/plans/tasks/PLAN-20260914-050-ec05-ec06-closeout.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-050-ec05-ec06-closeout.md
supersedes: []
tags:
  - ci
  - flake-vs-persistent
  - worker-shutdown
  - otel
  - evidence-discipline
---

# MEM-20260915-027 — "flake" 一词必须用跨 run 取证支撑

## 做了什么

GOAL-20260912-001 末轮（cycle 10，PLAN-050）对 `collector-quality` 做了跨 8 次
run（#61–#68）的取证：**该 job 每一次都失败，且失败测试每次完全相同**——
`tests/observability/test_collector_evidence.py::test_collector_persists_research_os_spans`
与 `tests/distributed/test_scenarios.py::test_scenario_d_network_partition_no_old_authority`
（每次 2 failed / 85 passed）。此前 RECHECK-042…049 把它记作 "timing flake"，
口径不准确：**这是持续失败，只是本地平台掩盖了它**。

## 事实一：D 场景的超时根因（已定位）

`test_scenario_d_network_partition_no_old_authority` 的失败发生在**断言之后的
teardown**：`partitioned.wait(timeout=10)`。该 worker 以
`RESEARCHOS_WORKER_EXECUTE_DELAY_SECONDS=25` 跑确定性后端，`services/worker/__main__.py`
的 SIGTERM 处理器**只置 drain 标志**（`_STOP["flag"]=True`），循环只在迭代之间检查 →
25s 在途执行无法在 10s 内退出 → `subprocess.TimeoutExpired`。
Windows 本地 `Popen.terminate()` = `TerminateProcess`（立即），Linux CI = SIGTERM
（协作式）——**这是"本地永远绿、CI 永远红"的机制**，不是抖动。

## 事实二：collector 证据链的另一项

`test_collector_persists_research_os_spans`：collector 可达（否则模块级 fixture 会以
"not reachable" 失败，且 `RESEARCHOS_REQUIRE_COLLECTOR=1` 下是 fail 而非 skip），
但 file exporter 在 45s 轮询窗口内没有把唯一 marker span 落盘到
`data/otel/research_os_signals.json`。根因未在本轮定位（需 collector 侧诊断）。

## 为什么这样做

把持续失败写成 flake 会让"每 cycle GHA 全绿"这条退出标准看起来接近达成（"只是抖"），
而实际是**结构性未达成**。GOAL 的 fix_policy 明确禁止"伪造或夸大验证证据"，因此
口径本身也是证据的一部分：判 flake 必须给出跨 run 的"有时成功"证据，否则应写
"持续失败 + 根因/未定位"。

## 怎么做与复现

- 取证命令（不打印 token）：
  `TOKEN=$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill | sed -n 's/^password=//p')`
  然后 `curl -s -H "Authorization: Bearer $TOKEN" ".../actions/runs/<id>/jobs"`（逐 run 看
  job conclusion）与 `.../actions/jobs/<job-id>/logs`（看 FAILED 行）。
- 本地复现 D 场景：`pytest -q tests/distributed/test_scenarios.py`（Windows 通过；
  在 Linux 容器/CI 里同样的 teardown 会超时）。
- 本地 m0 的负载敏感同类：`test_scenario_g_drain_stops_claims` 是 check-then-act
  竞态（`registry.get` 后假设仍为 REGISTERING），隔离复跑必过、满负载偶发。
  判读口径：**"isolated pass + full-gate fail"** 与 **"CI 每次都失败且失败集合恒定"**
  是两类不同事实，前者可记 flake，后者必须记持续失败。

## 适用边界

适用于本仓所有"CI 红但本地绿"的判读；不改变任何断言或超时（fix_policy 禁止）。
修复这两项需要动 worker 关闭语义（产品行为）或 OTel 证据链（基础设施）或 workflow
验收口径（治理面）——三者都超出自动循环的授权，属人工决策点。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260914-050-ec05-ec06-closeout.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260915-050-ec05-ec06-closeout.md`（F-1）
- 代码：`services/worker/__main__.py`（drain 处理器）、`tests/distributed/worker_harness.py`
  （`stop_workers` 的 10s 兜底）、`.github/workflows/m0-quality.yml`（job 定义，只读）
- 相关：MEM-20260913-021（CI 守卫与 linux-only 检查器）、MEM-20260915-026
