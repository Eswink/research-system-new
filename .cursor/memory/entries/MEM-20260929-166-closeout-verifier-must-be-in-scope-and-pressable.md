---
id: MEM-20260929-166
title: "收口验证器自己也必须进射程并被按压：否则它是唯一不过门的受判物；复检要「重算」而不是复述清单，且干净树须是已提交的收口树"
status: ACTIVE
created_at: 2026-09-29
updated_at: 2026-09-29
scope: repository
confidence: 0.9
review_after: 2027-03-29
source_plans:
  - .cursor/plans/tasks/PLAN-20260929-243-goal-025-ec04-closeout-two-tree-self-bootstrap.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260929-244-goal-025-ec04-closeout.md
supersedes: []
tags: [closeout, verifier, in-scope, pressable, recompute, two-tree, goal-025, ec-04]
---

## 做了什么

GOAL-025 cycle 4 用「标准收口断言集 + 本轮特有断言」的机器收口：新增
`tools/verify_goal025_closeout.py`（447 行 / **37 判词**），把它**显式**加入
`tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（4 → 5 条，**纯收紧**），
并让它自己按压（三条：改 GOAL 的 EC 状态 / 改 `latest_recheck` / 往派生面塞未登记路由）。

## 为什么这样做（为什么值得记）

- **验证器是唯一「不过门」的受判物的风险**：`tools/` **不在** `PRODUCT_ROOTS` ⇒ 收口验证器
  天生不过 ruff / format / mypy / 规模四道门。若不显式把它点进射程，**最该被检查的那个脚本
  反而无人检查**（GOAL-023 EC-02 的形态）。入库清单必须是**源码里的必备清单**（下界），
  不是文档里的一句点名 —— 且「必备清单 ⊆ 推导射程」这条断言是**单调**的 ⇒ 加一条是收紧。
- **复检要重算，不要复述清单**：`ec03` 不读「派生面有 68 条」这句话，而是**重新算**
  （读树内 OpenAPI 快照 JSON + 从两个清单源码里取 `FrameworkRoute(...)` / `ReadRouteRule(...)`
  的第一个字面量参数，**不执行**被检模块）⇒ 清单漂移会被算出来，而不是被复述过去。
  同理 `ec01` / `ec02` 断的是**分区形状与下界**（受判 2 / 豁免 3 / 不发射 1、正控制 6 / 机械 2），
  不是「文件存在」。
- **两树复检的干净树必须是「已提交的收口树」**：干净 checkout 由 `git worktree add --detach <ref>`
  产生 ⇒ 若在提交**之前**跑，干净树就是**收口前**的树，那些读记录（GOAL / RECHECK / 子计划）
  的判词会在两棵树上得到**不同**结果（甚至直接判红）。正确顺序是
  **写记录 → 门 → 提交 → 两树**，并把两树结果以**补记**落回 GOAL（承 GOAL-024 的收口补记做法）。
- **时序口径写进判词**：`EC-04` 的判词由本验证器产出 ⇒ 那条断言接受 `PASS ∪ PENDING`
  并在 detail 里说明「这是时序，不是放宽」；否则验证器永远无法在一次运行里自洽。

## 怎么做与复现

1. **进树 + 入射程**：新脚本 `tools/verify_<goal>_closeout.py`（`--root` / `--verdict-only`，
   判词纯净、路径无关），并把路径写进 `IN_SCOPE`；跑 `tests/tooling/` 三件套确认
   `IN_SCOPE ⊆ scope()` 且四道门对它生效。
2. **复用公共面**：只调用 `tools/closeout_recheck_assertions.py` 的
   `standard_verdicts` / `Verdict` / `emit`，**不重写**一行公共断言。
3. **特有断言**：每轮只写自己那几条（分区 / 下界 / 集合相等 / 状态取值 / 登记在位），
   且都**机械可算**（AST / JSON / 前端文件解析），不靠散文。
4. **按压**：改**被判对象**（GOAL 状态、`latest_recheck`、清单字面量）⇒ 必须判红且**点名**；
   逐字节复原（raw `sha256` + 二进制读写）。
5. **顺序**：写记录 → 记录面判据 → 全量门（m0）→ 提交 → 两树复检（`--script-mode shared`）
   → 补记两树结果。

## 适用边界

- 收口验证器是**自洽性**判据：它证明「清单形状 / 集合 / 状态 / 登记」当下成立，
  **不**证明被点名的判据在真实环境不再会红。
- `ec03` 的集合重算**不执行**被判据模块的函数 ⇒ 模块内部逻辑被改坏而清单不变时，
  验证器看不见（由该模块自己的判据负责）。
- 「残余在位」是字符串级断言：**登记在位 ≠ 已处置**。
- 两树复检只覆盖**判词层**的一致性；两棵树的其他差异（未追踪文件、环境）不在比对面。
- **不构成**任何"项目安全"结论（`R-M1` 未收口）。

## 来源

- 交付：`tools/verify_goal025_closeout.py`（447 行 / 37 判词）、
  `tests/tooling/test_tooling_scripts_meet_product_gates.py`（`IN_SCOPE` 4 → 5）
- 复检：RECHECK-20260929-244（`PASS_WITH_WARNINGS`；`W-1`…`W-5` 就是本条的边界）
- 前置：MEM-20260928-156（受判集合非空）、MEM-20260928-160（射程不许靠并集掩蔽）、
  MEM-20260927-152（按压 / 复原必须二进制读写）、MEM-20260925-139（收口要两树 + 两终态行）
