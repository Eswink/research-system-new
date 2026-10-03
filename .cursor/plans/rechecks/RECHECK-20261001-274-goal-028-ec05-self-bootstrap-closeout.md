---
id: RECHECK-20261001-274
slug: goal-028-ec05-self-bootstrap-closeout
title: GOAL-028 EC-05 复检 — 自举收口（验证器进树 + 两树同结论 + m0 23/23 + 台账终态）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-01
updated_at: 2026-10-01
plan_id: PLAN-20261001-273
parent_goal: GOAL-20261001-028
reviewer: root-agent
owners:
  - root-agent
---

## 复检对象

`PLAN-20261001-273`（GOAL-20261001-028 的 cycle 5 子计划）——自举收口。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | 收口验证器进树 + 过四道门 + 本树零 FAIL | **PASS** | `tools/verify_goal028_closeout.py`（**416 行** ≤450）复用 `standard_verdicts`，只写本轮特有断言；本树 `--verdict-only` ⇒ **46 PASS / 0 FAIL**；`tests/tooling` 四道门 **8 passed**；`IN_SCOPE` **纯追加**一条 |
| AC-2 | 两树复检**同结论** | **PASS** | `tools/two_tree_recheck.py --script tools/verify_goal028_closeout.py --script-mode shared --root .` ⇒ `TREE current` 与 `TREE clean` 各 **46 判词**、`sha256` **相同**（`e43cb3b0d718a078885ce46d2e93263a7b759b3ee9030962664569c35c74f2e1`）、`COMPARE identical=True`、**`TWO-TREE PASS` / `EXIT=0`**；留档 `scratch/goal028-c5b-twotree.log`（判词文件二进制写盘由入口负责） |
| AC-3 | as-is m0 **23/23**，跑在记录写入**之后** | **PASS** | 见 GOAL 迭代日志 cycle 5 行与「状态历史」；终态行 `PASS: profile=m0; 23 deterministic checks` |
| AC-4 | 治理与记录面 | **PASS** | `validate.py` = `Cursor 治理验证通过`（含 DOCS-CHECK 与 GOAL/PLAN/RECHECK/MEM 交叉引用）；记录面判据绿；`latest_recheck` 为**仓库相对路径** |
| AC-5 | 台账到终态 + 残余与未覆盖逐条 | **PASS** | CI 台账**逐提交**登记（本轮五批共 **17** 个提交逐条写明自带 run 或结构化覆盖声明）；cycle 4 起该口径由 `tools/audit_goal028_ledger.py` **机器复核**（本批实测 `checks=6 failed=0`）；未覆盖五条与残余逐条在位 |

## 复检发现（三处判红 + 一处两树首跑 RED，都在**验证器自身 / 自举时序**，已处置）

1. **例数下界量纲错**：首版按 `pytest` **收集**数写（参数化让收集数更大：13 定义 → 14 收集），
   而验证器用 `def test_` **声明**数 ⇒ 两条判词判红。改按**声明数**（并抽 `_count_defs` 与
   docstring 注明两个量不是一个量）。
2. **`IN_SCOPE` 自举时序**：验证器首次跑时自己还没进 `IN_SCOPE` ⇒ 判红（正确行为）⇒ 追加。
3. **子计划/复检路径指向旧件**：写的是 `RECHECK-20261001-270`（cycle 2 的）⇒ 改指本轮
   `RECHECK-20261001-272`。
4. **规模门判红 `deliverable_verdicts`（>50 行）**：按仓内形态**拆函数**
   （`_binding_face_verdicts` + `_retrieval_and_ledger_verdicts`），**未**用 `noqa` 掩盖。
5. **两树首跑 RED = 正确行为**：干净树是**已推送** HEAD 的 checkout，还不含未提交的验证器
   ⇒ 两条判词点名「文件不存在」。提交推送后**复跑 ⇒ 两树 PASS 且 `sha256` 相同**。
   （这条同时是两树入口**有效性**的正控制：它确实在比对两棵树，而不是恒定判绿。）

## WARNINGS（逐条登记，本 EC 不消解）

- **`W-1`｜收口验证器只覆盖「本轮交付物 + 标准面」**：它证的是交付物在树与结构在位，
  **不**证产品运行语义（那由各 EC 的行为判据承担）。射程边界承 GOAL-023 `W-1` 的有界射程。
- **`W-2`｜前四轮的 `W-NN` 族原样保留**（EC-01 五条 / EC-02 六条 / EC-03 五条 / EC-04 两条），
  本 EC 不消解任何一条。
- **`W-3`｜两树复检的干净树是 `HEAD` 的 checkout**：未提交的工作树内容**不会**被第二棵树看到
  ⇒ 收口必须**先提交再跑**（本轮首跑 RED 就是这条的现实例证）。

## 未覆盖范围（承继，逐条在位）

1. **读面未认证** —— GET / HEAD 无认证（GOAL-019 判词 (i)：保护范围**只有写面**）；
2. **多租户未做** —— 无 organization scope、无逐调用方身份（单 token ⇒ 单主体）；
3. **BOLA·BFLA 未做** —— 无对象级 / 功能级鉴权；
4. **部署面未验证** —— 跨副本 / 真实 broker / 真实 worker 集群 / 外部队列只在登记面；
5. **`R-M1` 未收口** —— Mimosa 钩子 `scanner_enobufs` 未得完整结论 ⇒ **不得**据此宣称
   项目安全。

**可靠性口径**：本 EC 不涉及投递语义；本仓**明确否认**「恰好一次」，口径只能是
at-least-once + idempotency + deduplication。

## 结论

GOAL-20261001-028 的 **EC-05 达成**：收口验证器进树（416 行、复用标准判词、`IN_SCOPE`
纯收紧）、**两树逐行相同 + `sha256` 相同**（`TWO-TREE PASS`）、as-is m0 **23/23**（记录写入后）、
治理与记录面绿、CI 台账**逐提交**到终态（cycle 4 起由新工具机器复核）。
三条 `W-NN` 如实登记。**五条 EC 全 PASS** ⇒ 本 GOAL 具备收口条件。
