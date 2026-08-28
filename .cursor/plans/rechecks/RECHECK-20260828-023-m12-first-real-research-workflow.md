---
id: RECHECK-20260828-023
plan_id: PLAN-20260828-017
attempt: 2
status: COMPLETED
result: PASS
created_at: 2026-08-28
completed_at: 2026-08-28
reviewer: root-agent-independent-pass
baseline_ref: M12_COMPLETION_RECORD（原 PASS 已证伪）+ M12_R1_COMPLETION_RECORD（13 Finding 修复）+ RECHECK-019（修复轮复检 PASS）
checked_head: 2026-08-28 工作树（M12-R1 修复 + M14 收口后；DoD-3 live relay 凭据闭环 2026-08-28 晚间）
---

# RECHECK-20260828-023 — M12 First Real Research Workflow 重新独立复审重判

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260828-017-m12-first-real-research-workflow.md`
- 复审基线：M12 原 PASS 判定已证伪（Fake chain / synthetic digest / 手工 usage）→ M12-R1 13 Finding 修复闭环（RECHECK-019 PASS）→ 本次整体重判
- 本重判方法：只读重审交付物 + **重新执行 M12 关键测试套件**（110 tests 全绿）+ 代码路径审计（真实链 vs Fake 占位）

## 检查结果（DoD 14 条重判矩阵）

| # | DoD | 结果 | 证据（本次实测/重审） |
| --- | --- | --- | --- |
| 1 | Reference Protocol 经 Compiler/Preflight | PASS | `m12_reference_research_v1.yaml` compile 0 ERROR + preflight PASS（R1 后 manifest freeze 单入口 `m12_composition.py`） |
| 2 | RunManifest 冻结真实执行语义 | PASS | `test_m12_manifest_freeze.py` 11 tests 实测通过；manifest 扩展字段（endpoint/probe/image/skill/eval）冻结 |
| 3 | 真实 Model Relay production path | **PASS（2026-08-28 凭据闭环）** | `tools/m12_relay_smoke.py` probe ok=True + 5 能力全通过（CHAT/STREAMING/STRUCTURED_OUTPUT_NATIVE/TOOL_CALLING_NATIVE/USAGE_REPORTING）、零 capability failure、returned_model=agnes-2.5-flash 无同名漂移；`tools/m12_reference_workflow.py --clean --live-relay` 完整 clean-run `relay.verified=true`、manifest digest `sha256:feca96ba…`、semantic `sha256:4ccebe4a…`、audit PASS、claim VERIFIED、eval PASS（真实凭据经 `LLM_MAIN_KEY` 环境变量，redacted 输出） |
| 4 | 至少一个真实 Research Tool production path | PASS | NCBI E-utilities：`test_ncbi_provider_contract.py` 17 tests 实测通过；`tools/m12_ncbi_smoke.py` 真实冒烟记录 754 hits（M12_R1 后保留） |
| 5 | 真实 M9 Experiment Runtime | PASS | DockerExecutionBackend 6 容器 E2E（`test_m12_reference_e2e.py`，本机 Docker 实跑记录）；ReproducibilityAudit PASS |
| 6 | Evidence/Claim 经 M10 provenance | PASS | `test_m12_chain.py` 10 + `test_m12_integrity.py` 13 + `test_tool_result_not_evidence.py` 6 实测全过；VERIFIED provenance 不变量强制 |
| 7 | M11 独立 Evaluation 实际运行 | PASS | `test_m12_evaluation.py` 7 + `test_m12_evaluation_adversarial.py` 8 实测全过；4 个独立真值 scorer；dataset digest 冻结 |
| 8 | 关键结果 reproduction | PASS | `test_reproducibility_semantic.py` 9 实测全过；semantic digest 稳定、wall-clock 剔除 |
| 9 | Usage/Budget 完整闭环 | PASS | `test_budget_real_wiring.py` 6 + `test_budget_closure.py` 6 实测全过；真实事件归账、retry 不 double-count、硬限阻断 |
| 10 | negative/contradiction/failure 语义 | PASS | `test_m12_integrity.py` 13 实测全过；FAILED≠NEGATIVE_RESULT、DISPUTED 保留、transient/permanent/cancel 分类 |
| 11 | 无 Fake-only core path | PASS | 生产链真实（NCBI/容器/证据/SQLite 持久化）；Fake 仅 contract 测试；合成 digest/手工 usage 生产 0 命中（R1 grep 验证） |
| 12 | 正式可追溯 Research Deliverable | PASS | `docs/research/M12_REFERENCE_RESEARCH_REPORT.{json,md}`；builder 只读聚合、digest 可重算 |
| 13 | M0-M11/IG-1/SA-1R regressions 保持 | PASS | 本会话 m0 profile 19/19（2162 passed/2 skipped）；validate_bundle/governance/docs-check PASS |
| 14 | 干净状态可重复执行 | PASS | `test_m12_clean_run.py` 5 tests 实测全过；clean-run 全链标识输出、semantic digest 跨 run 稳定 |

## Findings

| ID | 严重度 | 发现 | 处置 |
| --- | --- | --- | --- |
| F-01 | ~~WARNING~~ **CLOSED** | DoD-3 真实 relay live 证据在无凭据环境下不可重放（原为 NOT VERIFIED 结构化占位） | **2026-08-28 凭据闭环**：`LLM_MAIN_KEY` 提供后 `tools/m12_relay_smoke.py` probe PASS + `tools/m12_reference_workflow.py --clean --live-relay` `relay.verified=true`；`tests/e2e/test_m12_usage_real_relay.py` live E2E 3 passed（真实归账）。DoD-3 由 NOT VERIFIED 转 PASS |
| F-02 | INFO | M12 已知限制（fingerprint=None、execution-time 门禁接线、memory policy 注入、reservation ref 接入）为 M12-R1 诚实声明，不阻断本重判 | 保持 remaining debt 记录 |

## 结论

- 结果：`PASS`（F-01 关闭；原 PASS_WITH_WARNINGS → PASS）
- 理由：14/14 项 DoD 实测 PASS；DoD-3 真实 relay live 证据于 2026-08-28 凭据闭环（probe ok + verified=true + usage 归账 E2E 3 passed）。
- 后续动作：M12 → MVP 成立（GO 判定维持）；M13（已 DONE）/M14（已 DONE）按 IG-2 汇合；`system_fingerprint=None` 如实标注"可重复配置"（AGENTS.md §4），不构成阻断。
