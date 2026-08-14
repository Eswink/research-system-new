# Known Cursor Caveats — Observed, Not Normative

这些记录来自 Cursor 官方社区论坛/已确认兼容问题，仅用于 compatibility test；当前官方 docs 始终是规范源。

## Subagents

- 当前官方文档支持有限一层 nested subagents；本项目主动采用更严格的 no-nesting，不应把项目策略描述成 Cursor 平台限制。
- 2026 年社区/官方工作人员确认过部分版本的 custom subagent model pin/variant、background 行为和 nested propagation 存在兼容问题。
- 部分版本报告 `subagentStart` deny UI 显示阻断但实际任务仍执行，因此 Hook 计数只作为 defense-in-depth，不能作为唯一安全边界。
- background subagent 的 `subagentStop` 在部分版本存在不触发/字段不完整问题；本项目 reviewer 使用 foreground，并以 sessionEnd 清理 stale token。

结论：
- 不把 custom subagent 是否自动启动、model 是否绝对 pin、Hook 是否完整回调作为唯一 release truth；
- 更新 Cursor 后运行 framework compatibility/eval；
- 对高风险检查，根代理仍保留最终综合与验证责任。

## Hook Permission

不同 Hook 支持的输出 schema 不相同：
- `subagentStart`: allow/deny，`ask` 不支持；
- `subagentStop`: 当前只定义可选 `followup_message`；
- `postToolUseFailure`: 当前无输出字段；
- `beforeMCPExecution`: allow/deny/ask。

不得把一种 Hook 的 `permission` 输出机械复制到其他 Hook。

## Fail Closed

安全关键 hook 使用 `failClosed: true`。如果特定 Cursor 版本出现 Hook 初始化问题，应先运行 compatibility probe；不得为了“让它能跑”永久关闭 secret/shell/MCP hard gate 而不记录风险。

## Ignore Files

`.cursorignore` 是重要的上下文/文件访问保护，但官方文档明确说明 Terminal/MCP 不受其同等保护；历史版本还出现过 Grep 等工具未完全尊重 ignore 的 bug。因此 Secret 安全不能只依赖 ignore file。

## Global Rules

不要假定 `~/.cursor/rules/*.mdc` 在所有版本都作为项目约束可靠加载。仓库需要的约束全部 version-control 到项目内。

## Model Behavior

以下为父代理模型行为差异观察（非 Cursor 版本/平台事实，不改变官方规范地位）：

- **并行单消息批量遵循差异**：并行子代理要求父代理在同一条消息中发出多个 Task 工具调用；不同模型对此遵循程度不同，弱遵循模型可能把并行 wave 串行化。规则与 sessionStart 注入只能提高遵循率，不构成机制保证。详见 [SUBAGENT_DESIGN.md](SUBAGENT_DESIGN.md) 的"并行启动语义"。
- **deny 后的重试倾向**：fail-closed Hook 拒绝后，弱模型可能无差别重试同一动作形成拒绝循环。本框架在 fail-closed deny 中携带 `agent_message` 说明原因与下一步；若仍出现循环，优先由用户介入，不通过关闭 guard 缓解。
- **智能路由激活依赖**：仅 `alwaysApply` 规则保证全模型恒注入；带 `globs` 的规则（40/41/44/50）依赖 Cursor 智能路由按文件范围激活，不同模型触发质量可能不同。仓库级硬边界因此全部放在 alwaysApply 规则。
- **Custom reviewer 继承退化**：三个治理 reviewer 使用 `model: inherit`，父代理切换为较弱模型时复核质量同步退化；框架保留该取舍以保证可审计性，根代理仍对最终综合负责。
