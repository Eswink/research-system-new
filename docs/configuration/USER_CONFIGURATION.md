# User Configuration v0.2.2

## 1. First-run Wizard

```text
LLM Relay
→ Models/Probe
→ Team Template
→ Tools
→ Workspace/Compute
→ Default Autonomy/Budget
```

## 2. Relay

Required：

```text
Name
Base URL
API Key
```

Optional Advanced：

```text
timeout
concurrency
custom safe headers
TLS/egress policy
```

保持主体验简单。

## 3. Models

用户可：

- 手工添加 Model ID；
- 尝试 discovery；
- 运行 capability probe；
- 标注 context/output limit；
- 配置价格（可选）。

## 4. Team

选择：

```text
Lean
Standard
Rigorous
Custom
```

然后可为每个 Agent 单独选择模型。

## 5. Project Wizard

```text
Objective
Target Profile
Inputs
Data Classification
Team
Protocol
Autonomy
Budget
Deliverable
```

## 6. Dry Run / Preflight

展示：

- Role/Agent；
- Model/eligibility；
- Tool/permissions；
- Workspace/Compute；
- budget；
- gates；
- warnings；
- endpoint/tool health。

## 7. Safe Defaults

```text
GUARDED_AUTONOMOUS
Docker Workspace
Reviewer read-only
public network deny except approved tools
package install approval
external publish approval
content telemetry off
```
