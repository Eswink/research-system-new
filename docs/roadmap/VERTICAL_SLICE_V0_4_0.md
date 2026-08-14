# Vertical Slice v0.4.0

> 状态：**已实现**（M7，2026-08-14，commit `782887d`）。
> 本文件保留 Spec 定义；实现证据与逐环节核对见
> [M7_COMPLETION_RECORD.md](M7_COMPLETION_RECORD.md)。

## Scenario

用户：

1. 配置一个中转站；
2. 添加 `model-alpha` 和 `model-beta`；
3. 选择 Standard Team；
4. 输入一个小型公开 ML repo 分析/改进目标；
5. 使用 Guarded Autonomous 和低预算。

## Flow

```text
LLM Endpoint Test
→ Model Probe
→ Team Resolve
→ Protocol Compile
→ Preflight
→ Budget Reserve
→ Manifest Freeze
→ DomainResearch Task
→ Handoff
→ Experiment Task
→ Sandbox execution
→ Result Analysis
→ Reviewer Gate
→ Research Report
→ Audit/Export
```

### 实现状态注记

- 编排链（Protocol Compile → Preflight → Budget → Freeze → Task → Handoff
  → Reviewer Gate）已由 `packages/application/run_orchestration/` + SQLite
  持久化实现，`tests/e2e/` 全链路验证。
- **Sandbox execution**：M7 以进程内/Fake 语义执行（ExecutionBackend 容器
  实现为 Remaining Technical Debt，见 `BACKLOG.md`）；该步骤的容器化属于
  Next Product Capability（Real Experiment Runtime）。
- Reference Scenario 为 `examples/protocols/sort_analysis_v1.yaml`
  （2-phase，`execution` + `review`(QUALITY_GATE)）。

## Failure Injection

必须测试：

- Endpoint 暂时 429；
- duplicate task delivery；
- Tool timeout；
- worker crash/lease expire；
- budget threshold；
- model probe 不支持 tool calling；
- user pause/cancel；
- resume 时 model config drift。

### 实现状态注记

`tests/e2e/` 故障注入矩阵 F-01..F-12 覆盖：F-01 model timeout（retryable，
重试成功）、F-02 model permanent failure（FAILED 不重试）、F-05 workspace
failure（Preflight FAIL）、F-06 lease 过期（重排队）、F-07 重复投递
（幂等去重）、F-08 budget exhausted（Preflight FAIL）；F-09..F-12（policy
denied / cancellation / malformed / evaluator rejection）在
`test_fault_injection_gates.py`。F-03/F-04（ToolProvider failure/timeout）
注入面由 `tests/contracts` 与 M6 PolicyWrappedToolExecutor 测试覆盖
（编排层经 FakeAgentRuntime，不经过 ToolProvider Port，不伪造不可达注入点）。

## DoD

- Preflight 能在运行前拒绝不兼容 Model；
- Agent 按配置使用不同 Model；
- Tools/MCP 不受模型配置变化影响；
- duplicate delivery 无重复副作用；
- Run 可恢复；
- Claim 回溯到 Artifact/Evidence；
- Reviewer read-only；
- final audit 可导出。

### 实现状态注记

全部 DoD 项已核对通过（证据：`tests/e2e/`、`tests/contracts/`、m0 profile
回归；逐项核对见 [M7_COMPLETION_RECORD.md](M7_COMPLETION_RECORD.md) 与
retrospective 计划 DoD 节）。`final audit 可导出` 以 Artifact/Event 流与
内容寻址存储支撑，完整审计/导出 UI 属 Research Console 能力（Next
Product Capability）。