# Cursor Primitives — Project Engineering Model

## 1. AGENTS.md

用途：仓库级、跨工具兼容的高层工程契约。

适合：
- 产品边界；
- 不可破坏的架构原则；
- 仓库级完成标准；
- 对 Cursor/Codex/Claude 等多个 coding agent 都应成立的约束。

不要：保存动态任务状态或大量 Cursor 专属流程细节。

## 2. Project Rules

位置：`.cursor/rules/**/*.mdc`。

用途：稳定、可作用域的约束。当前 Cursor 通过 `alwaysApply`、`description` 和 `globs` 决定 Always / intelligent / file-scoped / manual 行为。

当前官方 Rule frontmatter 的激活字段是：

```text
description
globs
alwaysApply
```

本项目将这三个字段视为当前可接受 schema；Cursor 新增字段时必须先执行 `refresh-cursor-kb`，再更新 validator。为减少 Rule parser 兼容性歧义，本项目的 `globs` 统一使用逗号分隔字符串，不依赖 YAML list 行为。

项目策略：
- Always Rule 优先表达 hard negative constraints；
- 正向的多步骤“怎么做”迁移到 Skill；
- 文件特定约束用 `globs`，避免所有会话注入；
- 不复制整份架构文档，用路径引用 canonical docs。

## 3. Agent Skills

位置：`.cursor/skills/<name>/SKILL.md`。

用途：可重复、多步骤、可携带 scripts/references/assets 的程序化工作流。

当前官方 Skill frontmatter 字段：

```text
name                      required
description               required
paths                      optional
disable-model-invocation   optional
metadata                   optional
```

其中 `name` 只使用小写字母、数字和连字符，并与包含 `SKILL.md` 的目录名一致；`paths` 官方支持逗号分隔字符串或字符串列表。新的 Skill 使用 `paths`，不使用 legacy `globs`。

要求：
- `name` 与目录一致；
- 必须有 `description`；
- 新 Skill 用 `paths` 做文件范围；
- `disable-model-invocation: true` 仅用于必须显式触发的高风险/发布流程；
- Skill 内公开脚本从 Skill root 用相对路径（例如 `scripts/validate.py`）引用。

## 4. Subagents

位置：`.cursor/agents/*.md`。

用途：独立 context、并行工作流和真正独立复核。

当前官方 Custom Subagent frontmatter 字段：

```text
name
description
model
readonly
is_background
```

官方允许这些字段省略并使用默认值；本项目的治理 Reviewer 为了可审计性全部显式声明。`readonly: true` 的官方保证只覆盖文件编辑和状态变更 Shell，不能被解释成 MCP/外部系统权限隔离。

本项目只定义三个治理 Reviewer：
- architecture-reviewer
- verification-reviewer
- security-governance-reviewer

它们都 `readonly: true`、`model: inherit`、`is_background: false`，并遵循项目“每个并行 wave 最多 3 个子代理，禁止子代理继续委派”的额外治理约束。Cursor 平台当前支持有限嵌套；本项目 no-nesting 是更严格的项目策略。

## 5. Hooks

位置：`.cursor/hooks.json` + `.cursor/hooks/`。

用途：把高价值约束从“模型应该记住”下降为机器检查。

当前项目 `hooks.json` 使用 schema `version: 1`。Cursor 当前 per-hook 定义可包含：

```text
command
type
timeout
loop_limit
failClosed
matcher
```

Prompt Hook 还使用 `prompt`，并可使用 `model`。本项目当前只采用 command hooks；任何新增 Hook event 或配置字段必须先刷新 Cursor 知识库。项目 Hook command 从 project root 运行，因此脚本路径写成 `.cursor/hooks/...`。

项目原则：
- 安全 hard gate 使用 command hook，不使用 prompt hook；
- 需要强制阻止的行为返回 `deny`/exit 2；
- 安全关键 hook 使用 `failClosed: true`；
- 观测型 hook fail-open；
- Hook 只写 `.cursor/runtime/` 临时状态，不修改产品 Domain。

## 6. MCP

用途：Cursor 工程 Agent 连接外部工具和数据。

Research OS 产品内部 MCP 与 Cursor 工程 MCP 是两个不同层次。项目 MCP 配置不能成为产品 ToolProvider 的 canonical truth。

## 7. Plugins

Cursor Plugin 可打包 Rules、Skills、Agents、Commands、MCP 和 Hooks。当前框架暂不插件化；等 v0.4 的接口和学习闭环稳定后再评估，避免过早固化分发格式。

## 8. Plan Mode

复杂、多文件、架构性任务优先使用 Cursor Plan Mode 进行只读调查和可编辑计划。本仓库的 `.cursor/plans/` 是获批后的持久执行投影，不替代 Cursor 自身 Plan Mode。
