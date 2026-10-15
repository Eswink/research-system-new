---
id: RECHECK-20261015-474
slug: goal-078-ec03-what-entered-the-context-is-readable
title: GOAL-078 cycle 3 复检 — 「进了什么」在既有读面上可复核（EC-03）
status: COMPLETED
result: PASS
created_at: 2026-10-15
updated_at: 2026-10-15
plan_id: PLAN-20261015-473
parent_goal: GOAL-20261014-078
reviewer: root-agent
owners:
  - root-agent
---

# RECHECK-20261015-474 — GOAL-078 cycle 3

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | 上下文**落成制品**且 id 按 task 前缀 | **PASS** | `persist_retrieval_context` ⇒ `{task_id}:retrieval_context`；判据断言 `split(":",1)[0] == task_id`（**既有读面按这个约定收 run 作用域制品** ⇒ 零新路由） |
| AC-2 | **同源**（本轮的关键性质） | **PASS** | 写出的字节**就是** `retrieval_digest` 的源：判据独立重算 `Digest.of_bytes(raw) == snapshot.retrieval_digest`（**实测 True**），且 `store.meta(id).digest == snapshot.retrieval_digest`（**实测 True**）⇒ 读面值与会话值**不可能分叉** |
| AC-3 | 载荷**自足** | **PASS** | `{run_id, entries:[{identifier, evidence_id, artifact_id, shown}]}`；判据逐条断言四个键**都在场** |
| AC-4 | 空集合**也写且带理由** | **PASS** | 空 run ⇒ 制品在、`entries == []`、`reason` 含 `no retrieved evidence`（**实测**：读面上那件上游制品的 `reason` 逐字为该句） |
| AC-5 | `created_by` 记**装配事实** | **PASS** | `system:retrieval-context`（不是任何 agent 的产出）——判据钉住该值 |
| AC-6 | **只对会建会话的任务写**（射程） | **PASS** | 实现按**契约声明**分流（`experiment` / `report` 非空 ⇒ 跳过，不按合约名硬编码）；e2e 实测一个 run 上**恰两件**上下文制品（= 两个会话 phase），实验/报告格零件 |
| AC-7 | **HTTP 面端到端** | **PASS** | e2e：`GET /runs/{id}/artifacts` 上有两件上下文制品（下游 `entries` 非空 / 上游空且带理由）；`GET /artifacts/{id}/content` 读回自足载荷 |
| AC-8 | 读面 digest 与**会话** digest 同源 | **PASS** | e2e 断言：会话 spec 的 `retrieval_digest` **在场于**读面制品的 digest 列表里 |
| AC-9 | **四向按压全红** | **PASS** | `.cursor/plans/goals/evidence/GOAL-20261014-078-press-two-way.txt`（1142 字节、`CR=0`）：`V8-1`（摘接线）/ `V8-2`（去 run 过滤）/ `V8-3`（性质恒真）/ **`V8-4`（不落制品）** 各 `BASELINE GREEN=True / 按压 RED=True / sha 复原一致=True`，`all_red_and_restored=True` |
| AC-10 | 既有判据零放宽 | **PASS** | 接缝 16 passed、读面 5 passed、e2e 7 passed；**零新路由 / 零新 DTO / 零 OpenAPI 快照改动**（`git diff` 无 `docs/api/openapi.m13.json`） |
| AC-11 | 制品计数类既有判据不回归 | **PASS** | `test_vertical_slice_happy_path`（`len(artifacts) == 4 + len(DECLARED_INPUTS)`）与 `test_idempotency`（`_SEEDED + 1/3`）**都仍绿** —— 它们的 harness **不接**该缝（实测确认），所以新制品不出现在它们的作用域里 |

## 警告（如实登记）

- **`W-1`**：**EC-04 / EC-05 仍未完成** —— 真实中转站实跑与自举收口属后续 cycle。
- **`W-2`**：读面**按 run 收**上下文制品（task 前缀约定），但**载荷里的 `run_id` 是装配时
  传入的那个**；两者由**同一处装配**保证一致（`with_retrieval_context` 用 `task.run_id.value`
  求值、`persist_retrieval_context` 用同一 `view`）。判据断言二者相等（`payload["run_id"] == run_id`）。
- **`W-3`**：把上下文写成制品**会让 run 的制品清单多两条**（每个会话 phase 一条）——
  这是本 EC 的**代价**：读面要能回答「进了什么」就得有个落点。已核实**不回归**两条既有的
  精确计数判据（见 AC-11），但后来者若新增「按 run 数制品」的判据应把它们算进去。
- **`W-4`**：**不判模型行为**（承 EC-02 的 `W-4`）；也**不判**读面读者如何解释这些摘录。
- **`W-5`**：进上下文的仍是**有界摘录**（§10）；读面上的 `shown` 是截断后的文本。
- **`W-6`**：`R-M1` 未收口 ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」。

## 未覆盖的面

- 真实中转站上的一次完整研究（EC-04）；
- 自举收口（EC-05）；
- 模型侧「读没读」的行为观测（`W-4`）。

## 无可复用事实需要另建工程记忆（本轮教训已并进既有条目）

本轮的可复用面**已并进** `MEM-20261014-221`（那条讲「早声明却零构造点的死接缝」与
「按压不咬先怀疑射程」）：本 cycle 补的是**第三条**——「**同源**要用同一份字节证，
不要用两次计算证」。写盘字节即 digest 的源 ⇒ 读面值与装配点值**不可能分叉**，
比「分别算两次再比对」强（后者在实现换实现时会一起漂）。

## 结论

**PASS。** EC-03 成立：「哪些内容进了会话上下文、各自的 digest 与来源」现在在**既有读面**上
读得出来（`GET /runs/{id}/artifacts` + `/content`，**零新路由**）；读面值与会话值**同源**
（写盘字节即 `retrieval_digest` 的源）；空集合在读面上**带理由**（不是缺席）。
四向按压全红且逐字节复原，其中 `V8-4` 专门钉住本 cycle 的新面（不落制品 ⇒ 判红）。
