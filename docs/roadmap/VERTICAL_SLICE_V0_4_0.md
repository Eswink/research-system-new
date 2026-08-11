# Vertical Slice v0.4.0

## Scenario

用户：

1. 配置一个中转站；
2. 添加 `model-alpha` 和 `model-beta`；
3. 选择 Standard Team；
4. 输入一个小型公开 ML repo 分析/改进目标；
5. 使用 Guarded Autonomous 和低预算。

## Flow

```text
LLM Endpoint Test
→ Model Probe
→ Team Resolve
→ Protocol Compile
→ Preflight
→ Budget Reserve
→ Manifest Freeze
→ DomainResearch Task
→ Handoff
→ Experiment Task
→ Sandbox execution
→ Result Analysis
→ Reviewer Gate
→ Research Report
→ Audit/Export
```

## Failure Injection

必须测试：

- Endpoint 暂时 429；
- duplicate task delivery；
- Tool timeout；
- worker crash/lease expire；
- budget threshold；
- model probe 不支持 tool calling；
- user pause/cancel；
- resume 时 model config drift。

## DoD

- Preflight 能在运行前拒绝不兼容 Model；
- Agent 按配置使用不同 Model；
- Tools/MCP 不受模型配置变化影响；
- duplicate delivery 无重复副作用；
- Run 可恢复；
- Claim 回溯到 Artifact/Evidence；
- Reviewer read-only；
- final audit 可导出。
