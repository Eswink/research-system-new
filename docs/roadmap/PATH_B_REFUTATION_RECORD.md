# 路径 (B) 否证记录 —— 已否证 / 待重新设计

**状态：已否证（refuted）/ 待重新设计（needs redesign）。不是待办功能，也不是已完成。**

**载体与登记**：本文件由 `.cursor/plans/tasks/PLAN-20260923-146-path-b-refutation-record.md`
（GOAL-012 EC-04）落盘；在
`.cursor/plans/goals/GOAL-20260923-012-experiment-execution-unblock.md` 的残余节登记路径。

## 这份记录在说什么

GOAL-011（`GOAL-20260922-011-real-research-capability`）的 EC-03 停在两条都需要拍板的路径上：

- **路径 (A)**：让「预检 WARN 但策略已显式允许」的计划**可以冻结**（一条显式、留痕、可审计的
  接受口径）。GOAL-012 已按用户拍板落地并跑通（EC-01 / EC-02 PASS）。
- **路径 (B)**：**为 `m12_reference_research_v1` 补齐 phase 合约**，靠「装配方声明更多次检索调用」
  去满足 `domain_discovery` 合约里**既有**的 `minimum_sources: 10`。

**(B) 的前提被实测否证**：它的核心假设是「声明 N 次检索调用 ⇒ N 条来源」，而这条乘法关系
**不成立**。下面的四项事实是当时的实测结论（出处见每条的「实测出处」），**原样保留**，
不因为 (A) 走通而改写或删除。

## 四项实测事实（逐条）

### ① 单 task 的非自产来源上限 = 3

**机制**：一个 task 的**非模型自述**来源由三部分构成——1 份**声明输入**（`USER_PROVIDED`，
由组合根种入）+ 1 次**检索**调用产生的来源（`RETRIEVED`）+ 1 次**读取**调用产生的来源。
同一 task 内**再加一次检索**不会变成 4 条：见事实 ②。

**实测出处**：`.cursor/plans/tasks/PLAN-20260922-138-real-experiment-chain-via-m12.md`
的「实测结论」§被实测否证（AC-2）与其证据行 `E-3`（`scratch/goal011-c9-m12-offline-chain.py`：
证据面 = `GENERATED / USER_PROVIDED / RETRIEVED×2` ⇒ 非自产 **3**）。

### ② 同一 task 内的第二次检索调用是**硬失败**

**机制**：`phase_capabilities._operation_key` 只在调用参数里带 `ids` 时把它拼进操作键；
`register_tool_evidence` 的 Evidence id = `evidence:{run_id}:{operation_key}`、
`SourceRecord.origin` = `tool:{tool_id}:{task_id}:{operation_key}`。因此**同一 task 内操作键重复的
两次调用会撞同一个 id**：内容相同则记账塌成一条（不增量），内容不同则 `register_source`
抛 `conflicting source registration` ⇒ **整步失败**（run 终止），不是「凑不够 10 条」而是
**直接失败**。

**实测出处**：同 PLAN 的证据行 `E-4`（`scratch/goal011-c9-runchain-source-count-probe.py`，
A/B/C 三个方案的逐字判词：`conflicting source registration: tool:literature_search:…`）。

### ③ `minimum_sources: 10` 的口径与上述机制**不相容**

**机制**：事实 ① 给出的单 task 上限是 **3**，门槛是 **10**，差一个量级；事实 ② 说明「多声明几次
调用」这条路的终点不是「还差几条」而是**整步硬失败**。⇒ 在**不改判据、不改机制**的前提下，
`domain_discovery` 的覆盖判据**不可满足**。

**实测出处**：同 PLAN 的「实测结论」§被实测否证（AC-2 两条）与 `E-2`
（离线全链判词逐字：`acceptance gate rejected: SCHEMA_VALID: schema validator unavailable;
EVIDENCE_COVERAGE: 3 < 10 sources`）。

### ④ 三条判据维度在产品路径上**没有调用方**

**机制**：`SCHEMA_VALID` 需要 `schema_check`，而编排层调 `evaluate_contract(...)` 时**不传**它
（`_evaluate_schema_valid` 缺省即判 `"schema validator unavailable"`，fail-closed）；
`TEST_PASSES` 需要的 `tests` 与 `POLICY_COMPLIANT` 需要的 `policy_decision` 在
`EvaluationInputs.to_criterion_inputs()` 里**没有来源**。⇒ 这三条判据**今天判不出真值**：
声明在合约里，但没有任何产品装配方接过这条线。

**实测出处**：同 PLAN 的证据行 `E-5`（读
`packages/application/run_orchestration/evaluation_gate.py` 与
`packages/domain/acceptance.py`，全仓检索 `schema_check` 只命中域函数签名、域单测与 memory gate）。

## 与 GOAL-011 既有登记的关系（原样保留，不改写）

| GOAL-011 登记 | 原文要点 | 本记录的关系 |
| --- | --- | --- |
| `W-P` | `domain_discovery.minimum_sources: 10` 与「单 task 最多 3 条独立来源」的机制不相容 | **同一事实**（本记录 ① ③）；`W-P` 的正文**一字未改** |
| `W-Q` | `SCHEMA_VALID` / `TEST_PASSES` / `POLICY_COMPLIANT` 今天没有任何产品调用方 | **同一事实**（本记录 ④）；`W-Q` 的正文**一字未改** |
| `W-R` | 「接线未派发过」这类缺口在 cycle 6 的判据形态下不可见 | 背景（与 (B) 的载体经历一致） |
| `PLAN-20260922-138` | `status: BLOCKED`；载体的前提被实测否证；已落地的部分（5 份 phase 合约 + 实验缝三处缺陷修复）**不**因 BLOCKED 而回退 | 本记录**不**改它的状态；BLOCKED 就是本记录所述否证的**登记形态** |

**引用口径**：说到 (B) 时必须写成「**已否证 / 待重新设计**」；不得读成「待办功能」，
也不得因为 (A) 走通而把 (B) 写成「已完成」或从记录里抹掉。

## 重新设计需要什么（属**需拍板**项，不在任何现有 GOAL 的授权内）

若将来仍要走 (B) 这一类「多阶段真实研究协议」，按当时实测，至少要**先拍板并落地**下面几项
（顺序即依赖顺序；**本记录只列，不做**）：

1. **来源数口径的拍板**：要么改 `minimum_sources: 10` 这个数（改判据 = 需拍板），要么承认
   分面检索的成本（≈ 2 × 分面数 次真实出网）。
2. **多调用证据键**：让同一 task 内的多次检索调用可区分（`_operation_key` 按调用参数区分），
   否则事实 ② 的硬失败仍在。
3. **`SCHEMA_VALID` 接线**：为验收门提供 `schema_check`（含 JSON-Schema 实现选型）。
4. **`TEST_PASSES` 接线**：定义实验类合约的测试事实来源。
5. **`POLICY_COMPLIANT` 接线**：把已经做过的策略裁决交给验收门。

## 诚实边界

- 本记录**不重跑**任何实验：四项事实与出处均**引用** `PLAN-20260922-138` 的实测结论与
  GOAL-011 的登记；重跑不增加信息，且其中包含真实出网调用。
- 本记录**不**声称 (B) 永远不可行：它否证的是「**不改判据/不改机制**即可靠多次调用凑够来源数」
  这条具体前提。
- 本记录**不**改任何产品代码、协议、合约、测试或门禁；它只有文档与登记。
