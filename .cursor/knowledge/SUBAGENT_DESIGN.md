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

### 并行启动语义

官方语义（T1 来源 `cursor-subagents`，[cursor.com/docs/subagents](https://cursor.com/docs/subagents)）：并行执行要求 Agent **在一条消息中同时发出多个 Task 工具调用**，子代理才会同时运行；逐个发出并等待完成属于串行。

工程观察（非官方平台事实）：不同模型对"单条消息批量发出工具调用"的遵循程度存在差异，指令遵循较弱的模型可能把并行 wave 合法地串行化，使波次耗时成倍放大。规则与 sessionStart 注入只能提高遵循率，不构成机制保证；串行化复现时应检查父代理模型配置，并在规则约束内重新要求单消息批量启动。子代理之间存在真实数据依赖时属于 sequential 委派，应显式说明依赖关系，不伪装成并行。

**诊断步骤**：若并行意图未生效且未收到 Hook deny，先确认是否单消息批量；若收到 deny，查 `.cursor/runtime/subagents/<cid>/*.active` 是否已达 3 并核验 `preToolUse(Task)`/`subagentStart` 的 `task` 字段是否走 `prompt`/`description` 别名（2026-08-22 起 Hook 已兼容两者）。

### 确定性替代路径：SDK 并行编排

当确需真实并发且原生批量调用不可依赖时，使用显式 `parallel-agent-orchestration`
Skill（`disable-model-invocation: true`，需用户或根 Agent 明式启动）：

- TypeScript `@cursor/sdk` 编排器在 Node 进程里为每个任务创建**独立顶层 Agent 会话**，
  用 `Promise.allSettled` 真实并发启动、等待和汇总，并发决策与父模型无关。
- 每 wave 上限同样为 3（`runner.ts` 硬编码），无累计任务上限，`tools` 不含
  `task`/`mcp`/`shell`（工具面禁止嵌套委派与 Shell/MCP），并启用 SDK sandbox。
- 该路径不产生 Cursor 会话内子代理，不触发 `subagentStart/subagentStop` Hook，
  因此 `subagent_guard` 三路计数不适用；编排器自带同等上限。
- 资格、分辨率与 NOT VERIFIED 项见
  `docs/references/upstream/CURSOR_SDK_QUALIFICATION.md`（@cursor/sdk 1.0.30）。
- 诊断顺序：先区分"单条消息未批量发送"→"Hook deny/active count"→
  "模型目录/fallback"→"SDK 编排器运行是否重叠"。

### Hook 兼容性

为兼容不同 Cursor 版本的载荷差异，`subagentStart` 的任务文本同时接受 `task`/`prompt`/`description`/`agent_prompt` 别名，`subagent_type` 缺省时回退为 `generalPurpose` 计数；`preToolUse(Task)` 与 `subagentStart` 统一按 `parent_conversation_id || conversation_id` 的 `safe_id` 归桶，`subagentStop` 按任务签名与类型评分释放，`sessionEnd` 额外按 `created_at` TTL 清理残留。详见 `HOOKS_REFERENCE.md` 的 Subagent cleanup 说明。

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
