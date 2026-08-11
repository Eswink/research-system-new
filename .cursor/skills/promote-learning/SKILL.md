---
name: promote-learning
description: 将经过重复证据、before/after replay、确定性验证和显式授权的 LEARN proposal 晋升到长期工程资产。
disable-model-invocation: true
---
# Promote Learning
1. 验证 proposal / Registry 一致。
2. 普通经验至少有两个独立 task occurrence；安全严重问题必须有确定性 reproduction。
3. 执行 before replay。
4. 应用候选修改。
5. 执行 after replay 和全量 regression。
6. 保存 `validation.commands`、`validation.evidence_refs` 与 `validation.result=PASS`。
7. 根据修改范围选择必要 reviewer；不存在固定 reviewer 人数或固定 review round。
8. 获得显式 `promotion.authorization_ref` 后才能设为 `ACCEPTED`。
9. 保存 promoted/regression digest。
