---
name: refresh-cursor-kb
description: Cursor 升级、官方配置 schema 变化或知识库到期时，重新核对官方 Rules/Skills/Subagents/Hooks/MCP/Plugins/Plan Mode 并更新来源与 caveats。
paths:
  - ".cursor/knowledge/**"
  - ".cursor/hooks.json"
  - ".cursor/rules/**"
  - ".cursor/skills/**"
  - ".cursor/agents/**"
disable-model-invocation: true
---
# Refresh Cursor Knowledge Base

1. 优先搜索 `cursor.com/docs` 与 Cursor changelog。
2. 当前行为只以官方文档为 `T1_OFFICIAL`。
3. 官方论坛 bug 只写入 `KNOWN_CAVEATS.md`，不得覆盖官方 schema。
4. 学术论文放 `T2_PRIMARY_RESEARCH`，只支持设计判断。
5. 更新 `SOURCES.yaml` 的 `verified_at` 和失效触发器。
6. 对 Hook schema/事件变化更新 hook eval fixture。
7. 运行 `cursor-framework-check`。
