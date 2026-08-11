---
name: semantic-commit
description: 用户或已授权计划明确要求本地语义提交时，执行最小、可审计的 Conventional Commit，包括白名单暂存、范围相关验证、secret 检查和安全回滚说明。
disable-model-invocation: true
---
# Semantic Commit

仅在用户明确要求提交，或当前已授权计划明确包含本地提交步骤时显式调用。Framework 不为每个任务自动创建 commit。

## Preconditions

1. 确认提交授权仍覆盖当前变更范围。
2. `git status --short` 确认实际变更；不触碰任务外用户改动。
3. 如果任务流程要求 `recheck`，最新 recheck 必须是 `PASS` 或 `PASS_WITH_WARNINGS`；如果任务按风险规则不要求 recheck，不得为了提交而制造形式化 recheck。
4. 根据变更范围运行相应 validator/test：
   - system specification → `/system-spec-check`
   - Cursor governance → `/governance-check`
   - Cursor framework → `/cursor-framework-check`
   - learning system → `/learning-check`
   - 产品代码 → 对应 lint/typecheck/test

## Commit

1. 用明确路径逐项 `git add <path...>`；禁止 broad add。
2. 再检查 `git diff --cached --check`、`git diff --cached --stat` 和 staged diff。
3. 对 staged 内容执行 secret 检查。
4. 使用 Conventional Commit，并让 message 描述一个语义单元。
5. 提交后核对 `git status --short`；报告未提交但不属于本任务的改动。

## Remote Side Effects

本 Skill 默认只创建本地 commit。`git push`、PR、tag、release 需要单独的明确用户授权，不因为本地 commit 授权而自动获得。
