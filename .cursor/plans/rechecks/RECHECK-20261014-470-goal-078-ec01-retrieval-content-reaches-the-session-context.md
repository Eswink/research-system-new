---
id: RECHECK-20261014-470
slug: goal-078-ec01-retrieval-content-reaches-the-session-context
title: GOAL-078 cycle 1 复检 — 检索内容进会话上下文的接缝（EC-01）
status: COMPLETED
result: PASS
created_at: 2026-10-14
updated_at: 2026-10-14
plan_id: PLAN-20261014-469
parent_goal: GOAL-20261014-078
reviewer: root-agent
owners:
  - root-agent
---

# RECHECK-20261014-470 — GOAL-078 cycle 1

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | 装配器在树且只读 canonical、零出网 | **PASS** | `packages/application/run_orchestration/retrieval_context.py`（255 行）；**构造性判据**：AST 取该模块的属性名 / 名字集合，与传输层词表（`urlopen` / `socket` / `connect` / `Client` / `Session` / `request` / `urlencode`）**交集为空**，且它 **import 面零网络库**（`httpx` / `requests` / `socket` / `urllib` 都不在） |
| AC-2 | 逐条 ref 在场（不是「非空」了事） | **PASS** | 判据逐条断言：每条 `entry.artifact_id ∈ snapshot.selected_refs`；标识集合恰为 `{39284801, 40601758}` |
| AC-3 | digest **由内容重算** | **PASS** | 判据**独立重算**（不 import 产品的拼接函数）：按同一份摘录拼 canonical JSON ⇒ `Digest.of_bytes` 与 `snapshot.retrieval_digest` **相等**；确定性另有一条 |
| AC-4 | §10 有界口径**真的生效** | **PASS** | 超长标题 ⇒ `shown` 长度**恰为** `DEFAULT_MAX_CHARS` 且 `truncated=True`（原文保留在 `title` 里）；`token_allocation ≤ Σlen(shown)`；条数上限另有一条（50 条输入 ⇒ 恰 5 条） |
| AC-5 | 空集合**点名**，且两种空**分得开** | **PASS** | 无证据 ⇒ `reason` 含 `no retrieved evidence`；**有证据但内容读不出** ⇒ `reason` 含 `retrieved evidence record(s)` 且**不含** `no retrieved evidence`（判据显式断言两者不同） |
| AC-6 | 只收**系统取得** | **PASS** | `USER_PROVIDED` 与 `GENERATED` 两条各自 ⇒ `selected_refs == []`（性质判据与 `count_retrieved_sources` 同源：`SourceRecord.trust_label`） |
| AC-7 | **接上会话规格** | **PASS** | `SessionSpecContext.retrieval_context`（缺省 `None` ⇒ 既有语义不变）；`execute_task` 构造 `AgentSessionSpec` 时带上 `context_snapshot`（`_context_snapshot` 只取值、不构造）；`phase_runner` 在**每个任务开始前**求值（上游证据逐步落库 ⇒ 下游看到的是「它开始时已有的全部」） |
| AC-8 | **产品装配真的接线** | **PASS** | 两个组合根（`composition.py` / `pg_composition.py`）各一行 `retrieval_context=retrieval_context_builder(...)`（装配决策收在 `services/api/retrieval_context_support.py`）；实测 `assemble(...).runs._deps.retrieval_context is not None ⇒ True` |
| AC-9 | 既有判据零放宽 | **PASS** | `tests/application` + `tests/domain` + `tests/adapters` + `tests/api` ⇒ **2752 passed, 8 skipped**（此前 2739 ⇒ **+13** = 本文件全部新例）；`mypy` = `Success: no issues found in 1232 source files` |
| AC-10 | 规模门 | **PASS** | 新增 3 个文件（装配器 255 行 / 支持层 41 行 / 判据 ~300 行），全部 ≤ 450；无超 50 行函数（含判据类的辅助函数，逐个 ≤ 50） |

## 警告（如实登记）

- **`W-1`**：**EC-02 / EC-03 / EC-04 / EC-05 仍未完成** —— 本 cycle 只做 **EC-01**（接缝在树
  且判定成对）。「经**产品路径**进入会话」「读面可复核」「真实中转站」三格属后续 cycle。
- **`W-2`**：**本 cycle 不判「模型是否真的读了上下文」** —— 判的是「内容进了会话规格」
  这一**事实**。模型侧的行为需要观测面（属阶梯的再下一级 / 观测 GOAL），如实登记。
- **`W-3`**：`token_allocation` 是**字符数量级的近似**（本模块**不**引 tokenizer ——
  那会是新依赖，违反 `forbidden`）。判据断言的是**上界**（`≤ Σlen(shown)`），
  不是精确 token 数。**不得**把它读成「精确的 token 预算」。
- **`W-4`**：摘录**逐条截断到固定字符数**（`DEFAULT_MAX_CHARS = 240`）——
  更长的重要内容会被截掉前半之后的全部。这是 §10 有界口径的**代价**，不是缺陷；
  但读者不应把「上下文里有这条的摘录」读成「模型看到了全文」。
- **`W-5`**：`R-M1` 未收口 ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」。
- **`W-6`**：本 cycle 的**读面**（EC-03）尚未做 ⇒ 今天「上下文里进了什么」只有
  **进程内对象**与**会话规格**知道；读面可读性是 EC-03 的靶子（如实登记为未覆盖）。

## 未覆盖的面

- 经**产品路径**进入会话的端到端判据（EC-02，含「上游没有检索 ⇒ 空 + 点名」的反证臂）；
- 读面可复核「进了什么」（EC-03）；
- 真实中转站上的一次完整研究（EC-04）；
- 自举收口（EC-05）；
- 模型侧「读没读」的行为观测（`W-2`）。

## 可复用事实（工程记忆）

本轮的**可复用教训**（已进工程记忆 ）：一个**早就声明却零构造点**的域槽位
（）是「设计完成、产品路径没接」的典型形态 —— 判「有没有这个能力」时，
**数构造点**（ 只命中定义处）比读设计文档可靠；而把它接上时，
**求值点**要放在「上游事实已落库」的那一刻（本处 = 每个任务开始前），
放错位置（plan 期）会让下游只看到第一轮的内容。

## 可复用事实（工程记忆）

本轮的**可复用教训**（已进工程记忆 `MEM-20261014-221`）：一个**早就声明却零构造点**的
域槽位（`ContextSnapshot`）是「设计完成、产品路径没接」的典型形态 ——
判「有没有这个能力」时**数构造点**比读设计文档可靠；把它接上时**求值点**要放在
「上游事实已落库」的那一刻（本处 = 每个任务开始前），放错位置（plan 期）会让下游
只看到第一轮的内容。

## 结论

**PASS。** EC-01 成立：`ContextSnapshot` 这个**早就声明、全仓零构造点**的槽位
（建档实测）现在有了**唯一的**生产者，且五条性质各自可判 —— 逐条 ref、digest 由内容重算、
上界真的生效、空集合点名（两种空**分得开**）、只收系统取得。它经**两个组合根**接进产品路径
（各一行装配 + 一处装配决策模块），并已把 `AgentSessionSpec.context_snapshot` 填上 ⇒
阶梯「检索」域的**第一步**（会话拿得到检索内容）在机制上成立；
**「经产品路径实跑证明」是下一个 cycle 的事**（本 cycle 不声称已跑到那一步）。
