---
id: MEM-20260924-126
title: "差集审计要先分清「可达面」与「声明面」：词表并入声明面会让差集退化成空集"
status: ACTIVE
created_at: 2026-09-24
updated_at: 2026-09-24
scope: repository
confidence: 0.9
review_after: 2027-03-24
source_plans:
  - .cursor/plans/tasks/PLAN-20260924-157-policy-surface-difference-set-audit.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260924-159-policy-surface-difference-set-audit.md
supersedes: []
---

## 做了什么

把 `examples/config/policy.yaml` 的规则面与四个**使用声明面**（`roles.yaml` /
`skills.yaml` / `tool_providers.yaml` / 协议 phase 的 `required_capabilities`）做双向差集，
得 6 + 29 = 35 条，逐条判成三选一终态（该放行 0 / 该拒绝 20 / 该登记 15），
并落一份**可复跑**的机械判据（判据重算差集，文档只是表格载体，两边不一致即红）。

## 为什么这样做

三个坑，任何一个踩了都会得出**看起来合理但是错**的结论：

1. **「谁声明了」不等于「谁会被求值」**。只有出现在某 phase 的 `required_capabilities`
   （或该 phase 所引合约的 `required_capabilities`）的能力，才会变成 `ToolRequirement`
   交给 `PolicyEvaluator` —— 与 `packages/application/protocol_compile/requirements.py` 的
   `phase_capabilities()` **同口径**。roles / skills / tool_providers 上的名字是**供给声明**
   （「谁具备什么」），本身**不构成一次策略求值**。把这两类混成一张表 ⇒ 会把「今天跑不到、
   明天也不会自己跑」的名字报成活缺口。本仓的判词因此分成
   **该放行**（协议可达 ∧ 无放行规则 = 活缺口）/ **该登记**（协议不可达的读类潜在缺口）
   / **该拒绝**（其余）。
2. **词表必须排除，且要写一条有内容的护栏**。`capabilities.yaml` 是「可用能力名」的
   **词表**（全集）；把它并进声明面，差集立刻退化成空集、审计变成空转。
   护栏要有内容 —— 本 cycle 的第一版写成 `not (vocab ∩ diff − vocab)`，**恒真**（等于没断言），
   提交前改成两向：声明面/策略面读到的名字必须**都在**词表内（防止把 `scope` 值、域名
   当能力读进来），且词表里必须存在**仅词表**的名字（词表一旦并入声明面，这些名字消失 ⇒ 红）。
3. **判词要能从机制反推**。每条终态由代码里的机械条件算出（`expected_state()`），
   再与文档逐行比对；文档里写「待定」⇒ 终态闭环断言红。**「不在差集内」必须是一个
   显式取值**（`OUTSIDE_DIFF`），不要复用三选一里的某个词 —— 否则交集能力（两侧都有、
   已被现网规则覆盖）会被打上一个**文档并未定义**的终态，判词与机制看起来就不一致了。

## 怎么做与复现

```bash
# 差集与逐条判定（离线、零出网、只读 YAML）
PYTHONPATH=. uv run --frozen --no-sync python -B scratch/goal014_c3_diffset_probe.py
PYTHONPATH=. uv run --frozen --no-sync python -B scratch/goal014_c3_classify_probe.py
# 判据本身（7 passed，egress guard 计 0 次连接）
uv run --frozen --no-sync python -B -m pytest \
  tests/application/preflight/test_policy_surface_difference_set.py -q
# 4 组成对按压（注入 ⇒ 红，还原 ⇒ 绿；还原后 git diff --stat 为空）
uv run --frozen --no-sync python -B scratch/goal014_c3_press.py
```

按压要**留一组隔离按压**：加一条**词表内**但未声明的能力（`gpu.use`）时，**只有**
双向完备断言该红、词表护栏该绿 —— 这一组证明两条断言各自有内容、不互相顶替。
另加一组「文档多出一条陈旧行」覆盖反向（表有而差集无）。

## 适用边界

- 只对**本仓**的 `examples/config` + `examples/protocols` + `policy.yaml` 成立；
  「可达面 vs 声明面」这个分法可跨项目复用。
- 判据**故意**对声明面敏感：以后给四个声明面加任何未登记的能力都会判红，这是设计意图
  （差集表必须同步更新），不是产品行为回归。
- **该登记 = 15 条读类潜在缺口**不是「已修」：它们是否需要**成类预放行**是**口径问题**，
  需用户拍板（GOAL-014 的授权只覆盖 `evidence.read` 一条）。
- `action:` 形状的规则（`TOOL_PACK_INSTALL_OR_UPDATE` / `MOUNT_DOCKER_SOCKET`）与能力
  **不同命名空间**，本表不收 —— 想审计它们要另起一张表。

## 来源

- `.cursor/plans/tasks/PLAN-20260924-157-policy-surface-difference-set-audit.md`（定案 D-1…D-5）
- `.cursor/plans/rechecks/RECHECK-20260924-159-policy-surface-difference-set-audit.md`
- `docs/architecture/POLICY_SURFACE_AUDIT.md`（35 行差集表 + 口径）
- `tests/application/preflight/test_policy_surface_difference_set.py`（7 条判据）
- `scratch/goal014_c3_diffset_probe.py` / `goal014_c3_classify_probe.py` / `goal014_c3_press.py`
