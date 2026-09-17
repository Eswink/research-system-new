---
id: MEM-20260917-062
title: "收敛路径没有 outcome ⇒ 事实只能从事件链补回来；重放一致性用例必须钉住'非空'"
status: ACTIVE
created_at: 2026-09-17
updated_at: 2026-09-17
scope: repository
confidence: 0.9
review_after: 2027-09-17
source_plans:
  - .cursor/plans/tasks/PLAN-20260917-087-failed-run-semantic-digest.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260917-087-failed-run-semantic-digest.md
supersedes: []
tags:
  - manifest
  - semantic-digest
  - failure-convergence
  - event-sourcing
  - replay
  - test-vacuity
---

# 收敛路径的事实来自事件链，不是来自 outcome

## 做了什么

执行期失败收敛（`run_from_execution` 的 `except ValueError:`）此前只从 `manifest.frozen`
事件里捞回 `digest` / `pricing_version` / `pricing_digest`，**语义 digest 不落行**——于是
`assert_semantics_frozen` 一句 `frozen manifest lacks a semantic digest` 把这条 FAILED run
永远挡在重建入口之外（尽管它冻结过 manifest、事件也已经落 outbox）。

```text
producer：RunManifest.semantic_digest()（排除 frozen_at）
事件：    frozen_payload 增 semantic_digest（与 digest 同一时刻同一 producer）
收敛：    FrozenManifestRefs.from_payload(payload).apply(run)
          apply == ResearchRun.with_manifest(...)  ← 成功路径同一个域方法
读面：    GET /runs/{id}.manifest_semantic_digest（None = 未冻结或事件早于本轮）
消费：    assert_semantics_frozen 用它放行、也用它拒绝（换值 ⇒ drifted）
```

## 为什么这样做

1. **异常路径没有 outcome 可读**：`start_run` 抛 `ValueError` 时 `RunOutcome` 根本不存在，
   冻结事实的唯一副本就是 outbox 事件。"把事件链当 replay 源"不是设计偏好，是这条路径的
   物理事实。
2. **"同判据"要能被一眼看出**：同一个 producer（`semantic_digest()`）+ 同一个域方法
   （`with_manifest`）。手写字段赋值即使值对了，也无法证明两条路径的判据一致。
3. **缺一项就是缺入口**：语义 digest 不是装饰字段——缺它 → 漂移守卫拒绝 → 没有重建入口。

## 怎么做与复现

```bash
python -m pytest tests/application/run_orchestration/test_frozen_payload_semantic_digest.py -q
python -m pytest tests/api/test_failed_run_semantic_digest_api.py -q     # 判据/事件/重放/守卫
```

## 适用边界（踩过的坑）

- **重放用例会假绿**：反证"去掉 payload 键"时，'重放一致性'用例仍然通过——因为
  `from_payload` 读不到键 ⇒ None，而 run 行也是 None，**两侧同时为空时相等成立**。
  修法：重放断言必须先钉 `is not None` 再比相等。任何"重放/投影一致"用例都有这个陷阱。
- **测试替身要逐字段复制**：仿 `_park` 构造"同一条 run 的停车态"时漏掉
  `pricing_version`/`pricing_digest` ⇒ 重建被漂移守卫拒（`drifted`）。那是守卫在起作用
  （定价引用参与语义 digest），不是噪声；补上字段即可，不要放宽断言。
- **判据一致 ≠ 值相等**：语义 digest 覆盖 `run_id`，所以"同协议的两条 run"digest 必然不同；
  跨 run 比较会假红。要证同判据就共用同一个断言函数。
- **旧事件没有这个键**：新增的是可选键（`schema_version` 仍 "1"），旧 payload 读回 None，
  不回填、不猜测——旧 run 的重建行为与今天一致（仍被守卫拒绝）。
- 相关：[[MEM-20260917-061]]（声明要有消费者或点名）、[[MEM-20260917-060]]（停车语义成为
  读面事实）、[[MEM-20260915-047]]（冻结被解析的字节）。

## 来源

- PLAN-20260917-087 / RECHECK-20260917-087（GOAL-20260917-004 cycle 4 = EC-04）。
