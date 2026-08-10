# Release Review Rubric — v0.2.2

Release threshold: **9.2 / 10**

任何一轮低于阈值必须标记 `REJECTED → Reworked`，并在下一轮重新验证修改后的完整包。

## Dimensions

| Dimension | Weight |
|---|---:|
| Fixed product boundary | 10% |
| End-to-end implementability | 15% |
| Domain/schema/config consistency | 15% |
| Model relay compatibility | 10% |
| Role/Agent/Tool correctness | 10% |
| Reliability/recovery | 10% |
| Security/privacy/supply chain | 10% |
| Data governance/research integrity | 8% |
| Operations/deployment | 7% |
| Release hygiene/automated validation | 5% |

## Hard Fail Conditions

无论平均分多高，出现以下任一项均不通过：

- 改变 `Base URL + Key + Model IDs` 的主模型接入边界；
- 把 Codex/Claude Code/ACP 设为 MVP 默认 Runtime；
- Role/Agent/Model/Protocol 引用无法解析；
- Tool 或 Workspace 绕过执行时 Policy；
- API Key 可进入 Agent Context、日志或 Domain Event；
- VERIFIED Claim 无 Evidence invariant；
- 活跃配置无法通过 Schema/validator；
- ZIP 解压或 Manifest hash 校验失败。

## Evidence Required

最终通过至少需要：

1. 文档语义审核；
2. YAML/JSON/JSON Schema 解析；
3. 跨文件引用验证；
4. Protocol DAG 验证；
5. Role–Model 能力匹配；
6. Security/Governance 关键约束检查；
7. Manifest SHA-256 校验；
8. 压缩包解压后再次运行 validator。
