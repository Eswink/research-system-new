---
id: RECHECK-20261005-288
slug: goal-030-ec03-scientific-action-depth
title: 复检：GOAL-030 EC-03 —— 真容器实验 + 可否证的指标判据 + 下游消费 + 反证点名（并抓到一处判据射程缺口）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-05
updated_at: 2026-10-05
plan_id: PLAN-20261005-287
reviewer: root-agent
parent_goal: GOAL-20261005-030
verify_paths:
  - >-
    uv run --frozen --no-sync python -B -m pytest
    tests/e2e/test_scientific_action_depth.py -q ⇒ 9 passed
  - >-
    uv run --frozen --no-sync python -B -m pytest tests/architecture/python
    tests/application tests/contracts tests/loaders tests/tooling tests/adapters -q ⇒ 全绿
  - >-
    uv run --frozen --no-sync python -B -m pytest tests/e2e tests/api -q ⇒ 全绿
    （合跑 4142 passed / 90 skipped）
owners:
  - root-agent
---

# RECHECK-20261005-288 — GOAL-030 EC-03

## 结论

**PASS_WITH_WARNINGS**。EC-03 的四项（真科研动作 / 结构化产出 + canonical 落盘 + 读面 /
下游消费 / 反证点名）**实测到场**；**过程中抓到并闭合了自己判据的一处射程缺口**（反证臂改
运行时快照 ⇒ 抓不到出厂目录里的阈值本身），该修正已纳入交付。

## 检查结果

| EC-03 要求 | 判据 | 实测 |
| --- | --- | --- |
| 真科研动作 | `TestTheScientificActionIsReal` | `image_digest` 非空（容器产出）+ 指标是科学测量 |
| 结构化产出（逐字段） | 同上 | 六个字段逐条断言（`pairwise_comparisons` / `indexed_comparisons` / `comparison_reduction_ratio` / `agreement` / `duplicates_found` / `duplicates_expected`） |
| canonical 落盘 + 读面 | `TestTheActionOutputIsStructuredAndReviewable` | artifacts / experiments / evidence 三个读面都取得到 |
| 下游消费 | `TestTheDownstreamPhaseConsumesTheExperiment` | 实验证据 id 出现在 `verdict` 的 `evidence.read` 返回内容里 |
| 反证点名 | `TestARaisedThresholdRejectsAndNamesTheNumber` | run `FAILED`，判词含指标 + 算子 + 阈值 |
| **判据射程**（本轮新增） | `TestTheFalsifiableCriterionIsPinnedInTheCatalog` | 目录里阈值逐字钉住 + 实验实测值越阈值（非空真） |

## 按压（三处，逐字节复原）

1. **抬高阈值**（运行时快照 `1e6`）⇒ 实验 phase 判拒并点名；run `FAILED`。
2. **改小出厂目录阈值**（100 → 1）⇒ **最初未被抓到** ⇒ 补齐 `TestTheFalsifiableCriterionIs
   PinnedInTheCatalog` ⇒ 复压**判红**（`阈值必须是写死的那个数`）；复原 ⇒ 9 passed。
3. **实验脚本实测值**（直接跑脚本取 metrics）⇒ 断言越过阈值 ⇒ 阈值**可达**（非恒假装饰）。

## 复检发现（W-NN，如实登记，未修）

- **`W-1`｜反证臂与出厂目录是**两个受判面**，只做前者会漏掉后者**：本判据初版的反证只改
  `preflight_override`（运行时快照），因此「目录里那个数值本身」未被任何断言看着 ——
  实测把 100 改成 1 时**判据全绿**。补齐后该形态被判红。**这是受判面写窄的又一实例**
  （与 GOAL-029 EC-02 的 `declared ∩ implemented` 同族，承 `MEM-20260922-160`）：
  「机制被触发」与「触发它的那个数值被钉住」是**两件事**。
- **`W-2`｜`metrics` 判据不跨 phase**：接受门在**执行它的那个 phase** 上求值
  （`task_phase_helpers._experiment_facts` 只对带实验事实的 phase 填充）⇒ 下游 `verdict`
  消费的是 **run 级证据投影**，**不读** `metrics` 字段。本 EC **取证了两条路径**，
  但**不**声称「指标跨 phase 传播」——那需要新的传播机制（未做）。
- **`W-3`｜实验的「科学价值」射程有限**：字典序重复检测是**确定性、无随机性**的基准，
  它证明的是「本链路能跑真实验并对其结论下否证判据」，**不**证明系统能做开放科研
  （文献阅读、假设生成、统计推断都不在本 EC 内）。
- **`W-4`｜挂 `requires_docker`**：本判据在非 Linux 容器守护进程下如实 skip，由
  `container-quality` 作业真跑 ⇒ 本地跳过的环境里它**不构成证据**。
- **`W-5`｜`_raise_the_threshold` 只改 `METRIC_THRESHOLD` 那一类**：若有人把该判据**换成
  别的类型**（如 `CUSTOM_EVALUATOR`），反证臂的 `assert any(item.metric == _METRIC …)`
  会红并点名「前提变了」—— 这是**有意的 fail-loud**，但属需要维护的耦合。

## 未覆盖范围（原样保留）

读面未认证 / 多租户未做 / RBAC 未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口 /
D 组审批通道未接通。**不得**据此宣称项目安全；**不得**宣称投递语义为「恰好一次」
（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
