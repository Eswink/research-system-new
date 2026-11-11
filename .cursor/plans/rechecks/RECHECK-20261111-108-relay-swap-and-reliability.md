---
id: RECHECK-20261111-108
slug: relay-swap-and-reliability
title: GOAL-108 复检 —— 换接入商 + 四个免费模型真分工 + 静默停住四处收口
status: VERIFYING
result: null
created_at: 2026-11-11
updated_at: 2026-11-11
plan_id: PLAN-20261111-108
parent_goal: GOAL-20261111-108
owners:
  - root-agent
verify_paths:
  - examples/config/llm_endpoints.yaml
  - examples/config/models.yaml
  - examples/config/model_profiles.yaml
  - packages/application/run_orchestration/spec_assembly_guard.py
  - packages/application/run_orchestration/phase_runner.py
  - packages/application/run_orchestration/review_outcome.py
  - examples/contracts/task_contracts.yaml
  - tests/e2e/manuscript_chain_live_support.py
  - tests/application/test_spec_assembly_guard.py
  - tests/application/test_review_outcome_no_program.py
  - tests/application/test_session_contract_retries.py
---

# RECHECK-20261111-108

## 复检范围

GOAL-20261111-108 的十一条 EC 逐条取证。**两路以上**（`verify_paths` 每项都是独立取证路径）。

本轮的射程边界（写在前面，收口时逐条核对有没有越界）：

| 面 | 本轮**交付**什么 | 本轮**不**宣称什么 |
| --- | --- | --- |
| 换站 | 控制面切到局域网免费站、四个模型真分工 | 不宣称「一定跑通」：失败率主因是上游延迟，300s 是缓解不是保证 |
| 可靠性 | 四处静默停住路径收口 | 不宣称「已消除所有静默停住」：只收口了实测可达的四处 |
| 独立性 | 写作组与评审组互斥（真成立） | **不宣称「三位评审者全独立」**：四个免费模型数学上不够，用户拍板放宽了这一面 |
| 重试 | 五份会话合约声明瞬时重试 | 不宣称「统一了 `retryable_categories` 语义」：全仓两处矛盾保留，登记 `W-1` |

## 检查结果

（收口时逐条填写。）

## 反证臂汇总（**判据咬得住**的证据）

（收口时填写：每条新增判据的两向按压留证。）

## 结论

（收口时填写。）
