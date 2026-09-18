---
id: RECHECK-20260918-103
plan_id: PLAN-20260918-103
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-18
completed_at: 2026-09-18
reviewer: root-agent-goal-006-cycle4
baseline_ref: ce450c3
checked_head: 26bf47e
---

# RECHECK-20260918-103 — 时钟断言去调度依赖 + 真墙钟覆盖矩阵（GOAL-006 cycle 4 = EC-04）

## 检查范围

PLAN-20260918-103 声称的交付面：① `tests/postgres/test_claim_concurrency_pg.py` 里"并发是
真的"那条断言不再读调度产物、并有相位/计数判据；② `tests/postgres/test_cross_process_real.py`
的真墙钟覆盖矩阵 + 机器判据。

**不在本轮**：产品代码（零改动）；`tests/adapters/execution` 的 Docker/GPU 真实等待矩阵
（属那一档既有 E2E）；`tests/postgres` 以外套件的等待面。

## 检查结果

| 复查项 | 检验方式 | 结果 |
| --- | --- | --- |
| AC-01 旧断言真的依赖调度 | 读 `_concurrent_drain`：`threading.Barrier` 只保证"同时开始"，`_drain` 循环到 `claim_next` 返回 `None` | PASS（24 条任务下单线程可全排空；**实测**见下） |
| AC-01 判据换成相位/计数事实 | 读 `_ClaimProbe` + `_drain(probe, …)` + `_concurrent_drain` 返回值 | PASS（`attempts` = 领循环尝试数；`arrival_index` = 同一个 `overlap` barrier 的到达序号；`failures` = 线程异常；`>= 2` 这条调度代理**已删**） |
| AC-01 前提没被删掉 | 读 `test_concurrent_schedulers_claim_disjoint_work` 的断言集合 | PASS（仍是"真的在并发领任务"：所有 worker 尝试 ≥ 1 + 到达序号集合 = `{0…N-1}`；无重复/全覆盖不变量逐字保留） |
| AC-02 扰动反证：旧形态红 | `scratch/ec04/run_a_perturbation.py`（把 `overlap` 退化成每 worker 一个 `Barrier(1)` = cycle 4 之前的形态 + 注入 0.5s 调度扰动 + 放回旧断言） | PASS（**A1/A2/A3 全红**：`assert 1 >= 2` —— 恰好一个 worker 排空了全部 24 条） |
| AC-02 扰动反证：新判据不红 | `scratch/ec04/run_b_new_judgement.py`（**同一扰动**，保留强制重叠） | PASS（**B1/B2/B3 全绿**） |
| AC-02 无扰动基线 | 全文件 3 次 | PASS（`3 passed` × 3，0.51–0.55s） |
| AC-02 判据能识破"相位构造被拆" | 反证 A 的退化形态下跑新判据 | PASS（`{'w-0': 0, 'w-1': 0, 'w-2': 0, 'w-3': 0} != {0, 1, 2, 3}` ⇒ 红：到达序号判据确实在读"同一个 barrier 的 N 个到达者"） |
| AC-03 矩阵在位且是"覆盖 + 判据" | 读 `test_cross_process_real.py` 的模块 docstring | PASS（3 行矩阵 + 3 条"覆盖时序/证伪条件"要点 + **未覆盖小节 4 条**：跨进程时钟漂移、网络分区、>2 进程压测、GPU/容器等待） |
| AC-03 判据可判定 | `tests/postgres/test_wall_clock_coverage_matrix.py`（8 条） | PASS（**8 passed**；一一对应 + 判据词汇/数字与 AST 交叉核对 + 无界 sleep + 未覆盖小节 + `timing_sensitive` 标记） |
| AC-03 反证（4 种退化） | `scratch/ec04/run_wp_b_counterproofs.py` | PASS（删矩阵行 ⇒ 红「只在文件里：test_stale_fenced…」；判据写 `SLEEP(3s)` ⇒ 红；模块级 `time.sleep(60)` ⇒ 红 `<module>:51`；无守卫函数体内 `time.sleep(60)` ⇒ 红 `_clean:106`；还原后 **8 passed**） |
| AC-03 等待口径写明"有界轮询" | 读矩阵与判据 | PASS（`BOUNDED_POLL(deadline=40s,interval=2s)` 与文件里的 `time.sleep(2.0)` / `timeout: float = 40.0` 交叉核对；"非固定 sleep"由结构判据钉住） |
| WP-C 标记口径指针 | 读矩阵 docstring | PASS（"为什么属 `timing_sensitive`"一段：真实墙钟、不注入时钟 ⇒ 串行跑；指向 `pyproject.toml` 与 m0 runner docstring，未新造孤立文档） |
| AC-04 定向 | `pytest tests/postgres`（DSN pin） | PASS（**100 passed**，28.29s） |
| AC-04 规模门禁 | `tests/tooling/test_python_source_limits.py` | PASS（**939 passed**；新文件 3 处均在阈值内） |
| AC-04 风格/类型 | `ruff format --check` / `ruff check apps services packages adapters tests` / `mypy` | PASS（format 无差异、lint `All checks passed`、mypy `no issues`；**首跑 1 红**：矩阵行 220 字符触发 `E501` ⇒ 拆成"短表 + 逐条要点"，见「返工」） |
| AC-04 m0 全量 | `make validate-all`（DSN pin） | PASS（**23 deterministic checks**；首跑 1 红 `python/product-lint`（同上 E501），修后复跑全绿） |
| AC-04 未越界 | `git diff ce450c3 26bf47e --stat` | PASS（3 文件，全部在 `tests/postgres/**`；产品/Domain/API/schema/迁移/依赖零改动） |

### 交付物在位（结构证据）

- `tests/postgres/test_claim_concurrency_pg.py`：`_ClaimProbe`（尝试数 + 到达序号）、
  `_drain(probe, …)`、`_concurrent_drain` 返回 `(results, probes, failures)`、
  两个并发用例的相位断言。
- `tests/postgres/test_cross_process_real.py`：模块 docstring 的覆盖矩阵 + 未覆盖边界。
- `tests/postgres/test_wall_clock_coverage_matrix.py`（**新增**，8 条判据）。

## 反证与实测

1. **扰动反证（WP-A 核心）**：同一扰动（`start` barrier 之后给 worker-0 之外 0.5s 头程）
   下，`overlap` 退化成 `Barrier(1)` + 旧断言 ⇒ **A1/A2/A3 红**（`assert 1 >= 2`）；
   保留强制重叠 + 新判据 ⇒ **B1/B2/B3 绿**。⇒ 旧断言读调度产物、新判据不读。
2. **相位判据的鉴别力**：退化形态下新判据本身也红（到达序号全为 0），说明它判的是
   "同一个 barrier 的所有到达者"，不是"`wait()` 返回了"。
3. **矩阵判据的鉴别力**：四种退化各红一次（见上表），还原后 8 passed。
4. **定向**：`tests/postgres` 100 passed（含 `test_cross_process_real.py` 的真实 TTL/跨进程
   用例，30s 内跑完，无 flake）。
5. **m0**：23/23（见 GOAL 迭代日志 cycle 4 行）。

### 返工（记录诚实）

- **首跑 `python/product-lint` 红**：矩阵行（4 列、含中文说明）单行 220 字符 ⇒ `E501`。
  修法 = 把矩阵拆成"短表（用例 × 等待判据）+ 逐条要点（覆盖时序 / 证伪条件）"，判据同步
  改为两段式解析（表行 2 列 + 要点逐条）。**断言强度未降**：一一对应、判据词汇、数字与
  AST 交叉核对、未覆盖小节、无界 sleep 全部保留，另新增"要点必须含「证伪」"。
- **反证脚本首版两处失真**（记录以免误读）：① 头程 sleep 放在 `start` barrier **之前** ⇒
  被 barrier 抵消，旧断言在那次跑到的是"绿"（不是反例）；移到 barrier 之后才复现红。
  ② 无界 sleep 先注入到有 deadline 守卫的 `_poll_recover` 内 ⇒ 判据**不该**报（结构上确实
  有界），这一次"未红"是判据正确；改为模块级与 `_clean` 内注入后各红一次。

## 告警（W）

- **W-1（判据钉结构，不钉时间）**：`test_no_unbounded_sleep_in_the_file` 的判据是"`time.sleep`
  落在含 `deadline` 守卫的函数里"，**不检查等待是否真的终止于 deadline**——一个守卫函数里
  写 `time.sleep(300)` 仍会通过结构判据（反证时实测过这一情形）。它是"无界等待"的结构防线，
  不是时间正确性证明。
- **W-2（相位判据证明的是"测试的前提"）**：`arrival_index` 集合证明 N 个 worker 由同一个
  barrier 同时释放；它**不**证明数据库在同一瞬间看到两个并发事务（那部分仍需 SKIP LOCKED
  的真实竞态，本来就是概率性的）。所以本判据的边界是"前提由构造成立"，不是"DB 观测到重叠"。
- **W-3（扰动是测试内 sleep）**：反证用的扰动是代码内 `sleep`，不是真 CPU 抢占/降频。若调度
  器把线程饿到 30s 以上，`_PHASE_TIMEOUT_SECONDS` 会让用例**响亮地失败**（这是设计意图：
  不静默通过），而不是自动降级。
- **W-4（矩阵只覆盖本文件）**：`worker_cross_process.py`（子进程 helper）本身没有等待，不在
  矩阵里；它引入的等待属于"子进程启动/退出"这一层，由用例的 deadline 覆盖。
- **W-5（矩阵格式是判据的一部分）**：表行必须是 `| test_… | <判据> |`、要点必须以
  `` - `test_…`：`` 开头，否则判据红。这是有意的（矩阵与用例同址且被机器读），但意味着
  改矩阵的人要知道这个格式契约（判据会告诉他）。

## 结论

**PASS_WITH_WARNINGS**。EC-04 的两条都拿到终态：① 那条读调度产物的断言被换成**相位/计数
事实**（每 worker 至少一次领循环尝试 + 同一个 barrier 的互不相同的到达序号），"测试真的在
并发"的前提**没有被删掉**、反而由构造保证；同一扰动下旧形态 3/3 红（`assert 1 >= 2`）、
新判据 3/3 绿，拆掉相位构造新判据自己也会红（可识破）。② `test_cross_process_real.py` 有了
**文件级覆盖矩阵**（用例 × 等待判据 + 逐条覆盖时序/证伪条件 + 4 条未覆盖边界），并由
`tests/postgres/test_wall_clock_coverage_matrix.py` 用 8 条判据钉住（一一对应、判据形态与数字
与 AST 交叉核对、任何 `time.sleep` 必须在有 deadline 守卫的函数里、未覆盖小节非空、
`timing_sensitive` 标记在位）；四种退化各被识破一次。定向 100 passed、规模门禁 939 passed、
m0 23/23；零产品代码变化。W-1…W-5 是适用边界：判据钉结构不钉时间、相位判据证明前提而非
DB 观测、扰动是测试内 sleep、矩阵只覆盖本文件、矩阵格式本身是判据的一部分。

## 门禁

- 定向 / 规模门禁 / 风格类型 / m0 全量 23 项：见「检查结果」与「反证与实测」。
- CI 六 job：见 GOAL-006 迭代日志 cycle 4 行（本条推送的 run 按闭合约定在回合汇报给出终态）。
