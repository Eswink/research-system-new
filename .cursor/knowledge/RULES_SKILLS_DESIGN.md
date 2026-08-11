# Rule / Skill / Hook / Validator Decision Guide

## Rule

使用 Rule，当内容：
- 跨任务持续成立；
- 简短、可执行；
- 可以明确判断是否违反；
- 主要用于架构边界、权限边界和稳定项目约束。

Rules 应保持 focused、scoped、composable；长解释放 ADR/Knowledge。当前项目 Rule frontmatter 只允许 `description`、`globs`、`alwaysApply`；`globs` 使用逗号分隔字符串，以减少未充分文档化的 parser 表达差异。

## Skill

使用 Skill，当内容：
- 是多步骤流程；
- 需要模板/scripts/references；
- 只在特定任务相关；
- 适合动态按需加载，而不是每轮占用上下文。

例如：
- repository-orientation
- recheck
- governance-check
- refresh-cursor-kb

当前 Skill frontmatter 只使用官方字段 `name`、`description`、`paths`、`disable-model-invocation`、`metadata`；新增 Cursor 字段先进入知识刷新，再进入 validator。

## Subagent

使用 Subagent，当：
- 工作可并行；
- 需要独立上下文；
- 需要独立验证。

本项目单 wave 最多 3 个 child subagent；不是全任务累计配额；禁止嵌套委派。

## Hook

使用 Hook 做机器级观测和 defense-in-depth guard，例如：
- secret 文件访问；
- destructive shell；
- subagent 单波次并发边界；
- opt-in evolution loop。

Cursor Hook 当前存在版本性 enforcement/payload caveat，因此安全要求不能只依赖 Hook。对真正安全边界还要叠加 `.cursorignore`、Cursor approval/run-mode 和 Research OS Sandbox/Policy。

## Validator / Test

能离线确定性验证的规则，优先建立 validator/test：
- frontmatter/schema；
- 文件与引用完整性；
- Rule/Skill/Agent 配置；
- VERSION 一致性；
- release manifest/hash；
- learning replay / promotion invariants。

## Knowledge / ADR

外部事实、兼容性 caveat 和“为什么”放 Knowledge/ADR，不把长背景塞入 Always Rule。

## Script ownership

Cursor 官方 Skills 允许 skill package 携带 `scripts/`、`references/` 和 `assets/`。本项目因此规定：

- 与某一工程工作流绑定的自动化脚本必须放在该 `.cursor/skills/<skill>/scripts/` 下。
- `SKILL.md` 负责解释何时运行以及相对路径。
- 根目录不维护泛化 `scripts/`，避免所有权模糊、上下文路由失效和迁移时遗漏依赖。
- Hook implementation 仍放 `.cursor/hooks/`，因为它们属于 Cursor lifecycle callback，而不是 Skill invocation script。
