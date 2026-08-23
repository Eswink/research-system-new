# M12 Reference Research Report

- report_id: `m12-reference-research:12121212-2222-4333-8444-555555555555`
- objective: Compare baseline (TF-IDF + linear classifier) vs candidate (frozen hash-embedding + linear classifier) on a low-resource 20-class text classification subset

## Protocol
- id: `m12_reference_research_v1` version `0.4.0`
- phases: discovery, design, execution, analysis, peer_review, deliverable, final_audit

## Experiment（真实容器执行）
- artifact: `12121212-2222-4333-8444-555555555555:experiment_result.json`
- digest: `sha256:bc01f6a055d3e7b1ea4e6ab9c8e7ace8cd05908972761288abd88ae9a385ccd9`
- seed: 7
- baseline_accuracy: **0.745**
- candidate_accuracy: **0.28**
- n_train/n_test: 500/200

## Evidence Chain（M10 provenance）
- source: `experiment:5a1c6a8e-9b2d-4f3a-8c5e-2b2c3d4e5f6a:experiment_result.json` (trust_label=GENERATED)
- evidence: `evidence:12121212-2222-4333-8444-555555555555:5a1c6a8e-9b2d-4f3a-8c5e-2b2c3d4e5f6a`
- claim: `claim:12121212-2222-4333-8444-555555555555`
- after verify: VERIFIED
- after contradiction: DISPUTED

## Governed Memory
- memory: `mem:12121212-2222-4333-8444-555555555555:negative-result` kind=NEGATIVE_RESULT

## Budget / Usage Closure
- model tokens: 2000
- tool requests: 2
- experiment runs: 1
- evaluation cases: 10
- ledger entries: 5

## Independent Evaluation
- dataset: `m12_research_v1`
- digest: `sha256:af6630f33aea2750d7033fa23c8d86a189b968d0360ea4fc76f12fcc531b3888`
- verdict: **PASS**

## 关键结论

在 500 训练/200 测试、20 类、seed=7 的低资源子集上，TF-IDF baseline （0.745）显著优于 frozen hash-embedding candidate（0.28）。该结论为合法科学负结论（candidate 未提升），已作为 NEGATIVE_RESULT 记忆经 governed gate 入账，未被系统压制。
