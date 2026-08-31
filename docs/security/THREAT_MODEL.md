# Threat Model v0.4.0

## 1. 保护资产

- LLM/Tool/Compute credentials；
- 用户代码、数据和未公开研究；
- Workspace/Artifact；
- Domain canonical state；
- Evidence/Claim integrity；
- 预算和计算资源；
- 审计轨迹。

## 2. 主要信任边界

```text
Browser/User
Control Plane
Agent Runtime
LLM Relay
MCP/Tool Providers
Sandbox/Compute
Artifact Store
External Web/PDF/Data
```

## 3. 威胁与控制

### Prompt Injection

来源：Web/PDF/MCP Tool output。

控制：trust label、上下文隔离、不可修改系统策略、敏感 Tool 二次检查。

### Tool Poisoning / Schema Change

控制：ToolPack digest、版本 pin、schema diff、安装审批、canary。

### Confused Deputy / Token Passthrough

控制：CredentialBinding、audience/scope、禁止把 LLM key 给 Tool、禁止通用 bearer token 透传。

### Rogue / Stolen Worker（M16）

来源：被入侵的 worker 主机、被盗 session token、伪造注册。

控制（ADR-0027）：enrollment secret 常量时间比较 + session token 仅存
sha256（generation 单调，重注册作废旧 token）；worker_id 与 token 身份一致性
校验；`fence` 单调拒绝迟到结果；worker 不持有 PostgreSQL/ArtifactStore
凭据；非 loopback 绑定无 TLS 拒绝启动；作业级最小凭据 scope；秘密枚举面为零。

### Partition / Split-brain（M16）

来源：网络分区、重复投递、scheduler 重启。

控制：分区仅为 claim 过滤（所有权权威是 leases 行，结构上无双重所有权）；
服务端时间判定 LOST；`recover_expired_leases` 单一恢复权威；迟到结果被
fence 拒绝；重连不恢复旧权威。

### SSRF / Data Exfiltration

控制：egress proxy、domain allowlist、DNS/IP 检查、下载大小上限、private-network deny。

### Workspace Escape

控制：sandbox、readonly mount、无 Docker socket、无 privileged、path guard、resource limit。

### Supply Chain

控制：pin commit/digest、license/manifest、dependency scan、quarantine、可撤销安装。

### Resource Exhaustion

控制：budget/quota、timeout、max turns、process/memory/GPU limits、circuit breaker。

### Model Relay Drift / Malicious Relay

控制：TLS、endpoint health、runtime fingerprint、敏感项目提示、数据分类策略、可选 self-hosted relay。

### Evidence Tampering

控制：content digest、append-only provenance、artifact verification、separation of duties。

## 4. Data Classification

```text
PUBLIC
INTERNAL
CONFIDENTIAL
RESTRICTED
```

Project 分类影响：

- 是否允许外部 LLM Relay；
- 是否允许公网 Tool；
- telemetry 内容；
- artifact retention/export。

## 5. Security Invariants

- Agent 永远看不到明文 Secret；
- MCP Roots 不是安全边界；
- Reviewer 不可修改实验结果；
- Writer 不可创建 Verified Claim；
- 高风险 Tool 不能仅依赖模型自觉；
- 所有外部内容默认不可信。
