---
id: MEM-20260930-176
title: "「不声明网络域 ⇒ GENERATED」不是普遍规律：europe_pmc 把声明同时当运行期出口门，声明为空时它在触网前拒绝而不是降级；运行链接线是声明面（不接线 ⇒ 零观测 + 零请求 + 覆盖性质维度判拒）"
status: ACTIVE
created_at: 2026-09-30
updated_at: 2026-09-30
scope: repository
confidence: 0.90
review_after: 2027-03-30
source_plans:
  - .cursor/plans/tasks/PLAN-20260929-259-goal-027-ec03-capability-into-the-run-chain.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260930-260-goal-027-ec03-capability-into-the-run-chain.md
supersedes: []
tags: [run-chain, trust-label, url-policy, read-face, claim-relation, press-test, goal-027, ec-03]
---

## 做了什么

把新接入的文献能力（EC-01 的 `europe_pmc` / EC-02 的 MCP server）接进**运行链**并取证。
四条**实测**得到的事实：

- **「不声明网络域 ⇒ `GENERATED`」只对「不触网」的 provider 成立**：
  `_trust_label_for`（`packages/application/run_orchestration/phase_capabilities.py`）确实是
  唯一判定点（`network_domains` 非空 ⇒ `RETRIEVED`，否则 `GENERATED`），但 `europe_pmc`
  的 URL 策略（EC-01 的净增量）把**同一份声明**同时当运行期出口门 ⇒ 声明为空时它在
  **触网前拒绝**：`europe pmc host 'www.ebi.ac.uk' is outside the declared network_domains []`
  （零请求）。⇒ `GENERATED` 那一向必须用**不触网**的 provider 取证
  （本 EC 用 stdio MCP provider）。**首版判据按普遍规律写 ⇒ 实测判红**。
- **读面只经 claim relations 投影**：`GET /runs/{id}/evidence` 走
  `services/api/run_evidence.py::evidence_of_run`（claims → relations → evidence）。
  `result_handler.register_session_result` 若**不**把 `deps.retrieved_evidence` 并进
  `_LedgerBatch.extra_evidence_ids` ⇒ 检索来源在读面**完全不可见**（按压 P-G：
  只有读面那条判据转红，其余 10 passed ⇒ 断言精确）。
- **运行链的「接线」是声明面**：协议里 `capability_execution: run_chain` 是**声明**，
  装配方还得**真的把 provider 接上**（`CapabilityDeps.providers`）。两件事**都必须做**：
  只改协议声明（P-F）⇒ 读面静默退化；只接线不改声明 ⇒ 能力步根本不执行
  （`run_chain_tool_ids` 返回空）。去掉接线 ⇒ 零工具观测 + **零请求** + 覆盖判据的
  **性质维度**判拒（判词 `retrieved sources`）⇒ run `FAILED`。
- **两步链的参数真的来自数据**：`arguments_from_input`（brief 的 `retrieval.query`）→
  `ids_from_previous`（**检索响应里返回的**真 PMID）。离线传输里逐条可见：
  第 1 条请求 = query 串、第 2/3 条 = `EXT_ID:<真 PMID>`。**缺一 fail closed 且零请求**
  （抹掉 query ⇒ `retrieval.query` 点名；零命中 ⇒ `'ids'` 点名、不再发读取请求）。

## 为什么这样做

- **判据不能从产品代码倒推语义**：我写了「声明为空 ⇒ `GENERATED`」这条**看上去合理**的
  断言，实测被判红 —— 因为 `europe_pmc` 的声明有**两个**消费者（URL 门 + 性质标签），
  且前者的语义是 fail closed。⇒ 凡「同一个字段被多个消费者读且各自有语义」的地方，
  断言必须先探针实测、再写进判据（承 [[model-absence-has-no-own-failure-category]] 同族纪律）。
- **`register_evidence` 与 `attach_relation` 是两件事**（承 [[evidence-read-face-claim-relation]]）：
  本 EC 把这两件事的因果**成对**测出来（接上 ⇒ 四列可读 + `SUCCEEDED`；去掉 ⇒ 读面空 +
  `FAILED` 且判词点名性质维度）。
- **按压要压共享判定点**：P-H 架空的 `_trust_label_for` 让**既有两份**判据同时转红
  ⇒ 这既证明判据有牙，也证明本 EC 没有绕开既有语义另起一套（这是「新能力接上旧链」的
  正确形态）。

## 怎么做与复现

1. 跑本 EC 判据：
   `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_literature_chain_run_offline.py -q`
   ⇒ 11 passed（离线；`egress guard: judged N connection attempt(s); blocked 0`）。
2. 按压配方：协议 `run_chain` → `session`（P-F）；`result_handler.py` 的
   `extra_evidence_ids` 去掉 `deps.retrieved_evidence`（P-G）；
   `_trust_label_for` 判定架空（P-H）。复原后 raw `sha256` 与基线相等：
   协议 `4ad4ade4…b9f87` / `result_handler.py` `37634dda…2a6c366` /
   `phase_capabilities.py` `e0dc7699…3ea5b2f2`。
3. 读面取证：`GET /runs/{id}/evidence` 的每行取 `id` / `source_ref` / `content_digest` /
   `source_trust_label` / `tool_refs`（后两个字段由 GOAL-010/011 补上；此前没有任何读面）。

## 适用边界

- 本 EC **零产品代码改动**（只消费既有产品面）；新增的是协议 + 判据 + 支持件。
- 新协议（`real_literature_chain_v1.yaml`）与既有 `real_retrieval_research_v1.yaml`
  **并存**：同读一份 brief、检索策略不同（本协议两步链含按 id 精确取记录）；
  **不**声称谁替代谁。
- `ids_from_previous` 的点分路径只覆盖**单层**信封（`structured.ids`）；更深嵌套未测。
- `network_domains` 的运行时出口执法只覆盖**声明它的** provider（仓内无全局出口网关）
  ⇒ 不得据此宣称「全仓出站已受控」。
- **不得**据此宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为「恰好一次」
  （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。

## 来源

- `PLAN-20260929-259`（GOAL-027 EC-03）与 `RECHECK-20260930-260`（§3 / §4 / §5 / §6）；
- 判据与支持件：`tests/e2e/test_literature_chain_run_offline.py`、
  `tests/e2e/literature_chain_support.py`；协议 `examples/protocols/real_literature_chain_v1.yaml`；
- 相关代码：`packages/application/run_orchestration/phase_capabilities.py`（`_trust_label_for` /
  `_arguments`）、`packages/application/run_orchestration/result_handler.py`
  （`register_session_result` 的 relations）、`services/api/run_evidence.py`（读面投影）、
  `adapters/research_tools/europe_pmc_runtime.py`（`assert_url_allowed`）；
- 同族记忆：[[evidence-read-face-claim-relation]]（只登记不挂 relation ⇒ 读面看不到的**档案**，
  本条把它做成**成对判据**）、[[retrieved-source-and-coverage-nature]]（两维覆盖：
  计数 + 性质）、[[press-tests-need-real-failures-not-skips]]（按压纪律）、
  [[model-absence-has-no-own-failure-category]]（分类先实测）、
  [[mcp-envelope-needs-a-path-for-chained-ids]] 同族（EC-02 的信封点分路径）。
