---
id: RECHECK-20261005-291
slug: goal-030-closeout
title: GOAL-030 收口复检 — 承接能力的真实使用与科研闭环加深（五 EC 全 PASS；两树 TWO-TREE PASS；as-is m0 23/23）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-05
updated_at: 2026-10-05
plan_id: PLAN-20261005-289
reviewer: root-agent
parent_goal: GOAL-20261005-030
verify_paths:
  - >-
    uv run --frozen --no-sync python tools/verify_goal030_closeout.py --root . --verdict-only
    ⇒ 56 PASS / 0 FAIL（SUMMARY total=56 failed=0）
  - >-
    uv run --frozen --no-sync python tools/two_tree_recheck.py --script
    tools/verify_goal030_closeout.py --root . --base-ref HEAD --script-mode shared
    --verdict-current .cursor/plans/goals/evidence/GOAL-20261005-030-verdict-current.txt
    --verdict-clean .cursor/plans/goals/evidence/GOAL-20261005-030-verdict-clean.txt
    ⇒ TWO-TREE PASS（两树各 56 判词、sha256 相同）
  - >-
    as-is m0（独占、仓库 .venv、canonical DSN pin、不接管道）
    ⇒ PASS: profile=m0; 23 deterministic checks
owners:
  - root-agent
---

# RECHECK-20261005-291 — GOAL-030 收口

## 结论

**PASS_WITH_WARNINGS**。GOAL-030 的五个 EC 全部 `PASS`，收口三项（验证器进树 / 两树同结论 +
判词归档进树 / as-is m0 23/23 在记录之后）**实测到场**，治理绿，CI 台账逐提交。

## 检查结果

### 逐 EC 终态

| EC | 终态 | 交付物 | 本地证据 |
| --- | --- | --- | --- |
| EC-01 承接能力进入真实 run | PASS | 三条已放行承接读能力由运行链确定性执行 + **下游消费** + 反证点名 | `tests/e2e/test_capabilities_really_used_in_a_run.py` **8 passed** |
| EC-02 B 组承接 | PASS | `run.read` 接 `RunStore`（承接≠放行可区分）；`citation.validate` **判不可行**并登记受限面 | `tests/adapters/canonical/test_run_read_onboarding.py` **10 passed** |
| EC-03 科研动作深度 | PASS | 真容器实验 + **可否证的指标判据** + 下游消费 + 反证点名 | `tests/e2e/test_scientific_action_depth.py` **9 passed** |
| EC-04 判据射程自查 | PASS | 观察器 + 射程自查表 + **可判红用例**（并抓到扫描器自身的同族缺陷） | `tests/tooling/test_criterion_scope_self_check.py` **10 passed** |
| EC-05 自举收口 | PASS | 验证器进树 + 两树 + 归档 + m0 + 治理 + 台账 | 见下 |

## 收口三项

1. **验证器进树**：`tools/verify_goal030_closeout.py`（**429 行** ≤450，**复用**
   `closeout_recheck_tools` + `closeout_recheck_assertions.standard_verdicts`，只写本轮特有断言）；
   进 `IN_SCOPE`（**纯收紧**：只增不删）；四道门 **8 passed**。本树 `--verdict-only` ⇒
   **56 PASS / 0 FAIL**。
2. **两树复检 + 归档进树**：`--script-mode shared` ⇒ 两树各 **56 判词**、`sha256` **相同**
   （`4b16afb0fcce37074d2b3011934aad738c84f444690c05f24269d81e409ca2f4`）、
   `COMPARE identical=True`、**`TWO-TREE PASS`**（两树 exit=0）。两份判词**归档进树**
   `.cursor/plans/goals/evidence/GOAL-20261005-030-verdict-{current,clean}.txt`（各 2387 字节，
   二进制写盘）。
3. **as-is m0 = `PASS: profile=m0; 23 deterministic checks`**：`PASS [` **24** / `FAILED [` **0** /
   **5132 passed / 21 skipped / 140 warnings**，python 段 `in 665.46s`；日志
   `scratch/goal030-m0-c5.log`。**在记录写入之后**、独占运行、仓库 `.venv`、
   `uv run --frozen --no-sync python -B`、canonical DSN pin、**不接管道**、`EXIT=0`、零 python 残留。

## 复检发现（W-NN，如实登记）

- **`W-1`｜`97a9db4` 的 M0 三条 `cancelled`（流程问题，非代码缺陷）**：本 GOAL 的纪律明文
  要求「一个 cycle 攒成一次推送」，而我在 `97a9db4`（EC-04）推完**立刻**推 `fda5b64`（EC-05）
  ⇒ `cancel-in-progress` 取消了前者的 `quality-ubuntu-latest` / `quality-windows-latest` /
  `console-frontend`。**承 `MEM-20260925` 同族教训**。登记 `covered_by: fda5b64`
  （其 M0 八 job 全 `success` 覆盖同一工作树，且 `97a9db4` 的增量只有一个新增判据文件）。
- **`W-2`｜`6223c9c` 的 M0 红是**判据侧真缺陷**（本地假绿）**：`python/typecheck` 两条 mypy 错误，
  本地因只对**改动文件**跑 mypy 而漏过（CI 跑全量）。已修（`bf0919d`）并沉淀纪律
  「涉及 `tests/**` 的改动必须跑全量 mypy」（GOAL 残余 `W-8`）。
- **`W-3`｜三条 `PASS` 之外的能力仍不可协议可达**：`run.read` 与 GOAL-029 承接的五条读能力
  （`claim.read` / `budget.read` / `deliverable.read` / `experiment.read` /
  `experiment_plan.read`）都**已承接但未放行**（`policy.yaml` 无 `allow`）⇒ 属 `D-02(b)`
  待拍板；`citation.validate` 另属「pin 判据同轮同步需拍板」。**不以承接冒充满通。**
- **`W-4`｜本 GOAL 的用量未触及预算上限**：`max_cycles=20`，实际 5 个 cycle（建档 + EC-01…05），
  `no_progress_stop_cycles=2` 未触发。
- **`W-5`｜EC-03 的实验科学价值射程有限**：字典序重复检测是确定性基准；它证明「链路能跑真实验
  并对其结论下否证判据」，**不**证明系统能做开放科研（文献阅读 / 假设生成 / 统计推断都不在内）。
- **`W-6`｜记录面自洽的时间性**：本 RECHECK 与 GOAL 的 `ACHIEVED` 回写、`latest_recheck` 指向
  均在**同一条收口提交**里 —— 末条提交必然没有表内自己的 CI 行（由收口回写行 + `latest_recheck`
  双向登记；**空集合 = 未取证**）。

## 未覆盖范围（原样保留）

读面未认证 / 多租户未做 / RBAC 未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口 /
D 组审批通道未接通。**不得**据此宣称项目安全；**不得**宣称投递语义为「恰好一次」
（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
