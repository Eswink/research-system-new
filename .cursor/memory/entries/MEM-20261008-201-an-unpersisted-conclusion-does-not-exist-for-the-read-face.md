---
id: MEM-20261008-201
title: "只在内存里算出来的结论，对读面等于不存在 —— 「可判定」的落点是**存储**，且读面必须能区分「没算」与「算了是空」"
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
scope: repository
confidence: 0.92
review_after: 2027-04-08
source_plans:
  - .cursor/plans/tasks/PLAN-20261008-325-goal-035-ec02-reproducibility-conclusion-on-the-run-path.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261008-326-goal-035-ec02-reproducibility-conclusion.md
supersedes: []
tags: [reproducibility, read-face, canonical-state, goal-035]
---

## 做了什么

`ReproducibilityAudit`（域类型）、`build_reproducibility_audit` / `verify_reproducibility_audit` /
`verify_audit_outputs`（use case）、`save_audit` / `get_audit`（存储面）**全都早已存在**，
但产品侧唯一调用点是遗留 M12 参考链；研究循环的 run 路径**一次都不调用**，读面因此把
`reproduction_available` 恒写成 `False`，并用一句 `REPRODUCTION_NOTE` 诚实标注 unavailable。

本轮把「产出 + 落库」接到 run 路径（实验科学终态 ⇒ 封存 ⇒ 随实验一起进存储），读面改成
**按事实**给读数（`audit_digest` / `audit_status` / **重算**的 `audit_verified` / 逐条发现）。

## 为什么这样做

**在内存里算出来的结论对读面等于不存在。** 执行体里算一下、打条日志、对象回头就丢 ——
读面看不到，重启后也拿不回来。所以「可判定」的判据必须是**落库 + 读面可读**，而不是
「代码里调了那个函数」。

配套的三条纪律（本轮都踩到过）：

1. **可审态沿用既有谓词**：`is_auditable_state` 只让科学终态（`SUCCEEDED` /
   `NEGATIVE_RESULT`）入审计。我先自己写了个 `run.is_terminal` 的门 ⇒ 与既有口径**分叉**
   （会把执行失败/超时也审计进去）。**有既有谓词时不要写同义的第二个判据。**
2. **读面必须能区分「没算」与「算了是空」**：没有审计 ⇒ 字段**缺席** +
   `reproduction_available=false`（诚实 unavailable），不是给一堆空值假装算过。
3. **不要把 WARNING 藏起来凑空列表**：域函数对「`code_digest` 未单独 pin」给 WARNING
   （docstring 明说「诚实标注而非缺陷」）⇒ 判据断言的是「**零 FAIL 发现**」，并把 WARNING
   白名单化，而不是断言 `findings == []`。空列表断言会把「如实呈现」判成红。

## 怎么做与复现

```bash
uv run --frozen --no-sync python -B -m pytest tests/e2e/test_reproducibility_conclusion_on_the_run_path.py -q  # 3 passed（需 Docker）
uv run --frozen --no-sync python -B -m pytest tests/application/experiments tests/e2e/test_ec02_experiment_chain_offline.py -q  # 96 passed
```

按压（判据不得空转）：不产出审计 ⇒ **3 failed**；把 `audit_verified` 硬编码 `True`（不重算）
⇒ **1 failed** —— 后者证明「**重算**」是载重的：回读一个标记也能让主干绿，但抓不住篡改。

反证两向（都读同一张面）：篡改一个被绑定字段而不重新封存 ⇒ `audit_verified=false` 而
`audit_status` 仍 `PASS`（**两条是不同的事实**，要分开验）；把审计绑定的输出制品置墓碑 ⇒
出现 severity `FAIL` 的发现且 `message` **逐字点名**那个制品 id。

## 适用边界

- 适用于任何「某个结论必须在这一次执行里被算出来，并且可被复核」的要求（复现审计、
  覆盖判据、策略裁决、成本归因）。
- **不**适用于纯派生量（能从 canonical 事实重算且重算即真相的，如 digest / 计数投影）。
- 若既有类型/use case/存储已经存在，**先接线再考虑新增** —— 本轮零新域类型、零新表、
  零迁移（表早就在），只在执行体里加一个封存点 + 读面加四个字段。

## 来源

- `.cursor/plans/tasks/PLAN-20261008-325-goal-035-ec02-reproducibility-conclusion-on-the-run-path.md`
- `.cursor/plans/rechecks/RECHECK-20261008-326-goal-035-ec02-reproducibility-conclusion.md`
- 相关：[[MEM-20261008-199-a-judged-verdict-needs-a-recorded-read-face-not-a-recomputation]]
