# Research Protocol v0.4.0

## 1. Protocol 是可编译定义

```text
ProtocolDefinition
→ Compiler
→ CompiledRunPlan
→ Preflight
→ RunManifest
```

Protocol 不直接执行 Agent。

## 2. Macro Phases

```text
P0  Intake
P1  Target Profiling
P2  Domain & Literature Discovery
P3  Evidence Modeling
P4  Opportunity Exploration
P5  Question/Hypothesis
P6  Experiment Design
P7  Experiment Execution
P8  Result Analysis & Validation
P9  Claim Assembly
P10 Adversarial Evaluation
P11 Deliverable Assembly
P12 Reproducibility Audit
```

按项目裁剪。

## 3. Phase Definition

```text
inputs
outputs
dependencies
strategy
required_roles
required_capabilities
task_contracts
budget
timeout
retry
gate
stop_conditions
```

## 4. Compile

Compiler 负责：

- DAG/循环规则验证；
- Role/Agent/Model 解析；
- Tool/Capability 解析；
- Workspace/Compute 规划；
- Budget 聚合；
- Gate 注入；
- TaskContract materialization。

## 5. Dry Run

用户可在启动前查看：

```text
预计启动哪些 Role
每个 Agent 使用哪个模型
可调用哪些 Tool
需要什么 Workspace/Compute
预计成本
哪些动作需要审批
```

## 6. Team Resolution / Dynamic Role Activation

`Project.team_template` 是本次 Compile 的唯一 TeamTemplate 选择输入；Protocol 不绑定另一套 TeamTemplate，只声明各 Phase 的 `required_roles` / `required_capabilities` 约束。

```text
Project.team_template
→ resolve + flatten TeamTemplate
→ apply Protocol phase constraints
→ apply Budget / Policy / availability
→ Compiled Team Plan
```

若已选 TeamTemplate 无法满足 Phase 角色下限，Compiler 必须给出机器可读 finding；不得静默改用另一模板。Role folding 只有在 Protocol/Policy 明确定义等价 Skill 与验收条件时才允许。

TeamTemplate 是候选池，Protocol + Budget + Task complexity 决定实际激活 Role，避免 Agent proliferation。

## 7. Negative Result

科学负结果不是系统 FAILED。
