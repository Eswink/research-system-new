---
id: MEM-20260925-135
title: "「我们不做 X」类决定的判据必须带三条：结构否定 + 可按压的检测器 + 可核对的清单"
status: ACTIVE
created_at: 2026-09-25
updated_at: 2026-09-25
scope: repository
confidence: 0.9
review_after: 2027-03-25
source_plans:
  - .cursor/plans/tasks/PLAN-20260925-170-read-grant-stays-per-item.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260925-171-read-grant-stays-per-item.md
supersedes: []
tags: [judges, policy-surface, negative-criterion, goal-016, d-02]
---

## 做了什么

GOAL-016 的 **EC-02（D-02(b)）**要把「读类能力**维持逐条放行**、**不**成类预放行」这条
**否定式决定**钉成机械判据（`tests/application/preflight/test_read_grant_is_per_item.py`）。
落地后确认这类判据需要三条**同时**成立，缺一条就会退化成空转：

1. **结构否定**：不写「我们没有成类放行」这种散文，而是判**结构形态**——
   ① 每个 `capability:` 都是词表的**精确成员**；② **没有**任何规则的能力是另一个能力的
   **段前缀**（`read` 覆盖 `read.x` 正是「成类放行」的结构特征）。第 ② 条是把「类别级」
   翻译成可判定谓词的关键：**字符串天然只能命名一个能力**，所以「一条规则覆盖一类」只能以
   **前缀 / 通配**的形态出现——判这两者就够了。
2. **检测器必须可被按压**：`category_forms()` 先用现状断言为空，**再**注入 `read.*`（以及
   `literature.` 前缀形态）断言**必须命中**。只写前者的话，一个恒返回空列表的实现也能绿。
3. **可核对的清单**：把「15 条该登记的读能力**一条都没被放行**」做成断言——不算**数量**
   （`== 15`）而只写「无重叠」会漏掉「清单被删空」这一形态；清单来自
   `docs/architecture/POLICY_SURFACE_AUDIT.md` 的差集表（与 GOAL-014 的判据同源）。

## 为什么这样做

- **否定式决定没有正向见证物**：「不做 X」不会在产物里留下痕迹，所以判据只能判
  **结构形态 + 清单**；靠读代码或读文档都不可复核。
- **空转风险最高的正是否定判据**：正向判据至少会被「产品坏了」按红；否定判据在**被删空后
  仍然绿**。所以「检测器可被按压」不是锦上添花，是这类判据的**必要条件**。
- **数量断言是清单完整性的唯一护栏**：只断言「清单里没有已放行的」时，把清单删成 0 条也绿。

## 怎么做与复现

- 判据：`uv run --frozen --no-sync python -B -m pytest
  tests/application/preflight/test_read_grant_is_per_item.py -q` ⇒ `4 passed`。
- 零策略面改动的取证：`git status --short examples/config/policy.yaml
  packages/application/preflight/policy_check.py` ⇒ 输出行数 **0**；
  `git diff --stat` 对这两个文件**为空**。按压用**内存内字典**，不落盘。
- 形态口径（判据里写死）：
  - 类别级 / 通配 = 含 `*` 或 `?`，或以 `.` 结尾；
  - 段前缀 = `other.startswith(name + ".")`；
  - 读类 = 末段 ∈ `{read, inspect, validate}`（读类与写类的**区分**沿用差集表口径，
    但「是否该放行」不在本判据面内）。

## 适用边界

- 判据只判**放行的形态**（逐条 vs 成类），**不**判某个读能力**该不该**放行——那是逐次授权
  时的判断，属用户面。
- 「新增读能力会反复撞 `default_effect`、每次都要一次 GOAL 级授权」是 D-02(b) 的**已知代价**，
  原样保留；成类预放行属「`W-A` 之外的策略面放宽」，**需另行拍板**。
- 判据只读 `examples/config/policy.yaml` 与 `docs/architecture/POLICY_SURFACE_AUDIT.md`；
  「该登记」清单的维护仍归 GOAL-014 的差集判据与文档。

## 来源

- `.cursor/plans/tasks/PLAN-20260925-170-read-grant-stays-per-item.md`（WP1–WP4）
- `.cursor/plans/rechecks/RECHECK-20260925-171-read-grant-stays-per-item.md`
- `.cursor/plans/goals/GOAL-20260925-016-decisions-landed-and-threat-model.md`（EC-02）
- `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` D-02（判词与证据出处同源）
- `docs/architecture/POLICY_SURFACE_AUDIT.md`（「该登记 = 15 条」）
