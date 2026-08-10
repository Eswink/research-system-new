---
name: repository-orientation
description: 在 Research OS 中开始跨模块、架构、Domain、Runtime、Tool、Memory、UI 或安全任务前，建立最小且有证据的项目地图。
---

# Repository Orientation

## 目标

在提出方案或修改文件前，先回答“职责在哪里、数据如何流动、哪一层是真相、哪些边界不可改变”。不要把全仓库文档一次性塞入上下文。

## 流程

1. 读取根目录 `AGENTS.md`、`README.md` 和 `CODEX_BOOTSTRAP.md`，确认当前里程碑与不可变产品边界。
2. 依据任务选择最小文档路径：
   - Domain / state：`docs/architecture/DOMAIN_MODEL.md`、相关 ADR、`docs/storage/DATABASE_SCHEMA.md`
   - Protocol / task：`RESEARCH_PROTOCOL.md`、`TASK_HANDOFF.md`、`WORKFLOW_RELIABILITY.md`
   - Runtime / adapter：`AGENT_RUNTIME.md`、`OPENHANDS_ADAPTER.md`、`WORKSPACE_RUNTIME.md`
   - Model：`MODEL_COMPATIBILITY.md`、`LLM_ENDPOINTS.md`、`MODEL_GATEWAY.md`
   - Tool：`TOOL_RUNTIME.md`、`CAPABILITY_SECURITY.md`、`MCP_TOOL_PROVIDERS.md`
   - Memory / evidence：`CONTEXT_ENGINE.md`、ADR-0017、`DATA_LIFECYCLE.md`
   - UI：产品旅程与 Console IA；随后按项目 UI Rule 路由 Impeccable/shadcn
3. 检查当前真实目录和运行入口。规划中的路径不等于已有实现，运行行为优先于文档推断。
4. 形成最小项目地图：所有权模块、输入、输出、Canonical State、外部 port/adapter、策略门禁、失败状态、测试替身。
5. 记录未知项和证据路径。若多个实现路径会改变架构，先进入 Cursor Plan Mode 询问用户。

## 输出契约

```text
任务边界
├─ 所有者模块
├─ 上游输入
├─ 下游输出
├─ Canonical State
├─ Port / Adapter
├─ Policy / Security Gate
├─ 状态与失败语义
├─ 验证入口
└─ 尚未确认事项
```

不输出供应商类型进入 Domain 的方案，不把产品 Memory 与 `.cursor/memory` 混用，也不把聊天记录当作唯一上下文。