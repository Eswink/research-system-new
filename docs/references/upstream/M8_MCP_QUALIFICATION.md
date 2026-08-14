# M8 MCP Ecosystem Qualification

Phase: M8（Research Capability Plane）
Date: 2026-08-14
Author: root-agent（Plan Mode 调查 + Agent Mode 验证）

## 最终裁决

- **MCP ecosystem qualification = PASS**
- **adapter 形态 = ADOPT `mcp==1.29.0`（v1 stable line，MIT）**

## 事实清单

| 项 | 值 |
| --- | --- |
| protocol | Model Context Protocol（2026-07-28 spec 为 v2 SDK 基线；v1 line 覆盖此前全部修订） |
| PyPI | `mcp==1.29.0`（v1 stable line；v1.x 分支持续接收 critical bug fixes 与 security patches） |
| license | MIT（`LICENSE`，Model Context Protocol a Series of LF Projects, LLC） |
| python 要求 | >=3.10（本项目 3.12 满足） |
| transports | stdio / Streamable HTTP / SSE（官方声明三者齐全） |
| source | https://github.com/modelcontextprotocol/python-sdk（v1.x 分支） |
| 依赖 pin | `mcp>=1.28,<2` 写入 pyproject.toml dependencies + dev；uv.lock 解析为 1.29.0 |

## 关键版本决策：拒绝 mcp 2.0.0

`uv add "mcp==2.0.0"` 解析失败（2026-08-14 实测）：

```text
openhands-sdk==1.42.0 (M5R revision lock 冻结)
→ fastmcp>=3.0.0
→ mcp>=1.24.0,<2.0
```

结论：**openhands-sdk 1.42.0（M5R revision lock）通过 fastmcp 3.x 硬依赖
mcp<2.0**，mcp 2.0.0 不可行。官方 PyPI 明确支持 v1.x 分支并推荐
`mcp>=1.28,<2` 作为未迁移前的正确 pin 方式。M8 adapter 采用 v1 line；
OpenHands 自身 MCP 路径与 Research OS `adapters/mcp/` 互不干扰（分别
消费同一 SDK 的不同侧）。未来 openhands-sdk 升级解除 `<2.0` 约束时，
再评估 mcp 2.x 迁移（需重新 qualification）。

## 最小可执行验证（2026-08-14 实测）

```text
uv run python -c "..."
  import mcp.client.stdio          → ok
  import mcp.client.streamable_http → ok
  from mcp import ClientSession, StdioServerParameters → ok
  from mcp.client.streamable_http import streamablehttp_client → ok
  mcp version = 1.29.0
```

注：v1 顶层不导出 `Client`（该符号是 v2 API），adapter 直接消费
`ClientSession` + transport context manager。

## Adapter 决策

- `adapters/mcp/` 仅 adapter 层消费 mcp SDK；import-linter 契约 + 架构
  断言强制 Domain/Application 不可见（见 `.importlinter.*` 契约测试）。
- stdio：`StdioServerParameters` + `stdio_client`，子进程生命周期由
  adapter 管理（超时/崩溃 → transient/permanent 分类）。
- Streamable HTTP：采用非废弃入口 `streamable_http_client` + 自建
  `httpx.AsyncClient`（connect/read 超时均 = spec.timeout_seconds），
  Bearer 注入来自 `CredentialResolver`（TOOL 域），禁止 token
  passthrough。
- 硬超时（双 transport）：`initialize`/`call_tool`/`list_tools` 全部经
  `wait_for` 强制超时；超时取消触发的 SDK TaskGroup 关闭异常在 transport
  层归一化为 `TimeoutError` → `PortTimeoutError(TOOL_TIMEOUT)`。
- MCP 错误映射到 `packages/application/ports/errors.py` 分类。
- 安全控制继承 `UPSTREAM_COMPONENTS.yaml` mcp 条目：roots 非访问控制、
  scoped authorization、schema version tracking。

### 复审发现：v1 `streamablehttp_client` 超时语义陷阱（2026-08-14 独立复审实测）

v1 废弃入口 `streamablehttp_client(url, timeout=...)` 的 `timeout` 参数
只约束 HTTP connect（内部构造 `httpx.Timeout(timeout, read=sse_read_timeout)`），
读取超时由 `sse_read_timeout` 承担且默认 300 秒；在途请求被 `wait_for`
取消后，context teardown 会等待 slow tool 自然返回（实测 ~10s 后才浮出
异常）。结论：**不得**用该废弃入口承载工具调用超时；必须走非废弃入口
`streamable_http_client(http_client=...)` 并把 `httpx.Timeout(connect=read=
spec.timeout_seconds)` 作为唯一读超时来源。契约测试
`test_slow_tool_over_http_enforces_timeout`（FAULT_SLOW + 2s spec）锁死
该行为。

## 供应链

- revision pin：`mcp==1.29.0`（uv.lock 机器可读；pyproject 约束
  `>=1.28,<2`）。
- license matrix：MIT，与 openhands-sdk 一致，无 COPYLEFT 风险。
- 升级门禁：任何 mcp 版本变更必须重跑 ToolProvider contract suite
  （stdio + Streamable HTTP 双 transport）。