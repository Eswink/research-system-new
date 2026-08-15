# M11 Evaluation Harness Upstream Qualification

日期：2026-08-15。状态：决策完成。

## 1. 决策

**Native 自建 harness；不引入外部 evaluation framework 作为运行时依赖。**

理由：M11 DoD 的每一项要求（可复现运行、before/after regression 被
gate 拦截、CI 确定性接入、mock 评测对象）均可由仓库既有 Domain
（frozen dataclass + canonical digest）与既有 Port（ModelGateway /
ArtifactStore / PolicyEvaluator）满足；无外部框架能填补的缺口。

## 2. 逐项缺口回答

按 `docs/roadmap/MILESTONES.md` M11 上游 qualification 要求，每个候选
依赖必须先回答"它具体解决哪个当前 M11 DoD gap"。

| 候选 | 是否引入 | 结论 |
| --- | --- | --- |
| ragas | 否 | 面向 RAG 检索质量；M11 评测对象是 Model/Prompt/Skill/Tool/Runtime 的工程行为，无 DoD gap 被解决 |
| deepeval | 否 | 引入自有 EvalCase/Score 数据模型，会与 Research OS Domain 形成第二套 evaluation truth 模型（违反 AGENTS.md §6 Canonical State 边界）；其 deterministic checks 语义由自研 scorer 注册表覆盖 |
| lm-eval-harness | 否 | Benchmark 数据集执行器；M12 真实工作流之前无 benchmark 需求（MILESTONES M11 Non-goals），且会引入未 pin 模型资产 |
| pytest-benchmark | 否 | 性能基准与 quality 语义不同（MILESTONES §12 Usage/Cost 与 quality 分离）；usage 维度由 UsageLedgerEntry 关联，latency 归 M15 |
| inspect-ai | 否 | 全栈 eval 框架；M13 之前不需要其 UI/评分模型训练能力；同 deepeval 存在平行数据模型问题 |

## 3. 现有基建复核（不引入依赖的依据）

- 确定性序列化：`packages/domain/serialization.py`（canonical JSON，
  float 拒绝、key 排序、UTF-8）。
- 内容寻址与防篡改：`Digest`（sha256）+ `EvalDataset.digest()` +
  `adapters/contracts/eval_loaders.py` 加载时 freeze 校验。
- 独立评测输入：`ArtifactStore.verify`、`PolicyEvaluator.evaluate`、
  M7 `evaluate_task_gate`（被观测对象包装，见
  `packages/application/evaluation/scorers_runtime.py`）。
- Reviewer 模型链路：`ModelGateway` Port（真实 LLM 仅显式手动运行，
  默认 CI 全 Fake，符合 AGENTS.md §11）。

## 4. 升级门禁

若未来 M15（Eval Operations）或 M12 真实工作流暴露明确缺口（如
benchmark 数据集执行、eval 趋势存储），按 M5R 模式重新启动本
qualification：源码审计 + 最小 spike + revision lock + 结论更新本文件。