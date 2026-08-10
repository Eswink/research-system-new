# Review Round 2 — Implementability & Machine-readable Contracts

Threshold: **9.2 / 10**
Score: **8.9 / 10**
Result: **REJECTED → Reworked**

## Rubric

| Dimension | Score |
|---|---:|
| End-to-end flow | 9.4 |
| Machine-readable Role model | 7.8 |
| Task/output contracts | 8.1 |
| Backend/deployment references | 8.3 |
| Model eligibility examples | 8.8 |
| Security/reliability | 9.5 |

## Findings

1. 26 个 Role fixture 只有类型和默认模型，缺少 requested capabilities、模型硬能力和 Workspace policy。
2. TaskContract 引用了两个 output schema，但文件未落盘。
3. Deployment profiles 引用了未定义的 Workflow/Workspace backend。
4. Reviewer 示例模型未声明 Tool Calling，却被分配给需要检索工具的 Reviewer。
5. TeamTemplate `extends` 的 merge 语义未冻结。

## Remediation

- 扩展全部 26 个 Role fixture。
- 扩展 Capability Catalog。
- 新增 DomainDiscovery/Experiment/Handoff/Preflight/ToolPack schemas。
- 完整定义 Workflow/Workspace backend registry。
- 修正 Reviewer model capability。
- 冻结 TeamTemplate inheritance semantics。

Round 3 required.
