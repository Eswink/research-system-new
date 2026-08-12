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

最低字段（实现 `packages/domain/tasks.py::TaskContract` + `schemas/task-contract.schema.json`）：

```yaml
id:
version:
purpose:
input_schema:      # 引用 schemas/ 下 *_v{n} 输入 schema
output_schema:     # 引用 schemas/ 下 *_v{n} 输出 schema
required_capabilities:
required_artifacts:
acceptance_criteria:
budget:            # resource → 数量/上限（Decimal 或 null）
timeout_seconds:
retry_policy:
failure_policy:    # resource → 字符串/布尔/整数/字符串数组
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

结构化参数：`artifact` / `minimum_sources` / `metric` / `operator`（GT/GTE/EQ/LTE/LT）/
`threshold` / `evaluator` / `description`。

LLM 不能自行宣布验收通过：求值器（`packages/domain/acceptance.py`）只依赖显式注入的
`CriterionInputs`（structured output、artifacts、tests、metrics、evidence count、
review score、policy decision、human approval）；SCHEMA_VALID 经 jsonschema 校验
`output_schema`，未注入校验器时 fail-closed。CUSTOM_EVALUATOR 必须由编排层执行，不自动通过。

## 4. HandoffBundle

只传结构化、可引用的信息（实现 `packages/domain/tasks.py::HandoffBundle`）：

```text
task_id
producer            # 人类可读 producer 描述
producer_agent_id   # 结构化 agent 引用（可选）
producer_role_id    # 结构化 role 引用（可选）
summary
created_at          # UTC
structured output
artifacts / claims / evidence / decisions refs
failures
open questions
next-action hints
digest              # sha256:<64 hex>，由创建方对 bundle 确定性序列化
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
