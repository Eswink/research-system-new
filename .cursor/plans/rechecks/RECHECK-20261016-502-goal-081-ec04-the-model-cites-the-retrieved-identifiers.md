---
id: RECHECK-20261016-502
slug: goal-081-ec04-the-model-cites-the-retrieved-identifiers
title: GOAL-081 cycle 3 复检 — 真实 run 上模型引用检索标识（EC-04）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-16
updated_at: 2026-10-17
plan_id: PLAN-20261016-501
parent_goal: GOAL-20261016-081
reviewer: root-agent
owners:
  - root-agent
---

# RECHECK-20261016-502 — GOAL-081 cycle 3

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | **live 判据在树且默认门 skip** | **PASS** | `1 skipped`（理由逐字：开关未开 / runtime 未配 / 凭据不可解析） |
| AC-2 | **判据点名「写计划的会话」** | **PASS** | 断言 `sections_by_contract["research_report_plan"]` 非空 —— 只判「某个会话有」会漏掉实测形态（下游 `multi_role_review` 有、plan 没有） |
| AC-3 | **检索标识**确实**进了提示词** | **PASS** | 真实 run 上三个真标识逐字在场（`42781891` / `10.12688/f1000research.180013.2` / `10.31234/osf.io/w7xpq_v2`），543 字符那一段；归档 `evidence/GOAL-20261016-081-ec04-evidence.txt`（`CR=0`） |
| AC-4 | **模型引用标识** | **未达成**（EC-04 记为未通过并点名阻塞点） | 计划正文**零引用**（PMID 形态零命中）。**根因两条，都已实测定位**（见下） |
| AC-5 | **新增带侦察相的协议**（`grounded_report_chain_v1`） | **PASS** | 离线实测：`scouting` 相**成功**（6 条证据 + `scouting_report` 制品）；`plan` 相被判拒 `EVIDENCE_COVERAGE: 0 < 1 retrieved sources` —— 即 **EC-04 的阻塞点 (b)** |
| AC-6 | **已排除的假解法** | **PASS** | 把 `with_retrieval_context` 移到运行链之后 ⇒ 对 (a) **无效**、且会破坏 GOAL-078 的「上游会话为空」反证臂 ⇒ **已回退**（`git checkout`，7 条 e2e 复绿） |
| AC-7 | **CI 台账逐提交** | **PASS** | `e87f1f38` 两 job `failure`（新 live 模块漏登记 —— **同族缺陷第二次**）已如实登记；`667a01d5` 八 job 全绿 |
| AC-8 | **既有判据零放宽** | **PASS** | 规模门 **1276 passed**；`research_report_chain_v1` 一字未动；GOAL-078 的判据只**加**不改 |

## 警告（如实登记）

- **`W-1`**：**EC-04 未达成** —— 按 GOAL 的降级梯记为**未达成 + 点名阻塞点**，**不**伪造。
- **`W-2`**：**同一族缺陷（新 live 模块漏登记）第二次出现** —— GOAL-080 那一轮已经记过一次，
  本轮仍漏。⇒ 结论：该纪律（新增 live 套件要同改**两处清单 + 模块内口令行**）必须有
  **检查表条目**，不能靠记忆。
- **`W-3`**：我一度把「求值点前移」当成解法并写进记录，**实测无效后回退** ——
  记录已按实测更正（先前那段措辞已改写为两条真根因）。
- **`W-4`**：`grounded_report_chain_v1` 是**新增**协议，尚未被任何 live 判据跑通
  （它在 `plan` 相被覆盖门拒）⇒ 它是**资产的中间态**，不是「已可用的协议」。
- **`W-5`**：`R-M1` 未收口 ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」。

## 未覆盖的面

- EC-04 本身（阻塞）；EC-05 自举收口。

## 无可复用事实需要另建工程记忆

本轮两条教训（**「运行链证据在上下文装配时无 claim 关系」** 与
**「覆盖门只数本任务证据」**）已写进 GOAL 的 `blocker` 与 cycle-3 修复记录；
是否需要独立记忆条目取决于下一 cycle 的结论 —— 现在登记为**候选**。

## 结论

**PASS_WITH_WARNINGS。** 本 cycle 的产出**不是**「EC-04 达成」，而是**把它从「不知道」变成
「两条实测根因 + 已排除的假解法 + 一份带侦察相的新协议」**：

- **(a)** 运行链证据在上下文装配时**没有 claim 关系**（`register_tool_evidence` 只登记
  不挂关系，而读面口径只认 claim→relation）⇒ 同一 phase 看不见自己刚取回的内容；
- **(b)** 立题格的覆盖门**只数本任务**的证据 ⇒ 上游 `scouting` 相取回的来源不计入。

**EC-04 = 未达成（点名阻塞点）**；下一 cycle 需要在「上游产物能否作为下游声明输入」与
「覆盖门是否按 run 作用域计数」之间做**设计取舍**（不得为过判据放宽门）。
