# Agent Runtime Architecture v0.4.0

## 1. Port

M5 决策 D2：Port 为同步语义。实现契约见 `docs/architecture/PORTS.md`：

```python
class AgentRuntime(Protocol):
    def create_session(self, spec: AgentSessionSpec) -> AgentSessionHandle: ...
    def run(self, session_id: str) -> AgentSessionResult: ...
    def pause(self, session_id: str) -> None: ...
    def cancel(self, session_id: str) -> None: ...
    def stream_events(self, session_id: str) -> tuple[RuntimeEvent, ...]: ...
    def fork(self, session_id: str, spec: ForkSpec) -> AgentSessionHandle: ...
```

## 2. Session Spec

```text
TaskContract
RoleDefinition
AgentSpec
Resolved Model
Frozen Tool Set
WorkspaceLease
ContextSnapshot
RuntimePolicy
BudgetReservation
RunManifest ref
```

## 3. MVP Adapter

```text
OpenHandsRuntimeAdapter
→ OpenHands Agent
→ Conversation
→ Tools/MCP
→ Workspace
```

## 4. Adapter Guardrails

### Resume

OpenHands 可以允许 LLM/context 在恢复时变化；Research OS 先验证 Manifest。模型或关键 Context 改变时必须 Fork/Revision。

### Tool Set

OpenHands 恢复要求工具名一致，因此 Session 的 Effective Tool Set 冻结。

### Direct Tool Execution

绕过 Agent loop 的直接执行必须经过 Research OS Policy Wrapper；高风险调用禁止直接透传。

### Secrets

OpenHands SecretRegistry 只能作为 runtime injection 辅助，不是 canonical secret manager。

## 5. Status Mapping

Canonical `AgentSession` 状态只来自 `docs/reliability/RUN_STATE_MACHINE.md`：

```text
CREATED
INITIALIZING
RUNNING
WAITING_FOR_APPROVAL
PAUSED
STUCK
SUCCEEDED
FAILED
CANCELLED
```

上游状态不是 Domain enum。Adapter 使用显式映射，例如：

```text
OpenHands IDLE                     → CREATED
OpenHands RUNNING                  → RUNNING
OpenHands WAITING_FOR_CONFIRMATION → WAITING_FOR_APPROVAL
OpenHands PAUSED                   → PAUSED
OpenHands STUCK                    → STUCK
OpenHands terminal result          → SUCCEEDED / FAILED / CANCELLED
```

已开始执行的 Session 若再次收到含义不明确的 `IDLE`，Adapter 必须产生映射错误或受控恢复 finding，不得把状态静默回退到 `CREATED`。

## 6. Stuck Handling

结合 OpenHands stuck detector 与 Research OS progress signal：

```text
repeated actions
repeated errors
no artifact/progress
monologue
budget burn without progress
```

触发：

```text
retry
replan
switch agent
require approval
stop
```

## 7. Fork

Fork 用于：

- A/B model；
- alternate strategy；
- tool-set change；
- debug；
- review challenge。

Fork 必须创建新的 Domain lineage，不覆盖源 Run。
