---
id: RECHECK-20261010-366
slug: goal-042-ec03-04-memory-consumption-on-the-run-path
title: 独立复检：GOAL-20261009-042 cycle 2（记忆时效门驱动运行链 —— 三态分派 / 两条通道 / 两时点）
plan_id: PLAN-20261009-365
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-10
completed_at: 2026-10-10
owners:
  - root-agent
---

# RECHECK-20261010-366 — GOAL-20261009-042 cycle 2 独立复检

复检对象：`PLAN-20261009-365` 的 EC-03/EC-04 面。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 门的声明与缺省（AC-03，独立重跑）

| 检查 | 读数 |
| --- | --- |
| 声明在场且**缺省关** | `RunChainCall.memory_validity_gate: bool = False`（`runner` 逐字） |
| 未声明 ⇒ 不跳过 / 不标注 | `test_without_the_declaration_nothing_is_skipped_or_annotated` 独立重跑绿 |
| 未声明 ⇒ 过期记忆**不**阻止执行 | 运行链实跑：provider 调用次数 **2**（与无门时一致） |

### 2. 三态分派与两条通道（AC-03，独立重跑）

- `SKIP` ⇒ **不执行**：实跑 provider **只被调 1 次**，理由逐条点名 `m-old` / `EXPIRED` / 声明值；
- `ANNOTATE` ⇒ **照常执行**：provider **被调 2 次**，且落 `annotations`（`skipped == ()`）；
- `USE` ⇒ 两步都执行且**两条通道都空**；
- 过期**优先**于待复核（同时在场 ⇒ `SKIP`）；
- 0 条记忆 ⇒ `USE`（**不**当成「全部过期」）；
- **fail closed**：`memories` 缺字段 / 条目非对象 / `disposition` 未知 ⇒ 各自**点名**。

**独立重跑读数**：`test_memory_validity_gate.py` **19 passed**；
`test_memory_gate_on_the_run_chain.py` **6 passed**。

### 3. 两时点（AC-04(a)，独立重跑）

同一份记忆（`expires_at = 2026-10-09T00:00:00Z`）在两个时点：

| 时点 | provider 调用 | 通道 |
| --- | --- | --- |
| `2026-10-08T23:59:59Z`（边界前） | **2** | 两通道空 |
| `2026-10-09T00:00:01Z`（边界后） | **1** | `skipped` 点名 `m-boundary` / `EXPIRED` / `2026-10-09` |

⇒ 行为**可区分**，差异**只**来自时效判定。

### 4. 载荷唯一构造点（本轮抽出的结构性修复）

`run.completed` 的字段清单此前在 `phase_runner` 与 `round_loop_runner` **各写一份**
（后者注释自陈「否则跑循环的 run 会**丢掉**跳过事实」）⇒ 新通道会**只到一边**。
本轮抽出 `run_completion_payload`（`packages/application/run_orchestration/`），两处调用点
共用。**独立复核**：`grep -c "run_completion_payload("` 在三文件各命中（定义 1 / 两调用点各 1）。

### 5. 两向反证（AC-04，独立重跑）

| 按压 | 改坏什么 | 结果 |
| --- | --- | --- |
| `G-1` | 待复核改判 `SKIP`（三态混用） | RED |
| `G-2` | 门变恒真（缺省不再豁免） | RED |
| `G-3` | 点名理由变空串 | RED |
| `G-4` | **翻转 `validity_at` 的比较符** | RED |

复原后 raw `sha256` **逐字节相同**；判词归档进树
`.cursor/plans/goals/evidence/GOAL-20261009-042-ec03-press-two-way.txt`（220 B / `CR=0`）。

### 6. 门链与记录面（AC-05 前置）

四道门（`ruff format --check` / `ruff check` / `mypy` strict（392 files）/ 规模门）全绿；
广面 `tests/{application,architecture,e2e,tooling}` **2817 passed, 14 skipped**；
**全量 m0 23/23**（`PASS [` 24 / `FAILED [` 0 / **5317 passed, 228 skipped**）。

### 7. 本轮发现并修的缺陷（独立复现）

- **`tuple(f"..." )` 逐字符 tuple**：`memory_gate_verdict` 初版把点名字符串裹成了
  **逐字符 tuple**（测试先红、产品已修 ⇒ 判据的价值当场兑现）；
- **规模门**：`phase_capabilities.py` 曾 **466 行**（> 450）与 `phase_runner.py` **453 行**；
  判据文件曾 **492 行** ⇒ 已拆（判据拆单元 / 集成两文件；产品拆函数与抽小工厂，
  行为一字未改）。

## 结论

**result: PASS_WITH_WARNINGS**。AC-03/AC-04 逐条独立成立：门**真的**决定工具跑不跑
（调用次数可判）、三态互不混用且两条通道分列、两时点可区分、两向反证打满。

### Warnings

- **W-1（消费面只落在运行链，未覆盖其它路径）**：门只作用于 `RunChainCall` 声明的调用
  （与既有 `requires_previous_ids` 同一层）。**未覆盖**：会话工具面的模型自主调用不经此门
  （会话工具面在生产装配里仍是惰性的）、以及非运行链路径（REST 读面只披露、不阻止）。
- **W-2（本 GOAL 不做自动处置）**：`SKIP` 的效果是**本步不执行**（点名）；
  **不**自动删除 / 降权 / 重建索引（`T-1`）。
- **W-3（跨项目 scope 与置信度阈值未纳入判定）**：判定只按时效（`T-2` / `T-3`）。
- **W-4（承继残余原样保持）**：GOAL-041 的 `S-1`…`S-3`；GOAL-040 的 `R-1`…`R-3`；
  GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；
  `R26-*` 终态；未覆盖范围逐条保持。**不得**据此宣称项目安全（`R-M1`）；
  **不得**宣称投递语义为那四个字（**明确否认**）。
