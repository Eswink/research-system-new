# Subagent Design

Cursor 将 Subagent 定位为独立上下文的专业 Agent，可用于并行工作、代码库探索和独立验证。项目级 Custom Subagent 位于 workspace root 的 `.cursor/agents/*.md`。

## Cursor 官方能力边界

当前 Cursor 官方文档明确支持**有限嵌套**：主 Agent 和其直接 Subagent 可以启动 child Subagent，但第二层 child 不能继续向下启动。Subagent 默认继承父级工具，包括本地会话中配置的 MCP 工具；Cloud Subagent 是例外。

这属于 Cursor 平台能力，不等于本仓库必须启用它。

## Research OS 项目策略

Subagent 不是默认步骤，只在可明显并行的调查、模块验证或上下文隔离有收益时使用。

### 数量

```text
每个并行 delegation wave < 4
```

即同时最多 3 个 child subagent。

**没有整个用户任务累计最多 3 个的限制。**上一 wave 全部结束、根代理完成整合后，如果仍有新的独立必要工作，可以启动下一 wave。

### 嵌套：本项目采用比 Cursor 更严格的策略

尽管 Cursor 平台支持有限一层 child nesting，本项目 v0.4.0 **主动禁用 nested delegation**：只允许直接服务用户的 root Agent 创建 Subagent。

这是 Research OS Cursor Engineering Framework 的治理选择，不是 Cursor 技术限制。原因：

- 让根 Agent 保持最终责任和结果整合；
- 控制成本、上下文树和并行 fan-out；
- 降低 MCP/tool 权限随 Subagent 继承产生的治理复杂度；
- 当前 Hook/模型选择等实现仍存在版本相关 caveat。

如未来要开放 Cursor 官方支持的有限 nesting，必须通过 Framework proposal、Hook/permission regression 和独立安全复核，不得仅删除一条 Rule。

## Tool / MCP 继承

Cursor 官方当前行为是 Subagent 继承父 Agent 的工具，包括配置的 MCP 工具。因此：

- `readonly: true` 只用于限制写文件和状态变更 shell，不能被描述成细粒度 MCP allowlist；
- 高风险 MCP 必须在项目 MCP 配置、Cursor approval/Hook 与 Research OS 自身 Capability/Policy 层控制；
- 不把 Custom Subagent frontmatter 当作 MCP 权限隔离边界。

## Hook caveat

本仓库使用 `preToolUse(Task)` 与 `subagentStart`/`subagentStop` 做 best-effort active-count defense-in-depth。

官方 schema 支持 `subagentStart` allow/deny；但 Cursor 官方论坛在部分版本记录过 deny enforcement、background stop 事件和 model selection 的实现偏差。因此：

- custom reviewer 使用 `is_background: false`；
- Rule 仍是必要的语义约束；
- Hook 不是 OS sandbox，也不宣称单独证明完整调用树；
- caveat 只能记录为兼容性事实，不能覆盖官方 schema。
