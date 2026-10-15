---
id: RECHECK-20261015-486
slug: goal-079-ec05-closeout-recheck
title: 独立复检：GOAL-20261015-079 EC-05 自举收口（两树 + 归档 + m0 + 治理 + 阶梯记账）
plan_id: PLAN-20261015-485
parent_goal: GOAL-20261015-079
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-15
updated_at: 2026-10-15
verify_paths:
  - path: 当前工作树（含 cycle 1…5 全部交付与记录）
    evidence: .cursor/plans/goals/evidence/GOAL-20261015-079-verdict-current.txt
  - path: 干净 checkout（`git worktree add --detach HEAD`，同一份断言集）
    evidence: .cursor/plans/goals/evidence/GOAL-20261015-079-verdict-clean.txt
owners:
  - root-agent
---

# RECHECK-20261015-486 — GOAL-20261015-079 EC-05 独立复检

复检对象：`PLAN-20261015-485`（自举收口）。独立重跑下列机械面，不引用 PLAN 结论当证据。
**`verify_paths` 声明：2 路**（本树 + `--base-ref` 的干净 checkout，同一份断言集）。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | **收口资产进树**（断言集 + 验证器 + 两处射程） | **PASS** | `tools/goal079_closeout_assertions.py`（37 条）+ `tools/verify_goal079_closeout.py`（78 条判词：标准 18 + 自有 37 + 记录面 22 + `self-loading` 1）；两处射程**纯收紧**（`IN_SCOPE` / `_VERIFIERS` 各 +1，只增不删；家族判据 **9 passed**） |
| AC-2 | **本 cycle 抓到的同族缺陷已修**（本记录**唯一的独立发现**） | **PASS** | `verify_goal078_closeout.py` 的常量与加载行**双双**写着 `goal077_closeout_assertions.py` ⇒ 29 条自有断言**从未运行**（078 归档 73 条判词里零命中，逐条 grep）；修后**真跑 29 条、0 判负**（68 = 18 + 29 + 21） |
| AC-3 | **缺陷形态已机器封死** | **PASS** | 家族判据加**第三项对拍**（`declared == loaded == 自己那份`）+ 反向反例「自洽但非己有」；自指判词改为**按本文件名推**应载名（写死版在构造上不可能再通过） |
| AC-4 | **按压两处红 + 逐字节复原** | **PASS** | `scratch/goal079c5_press.py`：`BASELINE family_green=True / verifier_green=True` ⇒ `PRESSED family_red=True / verifier_red=True` + `sha 复原一致=True`；归档 `evidence/GOAL-20261015-079-c5-ownness-press.txt`（1092 B、`CR=0`） |
| AC-5 | **两树复检** | **PASS** | `tools/two_tree_recheck.py --script tools/verify_goal079_closeout.py --script-mode shared --base-ref HEAD` ⇒ **`TWO-TREE PASS`**：两路各 **78** 判词、`sha256` **相同** `2c9121ae5a0d3d1a87e93348ba7b131249a4c2c2eb2f7d4c989f0455df7c1774`、`COMPARE identical=True`；两份判词归档 `.cursor/plans/goals/evidence/GOAL-20261015-079-verdict-current.txt`（当前树）与 `.cursor/plans/goals/evidence/GOAL-20261015-079-verdict-clean.txt`（干净 checkout）**进树**（各 **3285 B / 78 行 / `CR=0` / `cmp` 逐字节相同**，0 `FAIL`） |
| AC-6 | **as-is m0 23/23**（在全部记录写入之后） | **PASS** | 终态行 `PASS: profile=m0; 23 deterministic checks`；零 `FAILED` |
| AC-7 | **治理 + 宪章判据** | **PASS** | `validate.py` = `Cursor 治理验证通过`；三条 MAINLINE 判据（程序面 / 归档连续性 / **阶梯推进**）全绿 |
| AC-8 | **阶梯记账**（★ EC-05 逐字要求） | **PASS** | 宪章 `进展记录` 追加本行（**能力域 = 实验**）+ 「实验」域 `依据 GOAL` 收录 `GOAL-20261015-079` + `下一级是什么` 前移一格 |
| AC-9 | **凭据审计四面零命中** | **PASS** | `tools/credential_audit.py` 四面 `offenders=0` |
| AC-10 | 既有判据零放宽 | **PASS** | 家族判据只**加强**（新加一项对拍 + 一条反例，既有断言一条未删）；两处射程只增不删；产品代码**零改动** |

## 警告（如实登记）

- **`W-1`**：**`R-M1` 未收口** ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」
  （**明确否认**）。
- **`W-2`**：**旧一代验证器未普查**（`LEGACY_INLINE`：断言内联、无外部断言集）——
  第三项对拍对它们**没有可对拍面**。本次是「同族缺陷第二例」，不排除那一代有别的形态。
- **`W-3`**：GOAL-078 的归档判词（73 条）**不会**被重跑 —— 它是**当时的**实测读数
  （跑的是上一轮断言集）；本记录如实说明其构成，**不改写历史归档**（不可变证据）。
- **`W-4`**：本复检的 `verify_paths` 两路都是**同一份断言集**在**同一提交**上的两棵树；
  「断言集内容是否正确」不由两树承担（那由各 EC 的判据承担）。
- **`W-5`**：臂数 > 2 与「哪个臂更好」仍不在射程内（承 EC-02/03/04 的同一残余）。

## 未覆盖的面

- 旧一代验证器的同族普查（`W-2`）；
- 多臂（> 2）与臂间优劣判定（`W-5`）；
- 「实验设计本身由检索/立题派生」（GOAL `W-5`）——阶梯下一格。

## 无可复用事实需要另建工程记忆（本轮已建）

本 cycle 的可复用面**已单列**为 `MEM-20261015-223`：**「声明 == 加载」不是「名副其实」**
—— 自洽地加载上一轮的断言集在一致性面永久隐身；自指判词写死「证据串」= **恒绿**；
归档的**条数**不能证明「是谁的判词」（要靠断言名的在场）。
本条与既有 `MEM-20261010-212`（第一例：声明 A、加载 B）是**同一缺陷家族的两例**，互相链接。

## 结论

**PASS_WITH_WARNINGS。** EC-05 成立：

- 收口复检**跑得动、跑得对**（本树 78 条判词全绿）；
- **两树 `TWO-TREE PASS`**（78 条逐行相同 + `sha256` 一致；判词归档进树、`CR=0`）；
- as-is m0 **23/23**（在全部记录写入**之后**）；治理 + 三条 MAINLINE 判据全绿；
- **阶梯记账成立**：「实验」域的上扬有了依据面（本 GOAL 被收录）。

**本 cycle 最有价值的读数**是 `W-2` 之外的那一条：**收口资产自身的「名副其实」有第三种
坏法** —— 不是「加载错别人」（`MEM-212` 的第一例），而是**自洽地加载上一轮**：
一致性判据全绿、归档像模像样、自有断言静默退役。三处修复 + 两处红按压 + 一条反向反例
已把它做成机器可检的事实。
