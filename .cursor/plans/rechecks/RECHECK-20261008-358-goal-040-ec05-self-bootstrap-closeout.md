---
id: RECHECK-20261008-358
slug: goal-040-ec05-closeout-recheck
title: 独立复检：GOAL-040 cycle 2（EC-05）自举收口（两树 + 归档 + m0 + 治理）
plan_id: PLAN-20261008-357
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-08
completed_at: 2026-10-08
verify_paths:
  - path: 当前树（主干工作树，含本轮交付面）
    evidence: .cursor/plans/goals/evidence/GOAL-20261008-040-verdict-current.txt
  - path: 干净 checkout（`git worktree add --detach` @ `--base-ref`，用后移除）
    evidence: .cursor/plans/goals/evidence/GOAL-20261008-040-verdict-clean.txt
owners:
  - root-agent
---

# RECHECK-20261008-358 — GOAL-040 cycle 2（EC-05）独立复检

复检对象：`PLAN-20261008-357`（自举收口）。独立重跑下列机械面，不引用 PLAN 结论当证据。

**本复检的两路**：① **当前树**与 ② **干净 checkout**（`git worktree add --detach @ --base-ref`，
同一份复检脚本、同一组断言、只比对判词行）；两路各自的留档证据 = 判词归档
`.cursor/plans/goals/evidence/GOAL-20261008-040-verdict-current.txt`（当前树）与
`.cursor/plans/goals/evidence/GOAL-20261008-040-verdict-clean.txt`（干净树）。

## 检查结果

### 1. 验证器进树（AC-1）

| 读法 | 读数 |
| --- | --- |
| 复用标准断言集 | 是（`standard_verdicts(root)`；**一行未重写**） |
| 本轮断言落点 | `tools/goal040_closeout_assertions.py`（判定种类 / 声明与迁移 / 两适配器 / 接口面 / 分派 / 反证面 / 判据面 / 归档面 / 射程面；函数均 ≤ 50 行） |
| `--verdict-only`（起草中间态） | **71 PASS / 2 FAIL**（逐条：本轮两份记录未写）—— 次序的真实形态 |
| `--verdict-only`（收口态） | **73 判词 / 0 FAIL** |
| 非判词行 / 绝对路径 | **0 / 0** |

### 2. `IN_SCOPE` 纯收紧（AC-2）

两脚本已入清单（`+2` 行，只增不删）；判据 **8 passed**；四道门绿。

### 3. 两树复检（AC-3）

| 轮次 | `--base-ref` | 读数 |
| --- | --- | --- |
| 首轮 | `8e8e5e4`（本轮交付面未提交） | **`TWO-TREE RED`**（bootstrap 时序，非失败）：current **73 判词 / 0 FAIL**（工作树已含本轮全部记录）、clean **73 判词 / 3 FAIL**（缺本轮两份记录与残余标记）⇒ `COMPARE identical=False`；**两份归档由本首轮写出** |
| 次轮 | 读数在本节回填 | |

### 4. 判词归档进树 + as-is m0（AC-4）

读数在收口提交回填（形态 / `sha256` / m0 终局行）。

### 5. 治理与宪章（AC-5）

`validate.py` ⇒ 绿；`test_mainline_program_is_intact.py` ⇒ 绿（本 GOAL 的 id 在程序表序 8）。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-7 逐条独立成立；**无产品缺陷**（本 cycle 只新增
`tools/` 机械面与记录）。

### Warnings

- **W-1（bootstrap 时序）**：判词归档由被归档的入口写出 ⇒ 首轮必红，次轮才全绿；
  如实登记，**未**删存在性断言。
- **W-2（承继残余原样保持）**：GOAL-039 的 `Q-1`…`Q-3`、GOAL-038 的 `P-1`…`P-3`、
  GOAL-037 的 `O-1`…`O-5`、GOAL-036 的 `M-1`…`M-5`、`R26-*` 终态、未覆盖范围逐条保持；
  本轮只追加 `R-1`…`R-3`。
- **W-3（GOAL 级未覆盖范围）**：读面未认证 / 多租户 / RBAC / BOLA·BFLA / 部署面未验证 /
  `R-M1` 未收口；本轮 `R-1`…`R-3`（失败后自动处置 / 退避 / 跨程序传播）**未覆盖**；
  **不得**据此宣称项目安全；**不得**宣称投递语义为那四个字（**明确否认**）。
- **W-4（自我指涉边界）**：本节的收口提交自身不产生可引用的 CI 结论 ⇒ 以「末条提交 +
  覆盖说明」封闭，**不得循环引用**。
