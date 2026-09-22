---
id: RECHECK-20260923-134
plan_id: PLAN-20260922-134
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-23
completed_at: 2026-09-23
reviewer: independent-closeout-script + root-agent-goal-011-ec06
baseline_ref: 6f5b9fb5
checked_head: 收口提交（RECHECK-133…139 + EC-06 置 PASS + GOAL 置 BLOCKED 同一次提交落地）
---

# RECHECK-20260923-134 — 证据链的「系统取得」性质（GOAL-011 EC-02）

## 检查范围

**不采信 PLAN-134 的结论文本**：性质面（枚举成员、覆盖判据的**性质**输入、准入入口、
合约侧的声明）由独立复检脚本从树上重新推导（AST + 文本），两树同结论见 `RECHECK-20260923-139`。

## 检查结果

| # | 该 PLAN 的主张 | 复检怎么验的 | 结论 |
| --- | --- | --- | --- |
| 1 | `TrustLabel` 新增 `RETRIEVED` 成员 | A 层：`packages/domain/enums.py` 里 `RETRIEVED` 在位（AST 标识符，不是子串） | ✅ |
| 2 | 覆盖判据按**来源性质**判，而不是计数 | A 层：`packages/domain/acceptance.py` 里 `minimum_retrieved_sources` 在位；`packages/application/run_orchestration/result_handler.py` 里 `count_retrieved_sources` 在位（域 + 应用面各一处，缺一条即红） | ✅ |
| 3 | 检索来源经**唯一准入入口**落 canonical | A 层：`packages/application/evidence/tool_evidence.py` 里 `register_tool_evidence` 在位 | ✅ |
| 4 | 合约侧声明了这条门槛 | A 层：`examples/contracts/task_contracts.yaml` 含 `real_retrieval_deliverable` 与 `minimum_retrieved_sources` | ✅ |
| 5 | 反证成对（去掉检索来源 ⇒ 覆盖判拒） | B 层：`tests/application/evidence/test_provenance.py`、`tests/domain/test_tasks_acceptance.py` 在位并实跑通过；覆盖判拒的**方向**在 `tests/e2e/test_run_chain_retrieval_offline.py` 的成对用例里 | ✅ |
| 6 | 判据面未被放宽 | 本 cycle 的 E 层：`tests/egress_guard.py` 的 `ALLOWED_KINDS` 未变；cycle 10 只撤回 cycle 9 的**载体**改动，**未动** EC-02 的任何文件（`git diff 6f5b9fb5 -- <EC-02 四条路径>` 为空） | ✅ |

## 结论

**PASS_WITH_WARNINGS**：读面能区分 `USER_PROVIDED` 与 `RETRIEVED`、覆盖判据吃的是**来源性质**
（不是计数）、检索来源只从准入入口进 canonical——四条在树上成立，且本 GOAL 收口时**逐字节未动**。

**W 列表（承自 PLAN-134，本次复检未消除）**

- **W-3**：`RETRIEVED` 的**条数**受限（单 task 非自产来源 3 条上限；见 `MEM-20260923-106`）⇒
  「覆盖由检索来源满足」在**小门槛**下可判定，但在 m12 的 `minimum_sources: 10` 上不可达。
  这是**判据与机制**的口径差，不是实现缺口；它属于 EC-03 的下一轮输入。
- **W-4**：验收门**另有维度未接线**（`SCHEMA_VALID` 的 `schema_check`、`TEST_PASSES`、`POLICY_COMPLIANT`
  在 `EvaluationInputs` 里没有对应字段；cycle 9 全仓搜索 0 命中，登记在 `PLAN-20260922-138`）。
  它们不影响 EC-02 的判据，但会让**任何**声明这些判据的合约停在「判不出」上——属 EC-03 的下一轮输入。
