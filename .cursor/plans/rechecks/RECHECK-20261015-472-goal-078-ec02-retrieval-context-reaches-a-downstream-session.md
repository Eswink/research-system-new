---
id: RECHECK-20261015-472
slug: goal-078-ec02-retrieval-context-reaches-a-downstream-session
title: GOAL-078 cycle 2 复检 — 检索内容经产品路径到达下游会话（EC-02）
status: COMPLETED
result: PASS
created_at: 2026-10-15
updated_at: 2026-10-15
plan_id: PLAN-20261014-471
parent_goal: GOAL-20261014-078
reviewer: root-agent
owners:
  - root-agent
---

# RECHECK-20261015-472 — GOAL-078 cycle 2

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | 新产品路径 e2e 判据在树 | **PASS** | `tests/e2e/test_retrieval_context_reaches_the_session.py`（4 个用例类 / 5 例，`requires_docker`） |
| AC-2 | 取证面 = **会话 spec**（不是内部对象） | **PASS** | `SessionSpecRecorder` 包在 runtime 上（`create_session` 留 spec、其余经 `__getattr__` **原样透传**）；产品代码**零改动**；按 `task_contract.id`（**声明事实**）索引，**不按顺序猜 phase** |
| AC-3 | **正向臂**：下游会话 `selected_refs` 非空 | **PASS** | `multi_role_review`（下游）的 spec ⇒ `selected_refs` 非空；另断言 `trust_labels == ["RETRIEVED"]`、`retrieval_digest` 与 `token_allocation > 0` 都在场 |
| AC-4 | **逐条**与证据读面对应（不是「非空」了事） | **PASS** | 每个 ref 断言：① 以 `tool-result:` 开头；② 属于 `GET /runs/{id}/evidence` 里 `source_trust_label == "RETRIEVED"` 的 `artifact_id` 集合；③ 读面上该集合**非空**（否则判据在空集上恒真） |
| AC-5 | **反证臂**：上游会话空**且**点名 | **PASS** | `research_report_plan`（上游，它开工时检索还没跑）⇒ `selected_refs == []`、`retrieval_digest is None`、`token_allocation == 0`；并断言两个 phase 的上下文**不是同一对象**、refs **不相同**（「按时刻装配」的直接读数） |
| AC-6 | 射程：只有**本 run 系统取得**的内容进上下文 | **PASS** | `refs ⊆ retrieved`；且 `everything - retrieved` **非空**（本 run 的证据链里确实还有声明输入 / 自产件 / 报告），并断言 `refs ∩ (everything - retrieved) == ∅` —— 非检索来源**不得**进上下文 |
| AC-7 | 检索真的执行了（正向臂非空转） | **PASS** | 离线传输记录含 `EXT_ID:` 请求（两步链真跑）；下游上下文非空 |
| AC-8 | 受判面自检：装配器接在**产品依赖**上 | **PASS** | `assemble(ApiSettings(db_path=":memory:")).runs._deps.retrieval_context is not None` ⇒ 断言的是**产品组合根**而非测试装配（没有它，AC-3 只证了测试自己塞进去的） |
| AC-9 | **按压三向全红**且逐字节复原 | **PASS** | `.cursor/plans/goals/evidence/GOAL-20261014-078-ec02-press-two-way.txt`（1026 字节、`CR=0`）：`V8-1`（摘装配接线）/ `V8-2`（去掉 run 过滤）/ `V8-3`（性质判据恒真）各 `BASELINE GREEN=True / 按压 RED=True / sha 复原一致=True`，`all_red_and_restored=True` |
| AC-10 | 既有判据零放宽 | **PASS** | 受影响套件 **997 passed, 1 skipped**（`tests/application` + 两个 e2e 模块）；接缝判据 **16 passed**（cycle 1 的 13 例 + 本轮 3 例） |
| AC-11 | 规模门 | **PASS** | 新 e2e 335 行、无超 50 行函数；接缝判据扩展后仍无超限函数 |

## 警告（如实登记）

- **`W-1`**：**EC-03 / EC-04 / EC-05 仍未完成** —— 本 cycle 只做 EC-02。
  「读面可复核『进了什么』」「真实中转站」「自举收口」属后续 cycle。
- **`W-2`（本轮**实测**到的覆盖缺口，已补）**：**两条按压臂首轮没咬住**。
  `V8-2`（去掉 run 过滤）与 `V8-3`（性质判据恒真）在 e2e 上**都不变红** ——
  该夹具只有**一个** run ⇒「按 run 过滤」这条性质**无处可测**；而协议的**声明输入不带**
  `tool-result:` 前缀 ⇒ 性质判据被前缀过滤**先挡住**。
  **处置 = 补判据、不调按压**：新增 `TestTheRunFilterBites`（同库放两个 run 的证据）
  与 `TestAToolResultWithoutTheRetrievedLabelDoesNotEnter`（**带前缀但性质为 `GENERATED`**
  的工具结果 —— 这正是 canonical 读面 provider 的真实形态，不是造出来的边角）⇒ 三臂全红。
- **`W-3`（夹具缺装配）**：run-ready 夹具不经产品组合根，因此**不带** `retrieval_context`
  （与 `capabilities` / `experiment_task` / `report_task` 三条缝同一形态）。判据侧以装配方
  身份补一行（用**产品件本身** `retrieval_context_builder`，不复制实现）。首跑失败形态正是
  「下游上下文为 `None`」 —— 即该缺口**真的**会被判据抓到，不是因为判据自己写错。
- **`W-4`**：**不判模型行为** —— 判的是「内容进了会话规格」这一事实；
  「模型读了它」需要观测面（属阶梯的再下一级），如实登记。
- **`W-5`**：进上下文的是**有界摘录**（§10）；判据只判「进了哪些 / 从哪来 / 是否系统取得」，
  **不**判内容质量与完整性。
- **`W-6`**：`R-M1` 未收口 ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」。

## 未覆盖的面

- 读面可复核「进了什么」（EC-03）；
- 真实中转站上的一次完整研究（EC-04）；
- 自举收口（EC-05）；
- 模型侧「读没读」的行为观测（`W-4`）。

## 无可复用事实需要另建工程记忆（本轮教训已并进既有条目）

本轮的**可复用教训**（承 `MEM-20261014-221`，并补一条）：**按压不咬时先怀疑射程，
不是先怀疑按压** —— 两条没咬住的臂暴露的是**判据覆盖缺口**（单 run 夹具测不出跨 run 隔离；
声明输入与检索证据经**不同前缀与不同性质**两条路进库）。补判据时要选**真实存在的形态**
（这里 = canonical 读面 provider 的 `tool-result:` + `GENERATED`），不要造边角情形去凑红。

## 结论

**PASS。** EC-02 成立：**经产品路径**的一次 run 里，**下游**会话的 spec 真的带上了上游取回的
检索内容（`selected_refs` 非空、逐条与证据读面的 `RETRIEVED` 性质对得上），而**上游**会话
（它开工时检索还没跑）拿到的是**空且可判**的上下文 —— 两向写在**同一次实跑**上，
互为对照。三向按压全红且逐字节复原，其中两条臂的**首轮失效**被如实登记为覆盖缺口并补判据。
