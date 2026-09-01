# Cursor Engineering Knowledge Base

Verified: **2026-08-11**
Framework: **v0.4.0**

本知识库用于编写和维护 Research OS 的 Cursor 项目工程层。它不是 Research OS 产品知识库，也不能覆盖根目录 `AGENTS.md`、Accepted ADR 或已批准产品架构。

## 读取顺序

1. `CURSOR_PRIMITIVES.md` — Rule / Skill / Subagent / Hook / MCP / Plugin / Plan Mode 的职责边界。
2. `HOOKS_REFERENCE.md` — 本项目实际使用的 Hook 事件、输入输出和 fail-open/fail-closed 选择。
3. `RULES_SKILLS_DESIGN.md` — 什么时候写 Rule，什么时候写 Skill。
4. `SUBAGENT_DESIGN.md` — 独立复核 Agent、单 wave 最多 3 个子代理约束与确定性 SDK 并行编排路径。
5. `SECURITY_BOUNDARIES.md` — Hooks、MCP、文件和 shell 的安全边界。
6. `CLOUD_AGENT_COMPATIBILITY.md` — IDE/local 与 Cloud Agent 的 Hook 支持差异。
7. `KNOWN_CAVEATS.md` — 社区报告的兼容性问题；仅作为风险提示，不视为规范。
8. `RESEARCH_EVIDENCE.md` — 与 coding-agent 配置、自进化相关的论文证据。
9. `SOURCES.yaml` — 来源、可信等级、验证日期和失效触发器。

## 知识等级

| Tier | 来源 | 用法 |
| --- | --- | --- |
| `T1_OFFICIAL` | Cursor 官方 docs/changelog、开放标准官方规范 | 可作为当前行为/格式的规范依据 |
| `T2_PRIMARY_RESEARCH` | arXiv/论文原文、规范论文 | 可支持设计取舍，不等于 Cursor 行为规范 |
| `T3_OBSERVED_CAVEAT` | Cursor 官方论坛 issue/回复、项目实测 | 仅用于兼容性防御和验证用例 |
| `T4_COMMUNITY_PATTERN` | 社区仓库/模板 | 只能作为模式参考，不能直接晋升为 Rule |

## 更新原则

- Cursor 版本升级、官方 docs schema 变化或 Hook/Skill/Subagent 行为变化时，先运行 `refresh-cursor-kb` 流程。
- 单个社区帖子不得直接改变 hard rule。
- 发现一次工程失败不得直接改 Rule/Skill；先形成可验证学习提案（v0.4 引入）。
- 所有时效性结论必须能追溯 `SOURCES.yaml`。

## Self-evolution

受控学习流程见 `.cursor/learning/README.md`；单次观察不得直接晋升。轻量工程经验缓冲在 `.cursor/experience/`，由 `capture-experience` skill 沉淀，sessionStart 注入摘要，不作为工程事实。

## 2026-08-11 关键更新

- Cursor 官方当前支持有限 Subagent nesting；本项目禁用 nesting 是更严格的项目策略。
- `postToolUseFailure` 官方字段包含 `error_message` 与 `failure_type`，Hook fixture 必须按官方 payload 回归。
- Skill 的 `scripts/` 是官方标准可选目录，脚本从 Skill root 使用相对路径引用。

- Cursor Cloud Agent 的 Hook 支持面与 IDE/local 不同；敏感 MCP 流程不得依赖 Cloud 不支持的 `beforeMCPExecution`。
