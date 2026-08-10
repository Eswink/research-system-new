# Task Contract & Handoff Architecture

## 1. 为什么需要 TaskContract

多 Agent 系统失败的常见原因不是“模型不聪明”，而是：

- 输入边界不清；
- 输出无法验证；
- Agent 只通过聊天交接；
- 下游不知道上游的假设、失败和 Artifact；
- 相同任务被重复执行产生副作用。

因此：

```text
Phase
→ ResearchTask
→ TaskContract
→ AgentSession
→ HandoffBundle
```

## 2. TaskContract

最低字段：

```yaml
id:
version:
purpose:
input_schema:
output_schema:
required_capabilities:
required_artifacts:
acceptance_criteria:
budget:
timeout:
retry_policy:
failure_policy:
idempotency_scope:
```

## 3. AcceptanceCriterion

类型：

```text
SCHEMA_VALID
ARTIFACT_EXISTS
TEST_PASSES
METRIC_THRESHOLD
EVIDENCE_COVERAGE
REVIEW_SCORE
POLICY_COMPLIANT
HUMAN_APPROVAL
CUSTOM_EVALUATOR
```

LLM 不能自行宣布验收通过。

## 4. HandoffBundle

只传结构化、可引用的信息：

```text
summary
structured output
artifacts
claims/evidence
decisions
failures
open questions
next-action hints
```

禁止把完整聊天记录作为唯一 Handoff。

## 5. Agent-to-Agent Delegation

默认由 WorkflowEngine 创建新 Task，而不是 Agent 无限递归创建子 Agent。

如允许 delegation：

```text
max_depth
max_children
budget
allowed_roles
```

必须受控。

## 6. Idempotency

Task 的副作用必须绑定：

```text
task_id + attempt + operation_key
```

重复投递时：

- 已成功且结果可复用 → 返回原结果；
- 正在执行 → 拒绝重复占用；
- 不可安全重试 → 进入人工恢复。
