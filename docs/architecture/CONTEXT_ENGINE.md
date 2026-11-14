# Context & Memory Architecture v0.4.0

## 1. 两个问题分开

### Runtime Context
当前 Agent 这一轮需要看到什么。

### Persistent Memory
未来 Run 可以复用什么。

OpenHands condenser 处理对话压缩；Research OS 处理领域上下文和 Memory 治理。

## 2. Context Sources

```text
Role instructions
TaskContract
Research objective
Target profile
World projection
Evidence
Sources
Experiments
Workspace excerpts
HandoffBundle
Policy
Budget
Recent observations
```

## 3. ContextSnapshot

记录：

```text
selected refs
template hash
retrieval query/digest
token allocation
trust labels
created_at
```

不保存私有 chain-of-thought。

## 4. Memory Tiers

```text
SESSION
RUN
PROJECT
ORGANIZATION
```

MVP 重点实现 Session/Run/Project。

## 5. Memory Types

```text
FACT
DECISION
NEGATIVE_RESULT
LESSON
PROCEDURE
PREFERENCE
OPEN_QUESTION
```

## 6. Memory Write Gate

```text
MemoryWriteProposal
→ schema
→ source/provenance
→ contradiction check
→ policy
→ curator/gate
→ MemoryRecord
```

未经证据支持的内容不能进入“事实记忆”。

### 6.1 合约声明式导出（GOAL-20261114-113）

`TaskContract.memory_export`（`MemoryExportSpec`，缺省 `None`）是**授权声明**：
只有合约显式声明，任务收尾才把已验证的 Claim 经本 gate 提交 —— 编排层以
`curator_approved=True` **代表合约**提交，授权来源就是声明本身；缺省 `None` ⇒
不晋升（不是拒绝：「没声明就没这条通道」）。gate 的 `_CURATOR_TIERS` 与
curator 判定**不因声明放宽**。

生产装配点（最后一米）：两个组合根经 `services/api/memory_gate_support` 注入
`MemoryGateDeps`（store 与 `memory.read` 的读面**同一实例** ⇒ 下一轮
`prior_knowledge` 读到刚落库的记忆）；`promote_memory`（`memory_promotion.py`）
是编排层唯一调用点，PROJECT 档的记录 `scope="project"` 与 §4 的档位一致。

## 7. Lifecycle

Memory 记录：

```text
scope
provenance
confidence
valid_from
review_after
expires_at
supersedes
contradictions
```

支持删除、归档、复核。

## 8. Vector Index

向量库只是 derived projection：

- 可重建；
- 不作为事实源；
- 删除 Memory 后必须同步移除索引。

## 9. 会话压缩：委派 SDK + 护栏 + 测量

压缩**委派给 OpenHands SDK**（`LLMSummarizingCondenser`），Research OS 不自建
摘要器。`session_builder._context_guardrail` 给每个真实 agent 装上护栏
（GOAL-20261114-113 EC-06）：

- `max_size=80`：实测真实包络（5–12 个 view event）距阈值差一个数量级 ⇒
  **护栏不改变当前行为**，它不是性能优化；
- `keep_first=4`：承重 —— hard context reset 会从 `summary_offset=0` 起摘要
  **包括用户消息（合约的 fenced-JSON 应答指令）在内的一切**；
- 复用 agent 的**同一个 `llm` 对象**：摘要若用另一个 LLM，`usage_id`/`Metrics`
  分叉 ⇒ observed model name 出现第二个值 ⇒ `runtime_fingerprint` 静默掉成
  `NOT_VERIFIED`（无红判据的破坏面）；
- 不设 `max_tokens`（类默认 `None`）⇒ 不触发 HARD 路径；
- 不设 `max_message_chars`（openhands-sdk==1.42.0 死字段：声明 6 处、读取 0 处）。

测量（EC-07，**只读**）：会话终态向 telemetry sink 采样
`research_os.session.view_events` 与 `research_os.session.prompt_tokens_total`
——「有没有会话接近 `max_size`」用生产读数回答，不估算；值是计数，不含
prompt/响应内容。

**登记的无人看守出口（W-N，本轮不修）**：SDK `LLMSummarizingCondenser` 的
`@observe` 有 `ignore_inputs` 但**没有 `ignore_output`** —— 摘要文本会作为
span output 导出。当前 SDK observability 未启用、`privacy_exit_census` 的
`PRODUCT_ROOTS` 不含 `.venv` ⇒ 该出口任何判据都看不见；归属上游面。
