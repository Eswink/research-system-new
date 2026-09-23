---
id: MEM-20260923-112
title: "复检脚本不要钉被检对象的中间形态字面量；任何 amend 之后此前写下的验证数字必须复测"
status: ACTIVE
created_at: 2026-09-23
updated_at: 2026-09-23
scope: repository
confidence: 0.94
review_after: 2027-03-23
source_plans:
  - .cursor/plans/tasks/PLAN-20260923-146-path-b-refutation-record.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260923-145-experiment-evidence-chain-traceability.md
supersedes: []
---

## 做了什么

GOAL-012 cycle 4 做两棵树成对复检时，把 cycle 3 的独立复检脚本
（`scratch/verify_goal012_c3.py`）**在当前树上重跑**，得到 `checked=24 failures=1`——而
RECHECK-145 的「当前树」一行写的是 `24/24`。红的是一条**判据存在性**检查（B2），它把判据文件的
一句实现写成字面量钉住：`"Digest.of_bytes(content)" in judge`。

## 为什么这样做（根因）

1. cycle 3 的判据文件在 m0 的**50 行/函数**门禁下被**纯重构**过：内容 digest 从
   「先取字节、再 `Digest.of_bytes(content)`」并成一行
   `digest = Digest.of_bytes(client.get(f"/artifacts/{artifact_id}/content").content)`，
   断言逐条未减。amend 之前的提交仍在 reflog：`git diff 919ad2c 6ccdf46 --
   tests/e2e/test_ec03_experiment_evidence_chain.py` 逐字可见这次并句。
2. B2 钉的正是被并掉的那个**中间形态**。⇒ 一次不改断言的纯重构就让复检脚本自己变红；
   反过来，**记录里那个 24/24 是在 amend 之前的判据上测的**——先测、后 amend、未复测就落记录。

## 怎么做与复现

- 复检脚本的判据要判**语义**，不判中间形态：
  `"Digest.of_bytes(" in judge and "/artifacts/{artifact_id}/content" in judge and
  "get_source(" in judge and 'extracted_by == f"experiment:{experiment_run_id}"' in judge`
  （token 更多、只增不减强度，且对合法的重构免疫）。
- 复测口径：当前树 `checked=24 failures=0`；基线树 `31dfbd4` `checked=24 failures=6`
  ⇒ 与原记录**同结论同数字**。
- 通用纪律：**任何 amend / 重跑会改到被检对象时，此前写进记录的数字一律作废重测**；
  发现记录与时点不符，就地写**勘误**（保留原行 + 标明测量时点 + 复测结果），不要静默改数。

## 适用边界

- 只对「复检脚本/判据存在性检查」成立；对**行为判据**（跑起来才知真假）不适用——那些本来
  就必须重跑，没有「钉字面量」的余地。
- 判据强度只增不减：这次是**读法**变严（3 token → 4 token），被检的判据文件本身一字未改。
- 门禁驱动的重构（50 行/函数、450 行/文件）会**反复**触发这一类漂移：只要看见 `_assert_*`
  helper 抽取，就假定此前所有「按字面量检查该文件」的复检脚本需要复测。

## 来源

- GOAL-20260923-012 cycle 4；PLAN-20260923-146；RECHECK-20260923-145 的「勘误」节（PASS 结论不变）。
- 实测：`git diff 919ad2c 6ccdf46 -- tests/e2e/test_ec03_experiment_evidence_chain.py`；
  两棵树复跑 `scratch/verify_goal012_c3.py`（当前树 24/24、基线树 6 红）。
