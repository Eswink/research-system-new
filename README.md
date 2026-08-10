# Research OS Bootstrap v0.2.2

Research OS 是一个面向长时程 Autonomous R&D 的软件系统。

它不是“自动写论文工具”，也不是 Codex / Claude Code 的外壳。论文、技术报告、代码、实验包、Benchmark 结果只是 Deliverable。

## v0.2.2 的主题

v0.2.1 已冻结：

- 用户通过 `Base URL + API Key + Model ID` 接入 OpenAI-compatible LLM 中转站；
- 每个 Agent 可以独立配置模型；
- Role 与 Agent 分离；
- OpenHands Software Agent SDK 是通用 Agent Runtime 基底；
- Tools / MCP / Workspace / Sandbox / Evidence / Evaluation 保持独立。

v0.2.2 在不改变上述边界的前提下，补齐：

```text
端到端用户旅程
Protocol 编译与 Preflight
Task / Handoff 契约
Model 兼容性与同名漂移检测
Team Template 与动态 Role 激活
预算预留与 Usage Ledger
工作流幂等、租约、恢复与补偿
Memory 写入门禁
MCP / Plugin 供应链治理
安全威胁模型
Artifact 生命周期
可观测性与隐私
部署分级
任务级 Agent 身份与访问控制
中转站数据边界与数据治理
研究诚信规则
备份恢复、SLO 与容量准入
评测与发布门禁
```

## 用户的模型接入保持简单

```text
LLMEndpoint
├ Base URL: https://xxx.com/api/v1
├ API Key: ********
└ Models
   ├ model-alpha
   ├ model-beta
   └ model-gamma
```

Research OS 不要求用户分别配置 OpenAI、Anthropic、DeepSeek 或其他厂商。

## Agent 配置

```text
DomainResearcher       → model-alpha
LiteratureScout A      → model-beta
LiteratureScout B      → model-gamma
ExperimentEngineer     → model-beta
ScientificReviewer A   → model-gamma
ScientificReviewer B   → model-alpha
ResearchWriter         → model-alpha
```

同一 Role 可以有多个 Agent 实例并绑定不同模型。

## 核心架构

```text
                         Research Console
                                |
                         Control Plane API
                                |
                     Protocol Compiler / Preflight
                                |
                         WorkflowEngine Port
                                |
                      Compiled Phase / Task Plan
                                |
                         AgentRuntime Port
                                |
                    OpenHandsRuntimeAdapter
                                |
        +-----------------------+-----------------------+
        |                       |                       |
   Model Gateway          Tool Runtime             Workspace
        |                       |                       |
 LLMEndpoint              Native/MCP/REST       Local/Docker/Remote
        |
 User Relay + Model IDs

=================== Research OS Owned Kernel ===================

Domain / Role / Protocol / Task Contract / RunManifest
Policy / Budget / Memory / Evidence / Experiment Provenance
Evaluation / Artifact Lifecycle / Events / Audit / UI
```

## 开发入口

依次阅读：

1. `AGENTS.md`
2. `CODEX_BOOTSTRAP.md`
3. `docs/INDEX.md`
4. `docs/PRODUCT.md`
5. `docs/product/END_TO_END_USER_JOURNEY.md`
6. `docs/architecture/SYSTEM_ARCHITECTURE.md`
7. `docs/architecture/DOMAIN_MODEL.md`
8. `docs/architecture/TASK_HANDOFF.md`
9. `docs/architecture/MODEL_COMPATIBILITY.md`
10. `docs/security/THREAT_MODEL.md`
11. `docs/references/OPEN_SOURCE_REUSE_AUDIT.md`
12. `BACKLOG.md`

## 发布质量

本包在发布前至少经过三轮独立门禁审核，低于阈值的轮次会被打回重做。审核记录位于 `docs/reviews/`。
