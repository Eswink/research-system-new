# Product Definition v0.2.2

## 1. 产品是什么

Research OS 是：

```text
Research Agent Operating Environment
+
Autonomous R&D Control Plane
+
Evidence-native Audit System
```

用户提供：

```text
Research Objective
Target Profile（可选）
Code/Data/Sources
LLM Relay URL + Key + Model IDs
Tool Integrations
Budget
Autonomy Policy
```

系统完成：

```text
Compile
→ Preflight
→ Role/Agent Allocation
→ Task Execution
→ Tool/Workspace Operations
→ Evidence/Experiment
→ Independent Evaluation
→ Deliverable
→ Reproducibility/Audit
```

## 2. 产品不是

- 纯聊天机器人；
- 固定 26 Agent 群聊；
- 论文文本生成器；
- IDE 克隆；
- 无权限边界的 Shell Agent；
- 把 LLM 评分当科学真相的系统。

## 3. 核心体验

### 最简用户

只需要：

```text
1. 填 LLM Relay URL + Key
2. 添加 Model IDs
3. 选择 Team Template
4. 输入研究目标
5. 选择预算和自治等级
6. 启动
```

### 高级用户

可以：

- 每个 Agent 单独选模型；
- 创建同 Role 多实例；
- 自定义 Role/Skill；
- 自定义 Protocol；
- 接入 MCP/REST Tools；
- 设置网络、Workspace、Compute；
- 配置质量门禁；
- Fork/重跑/替换模型。

## 4. 端到端阶段

```text
Configuration
→ Project Draft
→ Protocol Compile
→ Preflight
→ Run Ready
→ Execution
→ Review
→ Deliverable
→ Audit
→ Archive/Export
```

## 5. 成功标准

一次 Run 成功不是“生成了文档”，而是：

- 目标和计划可解释；
- Agent/模型/工具解析可审计；
- Tool 调用受控；
- Artifact 可验证；
- Claim 有 Evidence；
- 实验可追溯；
- 失败可恢复；
- 成本可核算；
- 输出能通过质量门禁。
