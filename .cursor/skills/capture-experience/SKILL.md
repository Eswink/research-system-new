---
name: capture-experience
description: 将本会话已解决的工程问题提炼为轻量经验条目（EXP-YYYYMMDD-NNN）写入 .cursor/experience/；条目是低置信度观察缓冲，不是工程事实。适用于 agent 被 sessionStart 提示、或会话中出现可复现问题并已形成稳定解法时。只创建经验条目，不直接修改 Rule/Skill/Hook/Memory。
paths:
  - ".cursor/experience/**"
  - ".cursor/runtime/observations/**"
  - ".cursor/runtime/distillation/**"
disable-model-invocation: true
---
# Capture Experience

适用：本会话出现工具/validator/构建失败并已解决，或 sessionStart 提示有待沉淀经验。

1. 先读取 `.cursor/runtime/observations/<cid>.jsonl`（cid 为当前 conversation_id 的脱敏值，`common.py::safe_id` 规则）、`session_context.py` 注入的待沉淀提示，以及本会话实际改动与验证输出。
2. 去重：查 `.cursor/experience/INDEX.md` 与 `.cursor/learning/REGISTRY.yaml`，同源问题已在库内时不新建条目；仅当出现新的解决上下文时更新原条目（`occurrences +1`、`supersedes` 关联，不静默覆盖历史）。
3. 新建 `entries/EXP-YYYYMMDD-NNN.md`（模板见 `templates/EXPERIENCE_ENTRY.md`），字段约束：
   - `confidence`：单次观察 ≤ 0.5 并标注"单次观察"；有独立复现或确定性权威证据才可 > 0.5。
   - `occurrences`：独立任务/attempt 次数；跨会话相同 `error_signature` 计为多次。
   - `error_signature`：从本会话 `.cursor/runtime/observations/<cid>.jsonl` 提取（digest，20 位 hex）；无失败记录留空。仅用于 stop 匹配，不进入 LEARN proposal。
   - `source_refs`：必须链接仓库内可验证来源（observations 行、Plan/Recheck、测试输出）。
   - `review_after`：默认 +90 天。
   - 隐私：不记录完整 prompt、模型输入输出、敏感 Tool 参数、凭据、secret 或用户个人数据。
   - 历史条目（无该字段）不迁移，匹配逻辑对缺省/空值跳过。
4. 更新 `.cursor/experience/INDEX.md`（ID/Status/Confidence/Scope/Review After/Summary 一行）。
5. 若同一 `error_signature` 已出现 ≥2 次且尚未生成 LEARN proposal，提示运行 `capture-learning`；但本 skill 不创建 LEARN proposal，也不直接修改任何 Rule/Skill/Hook。
6. 清理 `RUNTIME/distillation/<cid>.json` 中本会话的待沉淀标记（已处理）。