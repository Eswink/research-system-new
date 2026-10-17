---
id: RECHECK-20261016-504
slug: goal-081-ec04-cross-phase-inputs
title: GOAL-081 cycle 4 复检 — 跨相输入闭合 EC-04 的覆盖缺口
status: COMPLETED
result: PASS
created_at: 2026-10-17
updated_at: 2026-10-17
plan_id: PLAN-20261016-503
parent_goal: GOAL-20261016-081
reviewer: root-agent
owners:
  - root-agent
---

# RECHECK-20261016-504 — GOAL-081 cycle 4

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | **(a) 编译期点名六类非法引用** | **PASS** | `test_cross_phase_inputs.py` 8 条：自引用 / 未知 phase / 非上游 / 产出方未声明该产物 / 产物歧义 / 形态判定（`input-brief:` 不误判为跨相） |
| AC-2 | **(b) 性质由产出方决定** | **PASS** | `trust_label` 在**编译期**算好并随 `CompiledPhase.cross_phase_inputs` 携带；运行期 `resolve_cross_phase_sources` **不**重新推导（各推一次必然漂） |
| AC-2p | **(b) 按压** | **PASS** | 摘掉产出方的 `capability_execution: run_chain`（读取方一字不动）⇒ 性质从 `RETRIEVED` 变 `GENERATED` —— 若判据读的是读取方或常量，两读数不可能同时成立 |
| AC-3 | **(c) 两条来源并列** | **PASS** | `declared_inputs`（`USER_PROVIDED`）与 `cross_phase_evidence`（`RETRIEVED`）在**同一次**登记里并存：`evidence_source_count == 2`、`count_retrieved_sources == 1` |
| AC-3p | **(c) 按压：摘掉跨相证据 ⇒ 门判拒** | **PASS** | 单元层：`count_retrieved_sources == 0`（组合根供给**不能**伪装成检索来源）；e2e 层：`plan` 判拒且判词 `0 < 1 retrieved sources (1 >= 1 sources)`（计数维仍满足） |
| AC-3n | **反编造门**未被削弱 | **PASS** | `_input_evidence` 的内容校验（`meta` 非空 + `verify()`）一字未改；跨相那条**另起**一条路径（`meta` + `verify` 同一严格口径），且 origin 是**有向边**（`cross-phase:{读取方}:{产出方产物}`）⇒ 不与产出方自己的 `GENERATED` 记录相撞、也不覆盖它 |
| AC-4 | **接线**：`grounded_report_chain_v1.yaml` 的 `plan` 相 | **PASS** | `inputs: [input-brief:real_research_v1, scouting:scouting_report]`；编译期解析为 `(scouting, scouting_report, RETRIEVED)`，**零 findings** |
| AC-5 | **离线复现**：覆盖由 `0 < 1` 变成立 | **PASS** | run **`SUCCEEDED`**（此前稳定 `FAILED`）；`plan` 的提示词 710 字符、带三个真标识；`scratch/_ec04_probe3.py` |
| AC-6 | **live 实跑**（真实中转站 + 真容器 + 真模型） | **PASS** | run **`SUCCEEDED`**；`research_report_plan` 的提示词带检索段；**计划正文引用了全部 3 条标识**（`42853652` + 两个 DOI）；归档 `evidence/GOAL-20261016-081-ec04-live-citations.txt` |
| AC-7 | **零回归** | **PASS** | application + integration + architecture **1399 passed, 1 skipped**；报告链/检索/多角色 e2e **20 passed**；`research_report_chain_v1` 一字未动 |
| AC-8 | **规模与静态门** | **PASS** | 规模门 **1267 passed**；`ruff check` 全绿；`ruff format --check` 无改动；全量 `mypy` **1258 files, no issues**；受撞的 `phase_runner.py` / `task_phase_helpers.py` 拆出模块后回到 450 行内（447 / 425） |
| AC-9 | **as-is m0（记录全部写入之后）** | **PASS** | `PASS: profile=m0; 23 deterministic checks`（24 行 `PASS [`，含计数之外的 `release-assets-immutable`；`EXIT=0`） |

## 警告（如实登记）

- **`W-1`**：跨相输入只支持**一层**上游产物引用（不做多跳派生）。多跳需要「产物链的可解析
  闭包」设计，本轮不做、也未声称。
- **`W-2`**：**报告汇编器**与**沙箱实验**两个执行体不消费 `declared_input_artifacts`
  ⇒ 编译期**点名拒绝**给它们声明跨相输入。这不是缺陷掩盖，而是如实边界：一条「声明了但没人读」
  的来源会让覆盖门数到一个不存在的读者。
- **`W-3`**：同一份协议在**离线**夹具与 **live** 上都跑到 `SUCCEEDED`，但两次的检索结果
  **标识不同**（离线是 `OfflineEuropePmc` 的固定语料；live 是真 Europe PMC 的当轮响应）。
  判据比的是「本次 run 的标识」而不是写死的串 —— 这是有意为之，也意味着读数不可跨轮逐字复现。
- **`W-4`**：`W-2`（GOAL 级：内容一致性无人判）与 `W-3`（看到全文不在射程）**仍然成立**。
- **`W-5`**：`R-M1` 未收口 ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」。

## 未覆盖的面

- EC-05 自举收口（验证器进树 + 两树复检 + m0 终态行 + CI 台账）。

## 结论

**PASS**。EC-04 的三条硬要求（形态 / 性质来源 / 门不削弱）各有一条判据与一条按压；
`plan` 格的覆盖两维在**离线**与 **live** 两路上都由真实检索满足，且 live 上模型**引用**了
全部三条标识。两处既有判据（`_input_evidence` 的内容校验、`count_retrieved_sources` 的
「不接受自称」口径）**一字未改**。

残余见上（`W-1`…`W-5`）：多跳跨相、两个不消费声明输入的执行体、跨轮读数不可逐字复现。
