# Autonomy Levels & Gates

## Levels

### OBSERVE_ONLY

Agent 只规划/分析，不执行写操作。

### SUPERVISED

每个有副作用的 Task 需要审批。

### GUARDED_AUTONOMOUS

低风险自动；高风险、预算扩张、外部发布需要审批。默认推荐。

### FULLY_AUTONOMOUS

在固定 Policy/预算/Sandbox 内自动运行；仍不能绕过硬安全规则。

## Gate Types

```text
POLICY_GATE
BUDGET_GATE
QUALITY_GATE
HUMAN_GATE
SECURITY_GATE
PUBLISH_GATE
```

## Intervention

用户可以：

```text
pause
resume
cancel
approve/reject
replace agent for future task
fork task/run
request explanation
reduce/raise budget
```

运行中替换模型/Tool Set 必须产生 Manifest Revision 或 Fork。
