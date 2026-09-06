# UD — Research OS Usage-driven Improvement

本模板用于 Personal Production Baseline 完成后的真实使用驱动改进。每次只处理
一次真实 Research OS 使用中观察到的一个问题或机会，不建立新的固定 Milestone
主线，也不创建独立于现有工程计划体系的编号或状态体系。

## 使用条件

- 输入必须来自一次真实 Research OS 使用，而不是对未来场景的猜测。
- 首先进入 Plan Mode，确认问题、证据、范围和验收条件后再实施。
- 没有具体真实问题时保持等待，不实例化本模板，不为编号完整性创建工作。
- 每个实例只交付一个 scoped improvement；独立问题分别立项。

## 事实来源优先级

按以下顺序收集并交叉核对事实：

```text
real Run
→ Artifact / Event / Telemetry
→ Evaluation
→ Usage
→ reproduction
```

优先引用链条中更靠前且可取得的证据。后续证据用于定位、解释和复现，不能用
推测、聊天摘要或旧 PASS 替代当前真实使用事实。记录适用的 Run ID、时间、环境、
配置或运行指纹、Artifact digest、Event/Telemetry 定位信息、Evaluation 版本或摘要、
Usage 记录和复现结果；某项不可取得时明确写出原因与证据缺口。

Prompt、模型输入输出、Tool 参数、凭据及其他敏感内容只记录 digest、大小、类型和
脱敏元数据，遵守现有观测与保留策略。

## 问题分类

选择一个主分类；确有跨界影响时可记录次分类，但不能据此扩大实施范围。

- [ ] Research Capability
- [ ] Tool
- [ ] Skill
- [ ] Protocol
- [ ] Evaluation
- [ ] Runtime
- [ ] Reliability
- [ ] Performance
- [ ] Cost
- [ ] UX

## 基本信息

- 工作项标题：
- 观察日期与使用场景：
- 主分类：
- 次分类（可选）：
- 观察者或证据所有者：
- 关联工程计划状态（如适用）：

## 必填内容

### reproduction

- 前置条件和最小环境：
- 相关版本、revision、配置或运行指纹：
- 最小复现步骤：
- 实际结果：
- 复现频率与稳定性：
- 复现证据位置：

无法复现时不得把原因写成既定事实；记录已观察现象、尝试过的复现范围和仍缺少的
证据，并保持任务为调查或阻塞状态。

### expected outcome

- 用户或研究目标：
- 可观察的预期行为：
- 明确的成功标准：
- 明确的失败或降级语义：

### current evidence

- real Run：
- Artifact / Event / Telemetry：
- Evaluation：
- Usage：
- reproduction：
- 已排除的替代解释：
- 尚未确认的证据缺口：

每条结论应能回到稳定证据位置。只保留证据真正支持的强度，不从单次运行外推未验证
的平台能力。

### affected Contract

- 受影响的 Contract、Schema、API、状态机、Port、Policy 或用户流程：
- 当前契约和运行事实：
- 预期变化：
- 兼容性或迁移影响：
- 不受影响的相邻边界：

如判断没有契约变化，说明依据。若修改 `schemas/`、`examples/` 或受引用文档，必须
同步核对 ID、枚举、DAG、Role/Agent/Model/Tool 引用和文档索引。

### regression target

- 能在修改前暴露问题的目标：
- 修改后必须通过的断言：
- 回归命令或运行步骤：
- 受影响 Evaluation 及 before/after 判定：
- 真实 Research re-run 场景和证据要求：

## 最小范围

### 修改白名单

- 必须修改的文件或模块：
- 必须新增的测试或 Evaluation：
- 必须更新的文档：

### 非目标

- 与本问题无直接因果关系的重构：
- 未被当前证据触发的基础设施：
- 只为未来可能需求准备的扩展：

### 边界检查

- 所有者模块与依赖方向是否保持不变：
- Canonical State 是否保持为 PostgreSQL Domain Entity：
- 产品 Memory、Task、Handoff、Preflight、Manifest 是否与 Cursor 工程记录隔离：
- 安全、凭据、供应链和默认 deny 是否保持：
- 是否触及 Accepted ADR、核心安全策略或 Canonical State 边界：

最后一项如为“是”，必须停止超出原授权的实施，回到 Plan Mode 获取明确授权。

## 实施与验证

只实施能关闭上述 reproduction 与 regression target 的最小变化。不得为了一个真实
问题顺手重新启动大规模基础设施路线，也不得修改 validator 或伪造 Manifest 来让
门禁通过。

完成前必须满足：

- [ ] regression 已通过，并记录命令、输出摘要和证据位置。
- [ ] affected Evaluation 已执行 before/after 对照；不适用时已写明可核对的原因。
- [ ] real Research re-run 已完成，并留下新的 Run 与结果证据；旧 PASS、Fake 或 Mock
      不能替代本项。
- [ ] documentation update 已完成，当前行为、限制、恢复方法和迁移影响已同步。

缺少必要真实环境、凭据或重跑条件时，将任务标记为 BLOCKED 或保持 IN_PROGRESS，
不得宣称完成。长期、多阶段或跨会话工作复用现有工程 Plan 与 Recheck 流程；工程
记录不得写入产品 MemoryRecord、ResearchTask、数据库、事件流或 Runtime Context。

## 正式路线重新激活检查

以下条件用于发起独立的重新立项评估，不等于自动开工、部分完成或已支持；仍需新
ADR、Plan Mode 批准和原有依赖门槛。

- **M18**：出现真实第二用户、team、organization、shared service、RBAC 或 tenant
  isolation 需求之一。
- **M19**：出现真实 Enterprise deployment、formal SLO、compliance、incident
  governance 或 enterprise secrets 需求之一。
- **HPC Track**：已经获得可实际执行和验证的 multi-GPU、multi-node、Slurm 或 HPC
  环境。只有需求或模拟环境时可以记录机会，但不得启动支持声明；没有真实环境，
  不得宣布支持。

如均未满足，继续使用本模板处理 scoped improvement，固定 Milestone 主线保持暂停。

## 完成记录

- 最终范围与实际改动：
- regression 结果：
- affected Evaluation 结果或不适用依据：
- real Research re-run 结果：
- documentation update：
- Domain/API/schema 影响：
- 安全/凭据影响：
- 兼容性/迁移风险：
- 上游版本影响：
- 遗留风险与下一项真实使用问题：
