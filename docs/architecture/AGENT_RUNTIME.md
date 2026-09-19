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

### 3.1 装配事实（PLAN-20260919-107 / GOAL-007 EC-01）

**runtime 是配置驱动的选择面**：两个组合根（`services/api/composition.py` 与
`services/api/pg_composition.py`）都读同一个选择点
`services/api/runtime_support.py::build_agent_runtime`。

| 取值（`RESEARCHOS_AGENT_RUNTIME`） | 装配结果 | 说明 |
| --- | --- | --- |
| 未配置 / 空 | 受控 demo 执行体（Fake） | **默认**；CI 与离线开发不依赖网络 |
| `fake` | 同上 | 显式选择与默认都进选择结果（`configured` 区分两者） |
| `openhands` | `OpenHandsRuntimeAdapter` | 需要可解析凭据面与 policy 求值面，缺一点名拒绝 |

- **未知取值 fail-closed**：装配期报错并点名取值，**不静默回退** Fake——静默回退会让
  「我配了真实 runtime」与「我跑的是 demo」不可区分（AGENTS.md §4 要消灭的漂移）。
- **取值词表归组合层**：`packages/application/ports/**` 有 provider token 字符串门禁
  （`test_provider_types_do_not_leak_from_ports`），因此 Port 与 Domain 只见**中性的
  基质标识字符串**（`RunManifest.execution_backend`）。
- **选择结果进 manifest，并经既有读面可判**：组合根把选择写进
  `PreflightContext.execution_substrate`，`freeze_manifest` 冻结为
  `RunManifest.execution_backend`，并随 `MANIFEST_FROZEN` payload 出现在
  `GET /runs/{id}/events` 上（零 DTO / 路由 / OpenAPI / 迁移变化）。
- **本节不宣称的部分**：受控出网门链（端点 URL 策略 / 凭据存在性 / 端点健康 / 能力
  匹配）属 GOAL-007 EC-02，真实 runtime 的离线全链属 EC-03。EC-01 只保证**构造路径
  可用且可判**、且构造**不发起任何出站调用**——「能装配」不等于「已放行执行」。

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
