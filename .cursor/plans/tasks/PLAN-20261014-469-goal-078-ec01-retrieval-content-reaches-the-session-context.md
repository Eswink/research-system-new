---
id: PLAN-20261014-469
slug: goal-078-ec01-retrieval-content-reaches-the-session-context
title: GOAL-078 cycle 1 — 检索内容进会话上下文的**接缝**（EC-01）
status: DONE
created_at: 2026-10-14
updated_at: 2026-10-14
parent_goal: GOAL-20261014-078
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261014-470-goal-078-ec01-retrieval-content-reaches-the-session-context.md
memory_entries:
  - .cursor/memory/entries/MEM-20261014-221-declared-but-never-constructed-is-a-dead-seam.md
---

# PLAN-20261014-469 — GOAL-078 cycle 1

## 验收条件

- [x] EC-01 装配器在树（`retrieval_context.py`），只读 canonical、零出网
- [x] EC-01 判据成对：逐条 ref 在场 / digest 由内容重算 / 上界生效 / 空集合点名
- [x] EC-01 接上会话：`SessionSpecContext.retrieval_context` 缺省 `None` ⇒ 既有语义逐字节不变
- [x] 既有判据零放宽（定向套件 + 架构判据 + 全量 m0 绿）

## 目标（本 cycle 的可独立验收主题）

**EC-01**：把「本 run 已取回的检索内容 → 会话上下文」做成一个**声明式、可判定**的接缝，
**零出网、零新依赖、不绕过脱敏**，且判据成对（逐条 ref 在场 / digest 由内容重算 /
上界生效 / 空集合点名）。

## 设计（为什么这样接，而不是别的接法）

### 1. 落点：既有的 `ContextSnapshot` 槽位，**不新造第二个**

`packages/domain/memory.py` 早就声明了 `ContextSnapshot`（`selected_refs` /
`retrieval_digest` / `token_allocation` / `trust_labels` / `template_hash`），
`AgentSessionSpec.context_snapshot` 也一直存在 —— **建档实测：全仓零构造点**。
本 cycle 就是把这个**已经设计好的槽位**接上一个真生产者，
而不是发明第二套上下文注入面（那会让「上下文里有什么」有两处真相）。

### 2. 装配点是**编排层**（`session_resolution` / `task_executor` 之间）

为什么不是 adapter 层：adapter 不该知道「哪个 run 的检索结果」——那是编排事实。
为什么不是会话期：会话已经创建，上下文要在 `create_session` **之前**定下来
（会话期的「追加」是另一件事，且会绕过冻结快照语义）。

⇒ 在一个**新增的编排层模块**里把「本 run 的检索证据」汇成 `ContextSnapshot`，
由 `execute_task` 在构造 `AgentSessionSpec` 时带上。

### 3. 内容**有界**（§10 观测隐私，也是本 GOAL 的 `forbidden` 面）

进上下文的是**文本摘录**，不是原始字节：逐条 `title` 截断到**固定上限**，
条数也有上限；超限的部分**点名**（不静默丢）。判据断言上界**真的生效**
（构造一条超长标题 ⇒ 出来的串长度 ≤ 上限）。

### 4. 空集合**点名**

没有检索证据时 `selected_refs` 为空 —— 这**不是**失败（很多协议没有检索），
但必须**可判**：装配函数返回的判定里带 `reason`（点名「本 run 没有检索证据」），
判据两向都跑（有 ⇒ 非空 + 逐条；无 ⇒ 空 + 点名）。

### 5. 边界（如实登记，不夸大）

- **只读 canonical**：来源是 `EvidenceLedger` 的证据 + `ArtifactStore` 的
  `tool-result:` 制品，**不触发任何工具调用**（零出网）；
- **只收 `RETRIEVED` 性质**：来源性质由 `SourceRecord.trust_label` 决定
  （与 `count_retrieved_sources` 同源），**不**把声明输入（`USER_PROVIDED`）
  或自产件（`GENERATED`）当检索内容；
- **不改**任何既有判据的谓词；本 cycle 只**新增**判据文件。

## 实施清单

1. **WP-A：装配器**（`packages/application/run_orchestration/retrieval_context.py`）：
   `build_retrieval_context(artifacts, ledger, run_id, *, max_items, max_chars)` →
   `RetrievalContextView(snapshot, entries, reason)`。逐条取 `tool_refs` 非空且
   来源性质 `RETRIEVED` 的证据 → 其 `artifact_id` 的**内容**（`articles[].pmid/doi/title`）
   → 截断 → `ContextSnapshot(selected_refs=[...], retrieval_digest=<内容寻址摘要>,
   trust_labels=["RETRIEVED", ...], token_allocation=<估算>)`。
2. **WP-B：接上会话**：`SessionSpecContext` 增加 `retrieval_context`（缺省 `None`
   ⇒ 既有语义逐字节不变）；`execute_task` 把它放进 `AgentSessionSpec.context_snapshot`。
3. **WP-C：判据**（`tests/application/test_retrieval_context_seam.py`）：
   逐条 ref / digest 重算 / 上界生效 / 空集合点名 / **零出网**（用
   `FakeArtifactStore` + `FakeEvidenceLedger`，无 HTTP 客户端）。
4. **WP-D：记录 + 门**：本文件 + RECHECK / GOAL 回写 / ALL_PLAN 同提交；
   定向套件 → 记录面判据 → 全量 m0。

## 影响报告（预估，收口时按实测改写）

- **产品代码**：新增 1 个模块（装配器）；**改** `SessionSpecContext`（新增可选字段，
  缺省 `None` ⇒ 零回归）与 `execute_task` 的一处构造。
- **判据面**：新增 1 个测试模块；既有判据**零放宽**。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化、无出网新增**。

## 残余与未覆盖（如实登记）

- EC-02（经产品路径进入会话）/ EC-03（读面可复核）/ EC-04（真实中转站）/ EC-05（收口）
  **不在本 cycle**。
- **模型是否真的「读了」上下文**：本 GOAL 判的是**内容进了会话规格**这一事实，
  **不**判模型的行为（那需要模型侧观测，属观测面）。

## 证据

（收口时按实测填写：命令 + 读数。）

| 面 | 读数 | 命令 |
| --- | --- | --- |
| 接缝判据 | **13 passed** | `uv run --frozen --no-sync python -B -m pytest tests/application/test_retrieval_context_seam.py -q` |
| 产品装配接线 | `inner.retrieval_context is not None` ⇒ **True**；空 run ⇒ 点名理由 `run … has no retrieved evidence…` | 见 GOAL 的迭代日志 |
| 既有套件 | **2752 passed, 8 skipped**（此前 2739 ⇒ +13） | `uv run --frozen --no-sync python -B -m pytest tests/application tests/domain tests/adapters tests/api -q` |
| 类型 / 格式 | `mypy` = `Success: no issues found in 1232 source files` | `uv run --frozen --no-sync python -B -m mypy` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-14 | IN_PROGRESS | cycle 1 建档（EC-01 的靶子与设计）。 |
| 2026-10-14 | DONE | WP-A…WP-D 落地：装配器 + 两组合根接线 + 13 例判据；既有套件 +13 全绿。 |
