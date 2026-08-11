---
name: evolve-framework
description: 用户明确要求框架迭代时，启动有状态、有限 stop-loop 的 Cursor Framework evolution；执行知识刷新、候选改进、回放、确定性验证和受控发布。
disable-model-invocation: true
---
# Evolve Framework

只在用户明确要求框架自我迭代时使用。

状态机脚本：

```bash
python -B scripts/framework_evolution.py status
```

生命周期：

```text
ORIENT → REFRESH_KB → SELECT_PROPOSALS → IMPLEMENT_CANDIDATE → REPLAY → VALIDATE → PROMOTE → RELEASE
```

- 不设置固定审核轮数。
- 不使用数值自评分作为 release truth。
- 高风险变更按范围调用相关 reviewer。
- Release truth 来自确定性 validators/evals + manifest。
- Stop follow-up 仅在 active evolution state 使用，并受 loop limit 限制。
