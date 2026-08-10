---
name: recheck
description: 对 Research OS 项目任务执行独立、证据驱动的复检，重新核对验收、diff、校验、风险和外部 Skill 漂移。
disable-model-invocation: true
---

# Recheck

复检从原始任务目标与验收条件重新开始，不以“实现者说已完成”或已勾选 checklist 为依据。

## 创建 attempt

1. 读取任务计划、用户批准的 Cursor Plan、相关 Rules/ADR 和当前仓库状态。
2. 计算 `RECHECK-YYYYMMDD-NNN`。同一任务每次复检创建新文件，不覆盖旧 attempt。
3. 复制 `assets/recheck-template.md`，先冻结本次检查范围与命令，再执行检查。

## 检查顺序

1. **范围**：是否只修改批准范围，是否保留用户已有改动。
2. **架构**：职责、数据流、Canonical State、Port/Adapter、状态机和失败语义是否正确。
3. **验收**：逐条 AC 对应独立证据；无证据即未通过。
4. **质量**：lint、typecheck、test、bundle/governance validator、内部链接与确定性 digest。
5. **安全**：凭据、权限、默认 deny、日志/Prompt 隐私、供应链 pin。
6. **兼容性**：Domain/API/schema、迁移、上游版本和恢复路径。
7. **计划完整性**：状态历史、子代理预算、执行证据和工程记忆 provenance。

## 判定

- `PASS`：全部 hard gate 与验收条件通过。
- `PASS_WITH_WARNINGS`：hard gate 通过，仅剩已记录且不阻塞交付的风险。
- `REVISE`：可修复的不符合项，任务回到 `IN_PROGRESS`。
- `BLOCK`：安全、产品边界、数据完整性或必要环境阻塞，任务进入 `BLOCKED`。

任何 Hard Invariant 失败都不能降级为 warning。复检完成后只更新任务的 `latest_recheck` 和状态投影，保留所有旧报告。