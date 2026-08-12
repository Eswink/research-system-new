---
id: EXP-YYYYMMDD-NNN
status: ACTIVE
created_at: YYYY-MM-DD
confidence: 0.0
scope: repository
review_after: YYYY-MM-DD
occurrences: 1
supersedes: []
source_refs: []
---

# 标题：一句话概括问题与解法

## Problem

- 现象：实际观察到的失败/错误行为。
- 上下文：发生的模块、工具、命令或场景（不记录完整 prompt、敏感参数与凭据）。
- 影响：阻塞了什么、重复频率。

## Solution

- 根因：定位到的原因；单次观察时明确标注"单次观察，未经独立复现"。
- 解法：可复现的处理步骤、命令、关键文件与入口。
- 被拒方案：尝试过但无效的做法（如有）。

## Evidence

- source_refs：本会话 observations（`.cursor/runtime/observations/<cid>.jsonl` 行号）、Plan/Recheck、测试输出等可验证来源。
- 如何失效：当依赖、Schema、Skill digest 或运行行为变化时本条可能不再适用。

## 备注

- 本条是经验缓冲，不是工程事实；重复 occurrence ≥2 时由 capture-learning 生成 LEARN proposal，晋升仍走既有门禁。