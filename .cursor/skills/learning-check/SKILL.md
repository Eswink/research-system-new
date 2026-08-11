---
name: learning-check
description: 校验 Cursor Framework 受控学习系统的 Registry、Proposal、Skill relation、Replay/Promotion 证据，并运行 learning regression cases。
disable-model-invocation: true
---
# Learning Check

修改 `.cursor/learning/`、learning schema、promotion policy 或 learning-related Skill 后显式运行：

```bash
python -B scripts/validate_cursor_learning.py
python -B scripts/run_cursor_learning_evals.py
```

任一命令失败都禁止晋升长期 Rule/Skill/Knowledge，也禁止 Framework release。
