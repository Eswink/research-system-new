# Changelog

## v0.4.0 — 2026-08-10

- Cursor 工程自动化脚本迁移到对应 `.cursor/skills/<skill>/scripts/`；删除根 `scripts/`。
- 清理遗留的双版本语义与 `research_os_baseline` session context。
- Reviewer 输出改为 hard gate + evidence，不固化数值自评分。
- Plan Mode 改为风险/歧义驱动；明确用户已授权实现时不重复确认。
- 区分 learning lifecycle 与 framework evolution lifecycle。


当前主包统一为一个版本体系。

### Research OS
- 用户通过 OpenAI-compatible 中转站配置 `Base URL + API Key + Model ID`。
- 每个 Agent 可独立绑定模型。
- Role / Agent / Task / Handoff 分离。
- OpenHands Native 是 MVP Agent Runtime adapter。
- Tool / Skill / Capability、Workspace、Evidence、Experiment、Evaluation 保持独立。
- 包含 Protocol compile/preflight、可靠任务语义、预算、数据治理和安全边界。

### Cursor Engineering Framework
- Project Rules 使用 `.cursor/rules/*.mdc`。
- Agent Skills 使用 `SKILL.md`。
- Custom Subagents 使用 `.cursor/agents/*.md`。
- Hooks 提供 secret/shell/subagent/evolution 等机器级控制。
- Cursor 工程知识库存放于 `.cursor/knowledge/`。
- 自学习采用 Observation → Proposal → Replay → Validation → Promotion。
- Subagent 改为“按波次最多 3 个”，取消整个用户任务累计 3 个上限。
- 发布质量由确定性 validators/evals + release manifest 驱动；独立 reviewer 按变更风险选择。
