---
name: engineering-memory
description: 从已验证的计划、复检和仓库证据中提炼“做了什么、为何这样做、如何复现”的工程记忆，并维护 provenance、置信度、适用范围和复核策略。
disable-model-invocation: true
---

# Engineering Memory

工程记忆是 Git 中可审阅的协作知识，不是产品 `MemoryRecord`，也不是聊天摘要。

## 写入门禁

仅当事实满足以下条件时写入：

1. 来源于已批准任务计划、通过的复检、当前源码/配置、测试结果、Accepted ADR 或确定性 digest；
2. 能区分事实、决策和推断；
3. 不包含凭据、完整 Prompt、完整模型输入输出、敏感 Tool 参数或个人数据；
4. 对后续任务有复用价值，而不是重复 changelog。

## 流程

1. 从 `.cursor/memory/entries/` 计算下一个 `MEM-YYYYMMDD-NNN`，复制 `assets/memory-entry-template.md`。
2. 写清：
   - 做了什么：稳定结果和改动边界；
   - 为什么：约束、权衡和被拒绝的替代方案；
   - 怎么做：可复现步骤、入口、命令和关键文件；
   - 如何失效：依赖、Schema、Skill digest、架构或运行行为的触发条件。
3. `sources` 必须链接仓库内可验证来源；`source_plans` 和 `source_rechecks` 必须存在。
4. 设定 `confidence`、`scope`、`review_after`、`status` 和 `supersedes`。未知内容明确标注，不用高置信度掩盖证据不足。
5. 更新 `.cursor/memory/INDEX.md`。同一事实更新时新增条目并用 `supersedes` 关联，禁止静默覆盖历史。

## 生命周期

- `ACTIVE`：可用于当前工程决策。
- `SUPERSEDED`：被新证据取代，保留历史引用。
- `RETIRED`：不再适用且无直接替代项。
- 到达 `review_after` 或命中失效触发器后，不得直接引用为事实；先调用 `recheck` 或重新读取来源。

向量索引若未来存在，只能作为可重建投影；本目录 Markdown 与其 Git 历史才是工程记录面。