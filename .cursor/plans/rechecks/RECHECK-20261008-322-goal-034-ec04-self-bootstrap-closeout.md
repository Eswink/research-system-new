---
id: RECHECK-20261008-322
slug: goal-034-ec04-self-bootstrap-closeout
title: 独立复检：GOAL-034 cycle 3（EC-04）自举收口
plan_id: PLAN-20261008-321
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-08
completed_at: 2026-10-08
owners:
  - root-agent
---

# RECHECK-20261008-322 — GOAL-034 cycle 3（EC-04）独立复检

复检对象：`PLAN-20261008-321`（自举收口）。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 验证器进树（AC-1）

| 读法 | 读数 |
| --- | --- |
| 复用标准断言集 | 是（调用 `standard_verdicts(root)`；**一行未重写**） |
| 本轮断言落点 | `tools/goal034_closeout_assertions.py`（4 个分区函数，均 ≤ 50 行） |
| `--verdict-only` 判词计数 | **59 判词**（本树） |
| 非判词行 / 绝对路径 | **0 / 0**（纯度与路径无关两条契约成立） |

### 2. `IN_SCOPE` 纯收紧（AC-2）

两个新脚本已加入必备清单（`+2` 行，只增不删）；
`tests/tooling/test_tooling_scripts_meet_product_gates.py` **8 passed**。
**门当场抓到**我自己的缺陷：`assertion_verdicts` **77 行** > 50 行上限 ⇒ 拆 4 个分区函数
（**断言一条未改**）。

### 3. 两树复检（AC-3）

```
TREE current=D:\research-system exit=0 verdicts=59 sha256=9b05e6d5...
TREE clean=D:\research-system-clean-tree exit=0 verdicts=59 sha256=9b05e6d5...
COMPARE identical=True
TWO-TREE PASS
```

### 4. 判词归档进树（AC-4，含 bootstrap 时序）

| 轮次 | base-ref | 读数 |
| --- | --- | --- |
| 首轮 | `b136cc8`（归档尚未生成） | 两路判词**逐字节相同**（`e395107e…`），红项**仅**两份归档缺失 |
| 次轮 | `HEAD`（含归档） | **`TWO-TREE PASS`**，两路 `sha256` 相同 |

归档：`.cursor/plans/goals/evidence/GOAL-20261008-034-verdict-{current,clean}.txt`
（2039 B / 59 行 / **CR=0** / 两份逐字节相同）。**未**为让首轮变绿而删掉存在性断言。

### 5. as-is m0（AC-5）

见 GOAL 迭代日志「cycle 3」行与 m0 日志终局行（在**全部记录写入之后**跑）。

### 6. 治理与宪章（AC-6）

`validate.py` ⇒ 绿；`tests/tooling/test_mainline_program_is_intact.py` ⇒ 绿（8 passed）。

### 7. CI 台账（AC-7）

见 GOAL 的「CI 台账」节（逐提交、含两次真红/取消的如实登记与自我指涉边界）。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-7 逐条独立成立；**无产品缺陷**（本 cycle 零产品改动）。

### Warnings

- **W-1（bootstrap 时序是本 EC 的固有形态）**：判词归档由**被归档的那个入口**写出 ⇒
  首轮必红（归档不存在），次轮才全绿。这不是缺陷，但**必须如实登记**（否则「首轮红」
  会被误读成失败）；PLAN 的 AC-4 与本节都写明了。
- **W-2（`RECHECK-320` 的五条 W 保持）**：三处真机制缺口（已修）/ 一次判据假信号（已修）/
  `calls_by_round` 的边界 / 未覆盖（并行多轮、跨 run 累积、`budget_exhausted`）/
  判据自证伪的返工 —— 逐条**原样保持**。
- **W-3（GOAL 级未覆盖范围）**：读面未认证 / 多租户 / RBAC / BOLA·BFLA / 部署面未验证 /
  `R-M1` 未收口；**不得**据此宣称项目安全；**不得**宣称投递语义为「恰好一次」
  （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
- **W-4（自我指涉边界）**：本节的收口提交自身不产生可引用的 CI 结论 ⇒ 以「末条提交 +
  覆盖说明」封闭，**不得循环引用**（承 GOAL-032/033 同款）。
