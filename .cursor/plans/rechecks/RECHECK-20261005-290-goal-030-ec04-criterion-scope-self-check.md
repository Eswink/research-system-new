---
id: RECHECK-20261005-290
slug: goal-030-ec04-criterion-scope-self-check
title: 复检：GOAL-030 EC-04 —— 判据射程自查（观察器 + 自查表 + 可判红用例；并抓到扫描器自身的同族缺陷）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-05
updated_at: 2026-10-05
plan_id: PLAN-20261005-289
reviewer: root-agent
parent_goal: GOAL-20261005-030
verify_paths:
  - >-
    uv run --frozen --no-sync python -B -m pytest
    tests/tooling/test_criterion_scope_self_check.py -q ⇒ 10 passed
  - >-
    uv run --frozen --no-sync python -B -m pytest tests/tooling -q ⇒ 1314 passed
  - >-
    uv run --frozen --no-sync python -B -m pytest tests/architecture/python
    tests/application tests/adapters tests/e2e tests/api tests/loaders -q ⇒
    2334 passed / 21 skipped
owners:
  - root-agent
---

# RECHECK-20261005-290 — GOAL-030 EC-04

## 结论

**PASS_WITH_WARNINGS**。EC-04 的四半（观察器 / 自查表 / 可判红用例 / 端到端按压）**实测到场**；
**过程中抓到并修掉扫描器自身的一处同族缺陷**（后写覆盖索引 ⇒ 被按压的形态被吃掉），
该修正连同其**自身按压用例**一并交付。

## 检查结果

| EC-04 要求 | 判据 | 实测 |
| --- | --- | --- |
| 受判面是否被写成交集/过滤（同一种手法） | `scan_judge_faces`（AST + 一层数据流） | 三种形态可识别；本轮三条判据**报空** |
| 射程自查表（每条：受判面 / 是否掩蔽 / 按压形态 / 实测） | `SCOPE_TABLE` + 四条结构用例 | 逐条齐备；空理由 / 幽灵 / 下界不足各自判红 |
| 反证：掩蔽形态有**可判红**用例 | `TestTheScannerBitesOnAMaskingForm`（5 条） | GOAL-029 **原形**报出 / 差集报出 / 诚实计算报空 / 干净报空 |
| 对至少一条判据人为改成「安全」交集并断言能抓到 | 端到端按压 EC-01 真实判据 | 主判据**判红并点名**（文件 + 行号 + 形态）；复原逐字节一致 |

## 按压（三处，逐字节复原）

1. **合成原形**：`missing = [name for name in declared & implemented …]` ⇒ 报出
   `intersection_as_expectation` + `intersection_narrowed_universe`。
2. **端到端**：把 EC-01 的真实判据按压成掩蔽形态 ⇒ `test_the_real_judges_carry_no_masking_form`
   判红并点名行号；复原 ⇒ 10 passed。
3. **自查器自身修复**（`_assigned_set_ops` 改回单值 dict）⇒
   `test_the_assignment_index_keeps_every_definition` 判红；复原 ⇒ 10 passed。

## 复检发现（W-NN，如实登记）

- **`W-1`｜扫描器初版的两处缺陷都是「受判面写窄」的同族变体**（本轮实测抓到并修）：
  ① 只看 `assert` 表达式 ⇒ 漏掉藏在赋值里的掩蔽（补：一层数据流跟进）；
  ② 数据流索引用**单值 dict** ⇒ 同名多次赋值时**后写覆盖前写**，被按压成掩蔽形态的那一次
  **被后来的诚实写法覆盖** ⇒ 报空。**这正是 `MEM-20260922-160` 的形态，出现在自查器自己身上**
  —— 与 GOAL-029 的原始缺陷同族。修法 + 单列按压用例已交付。
- **`W-2`｜观察器是形态检测，不是语义证明**：它抓「受判集合被集合运算收窄」这类**结构特征**；
  「断言是否真的覆盖了它声称覆盖的东西」仍需**按压**（本 GOAL 的 EC-01…EC-03 各自做了，
  见 `RECHECK-20261005-284/286/288`）。**不得**把「观察器报空」当成语义级保证。
- **`W-3`｜射程面只覆盖本轮新增判据**：`JUDGES` 是逐条写死的三条；既有判据（含 GOAL-029 的
  那些）**不在**本判据的受判面内。把它们纳入需要先确认若干既有判据**确实**含诚实计算的写法
  （否则会大面积误报）—— 属下一批候选。
- **`W-4`｜「诚实缺口计算」的判别是形态规则**：`missing = set(expected) - set(actual)` 被视作
  合法，判据是「遍历面不是那个差集」。若有人写成 `for x in set(expected) - set(actual)` 后再
  断言其为空，**会**被判红 —— 那是**有意的**（此时遍历面确实被收窄了）。
- **`W-5`｜`min_assertions` 下界是手写常量**：三条判据各自给 20~25；它只防「判据被削成空转」，
  不保证「每条断言都在判该判的东西」。

## 未覆盖范围（原样保留）

读面未认证 / 多租户未做 / RBAC 未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口 /
D 组审批通道未接通。**不得**据此宣称项目安全；**不得**宣称投递语义为「恰好一次」
（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
