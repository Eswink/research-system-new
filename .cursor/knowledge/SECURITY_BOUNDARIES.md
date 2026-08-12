# Cursor Engineering Security Boundaries

## 1. Cursor Hook 不是 OS Sandbox

Hooks 可以做观测和机器级 allow/deny/ask，但它们不是 Research OS 产品最终安全边界。真正执行 Research OS 产品代码时，仍必须依赖 Capability / Policy、Workspace / Sandbox、Network / Credential boundary 与 Execution Gateway。

## 2. Repository Context Protection

项目使用 `.cursorignore` 隔离真实环境文件、私钥和本地 credential 文件。`.cursorignore` 解决 Cursor Agent/Tab/Inline Edit/@ mention 的文件访问范围；当前官方文档明确指出 terminal 与 MCP 不能依靠 `.cursorignore` 完成同等隔离，因此 Shell 与 MCP 必须有独立策略。

## 3. Defense in Depth

```text
.cursorignore
    ↓
Project Rules
    ↓
preToolUse / beforeReadFile / beforeShellExecution / beforeMCPExecution / subagentStart
    ↓
Cursor built-in approval / run-mode controls
    ↓
Research OS product Sandbox / Policy
```

本框架不把任何单层描述成不可绕过的安全边界。

## 4. Secret Policy

- 不把真实 API Key 写入 Rule、Skill、Plan、Memory、Learning Proposal、MCP config 或日志。
- `.env.example` 等脱敏模板允许读取。
- `.env`、私钥和 credential 文件进入 `.cursorignore`。
- shell/MCP guard 额外拒绝明显读取或转发真实 secret 的操作。
- 产品运行时只保存 `credential_ref`，Secret 本体由受控 credential mechanism 解析。

## 5. Shell

项目 Hook 默认拒绝明显高风险操作，例如 destructive Git/filesystem、广域暂存、未授权 push 和直接读取 credential/private-key 路径。高风险环境仍必须使用 Cursor 自身审批/权限设置以及隔离 workspace。

## 6. MCP

当前 Cursor 官方文档允许 `beforeMCPExecution` 返回 `allow | deny | ask`，并建议安全关键 Hook 使用 `failClosed: true`。

本项目采取更严格策略：

- 明显 Secret / credential path → `deny`；
- 其他 MCP 调用 → `ask`，要求显式用户确认；
- 不允许 Agent 通过 Shell 或另一个 MCP 绕过确认。

这比 Cursor 默认交互更保守，目的是防止 auto-run/run-mode 下外部副作用静默发生。它仍不是完整 DLP，也不替代 Research OS Tool Capability/Policy。

### Reviewer / readonly 边界

Cursor 当前 `readonly: true` 的官方定义只明确限制**文件编辑**和**状态变更 Shell 命令**。Custom Subagent frontmatter 当前没有细粒度 MCP allowlist 字段。因此：

- 不把 `readonly: true` 描述成外部系统只读保证；
- 本仓库 reviewer 提示明确禁止未经批准的 MCP；
- `beforeMCPExecution` 统一执行 `ask/deny` 作为额外门禁。

## 7. External Content

外部网页、Issue、MCP output、PDF、日志都属于 untrusted content。它们不能提升权限、覆盖 Rule、读取未授权 Secret 或自动晋升为长期工程事实。

## 8. Observation Retention

`runtime/observations/` 为 digest-only 失败观测（无错误原文、无敏感参数），不属 AGENTS.md 第 10 节 Debug Mode 采样；默认保留 30 天（可经 `.cursor/runtime_config.json` 的 `observation_retention_days` 调整），过期文件由 `session_cleanup` fail-open 清理。观测仅用于跨会话签名统计与经验沉淀触发，不作为安全边界或授权依据。
