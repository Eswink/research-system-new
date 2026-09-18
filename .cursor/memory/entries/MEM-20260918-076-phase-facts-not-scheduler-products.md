---
id: MEM-20260918-076
title: "并发用例的前提要用相位事实（尝试计数 + 同一 barrier 的到达序号），不要用'谁赢'这种调度产物"
status: ACTIVE
created_at: 2026-09-18
updated_at: 2026-09-18
scope: repository
confidence: 0.9
review_after: 2027-09-18
source_plans:
  - .cursor/plans/tasks/PLAN-20260918-103-clock-assertion-and-wall-clock-matrix.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260918-103-clock-assertion-and-wall-clock-matrix.md
supersedes: []
tags:
  - test-determinism
  - concurrency
  - postgres
  - clock-discipline
  - governance
---

# 并发用例：判"前提成立"要用相位事实；判"等待有界"要用结构而非观测

## 做了什么

GOAL-006 cycle 4（EC-04）把并发用例的**前提判据**从调度产物换成相位事实：

- 旧形态（`tests/postgres/test_claim_concurrency_pg.py`）：
  `assert sum(1 for claimed in results.values() if claimed) >= 2`——"至少两个 worker 领到活"。
  `threading.Barrier` 只保证**同时开始**；24 条任务下**单线程合法地把全部排空**不是缺陷，
  所以这条断言读的是"谁先拿到 CPU"（实测：给其余 worker 0.5s 头程 ⇒ `assert 1 >= 2`）。
- 新形态：`_ClaimProbe` 记两件事实 —— ① `attempts`（该 worker 进过几次领循环，含最后一次
  空返回）；② `arrival_index`（**同一个** `overlap` barrier 上的到达序号，`Barrier(parties=N)`
  的 N 个到达者拿到互不相同的 `0…N-1`）。断言 = 所有 worker `attempts >= 1` 且序号集合
  `== {0…N-1}`；线程异常进 `failures` 断言（不再静默），`overlap.abort()` 防挂死。

**同一扰动**（`start` barrier 之后给 worker-0 之外 0.5s 头程）下的实跑对照：
把相位构造退化成"每 worker 一个 `Barrier(1)`"（= 旧形态）并放回旧断言 ⇒ **3/3 红**
（`assert 1 >= 2`）；保留强制重叠 + 新判据 ⇒ **3/3 绿**；去扰动 ⇒ 全文件 3 passed ×3。

真墙钟面（`tests/postgres/test_cross_process_real.py`）：模块 docstring 写**覆盖矩阵**
（用例 × 等待判据，判据词汇 = `NO_WAIT` / `BOUNDED_POLL(deadline=40s,interval=2s)`），
逐条给"覆盖的时序 / 证伪条件"，并明列**未覆盖**（跨进程时钟漂移、网络分区、>2 进程压测、
GPU/容器等待）；机器判据 `tests/postgres/test_wall_clock_coverage_matrix.py` 用 AST 把
矩阵与用例一一对应，并把"有界"钉成**结构事实**：任何 `time.sleep` 必须落在同时含
`time.monotonic()` 与 `deadline` 的函数里（模块级 sleep 也算无界）。

## 为什么这样做

- **判"谁赢"必然 flake**：调度决定谁先跑；把它写进断言，等于把 CI 的绿色押在调度器上。
  判"测试做过什么"（尝试、相位）则是可复核事实。
- **barrier 的到达序号是自证式的**：`wait()` 返回一个整数只说明它返回了；**同一 barrier 的
  互不相同的序号集合**才证明"N 个到达者同属一个释放点"。把 barrier 退化成每个 worker 一个
  `Barrier(1)` 会得到全 0 序号 ⇒ **判据自己会红**，不靠人去看代码。
- **等待要么有界、要么说明不可行**："未观测到失败"不是证据。把等待判据词汇化 + 与 AST 交叉
  核对（`interval` 必须是文件里某个 `time.sleep` 的数字、`deadline` 必须是某个 `timeout`
  默认值），矩阵就不可能写一个文件里不存在的口径。
- **诚实边界要机器可见**：未覆盖小节必须有内容（≥3 条），防止"全覆盖"这种收尾。

## 怎么做与复现

```bash
export RESEARCHOS_POSTGRES_DSN="postgresql://research_os:research_os_m14_test@localhost:15432/research_os"
uv run --frozen --no-sync python -B -m pytest tests/postgres -q          # 100 passed
# 反证 A（旧形态 + 扰动 ⇒ 3 红）/ B（新判据 + 同扰动 ⇒ 3 绿）
uv run --frozen --no-sync python -B scratch/ec04/run_a_perturbation.py
uv run --frozen --no-sync python -B scratch/ec04/run_b_new_judgement.py
# 矩阵判据的四种退化（删行 / 判据写 SLEEP(3s) / 模块级 sleep / 无守卫函数内 sleep）
uv run --frozen --no-sync python -B scratch/ec04/run_wp_b_counterproofs.py
```

## 适用边界（踩过的坑）

- **结构判据钉结构，不钉时间**：`time.sleep` 在带 `deadline` 守卫的函数里就算"有界"——
  守卫函数里写 `time.sleep(300)` 也能通过（实测）。它是"无界等待"的防线，不是时间正确性证明。
- **相位判据证明的是"测试的前提"**：它证明 N 个线程由同一 barrier 同时进入领任务，**不**证明
  数据库在同一瞬间看到两个并发事务。SKIP LOCKED 的真实竞态仍然是概率性的（这就是它的价值）。
- **扰动要放在 barrier 之后**：头程 sleep 若放在 `start` barrier 之前，会被 barrier 抵消，
  反证会"假绿"（我第一次就这么写错过）。反证跑一次不够，要确认红的是**预期的那个断言**。
- **`Barrier(1)` 不是"更宽松的 barrier"**：它让 `wait()` 立即返回 ⇒ 到达序号全 0 ⇒ 前提瓦解。
  这正是判据要识破的形态；写"退化版"反证时用它。
- 相关：[[MEM-20260918-070]]（时钟注入纪律）、[[MEM-20260918-073]]（组合读一次语句=一个快照）、
  [[MEM-20260918-075]]（页面消费读面的两渠道判据）。

## 来源

- PLAN-20260918-103 / RECHECK-20260918-103（GOAL-20260918-006 cycle 4 = EC-04）。
- 上游：RECHECK-20260918-096 W-1 / W-4（时钟断言的调度依赖、真墙钟覆盖口径）。
