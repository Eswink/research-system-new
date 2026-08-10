---
name: all-plan
description: 将用户已批准的 Cursor Plan 固化为 Research OS 项目任务计划，维护 ALL_PLAN 索引、证据化 checklist、状态历史和子代理预算。
disable-model-invocation: true
---

# All Plan

仅在 Cursor Plan 已获用户批准后显式调用。本 Skill 不负责替代 Plan Mode，也不能自行批准计划。

## 创建

1. 从 `.cursor/plans/tasks/` 和 `.cursor/plans/archive/` 计算下一个稳定 `PLAN-YYYYMMDD-NNN`，不得复用 ID。
2. 复制 `assets/task-plan-template.md`，填写所有 YAML 字段和正文。文件名使用 `PLAN-YYYYMMDD-NNN-short-slug.md`。
3. 将 Cursor Plan 的目标、范围、非目标、架构决策、验收条件和验证命令写入任务文件。
4. 记录 `subagent_budget`，其值只能为 0–3；`subagents_used` 从实际累计值开始，任何子代理不得再委派。
5. 在 `.cursor/plans/ALL_PLAN.md` 活动表新增唯一链接，初始不勾选。

## 执行

- 状态按 `APPROVED → IN_PROGRESS → VERIFYING → DONE` 推进；阻塞使用 `BLOCKED`，失效使用 `REOPENED`，不删除旧历史。
- 每完成一项 checklist，先在“证据”表添加文件、命令、digest 或复检引用，再勾选对应项。
- 需求或架构变化先追加 Decision/状态历史；超出批准范围时回到 Cursor Plan Mode，不在任务文件中自行扩张范围。
- 每次委派都更新 `subagents_used` 和委派记录；同一用户任务跨批次累计，最多 3 个。

## 完成

1. 所有验收条件均有证据后，将状态改为 `VERIFYING`，但不勾选 `ALL_PLAN`。
2. 显式调用 `recheck` 创建独立 attempt。
3. 仅当最新复检为 `PASS` 或 `PASS_WITH_WARNINGS` 时：
   - 调用 `engineering-memory` 提炼可复用事实；
   - 将任务状态改为 `DONE`；
   - 追加状态历史；
   - 在 `ALL_PLAN.md` 勾选并链接复检、记忆。
4. 复检为 `REVISE` 或 `BLOCK` 时恢复 `IN_PROGRESS` 或 `BLOCKED`，修复后创建新 attempt，禁止覆盖旧复检。

## 归档

完成任务默认仍保留在总索引的“最近完成”区。需要归档时移动文件并同步所有链接；归档是存储位置变化，不得改写历史。