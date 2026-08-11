---
name: governance-check
description: 离线校验 Research OS Cursor Rules、Skills、计划/复检/工程记忆、外部技能锁、框架知识库、Hooks/Subagents 与单一版本策略。
---
# Governance Check

Cursor 治理资产有变更或任务复检前运行：

```bash
python -B scripts/validate.py
/cursor-framework-check
```

如果同时修改 Research OS specification，再运行：

```bash
/system-spec-check
```

任一 error 阻止任务完成；warning 必须在 recheck 中显式处置。
