---
name: parallel-agent-orchestration
description: 用 TypeScript Cursor SDK 编排器确定性并发运行多个独立只读 Agent 会话（每波最多 3 个），不依赖父模型在同一条消息中批量发出 Task 调用。
disable-model-invocation: true
paths: ".cursor/skills/parallel-agent-orchestration/scripts/**"
---
# Parallel Agent Orchestration

本 Skill 是显式工程工具：只能由用户或根 Agent 明确要求"用 SDK 并发编排"时调用。
它解决的问题是模型行为层面的：Cursor 原生并行子代理要求父 Agent 在一条消息中
同时发出多个 Task 工具调用，不同模型的遵循程度是 best-effort（见
`.cursor/knowledge/SUBAGENT_DESIGN.md`）。本编排器把并发决策从父模型转移到
Node 进程：每个任务都是独立顶层 Agent 会话，由 `Promise.allSettled` 真实并发
启动，与 GPT/Claude/Composer 等具体模型无关。

## 与原生 Task 子代理的关系

- 原生 Task 路径不变：仍是轻量首选，遵循 Rule 10 的三路上限与 no-nesting。
- 本编排器不产生 Cursor 会话内的子代理树，`subagentStart` Hook 计数不适用；
  它自带同等的"每波最多 3 个"硬上限（`runner.ts` + `waves.ts`）。
- 需要真正同时运行的独立上下文（如并行复审、并行调查）且原生批量调用未生效时使用。

## 运行前提

1. Node >= 22.13（仓库 engines 为 `>=22.18.0 <23`）。
2. `@cursor/sdk` 已由 `pnpm-lock.yaml` 精确锁定（当前 1.0.30）。
3. 环境变量 `CURSOR_API_KEY` 由调用方提供；本 CLI 不接受命令行 key，不读 `.env`。
4. 模型 id 必须能通过 `Cursor.models.list()` 目录校验（fail closed）。

## 用法

```powershell
# tasks 文件：JSON 数组，每项 {"id","prompt","mutation":"read_only"}
$env:CURSOR_API_KEY = "<在会话外注入>"
pnpm run agents:parallel -- --model-id <catalog-verified-id> --tasks <safe-json-file> --cwd <abs-path>
```

行为约束（均为代码强制，非提示词约束）：

- 任务必须 `mutation: "read_only"`；重复 id、空 prompt、越界 cwd 直接拒绝。
- Agent 以最小只读工具集创建（`tools: read/grep/glob/ls`，无 shell/edit/mcp/task），
  并启用 SDK sandbox；prompt 只是辅助，不是安全边界。
- 每 wave 最多 3 个；超过 3 个任务按波顺序执行，无累计任务上限。
- Ctrl+C：abort 信号阻止后续 wave，活动 Run 逐个 cancel，Agent 句柄释放。
- stdout 只输出脱敏摘要（task/agent/run/request id、请求/解析模型、状态、
  耗时、结果 sha256 与大小、SDK 错误码）；不输出 prompt、结果正文或凭据。
- 退出码：0 全部 finished；1 存在 startup/preflight 失败；2 存在运行失败或取消。

## 验证与边界

- 确定性单测：`pnpm run agents:parallel:test`（AgentFactory fake，无网络无凭据）。
- 手工 smoke 需要真实 `CURSOR_API_KEY`，结果记录到 qualification/recheck，
  不进入默认 CI；模型不可用时如实记 `NOT VERIFIED`，不伪造 PASS。
- 不支持并发修改同一工作树；需要写路径时另立 worktree/Cloud 隔离方案。
- SDK 为 beta 上游：升级须走 `UPSTREAM_COMPONENTS.yaml` 升级门禁与回归。
