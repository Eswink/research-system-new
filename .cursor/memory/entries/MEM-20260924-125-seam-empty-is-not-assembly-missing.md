---
id: MEM-20260924-125
title: "「缝为空」不等于「装配缺失」：补执行体与换控制面的分界线，以及验收门输入缺口的判读"
status: ACTIVE
created_at: 2026-09-24
updated_at: 2026-09-24
scope: repository
confidence: 0.9
review_after: 2027-03-24
source_plans:
  - .cursor/plans/tasks/PLAN-20260924-156-real-control-plane-end-to-end.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260924-158-real-control-plane-end-to-end.md
supersedes: []
---

## 做了什么

要让一条**检索协议**在**产品控制面**（`preflight_override = None`）上跑起来，本仓今天
需要装配方补两段缝：`ApiDeps.tool_providers`（provider **实例**）与
`OrchestrationDependencies.capabilities`（运行链能力步）。补上之后实测：

- 检索类协议在真实控制面上由 `WARN`（`TOOL_HEALTH_UNPROVEN`）+ **拒冻** 变成
  **`PASS` + 可冻结**；经既有 API 跑到 **`SUCCEEDED`**，证据面 2 条 `RETRIEVED`（真 PMID）。
- 只补**执行体**、**不**补判词，控制面就是**产品自己的**：`NativePolicyEvaluator` +
  产品 `policy.yaml`（版本 0.4.0）+ **真探测**出来的 `provider_health`。

同一轮还测出一条**结构性阻断**：出厂目录里两份声明了 `experiment` 的合约
（`experiment_execution` / `m12_experiment_execution`）都带 `TEST_PASSES` +
`POLICY_COMPLIANT`，而产品路径的 `EvaluationInputs` **没有** `tests` / `policy_decision`
两个维度 ⇒ 实验**跑成功、制品齐备**时仍判拒 ⇒ 带真实实验的 run 到不了 `SUCCEEDED`。

## 为什么这样做

**「缝为空」有三种完全不同的含义，混起来会得出错误的结论**：

1. **产品不接**（组合根没写）——如 `tool_providers`（注释写死「生产未注册时空 dict」）、
   `capabilities` / `experiment_task`（缺省 `None`）。这是**能力缺口**，装配方补**执行体**
   即可，属于「装配」；
2. **判据不想让你接**（本模块明确禁止注入的东西）——`provider_health` / `endpoint_health` /
   `policy_evaluator` / 任何 `PreflightContext` 字段。注入它们＝**换一套控制面**，
   与 `preflight_override` 同类；
3. **门禁还不认识这个维度**——`EvaluationInputs` 缺 `tests` / `policy_decision`。
   这一条**不是**装配问题：它是验收门的**输入面**，改它等于改产品门禁。

分界线（本仓可直接复用的判据）：**补的是「谁去干」，还是「干成了没有」**。
provider 实例 = 谁去干（可补）；健康状态 / 策略判定 / 验收结论 = 干成了没有（不可补）。

## 怎么做与复现

```bash
# 控制面矩阵（注册真适配器 vs 不注册），离线可得、只花两次廉价探测
set -a; . ./.env; set +a
PYTHONPATH=. uv run --frozen --no-sync python -B scratch/goal014_c2_probe.py
# 验收门输入缺口（纯离线、零出网）
PYTHONPATH=. uv run --frozen --no-sync python -B scratch/goal014_c2_acceptance_probe.py
# 真跑一次（1 会话 + 2 次检索，最小必要；跑完不留开关）
RESEARCHOS_OTEL_ENABLED=0 RESEARCHOS_AGENT_RUNTIME=openhands \
  uv run --frozen --no-sync python -B -m pytest \
  tests/e2e/test_real_control_plane_retrieval_live.py -q -rs
```

要点：

1. **按压要选在承重的那条规则上**：`evidence.read` 的 allow 对**检索协议不承重**
   （它只用 `artifact.read` + `literature.*`）⇒ 撤它压不动检索协议。要按**协议真正用到**
   的那条 allow 去撤（本次两条按压各撤一条，形态都是 `FAILED` + `manifest_digest: null`
   + 零 task / 零实验 / 零证据）。
2. **按压止于 preflight 时是免费的**：撤 allow ⇒ 判红在冻结前 ⇒ **零真实 LLM 调用**，
   是最划算的反证形态。
3. **Windows 上别把结论放在 `TemporaryDirectory` 之外打印**：SQLite 连接可能仍占着文件，
   退出清理抛 `PermissionError` 会把结论吞掉（探针要在 `with` 内打印或写文件）。

## 适用边界

- 只对**本仓**的 run 编排 / 预检 / 验收门成立；「补执行体不补判词」这条分界线可跨项目复用。
- 第 3 类（门禁输入面）**不是**本仓测试能自行决定的：它是产品验收门的语义，
  改动属产品面 + 需拍板（本仓已成文登记在 GOAL-011 的下一轮输入 ①②③）。
- 「注册真适配器 ⇒ `PASS`」只在**该适配器真能探测成功**时成立；网络不可达时健康会
  如实回落 `UNKNOWN`（那时仍会 `WARN` + 拒冻——**不要**把它读成配置错误）。
- 补 `tool_providers` **会增加真实出网**（每次 preflight 都会探测 provider）——
  默认门（离线）里不要这么装配。

## 来源

- `.cursor/plans/tasks/PLAN-20260924-156-real-control-plane-end-to-end.md`（定案 D-2 与阻断 M-1/M-2/M-3）
- `.cursor/plans/rechecks/RECHECK-20260924-158-real-control-plane-end-to-end.md`（判据性质披露）
- `.cursor/plans/goals/GOAL-20260924-014-policy-surface-consistency.md`（`F-10` / `F-11` 的登记处）
- `scratch/goal014_c2_probe.py` / `scratch/goal014_c2_acceptance_probe.py` /
  `scratch/goal014_c2_press_probe.py`（三份可复跑探针）
