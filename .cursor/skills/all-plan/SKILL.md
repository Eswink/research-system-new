---
name: all-plan
description: 将已授权的复杂/长时程 Cursor 工作固化为 Research OS 项目任务计划，维护 ALL_PLAN、证据化 checklist、状态历史和按波次子代理记录。
disable-model-invocation: true
---
# All Plan

用于长时程、多阶段、跨会话恢复或需要正式验收证据的工作。授权来源可以是：

- 用户已经审阅的 Cursor Plan；或
- 用户当前请求已经明确授权实施，且计划内容没有扩大该授权范围。

本 Skill 不自行扩大权限，也不要求对已经明确授权的同一工作重复确认。

## 创建
1. 从 `.cursor/plans/tasks/` 和 `.cursor/plans/archive/` 计算下一个稳定 `PLAN-YYYYMMDD-NNN`。
2. 复制 `assets/task-plan-template.md` 并填写 YAML 与正文。
3. 写入授权来源、目标、范围、非目标、架构决策、验收条件和验证命令。
4. `subagent_parallel_limit` 固定为 3；只表示每个并行 wave 的最大 child 数量，不是整个任务累计预算。
5. 在 `.cursor/plans/ALL_PLAN.md` 增加唯一链接。

## 执行
- 状态按 `APPROVED → IN_PROGRESS → VERIFYING → DONE` 推进；如果授权仍待用户确认则保持 `DRAFT`。
- 每完成一项 checklist，先记录证据，再勾选。
- 子代理仅在并行收益明确时使用；简单任务不委派。
- 一个 wave 最多 3 个子代理；下一 wave 前必须整合上一 wave。
- 子代理不得再委派子代理。
- 若需求/架构超出当前授权范围，回到 Plan Mode 并获取新授权。

## 完成
1. 验收条件有证据后进入 `VERIFYING`。
2. 显式调用 `recheck`。
3. 最新复检通过后才进入 `DONE` 并更新 `ALL_PLAN`。
4. 有稳定、可复用工程事实时再写 `engineering-memory`。
