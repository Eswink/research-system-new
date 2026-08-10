# Research OS Cursor 工程治理层

本目录保存 Agent 在仓库内协作所需的规则、可复用流程、活动计划、复检证据与工程记忆。它不属于 Research OS 产品运行时，也不进入产品 Domain。

## 权威顺序

发生冲突时按以下顺序处理：

1. 根目录 `AGENTS.md` 与 Accepted ADR
2. `docs/architecture/`、`docs/security/` 等已批准产品文档
3. `.cursor/rules/` 中按作用域生效的项目规则
4. `.cursor/plans/tasks/` 中当前已批准的任务计划
5. `.cursor/memory/` 中有来源且仍有效的工程记忆
6. `.cursor/skills/` 的流程说明与模板

Rules 不能重新定义产品边界；Skills 不能覆盖 Rules；计划不能把未批准决策提升为事实；工程记忆不能替代源码、测试、ADR 或运行时证据。

## 职责分离

| 资产 | 职责 | 禁止承担的职责 |
| --- | --- | --- |
| `AGENTS.md` | 产品边界和不可变工程契约 | 任务执行日志 |
| `.cursor/rules/` | Cursor 中可执行、可作用域化的协作约束 | 复制整份架构文档 |
| `.cursor/skills/` | 可重复的操作流程、模板和校验器 | 保存任务进度 |
| `.cursor/plans/ALL_PLAN.md` | 活动任务总索引和完成投影 | 保存详细实施历史 |
| `.cursor/plans/tasks/` | 单任务计划、状态和追加式执行记录 | 产品 `ResearchTask` 持久化 |
| `.cursor/plans/rechecks/` | 独立验收与复检 attempt | 自报完成 |
| `.cursor/memory/` | 经证据提炼的工程事实与决策经验 | 自由聊天摘要或产品 Memory |
| `.cursor/hooks.json` + `.cursor/hooks/` | 会话结束兜底快照提交 | 替代任务语义提交（语义提交见 `43-git-commit-policy.mdc`） |

## 标准闭环

```text
Cursor Plan Mode 只读研究
→ 用户批准
→ all-plan 固化任务计划
→ 实施并追加证据
→ recheck 独立复检
→ engineering-memory 提炼
→ ALL_PLAN 勾选
→ 按 43-git-commit-policy.mdc 执行 git 提交（仅本地）
→ 到期或变更触发再复检
```

只有关联复检结果为 `PASS` 或 `PASS_WITH_WARNINGS` 的任务才能标记 `DONE` 并在 `ALL_PLAN.md` 中勾选。复检为 `REVISE` 或 `BLOCK` 时必须回到实施状态。

## 产品 Memory 隔离

工程记录使用 `PLAN-*`、`RECHECK-*`、`MEM-*` 标识。不得把它们命名或映射为 `MemoryRecord`、`MemoryWriteProposal`、`ResearchTask`、`TaskContract`、`HandoffBundle`、`PreflightReport` 或 `RunManifest`，也不得写入产品数据库、事件流、向量索引或 Agent Runtime Context。

## 安全与隐私

- 不在计划、复检或记忆中写入 API Key、令牌、凭据值、完整 Prompt、完整模型输入输出或敏感 Tool 参数。
- 记录命令时只保存复现所需的非敏感命令、摘要、状态与必要的脱敏输出。
- 外部 Skill 的来源、revision 和安装树摘要由 `skills.lock.yaml` 管理；漂移必须显式复核，不能静默接受。