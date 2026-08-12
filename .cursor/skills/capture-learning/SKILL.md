---
name: capture-learning
description: 将重复 validator/tool/review failure 或用户纠正提炼为证据化 LEARN proposal；只创建提案，不直接修改 Rule/Skill/Hook。
paths:
  - ".cursor/learning/**"
  - ".cursor/runtime/observations/**"
disable-model-invocation: true
---
# Capture Learning

适用：出现可复现工程问题、重复纠正或稳定 workaround。

1. 先读取 `.cursor/runtime/observations/`、活动 Plan/Recheck 和相关源码。
2. 去重 `REGISTRY.yaml` 与 `.cursor/experience/INDEX.md`，避免重复提案；经验库中同源条目可作为 occurrence 证据。
3. 新建 `LEARN-YYYYMMDD-NNN.yaml`，填写 source refs、occurrences、reproduction、confidence 和 proposed target。
4. 不得直接改被建议的 Rule/Skill/Hook。
5. 单次普通失败只能保持 `PROPOSED`；等待第二个独立 occurrence 或 deterministic+authoritative evidence。
6. 更新 registry。
