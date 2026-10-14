---
id: MEM-20261014-221
title: "「早就声明却零构造点」是设计完成但产品路径没接的典型形态：数构造点比读设计文档可靠；接上它时求值点要放在「上游事实已落库」的那一刻"
status: ACTIVE
created_at: 2026-10-14
updated_at: 2026-10-14
scope: repository
confidence: 0.9
review_after: 2027-04-14
source_plans:
  - .cursor/plans/tasks/PLAN-20261014-469-goal-078-ec01-retrieval-content-reaches-the-session-context.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261014-470-goal-078-ec01-retrieval-content-reaches-the-session-context.md
supersedes: []
tags: [research-loop, retrieval-context, dead-seam, evaluation-point, observability-privacy]
---

## 做了什么

把「活检索的内容 → 会话上下文」接上（GOAL-20261014-078 EC-01，阶梯「检索」域 L1 → L2）：

- 域层 `ContextSnapshot`（`selected_refs` / `retrieval_digest` / `token_allocation` /
  `trust_labels`）与 Port 的 `AgentSessionSpec.context_snapshot` **早就声明**，
  但**建档实测：全仓零构造点**（`context_snapshot=` 在 `packages/`·`services/` 零命中）
  ⇒ 会话上下文里没有任何检索内容；
- 新增**唯一**生产者 `run_orchestration/retrieval_context.py`：只读 canonical
  （`EvidenceLedger` + `ArtifactStore`），只收 `TrustLabel.RETRIEVED`，
  摘录**有界**（逐条截断 + 条数上限），空集合**点名**；
- 装配决策收在 `services/api/retrieval_context_support.py`，两个组合根各接一行。

## 为什么这样做（三条可复用）

1. **「这个能力有没有」要数构造点，不要读设计文档**：`ContextSnapshot` 的 docstring 与字段
   看起来完备，但 `rg "<Type>("` 只命中定义处 ⇒ 它在运行路径上**从未被填充**。
   「槽位存在」≠「有人往里写」——判据/勘察都该数**生产者**。
2. **接上时求值点决定「看到多少」**：本处放在**每个任务开始前**（`_run_group_task`），
   而不是 plan 期 —— 上游 phase 的证据是**逐步落库**的，plan 期求值只会拿到第一轮的，
   下游就看不到它开始时已有的内容。同类接缝（记忆读面、前序结论读取器）都适用。
3. **§10 的有界口径要落到实现里**：进上下文的是**摘录**（逐条字符上限 + 条数上限），
   不是原始字节；判据断言**上界真的生效**（`len(shown) == 上限` 且 `truncated=True`）。
   代价如实登记：更长的重要内容会被截断，读者不得把「有摘录」读成「看到全文」。

## 怎么做与复现

```bash
# 接缝判据（13 例：逐条 ref / digest 独立重算 / 上界生效 / 两种空分得开 / 只收系统取得 / 零出网构造性证据）
uv run --frozen --no-sync python -B -m pytest tests/application/test_retrieval_context_seam.py -q

# 产品装配真的接线（组合根一行）
uv run --frozen --no-sync python -B -c "
from services.api.composition import assemble
from services.api.settings import ApiSettings
d = assemble(ApiSettings(db_path=':memory:'))
print(d.runs._deps.retrieval_context is not None)"     # ⇒ True
```

实测：`13 passed`；既有四套件 `2752 passed, 8 skipped`（此前 2739 ⇒ +13）；
`mypy` 1232 源文件零问题。

## 适用边界

- **零出网是构造性的**：判据按 **AST** 取该模块的属性名 / 名字集合与 import 面，
  与传输层词表求交集为**空** —— 比「跑的时候没出网」更强（代码里没有能力出网）。
  ⚠️ 词表**不要**含 `get`：`dict.get` 会误报（本轮的第一次实现就栽在这里）。
- **不判模型行为**：「内容进了会话规格」是事实，「模型读了它」是另一件事（要观测面）。
- **`token_allocation` 是字符数量级近似**（不引 tokenizer ⇒ 不增依赖）；
  判据断言上界，**不得**读成精确 token 预算。
- **两种空分得开**：「没有检索证据」与「有证据但内容读不出来」必须是两句判词 ——
  否则「读不到」会被读成「没有」（本 GOAL 要消灭的正是这种含混）。
- 本记忆**不**作任何安全结论（`R-M1` 未收口）。

## 来源

- `PLAN-20261014-469` / `RECHECK-20261014-470`；
- 装配器：`packages/application/run_orchestration/retrieval_context.py`（255 行）；
- 判据：`tests/application/test_retrieval_context_seam.py`（13 例）。
