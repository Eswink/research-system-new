---
id: RECHECK-20260923-133
plan_id: PLAN-20260922-133
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-23
completed_at: 2026-09-23
reviewer: independent-closeout-script + root-agent-goal-011-ec06
baseline_ref: 6f5b9fb5
checked_head: 收口提交（RECHECK-133…139 + EC-06 置 PASS + GOAL 置 BLOCKED 同一次提交落地）
---

# RECHECK-20260923-133 — 真实检索进协议（GOAL-011 EC-01）

## 检查范围

**不采信 PLAN-133 的结论文本**：承重面由**独立复检脚本** `scratch/verify_goal011_closeout.py`
从**树上重新推导**（只用标准库、不 import 仓库代码、可在干净 checkout 里跑），
两棵树的同结论证据见 `RECHECK-20260923-139`（同一次收口）。

## 检查结果

| # | 该 PLAN 的主张 | 复检怎么验的 | 结论 |
| --- | --- | --- | --- |
| 1 | 能力由**运行链**执行（不是会话工具） | A 层：`packages/application/run_orchestration/phase_capabilities.py` 里 `execute_run_chain_capabilities` / `RunChainCall` / `CapabilityDeps` / `ScopedPolicy` 四个符号在位（AST，不读注释） | ✅ |
| 2 | 协议侧**声明**了能力执行面 | A 层：`examples/protocols/real_retrieval_research_v1.yaml` 含 `real_retrieval_research_v1_0_1`、`capability_execution: run_chain`、`literature.search`；**文档自己**写的那一行与加载/编译面逐字对上（判据 `test_declared_protocol_says_run_chain_in_the_document_itself`） | ✅ |
| 3 | 工具观测经**读面**可读（不是只在进程内存里） | B 层：`tests/e2e/test_run_chain_retrieval_offline.py::test_run_chain_retrieval_is_observed_and_traceable` 与 `…_absent_without_the_wiring`（成对）按名在位；本 cycle 实跑该文件 **passed**（`egress guard: judged … blocked 0`，离线） | ✅ |
| 4 | 反证成对（移除能力 ⇒ 判定回落） | 同上第二条用例即反证面；`tests/application/run_orchestration/test_run_chain_capabilities.py` 的三条（含 `…_missing_declared_query_fails_closed`）在位并实跑通过 | ✅ |
| 5 | 判据**寄存器**与产品一致 | A 层反向检查：`tests/architecture/python/test_run_chain_capability_exposure.py` **逐字仍在**且本 cycle 实跑 **8 passed**（cycle 10 未改它一个字——见下「W-1」的由来） | ✅ |
| 6 | 出网纪律 | E 层：`tests/egress_guard.py` 的 `ALLOWED_KINDS` 仍**只有** `localhost`（正则判）；本 cycle 所有实跑的 guard 行都是 `blocked 0`；未做 live 检索 | ✅ |

## 结论

**PASS_WITH_WARNINGS**：EC-01 的承重面（协议声明 → 加载/编译透传 → 运行链执行 → 工具观测可读 →
证据准入）在树上逐条成立，且其**唯一**结构性判据（能力执行面同源判据）**未被本 GOAL 改动**。

**W 列表（承自 PLAN-133，本次复检未消除）**

- **W-1**（本轮新增，登记在 `RECHECK-20260923-139`）：协议声明面的**寄存器是字面量**——
  cycle 9 一度把 m12 也声明为 `run_chain`，该判据依设计**立刻判红**（判据没错，是声明错了位置）。
  撤回后重新变绿；这条按设计工作，登记以免下次再踩。
- **W-2**：能力链的**多调用**受限（`_operation_key` 只含 `ids` ⇒ 单 task 非自产来源上限 3），
  已独立登记为工程记忆 `MEM-20260923-106`；它不属于 EC-01 的判据面，但会限制 EC-03 的载体。
