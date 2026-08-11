# Cursor Cloud Agent Compatibility

本框架的主验证目标是 **Cursor IDE / local agent**。Cursor Cloud Agent 支持项目级 command hooks，但当前官方文档明确列出若干差异。

## 当前官方差异

Cloud Agent 有时会先进入早期只读探索环境；**该阶段项目 Hook 完全不运行**，直到获得可写环境后才开始执行。即使后续支持 `beforeReadFile`，也不能把项目 Hook 当作早期只读阶段的 credential 隔离层。

Cloud Agent 支持包括：

- `beforeShellExecution` / `afterShellExecution`
- `beforeReadFile` / `afterFileEdit`
- `preToolUse` / `postToolUse` / `postToolUseFailure`
- `subagentStart` / `subagentStop`
- `stop`、`preCompact` 等

当前不提供或延后：

- `sessionStart`
- `sessionEnd`
- `beforeMCPExecution` / `afterMCPExecution`
- Tab hooks
- `workspaceOpen`

因此，**不能把 IDE/local 的 MCP guard 当作 Cloud Agent 的安全保证**。

## 本项目策略

- 默认把 Framework 的完整安全 profile 定义为 `ide_local`。
- Cloud 早期只读阶段不得接触真实凭据，也不得依赖项目 Hook、`sessionStart` 注入或 `beforeMCPExecution`；敏感资产必须由仓库/运行环境隔离在该阶段之外。
- Cloud Agent 可以执行普通仓库任务，但高敏感 MCP/credential 工作流只有在存在 Enterprise/Cloud 等价控制或 Research OS 产品级 Sandbox/Policy 时才允许。
- `sessionStart` 注入和 `sessionEnd` stale-state cleanup 只是 IDE/local 增强；产品正确性不能依赖它们。
- Cloud Agent 的项目 hooks 仍来自受版本控制的 `.cursor/hooks.json`，但使用前必须以当前 Cursor 官方文档重新核对支持矩阵。

该文件描述兼容边界，不把 Cloud Agent 视为不安全；它只是提醒不同执行面不能共享未经验证的 Hook 假设。
