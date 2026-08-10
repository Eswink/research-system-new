# Context & Memory Architecture v0.2.2

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
