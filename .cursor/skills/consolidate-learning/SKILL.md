---
name: consolidate-learning
description: 聚类多个 LEARN proposal，检查重复/冲突/Skill Relation Graph，并把局部 workaround 抽象为最小可泛化候选。
disable-model-invocation: true
---
# Consolidate Learning

1. 选择一组问题同源的 PROPOSED proposals。
2. 检查 `SKILL_RELATIONS.yaml`、相关 Rule/Skill 和历史 rejected proposal。
3. 输出 cluster record：共同 failure mode、不同上下文、最小共享机制、不能泛化的例外。
4. 优先新增 EVAL/VALIDATOR，再决定是否需要 Rule/Skill。
5. 不复制多个局部规则；发现冲突时阻止 promotion 并要求重新设计。
