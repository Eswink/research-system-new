---
id: RECHECK-20261015-476
slug: goal-078-ec04-live-run-on-the-new-relay
title: GOAL-078 cycle 4 复检 — 新站真实 run 上检索内容到达会话（EC-04）
status: COMPLETED
result: PASS
created_at: 2026-10-15
updated_at: 2026-10-15
plan_id: PLAN-20261015-475
parent_goal: GOAL-20261014-078
reviewer: root-agent
owners:
  - root-agent
---

# RECHECK-20261015-476 — GOAL-078 cycle 4

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | live 判据断言**上下文到达会话** | **PASS** | `tests/e2e/retrieval_context_support.assert_the_context_reached_sessions`：读面上下文载荷**非空** + 逐条四列在场 + `refs ⊆` 本次 `RETRIEVED` 证据 |
| AC-2 | **真实 run 实跑通过** | **PASS** | **1 passed in 72.64s**（`RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1`）；run `218280b6-5aa5-43f8-9556-3981c2fe6033`，终态 `SUCCEEDED` |
| AC-3 | **活检索的真标识进了下游会话** | **PASS** | 落盘读数（`evidence/GOAL-20261014-078-ec04-context-evidence.txt`）：下游 `multi_role_review` 的上下文 **4 条**，各带真标识 —— `42781891`（PhotoChem）、`10.12688/f1000research.180013.2`（SwissRN Hackathon 2025）、`10.31234/osf.io/w7xpq_v2`（Ten simple rules）；`token_allocation=390` |
| AC-4 | **同源**（会话值 == 读面值） | **PASS** | 会话 spec 的 `retrieval_digest = sha256:8cfa62f321e2cd77…`；读面上那件制品的 digest **同一串**（判据断言「在场于读面 digest 列表」） |
| AC-5 | **两向读数**（按时刻装配） | **PASS** | 上游 `research_report_plan` 的上下文 **空**（`refs: 0`、`digest: None`）且它的制品带**点名理由** `run … has no retrieved evidence to place in the context` —— 与下游非空形成对照 |
| AC-6 | 上下文面**记档** | **PASS** | run id / 逐条 ref / digest / 检索证据 id 全部写进 `evidence/GOAL-20261014-078-ec04-context-evidence.txt`（1456 字节、`CR=0`） |
| AC-7 | 降级梯如实 | **PASS** | **未触发降级**：真实模型会话（立题 / 评审）+ 真实检索（Europe PMC）+ 真实容器实验都在同一 run 里跑到终态 |
| AC-8 | 既有判据零放宽 | **PASS** | 产品代码**零改动**（本 cycle 只扩判据与支持件）；离线 e2e / 接缝 / 读面判据均未改 |

## 警告（如实登记）

- **`W-1`**：**EC-05（自举收口）仍未完成** —— 验证器 / 两树 / m0 终态 / 治理 / 台账属 cycle 5。
- **`W-2`**：live 判据**只跑一次** run（不重试、不批量）；模型侧可用性波动会让重复运行结果不同
  —— 本记录是一次**特定**实跑的事实（与 GOAL-077 `W-5` 同款）。
- **`W-3`**：上下文**四条的来历**（如实）：`literature_read` 那一条是关键的两步链结果；
  `literature_search` 的两条是检索步的结果。**同一篇文献可能以 PMID 与 DOI 各出现一次**
  （工具结果里就有这两列）⇒ 条数 ≠ 文献数。
- **`W-4`**：**不判模型行为** —— 本 EC 证「内容进了会话规格」这一事实；「模型读了它」
  需要观测面（承 EC-02 的 `W-4`）。
- **`W-5`**：进上下文的是**有界摘录**（§10）；`token_allocation` 是字符数量级近似。
- **`W-6`**：`R-M1` 未收口 ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」。

## 未覆盖的面

- 自举收口（EC-05）；
- 模型侧「读没读」的行为观测（`W-4`）。

## 无可复用事实需要另建工程记忆（本轮教训已并进既有条目）

本轮的可复用面**已并进** `MEM-20261014-221`：live 判据若要证**装配面**的事实
（而不是最终产物），取证点应当放在**runtime 的 `create_session`**（那是产品交给执行体的
那一刻）——包一层记录器即可，**产品代码零改动**；而**同源**要用「同一份字节」证
（写盘字节即 digest 的源），不要用两次计算比。两条都在本轮被真的用上。

## 结论

**PASS。** EC-04 成立：**新站**上的一次真实 run 里，**活检索取得的内容真的进了下游会话**
（4 条真标识、`token_allocation=390`），且「进了什么」在**既有读面**上读得出来
（两件上下文制品：下游 4 条 / 上游 0 条带点名理由），两处**同源**（digest 逐一对应）。
上游会话拿到空上下文（它开工时检索还没跑）—— 这证明上下文是**按时刻装配**的，
不是一次性全量注入。
