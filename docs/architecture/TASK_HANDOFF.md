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
failure_policy:    # resource → 字符串/布尔/整数/字符串数组（见 §2.1）
idempotency_scope:
```

### 2.1 `failure_policy` 的消费者（GOAL-004 cycle 3）

`failure_policy` 是自由键值 dict，**能消费的键才有语义**，其余键不假装生效：

| 键 | 取值 | 消费点 | 语义 |
| --- | --- | --- | --- |
| `on_task_failure` | `FAIL_RUN`（缺省） | `phase_runner.failure_step` | 任务**终局失败** ⇒ run 立刻收敛 `FAILED`（隐式 fail-fast，既有行为） |
| | `CONTINUE` | 同上 | 失败被记为"被容忍"（`task.failed` 事件 + `TaskOutcome.failure_policy`），**剩余工作照跑**；跑完收敛 `DEGRADED`（非终态）并发 `run.degraded` |

- 已知键取值非法 ⇒ `ValueError`（响亮失败，不静默回退）；
- 未消费的键（用户契约里任何不在 `KNOWN_KEYS` 的键）由
  `TaskContract.failure_policy_view().unhonored` **点名**，行为按缺省；
- **平台自带的示例契约只声明被消费的键**（GOAL-005 cycle 3 = EC-03）：示例里曾同时写着
  `on_validation_failure: DEAD_LETTER` 与 `allow_partial_evidence: false`，两者都没有执行期
  消费者——示例不该示范一条不生效的策略，故从 `examples/contracts/task_contracts.yaml`
  移除（`on_task_failure: FAIL_RUN` 是显式写出的缺省值）。移除的是**声明**，不是这个键本身：
  用户契约里再写 `on_validation_failure` 照样进 `unhonored` 被点名、行为按缺省；
- `on_validation_failure` 的消费为什么仍未做：验收门跑在任务行 **durable `SUCCEEDED` 之后**
  （`task_executor._attempt_once` 先 `engine.complete(...)`，`register_and_gate` 才
  `evaluate_gate`），门拒收时任务行已是终态；按 `DEAD_LETTER` 处置就得把一条 `SUCCEEDED`
  行改写回去 ⇒ **canonical 状态机改动（ADR 边界）**，登记为后继入口，不在清账里私自实现；
- `DEGRADED` 是"活干完了、但有几条被容忍的失败"的诚实状态：不冒充 `SUCCEEDED`，也不把整条
  run 判死（`FAILED` 是终态，那正是 `CONTINUE` 要避免的）。

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
