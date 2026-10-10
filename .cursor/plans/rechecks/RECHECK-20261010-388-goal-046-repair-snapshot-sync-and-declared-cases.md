---
id: RECHECK-20261010-388
slug: goal-046-repair-snapshot-sync-and-declared-cases
title: 独立复检：GOAL-20261010-046 cycle 3（修复轮 —— 快照同步真红 / EC 声明的用例补齐 / 归档定格）
plan_id: PLAN-20261010-387
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-10
completed_at: 2026-10-10
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（修复后的 HEAD + 工作树改动）
    evidence: .cursor/plans/goals/evidence/GOAL-20261010-046-verdict-current.txt
  - path: 干净 checkout（`git worktree add --detach <base-ref>`，同一份断言集）
    evidence: .cursor/plans/goals/evidence/GOAL-20261010-046-verdict-clean.txt
---

# RECHECK-20261010-388 — GOAL-20261010-046 cycle 3（修复轮）独立复检

复检对象：`PLAN-20261010-387`。独立重跑下列机械面，不引用 PLAN 结论当证据。
**`verify_paths` 声明：2 路**（本树 + `--base-ref` 的干净 checkout，同一份断言集）。

## 检查结果

### 1. 三处缺口的**修前复核**（独立重跑，不引用 PLAN 叙述）

| # | 检查 | 读数 |
| --- | --- | --- |
| 1.1 | **CI 真红逐字** | `de9d396` 的 `quality-ubuntu-latest` / `quality-windows-latest` **failure**；失败面逐字 `test_openapi_snapshot_is_current` 的 `assert regenerated == committed` |
| 1.2 | 同一次 run 的**另一条**红 | `test_every_named_assertion_set_reports_no_negative_on_this_tree` ⇒ `['verdict-archive-current', 'verdict-archive-clean']`（**归档时序**，与 1.1 **不同类**） |
| 1.3 | **快照缺字段**（修前） | `git show 04123a7:docs/api/openapi.m13.json \| grep -c human_gate_at_index` ⇒ **0**（`de9d396` / 当时的 HEAD 同） |
| 1.4 | **工作树里的快照为何「看着有」** | 该判据先读已提交字节、再**重生成**（会覆写文件）后比对 ⇒ 本地跑一次它就自我修复 ⇒ 工作树文件比 HEAD 新（**这就是那个 `M` 的来源**） |
| 1.5 | **EC-02 声明的用例当时不存在** | `rg -l human_gate_at_index tests/` ⇒ 修前**只有** `test_program_waiting_on_the_run_path.py`（判定面）；SQLite / PG / 域 / e2e **零用例** |
| 1.6 | **EC-04 声明的实跑臂当时不存在** | `tests/e2e/test_program_advance_on_the_run_path.py` 修前 7 例，**无一**经 HTTP 面声明闸门 |

### 2. 修复面逐条（独立重跑）

| 检查 | 读数 |
| --- | --- |
| 快照重生成 | `uv run --frozen --no-sync python -B tools/gen_openapi.py` ⇒ 两个 DTO 各 +1 属性块；`numstat` `+23 / -0` |
| 快照判据**一字未改**且绿 | `tests/contracts/test_openapi_snapshot.py` ⇒ **8 passed**（`git log -1 --stat` 该文件本轮无改动） |
| EC-02 用例 | SQLite **5 passed** / PG **3 passed** / 域 **10 passed** |
| EC-04 用例 | e2e **9 passed**（含声明闸门拦下 + 未声明逐字不变**成对**） |
| 判定面用例 | `test_program_waiting_on_the_run_path.py` **14 passed** |
| 收口验证器 | **74 判词 / 0 FAIL**（归档两项在本轮归档写入后转绿） |
| 四道门 | `ruff check` / `ruff format --check`（5 文件）/ `mypy` strict（5 文件）**全绿**；规模门：改动的 5 个测试文件 ≤ 450 行、函数全 ≤ 50 |
| 收口断言集**纯收紧** | 例数下界 +3 文件（`8`→`10`、+5、+3、+9）+ 新增 2 条判词；**未删任何既有断言** |

### 3. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | 改动 | 谓词比对 | `numstat` | 删除行 |
| --- | --- | --- | --- | --- |
| `tests/adapters/sqlite/test_program_store_sqlite.py` | **追加** 1 例 + import | — | `+16 / -0` | **0** |
| `tests/postgres/test_program_store_pg.py` | **追加** 1 例 | — | `+34 / -0` | **0** |
| `tests/domain/test_research_program.py` | **追加** 1 例 | — | `+28 / -0` | **0** |
| `tests/e2e/test_program_advance_on_the_run_path.py` | **追加** 2 例 + 1 常量 | — | `+50 / -0` | **0** |
| `tests/e2e/program_advance_support.py` | `create_program` +1 **可选**形参 | 缺省路径请求体与旧字面量**逐键相同**（逐条核对：`protocol_path` / `max_runs` / `continue_on_verdicts` / `max_attempts_per_index` 四个键一字未改） | `+13 / -7` | 7 行 = 同一字面量改写成 `payload` 变量（**非**谓词改动） |
| `tools/goal046_closeout_assertions.py` | 例数下界 +3 + 2 条新判词 | **纯收紧**（只加） | `+41 / -2` | 2 行 = `CASE_FLOORS` 表项改写（下界 `8`→`10`；扩项），**原有两条下界一字未降** |

**收窄受判面？** 无。本轮**未**收窄任何受判面；`tests/contracts/test_openapi_snapshot.py`
**一字未改**。

### 4. 两树复检与归档（独立重跑）

`tools/two_tree_recheck.py --script tools/verify_goal046_closeout.py --script-mode shared
--base-ref HEAD` ⇒ 终局行 **`TWO-TREE PASS`**；两路 **76 判词**、`sha256` 相同
`9d1c8a1c5996a12b…`、`COMPARE identical=True`。归档两份各 **2897 B / 76 行 / `CR=0` / 0 FAIL**
（二进制写盘）。**as-is m0**：`PASS: profile=m0; 23 deterministic checks`
（`PASS [` 24 / `FAILED [` 0 / **5565 passed, 21 skipped**；在全部记录写完之后、独占、
仓库 `.venv`、不接管道；**读数口径**：本轮 postgres-test 容器已启 ⇒ PG 标记用例**实跑**，
故与 GOAL-045 那轮（228 skipped）不可直接比）。

## 结论

**result: PASS_WITH_WARNINGS**。三处缺口（CI 真红 / EC-02 声明用例缺失 / EC-04 实跑臂缺失）
**逐条如实登记并修好**：快照按生成器重生成且判据一字未改，四类用例补齐且例数下界钉进收口
断言集，归档与最终一轮同结论。

### Warnings

- **W-1（本轮抓到的真红是**产品面**缺同步，不是判据放宽）**：cycle 1 改了 DTO 未重生成快照
  ⇒ CI 判红；**处置是修产品面**（重生成 + 提交 + 写进收口断言集），`test_openapi_snapshot.py`
  一字未改。**不得**把它读成「时序」或「判据问题」。
- **W-2（cycle 2 的收口依据不足，本文更正）**：cycle 2 把 GOAL 收口成 ACHIEVED 时，
  EC-02 / EC-04 的 `verify` 行点名的行为面用例**当时不存在**，且 CI 真红未被读到
  （当时只轮询到 `04123a7` 与 `de9d396`，未见随后的归档提交 `06e9b01`）。
  **本文按实测更正**：GOAL 的收口状态在修复轮完成前**不成立**（由本轮补齐后重新回写）。
- **W-3（闸门的处置 / 条件式闸门不在本 GOAL；承 `X-1` / `X-2`）**：本轮让闸门
  **可声明 / 可判定 / 可点名**；**不**做催办 / 升级 / 超时取消，**不**做条件式或多点声明。
- **W-4（D 组审批通道本身不在本 GOAL；触达即 BLOCKED；承 `X-3`）**：闸门用的审批面是
  **既有**实例；不放开任何 destructive 能力的放行。
- **W-5（既有判据假红，已修；承 `MEM-20261010-215`）**：为守 450 行规模门把失败重试面搬到
  `program_retry.py` ⇒ `goal041` 的两条**按位置写死**的断言假红，**被 GOAL-043 立的「零判负」
  判据当场捕获** ⇒ 改成「判关系不判位置」。登记为**搬迁的既有代价**。
- **W-6（承继残余原样保持）**：GOAL-045 的 `W-1`…`W-3`；GOAL-044 的 `V-1`…`V-3`；
  GOAL-043 的 `U-1`…`U-3`；GOAL-042 的 `T-1`…`T-3`；GOAL-041 的 `S-1`…`S-3`；
  GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；
  GOAL-037 的 `O-1` / `O-3` / `O-4` / `O-5`；`R26-*` 终态；未覆盖范围逐条保持。
  **不得**据此宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
