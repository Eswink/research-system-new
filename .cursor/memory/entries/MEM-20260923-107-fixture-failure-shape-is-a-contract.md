---
id: MEM-20260923-107
title: "「把参考协议补成能跑的载体」**不是加性改动**（实测）：m12 一旦补齐合约，它的**失败形态**从构造期 ValueError 变成执行期优雅收敛 ⇒ 用它的失败当夹具的判据成片失效（点名判词、预留可见性、判据寄存器）"
status: ACTIVE
created_at: 2026-09-23
updated_at: 2026-09-23
scope: repository
confidence: 0.9
review_after: 2027-09-23
source_plans:
  - .cursor/plans/tasks/PLAN-20260922-138-real-experiment-chain-via-m12.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260923-139-goal-011-closeout-recheck.md
supersedes: []
tags:
  - fixture-semantics
  - failure-path
  - goal-011
  - governance
---

# 参考协议的失败形态是**夹具契约**（GOAL-011 cycle 9→10 实测）

## 做了什么

给 `m12_reference_research_v1` 补齐 5 份 phase 合约后，CI（`M0` run `35765996603` @ `02a4f47`）
判红 **11 + 2** 条。逐条溯源（本机复跑 + 在 `6f5b9fb5` 与 `02a4f47` 两棵 detached worktree 上做
A/B）后确认：**没有一条是"功能坏了"**，全部是**夹具语义**被改掉：

| 失效的判据 | 为什么 |
| --- | --- |
| 「重建说明点名 `task contract`」 | 该字符串是**旧失败原因**；补上合约后 m12 不再在缺合约处失败，重建甚至**不再失败** |
| 「失败 run 仍持有 preflight 预留」（API 与 console 各一条） | 旧绿靠**泄漏**：`_contract_for` 的 ValueError **绕过** `_fail_run` 的 `release_reservation`；优雅收敛按设计释放 |
| `test_run_chain_capability_exposure.py`（2 条） | 它把 m12 写进「未声明 `capability_execution`」的**字面寄存器**当对照协议 |
| 顺带抓到的真缺口 | 优雅收敛的 `RunOutcome` 不带字节 digest ⇒ 冻结过的 run 被读面判成「从未冻结」 |

## 为什么这样做

- **失败路径是行为的一部分**：`m12` 在仓库里的角色是「**冻结成功、执行期失败**的参照物」——
  它被 8 处判据当夹具用。改它的**失败落点**等于改这些判据的输入，而判据本身一个字没动。
- **「加性改动」的判断要按路径而不是按文件**：合约/schema 是新增文件，但**可达路径**变了
  （构造期 → 执行期），所以成片的既有断言换了含义。
- **纪律禁止改测试断言使其通过**：因此正确处置是**撤回**（逐字节退回）+ 把「1–3 条需要一次决定」
  登记进目标记录，而不是把断言改成跟新现实一致。

## 怎么做与复现

1. **先量基线**：`git worktree add --detach <仓外> <旧 tip>` ⇒ 同一子集在旧树跑一遍
   （本次：`11 passed`）。**没有基线就没有归因**。
2. **A/B 变量**：在旧 tip 的 worktree 里逐条摘掉可疑声明再跑同一子集——本次实测「摘掉
   `capability_execution` 与 `inputs:` 后失败形态**不变**」，据此把根因锁定在**合约补齐**本身。
3. **撤回要判到字节**：`git diff <旧 tip> -- <四条路径>` **为空**才算撤回干净。
4. 残留的真缺口**当场修 + 判据钉住**（先红后绿），不要跟着载体一起退回。

## 适用边界

- 这条不是「不许补合约」，而是「补之前先数**谁把它的失败当夹具**」，并准备好三步：修产品、
  改夹具语义（需授权）、或撤回。
- `m12` 的 `m12_experiment_execution` 合约**本来就在**（实验缝用它是安全的）；被撤回的是
  5 份 phase 合约与两处声明。

## 来源

- `PLAN-20260922-138`「cycle 10 撤回」节；`RECHECK-20260922-139`。
- CI 判红与基线成对：`M0` run `35765996603`（11 failed）vs 同作业在 `6f5b9fb5` 的 success。
