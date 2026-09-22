# Capability & Security v0.4.0

## 1. Capability 示例

```text
workspace.read
workspace.write.notes
workspace.write.code
workspace.delete
network.academic
network.public
literature.search
evidence.write
code.execute
package.install
gpu.use
git.commit
external.publish
```

## 2. Effective Policy

```text
Organization/Project Policy
∩ Autonomy Level
∩ Phase Policy
∩ Role defaults
∩ Agent overrides
∩ WorkspaceLease
∩ Tool requirements
=
Decision
```

## 3. Policy Decision

```text
ALLOW
DENY
REQUIRE_APPROVAL
ALLOW_WITH_CONSTRAINTS
```

约束包括：

```text
domain allowlist
max bytes
max cost
readonly path
command pattern
time window
```

## 4. Credential Domains

严格区分：

- LLM Endpoint Credential
- Tool Provider Credential
- Workspace/Compute Credential
- User OAuth grant

Agent 不直接读取 Secret。

## 5. External Content

来源标记：

```text
TRUSTED_INTERNAL
VERIFIED_SOURCE
UNTRUSTED_EXTERNAL
GENERATED
USER_PROVIDED
RETRIEVED
```

`RETRIEVED` = **系统自己取回来**的来源（执行声明的能力时从外部取得，如检索类 provider
打到它声明的 `network_domains`）。它与 `USER_PROVIDED`（用户交付的输入）、`GENERATED`
（会话/实验自产，含模型自述）**互不混称**：来源性质在准入时盖章
（`ToolEvidenceInput.trust_label`），验收门的 `EVIDENCE_COVERAGE` 可据此要求
「覆盖里至少有一条是系统取得」（GOAL-011 EC-02）。

Web/PDF/MCP 内容不能修改系统指令或权限。

## 6. MCP

- Roots/目录提示不是 access control；
- Remote server 使用独立授权/credential scope；
- Tool schema 和 server capability 要版本化；
- Server 返回的 state handle 不是授权凭据；
- 不允许 token passthrough/confused-deputy。

## 7. Content/Telemetry Privacy

Prompt、输出、Tool 参数默认不进入 telemetry。

## 8. Human Gate

高风险动作默认需要审批：

- 新 ToolPack；
- 新网络域；
- Package install；
- 大额预算；
- destructive operation；
- external publish；
- 运行中更换模型/Tool Set。
