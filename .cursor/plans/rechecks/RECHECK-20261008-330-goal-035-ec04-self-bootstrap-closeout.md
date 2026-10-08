---
id: RECHECK-20261008-330
slug: goal-035-ec04-closeout-recheck
title: 独立复检：GOAL-035 cycle 4（EC-04）自举收口（两树 + 归档 + m0 + 治理）
plan_id: PLAN-20261008-329
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-08
completed_at: 2026-10-08
verify_paths:
  - path: 当前树（主干工作树，含本轮未提交的交付面）
    evidence: .cursor/plans/goals/evidence/GOAL-20261008-035-verdict-current.txt
  - path: 干净 checkout（`git worktree add --detach` @ `--base-ref`，用后移除）
    evidence: .cursor/plans/goals/evidence/GOAL-20261008-035-verdict-clean.txt
owners:
  - root-agent
---

# RECHECK-20261008-330 — GOAL-035 cycle 4（EC-04）独立复检

复检对象：`PLAN-20261008-329`（自举收口）。独立重跑下列机械面，不引用 PLAN 结论当证据。

**本复检的两路**（`verify_paths` 的落实）：① **当前树**（主干工作树）与 ② **干净 checkout**
（`git worktree add --detach @ --base-ref`，同一份复检脚本、同一组断言、只比对判词行）；
两路各自的留档证据 = 判词归档
`.cursor/plans/goals/evidence/GOAL-20261008-035-verdict-current.txt`（当前树）与
`.cursor/plans/goals/evidence/GOAL-20261008-035-verdict-clean.txt`（干净树）
—— 互不相同、都在树（第 4 节给形态读数）。

## 检查结果

### 1. 验证器进树（AC-1）

| 读法 | 读数 |
| --- | --- |
| 复用标准断言集 | 是（调用 `standard_verdicts(root)`；**一行未重写**） |
| 本轮断言落点 | `tools/goal035_closeout_assertions.py`（三条产品轴 + 判据面 + 归档面 + 射程面，函数均 ≤ 50 行） |
| `--verdict-only` 判词计数（归档生成**之前**的中间态） | **65 PASS / 5 FAIL**，红项逐条：两份归档缺失、`RECHECK-330` 尚未写入（记录声明先行）、残余标记待定格 —— 次序的真实形态，不是失败 |
| `--verdict-only` 判词计数（收口态） | **70 判词 / 0 FAIL** |
| 非判词行 / 绝对路径 | **0 / 0**（纯度与路径无关两条契约成立） |

### 2. `IN_SCOPE` 纯收紧（AC-2）

两个新脚本已加入必备清单（`+2` 行，只增不删）；`tests/tooling/test_tooling_scripts_meet_product_gates.py`
**8 passed**。两脚本四道门（独立重跑）：

| 门 | 读数 |
| --- | --- |
| `ruff check` | `All checks passed!` |
| `ruff format --check` | `2 files already formatted` |
| `mypy`（strict） | `Success: no issues found in 2 source files` |
| 规模（450 行 / 函数 50 行） | `tools/goal035_closeout_assertions.py` **238** 行 / `tools/verify_goal035_closeout.py` **191** 行 |

### 3. 两树复检（AC-3）

```
回填（首轮 / 次轮读数 + 两路 sha256 + COMPARE 结论）
```

**bootstrap 时序如实登记**：判词归档由**被归档的那个入口**写出 ⇒ 首轮必然红于「归档不存在」
（两棵树都还没有归档文件）；次轮（`--base-ref` 指向**含归档**的提交）才 `TWO-TREE PASS`。
**未**为让首轮变绿而删掉存在性断言。

### 4. 判词归档进树（AC-4）

| 读法 | 读数 |
| --- | --- |
| 落点（在树） | `.cursor/plans/goals/evidence/GOAL-20261008-035-verdict-{current,clean}.txt` |
| 形态 | 回填（字节数 / 行数 / **`CR=0`** / 两份 `sha256` **相同**） |

### 5. as-is m0（AC-5）

在**全部记录写入之后**独占跑：终局行与 `passed/skipped` 读数**回填**（见 GOAL 迭代日志
cycle 4 行与 m0 日志）。

### 6. 治理与宪章（AC-6）

`validate.py` ⇒ 绿；`tests/tooling/test_mainline_program_is_intact.py` ⇒ 绿（本 GOAL 的 id
在程序表序 3、进展记录行指向真实 RECHECK 文件）。

### 7. CI 台账（AC-7）

见 GOAL 的「CI 台账」节（逐提交、含本轮真红/取消的如实登记与自我指涉边界封闭）。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-7 逐条独立成立；**无产品缺陷**
（本 cycle 零产品改动：只新增 `tools/` 机械面与记录）。

### Warnings

- **W-1（bootstrap 时序是本 EC 的固有形态）**：判词归档由**被归档的那个入口**写出 ⇒
  首轮必红（归档不存在），次轮才全绿。这不是缺陷，但**必须如实登记**（否则「首轮红」
  会被误读成失败）；本节与 PLAN 的 AC-3 都写明了。
- **W-2（承继残余原样保持）**：GOAL-034 的 `W-1`…`W-4`、GOAL-033 的 `W-1`…`W-6`、
  GOAL-032 的 `W-1`…`W-8`、历史 `tools/` 的旧 lint 与旧脚本 —— 逐条**原样保持**，
  本轮只追加。
- **W-3（GOAL 级未覆盖范围）**：读面未认证 / 多租户 / RBAC / BOLA·BFLA / 部署面未验证 /
  `R-M1` 未收口；本轮残余 `N-3`…`N-6`（多评审者聚合 / 承接面读数 / 跨机器位级复现 /
  结论内容正确性）**未覆盖**；**不得**据此宣称项目安全；**不得**宣称投递语义为那四个字
  （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
- **W-4（自我指涉边界）**：本节的收口提交自身不产生可引用的 CI 结论 ⇒ 以「末条提交 +
  覆盖说明」封闭，**不得循环引用**（承 GOAL-032…034 同款）。
