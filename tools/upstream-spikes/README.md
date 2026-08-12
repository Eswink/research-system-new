# Upstream Spikes — OpenHands Software Agent SDK v1.42.0

M5R 阶段的最小可执行实验。所有 spike 使用 mock/test credential，不依赖真实
用户 Secret，不进行高风险外部操作。

## 环境

- Python: `d:\upstream\.venv-sdk`（3.12.13，与仓库 uv.lock 隔离）
- SDK: `d:\upstream\openhands-software-agent-sdk`（v1.42.0, 391fbb8d）
- 运行方式（PowerShell）：
  ```powershell
  d:\upstream\.venv-sdk\Scripts\python.exe tools\upstream-spikes\S1_import_fingerprint.py
  ```

## Spike 清单

| ID | 脚本 | 验证点 | 结论对 Adapter 决策的意义 |
| --- | --- | --- | --- |
| S1 | S1_import_fingerprint.py | import SDK、版本指纹、核心符号存在性 | 环境可行性；版本锁定 |
| S2 | S2_llm_construction.py | LLM 构造（model/base_url/api_key）、自定义 base_url 透传、mock 请求验证 | ModelGateway → OpenHands LLM 映射 |
| S3 | S3_agent_conversation_run.py | Agent + Conversation 创建与 run（mock LLM）、自定义安全工具注册、事件流观察 | AgentRuntime create/run/stream_events |
| S4 | S4_cancel_pause_error.py | pause/interrupt 语义、错误路径（ConversationRunError） | cancellation/error 映射 |
| S5 | S5_local_workspace.py | LocalWorkspace 生命周期（create/write/command/close） | WorkspaceBackend 映射 |
| S6 | S6_persistence_resume.py | persistence 往返（conversation_id + persistence_dir）、tool set 一致性 | resume/持久化边界 |

## 执行记录

每次执行记录命令与结果，追加到 `results/` 目录（见各脚本执行输出）。
Docker workspace spike 为门控步骤（需用户确认后另行执行），不在默认清单内。