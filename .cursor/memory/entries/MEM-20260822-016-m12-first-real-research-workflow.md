---
id: MEM-20260822-016
title: M12 First Real Research Workflow 与真实 Relay 冒烟
status: ACTIVE
created_at: 2026-08-22
updated_at: 2026-08-22
scope: repository
confidence: 0.9
review_after: 2026-12-22
source_plans:
  - .cursor/plans/tasks/PLAN-20260822-016-m12-first-real-research-workflow.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260822-016-m12-first-real-research-workflow.md
supersedes: []
tags: [m12, relay, ncbi, budget, evidence]
---

# MEM-20260822-016 — M12 First Real Research Workflow 与真实 Relay 冒烟

## 做了什么

1. M12 端到端真实研究链落地并验证：真实学术工具（NCBI E-utilities REST
   provider，`adapters/research_tools/ncbi.py`，17 契约测试 + 真实冒烟
   754 hits）、真实容器实验（`test_m12_reference_e2e.py`，6 docker E2E，
   baseline 0.745 vs candidate 0.28 对照）、证据链（`packages/application/
   evidence/m12_chain.py`，10 测试）、M11 独立评测（10 维度冻结数据集，
   verdict PASS）、四源 Budget 闭环（`budget_closure.py`，清偿 SA-1-M008）、
   formal deliverable（`docs/research/M12_REFERENCE_RESEARCH_REPORT.*`）。
2. 真实 Model Relay 冒烟成功：`https://opencode.ai/zen/go/v1` +
   `muse-spark-1.2-contributor`，probe ok、5 项能力（CHAT/STREAMING/
   STRUCTURED_OUTPUT_NATIVE/TOOL_CALLING_NATIVE/USAGE_REPORTING）全通过，
   returned_model_name 与请求一致，system_fingerprint=None（relay 不返回，
   如实记录为"可重复配置"）。

## 为什么这样做

- M12 目标：不造第二套 pipeline，最大组合 M0-M11 既有生产 Contracts
  （Protocol Compiler/Preflight/Manifest、M9 Experiment、M10 Evidence、
  M11 Eval、BudgetLedger）。
- 真实工具选 NCBI E-utilities：官方 API、无 OAuth、ToS 明确；REST adapter
  而非 MCP 包壳（无官方 MCP server，自建 stdio 包壳无隔离收益）。
- 实验纯标准库实现：sandbox 镜像 `python:3.12-slim` 无第三方 ML 依赖，
  避免引入未 pin 的 package install（供应链纪律）。

## 怎么做与复现

1. 真实 relay 冒烟：`$env:LLM_MAIN_KEY = "<key>"`（PowerShell 强制 env 名
   大写）；`uv run --frozen --no-sync python -B tools/m12_relay_smoke.py`；
   预期 `probe ok=True` + `RELAY SMOKE OK`。base_url 必须以 `/v1` 结尾
   （OpenAI-compatible 路径前缀，`/zen/go` 根路径 GET /models 返回 404
   HTML）。
2. NCBI provider：`uv run --frozen --no-sync python -B tools/m12_ncbi_smoke.py`
   （需 `NCBI_API_KEY`）；`pytest tests/contracts/test_ncbi_provider_contract.py`。
3. 容器实验：`pytest tests/application/experiments/test_m12_reference_e2e.py
   -m requires_docker`。
4. 评测：`pytest tests/evals/test_m12_evaluation.py`；数据集冻结用
   `uv run --frozen --no-sync python -B tools/freeze_eval_dataset.py
   examples/eval/datasets/m12_research_v1.yaml`。
5. Deliverable：`uv run --frozen --no-sync python -B
   tools/m12_generate_deliverable.py`。

## 适用边界

- 适用于：M12/M13/M14 复用 M12 证据链（m12_chain）、budget_closure、
  NCBI provider 作为真实工具范例；后续真实 relay 接入时按
  `tools/m12_relay_smoke.py` 冒烟。
- 不适用于：M14+ 持久化语义（EvidenceLedger/MemoryStore 仍为进程内
  Fake）；DeepSeek Harness runtime（future candidate）；批量科研工具接入。

## 失效与复核触发器

- 到达 `review_after`。
- opencode.ai relay 端点结构变化（/v1 前缀、模型名变更）。
- NCBI E-utilities 协议/ToS 变更。
- M14 落地 EvidenceLedger/MemoryStore 持久化后，M12 证据链内存语义被替代。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20260822-016-m12-first-real-research-workflow.md` | M12 范围/DoD/验收条件 |
| recheck | `.cursor/plans/rechecks/RECHECK-20260822-016-m12-first-real-research-workflow.md` | DoD 14 项 PASS 独立复核 |
| repository | `docs/roadmap/M12_COMPLETION_RECORD.md` | DoD 14 项逐项证据 |
| repository | `tools/m12_relay_smoke.py` 运行输出 | probe ok + 5 能力 + returned_model 一致 |
| repository | `adapters/research_tools/ncbi.py` + 17 契约测试 | NCBI provider 生产路径 |
| repository | `examples/eval/datasets/m12_research_v1.yaml` digest sha256:af6630f3… | 冻结评测集 |