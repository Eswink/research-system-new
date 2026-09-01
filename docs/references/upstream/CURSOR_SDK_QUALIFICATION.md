# Cursor SDK Qualification — @cursor/sdk 1.0.30

Qualification date: 2026-08-31 (Windows, Node 22.18.0, pnpm 9.15.1, TypeScript 6.0.3)

## Decision

```text
ADOPT — Cursor 工程 BUILD_TOOLING（parallel-agent-orchestration Skill 专用）
```

不进入 Research OS 产品依赖面；SDK 类型只存在于
`.cursor/skills/parallel-agent-orchestration/scripts/sdk-adapter.ts`。

## Resolution

| 项目 | 值 |
| --- | --- |
| 包 | `@cursor/sdk`（npm，registry.npmjs.org） |
| 版本 | `1.0.30`（exact，写入 `package.json` devDependencies 与 `pnpm-lock.yaml`） |
| tarball sha256 | `b26bf8bd73859b3eac50d209e60953f70470d7a9e5182add9e37dd63398884c1`（2026-08-31 实测下载计算） |
| registry integrity | `sha512-s3gIXfTD3w8ys+KFE81JjjoiJcynkHsf/JCDyXrnbliIac3dkT59hwYZII3XhsT1DlXIfqg+YzSMru6w1CkZow==` |
| 平台可选依赖 | `@cursor/sdk-{darwin,linux,windows}-{x64,arm64}@1.0.30`；本机实测 `@cursor/sdk-win32-x64@1.0.30` 从 SDK 主包真实路径可解析 |
| engines | `node >=22.13`（仓库 engines `>=22.18.0 <23` 满足） |
| 传递依赖 | `@bufbuild/protobuf`、`@connectrpc/*`、`@statsig/js-client`、`zod` 等（完整树见 lockfile） |

## License

- `SEE LICENSE IN LICENSE.md`；包内 LICENSE.md 原文：
  `© Anysphere Inc. All rights reserved. Use is subject to Cursor's Terms of Service.`
- 非 OSI 开源许可，登记为 `LicenseRef-Anysphere-Proprietary`，
  证据为 tarball 内 LICENSE.md 与 https://cursor.com/terms-of-service 。
- 使用面：仅本仓库工程自动化（开发者本机运行），不随产品分发。

## Verified in this session（确定性证据）

1. `npm view` 元数据（版本/license/dist/engines/optionalDependencies）。
2. tarball 下载 + SHA-256 计算 + LICENSE.md 提取。
3. `pnpm add -D -E -w @cursor/sdk@1.0.30` → `pnpm-lock.yaml` 锁定全部平台包；
   `pnpm install --frozen-lockfile` 复现安装。
4. 类型面核对（`dist/esm/*.d.ts`）：`Agent.create/resume/prompt`、`SDKAgent.send/close/
   [Symbol.asyncDispose]`、`Run.wait/cancel`、`RunResult.status/model/usage`、
   `Cursor.models.list(): SDKModel[]`、`AgentOptions.tools/disallowedTools`
   （`task` 门控子代理、省略 `mcp` 禁用 MCP 家族）、
   `LocalAgentOptions.settingSources/sandboxOptions`、
   `CursorAgentError.isRetryable/code/requestId`、错误类
   Authentication/RateLimit/Configuration/Network/AgentBusy。
5. 编排器实现 + `node --experimental-strip-types` 确定性单测 15/15、
   `tsc --project` strict 通过、ESLint strictTypeChecked 通过（AgentFactory fake，无网络）。

## NOT VERIFIED（需真实 `CURSOR_API_KEY` 的手工 smoke；不进入 CI）

- `Cursor.models.list()` 真实目录内容与目标模型（如 `gpt-5.6-sol`）的可用性
  （账号/套餐/团队策略/Legacy Max Mode 可能导致不可用）。
- 多个 SDK Run 的时间区间真实重叠、独立 `agentId/runId/requestId`、
  解析模型与请求模型一致。
- sandbox 负测：写文件/破坏性 Shell/越界路径在 `sandboxOptions.enabled: true` 下被阻断。
- headless 模式的审批/权限行为与费用观测（`getUsage`）。

上述任一项未验证前，相关能力按 fail-closed 设计运行（模型目录校验失败即拒绝；
sandbox 启动抛 `ConfigurationError` 时任务按 startup_failed 处理），不得宣称 PASS。

## Risks / Caveats

- SDK 为 public beta：API 形态可能变更；升级必须走 `UPSTREAM_COMPONENTS.yaml`
  升级门禁（lock refresh、license review、adapter contract、orchestration tests、
  `pnpm run check` + framework profile）。
- 依赖 `@statsig/js-client`（分析/遥测面）：编排进程的网络出站行为未在本次审计，
  敏感环境使用前需单独评估；本仓库默认不向 SDK 传入任何 secret（仅 `CURSOR_API_KEY`）。
- 平台二进制缺失时 `sandboxOptions` 抛 `ConfigurationError`（fail-closed）。
- 不支持并发修改同一工作树；写路径需要 worktree/Cloud 隔离，属后续独立任务。

## 与原生 Subagent 的边界

- 本 SDK 编排创建的是**独立顶层 Agent 会话**，不是 Cursor 会话内 Task 子代理；
  不产生 `subagentStart/subagentStop` Hook 事件，`subagent_guard` 的三路计数不适用。
- `tools` 排除 `task`，从工具面禁止嵌套委派，与 Rule 10 no-nesting 一致。
- 原生 Task 并行路径保留且仍是轻量首选；本编排器用于需要确定性并发保证的场景。
