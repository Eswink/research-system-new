# Cursor Hooks Reference

本文件只记录本框架实际依赖的 Hook 语义。

| Hook | 用途 | 类型 |
| --- | --- | --- |
| `sessionStart` | 注入框架/知识入口 | observational |
| `preToolUse` (`matcher: Read`) | 在文件正文进入 Hook 载荷前按目标路径阻断 secret/private-key 读取 | hard |
| `beforeShellExecution` | 危险 shell/git/fs 阻断 | hard |
| `beforeMCPExecution` | 明显 secret/path 外发阻断 | hard |
| `preToolUse` (`matcher: Task`) | Task 委派前的并发检查 | guard |
| `subagentStart` | active subagent 计数与第二层并发检查 | guard |
| `subagentStop` | 按官方 type/task payload 匹配并释放一个 active token；`sessionEnd` 兜底清理 | cleanup |
| `afterFileEdit` | 记录改动路径 | observational |
| `preCompact` | compaction checkpoint | observational |
| `postToolUseFailure` | 脱敏失败 observation | observational |
| `stop` | opt-in evolution continuation / snapshot | controlled |

## 原则
- Hook command 通过 stdin/stdout JSON 与 Cursor 交互；安全 Hook 以 UTF-8 bytes 读取 stdin（接受 UTF-8 BOM），并以 UTF-8 bytes 输出 JSON。
- 安全 Hook 使用 fail-closed，但 Hook 本身不是 OS sandbox。
- Read 凭据门禁绑定 `preToolUse` 的 `matcher: Read`；`.cursorignore` 同时保留为 Cursor 原生上下文边界。
- `stop` 自动 follow-up 只允许在用户显式启动 evolution state 中出现。
- Subagent 数量按**同时 active / 单 wave**限制，不做整个用户任务累计计数。

## Cursor 3.14.7 / Windows 实测

- 实测 `beforeReadFile` stdin 带 UTF-8 BOM；部分包含中文和引号的文件正文被放入 `content` 后会形成无效 JSON。`failClosed` 会正确阻断，但会把普通源码读取锁死。
- 本项目不修复或猜测损坏的 JSON，也不对无效载荷 fail-open；Read 安全判定前移到 `preToolUse(Read)`，只检查 `tool_input.path` / 兼容 `file_path`。
- 实测普通 Read 放行、`.envrc` 被 Hook 拒绝、惰性 PowerShell 根目录删除探测被 Shell Hook 拒绝；BOM、畸形 JSON、非对象、非法 UTF-8 和中文 stdout 由 subprocess 回归覆盖。

## 兼容性 caveat
截至 2026-08-10，Cursor 官方社区工作人员确认过：`subagentStart` deny 在部分版本可能未被执行；background subagent 可能不触发 `subagentStop`；subagent hook linkage 仍有缺口。因此采用 Rule + foreground custom reviewer + best-effort Hook 的多层策略。

- 安全关键 `beforeMCPExecution` 使用 `failClosed: true`；MCP guard 仅是 defense-in-depth，不替代产品 Capability/Policy。

## Subagent cleanup 说明

Cursor 当前 `subagentStart` 提供 `subagent_id` / `parent_conversation_id`，但官方 `subagentStop` 专用字段不提供这两个 ID。框架不能假造不存在的字段做精确删除，因此 start token 保存 `subagent_type + task digest`，stop 优先在 common `conversation_id` bucket 中匹配，必要时对 active token 做降级匹配；`sessionEnd` 负责最终清理 stale state。该机制是并发提示/防御，不是强一致分布式 semaphore。
