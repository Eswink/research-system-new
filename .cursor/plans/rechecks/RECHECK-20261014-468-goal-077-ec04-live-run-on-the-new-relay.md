---
id: RECHECK-20261014-468
slug: goal-077-ec04-live-run-on-the-new-relay
title: GOAL-20261014-077 cycle 2 复检 — 新站真实 run 跑完整链并留下报告（EC-04）
status: COMPLETED
result: PASS
created_at: 2026-10-14
updated_at: 2026-10-14
plan_id: PLAN-20261014-466
parent_goal: GOAL-20261014-077
reviewer: root-agent
owners:
  - root-agent
---

# RECHECK-20261014-468 — GOAL-077 cycle 2（EC-04）

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | live 判据在树且门控正确 | **PASS** | `tests/e2e/test_research_report_chain_live.py`（`requires_live_llm`）；无开关/无 runtime/无凭据三态 ⇒ **如实 skip**（实测 skip 理由逐条点名三项） |
| AC-2 | **真实 run 跑到终态 `SUCCEEDED`** | **PASS** | 实跑 **1 passed in 151.89s**；run `02c0adf5-b59c-4726-ac12-73f8d7ef4cc4`，协议 `research_report_chain_v1_0_0`，`manifest_digest` 在场（冻结真发生），失败面为空 |
| AC-3 | 报告制品在位且内联 markdown | **PASS** | `{run_id}:research_report.md` 在 `GET /runs/{id}/artifacts` 上；`GET /artifacts/{id}/content` ⇒ 200 且 `content-type` 含 `text/markdown` |
| AC-4 | 四节齐全 | **PASS** | 四条 `SECTION_HEADINGS` 逐条在位（见落盘正文） |
| AC-5 | **活检索的真标识进报告** | **PASS** | 报告第 2 节含三条**本次活检索取得**的真标识：`42781891`（真标题 `From reproducibility to comparability in computational photochemistry: lessons from the PhotoChem explorer prototype.`）、`10.12688/f1000research.180013.2`（SwissRN Hackathon 2025）、`10.31234/osf.io/w7xpq_v2`（Ten simple rules…）——判据另断言这些标识与 `GET /runs/{id}/evidence` 的检索证据**逐条一致** |
| AC-6 | **真容器实验的指标进报告** | **PASS** | 报告第 3 节 8 条实测指标（`agreement=true` / `comparison_reduction_ratio=7990.0` / `n_items=800` / `pairwise_comparisons=319600` / `seed=7` …），判据断言与 `GET /runs/{id}/experiments` 的落库值**逐字相同** |
| AC-7 | 评审判词可读且是真实决定 | **PASS** | 报告第 4 节 `决定: PASS` + 逐字判词 `ARTIFACT_EXISTS: artifact review_decision exists; EVIDENCE_COVERAGE: 1 >= 1 sources` + `contract=multi_role_review` |
| AC-8 | 报告落盘（交付面） | **PASS** | `scratch/goal077-ec04-02c0adf5-b59c-4726-ac12-73f8d7ef4cc4.md`（2341 字节，人类可读） |
| AC-9 | 降级梯如实 | **PASS** | **未触发降级**：真实模型会话（立题 / 评审两个 phase）与真实检索（Europe PMC）、真实容器实验都在同一 run 里跑到终态 |

## 两处装配侧缺口（本轮**实测**，如实登记）

1. **两件 REST provider 都要注册可探测实例**：本协议的能力面同时含 `europe_pmc`（运行链）
   与 `ncbi_eutils`（评审格的会话绑定）。只注册一件时另一件的健康是三态里的 `UNKNOWN`，
   而冻结对「未获接受通道的 EXECUTE 风险警示」**点名拒冻**。实测判词逐字：
   `cannot freeze manifest before a passing preflight: WARNING TOOL_HEALTH_UNPROVEN
   (provider:ncbi_eutils) is not an explicitly allowed EXECUTE risk; ...`（`manifest_digest=None`
   是它的可观测后果）。补上实例后冻结真发生（`manifest_digest` 在场）。
2. **出厂会话工具绑定表只覆盖 canonical 读面**：本协议把 `literature.search` /
   `literature.read` 声明为**会话工具**（评审格四条绑定之一），而协议声明的是**名字**，
   「名字桥到哪个 provider 的哪个 tool id」归**装配方**。实测（未补时）失败逐字：
   `task … failed: "ToolDefinition 'literature…' is not registered"`。
   本判据以装配方身份补一张实现表（与出厂绑定走**同一个** `make_tool_invoker` /
   `execute_tool_call`）⇒ 会话起得来、run 到 `SUCCEEDED`。
   **这与 GOAL-028 登记的 `W-1` 是同一类缺口**（组合根不自带「工具名→实现」表），
   **不改产品代码**（诚实边界）。

## 警告（如实登记）

- **`W-1`**：**EC-05（自举收口）仍未完成** —— 验证器 / 两树 / m0 终态 / 治理 / CI 台账
  属 cycle 3。
- **`W-2`**：报告抬头标「**汇编时状态** `RUNNING`」（汇编在 run 内发生，终态尚未产生）——
  这是如实读数，**不是**缺陷；读者要终态须读 `GET /runs/{id}`。
- **`W-3`**：报告的来源标识取自**工具结果内容**（`articles[].pmid` / `doi` / `title`），
  因而报告里同时出现 PMID 与 DOI 两种形态（同一篇的两个标识）——这是工具结果里就有的两列，
  不是重复计数。判据读的是「报告里的标识 ⊆ 证据读面里出现过的标识」。
- **`W-4`**：`R-M1` 未收口 ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」。
- **`W-5`**：本轮 live 只跑**一次** run（不重试、不批量）；模型侧可用性波动可能让重复运行
  结果不同 —— 本条记录的是一次**特定**实跑的事实。
- **`W-6`**：装配侧两张表（provider 实例 + 会话工具实现表）由**判据侧**给出；
  产品组合根今天仍不自带（`F-10` / `W-1` 同一家族的缺口），如实登记。
- **`W-7`（最要紧的一条：push 后的 CI 真红）**：本 EC 的**第一版** live 判据
  （提交 `c0f793ad`）在 CI 上判**红**，三处，**全部是判据文件自身**的问题、与产品代码无关：
  ① `python/typecheck` —— `_live_deps` 里 `deps.artifacts` / `deps.runs` 是
  `X | None` 而我没有收窄（本地当时**没跑 mypy**，只跑了 ruff）；② `python/tests` ——
  `test_live_switch_is_single_source` 的两条清单（`LITERAL_MENTIONS` / `LIVE_MODULES`）
  要求新的 live 模块**显式**登记；③ 同一条 —— `_live_deps` 58 行超 50 行函数门
  （我在本地修过一次 71 行的用例，但**没有重跑规模门**）。
  **处置**：三处逐条修复（本文件与 GOAL 的「修复记录」逐条写明），并**在修复后重跑
  live 实跑**（`1 passed in 62.36s`）。**教训（已进纪律）**：本地只跑定向套件不够 ——
  `mypy` / 规模门 / 同源清单判据都在**全量门**里；push 前必须跑到 m0。
- **`W-8`**：本轮的**两树复检**在 **`c0f793ad` 树上**跑过一次（判词一致，RED 项两树相同），
  修复后需要在**新 tip** 上重跑 —— 属 cycle 3。

## 未覆盖的面

- 自举收口（EC-05）；
- 报告的**叙述性撰写**（模型写正文；报告域的再下一级）；
- 活检索结果进模型上下文（检索域的下一级）。

## 结论

**PASS。** EC-04 成立：**新站真实中转站**上的一次完整研究（4 phase：立题 + 实验 + 评审 +
报告）跑到 `SUCCEEDED`，报告中含**活检索**取得的真标识与真标题、**真容器**的实测指标、
**真实评审**的逐字判词；报告正文落盘为人可读的一页 markdown。装配侧补的两处（provider 实例
与文献会话工具实现表）**只补执行体、不注入判词**，且都有实测的失败形态作为「不补就真红」的
证据。
