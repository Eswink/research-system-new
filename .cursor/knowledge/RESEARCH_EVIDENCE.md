# Research Evidence for Agent-Engineering Design

## 1. Configuration practice

`Configuring Agentic AI Coding Tools: An Exploratory Study` (arXiv:2602.14690) 对 2,926 个 GitHub 仓库研究发现，Context Files 是最常见配置形式，AGENTS.md 正成为跨工具互操作入口，而 Skills/Subagents 的实际采用仍较浅。

设计含义：保留短而稳定的 `AGENTS.md`，不依赖堆叠大量高级机制。

## 2. Guardrails vs guidance

`Do Agent Rules Shape or Distort? Guardrails Beat Guidance in Coding Agents` (arXiv:2604.11088) 的大规模实验发现，负向约束是单独最稳定有益的规则类型，过多正向指导可能产生负面效果。

设计含义：Always Rules 主要表达 hard constraints；多步骤正向流程放 Skill/Hook/validator。

## 3. Global skill evolution

`Learning Globally Reusable Skills for Coding Agents` (arXiv:2608.06153) 提出 Skill Relation Graph、cluster-based consolidation 和 replay-driven verification，避免单任务局部更新过拟合，并在 OpenHands/mini-SWE-agent 上展示更好的跨任务泛化。

设计含义：Research OS Cursor Framework 的自学习不能“一次失败就改 Rule/Skill”。应该：

```text
observation
→ proposal
→ cluster/consolidate
→ replay/regression
→ independent review
→ promote
```

v0.3 先搭安全基础，v0.4 才启用该闭环。
