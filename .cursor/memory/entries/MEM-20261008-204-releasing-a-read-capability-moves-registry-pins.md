---
id: MEM-20261008-204
title: "放行一条读能力会牵动策略面登记表族：五处同轮同步，谓词不动、登记加一条"
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
scope: repository
confidence: 0.95
review_after: 2027-04-08
source_plans:
  - .cursor/plans/tasks/PLAN-20261008-331-goal-036-ec01-02-review-read-onboarding.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261008-332-goal-036-ec01-02-review-read-onboarding.md
supersedes: []
tags: [capability-onboarding, policy-surface, same-round-sync, pins, goal-036]
---

## 做了什么

给 `policy.yaml` 的 `allow` 加**一条**只读放行（`review.read`）后，门链立刻报出 **6 条**红
（4 个判据文件），全部来自「**策略面登记表**」这一族 —— 它们不是「另一条判据」，而是同一件事
（「放行了哪些读能力」）的注册面。逐个量出来的同步集：

| # | 落点 | 改动形态 |
| --- | --- | --- |
| 1 | `examples/config/policy.yaml` | `allow` **+1**（其余三段 + `default_effect` 零变化） |
| 2 | `packages/application/preflight/policy_check.py::_CAPABILITY_SCOPE` | **+1**（并集相等由 `test_m2_audit` 锁死） |
| 3 | `docs/architecture/POLICY_SURFACE_AUDIT.md` | 该行**离开差集**、进交集清单、计数、日期化变更注 |
| 4 | `tests/application/preflight/test_read_grant_is_per_item.py` | `EXPECTED_REGISTERED` 8 → 7 |
| 5 | `tests/application/preflight/test_release_expansion_is_read_only.py` | `_RELEASED` +1 / `_UNRELEASED_READS` −1 / scope 期望表 +1 |

## 为什么这样做

这些 pin 是**精确集合**（「放行面 − 基线 == 声明集」「该登记 == N 条」「逐条 scope == 邻接形态」），
所以**任何**新放行都必然让它们红一次。红的形态是「集合不再相等」，而不是「谓词被违反」——
两者的处置完全不同：

- **处置 = 加法 / 搬迁登记**：把新的放行项**登记进集合**，谓词、阈值、受判形态一个字都不改；
- **不得**处置成：把等值断言改成包含断言、把精确计数改成范围、把「逐条」改成「至少一条」。

**判断有没有偷工的正确读法**：看**反证臂**还在不在、还咬不咬得住。本轮实测三门全绿：

- 非只读能力代入只读面 ⇒ 谓词点名（`workspace.delete: 末段不是只读后缀`）；
- 删除一条放行规则 ⇒ 真实求值器回落 `default_effect`（`used default policy effect`）；
- 把非只读能力**注入真实 `allow`** ⇒ 扩集断言报出（初版判据的缺口，实测过：只看写死清单时
  插入 `workspace.delete` 会全绿）。

若有人放松了谓词，**这三条会先失效** —— 它们比「断言看起来还在」更接近真相。

## 怎么做与复现

```bash
# 1) 改 policy.yaml（只加一条 allow）+ 镜像表 _CAPABILITY_SCOPE（加一条）
# 2) 跑门，读红项：它们会逐条点名缺哪条登记
uv run --frozen --no-sync python -B -m pytest tests/application/preflight tests/application/test_m2_audit.py -q
# 3) 按红项逐条加登记（5 处），再跑
# 4) 核对「段指纹」仍绿（deny/require_approval 段正文 sha256 未变）
```

**清单外仍禁改**：把这条经验写成「凡 pin 皆可疑」是错的 —— 同步集是**有界**的（本例 5 处），
清单外的既有判据触达即 BLOCKED。所以要把同步集**逐条枚举进 GOAL 的 `fix_policy`**，
而不是给自己一个「同轮同步」的宽泛豁免。

## 适用边界

- 适用于任何「**有界放宽**」的登记面（放行、白名单、pin 集合、清单）。
- **不**适用于「谓词错了」的场景 —— 那时改的是判据本身，需要单独理由与新反证，不是本条。
- 本条**不**声称这些 pin 覆盖了放行的全部影响面（EC-03 的「真的被用上」是另一个面）。

## 来源

- `.cursor/plans/tasks/PLAN-20261008-331-goal-036-ec01-02-review-read-onboarding.md`
- `.cursor/plans/rechecks/RECHECK-20261008-332-goal-036-ec01-02-review-read-onboarding.md`
- 先例：GOAL-20261006-031 的两轮放行（同样的 5 处同步；`POLICY_SURFACE_AUDIT.md` 的日期化变更注）
