# Engineering Experience Library v0.4.0

本目录是 Cursor Engineering Framework 的**轻量工程经验缓冲层**，记录 agent 在开发中遇到的问题、原因与解法。

## 定位与边界

- 经验条目 = **结构化 Observation 缓冲**，不是工程事实；不得被当作 Rule/Skill/Memory 或产品 `MemoryRecord` 直接引用。
- 低置信度是默认状态：单次观察的条目 `confidence <= 0.5` 且必须标注"单次观察"。
- 跨会话重复（≥2 个独立 occurrence）才允许升级为 LEARN proposal（见 `.cursor/learning/`），晋升仍走既有 promotion 门禁。
- 隐私约束与 `.cursor/hooks/failure_observer.py` 一致：不记录完整 prompt、模型输入输出、敏感 Tool 参数、凭据或 secret。
- 本目录属于 `.cursor/` 工程层，生命周期由 `.cursor/rules/22-learning-promotion.mdc` 管辖。

## 生命周期

- `ACTIVE`：当前可复用。
- `SUPERSEDED`：被新条目取代，保留历史。
- `RETIRED`：不再适用且无直接替代项。
- 到达 `review_after` 或命中失效触发器后，不得直接引用为事实，先复检来源。

## 结构

```text
experience/
├── README.md                 # 本说明
├── INDEX.md                  # 条目索引（sessionStart 注入与检索入口）
├── templates/
│   └── EXPERIENCE_ENTRY.md   # 新条目模板
└── entries/
    └── EXP-YYYYMMDD-NNN.md   # 条目正文
```

## 沉淀与复用

- 沉淀：agent 在会话中被提示或判断"已形成稳定解法"时，运行 `capture-experience` skill 写入新条目并更新 `INDEX.md`。
- 复用：每次会话开始，`.cursor/hooks/session_context.py` 会把 INDEX 中最近 ≤5 条摘要注入上下文；遇到问题时先查 `INDEX.md` 再动手。
- 升级：`capture-learning` skill 在生成 LEARN proposal 前先对经验库去重，重复条目可作为 occurrence 证据。

## 与既有目录的关系

| 目录 | 层级 | 写入门槛 | 事实性 |
| --- | --- | --- | --- |
| `.cursor/experience/` | 观察缓冲 | 低（问题+原因+解法） | 否，仅经验 |
| `.cursor/learning/` | 学习提案 | 中（LEARN proposal） | 否，提案 |
| `.cursor/memory/` | 工程记忆 | 高（计划/复检证据） | 是 |
| `.cursor/rules/` | 稳定约束 | 高（promotion 门禁） | 是 |