---
name: governance-check
description: 离线校验 Research OS 的 Cursor Rules、Skills、持久计划、复检、工程记忆、外部技能锁和冻结 Bootstrap 基线。
---

# Governance Check

在以下场景运行：

- 修改 `.cursor/rules/`、`.cursor/skills/`、`.cursor/plans/` 或 `.cursor/memory/` 后；
- 完成项目任务复检前；
- 全局 Impeccable/shadcn 更新后；
- 计划或记忆链接失效、状态不一致时。

## 命令

```powershell
python -B .cursor/skills/governance-check/scripts/validate.py
```

校验器不联网、不写文件，检查：

- `.mdc` 与 `SKILL.md` frontmatter、命名和作用域；
- 子代理最多 3 个且禁止嵌套的唯一预算约束；
- ALL_PLAN、任务状态、证据、复检结果和完成勾选一致性；
- 工程记忆 provenance、置信度、复核日期和来源链接；
- Impeccable/shadcn 全局安装树是否与 `skills.lock.yaml` 一致；
- v0.2.2 `BOOTSTRAP_MANIFEST.json` 中原始文件摘要是否仍匹配；
- Cursor 治理目录中是否出现明显凭据材料。

任一 error 都阻止任务完成。warning 只能通过复检显式记录为 `PASS_WITH_WARNINGS`，不能静默忽略。