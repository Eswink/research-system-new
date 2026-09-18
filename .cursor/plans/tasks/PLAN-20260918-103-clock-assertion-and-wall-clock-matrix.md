---
id: PLAN-20260918-103
slug: clock-assertion-and-wall-clock-matrix
title: 时钟断言去调度依赖 + 真墙钟覆盖矩阵（EC-04）
status: DONE
created_at: 2026-09-18
updated_at: 2026-09-18
parent_goal: GOAL-20260918-006
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260918-006 cycle 4 = EC-04（GOAL-005 收口结论 / RECHECK-096 W-1 + W-4）。授权来源：2026-09-18 用户 goal 模式指令（新建承接 GOAL-006 并自动化循环推进、无需逐轮确认）。push-to-main-for-CI 授权沿用 GOAL-001…005 批准口径（只推 main、不 force、不重写历史、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260918-103-clock-assertion-and-wall-clock-matrix.md
memory_entries:
  - MEM-20260918-076
---

# PLAN-20260918-103 — 时钟断言去调度依赖 + 真墙钟覆盖矩阵（GOAL-006 cycle 4 = EC-04）

## 目标

EC-04 的两件事（RECHECK-096 W-1 / W-4）：

1. **去掉断言对调度时序的依赖**：`tests/postgres/test_claim_concurrency_pg.py` 里
   "并发是真的"那条断言（`sum(1 for claimed in results.values() if claimed) >= 2`）
   读的是**调度产物**（谁先抢到 CPU 谁就能把 24 条任务全排空）⇒ 换成可复核的
   **相位/计数事实**，且**不得删掉**它保护的前提（"这个测试真的在并发领任务"）。
2. **真墙钟覆盖矩阵**：`tests/postgres/test_cross_process_real.py` 给出一等口径
   （用例 × 覆盖的时序 × 等待有界判定方式），**不得以"未观测到失败"收尾**。

## 先探明再动手（只读勘察，逐条可复核）

1. **旧形态在哪**：`tests/postgres/test_claim_concurrency_pg.py`（168 行）
   `test_concurrent_schedulers_claim_disjoint_work` 末尾三条断言，最后一条是
   `# concurrency was real: at least two workers pulled work (not one draining all)`
   + `assert sum(1 for claimed in results.values() if claimed) >= 2`。
2. **为什么它依赖调度**：`_concurrent_drain` 用 `threading.Barrier(len(worker_ids))`
   把 4 个线程**同时释放**，每个线程随后 `_drain`（`claim_next` 直到 `None`）；
   24 条任务下**单线程可以全排空**——barrier 只保证"同时开始"，不保证"都有活干"。
   这是**真实存在的调度依赖**（RECHECK-096 W-1 的原话），不是理论风险。
3. **`_drain` 今天不记任何相位事实**（无尝试计数、无重叠计数）⇒ 要换成
   "进入领循环的线程计数/显式相位判据"必须先补计数。
4. **真墙钟面**：`test_cross_process_real.py`（207 行）三个用例，等待面分别是
   `_poll_reclaim`（deadline 40s、轮询 2s、判据 = lease id 变化）、
   `_poll_recover`（deadline 40s、轮询 2s、判据 = `n >= 1`）、
   `test_stale_fenced_after_expiry_window` 用**真实 `ttl = 5` 秒**（不注入时钟）；
   模块 docstring 已承诺 "bounded POLLS, not fixed `sleep(ttl+3)`"（PART B W-04），
   但**没有覆盖表**：哪些时序被覆盖、哪些没有、每个等待的判据是什么，只散在注释里。
5. **标记语义**：`pytest.mark.timing_sensitive`（`pyproject.toml` 注册）=
   "wall-clock 敏感；必须串行、不得与重负载并行"；m0 的 runner docstring 明确
   "这些用例在并发负载下可能 flake、不是产品回归"。矩阵要写清"哪条用例属这一档、
   为什么"（这正是"不得以未观测到失败收尾"要的东西）。
6. **跨进程真实面**：`tests/postgres/worker_cross_process.py` 每个 worker 是独立
   OS 进程 + 独立 psycopg 连接（无线程/asyncio/进程内双连接模拟），`acquire` /
   `recover` / `claim-complete` 动作都是真引擎调用。

## 口径

- **(a) 换断言，不删前提**：新判据必须是"这个测试**做了**什么"（相位/计数事实），
  不是"这个测试**跑赢**了什么"（谁领到了任务）。至少两条：① 每个 worker 都真的
  **进过领循环**（尝试计数 ≥ 1）；② 至少两个 worker 的**首次领任务在时间上重叠**
  —— 用测试侧的 `claim_next` 包装 + `threading.Barrier(2)` **强制**这个相位（不再
  靠碰运气），重叠由构造保证、断言可直接复核。
- **(b) 矩阵是"覆盖 + 判据"，不是清单**：每行 = 用例 × 覆盖的时序 × 等待有界判定
  方式（deadline + 轮询间隔 + 判据） × 什么会证伪它；并写明**没有覆盖**的时序
  （诚实边界），不得写成"全部覆盖"。
- **判据可判定**：新增一条读真实文件的判据用例（矩阵 ↔ 文件里的用例一一对应、
  每个等待都有 deadline 判据），并用反证证明它真会红。
- **零产品改动**：只动 `tests/postgres/**`（若需产品侧钩子才改，先评估是否越界；
  本 PLAN 预期不需要）。

## 验收条件

- **AC-01 去调度依赖（结构判据）**：`test_claim_concurrency_pg.py` 的断言不再读
  "谁领到了任务"；改后**仍有**"并发前提成立"的判据（尝试计数 + 强制重叠相位）；
  反证：把断言换回调度依赖形态 + 注入调度扰动 ⇒ 旧形态红、新形态绿（两次实跑记录）。
- **AC-02 扰动实跑**：注入"串行化扰动"（例如让除首个 worker 外的线程在进入领循环前
  先睡一会儿）⇒ 新判据**不红**（前提由构造保证），并记录旧断言在同一扰动下的表现
  （预期：可复现地红）。**不得**以"未观测到失败"代替。
- **AC-03 矩阵 + 判据**：覆盖表写进 `test_cross_process_real.py` 的模块 docstring
  （或同目录既有文档），并有**机器判据**：文件里的每个用例都在矩阵里、矩阵不列
  不存在的用例、每个等待有 deadline 判据；反证：删一行 / 加一条无 deadline 等待 ⇒ 红。
- **AC-04 门禁**：`tests/postgres` 定向（DSN pin，含 `timing_sensitive` 串行跑）+
  规模门禁 + `make validate-all` 全量 23 项 + CI 六 job 终态。

## 实施清单

### WP-A — 并发断言去调度依赖

- [x] `_ClaimProbe` 记尝试计数（含空返回）与到达序号；`_concurrent_drain` 返回
      `(results, probes, failures)`。
- [x] 测试侧 `claim_next` 包装（`_ClaimProbe.call`）+ 共享 `threading.Barrier(N)`：所有
      worker 的**首次**领任务由构造同时进入（重叠 = 相位事实，不依赖调度）；线程异常进
      `failures` 且 `overlap.abort()` 防挂死。
- [x] 断言：每个 worker 尝试 ≥ 1；到达序号集合 `== {0…N-1}`（同一 barrier）；原有的
      "无重复 / 全覆盖"不变量逐字保留；`>= 2` 这条调度代理**已删**。
- [x] **反证实跑**：① 同扰动下新判据 **3/3 绿**；② 退化成旧形态（每 worker 一个
      `Barrier(1)`）+ 同扰动 + 旧断言 ⇒ **3/3 红**（`assert 1 >= 2`）；③ 退化形态下新判据
      也红（序号全 0 ⇒ 可识破）。

### WP-B — 真墙钟覆盖矩阵

- [x] 覆盖表（`test_cross_process_real.py` 模块 docstring：用例 × 等待判据 + 逐条"覆盖时序 /
      证伪条件" + **未覆盖小节 4 条**）。
- [x] 判据用例 `tests/postgres/test_wall_clock_coverage_matrix.py`（8 条）：一一对应、判据
      词汇与数字同 AST 交叉核对、任何 `time.sleep` 必须在有 `deadline` 守卫的函数里、
      未覆盖小节非空、`timing_sensitive` 标记在位。
- [x] 反证实跑（4 种退化）：删矩阵行 / 判据写 `SLEEP(3s)` / 模块级 `time.sleep(60)` /
      无守卫函数内 `time.sleep(60)` ⇒ 各红一次；还原 **8 passed**。

### WP-C — 文档同源

- [x] 矩阵 docstring 写明"这一档的用例为什么属 `timing_sensitive`"（真实墙钟、不注入时钟 ⇒
      串行跑），指向既有注册表 `pyproject.toml` 与 m0 runner docstring，不新造孤立文档。

### WP-D — 记录与回写

- [x] RECHECK-20260918-103、MEM-20260918-076、PLAN/ALL_PLAN/`memory/INDEX.md`、
      GOAL-006 回写（EC-04 状态 / 迭代日志 / child_plans / 状态历史 / 续点 → EC-05）。

## 证据

- **反证 A/B（WP-A）**：同一扰动下旧形态 3/3 红（`assert 1 >= 2`）、新判据 3/3 绿；退化
  形态下新判据也红（到达序号全 0）。脚本：`scratch/ec04/run_a_perturbation.py`、
  `scratch/ec04/run_b_new_judgement.py`。
- **矩阵判据反证（WP-B）**：4 种退化各红一次（`<module>:51` / `_clean:106` / 缺行 / `SLEEP(3s)`）；
  还原 8 passed。脚本：`scratch/ec04/run_wp_b_counterproofs.py`。
- **返工**：矩阵 4 列行 220 字符触发 `E501`（m0 首跑 `python/product-lint` 红）⇒ 拆成
  "短表 + 逐条要点"，判据同步两段式（断言强度未降，另加"要点必须含「证伪」"）。
- **定向**：`tests/postgres` **100 passed**（28.29s）；规模门禁 **939 passed**。
- **m0 全量**：**PASS: profile=m0; 23 deterministic checks**。

## 状态历史

- 2026-09-18 建档（GOAL-006 cycle 4 = EC-04，driver=client-goal / owner=root-agent）：
  只读勘察确认旧断言的调度依赖机理（单线程可全排空、`_drain` 无相位事实）与
  `test_cross_process_real.py` 的等待面现状（有界轮询但无覆盖表）；`status: IN_PROGRESS`。
- 2026-09-18 执行完成：WP-A…WP-D 全绿（相位判据 + 反证 A/B + 覆盖矩阵 + 8 条判据 + 4 种
  退化反证 + 定向 100 passed + m0 23/23）；`status: DONE`；`latest_recheck` 指向
  RECHECK-20260918-103（PASS_WITH_WARNINGS，W-1…W-5）。

## 影响报告

- **Domain / API / schema**：零变化（只动 `tests/postgres/**`）。
- **持久化 / 迁移**：无。
- **安全 / 凭据**：无（不引入新连接面；DSN 仍只从环境变量读）。
- **兼容性 / 迁移风险**：低（测试形态变化；`timing_sensitive` 标记与串行要求不变）。
- **上游版本影响**：无。
- **下一项任务**：GOAL-006 cycle 5 = EC-05（批量读显式上限 + Fake 弱同判对齐或显式边界）。
